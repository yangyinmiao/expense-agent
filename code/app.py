"""
财务报销 Agent - Streamlit Web 界面 v2
对接 FastAPI 后端
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import requests
import tempfile
from pathlib import Path

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
            email = st.text_input("邮箱")
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
        page = st.radio("导航", ["📤 提交报销", "📋 我的申请", "✅ 待审批", "📊 统计报表"])
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
                    # 自动创建并提交申请
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
                for c in claims:
                    with st.expander(f"#{c['id']} — {status_emoji.get(c['status'], c['status'])} — {c.get('submitted_at', '')[:10]}"):
                        st.write(f"说明：{c.get('description', '-')}")
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
                    with st.expander(f"申请 #{c['id']} — 用户ID:{c['user_id']}"):
                        col1, col2 = st.columns(2)
                        comment = col1.text_input("备注", key=f"comment_{c['id']}")
                        if col1.button("✅ 通过", key=f"approve_{c['id']}"):
                            r = requests.post(f"{API_BASE}/claims/{c['id']}/approve",
                                              json={"comment": comment},
                                              headers=api_headers())
                            st.success("已通过" if r.status_code == 200 else r.json().get("detail"))
                            st.rerun()
                        if col2.button("❌ 驳回", key=f"reject_{c['id']}"):
                            r = requests.post(f"{API_BASE}/claims/{c['id']}/reject",
                                              json={"comment": comment or "不符合规定"},
                                              headers=api_headers())
                            st.error("已驳回" if r.status_code == 200 else r.json().get("detail"))
                            st.rerun()

    # ---- 页面：统计报表 ----
    elif page == "📊 统计报表":
        if role not in ("finance", "admin"):
            st.warning("此页面仅限财务/管理员使用")
        else:
            st.title("📊 统计报表")
            col1, col2 = st.columns(2)
            year = col1.number_input("年", value=2026, min_value=2020, max_value=2030)
            month = col2.number_input("月", value=5, min_value=1, max_value=12)

            if st.button("查询", type="primary"):
                r1 = requests.get(f"{API_BASE}/admin/stats/monthly",
                                  params={"year": year, "month": month},
                                  headers=api_headers())
                r2 = requests.get(f"{API_BASE}/admin/stats/department",
                                  params={"year": year, "month": month},
                                  headers=api_headers())

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("按类别")
                    if r1.status_code == 200 and r1.json():
                        st.dataframe(r1.json())
                    else:
                        st.info("暂无数据")
                with col2:
                    st.subheader("按部门")
                    if r2.status_code == 200 and r2.json():
                        st.dataframe(r2.json())
                    else:
                        st.info("暂无数据")


# ---- 路由 ----
if st.session_state.token is None:
    login_page()
else:
    main_app()
