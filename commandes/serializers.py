from rest_framework import serializers
from .models import Commande, DetailCommande
from clients.models import Client
from produits.models import Produit
from utilisateurs.serializers import UtilisateurSerializer
from utilisateurs.models import Utilisateur
from .models import AttributionCommande

class ItemSerializer(serializers.Serializer):
    identifiant_produit = serializers.CharField()
    nom_produit = serializers.CharField()
    prix_unitaire_produit = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantite_produit_disponible = serializers.IntegerField()

class ClientSerializer(serializers.Serializer):
    nom_client = serializers.CharField()
    numero_telephone_client = serializers.CharField()

class CommandeCreateSerializer(serializers.Serializer):
    client = ClientSerializer()
    items = ItemSerializer(many=True)

    def create(self, validated_data):
        client_data = validated_data.pop('client')
        items_data = validated_data.pop('items')

        # Créer ou récupérer le client
        client, _ = Client.objects.get_or_create(
            nom_client=client_data['nom_client'],
            numero_telephone_client=client_data['numero_telephone_client']
        )

        # Round Robin pour le vendeur
        vendeurs = Utilisateur.objects.filter(role='vendeur')
        attribution, _ = AttributionCommande.objects.get_or_create(id=1)
        index = attribution.dernier_index % vendeurs.count()
        vendeur_choisi = vendeurs[index]
        attribution.dernier_index = index + 1
        attribution.save()

        # Créer la commande
        commande = Commande.objects.create(
            client=client,
            utilisateur=vendeur_choisi
        )

        # Créer les détails de commande
        for item in items_data:
            produit, _ = Produit.objects.get_or_create(
                identifiant_produit = item['identifiant_produit'],
                defaults={
                    'nom_produit': item['nom_produit'],
                    'prix_unitaire': item['prix_unitaire_produit'],
                    'quantite_disponible': item['quantite_produit_disponible']
                }
            )

            # Décrementer le stock

            produit.quantite_produit_disponible -= item['quantite_produit_disponible']
            produit.save()

            DetailCommande.objects.create(
                commande=commande,
                produit=produit,
                quantite=item['quantite_produit_disponible'],
                prix_unitaire=item['prix_unitaire_produit'],
                sous_total=item['prix_unitaire_produit'] * item['quantite_produit_disponible']
            )
        
        # Calculer les totaux de la vente
        commande.calculer_totaux()
        return commande
    

# Serializer pour les details de commande
class VoirDetailCommandeSerializer(serializers.ModelSerializer):
    produit = serializers.StringRelatedField()

    class Meta:
        model = DetailCommande
        fields = ['id', 'produit', 'quantite', 'prix_unitaire', 'sous_total']

# Serializer pour voir les commandes
class VoirCommandeSerializer(serializers.ModelSerializer):
    client = ClientSerializer()  # Client imbriqué
    details_commandes = VoirDetailCommandeSerializer(many=True, read_only=True)
    utilisateur = UtilisateurSerializer() 

    class Meta:
        model = Commande
        fields = [
            'id',
            'identifiant_commande',
            'client',
            'utilisateur',
            'date_commande',
            'etat_commande',
            'total_ht',
            'tva',
            'total_ttc',
            'details_commandes',
        ]
 

#  Serializer pour changer l'etat de la commande
class CommandeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commande
        fields = ['etat_commande']

    def validate_etat_commande(self,value):
        commande = self.instance

        if commande.etat_commande == 'livre':
            raise serializers.ValidationError(
                "Une commande livrée ne peut plus être modifiée."
            )
        if commande.etat_commande == 'annule' and value != 'annule':
            raise serializers.ValidationError(
                "Une commande annulée ne peut pas changer d’état."
            )
        
        return value