from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from datetime import date, timedelta

from ventes.models import Vente
from produits.models import Produit, AlertProduit
from clients.models import Client
from ventes.models import DetailVente
from django.db.models import Sum
import calendar
from permissions import EstAdministrateur
# Create your views here.

# Vue des statistiqes quotidiennes par vendeurs
@api_view(['GET'])
def statistiques_quotidiennes_vendeur(request):
    user = request.user
    if user.role != 'vendeur':
        return Response({
            "success": False,
            "errors": "Accès refusé. Cette vue est réservée aux vendeurs."
        }, status=403)
    else :
        aujourd_hui = date.today()
        try :
            # Somme de toutes les quantités vendues aujourd'hui par le vendeur connecté
            ventes_du_aujourdhui = Vente.objects.filter(utilisateur=user, date_vente__date=aujourd_hui)
            total_ventes_aujourd_hui = sum(vente.total_ttc for vente in ventes_du_aujourdhui)

            # Produit en stock
            total_produits_en_stock = Produit.objects.filter(quantite_produit_disponible__gte=1).count()

            # nombre de clients du jour
            total_clients_aujourd_hui = Client.objects.filter(date_creation__date=aujourd_hui).count()

            # nombre totale de produits avec stocks faibles
            nombre_produits_stocks_faibles = AlertProduit.objects.filter(statut_alerte=False).count()

            return Response({
            "success":True,
            "data":{
                "total_ventes_aujourd_hui": total_ventes_aujourd_hui,
                "total_produits_en_stock": total_produits_en_stock,
                "total_clients_aujourd_hui": total_clients_aujourd_hui,
                "nombre_produits_stocks_faibles": nombre_produits_stocks_faibles,
            }
        }, status=200)
        except Exception as e :
            import traceback
            traceback.print_exc()
            return Response({
                "success":False,
                "errors":"Erreur interne du serveur",
                "message":str(e)
            }, status=500)

# Vue pour obtenir des statistiques du jour
@api_view(['GET'])
@permission_classes([EstAdministrateur])
def statistiques_du_jour(request):
    # Obtenir la date actuelle
    aujourd_hui = date.today()

    try :

        # Total vendus aujourd'hui
        ventes_aujourd_hui = Vente.objects.filter(date_vente__date=aujourd_hui)
        total_ventes_aujourd_hui = sum(vente.total_ttc for vente in ventes_aujourd_hui)

        # Produit en stock
        total_produits_en_stock = Produit.objects.filter(quantite_produit_disponible__gte=1).count()

        # nombre de clients du jour
        total_clients_aujourd_hui = Client.objects.filter(date_creation__date=aujourd_hui).count()

        # Somme de toutes les quantités vendues aujourd'hui
        nombre_produits_vendus = DetailVente.objects.filter(
            vente__date_vente__date=aujourd_hui
        ).aggregate(total_produits=Sum('quantite'))['total_produits'] or 0

        # Nombre de ventes du jour
        nombre_ventes = ventes_aujourd_hui.count()

        # Panier moyen
        panier_moyen_aujourd_hui = total_ventes_aujourd_hui / nombre_ventes if nombre_ventes > 0 else 0


        # Top 3 produits les plus vendus
        top_produits_aujourd_hui = (
            DetailVente.objects.filter(vente__date_vente__date=aujourd_hui)
            .values('produit__nom_produit')
            .annotate(qte_vendue=Sum('quantite'))
            .order_by('-qte_vendue')[:3]  # limite à 3
        )

        # nombre totale de produits avec stocks faibles
        nombre_produits_stocks_faibles = AlertProduit.objects.filter(statut_alerte=False).count()

        return Response({
            "success":True,
            "data":{
                "total_ventes_aujourd_hui": total_ventes_aujourd_hui,
                "total_produits_en_stock": total_produits_en_stock,
                "total_clients_aujourd_hui": total_clients_aujourd_hui,
                "nombre_produits_vendus_aujourd_hui": nombre_produits_vendus,
                "panier_moyen_aujourd_hui": panier_moyen_aujourd_hui,
                "top_produits_aujourd_hui": list(top_produits_aujourd_hui),
                "nombre_produits_stocks_faibles": nombre_produits_stocks_faibles,
            }
        }, status=200)
    except Exception as e :
        import traceback
        traceback.print_exc()
        return Response({
            "success":False,
            "errors":"Erreur interne du serveur",
            "message":str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([EstAdministrateur])
def statistiques_de_la_semaine(request):
    # Obtenir la date actuelle
    aujourd_hui = date.today()
    # Début de la semaine (lundi)
    debut_semaine = aujourd_hui - timedelta(days=aujourd_hui.weekday())
    # Fin de la semaine (dimanche)
    fin_semaine = debut_semaine + timedelta(days=6)

    try:
        # Total des ventes de la semaine
        ventes_semaine = Vente.objects.filter(date_vente__date__range=[debut_semaine, fin_semaine])
        total_ventes_semaine = sum(vente.total_ttc for vente in ventes_semaine)

        # Produits en stock
        total_produits_en_stock = Produit.objects.count()

        # Nombre de clients créés cette semaine
        total_clients_semaine = Client.objects.filter(date_creation__date__range=[debut_semaine, fin_semaine]).count()

        # Somme de toutes les quantités vendues cette semaine
        nombre_produits_vendus_semaine = DetailVente.objects.filter(
            vente__date_vente__date__range=[debut_semaine, fin_semaine]
        ).aggregate(total_produits=Sum('quantite'))['total_produits'] or 0

        # Nombre de ventes
        nombre_ventes = ventes_semaine.count()

        # Panier moyen
        panier_moyen_semaine = total_ventes_semaine / nombre_ventes if nombre_ventes > 0 else 0

        # Top 3 produits les plus vendus
        top_produits_semaine = (
            DetailVente.objects.filter(vente__date_vente__date__range=[debut_semaine, fin_semaine])
            .values('produit__nom_produit')
            .annotate(qte_vendue=Sum('quantite'))
            .order_by('-qte_vendue')[:3]
        )

        return Response({
            "success": True,
            "data": {
                "total_ventes_semaine": total_ventes_semaine,
                "total_produits_en_stock": total_produits_en_stock,
                "total_clients_semaine": total_clients_semaine,
                "nombre_produits_vendus_semaine": nombre_produits_vendus_semaine,
                "panier_moyen_semaine": panier_moyen_semaine,
                "top_produits_semaine": list(top_produits_semaine),
            }
        }, status=200)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            "success": False,
            "errors": "Erreur interne du serveur",
            "message": str(e)
        }, status=500)


# Rapports mois
@api_view(['GET'])
@permission_classes([EstAdministrateur])
def statistiques_du_mois(request):
    # Obtenir la date actuelle
    aujourd_hui = date.today()
    # Premier jour du mois
    debut_mois = aujourd_hui.replace(day=1)
    # Dernier jour du mois
    dernier_jour = calendar.monthrange(aujourd_hui.year, aujourd_hui.month)[1]
    fin_mois = aujourd_hui.replace(day=dernier_jour)

    try:
        # Total des ventes du mois
        ventes_mois = Vente.objects.filter(date_vente__date__range=[debut_mois, fin_mois])
        total_ventes_mois = sum(vente.total_ttc for vente in ventes_mois)

        # Produits en stock
        total_produits_en_stock = Produit.objects.count()

        # Nombre de clients créés ce mois
        total_clients_mois = Client.objects.filter(date_creation__date__range=[debut_mois, fin_mois]).count()

        # Somme de toutes les quantités vendues ce mois
        nombre_produits_vendus_mois = DetailVente.objects.filter(
            vente__date_vente__date__range=[debut_mois, fin_mois]
        ).aggregate(total_produits=Sum('quantite'))['total_produits'] or 0

        # Nombre de ventes
        nombre_ventes = ventes_mois.count()

        # Panier moyen
        panier_moyen_mois = total_ventes_mois / nombre_ventes if nombre_ventes > 0 else 0

        # Top 3 produits les plus vendus
        top_produits_mois = (
            DetailVente.objects.filter(vente__date_vente__date__range=[debut_mois, fin_mois])
            .values('produit__nom_produit')
            .annotate(qte_vendue=Sum('quantite'))
            .order_by('-qte_vendue')[:3]
        )

        return Response({
            "success": True,
            "data": {
                "total_ventes_mois": total_ventes_mois,
                "total_produits_en_stock": total_produits_en_stock,
                "total_clients_mois": total_clients_mois,
                "nombre_produits_vendus_mois": nombre_produits_vendus_mois,
                "panier_moyen_mois": panier_moyen_mois,
                "top_produits_mois": list(top_produits_mois),
            }
        }, status=200)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            "success": False,
            "errors": "Erreur interne du serveur",
            "message": str(e)
        }, status=500)