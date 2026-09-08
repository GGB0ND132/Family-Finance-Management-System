"""分类路由。

权限（`docs/详细设计.md` 第5节）：
- 查询：成员可访问。
- 新增/编辑/删除：仅管理员可操作。
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.response import ApiResponse, PageData, ok
from app.core.deps import get_current_user, get_db, require_family_member
from app.core.exceptions import PermissionDeniedError
from app.modules.categories.repository import CategoryRepository
from app.modules.categories.schemas import (
    CategoryOut,
    CreateCategoryRequest,
    UpdateCategoryRequest,
)
from app.modules.categories.service import (
    create_category,
    delete_category,
    get_category,
    update_category,
)
from app.modules.families.models import FamilyMember
from app.modules.users.models import User

router = APIRouter(prefix="/categories", tags=["分类"])


@router.get("", summary="查询分类列表")
def list_categories(
    family_id: int = Query(..., description="家庭 ID"),
    type: str | None = Query(None, description="INCOME | EXPENSE"),
    include_deleted: bool = Query(False, description="是否包含已删除分类"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    member: FamilyMember = Depends(require_family_member),
):
    """查询可用或历史分类。成员权限即可访问。"""
    repo = CategoryRepository(db)
    categories = repo.list_by_family(
        family_id, type_=type, include_deleted=include_deleted
    )
    return ok(data=PageData(items=categories, page=page, page_size=page_size, total=len(categories)))


@router.post("", summary="新增分类", status_code=201)
def post_category(
    payload: CreateCategoryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """新增自定义分类（仅管理员）。"""
    # 校验家庭归属 + 管理员权限
    from app.modules.families.service import get_member
    member = get_member(db, payload.family_id, current_user.id)
    if not member:
        raise PermissionDeniedError("你不是该家庭的成员")
    if member.role != "ADMIN":
        raise PermissionDeniedError("需要管理员权限")

    category = create_category(
        db,
        family_id=payload.family_id,
        name=payload.name,
        type_=payload.type,
        icon=payload.icon,
        color=payload.color,
    )
    db.commit()
    return ok(data=category, message="分类创建成功")


@router.patch("/{category_id}", summary="编辑分类")
def patch_category(
    category_id: int,
    payload: UpdateCategoryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """编辑分类名称、图标或颜色（仅管理员）。"""
    from app.modules.families.service import get_member
    category = get_category(db, category_id)

    # 校验家庭归属 + 管理员权限
    member = get_member(db, category.family_id, current_user.id)
    if not member:
        raise PermissionDeniedError("无权操作该分类")
    if member.role != "ADMIN":
        raise PermissionDeniedError("需要管理员权限")

    category = update_category(db, category_id, **payload.model_dump(exclude_none=True))
    db.commit()
    return ok(data=category)


@router.delete("/{category_id}", status_code=204)
def delete_category_endpoint(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除分类（仅管理员）。

    - 未引用时物理删除。
    - 已被流水或预算引用时软删除（保留历史名称）。
    """
    from app.modules.families.service import get_member
    category = get_category(db, category_id)

    # 校验家庭归属 + 管理员权限
    member = get_member(db, category.family_id, current_user.id)
    if not member:
        raise PermissionDeniedError("无权操作该分类")
    if member.role != "ADMIN":
        raise PermissionDeniedError("需要管理员权限")

    delete_category(db, category_id)
    db.commit()
    # 204 No Content，不返回响应体