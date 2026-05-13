"""
财务报销 Agent - Streamlit Web 界面 v3
对接 FastAPI 后端，含批量上传、Plotly 统计图表、自然语言问答
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

# ---- 页面配置 ----
st.set_page_config(
    page_title="财务报销 Agent",
    page_icon="🧾",
    layout="wide",
)

# ---- Session State 初始化 ----
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None


def api_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


# ---- 登录页 ----
def login_page():
    st.title("🧾 财务报销 Agent")
    st.caption("请登录后使用")

    tab_login, tab_register = st.tabs(["登录", "注册"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("用户名 / 邮箱")
            password = st.text_input("密码", type="password")
            submitted = st.form_submit_button("登录", type="primary")
        if submitted:
            resp = requests.post(f"{API_BASE}/auth/login",
                                 data={"username": email, "password": password})
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.token = data["access_token"]
                st.session_state.user = data["user"]
                st.rerun()
            else:
                st.error(resp.json().get("detail", "登录失败"))

    with tab_register:
        with st.form("register_form"):
            name = st.text_input("姓名")
            email = st.text_input("邮箱", key="reg_email")
            password = st.text_input("密码", type="password", key="reg_pwd")
            department = st.text_input("部门")
            role = st.selectbox("角色", ["employee", "manager", "finance", "admin"])
            submitted = st.form_submit_button("注册")
        if submitted:
            resp = requests.post(f"{API_BASE}/auth/register", json={
                "name": name, "email": email, "password": password,
                "department": department, "role": role,
            })
            if resp.status_code == 200:
                st.success("注册成功，请登录")
            else:
                st.error(resp.json().get("detail", "注册失败"))


# ---- 主应用 ----
def main_app():
    user = st.session_state.user
    role = user.get("role", "employee")

    # 侧边栏
    with st.sidebar:
        st.markdown(f"👤 **{user['name']}**")
        st.caption(f"角色：{role}")
        st.divider()
        pages = ["📤 提交报销", "📦 批量上传", "📋 我的申请", "✅ 待审批", "📊 统计报表", "🤖 智能问答"]
        page = st.radio("导航", pages)
        st.divider()
        if st.button("退出登录"):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()

    # ---- 页面：提交报销 ----
    if page == "📤 提交报销":
        st.title("📤 提交报销")

        uploaded = st.file_uploader("上传发票", type=["jpg", "jpeg", "png", "pdf"])
        description = st.text_area("报销说明（可选）")

        if uploaded and st.button("🔍 识别并提交", type="primary"):
            with st.spinner("正在识别发票..."):
                resp = requests.post(
                    f"{API_BASE}/invoices/upload",
                    files={"file": (uploaded.name, uploaded.getvalue())},
                    headers=api_headers(),
                )

            if resp.status_code != 200:
                st.error(f"识别失败：{resp.json().get('detail', resp.text)}")
            else:
                data = resp.json()
                info = data["info"]
                validation = data["validation"]
                invoice_id = data["invoice_id"]

                st.subheader("📋 识别结果")
                col1, col2, col3 = st.columns(3)
                col1.metric("价税合计", f"¥ {info.get('价税合计', 'N/A')}")
                col2.metric("费用类别", info.get("费用类别", "N/A"))
                col3.metric("开票日期", info.get("开票日期", "N/A"))
                col1.metric("发票类型", info.get("发票类型", "N/A"))
                col2.metric("供应商", info.get("供应商名称", "N/A"))
                col3.metric("发票号码", info.get("发票号码", "N/A"))

                with st.expander("完整识别数据"):
                    st.json(info)

                st.divider()
                if validation["通过"]:
                    st.success(f"✅ 规则校验通过 — {validation['建议']}")
                    claim_resp = requests.post(
                        f"{API_BASE}/claims/",
                        json={"invoice_id": invoice_id, "description": description},
                        headers=api_headers(),
                    )
                    if claim_resp.status_code == 200:
                        claim_id = claim_resp.json()["claim_id"]
                        requests.post(f"{API_BASE}/claims/{claim_id}/submit",
                                      headers=api_headers())
                        st.success(f"🎉 报销申请已提交！申请编号：**#{claim_id}**")
                else:
                    st.error("❌ 规则校验未通过，请修正后重新提交")
                    for issue in validation["问题列表"]:
                        st.warning(f"• {issue}")

    # ---- 页面：批量上传 ----
    elif page == "📦 批量上传":
        st.title("📦 批量上传发票")
        st.caption("一次最多上传 10 张，系统并发识别，识别完成后统一提交申请")

        uploaded_files = st.file_uploader(
            "选择发票文件（可多选）",
            type=["jpg", "jpeg", "png", "pdf"],
            accept_multiple_files=True,
        )
        description = st.text_area("统一报销说明（可选）")

        if uploaded_files:
            st.info(f"已选择 {len(uploaded_files)} 张发票")

        if uploaded_files and st.button("🚀 批量识别并提交", type="primary"):
            if len(uploaded_files) > 10:
                st.error("每次最多上传 10 张，请分批上传")
            else:
                with st.spinner(f"正在并发识别 {len(uploaded_files)} 张发票..."):
                    files_payload = [
                        ("files", (f.name, f.getvalue())) for f in uploaded_files
                    ]
                    resp = requests.post(
                        f"{API_BASE}/invoices/batch-upload",
                        files=files_payload,
                        headers=api_headers(),
                    )

                if resp.status_code != 200:
                    st.error(f"上传失败：{resp.json().get('detail', resp.text)}")
                else:
                    data = resp.json()
                    st.subheader(f"📊 识别结果：{data['success_count']}/{data['total']} 成功")

                    for item in data["results"]:
                        if item["success"]:
                            with st.expander(f"✅ {item['filename']} — 发票ID #{item['invoice_id']}"):
                                info = item["info"]
                                col1, col2, col3 = st.columns(3)
                                col1.metric("价税合计", f"¥ {info.get('价税合计', 'N/A')}")
                                col2.metric("费用类别", info.get("费用类别", "N/A"))
                                col3.metric("供应商", info.get("供应商名称", "N/A"))
                                v = item["validation"]
                                if v["通过"]:
                                    st.success(f"✅ {v['建议']}")
                                    # 自动提交
                                    claim_resp = requests.post(
                                        f"{API_BASE}/claims/",
                                        json={"invoice_id": item["invoice_id"], "description": description},
                                        headers=api_headers(),
                                    )
                                    if claim_resp.status_code == 200:
                                        cid = claim_resp.json()["claim_id"]
                                        requests.post(f"{API_BASE}/claims/{cid}/submit", headers=api_headers())
                                        st.info(f"已提交申请 #{cid}")
                                else:
                                    st.warning("⚠️ 校验未通过，需手动处理")
                                    for issue in v["问题列表"]:
                                        st.caption(f"• {issue}")
                        else:
                            with st.expander(f"❌ {item['filename']} — 失败"):
                                st.error(item.get("error", "未知错误"))

    # ---- 页面：我的申请 ----
    elif page == "📋 我的申请":
        st.title("📋 我的报销申请")
        resp = requests.get(f"{API_BASE}/claims/my", headers=api_headers())
        if resp.status_code == 200:
            claims = resp.json()
            if not claims:
                st.info("暂无报销申请")
            else:
                status_emoji = {
                    "draft": "📝 草稿", "pending": "⏳ 待审批",
                    "manager_approved": "👍 主管已批", "finance_approved": "✅ 财务已批",
                    "rejected": "❌ 已驳回", "paid": "💰 已打款",
                }
                # 汇总卡片
                total_amount = sum(c.get("total", 0) or 0 for c in claims)
                pending_count = sum(1 for c in claims if c.get("status") == "pending")
                approved_count = sum(1 for c in claims if c.get("status") in ("finance_approved", "paid"))
                col1, col2, col3 = st.columns(3)
                col1.metric("申请总数", len(claims))
                col2.metric("待审批", pending_count)
                col3.metric("已通过金额", f"¥ {total_amount:.2f}")
                st.divider()

                for c in claims:
                    label = f"#{c['id']} — {status_emoji.get(c['status'], c['status'])}"
                    if c.get("vendor"):
                        label += f" — {c['vendor']}"
                    if c.get("total"):
                        label += f" — ¥{c['total']}"
                    if c.get("submitted_at"):
                        label += f" — {c['submitted_at'][:10]}"
                    with st.expander(label):
                        col1, col2 = st.columns(2)
                        col1.write(f"**类别：** {c.get('category', '-')}")
                        col1.write(f"**发票日期：** {c.get('invoice_date', '-')}")
                        col2.write(f"**说明：** {c.get('description', '-')}")
                        if c.get("status") == "rejected":
                            st.error("此申请已被驳回，请重新提交")
        else:
            st.error("获取失败")

    # ---- 页面：待审批 ----
    elif page == "✅ 待审批":
        if role not in ("manager", "finance", "admin"):
            st.warning("此页面仅限主管/财务/管理员使用")
        else:
            st.title("✅ 待审批列表")
            resp = requests.get(f"{API_BASE}/claims/pending", headers=api_headers())
            if resp.status_code == 200:
                claims = resp.json()
                if not claims:
                    st.info("暂无待审批申请")
                for c in claims:
                    vendor = c.get("vendor") or "未知供应商"
                    total = c.get("total") or "-"
                    category = c.get("category") or "-"
                    header = f"申请 #{c['id']} — {vendor} — ¥{total} — {category}"
                    with st.expander(header):
                        col1, col2, col3 = st.columns(3)
                        col1.write(f"**申请人ID：** {c['user_id']}")
                        col2.write(f"**发票日期：** {c.get('invoice_date', '-')}")
                        col3.write(f"**说明：** {c.get('description', '-')}")
                        st.divider()
                        col_a, col_b, col_c = st.columns([2, 1, 1])
                        comment = col_a.text_input("审批备注", key=f"comment_{c['id']}")
                        if col_b.button("✅ 通过", key=f"approve_{c['id']}", type="primary"):
                            r = requests.post(f"{API_BASE}/claims/{c['id']}/approve",
                                              json={"comment": comment},
                                              headers=api_headers())
                            st.success("已通过" if r.status_code == 200 else r.json().get("detail"))
                            st.rerun()
                        if col_c.button("❌ 驳回", key=f"reject_{c['id']}"):
                            r = requests.post(f"{API_BASE}/claims/{c['id']}/reject",
                                              json={"comment": comment or "不符合规定"},
                                              headers=api_headers())
                            st.error("已驳回" if r.status_code == 200 else r.json().get("detail"))
                            st.rerun()
            else:
                st.error("获取失败")

    # ---- 页面：统计报表 ----
    elif page == "📊 统计报表":
        if role not in ("finance", "admin"):
            st.warning("此页面仅限财务/管理员使用")
        else:
            st.title("📊 统计报表")

            col1, col2 = st.columns(2)
            year = col1.number_input("年", value=datetime.now().year, min_value=2020, max_value=2030)
            month = col2.number_input("月", value=datetime.now().month, min_value=1, max_value=12)

            if st.button("📥 查询", type="primary"):
                r1 = requests.get(f"{API_BASE}/admin/stats/monthly",
                                  params={"year": year, "month": month},
                                  headers=api_headers())
                r2 = requests.get(f"{API_BASE}/admin/stats/department",
                                  params={"year": year, "month": month},
                                  headers=api_headers())
                r3 = requests.get(f"{API_BASE}/admin/stats/trend",
                                  params={"year": year},
                                  headers=api_headers())

                # --- 顶部汇总指标 ---
                cat_data = r1.json() if r1.status_code == 200 else []
                dept_data = r2.json() if r2.status_code == 200 else []
                trend_data = r3.json() if r3.status_code == 200 else []

                total_amt = sum(item.get("总金额") or 0 for item in cat_data)
                total_cnt = sum(item.get("申请数") or 0 for item in cat_data)
                dept_count = len(dept_data)

                c1, c2, c3 = st.columns(3)
                c1.metric(f"{year}年{month}月报销总额", f"¥ {total_amt:,.2f}")
                c2.metric("审批通过申请数", total_cnt)
                c3.metric("涉及部门数", dept_count)
                st.divider()

                # --- 图表区 ---
                row1_col1, row1_col2 = st.columns(2)

                with row1_col1:
                    st.subheader("📈 类别报销金额")
                    if cat_data:
                        df_cat = pd.DataFrame(cat_data)
                        df_cat.columns = ["类别", "申请数", "总金额"]
                        fig = px.bar(df_cat, x="类别", y="总金额", color="类别",
                                     text="总金额", title=f"{year}年{month}月各类别报销金额")
                        fig.update_traces(texttemplate="¥%{text:,.0f}", textposition="outside")
                        fig.update_layout(showlegend=False, height=350)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("暂无数据")

                with row1_col2:
                    st.subheader("🥧 类别占比")
                    if cat_data:
                        df_pie = pd.DataFrame(cat_data)
                        df_pie.columns = ["类别", "申请数", "总金额"]
                        fig = px.pie(df_pie, names="类别", values="总金额",
                                     title="报销金额类别分布", hole=0.4)
                        fig.update_layout(height=350)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("暂无数据")

                row2_col1, row2_col2 = st.columns(2)

                with row2_col1:
                    st.subheader("🏢 部门报销对比")
                    if dept_data:
                        df_dept = pd.DataFrame(dept_data)
                        df_dept.columns = ["部门", "申请数", "总金额"]
                        fig = px.bar(df_dept, x="部门", y="总金额", color="部门",
                                     text="总金额", title=f"{year}年{month}月各部门报销金额")
                        fig.update_traces(texttemplate="¥%{text:,.0f}", textposition="outside")
                        fig.update_layout(showlegend=False, height=350)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("暂无数据")

                with row2_col2:
                    st.subheader("📅 月度报销趋势")
                    if trend_data:
                        df_trend = pd.DataFrame(trend_data)
                        df_trend.columns = ["月份", "申请数", "总金额"]
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=df_trend["月份"], y=df_trend["总金额"],
                            mode="lines+markers+text",
                            text=[f"¥{v:,.0f}" for v in df_trend["总金额"]],
                            textposition="top center",
                            name="报销金额",
                            line=dict(color="#636EFA", width=2),
                        ))
                        fig.update_layout(title=f"{year}年月度报销趋势", height=350,
                                          xaxis_title="月份", yaxis_title="金额（元）")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("暂无年度趋势数据")

                # --- 明细表格 ---
                st.divider()
                tab_cat, tab_dept = st.tabs(["📋 类别明细", "📋 部门明细"])
                with tab_cat:
                    if cat_data:
                        st.dataframe(pd.DataFrame(cat_data), use_container_width=True)
                    else:
                        st.info("暂无数据")
                with tab_dept:
                    if dept_data:
                        st.dataframe(pd.DataFrame(dept_data), use_container_width=True)
                    else:
                        st.info("暂无数据")

    # ---- 页面：智能问答 ----
    elif page == "🤖 智能问答":
        st.title("🤖 智能问答")
        st.caption("用自然语言查询报销数据，例如：「我这个月报销了多少？」「哪个部门花费最多？」")

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # 显示历史消息
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # 输入框
        user_input = st.chat_input("请输入您的问题...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)

            with st.chat_message("assistant"):
                with st.spinner("思考中..."):
                    resp = requests.post(
                        f"{API_BASE}/agent/chat",
                        json={"question": user_input},
                        headers=api_headers(),
                    )
                if resp.status_code == 200:
                    answer = resp.json().get("answer", "暂无回答")
                else:
                    answer = f"⚠️ 服务暂不可用（{resp.status_code}），智能问答功能正在开发中"
                st.write(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})

        if st.button("🗑️ 清空对话"):
            st.session_state.chat_history = []
            st.rerun()


# ---- 路由 ----
if st.session_state.token is None:
    login_page()
else:
    main_app()
