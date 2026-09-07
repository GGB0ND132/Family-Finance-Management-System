"""账户路由。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.response import ApiResponse, PageData, ok
from app.core.deps import get_current_user, get_db, require_family_member
from app.core.exceptions import PermissionDeniedError
from app.modules.accounts.schemas import (
    AccountOut,
    CreateAccountRequest,
    UpdateAccountRequest,
)
from app.modules.accounts.service import (
    _build_account_out,
    close_or_delete_account,
    create_account,
    get_account,
    get_account_with_owner,
    list_accounts,
    update_account,
)
from app.modules.families.models import FamilyMember
from app.modules.families.service import get_member
from app.modules.users.models import User

router = APIRouter(prefix="/accounts", tags=["账户"])


@router.get("", summary="查询账户列表")
def api_list_accounts(
    family_id: int = Query(..., description="家庭 ID"),
    scope: str = Query("family", description="personal | family"),
    owner_member_id: int | None = Query(None, description="按所属成员筛选（family 范围可选）"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    member: FamilyMember = Depends(require_family_member),
):
    """获取账户列表。

    - `scope=personal`: 后端强制过滤当前成员所属账户。
    - `scope=family`: 查询全部家庭成员账户，可按 `owner_member_id` 筛选。
    """
    repo_owner_id = owner_member_id
    if scope == "personal":
        # 个人范围：强制使用当前成员的 member_id，忽略前端传入的 owner_member_id
        repo_owner_id = member.id

    accounts, total = list_accounts(
        db,
        family_id=family_id,
        owner_member_id=repo_owner_id,
        page=page,
        page_size=page_size,
    )
    items = [_build_account_out(a) for a in accounts]
    return ok(data=PageData(items=items, page=page, page_size=page_size, total=total))


@router.post("", summary="创建账户", status_code=201)
def api_create_account(
    payload: CreateAccountRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建账户。

    权限：
    - 普通成员只能创建所属人为自己的账户。
    - 管理员可指定任意家庭成员作为账户所属人。
    """
    # 校验家庭归属
    member = get_member(db, payload.family_id, current_user.id)
    if not member:
        raise PermissionDeniedError("你不是该家庭的成员")

    # 权限检查：普通成员只能为自己创建账户
    if member.role != "ADMIN" and payload.owner_member_id != member.id:
        raise PermissionDeniedError("只能为自己创建账户")

    account = create_account(
        db,
        family_id=payload.family_id,
        owner_member_id=payload.owner_member_id,
        name=payload.name,
        type_=payload.type,
        initial_balance=payload.initial_balance,
        remark=payload.remark,
    )
    # 重新加载以获取完整的关联数据（所属成员及用户信息）
    account = get_account_with_owner(db, account.id)
    return ok(data=_build_account_out(account), message="账户创建成功")


@router.patch("/{account_id}", summary="更新账户")
def api_update_account(
    account_id: int,
    payload: UpdateAccountRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新账户名称、类型、所属人或备注。

    权限：
    - 账户所属人或管理员可编辑。
    - 编辑所属人不改变历史流水的资金归属人和录入人。
    """
    account = get_account_with_owner(db, account_id)

    # 校验家庭归属
    member = get_member(db, account.family_id, current_user.id)
    if not member:
        raise PermissionDeniedError("无权操作该账户")

    # 权限检查：所属人或管理员
    if member.role != "ADMIN" and account.owner_member_id != member.id:
        raise PermissionDeniedError("只能编辑自己的账户")

    # 若要修改所属人，校验目标成员
    if payload.owner_member_id is not None:
        if member.role != "ADMIN" and payload.owner_member_id != member.id:
            raise PermissionDeniedError("只能将账户转移给自己")

    account = update_account(
        db,
        account_id=account_id,
        family_id=account.family_id,
        name=payload.name,
        type_=payload.type,
        owner_member_id=payload.owner_member_id,
        remark=payload.remark,
    )
    # 重新加载以获取更新后的关联数据
    account = get_account_with_owner(db, account_id)
    return ok(data=_build_account_out(account))


@router.delete("/{account_id}", status_code=204)
def api_delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除或销户账户。

    规则：
    - 余额非 0.00 时拒绝操作（409）。
    - 余额为 0 且无历史流水/转账 → 物理删除。
    - 余额为 0 且有历史流水/转账 → 销户（设置 closed_at），保留历史记录。

    权限：
    - 账户所属人或管理员可操作。
    - 销户账户不计入当前资产，历史报表仍可查询。
    """
    account = get_account(db, account_id)

    # 校验家庭归属
    member = get_member(db, account.family_id, current_user.id)
    if not member:
        raise PermissionDeniedError("无权操作该账户")

    # 权限检查：所属人或管理员
    if member.role != "ADMIN" and account.owner_member_id != member.id:
        raise PermissionDeniedError("只能操作自己的账户")

    close_or_delete_account(db, account_id=account_id, family_id=account.family_id)
    # 204 No Content，不返回响应体