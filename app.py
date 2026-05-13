"""
财务报销 Agent - Streamlit Web 界面
"""
import streamlit as st
import tempfile
import os
import json
from pathlib import Path

from extractor import extract_invoice_info
from validator import validate_expense

# ---- 页面配置 ----
st.set_page_config(
    page_title="财务报销 Agent",
    page_icon="🧾",
    layout="centered",
)

st.title("🧾 财务报销 Agent")
st.caption("上传发票图片或PDF，自动识别信息并校验是否符合报销规定")

# ---- 侧边栏：API配置 ----
with st.sidebar:
    st.header("⚙️ 配置")
    api_key = st.text_input("OpenAI API Key", type="password", help="输入你的API Key")
    base_url = st.text_input(
        "API Base URL（可选）",
        placeholder="https://goods.fatrabbits.shop:12788/v1",
        help="使用国内中转时填写",
    )
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    if base_url:
        os.environ["OPENAI_BASE_URL"] = base_url

    st.divider()
    st.markdown("**报销规则**")
    st.markdown("- 餐饮：≤ 500元")
    st.markdown("- 交通：≤ 2000元")
    st.markdown("- 住宿：≤ 800元/晚")
    st.markdown("- 办公用品：≤ 1000元")
    st.markdown("- 其他：≤ 500元")

# ---- 主区域 ----
uploaded_file = st.file_uploader(
    "上传发票",
    type=["jpg", "jpeg", "png", "pdf"],
    help="支持JPG、PNG图片和PDF文件",
)

if uploaded_file:
    # 显示上传的图片
    if uploaded_file.type.startswith("image"):
        st.image(uploaded_file, caption="已上传发票", use_column_width=True)

    # 保存到临时文件
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    # 提取按钮
    if st.button("🔍 开始识别并校验", type="primary"):
        if not os.environ.get("OPENAI_API_KEY"):
            st.error("请先在左侧填写 API Key")
        else:
            with st.spinner("正在识别发票信息..."):
                invoice_info = extract_invoice_info(tmp_path)

            if "error" in invoice_info:
                st.error(f"识别失败：{invoice_info['error']}")
            else:
                st.subheader("📋 识别结果")

                # 显示提取的信息
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("价税合计", f"¥ {invoice_info.get('价税合计', 'N/A')}")
                    st.metric("费用类别", invoice_info.get("费用类别", "N/A"))
                    st.metric("开票日期", invoice_info.get("开票日期", "N/A"))
                with col2:
                    st.metric("发票类型", invoice_info.get("发票类型", "N/A"))
                    st.metric("供应商", invoice_info.get("供应商名称", "N/A"))
                    st.metric("发票号码", invoice_info.get("发票号码", "N/A"))

                # 完整JSON（可展开）
                with st.expander("查看完整识别数据"):
                    st.json(invoice_info)

                st.divider()

                # 校验结果
                with st.spinner("正在校验报销规则..."):
                    validation = validate_expense(invoice_info)

                st.subheader("✅ 校验结果")
                if validation["通过"]:
                    st.success(f"**审核通过** — {validation['建议']}")
                else:
                    st.error("**审核不通过**")
                    for issue in validation["问题列表"]:
                        st.warning(f"• {issue}")
                    if validation["建议"]:
                        st.info(f"💡 建议：{validation['建议']}")

                # 生成报销摘要
                st.divider()
                st.subheader("📄 报销摘要")
                summary = f"""
**报销摘要**
- 发票类型：{invoice_info.get('发票类型', 'N/A')}
- 供应商：{invoice_info.get('供应商名称', 'N/A')}
- 开票日期：{invoice_info.get('开票日期', 'N/A')}
- 费用类别：{invoice_info.get('费用类别', 'N/A')}
- 报销金额：¥ {invoice_info.get('价税合计', 'N/A')}
- 审核状态：{'✅ 通过' if validation['通过'] else '❌ 不通过'}
"""
                st.markdown(summary)
                st.download_button(
                    "📥 下载摘要",
                    data=summary,
                    file_name="报销摘要.md",
                    mime="text/markdown",
                )

    # 清理临时文件
    try:
        os.unlink(tmp_path)
    except Exception:
        pass
