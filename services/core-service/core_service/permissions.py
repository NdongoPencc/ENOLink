from rest_framework.permissions import BasePermission


class IsDFIP(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_dfip


class IsEnseignantOrCoordinateur(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_enseignant or request.user.is_coordinateur
        )
