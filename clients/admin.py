from django.contrib import admin
from .models import Client

# Register your models here.
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display=('id','identifiant_client','nom_client','numero_telephone_client','date_creation','date_modification',)
    search_fields=('nom_client',)
    ordering = ['nom_client']