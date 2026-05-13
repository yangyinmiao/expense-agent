"""
发票信息提取模块
支持：图片（JPG/PNG）、PDF
"""
import os
import base64
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://goods.fatrabbits.shop:12788/v1"),
)


def encode_image(image_path: str) -> str:
    """将图片转为base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def extract_invoice_info(file_path: str) -> dict:
    """
    从发票图片中提取结构化信息
    返回: dict，包含金额、日期、类型、供应商等
    """
    suffix = Path(file_path).suffix.lower()

    if suffix in [".jpg", ".jpeg", ".png", ".webp"]:
        return _extract_from_image(file_path)
    elif suffix == ".pdf":
        return _extract_from_pdf(file_path)
    else:
        return {"error": f"不支持的文件格式: {suffix}"}


def _extract_from_image(image_path: str) -> dict:
    """用GPT-4o Vision提取发票信息"""
    b64 = encode_image(image_path)
    suffix = Path(image_path).suffix.lower().replace(".", "")
    media_type = "jpeg" if suffix == "jpg" else suffix

    prompt = """请仔细识别这张发票，提取以下信息并以JSON格式返回：
{
  "发票类型": "增值税专用发票/增值税普通发票/出租车票/餐饮发票/其他",
  "发票号码": "",
  "开票日期": "YYYY-MM-DD",
  "供应商名称": "",
  "购买方名称": "",
  "金额（不含税）": 0.00,
  "税额": 0.00,
  "价税合计": 0.00,
  "费用类别": "交通/餐饮/住宿/办公用品/其他",
  "备注": ""
}
如果某项信息无法识别，填null。只返回JSON，不要其他文字。"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{media_type};base64,{b64}"
                        },
                    },
                ],
            }
        ],
        max_tokens=500,
    )

    import json
    raw = response.choices[0].message.content.strip()
    # 去掉可能的```json```包裹
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw)
    except Exception:
        return {"raw_text": raw, "error": "JSON解析失败"}


def _extract_from_pdf(pdf_path: str) -> dict:
    """PDF转图片后提取（需要poppler）"""
    try:
        from pdf2image import convert_from_path
        import tempfile

        images = convert_from_path(pdf_path, first_page=1, last_page=1)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            images[0].save(tmp.name, "JPEG")
            return _extract_from_image(tmp.name)
    except Exception as e:
        return {"error": f"PDF处理失败: {str(e)}"}
