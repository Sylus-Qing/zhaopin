import os
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
import streamlit as st
import pandas as pd

st.set_page_config(page_title="智能招聘筛选系统", layout="wide")
st.title("📊 智能招聘筛选系统")
st.write("请上传候选人 Excel 数据表，系统将自动匹配并排序最合适的人选。")

# 侧边栏：岗位筛选标准设置
st.sidebar.header("⚙️ 岗位筛选标准设置")
target_job = st.sidebar.selectbox("招聘岗位", ["数据分析师", "前端开发", "新媒体运营", "人事专员", "财务", "销售经理"])
min_edu = st.sidebar.selectbox("最低学历要求", ["本科", "硕士"])
min_exp = st.sidebar.number_input("最低工作经验(年)", min_value=0, value=1)
max_salary = st.sidebar.number_input("岗位薪资预算上限(元)", min_value=5000, value=10000, step=1000)

# 主界面：上传文件
uploaded_file = st.file_uploader("📁 请上传候选人Excel表 (支持 .xlsx 格式)", type=["xlsx"])

if uploaded_file is not None:
    # 读取数据
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip() # 清理列名空格
    
    # 提取有效数据（跳过第一行的大标题）
    df = df.iloc[1:].reset_index(drop=True) 
    
    # 核心逻辑：处理每一条数据
    results = []
    for index, row in df.iterrows():
        name = row.get('姓名', '未知')
        job = row.get('应聘岗位', '')
        edu = str(row.get('学历', ''))
        exp_str = str(row.get('工作经验', '0年'))
        # 处理年份提取
        try:
            if "应届" in exp_str or "实习" in exp_str:
                exp = 0.5
            else:
                import re
                match = re.search(r'(\d+(\.\d+)?)', exp_str)
                exp = float(match.group(1)) if match else 0
        except:
            exp = 0
            
        salary = float(row.get('期望薪资(元)', 0))
        
        # 规则判定
        score = 0
        reason = []
        status = "通过"
        
        # 只筛选当前设定岗位的人
        if job != target_job:
            status = "淘汰"
            reason.append(f"应聘岗位不符(投递{job})")
        else:
            # 1. 学历判断
            if min_edu == "本科" and edu in ["本科", "硕士", "博士"]:
                score += 20
            elif min_edu == "硕士" and edu in ["硕士", "博士"]:
                score += 20
            else:
                status = "淘汰"
                reason.append(f"学历不达标({edu})")
            
            # 2. 经验判断
            if exp >= min_exp:
                score += 30
            else:
                if status != "淘汰":
                    status = "待定"
                reason.append(f"经验不足({exp}年)")
            
            # 3. 薪资判断
            if salary <= max_salary:
                score += 40
            else:
                status = "淘汰"
                reason.append(f"薪资超标(要价{salary}, 预算{max_salary})")
                
            # 4. 技能加分
            skills = str(row.get('技能/备注', ''))
            if any(word in skills for word in ["Python", "SQL", "数据", "分析"]):
                score += 10
        
        results.append({
            "姓名": name,
            "应聘岗位": job,
            "学历": edu,
            "经验(年)": exp,
            "期望薪资": salary,
            "匹配得分": score if status != "淘汰" else 0,
            "系统结论": status,
            "淘汰/待定原因": "，".join(reason) if reason else "完美匹配"
        })
    
    result_df = pd.DataFrame(results)
    
    job_candidates = result_df[result_df["应聘岗位"] == target_job]
    job_candidates = job_candidates.sort_values(by="匹配得分", ascending=False)
    
    st.write(f"### 🎯 【{target_job}】岗位筛选结果 (共 {len(job_candidates)} 人)")
    
    if len(job_candidates) > 0:
        st.dataframe(job_candidates, use_container_width=True, hide_index=True)
        
        best_candidate = job_candidates.iloc[0]
        if best_candidate['系统结论'] == "通过":
            st.success(f"🏆 **系统强烈推荐最合适人选：{best_candidate['姓名']}** (得分: {best_candidate['匹配得分']})")
    else:
        st.warning("没有找到应聘该岗位的候选人。")

    st.write("### 📈 招聘漏斗数据看板")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**候选人筛选结论占比**")
        status_counts = result_df['系统结论'].value_counts()
        st.bar_chart(status_counts)
    with col2:
        st.write("**各岗位投递人数**")
        job_counts = result_df['应聘岗位'].value_counts()
        st.bar_chart(job_counts)