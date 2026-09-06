"""报表数据聚合（只读 SQL 查询）。"""

from sqlalchemy.orm import Session


class ReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def personal_daily(
        self, family_id: int, beneficiary_member_id: int, date: str
    ) -> dict:
        """个人日报：按受益成员聚合当日收入/支出。"""
        # TODO: 实现 SQL 聚合
        return {"date": date, "income": "0.00", "expense": "0.00", "balance": "0.00"}

    def personal_summary(
        self, family_id: int, beneficiary_member_id: int, from_date: str, to_date: str
    ) -> dict:
        """个人摘要。"""
        # TODO: 实现 SQL 聚合
        return {"income": "0.00", "expense": "0.00", "balance": "0.00"}

    def personal_trend(
        self, family_id: int, beneficiary_member_id: int, from_month: str, to_month: str
    ) -> list[dict]:
        """个人月度趋势。"""
        # TODO: 实现 SQL 聚合
        return []

    def personal_by_category(
        self, family_id: int, beneficiary_member_id: int, month: str
    ) -> list[dict]:
        """个人分类统计。"""
        # TODO: 实现 SQL 聚合
        return []

    def family_summary(self, family_id: int, month: str) -> dict:
        """家庭摘要。"""
        # TODO: 实现 SQL 聚合
        return {"income": "0.00", "expense": "0.00", "balance": "0.00"}

    def family_trend(
        self, family_id: int, from_month: str, to_month: str
    ) -> list[dict]:
        """家庭月度趋势。"""
        # TODO: 实现 SQL 聚合
        return []

    def family_by_category(self, family_id: int, month: str) -> list[dict]:
        """家庭分类统计。"""
        # TODO: 实现 SQL 聚合
        return []

    def family_by_member(self, family_id: int, month: str) -> list[dict]:
        """家庭成员统计。"""
        # TODO: 实现 SQL 聚合
        return []