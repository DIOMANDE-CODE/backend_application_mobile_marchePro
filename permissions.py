from rest_framework.permissions import BasePermission

# verifier que l'utilisateur connecté est l'admin
class EstAdministrateur(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


# verifier que l'utilisateur connecté est le gérant
class EstGerant(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'gerant'
    

# Permission objets accordé uniquement à l'utilisateur connecté
class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user