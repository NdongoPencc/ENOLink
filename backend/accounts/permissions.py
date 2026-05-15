from rest_framework.permissions import BasePermission


class IsDFIP(BasePermission):
    message = "Accès réservé à la DFIP."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_dfip


class IsEnseignantOrCoordinateur(BasePermission):
    message = "Accès réservé aux enseignants et coordinateurs ENO."

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_enseignant or request.user.is_coordinateur
        )


class IsApprenant(BasePermission):
    message = "Accès réservé aux apprenants."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_apprenant


class IsDFIPOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_dfip


class IsStaffOrDFIP(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or request.user.is_dfip
        )
