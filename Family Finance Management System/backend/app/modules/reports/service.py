"""报表业务逻辑：聚合查询入口。"""

from sqlalchemy.orm import Session

from app.modules.reports.repository import ReportRepository


def get_personal_daily(
    db: Session, family_id: int, beneficiary_member_id: int, date: str
) -> dict:
    return ReportRepository(db).personal_daily(family_id, beneficiary_member_id, date)


def get_personal_summary(
    db: Session,
    family_id: int,
    beneficiary_member_id: int,
    from_date: str,
    to_date: str,
) -> dict:
    return ReportRepository(db).personal_summary(
        family_id, beneficiary_member_id, from_date, to_date
    )


def get_personal_trend(
    db: Session,
    family_id: int,
    beneficiary_member_id: int,
    from_month: str,
    to_month: str,
) -> list[dict]:
    return ReportRepository(db).personal_trend(
        family_id, beneficiary_member_id, from_month, to_month
    )


def get_personal_by_category(
    db: Session, family_id: int, beneficiary_member_id: int, month: str
) -> list[dict]:
    return ReportRepository(db).personal_by_category(
        family_id, beneficiary_member_id, month
    )


def get_family_summary(db: Session, family_id: int, month: str) -> dict:
    return ReportRepository(db).family_summary(family_id, month)


def get_family_trend(
    db: Session, family_id: int, from_month: str, to_month: str
) -> list[dict]:
    return ReportRepository(db).family_trend(family_id, from_month, to_month)


def get_family_by_category(db: Session, family_id: int, month: str) -> list[dict]:
    return ReportRepository(db).family_by_category(family_id, month)


def get_family_by_member(db: Session, family_id: int, month: str) -> list[dict]:
    return ReportRepository(db).family_by_member(family_id, month)