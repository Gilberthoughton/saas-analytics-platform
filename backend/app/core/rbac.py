"""Role-based access control primitives.

Roles are ordered: owner > admin > member. `role_satisfies` checks whether a
member's role meets a minimum requirement, which the API dependency layer uses
to guard routes.
"""

from enum import Enum


class Role(str, Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


# Higher number = more privilege.
_RANK: dict[str, int] = {
    Role.member.value: 1,
    Role.admin.value: 2,
    Role.owner.value: 3,
}


def role_satisfies(actual: str, minimum: Role) -> bool:
    """True if `actual` role has at least `minimum` privilege."""
    return _RANK.get(actual, 0) >= _RANK[minimum.value]
