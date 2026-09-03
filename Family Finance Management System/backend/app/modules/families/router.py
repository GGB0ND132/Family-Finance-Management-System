from fastapi import APIRouter

from app.common.response import ok
from app.core.deps import CurrentUser, DbSession, require_family_admin, require_family_member
from app.modules.families import repository as family_repo
from app.modules.families.schemas import (
    CreateFamilyRequest,
    FamilyOut,
    InviteCodeOut,
    JoinFamilyRequest,
    MemberOut,
    UpdateFamilyNameRequest,
    UpdateMemberRoleRequest,
)
from app.modules.families.service import (
    create_family,
    generate_invite_code,
    join_family,
    remove_member,
    revoke_invite_code,
    update_family_name,
    update_member_role,
)

router = APIRouter(prefix="/families", tags=["家庭与成员"])


def _family_out(db, family) -> dict:
    return FamilyOut(
        id=family.id,
        name=family.name,
        owner_id=family.owner_id,
        members_count=family_repo.count_family_members(db, family.id),
        created_at=family.created_at,
    ).model_dump()


@router.get("", summary="查询本人加入的家庭列表")
def list_families(user: CurrentUser, db: DbSession):
    families = family_repo.list_user_families(db, user.id)
    return ok([_family_out(db, family) for family in families])


@router.post("", summary="创建家庭（创建者自动成为管理员）")
def create(user: CurrentUser, db: DbSession, payload: CreateFamilyRequest):
    family = create_family(db, user, payload.name)
    return ok(_family_out(db, family), message="家庭创建成功")


@router.post("/join", summary="使用邀请码加入家庭")
def join(user: CurrentUser, db: DbSession, payload: JoinFamilyRequest):
    member = join_family(db, user, payload.invite_code)
    return ok({"family_id": member.family_id}, message="加入家庭成功")


@router.patch("/{family_id}", summary="修改家庭名称（管理员）")
def update_name(family_id: int, payload: UpdateFamilyNameRequest, user: CurrentUser, db: DbSession):
    admin = require_family_admin(db, user, family_id)
    family = family_repo.get_family_by_id(db, family_id)
    if family is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("家庭不存在")
    updated = update_family_name(db, family, payload.name)
    return ok(_family_out(db, updated), message="家庭名称修改成功")


@router.get("/{family_id}/members", summary="查询家庭成员列表")
def list_members(family_id: int, user: CurrentUser, db: DbSession):
    require_family_member(db, user, family_id)
    members = [
        MemberOut(
            id=member.id,
            family_id=member.family_id,
            user_id=member.user_id,
            username=user_obj.username,
            nickname=user_obj.nickname,
            role=member.role,
            joined_at=member.joined_at,
        ).model_dump()
        for member, user_obj in family_repo.list_members(db, family_id)
    ]
    return ok(members)


@router.post("/{family_id}/invite-code", summary="生成邀请码（管理员）")
def create_invite_code(family_id: int, user: CurrentUser, db: DbSession):
    require_family_admin(db, user, family_id)
    family = family_repo.get_family_by_id(db, family_id)
    if family is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("家庭不存在")
    code, expires_at = generate_invite_code(db, family)
    return ok(InviteCodeOut(invite_code=code, expires_at=expires_at).model_dump(), message="邀请码已生成")


@router.delete("/{family_id}/invite-code", summary="使邀请码失效（管理员）")
def revoke(family_id: int, user: CurrentUser, db: DbSession):
    require_family_admin(db, user, family_id)
    family = family_repo.get_family_by_id(db, family_id)
    if family is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("家庭不存在")
    revoke_invite_code(db, family)
    return ok(message="邀请码已失效")


@router.delete("/{family_id}/members/{member_id}", summary="移除成员（管理员）")
def delete_member(family_id: int, member_id: int, user: CurrentUser, db: DbSession):
    admin = require_family_admin(db, user, family_id)
    member = family_repo.get_member_by_id(db, member_id)
    if member is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("成员不存在")
    remove_member(db, admin, member)
    return ok(message="成员已移除")


@router.patch("/{family_id}/members/{member_id}", summary="调整成员角色（管理员）")
def update_member(family_id: int, member_id: int, payload: UpdateMemberRoleRequest, user: CurrentUser, db: DbSession):
    admin = require_family_admin(db, user, family_id)
    member = family_repo.get_member_by_id(db, member_id)
    if member is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("成员不存在")
    updated = update_member_role(db, admin, member, payload.role)
    from app.modules.users.repository import get_user_by_id

    user_obj = get_user_by_id(db, updated.user_id)
    return ok(
        MemberOut(
            id=updated.id,
            family_id=updated.family_id,
            user_id=updated.user_id,
            username=user_obj.username,
            nickname=user_obj.nickname,
            role=updated.role,
            joined_at=updated.joined_at,
        ).model_dump(),
        message="角色已更新",
    )