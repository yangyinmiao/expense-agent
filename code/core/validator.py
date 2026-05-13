"""
报销规则校验模块
"""

# 报销规则配置（可以后续改成从配置文件读取）
RULES = {
    "餐饮": {
        "单次上限": 500,
        "说明": "餐饮单次报销不超过500元",
    },
    "交通": {
        "单次上限": 2000,
        "说明": "交通单次报销不超过2000元",
    },
    "住宿": {
        "单次上限": 800,
        "说明": "住宿单次报销每晚不超过800元",
    },
    "办公用品": {
        "单次上限": 2000,
        "说明": "办公用品单次报销不超过2000元",
    },
    "其他": {
        "单次上限": 500,
        "说明": "其他类别单次报销不超过500元",
    },
}

REQUIRED_FIELDS = ["发票类型", "开票日期", "价税合计", "费用类别"]


def validate_expense(invoice_info: dict) -> dict:
    """
    校验发票是否符合报销规则
    返回: {
        "通过": True/False,
        "问题列表": [...],
        "建议": "..."
    }
    """
    issues = []
    suggestions = []

    # 1. 检查必填字段
    for field in REQUIRED_FIELDS:
        if not invoice_info.get(field):
            issues.append(f"缺少必填信息：{field}")

    # 2. 检查金额上限
    category = invoice_info.get("费用类别", "其他")
    amount = invoice_info.get("价税合计", 0)
    rule = RULES.get(category, RULES["其他"])

    if amount and amount > rule["单次上限"]:
        issues.append(
            f"金额超限：{category}类别上限为{rule['单次上限']}元，"
            f"本次金额为{amount}元"
        )
        suggestions.append(f"请附上审批单或拆分报销")

    # 3. 检查发票类型合规性
    invoice_type = invoice_info.get("发票类型", "")
    if invoice_type and "收据" in invoice_type:
        issues.append("收据不能用于报销，需提供正规发票")

    passed = len(issues) == 0
    return {
        "通过": passed,
        "问题列表": issues,
        "建议": "；".join(suggestions) if suggestions else ("符合报销规定，可以提交" if passed else "请修正以上问题后重新提交"),
    }
