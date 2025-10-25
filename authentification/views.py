from django.shortcuts import render
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

from utilisateurs.models import Utilisateur
from utilisateurs.serializers import UtilisateurSerializer
# Create your views here.

# Fonction de connexion
@api_view(['POST'])
@permission_classes([AllowAny])
def login_utilisateur(request):
    email = request.data.get('email_utilisateur')
    password = request.data.get('password')

    # Vérification des champs requis
    if not email or not password:
        return Response({
            "success": False,
            "errors": "Tous les champs sont obligatoires"
        }, status=status.HTTP_400_BAD_REQUEST)

    # Validation du format d'email
    try:
        validate_email(email)
    except ValidationError:
        return Response({
            "success": False,
            "errors": "Adresse e-mail invalide"
        }, status=status.HTTP_400_BAD_REQUEST)

    # Vérification de l'existence de l'utilisateur
    try:
        user = Utilisateur.objects.get(email_utilisateur=email, is_active=True)
    except Utilisateur.DoesNotExist:
        return Response({
            "success": False,
            "errors": "Aucun compte associé à cet e-mail"
        }, status=status.HTTP_404_NOT_FOUND)

    # Vérification du mot de passe
    if not user.check_password(password):
        return Response({
            "success": False,
            "errors": "Mot de passe incorrect"
        }, status=status.HTTP_401_UNAUTHORIZED)

    # Connexion (session)
    try :
        user = authenticate(request, username=email, password=password)
        if user is not None:
            token, _ = Token.objects.get_or_create(user=user)
            info_user = UtilisateurSerializer(user).data
            return Response({
            "success": True,
            "message": "Connexion établie",
            "token": token.key,
            "user":info_user,
            }, status=status.HTTP_200_OK)
        return Response({
            "success": False,
            "errors": "Identifiant invalide"
        }, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e :
        import traceback
        traceback.print_exc()
        print(Exception)
        return Response({
            "success":False,
            "errors":"Erreur interne du serveur",
            "message":str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
@api_view(['POST'])
def logout_utilisateur(request):
    try :
        token_key = request.auth.key
        print(token_key)
        Token.objects.filter(key=token_key).delete()
    except Exception as e :
        import traceback
        traceback.print_exc()
        print(Exception)
        return Response({
            "success":False,
            "errors":"Erreur interne du serveur",
            "message":str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response({
                "success":True,
                "message":"Compte déconnecté"
            }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def check_session(request):
    token_key = request.data.get('token_key')

    if not token_key:
        return Response({
            "success": False,
            "authenticated": False,
            "message": "Token manquant"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Vérifie si le token existe dans la table Token
        token = Token.objects.filter(key=token_key).first()

        if token:
            return Response({
                "success": True,
                "authenticated": True,
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "success": False,
                "authenticated": False,
                "message": "Token invalide ou expiré"
            }, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            "success": False,
            "errors": "Erreur interne du serveur",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)