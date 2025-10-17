from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .serializers import VenteCreateSerializer, VoirVenteSerializer
from .models import Vente
from datetime import date

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
@permission_classes([AllowAny])
def liste_ventes(request):
    try :
        ventes = Vente.objects.filter(date_vente__date=date.today()).order_by('-date_vente')
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
@permission_classes([AllowAny])
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
