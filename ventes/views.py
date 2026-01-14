from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .serializers import VenteCreateSerializer, VoirVenteSerializer
from .models import Vente
from datetime import date
from rest_framework.pagination import LimitOffsetPagination
from django.core.cache import cache

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def creer_vente(request):
    """
    Reçoit un JSON type Facture et crée la vente avec les détails et le client.
    """
    try :
        serializer = VenteCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            vente = serializer.save()
            return Response({"message": "Vente créée avec succès", "vente_id": vente.id}, status=status.HTTP_201_CREATED)
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_ventes(request):
    try :
        cache_version = cache.get("ventes_cache_version",1)


        ventes = Vente.objects.filter(date_vente__date=date.today()).order_by('-date_vente')

        # Creation de la clé cache
        limit = request.GET.get("limit","7")
        offset = request.GET.get("offset","O")
        cache_key = f"cache_vente_list_v_{cache_version}_{limit}_{offset}_{request.user.id}"

        # Charger les données depuis le cache
        cached_data = cache.get(cache_key)  
        if cached_data:
             return Response({
            "success":True,
            "data":pagination_response.data
        }, status=status.HTTP_200_OK)


        # pagination
        pagination = LimitOffsetPagination()
        pagination.default_limit = 7
        ventes_page = pagination.paginate_queryset(ventes,request)
        serializer = VoirVenteSerializer(ventes_page, many=True)
        pagination_response = pagination.get_paginated_response(serializer.data)
        response_data = pagination_response.data

        # Stocker les ventes dans le cache
        cache_timeout = 60 * 5
        cache.set(cache_key,response_data,cache_timeout)

        return Response({
            "success":True,
            "data":response_data,
            "cached":True
        }, status=status.HTTP_200_OK)
    except Exception as e :
        return Response({
            "success":False,
            "errors":"Erreur interne du serveur",
            "message":str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
def liste_ventes_par_vendeur(request):
    user = request.user
    if user.role != "vendeur":
        return Response({
            "success": False,
            "errors": "Accès refusé. Cette vue est réservée aux vendeurs."
        }, status=403)
    else :
        try :
            ventes = Vente.objects.filter(date_vente__date=date.today(), utilisateur=user).order_by('-date_vente')
            serializer = VoirVenteSerializer(ventes, many=True)
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detail_ventes(request, vente_id):
    try:
        vente = Vente.objects.get(identifiant_vente=vente_id)
    except Vente.DoesNotExist:
        return Response({'success': False, 'message': 'Vente non trouvée'}, status=status.HTTP_404_NOT_FOUND)
    
    try :
        serializer = VoirVenteSerializer(vente)
        return Response({'success': True, 'data': serializer.data}, status=status.HTTP_200_OK)
    except Exception as e :
        return Response({
            "success":False,
            "errors":"Erreur interne du serveur",
            "message":str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
