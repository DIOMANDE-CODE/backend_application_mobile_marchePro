from django.db import models
import uuid
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

# Create your models here.

# Fonction de l'image par defaut
def image_produit_par_defaut():
    return 'media/logo_marchePro.png'

# Creation de la classe Catégorie
class Categorie(models.Model):
    identifiant_categorie = models.UUIDField(default=uuid.uuid4, editable=False, unique=True )
    nom_categorie = models.CharField(max_length=50, verbose_name="nom catégorie", unique=True)
    description_categorie = models.TextField(null=True, blank=True, verbose_name="description produit")

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom_categorie

# Creation du modèle Produit
class Produit(models.Model):
    identifiant_produit = models.UUIDField(default=uuid.uuid4,editable=False, unique=True )
    nom_produit = models.CharField(max_length=50, unique=True)
    image_produit = models.ImageField(upload_to='media/image_produit/', default='media/logo_marchePro.png', blank=True, null=True, verbose_name='Image du produit')
    description_produit = models.TextField(blank=True, null=True, verbose_name="Description produit")
    prix_unitaire_produit = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire produit",validators=[MinValueValidator(0)])
    quantite_produit_disponible = models.IntegerField(verbose_name="quantite produit disponible", validators=[MinValueValidator(0)])
    seuil_alerte_produit = models.IntegerField(verbose_name="Quantite alerte du produit", validators=[MinValueValidator(0)])
    categorie_produit = models.ForeignKey(Categorie, on_delete=models.CASCADE, verbose_name="Categorie du produit", related_name="categories")

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.quantite_produit_disponible < 0:
            raise ValidationError("La quantité disponible ne peut pas être négative.")
        
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

        # Vérification automatique du stock faible
        if self.quantite_produit_disponible <= self.seuil_alerte_produit:
            # Vérifie si une alerte existe déjà
            alerte_existante = AlertProduit.objects.filter(produit=self, statut_alerte=True).first()
            if not alerte_existante:
                AlertProduit.objects.create(
                    produit=self,
                    message_alerte=f"Le stock du produit '{self.nom_produit}' est faible ({self.quantite_produit_disponible} restants)."
                )
        else:
            # Si le stock est revenu à la normale, fermer l’alerte
            AlertProduit.objects.filter(produit=self, statut_alerte=True).update(statut_alerte=False)


    def __str__(self):
        return self.nom_produit


# Creation de la classe AlertProduit
class AlertProduit(models.Model):
    identifiant_alerte = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, verbose_name="alert_produit")
    message_alerte = models.CharField(max_length=50, null=True, blank=True)
    statut_alerte = models.BooleanField(default=True)
    date_alerte = models.DateTimeField(auto_now_add=True)