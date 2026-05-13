"""
财务报销 Agent - Streamlit Web 界面 v4
蓝白专业配色，扁平化设计
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

st.set_page_config(
    page_title="智报 · 财务报销系统",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 全局样式注入
# ============================================================
st.markdown("""
<style>
/* ---- 全局字体 & 背景 ---- */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #F0F4FA;
    font-family: "PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif;
}

/* ---- 隐藏默认 Streamlit 元素 ---- */
#MainMenu, footer, header { visibility: hidden; }
/* keep toolbar so sidebar expand/collapse control remains visible */

/* ---- 侧边栏 ---- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1A3A6B 0%, #1E4D9E 100%);
    border-right: none;
}
[data-testid="stSidebar"] * { color: #E8EFF9 !important; }
[data-testid="stSidebar"] .stRadio label {
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.2s;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,0.12) !important;
}
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15) !important; }
[data-testid="stSidebar"] .stButton button {
    background: rgba(255,255,255,0.1) !important;
    color: #E8EFF9 !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    border-radius: 6px;
    width: 100%;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(255,255,255,0.2) !important;
}

/* 当侧栏收起时，显示一个悬浮展开按钮（兼容不同 Streamlit 版本） */
button[title="Show sidebar"], button[title="显示侧边栏"] {
    position: fixed !important;
    left: 12px !important;
    top: 84px !important;
    background: #1E4D9E !important;
    color: #fff !important;
    border-radius: 8px !important;
    padding: 8px 10px !important;
    box-shadow: 0 4px 12px rgba(30,77,158,0.18) !important;
    border: none !important;
    z-index: 9999 !important;
}

/* ---- 主内容区 ---- */
[data-testid="stMainBlockContainer"] {
    padding: 2rem 2.5rem 2rem 2.5rem;
}

/* ---- 页面标题 ---- */
h1 { color: #1A3A6B !important; font-size: 1.65rem !important; font-weight: 700 !important; margin-bottom: 0.2rem !important; }
h2 { color: #1E4D9E !important; font-size: 1.2rem !important; font-weight: 600 !important; }
h3 { color: #1E4D9E !important; }

/* ---- 主按钮 ---- */
.stButton > button[kind="primary"] {
    background: #1E4D9E !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.45rem 1.4rem !important;
    font-weight: 600 !important;
    transition: background 0.2s !important;
}
.stButton > button[kind="primary"]:hover {
    background: #163D82 !important;
}
.stButton > button[kind="secondary"] {
    border: 1.5px solid #1E4D9E !important;
    color: #1E4D9E !important;
    border-radius: 6px !important;
    background: white !important;
}

/* ---- 卡片 ---- */
.card {
    background: white;
    border-radius: 10px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 1px 4px rgba(30,77,158,0.08);
    margin-bottom: 1rem;
}

/* ---- metric 卡片重写 ---- */
[data-testid="stMetric"] {
    background: white;
    border-radius: 10px;
    padding: 1rem 1.25rem !important;
    box-shadow: 0 1px 4px rgba(30,77,158,0.08);
    border-left: 4px solid #1E4D9E;
}
[data-testid="stMetricLabel"] { color: #6B7A99 !important; font-size: 0.82rem !important; }
[data-testid="stMetricValue"] { color: #1A3A6B !important; font-size: 1.6rem !important; font-weight: 700 !important; }

/* ---- expander ---- */
[data-testid="stExpander"] {
    background: white !important;
    border: 1px solid #E0E8F4 !important;
    border-radius: 8px !important;
    margin-bottom: 0.5rem !important;
    box-shadow: none !important;
}
[data-testid="stExpanderToggleIcon"] { color: #1E4D9E !important; }

/* ---- 表单输入 ---- */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] select {
    border: 1.5px solid #D0DAEA !important;
    border-radius: 6px !important;
    background: #FAFCFF !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #1E4D9E !important;
    box-shadow: 0 0 0 2px rgba(30,77,158,0.12) !important;
}

/* ---- file uploader ---- */
[data-testid="stFileUploader"] {
    border: 2px dashed #B8CCE8 !important;
    border-radius: 8px !important;
    background: #F7FAFF !important;
}

/* ---- tab ---- */
[data-testid="stTabs"] [role="tab"] {
    color: #6B7A99 !important;
    font-weight: 500;
    border-bottom: 2px solid transparent;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #1E4D9E !important;
    border-bottom: 2px solid #1E4D9E !important;
    font-weight: 700;
}

/* ---- dataframe ---- */
[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }

/* ---- 状态徽章 ---- */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
}
.badge-pending  { background: #FFF3CD; color: #856404; }
.badge-approved { background: #D1FAE5; color: #065F46; }
.badge-rejected { background: #FEE2E2; color: #991B1B; }
.badge-draft    { background: #EEF2FF; color: #3730A3; }

/* ---- 分割线 ---- */
hr { border-color: #E0E8F4 !important; }

/* ---- success / error / info ---- */
[data-testid="stAlert"] { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Session State
# ============================================================
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None


def api_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


def status_badge(status: str) -> str:
    mapping = {
        "draft":            ('<span class="badge badge-draft">📝 草稿</span>', "草稿"),
        "pending":          ('<span class="badge badge-pending">⏳ 待审批</span>', "待审批"),
        "manager_approved": ('<span class="badge badge-approved">👍 主管已批</span>', "主管已批"),
        "finance_approved": ('<span class="badge badge-approved">✅ 财务已批</span>', "财务已批"),
        "rejected":         ('<span class="badge badge-rejected">❌ 已驳回</span>', "已驳回"),
        "paid":             ('<span class="badge badge-approved">💰 已打款</span>', "已打款"),
    }
    return mapping.get(status, (status, status))


# ============================================================
# 登录页
# ============================================================
def login_page():
    col_l, col_m, col_r = st.columns([1.2, 1, 1.2])
    with col_m:
        st.markdown("""
        <div style="text-align:center; padding: 2.5rem 0 1.5rem 0;">
            <div style="font-size:3rem;">🧾</div>
            <div style="font-size:1.6rem; font-weight:800; color:#1A3A6B; margin-top:0.4rem;">智报</div>
            <div style="font-size:0.9rem; color:#6B7A99; margin-top:0.2rem;">企业财务报销管理系统</div>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["🔑  登 录", "📝  注 册"])

        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("login_form"):
                email = st.text_input("用户名 / 邮箱", placeholder="请输入用户名或邮箱")
                password = st.text_input("密码", type="password", placeholder="请输入密码")
                submitted = st.form_submit_button("登 录", type="primary", use_container_width=True)
            if submitted:
                resp = requests.post(f"{API_BASE}/auth/login",
                                     data={"username": email, "password": password})
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.user = data["user"]
                    st.rerun()
                else:
                    st.error(resp.json().get("detail", "登录失败，请检查账号密码"))

            st.markdown("""
            <div style="margin-top:1rem; padding:0.8rem 1rem; background:#EEF4FF;
                        border-radius:8px; font-size:0.8rem; color:#4A6FA5;">
            <b>测试账号（密码均为 test123456）</b><br>
            员工小李 · 主管张经理 · 财务王姐 · 管理员Admin
            </div>
            """, unsafe_allow_html=True)

        with tab_register:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("register_form"):
                name = st.text_input("姓名", placeholder="请输入真实姓名")
                email_r = st.text_input("邮箱", key="reg_email", placeholder="name@company.com")
                password_r = st.text_input("密码", type="password", key="reg_pwd", placeholder="至少6位")
                department = st.text_input("部门", placeholder="如：研发部、财务部")
                role = st.selectbox("角色", ["employee", "manager", "finance", "admin"],
                                    format_func=lambda x: {"employee":"员工","manager":"主管",
                                                            "finance":"财务","admin":"管理员"}[x])
                submitted_r = st.form_submit_button("注 册", use_container_width=True)
            if submitted_r:
                resp = requests.post(f"{API_BASE}/auth/register", json={
                    "name": name, "email": email_r, "password": password_r,
                    "department": department, "role": role,
                })
                if resp.status_code == 200:
                    st.success("✅ 注册成功，请切换至登录页")
                else:
                    st.error(resp.json().get("detail", "注册失败"))


# ============================================================
# 主应用
# ============================================================
def main_app():
    user = st.session_state.user
    role = user.get("role", "employee")
    role_label = {"employee": "员工", "manager": "主管", "finance": "财务", "admin": "管理员"}.get(role, role)

    # ---- 侧边栏 ----
    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 1rem 0 0.5rem 0;">
            <div style="font-size:1.1rem; font-weight:700;">{user['name']}</div>
            <div style="font-size:0.8rem; opacity:0.7; margin-top:2px;">{role_label}</div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        pages = ["📤 提交报销", "📦 批量上传", "📋 我的申请", "✅ 待审批", "📊 统计报表", "🤖 智能问答"]
        page = st.radio("", pages, label_visibility="collapsed")

        st.divider()
        if st.button("退出登录"):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()

        st.markdown("""
        <div style="position:absolute; bottom:1.5rem; left:1rem;
                    font-size:0.72rem; opacity:0.45;">
            智报 v4.0 · Expense Agent
        </div>
        """, unsafe_allow_html=True)

    # ============================================================
    # 页面：提交报销
    # ============================================================
    if page == "📤 提交报销":
        st.title("📤 提交报销")
        st.markdown("<p style='color:#6B7A99;margin-top:-0.5rem;'>上传发票，AI 自动识别并完成规则校验</p>", unsafe_allow_html=True)
        st.divider()

        col_left, col_right = st.columns([1, 1.1], gap="large")

        with col_left:
            uploaded = st.file_uploader("上传发票文件", type=["jpg", "jpeg", "png", "pdf"],
                                        label_visibility="collapsed")
            description = st.text_area("报销说明（可选）", placeholder="简要描述报销用途，如：5月研发部团队餐饮",
                                       height=100)
            btn_col, _ = st.columns([1, 2])
            with btn_col:
                submit_btn = st.button("🔍 识别并提交", type="primary", disabled=not uploaded,
                                       use_container_width=True)

        with col_right:
            if uploaded:
                st.markdown("**预览**")
                if uploaded.type.startswith("image"):
                    st.image(uploaded, use_container_width=True)
                else:
                    st.markdown(f"""
                    <div class="card" style="text-align:center; padding:2rem; color:#6B7A99;">
                        📄 {uploaded.name}
                    </div>
                    """, unsafe_allow_html=True)

        if submit_btn:
            with st.spinner("AI 正在识别发票..."):
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

                st.divider()
                st.subheader("识别结果")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("价税合计", f"¥{info.get('价税合计', 'N/A')}")
                c2.metric("费用类别", info.get("费用类别", "N/A"))
                c3.metric("开票日期", info.get("开票日期", "N/A"))
                c4.metric("供应商", info.get("供应商名称", "N/A"))

                with st.expander("查看完整识别数据"):
                    st.json(info)

                st.markdown("<br>", unsafe_allow_html=True)
                if validation["通过"]:
                    st.success(f"✅ 规则校验通过 — {validation['建议']}")
                    claim_resp = requests.post(
                        f"{API_BASE}/claims/",
                        json={"invoice_id": invoice_id, "description": description},
                        headers=api_headers(),
                    )
                    if claim_resp.status_code == 200:
                        claim_id = claim_resp.json()["claim_id"]
                        requests.post(f"{API_BASE}/claims/{claim_id}/submit", headers=api_headers())
                        st.success(f"🎉 报销申请已提交！申请编号：**#{claim_id}**，请等待主管审批")
                else:
                    st.error("❌ 规则校验未通过，请修正后重新提交")
                    for issue in validation["问题列表"]:
                        st.warning(f"• {issue}")

    # ============================================================
    # 页面：批量上传
    # ============================================================
    elif page == "📦 批量上传":
        st.title("📦 批量上传发票")
        st.markdown("<p style='color:#6B7A99;margin-top:-0.5rem;'>一次最多上传 10 张，并发识别，识别通过后自动提交申请</p>",
                    unsafe_allow_html=True)
        st.divider()

        uploaded_files = st.file_uploader(
            "选择发票文件（可多选）",
            type=["jpg", "jpeg", "png", "pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        description = st.text_input("统一报销说明（可选）", placeholder="如：Q2 差旅费用报销")

        if uploaded_files:
            st.markdown(f"<p style='color:#1E4D9E;font-weight:600;'>已选择 {len(uploaded_files)} 个文件</p>",
                        unsafe_allow_html=True)

        if uploaded_files and st.button("🚀 批量识别并提交", type="primary"):
            if len(uploaded_files) > 10:
                st.error("每次最多上传 10 张，请分批上传")
            else:
                with st.spinner(f"正在并发识别 {len(uploaded_files)} 张发票..."):
                    files_payload = [("files", (f.name, f.getvalue())) for f in uploaded_files]
                    resp = requests.post(f"{API_BASE}/invoices/batch-upload",
                                         files=files_payload, headers=api_headers())

                if resp.status_code != 200:
                    st.error(f"上传失败：{resp.json().get('detail', resp.text)}")
                else:
                    data = resp.json()
                    s, f_cnt = data["success_count"], data["failed_count"]
                    c1, c2, c3 = st.columns(3)
                    c1.metric("提交总数", data["total"])
                    c2.metric("识别成功", s)
                    c3.metric("识别失败", f_cnt)
                    st.divider()

                    for item in data["results"]:
                        if item["success"]:
                            info = item["info"]
                            with st.expander(f"✅  {item['filename']}  ·  {info.get('供应商名称','—')}  ·  ¥{info.get('价税合计','—')}"):
                                cc1, cc2, cc3 = st.columns(3)
                                cc1.metric("价税合计", f"¥{info.get('价税合计','N/A')}")
                                cc2.metric("费用类别", info.get("费用类别", "N/A"))
                                cc3.metric("开票日期", info.get("开票日期", "N/A"))
                                v = item["validation"]
                                if v["通过"]:
                                    st.success(f"✅ {v['建议']}")
                                    claim_resp = requests.post(
                                        f"{API_BASE}/claims/",
                                        json={"invoice_id": item["invoice_id"], "description": description},
                                        headers=api_headers(),
                                    )
                                    if claim_resp.status_code == 200:
                                        cid = claim_resp.json()["claim_id"]
                                        requests.post(f"{API_BASE}/claims/{cid}/submit", headers=api_headers())
                                        st.info(f"已自动提交申请 #{cid}")
                                else:
                                    st.warning("⚠️ 校验未通过，请手动处理")
                                    for issue in v["问题列表"]:
                                        st.caption(f"• {issue}")
                        else:
                            with st.expander(f"❌  {item['filename']}  ·  失败"):
                                st.error(item.get("error", "未知错误"))

    # ============================================================
    # 页面：我的申请
    # ============================================================
    elif page == "📋 我的申请":
        st.title("📋 我的报销申请")
        st.markdown("<p style='color:#6B7A99;margin-top:-0.5rem;'>查看所有报销申请的状态与进度</p>",
                    unsafe_allow_html=True)
        st.divider()

        resp = requests.get(f"{API_BASE}/claims/my", headers=api_headers())
        if resp.status_code != 200:
            st.error("获取失败，请刷新重试")
        else:
            claims = resp.json()
            if not claims:
                st.markdown("""
                <div class="card" style="text-align:center;padding:3rem;color:#6B7A99;">
                    📭 暂无报销申请<br>
                    <small>点击「提交报销」上传第一张发票</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                # 顶部汇总
                total_amt = sum(c.get("total") or 0 for c in claims)
                pending_cnt = sum(1 for c in claims if c.get("status") == "pending")
                approved_cnt = sum(1 for c in claims if c.get("status") in ("finance_approved", "paid"))
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("申请总数", len(claims))
                c2.metric("待审批", pending_cnt)
                c3.metric("已通过", approved_cnt)
                c4.metric("累计金额", f"¥{total_amt:,.2f}")
                st.markdown("<br>", unsafe_allow_html=True)

                for c in claims:
                    badge_html, badge_text = status_badge(c.get("status", ""))
                    vendor = c.get("vendor") or "—"
                    total = f"¥{c['total']}" if c.get("total") else "—"
                    date = c.get("submitted_at", "")[:10] if c.get("submitted_at") else "—"
                    label = f"#{c['id']}  {vendor}  {total}  {date}"
                    with st.expander(label):
                        d1, d2, d3, d4 = st.columns(4)
                        d1.markdown(f"**状态**<br>{badge_html}", unsafe_allow_html=True)
                        d2.markdown(f"**费用类别**<br>{c.get('category') or '—'}", unsafe_allow_html=True)
                        d3.markdown(f"**发票日期**<br>{c.get('invoice_date') or '—'}", unsafe_allow_html=True)
                        d4.markdown(f"**报销说明**<br>{c.get('description') or '—'}", unsafe_allow_html=True)
                        if c.get("status") == "rejected":
                            st.error("此申请已被驳回，请根据反馈重新提交")

    # ============================================================
    # 页面：待审批
    # ============================================================
    elif page == "✅ 待审批":
        if role not in ("manager", "finance", "admin"):
            st.warning("此页面仅限主管 / 财务 / 管理员使用")
        else:
            st.title("✅ 待审批列表")
            st.markdown("<p style='color:#6B7A99;margin-top:-0.5rem;'>审核员工提交的报销申请</p>",
                        unsafe_allow_html=True)
            st.divider()

            resp = requests.get(f"{API_BASE}/claims/pending", headers=api_headers())
            if resp.status_code != 200:
                st.error("获取失败")
            else:
                claims = resp.json()
                if not claims:
                    st.markdown("""
                    <div class="card" style="text-align:center;padding:3rem;color:#6B7A99;">
                        🎉 暂无待审批申请
                    </div>
                    """, unsafe_allow_html=True)

                for c in claims:
                    vendor = c.get("vendor") or "未知供应商"
                    total = f"¥{c['total']}" if c.get("total") else "—"
                    category = c.get("category") or "—"
                    date = c.get("invoice_date") or "—"
                    label = f"申请 #{c['id']}  ·  {vendor}  ·  {total}  ·  {category}"

                    with st.expander(label):
                        d1, d2, d3, d4 = st.columns(4)
                        d1.markdown(f"**申请人 ID**<br>{c['user_id']}", unsafe_allow_html=True)
                        d2.markdown(f"**发票日期**<br>{date}", unsafe_allow_html=True)
                        d3.markdown(f"**费用类别**<br>{category}", unsafe_allow_html=True)
                        d4.markdown(f"**说明**<br>{c.get('description') or '—'}", unsafe_allow_html=True)

                        st.markdown("<br>", unsafe_allow_html=True)
                        col_a, col_b, col_c = st.columns([2.5, 0.8, 0.8])
                        comment = col_a.text_input("审批备注", key=f"comment_{c['id']}",
                                                    placeholder="可填写备注或驳回原因")
                        with col_b:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("✅ 通过", key=f"approve_{c['id']}", type="primary",
                                         use_container_width=True):
                                r = requests.post(f"{API_BASE}/claims/{c['id']}/approve",
                                                  json={"comment": comment}, headers=api_headers())
                                if r.status_code == 200:
                                    st.success("已通过")
                                    st.rerun()
                                else:
                                    st.error(r.json().get("detail"))
                        with col_c:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("❌ 驳回", key=f"reject_{c['id']}", use_container_width=True):
                                r = requests.post(f"{API_BASE}/claims/{c['id']}/reject",
                                                  json={"comment": comment or "不符合报销规定"},
                                                  headers=api_headers())
                                if r.status_code == 200:
                                    st.error("已驳回")
                                    st.rerun()
                                else:
                                    st.error(r.json().get("detail"))

    # ============================================================
    # 页面：统计报表
    # ============================================================
    elif page == "📊 统计报表":
        if role not in ("finance", "admin"):
            st.warning("此页面仅限财务 / 管理员使用")
        else:
            st.title("📊 统计报表")
            st.markdown("<p style='color:#6B7A99;margin-top:-0.5rem;'>查看报销数据汇总与趋势分析</p>",
                        unsafe_allow_html=True)
            st.divider()

            col_y, col_m, col_btn = st.columns([0.8, 0.8, 1.5])
            year = col_y.number_input("年份", value=datetime.now().year, min_value=2020, max_value=2030,
                                       label_visibility="visible")
            month = col_m.number_input("月份", value=datetime.now().month, min_value=1, max_value=12,
                                        label_visibility="visible")
            col_btn.markdown("<br>", unsafe_allow_html=True)
            query_btn = col_btn.button("📥 查询报表", type="primary")

            if query_btn:
                r1 = requests.get(f"{API_BASE}/admin/stats/monthly",
                                   params={"year": year, "month": month}, headers=api_headers())
                r2 = requests.get(f"{API_BASE}/admin/stats/department",
                                   params={"year": year, "month": month}, headers=api_headers())
                r3 = requests.get(f"{API_BASE}/admin/stats/trend",
                                   params={"year": year}, headers=api_headers())

                cat_data   = r1.json() if r1.status_code == 200 else []
                dept_data  = r2.json() if r2.status_code == 200 else []
                trend_data = r3.json() if r3.status_code == 200 else []

                total_amt = sum(i.get("总金额") or 0 for i in cat_data)
                total_cnt = sum(i.get("申请数") or 0 for i in cat_data)

                # 顶部指标
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("当月报销总额", f"¥{total_amt:,.2f}")
                m2.metric("审批通过笔数", total_cnt)
                m3.metric("涉及部门", len(dept_data))
                m4.metric("统计范围", f"{year}年{month}月")
                st.markdown("<br>", unsafe_allow_html=True)

                BLUE_PALETTE = ["#1E4D9E","#2E6FD8","#5B9BD5","#89C4E1","#B8DCF0","#D6EEF8"]

                row1_c1, row1_c2 = st.columns(2, gap="medium")
                with row1_c1:
                    if cat_data:
                        df = pd.DataFrame(cat_data)
                        df.columns = ["类别", "申请数", "总金额"]
                        fig = px.bar(df, x="类别", y="总金额", color="类别",
                                     color_discrete_sequence=BLUE_PALETTE,
                                     text="总金额", title=f"{year}/{month} 各类别报销金额")
                        fig.update_traces(texttemplate="¥%{text:,.0f}", textposition="outside",
                                          marker_line_width=0)
                        fig.update_layout(showlegend=False, height=320, plot_bgcolor="white",
                                          paper_bgcolor="white", margin=dict(t=40,b=20,l=20,r=20),
                                          font_color="#1A3A6B")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("暂无类别数据")

                with row1_c2:
                    if cat_data:
                        df = pd.DataFrame(cat_data)
                        df.columns = ["类别", "申请数", "总金额"]
                        fig = px.pie(df, names="类别", values="总金额",
                                     color_discrete_sequence=BLUE_PALETTE,
                                     title="报销类别占比", hole=0.45)
                        fig.update_layout(height=320, paper_bgcolor="white",
                                          margin=dict(t=40,b=20,l=20,r=20),
                                          font_color="#1A3A6B",
                                          legend=dict(orientation="v", x=1, y=0.5))
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("暂无数据")

                row2_c1, row2_c2 = st.columns(2, gap="medium")
                with row2_c1:
                    if dept_data:
                        df = pd.DataFrame(dept_data)
                        df.columns = ["部门", "申请数", "总金额"]
                        fig = px.bar(df, x="部门", y="总金额", color="部门",
                                     color_discrete_sequence=BLUE_PALETTE,
                                     text="总金额", title=f"{year}/{month} 各部门报销对比")
                        fig.update_traces(texttemplate="¥%{text:,.0f}", textposition="outside",
                                          marker_line_width=0)
                        fig.update_layout(showlegend=False, height=320, plot_bgcolor="white",
                                          paper_bgcolor="white", margin=dict(t=40,b=20,l=20,r=20),
                                          font_color="#1A3A6B")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("暂无部门数据")

                with row2_c2:
                    if trend_data:
                        df = pd.DataFrame(trend_data)
                        df.columns = ["月份", "申请数", "总金额"]
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=df["月份"], y=df["总金额"],
                            mode="lines+markers+text",
                            text=[f"¥{v:,.0f}" for v in df["总金额"]],
                            textposition="top center",
                            line=dict(color="#1E4D9E", width=2.5),
                            marker=dict(color="#1E4D9E", size=8),
                            fill="tozeroy",
                            fillcolor="rgba(30,77,158,0.07)",
                        ))
                        fig.update_layout(title=f"{year}年月度报销趋势", height=320,
                                          plot_bgcolor="white", paper_bgcolor="white",
                                          xaxis_title="月份", yaxis_title="金额（元）",
                                          margin=dict(t=40,b=20,l=20,r=20),
                                          font_color="#1A3A6B")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("暂无趋势数据")

                st.divider()
                tab1, tab2 = st.tabs(["📋 类别明细", "📋 部门明细"])
                with tab1:
                    if cat_data:
                        st.dataframe(pd.DataFrame(cat_data), use_container_width=True, hide_index=True)
                    else:
                        st.info("暂无数据")
                with tab2:
                    if dept_data:
                        st.dataframe(pd.DataFrame(dept_data), use_container_width=True, hide_index=True)
                    else:
                        st.info("暂无数据")

    # ============================================================
    # 页面：智能问答
    # ============================================================
    elif page == "🤖 智能问答":
        st.title("🤖 智能问答")
        st.markdown("<p style='color:#6B7A99;margin-top:-0.5rem;'>用自然语言查询报销数据，无需手动翻表格</p>",
                    unsafe_allow_html=True)
        st.divider()

        # 示例提示
        examples = ["我这个月报销了多少？", "现在有几条待审批？", "报销规则是什么？", "帮我看看我的申请状态"]
        st.markdown("**💡 你可以这样问：**")
        cols = st.columns(len(examples))
        for i, ex in enumerate(examples):
            with cols[i]:
                st.markdown(f"""
                <div style="background:#EEF4FF;border:1px solid #C5D8F5;border-radius:8px;
                            padding:0.5rem 0.75rem;font-size:0.82rem;color:#1E4D9E;
                            cursor:pointer;text-align:center;">{ex}</div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        user_input = st.chat_input("请输入您的问题，例如：我上个月餐饮报销了多少？")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)
            with st.chat_message("assistant"):
                with st.spinner("思考中..."):
                    resp = requests.post(f"{API_BASE}/agent/chat",
                                         json={"question": user_input},
                                         headers=api_headers())
                if resp.status_code == 200:
                    answer = resp.json().get("answer", "暂无回答")
                else:
                    answer = f"⚠️ 服务暂不可用（{resp.status_code}）"
                st.write(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})

        if st.session_state.chat_history:
            if st.button("🗑️ 清空对话"):
                st.session_state.chat_history = []
                st.rerun()


# ============================================================
if st.session_state.token is None:
    login_page()
else:
    main_app()
