"""分类数据访问。"""

from sqlalchemy.orm import Session

from app.modules.categories.models import Category


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, category: Category) -> Category:
        self.db.add(category)
        self.db.flush()
        return category

    def get_by_id(self, category_id: int) -> Category | None:
        return self.db.get(Category, category_id)

    def list_by_family(
        self,
        family_id: int,
        type_: str | None = None,
        include_deleted: bool = False,
    ) -> list[Category]:
        q = self.db.query(Category).filter(Category.family_id == family_id)
        if type_:
            q = q.filter(Category.type == type_)
        if not include_deleted:
            q = q.filter(Category.deleted_at.is_(None))
        return q.all()

    def get_active_by_name(
        self, family_id: int, name: str, type_: str
    ) -> Category | None:
        """查询同家庭同方向未删除（deleted_at IS NULL）的分类，用于防重名。"""
        return (
            self.db.query(Category)
            .filter(
                Category.family_id == family_id,
                Category.name == name,
                Category.type == type_,
                Category.deleted_at.is_(None),
            )
            .first()
        )

    def has_transactions(self, category_id: int) -> bool:
        """检查是否有流水引用了该分类。"""
        from app.modules.transactions.models import Transaction

        return (
            self.db.query(Transaction)
            .filter(Transaction.category_id == category_id)
            .count()
            > 0
        )

    def has_category_budgets(self, category_id: int) -> bool:
        """检查是否有分类预算引用了该分类。"""
        from app.modules.budgets.models import CategoryBudget

        return (
            self.db.query(CategoryBudget)
            .filter(CategoryBudget.category_id == category_id)
            .count()
            > 0
        )