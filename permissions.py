from rest_framework.permissions import BasePermission
# from utilisateurs.models import ROLE_CHOICES

# verifier que l'utilisateur connecté est l'admin
class EstAdministrateur(BasePermission):
    def has_permission(self, request, view):
        return request.user.authenticated and request.user.role == 'admin'


# verifier que l'utilisateur connecté est le gérant
class EstGerant(BasePermission):
    def has_permission(self, request, view):
        return request.user.authenticated and request.user.role == 'gerant'