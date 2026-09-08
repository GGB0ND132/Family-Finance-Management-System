"""分类业务逻辑。

规则（`docs/详细设计.md` 第5节 + `docs/需求分析.md` FR-07/FR-08）：
- 管理员新增、编辑、删除自定义分类。
- 相同家庭、相同方向的现用（deleted_at IS NULL）分类不能重名。
- 已被流水或分类预算引用的分类不可物理删除，执行软删除（设置 deleted_at）。
"""

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ResourceNotFoundError
from app.modules.categories.models import Category
from app.modules.categories.repository import CategoryRepository


def create_category(
    db: Session,
    family_id: int,
    name: str,
    type_: str,
    icon: str | None = None,
    color: str | None = None,
) -> Category:
    """新增自定义分类。"""
    repo = CategoryRepository(db)

    # 同家庭同方向现用分类不可重名
    existing = repo.get_active_by_name(family_id, name, type_)
    if existing:
        raise ConflictError("同家庭同方向已存在同名分类")

    category = repo.create(
        Category(
            family_id=family_id,
            name=name,
            type=type_,
            icon=icon,
            color=color,
        )
    )
    db.commit()
    return category


def get_category(db: Session, category_id: int) -> Category:
    """获取单一分类（含已删除），否则 404。"""
    category = CategoryRepository(db).get_by_id(category_id)
    if not category:
        raise ResourceNotFoundError("分类不存在")
    return category


def update_category(db: Session, category_id: int, **kwargs) -> Category:
    """编辑分类名称、图标或颜色。

    若修改名称，需校验同家庭同方向的现用分类不重名。
    """
    category = get_category(db, category_id)
    repo = CategoryRepository(db)

    name = kwargs.get("name")
    if name is not None and name != category.name:
        existing = repo.get_active_by_name(category.family_id, name, category.type)
        if existing and existing.id != category_id:
            raise ConflictError("同家庭同方向已存在同名分类")

    for key, value in kwargs.items():
        if value is not None and hasattr(category, key):
            setattr(category, key, value)

    db.flush()
    return category


def delete_category(db: Session, category_id: int) -> None:
    """删除分类。

    - 无流水/分类预算引用时物理删除。
    - 有引用时软删除（设置 deleted_at），保留历史引用。
    """
    category = get_category(db, category_id)
    if category.deleted_at is not None:
        raise ResourceNotFoundError("分类已被删除")

    repo = CategoryRepository(db)

    has_refs = repo.has_transactions(category_id) or repo.has_category_budgets(category_id)
    if has_refs:
        # 软删除：保留历史引用，不再用于新流水或预算
        from datetime import datetime, timezone

        category.deleted_at = datetime.now(timezone.utc)
        db.flush()
    else:
        db.delete(category)
        db.flush()