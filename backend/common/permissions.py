from rest_framework.permissions import BasePermission

from common.constants import ROLE_ADMIN, ROLE_CUSTOMER, ROLE_STAFF


class IsAuthenticatedAndActive(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active)


class IsAdmin(IsAuthenticatedAndActive):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == ROLE_ADMIN


class IsCustomer(IsAuthenticatedAndActive):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == ROLE_CUSTOMER


class IsStaff(IsAuthenticatedAndActive):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == ROLE_STAFF


class IsStaffOrAdmin(IsAuthenticatedAndActive):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role in {ROLE_STAFF, ROLE_ADMIN}


class HasAnyStaffSubdivision(IsAuthenticatedAndActive):
    allowed_staff_roles = set()

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.user.role == ROLE_ADMIN:
            return True
        return request.user.role == ROLE_STAFF and request.user.staff_role in self.allowed_staff_roles


def build_staff_role_permission(*staff_roles):
    class RolePermission(HasAnyStaffSubdivision):
        allowed_staff_roles = set(staff_roles)

    return RolePermission
