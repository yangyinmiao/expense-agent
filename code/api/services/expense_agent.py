"""
报销问答 Agent
使用 LangChain + 自定义工具，支持自然语言查询报销数据
"""
import json
from datetime import datetime
from typing import Optional

from langchain_classic.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from config.settings import settings


def build_expense_agent(db: Session, current_user_id: int, current_user_role: str):
    """构建报销查询 Agent，绑定当前用户上下文"""

    # ---------- Tools ----------

    @tool
    def get_my_claims_summary() -> str:
        """查询当前用户的报销申请汇总：总数、各状态数量、总金额"""
        from api.models.claim import ExpenseClaim, ClaimStatus
        from api.models.invoice import Invoice

        claims = db.query(ExpenseClaim).filter(ExpenseClaim.user_id == current_user_id).all()
        if not claims:
            return "您目前没有任何报销申请。"

        status_map = {
            "draft": "草稿", "pending": "待审批",
            "manager_approved": "主管已批", "finance_approved": "财务已批",
            "rejected": "已驳回", "paid": "已打款",
        }
        status_count = {}
        for c in claims:
            s = status_map.get(c.status.value if hasattr(c.status, "value") else c.status, c.status)
            status_count[s] = status_count.get(s, 0) + 1

        # 统计已通过总金额
        approved = db.query(func.sum(Invoice.total)) \
            .join(ExpenseClaim, ExpenseClaim.invoice_id == Invoice.id) \
            .filter(
                ExpenseClaim.user_id == current_user_id,
                ExpenseClaim.status.in_(["finance_approved", "paid"]),
            ).scalar() or 0

        result = f"您共有 {len(claims)} 条报销申请：\n"
        for s, cnt in status_count.items():
            result += f"  · {s}：{cnt} 条\n"
        result += f"已通过/打款总金额：¥{approved:.2f}"
        return result

    @tool
    def get_monthly_summary(year: int, month: int) -> str:
        """查询某年某月的报销统计（所有人），需要 year 和 month 参数。管理员/财务专用。"""
        if current_user_role not in ("admin", "finance"):
            return "抱歉，此查询需要管理员或财务权限。"

        from api.models.claim import ExpenseClaim, ClaimStatus
        from api.models.invoice import Invoice
        from api.models.user import User

        results = (
            db.query(Invoice.category, func.count(ExpenseClaim.id), func.sum(Invoice.total))
            .join(ExpenseClaim, ExpenseClaim.invoice_id == Invoice.id)
            .filter(
                ExpenseClaim.status == "finance_approved",
                extract("year", ExpenseClaim.submitted_at) == year,
                extract("month", ExpenseClaim.submitted_at) == month,
            )
            .group_by(Invoice.category)
            .all()
        )

        if not results:
            return f"{year}年{month}月暂无已审批通过的报销记录。"

        total = sum(r[2] or 0 for r in results)
        lines = [f"{year}年{month}月报销统计（已审批）："]
        for cat, cnt, amt in results:
            lines.append(f"  · {cat or '未分类'}：{cnt} 笔，¥{(amt or 0):.2f}")
        lines.append(f"合计：¥{total:.2f}")
        return "\n".join(lines)

    @tool
    def get_top_spenders(year: int, month: int, top_n: int = 5) -> str:
        """查询某月报销金额最高的员工排名，需要 year 和 month 参数。管理员/财务专用。"""
        if current_user_role not in ("admin", "finance"):
            return "抱歉，此查询需要管理员或财务权限。"

        from api.models.claim import ExpenseClaim
        from api.models.invoice import Invoice
        from api.models.user import User

        results = (
            db.query(User.name, func.sum(Invoice.total).label("total_amt"))
            .join(ExpenseClaim, ExpenseClaim.user_id == User.id)
            .join(Invoice, Invoice.id == ExpenseClaim.invoice_id)
            .filter(
                ExpenseClaim.status.in_(["finance_approved", "paid"]),
                extract("year", ExpenseClaim.submitted_at) == year,
                extract("month", ExpenseClaim.submitted_at) == month,
            )
            .group_by(User.name)
            .order_by(func.sum(Invoice.total).desc())
            .limit(top_n)
            .all()
        )

        if not results:
            return f"{year}年{month}月暂无数据。"

        lines = [f"{year}年{month}月报销金额 TOP{top_n}："]
        for i, (name, amt) in enumerate(results, 1):
            lines.append(f"  {i}. {name}：¥{(amt or 0):.2f}")
        return "\n".join(lines)

    @tool
    def get_pending_claims_count() -> str:
        """查询当前待审批的报销申请数量。主管/财务/管理员可用。"""
        if current_user_role not in ("admin", "finance", "manager"):
            return "抱歉，此查询需要审批权限。"

        from api.models.claim import ExpenseClaim, ClaimStatus
        pending_map = {
            "manager": ["pending"],
            "finance": ["manager_approved"],
            "admin": ["pending", "manager_approved"],
        }
        statuses = pending_map.get(current_user_role, [])
        count = db.query(func.count(ExpenseClaim.id)).filter(
            ExpenseClaim.status.in_(statuses)
        ).scalar()
        return f"当前待您审批的申请共 {count} 条。"

    @tool
    def get_expense_rules() -> str:
        """查询当前报销规则，包括各类别单次上限。"""
        return json.dumps({
            "餐饮": "单次上限 ¥2,000，月度预警 ¥3,000",
            "交通": "单次上限 ¥2,000，月度预警 ¥10,000",
            "住宿": "单次上限 ¥800/晚，月度预警 ¥5,000",
            "办公用品": "单次上限 ¥20,000，月度预警 ¥100,000",
            "其他": "单次上限 ¥500，月度预警 ¥3,000",
        }, ensure_ascii=False, indent=2)

    @tool
    def get_my_monthly_spending(year: int, month: int) -> str:
        """查询当前用户某月的报销金额合计，需要 year 和 month 参数。"""
        from api.models.claim import ExpenseClaim
        from api.models.invoice import Invoice

        total = db.query(func.sum(Invoice.total)) \
            .join(ExpenseClaim, ExpenseClaim.invoice_id == Invoice.id) \
            .filter(
                ExpenseClaim.user_id == current_user_id,
                extract("year", ExpenseClaim.submitted_at) == year,
                extract("month", ExpenseClaim.submitted_at) == month,
            ).scalar() or 0

        return f"您在 {year}年{month}月 共提交报销金额（含所有状态）：¥{total:.2f}"

    # ---------- LLM & Prompt ----------
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
        openai_api_base=settings.OPENAI_BASE_URL,
        temperature=0,
    )

    now = datetime.now()
    system_prompt = f"""你是财务报销系统的智能助手，帮助用户查询报销数据。
今天是 {now.year}年{now.month}月{now.day}日。
当前用户角色：{current_user_role}。

回答规则：
- 用中文简洁回答
- 如果需要查询数据，请调用工具获取
- 不要编造数据，数据必须来自工具返回值
- 如果用户问的是「这个月」「本月」，默认是 {now.year}年{now.month}月
- 如果用户问的是「上个月」，默认是 {now.year}年{now.month - 1 if now.month > 1 else 12}月
- 员工只能查自己的数据，财务/管理员可查全公司数据
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    tools = [
        get_my_claims_summary,
        get_monthly_summary,
        get_top_spenders,
        get_pending_claims_count,
        get_expense_rules,
        get_my_monthly_spending,
    ]

    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=5)
