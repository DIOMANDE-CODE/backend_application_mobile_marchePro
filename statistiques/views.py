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
from commandes.models import Commande, DetailCommande
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
            # Somme total des ventes du jour effectuée par le vendeur connecté
            ventes_du_aujourdhui = Vente.objects.filter(utilisateur=user, date_vente__date=aujourd_hui)
            total_ventes_aujourd_hui = sum(vente.total_ttc for vente in ventes_du_aujourdhui)

            # Somme total des commandes du jour effectuée et livré par le vendeur connecté
            commandes_du_aujourdhui = Commande.objects.filter(utilisateur=user, date_commande__date=aujourd_hui, etat_commande="livre")
            total_ventes_commandes_aujourd_hui = sum(vente.total_ttc for vente in commandes_du_aujourdhui)

            # Caisse du jour du vendeur connecté
            total_caisse_jour = total_ventes_aujourd_hui + total_ventes_commandes_aujourd_hui

            # Total Commande du jour
            total_commande_aujourd_hui = Commande.objects.filter(date_creation__date=aujourd_hui).count()

            # Total Commande Attente du jour
            total_commande_attente_aujourd_hui = Commande.objects.filter(date_creation__date=aujourd_hui,etat_commande='en_cours').count()

            # Total Commande Attente du jour
            total_commande_valide_aujourd_hui = Commande.objects.filter(date_creation__date=aujourd_hui,etat_commande='valide').count()

            # Total Commande Livre du jour
            total_commande_livre_aujourd_hui = Commande.objects.filter(date_creation__date=aujourd_hui,etat_commande='livre').count()

            # Total Commande Annulée du jour
            total_commande_annulee_aujourd_hui = Commande.objects.filter(date_creation__date=aujourd_hui,etat_commande='annule').count()

            return Response({
            "success":True,
            "data":{
                "total_caisse_jour": total_caisse_jour,
                "total_commande_aujourd_hui":total_commande_aujourd_hui,
                "total_commande_valide_aujourd_hui":total_commande_valide_aujourd_hui,
                "total_commande_livre_aujourd_hui":total_commande_livre_aujourd_hui,
                "total_commande_attente_aujourd_hui":total_commande_attente_aujourd_hui,
                "total_ventes_aujourd_hui":total_ventes_aujourd_hui,
                "total_ventes_commandes_aujourd_hui":total_ventes_commandes_aujourd_hui,
                "total_commande_annulee_aujourd_hui":total_commande_annulee_aujourd_hui,
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

        # Produit en stock
        total_produits_en_stock = Produit.objects.filter(quantite_produit_disponible__gte=1).count()

        # Produits avec faible stock
        total_produits_stock_faible = AlertProduit.objects.all().count()

        # Total commande du jour
        total_commandes_du_jour = Commande.objects.filter(date_creation__date=aujourd_hui).count()

        # Total ventes
        total_ventes_du_jour = Vente.objects.filter(date_creation__date=aujourd_hui).count()

        # Total commande en attente du jour
        total_commandes_attente_du_jour = Commande.objects.filter(date_creation__date=aujourd_hui, etat_commande='en_cours').count()

        # Total commande en livraison/validé du jour
        total_commandes_valide_du_jour = Commande.objects.filter(date_creation__date=aujourd_hui, etat_commande='valide').count()

        # Total commande en livré du jour
        total_commandes_livre_du_jour = Commande.objects.filter(date_creation__date=aujourd_hui, etat_commande='livre').count()

        # Total clients du jour
        total_client_du_jour = Client.objects.filter(date_creation__date=aujourd_hui).count()

        # Total vendus aujourd'hui
        ventes_aujourd_hui = Vente.objects.filter(date_vente__date=aujourd_hui)
        total_ventes_aujourd_hui = sum(vente.total_ttc for vente in ventes_aujourd_hui)

        # nombre de clients du jour
        total_clients_aujourd_hui = Client.objects.filter(date_creation__date=aujourd_hui).count()

        # Somme total des ventes du jour
        ventes_du_jour = Vente.objects.filter(date_vente__date=aujourd_hui)
        somme_totale_ventes_du_jour = sum(vente.total_ttc for vente in ventes_du_jour)

        # Somme total des commandes du jour
        commandes_du_jour = Commande.objects.filter(date_commande__date=aujourd_hui, etat_commande="livre")
        somme_totale_commandes_aujourd_hui = sum(commande.total_ttc for commande in commandes_du_jour)

        # Somme totale de la caisse du jour
        somme_totale_caisse_du_jour = somme_totale_ventes_du_jour + somme_totale_commandes_aujourd_hui

        # Somme de toutes les quantités vendues aujourd'hui
        nombre_produits_vendus = DetailVente.objects.filter(
            vente__date_vente__date=aujourd_hui
        ).aggregate(total_produits=Sum('quantite'))['total_produits'] or 0

        # Somme de toutes les commandes livrés aujourd'hui
        nombre_commandes_livre = DetailCommande.objects.filter(
            commande__date_commande__date=aujourd_hui
        ).aggregate(total_produits=Sum('quantite'))['total_produits'] or 0

        # Totaux produits vendus
        totaux_produits_vendus_du_jour = nombre_produits_vendus + nombre_commandes_livre

        # Nombre de ventes du jour
        nombre_ventes = ventes_aujourd_hui.count()
        nombre_commandes = commandes_du_jour.count()
        total_vente_jour = nombre_ventes + nombre_commandes

        # Panier moyen
        panier_moyen_aujourd_hui = somme_totale_caisse_du_jour / total_vente_jour if total_vente_jour > 0 else 0


        # nombre totale de produits avec stocks faibles
        nombre_produits_stocks_faibles = AlertProduit.objects.filter(statut_alerte=False).count()

        return Response({
            "success":True,
            "data":{
                "total_produits_en_stock": total_produits_en_stock,
                "total_produits_stock_faible":total_produits_stock_faible,
                "total_commandes_du_jour":total_commandes_du_jour,
                "total_ventes_du_jour":total_ventes_du_jour,
                "total_commandes_attente_du_jour":total_commandes_attente_du_jour, 
                "total_commandes_valide_du_jour":total_commandes_valide_du_jour, 
                "total_commandes_livre_du_jour":total_commandes_livre_du_jour,
                "total_client_du_jour":total_client_du_jour,
                "somme_totale_caisse_du_jour":somme_totale_caisse_du_jour,
                "somme_totale_commandes_aujourd_hui":somme_totale_commandes_aujourd_hui,
                "somme_totale_ventes_du_jour":somme_totale_ventes_du_jour,
                "totaux_produits_vendus_du_jour":totaux_produits_vendus_du_jour,

                "total_ventes_aujourd_hui": total_ventes_aujourd_hui,
                "total_clients_aujourd_hui": total_clients_aujourd_hui,
                "nombre_produits_vendus_aujourd_hui": nombre_produits_vendus,
                "panier_moyen_aujourd_hui": panier_moyen_aujourd_hui,
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

        # Somme total des ventes de la semaine
        ventes_semaine = Vente.objects.filter(date_vente__date__range=[debut_semaine, fin_semaine])
        somme_totale_ventes_semaine = sum(vente.total_ttc for vente in ventes_semaine)

        # Somme total des commandes de la semaine
        commandes_semaine = Commande.objects.filter(date_commande__date__range=[debut_semaine, fin_semaine],etat_commande="livre")
        somme_totale_commandes_semaine = sum(commande.total_ttc for commande in commandes_semaine)

        # Somme totale de la caisse de la semaine
        somme_totale_caisse_semaine = somme_totale_ventes_semaine + somme_totale_commandes_semaine        

        # Total clients semaine
        total_client_semaine = Client.objects.filter(date_creation__date__range=[debut_semaine, fin_semaine]).count()

        # Somme de toutes les quantités vendues semaine
        nombre_produits_vendus_semaine = DetailVente.objects.filter(
            vente__date_vente__date__range=[debut_semaine, fin_semaine]
        ).aggregate(total_produits=Sum('quantite'))['total_produits'] or 0

        # Somme de toutes les commandes livrés semaine
        nombre_commandes_livre_semaine = DetailCommande.objects.filter(
            commande__date_commande__date__range=[debut_semaine, fin_semaine]
        ).aggregate(total_produits=Sum('quantite'))['total_produits'] or 0

        # Somme de toutes les quantités vendues cette semaine
        nombre_produits_vendus_semaine = DetailVente.objects.filter(
            vente__date_vente__date__range=[debut_semaine, fin_semaine]
        ).aggregate(total_produits=Sum('quantite'))['total_produits'] or 0


        # Totaux produits vendus
        totaux_produits_vendus_semaine = nombre_produits_vendus_semaine + nombre_commandes_livre_semaine

        # Nombre de ventes du jour
        nombre_ventes_semaine = ventes_semaine.count()
        nombre_commandes_semaine = commandes_semaine.count()
        total_vente_semaine = nombre_ventes_semaine + nombre_commandes_semaine

        # Panier moyen semaine
        panier_moyen_semaine = somme_totale_caisse_semaine / total_vente_semaine if total_vente_semaine > 0 else 0
    

        return Response({
            "success": True,
            "data": {
                "somme_totale_caisse_semaine":somme_totale_caisse_semaine,
                "total_client_semaine":total_client_semaine,
                "totaux_produits_vendus_semaine":totaux_produits_vendus_semaine,
                "panier_moyen_semaine":panier_moyen_semaine,
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

        # Somme total des ventes du mois
        ventes_mois = Vente.objects.filter(date_vente__date__range=[debut_mois, fin_mois])
        somme_totale_ventes_mois = sum(vente.total_ttc for vente in ventes_mois)

        # Somme total des commandes du mois
        commandes_mois = Commande.objects.filter(date_commande__date__range=[debut_mois, fin_mois])
        somme_totale_commandes_mois = sum(commande.total_ttc for commande in commandes_mois)

        # Somme totale de la caisse du jour
        somme_totale_caisse_mois = somme_totale_ventes_mois + somme_totale_commandes_mois        

        # Total clients semaine
        total_client_mois = Client.objects.filter(date_creation__date__range=[debut_mois, fin_mois]).count()

        # Somme de toutes les quantités vendues du mois
        nombre_produits_vendus_mois = DetailVente.objects.filter(
            vente__date_vente__date__range=[debut_mois, fin_mois]
        ).aggregate(total_produits=Sum('quantite'))['total_produits'] or 0

        # Somme de toutes les commandes livrés du mois
        nombre_commandes_livre_mois = DetailCommande.objects.filter(
            commande__date_commande__date__range=[debut_mois, fin_mois]
        ).aggregate(total_produits=Sum('quantite'))['total_produits'] or 0



        # Totaux produits vendus
        totaux_produits_vendus_mois = nombre_produits_vendus_mois + nombre_commandes_livre_mois

        # Nombre de ventes du mois
        nombre_ventes_mois = ventes_mois.count()
        nombre_commandes_mois = commandes_mois.count()
        total_vente_mois = nombre_ventes_mois + nombre_commandes_mois

        # Panier moyen semaine
        panier_moyen_mois = somme_totale_caisse_mois / total_vente_mois if total_vente_mois > 0 else 0
    


        return Response({
            "success": True,
            "data": {
                "somme_totale_caisse_mois":somme_totale_caisse_mois,
                "total_client_mois":total_client_mois,
                "totaux_produits_vendus_mois":totaux_produits_vendus_mois,
                "panier_moyen_mois":panier_moyen_mois,
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
    




    