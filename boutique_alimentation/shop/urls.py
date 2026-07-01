from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentification
    path('', views.connexion, name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),

    # Gestion du mot de passe (personnalisée, sans email)
    path('password-reset-custom/', views.custom_password_reset, name='custom_password_reset'),

    # Les 4 vues standards de réinitialisation (nécessaires pour la confirmation)
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='shop/auth/password_reset.html',
             email_template_name='shop/auth/password_reset_email.html',
             subject_template_name='shop/auth/password_reset_subject.txt'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='shop/auth/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='shop/auth/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='shop/auth/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    # Dashboards
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard-admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard-gerant/', views.dashboard_gerant, name='dashboard_gerant'),
    path('dashboard-comptable/', views.dashboard_comptable, name='dashboard_comptable'),

    # Produits
    path('produits/', views.liste_produits, name='liste_produits'),
    path('produits/ajouter/', views.ajouter_produit, name='ajouter_produit'),
    path('produits/modifier/<int:produit_id>/', views.modifier_produit, name='modifier_produit'),
    path('produits/supprimer/<int:produit_id>/', views.supprimer_produit, name='supprimer_produit'),
    path('produits/detail/<int:produit_id>/', views.detail_produit, name='detail_produit'),

    # Catégories
    path('categories/', views.liste_categories, name='liste_categories'),
    path('categories/ajouter/', views.ajouter_categorie, name='ajouter_categorie'),
    path('categories/modifier/<int:categorie_id>/', views.modifier_categorie, name='modifier_categorie'),
    path('categories/supprimer/<int:categorie_id>/', views.supprimer_categorie, name='supprimer_categorie'),

    # Ventes
    path('ventes/', views.liste_ventes, name='liste_ventes'),
    path('ventes/ajouter/', views.nouvelle_vente, name='nouvelle_vente'),
    path('ventes/detail/<int:vente_id>/', views.detail_vente, name='detail_vente'),

    # Achats
    path('achats/', views.liste_achats, name='liste_achats'),
    path('achats/ajouter/', views.nouvel_achat, name='nouvel_achat'),
    path('achats/changer-statut/<int:achat_id>/', views.changer_statut_achat, name='changer_statut_achat'),
    path('achats/detail/<int:achat_id>/', views.detail_achat, name='detail_achat'),

    # Fournisseurs
    path('fournisseurs/', views.liste_fournisseurs, name='liste_fournisseurs'),
    path('fournisseurs/ajouter/', views.ajouter_fournisseur, name='ajouter_fournisseur'),
    path('fournisseurs/modifier/<int:fournisseur_id>/', views.modifier_fournisseur, name='modifier_fournisseur'),
    path('fournisseurs/supprimer/<int:fournisseur_id>/', views.supprimer_fournisseur, name='supprimer_fournisseur'),

    # Utilisateurs (admin)
    path('utilisateurs/', views.liste_utilisateurs, name='liste_utilisateurs'),
    path('utilisateurs/ajouter/', views.ajouter_utilisateur, name='ajouter_utilisateur'),
    path('utilisateurs/modifier/<int:user_id>/', views.modifier_utilisateur, name='modifier_utilisateur'),
    path('utilisateurs/supprimer/<int:user_id>/', views.supprimer_utilisateur, name='supprimer_utilisateur'),

    # Configuration
    path('config/', views.config_app, name='config_app'),

    # Alertes et gestion des stocks
    path('alertes-stock/', views.alertes_stock, name='alertes_stock'),
    path('stocks/', views.gestion_stock, name='gestion_stock'),
    path('stocks/historique/<int:produit_id>/', views.historique_stock_produit, name='historique_stock_produit'),
]