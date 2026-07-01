from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import *

# ==================== Profil (inline dans User) ====================
class ProfilInline(admin.StackedInline):
    model = Profil
    can_delete = False
    verbose_name_plural = 'Profil'

class CustomUserAdmin(UserAdmin):
    inlines = [ProfilInline]
    list_display = ['username', 'email', 'get_role']
    
    def get_role(self, obj):
        return obj.profil.get_role_display() if hasattr(obj, 'profil') else 'Non défini'
    get_role.short_description = 'Rôle'

# Re-enregistrer User avec le nouvel admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# ==================== Enregistrement des modèles ====================

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ['nom', 'slug', 'date_creation']
    search_fields = ['nom']
    prepopulated_fields = {'slug': ('nom',)}

@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ['nom', 'phone', 'email', 'ville', 'actif']
    search_fields = ['nom', 'email', 'phone']
    list_filter = ['actif', 'ville', 'pays']

@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ['nom', 'sku', 'prix_achat', 'prix_vente', 'quantite_stock', 'stock_faible', 'est_expire']
    search_fields = ['nom', 'sku', 'code_barre']
    list_filter = ['categorie', 'fournisseur', 'is_active', 'unite']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'description', 'unite', 'sku', 'code_barre')
        }),
        ('Catégorie et Fournisseur', {
            'fields': ('categorie', 'fournisseur')
        }),
        ('Prix', {
            'fields': ('prix_achat', 'prix_vente')
        }),
        ('Stock', {
            'fields': ('quantite_stock', 'stock_min')
        }),
        ('Autres', {
            'fields': ('image', 'date_expiration', 'is_active')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['produit', 'type_mouvement', 'quantite', 'reference', 'created_at']
    list_filter = ['type_mouvement', 'created_at']
    search_fields = ['produit__nom', 'reference']

@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    list_display = ['numero', 'client', 'total', 'mode_paiement', 'statut', 'agent', 'date_vente']
    list_filter = ['statut', 'mode_paiement', 'date_vente']
    search_fields = ['numero', 'client']
    readonly_fields = ['numero', 'date_vente']

class DetailVenteInline(admin.TabularInline):
    model = DetailVente
    extra = 1
    readonly_fields = ['total']

@admin.register(DetailVente)
class DetailVenteAdmin(admin.ModelAdmin):
    list_display = ['vente', 'produit', 'quantite', 'prix', 'total']
    search_fields = ['vente__numero', 'produit__nom']

@admin.register(Achat)
class AchatAdmin(admin.ModelAdmin):
    list_display = ['id', 'fournisseur', 'statut', 'total', 'user', 'date_commande']
    list_filter = ['statut', 'date_commande']
    search_fields = ['fournisseur__nom']

class DetailAchatInline(admin.TabularInline):
    model = DetailAchat
    extra = 1
    readonly_fields = ['total']

@admin.register(DetailAchat)
class DetailAchatAdmin(admin.ModelAdmin):
    list_display = ['achat', 'produit', 'quantite', 'prix', 'total']
    search_fields = ['achat__fournisseur__nom', 'produit__nom']

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ['reference', 'client', 'total', 'statut', 'cree_par', 'date_commande']
    list_filter = ['statut', 'date_commande']
    search_fields = ['reference', 'client']

@admin.register(DetailProduit)
class DetailProduitAdmin(admin.ModelAdmin):
    list_display = ['produit', 'poids', 'couleur', 'taille', 'date_expiration']
    search_fields = ['produit__nom']

@admin.register(Rapport)
class RapportAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type', 'user', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['titre']

@admin.register(Historique)
class HistoriqueAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'target', 'date_action']
    list_filter = ['action', 'date_action']
    search_fields = ['user__username']
    readonly_fields = ['user', 'action', 'target', 'anciennes_valeurs', 'nouvelles_valeurs']