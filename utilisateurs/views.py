from django.shortcuts import render
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from permissions import EstAdministrateur, EstGerant

from .models import Utilisateur
from .serializers import UtilisateurSerializer

import re

# Create your views here.

# Fonction pour lister les utilisateurs
@api_view(['GET'])
@permission_classes([AllowAny])
def list_utilisateur(request):
    try :
        user = Utilisateur.objects.all().filter(role='vendeur')
        serializer = UtilisateurSerializer(user, many=True)
        return Response({
            "success":True,
            "data":serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e :
        return Response({
            "success":False,
            "errors":"Erreur interne du serveur",
            "message":str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Fonction de creation d'un utilisateur
@api_view(['POST'])
@permission_classes([AllowAny])
def create_utilisateur(request):
    print(request.data)
    nom = request.data.get('nom_utilisateur')
    email = request.data.get('email_utilisateur')
    numero = request.data.get('numero_telephone_utilisateur')
    password = request.data.get('password')

    # Verifier email, numero et nom
    if not email or not numero or not nom or not password : 
        return Response({
            "success":False,
            "errors":"Tous les champs sont obligatoires"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try :
        validate_email(email)
    except ValidationError:
        return Response({
            "success":False,
            "errors":"Email invalide"
        })
    if numero.isdigit():
        pattern = r'^(?:\+225|00225)?(01|05|07|25|27)\d{8}$'
        if not re.match(pattern,numero):
            return Response({
                "success":False,
                "errors":"Numéro invalide (ex: +2250102030405 ou 0102030405)."
            }, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({
                "success":False,
                "errors":"Numéro invalide (ex: +2250102030405 ou 0102030405)."
            }, status=status.HTTP_400_BAD_REQUEST)
        
    # Verfier que l'utilisateur n'existe pas
    if Utilisateur.objects.filter(email_utilisateur=email, numero_telephone_utilisateur=numero).exists():
        return Response({
            "success":False,
            "errors":"Cet utilisateur existe dejà"
        })
    
    # Création du compte
    try :
        serializer = UtilisateurSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success":True,
                "message":"Compte crée avec succès"
            }, status=status.HTTP_201_CREATED)
        return Response({
            "success":False,
            "errors":serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e :
        import traceback
        traceback.print_exc()
        print(Exception)
        return Response({
            "success":False,
            "errors":"Erreur interne du serveur",
            "message":str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

# Voir et modifier les details de l'utilisateur connecté
@api_view(['GET','PUT'])
def detail_utilisateur(request):

    try :
        user = Utilisateur.objects.filter(email_utilisateur=request.user, is_active=True)
    except Exception:
        return Response({
            "success":False,
            "errors":"Cet utilisateur n'existe pas"
        }, status=status.HTTP_400_BAD_REQUEST)
    # Requette GET
    if request.method == 'GET':
        try :
            serializer = UtilisateurSerializer(user)
            return Response({
                "success":True,
                "data":serializer.data
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({
                "success":False,
                "errors":serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Requette PUT
    if request.method == 'PUT':
        try :
            serializer = UtilisateurSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "success":True,
                    "message":"Compte modifié avec succès",
                    "data":serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "success":False,
                    "errors":serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e :
            return Response({
                "success":False,
                "errors":"Erreur interne du serveur",
                "message":str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
# Requette DELETE
@api_view(['DELETE'])
@permission_classes([EstGerant, EstAdministrateur])
def delete_utilisateur(request, id):
    try:
        # Vérifier l'existence de l'utilisateur
        user = Utilisateur.objects.get(identifiant=id, is_active=True)
    except Utilisateur.DoesNotExist:
        return Response({
            "success": False,
            "errors": "Cet utilisateur n'existe pas"
        }, status=status.HTTP_404_NOT_FOUND)

    try:
        user.is_active = False
        user.save()

        return Response({
            "success": True,
            "message": "Utilisateur supprimé avec succès"
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "success": False,
            "errors": "Erreur interne du serveur",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)