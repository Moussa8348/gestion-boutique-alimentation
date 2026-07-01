from collections import UserDict

from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from datetime import datetime, timedelta, timezone
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Produit, Vente, DetailVente, Achat, DetailAchat, Fournisseur, Categorie, Profil, Stock
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
# ==================== AUTHENTIFICATION ====================

def connexion(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if hasattr(user, 'profil'):
                if user.profil.role == 'admin':
                    messages.success(request, f'Bienvenue Administrateur {user.username} !')
                    return redirect('dashboard_admin')
                elif user.profil.role == 'comptable':
                    messages.success(request, f'Bienvenue Comptable {user.username} !')
                    return redirect('dashboard_comptable')
                else:
                    messages.success(request, f'Bienvenue Gérant {user.username} !')
                    return redirect('dashboard_gerant')
                
            else:
                Profil.objects.create(user=user, role='manager')
                messages.success(request, f'Bienvenue {user.username} !')
                return redirect('dashboard_gerant')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect')
    
    return render(request, 'shop/auth/connexion.html')

def deconnexion(request):
    logout(request)
    messages.info(request, 'Vous avez été déconnecté')
    return redirect('connexion')

# ==================== DASHBOARDS ====================

@login_required
def dashboard(request):
    if hasattr(request.user, 'profil') and request.user.profil.role == 'admin':
        return redirect('dashboard_admin')
    else:
        return redirect('dashboard_gerant')


@login_required
def dashboard_admin(request):
    """Dashboard pour l'administrateur"""
    
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'admin':
        messages.error(request, 'Accès réservé à l\'administrateur')
        return redirect('dashboard_gerant')
    
    aujourd_hui = datetime.now().date()
    debut_mois = aujourd_hui.replace(day=1)
    debut_annee = aujourd_hui.replace(month=1, day=1)
    
    # Statistiques globales
    total_produits = Produit.objects.count()
    produits_rupture = Produit.objects.filter(quantite_stock=0)
    produits_alerte = Produit.objects.filter(quantite_stock__lte=5, quantite_stock__gt=0)
    
    total_ventes = Vente.objects.count()
    ca_total = Vente.objects.aggregate(total=Sum('total'))['total'] or 0
    ca_jour = Vente.objects.filter(date_vente__date=aujourd_hui).aggregate(total=Sum('total'))['total'] or 0
    ca_mois = Vente.objects.filter(date_vente__date__gte=debut_mois).aggregate(total=Sum('total'))['total'] or 0
    ca_annee = Vente.objects.filter(date_vente__date__gte=debut_annee).aggregate(total=Sum('total'))['total'] or 0
    
    total_utilisateurs = User.objects.count()  # ← Utilise User de django.contrib.auth.models
    total_gerants = Profil.objects.filter(role='manager').count()
    
    # Ventes par mois (pour graphique)
    mois_noms = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
    ventes_par_mois = []
    
    for i in range(6):
        mois_num = aujourd_hui.month - i
        annee_num = aujourd_hui.year
        if mois_num <= 0:
            mois_num += 12
            annee_num -= 1
        ca_mois_valeur = Vente.objects.filter(
            date_vente__year=annee_num,
            date_vente__month=mois_num
        ).aggregate(total=Sum('total'))['total'] or 0
        ventes_par_mois.insert(0, {
            'mois': mois_noms[mois_num-1],
            'total': float(ca_mois_valeur)
        })
    
    context = {
        'total_produits': total_produits,
        'total_ventes': total_ventes,
        'ca_total': ca_total,
        'ca_jour': ca_jour,
        'ca_mois': ca_mois,
        'ca_annee': ca_annee,
        'produits_rupture': produits_rupture.count(),
        'produits_alerte': produits_alerte.count(),
        'produits_rupture_liste': produits_rupture[:10],
        'produits_alerte_liste': produits_alerte[:10],
        'total_utilisateurs': total_utilisateurs,
        'total_gerants': total_gerants,
        'dernieres_ventes': Vente.objects.all().order_by('-date_vente')[:10],
        'derniers_utilisateurs': User.objects.all().order_by('-date_joined')[:5],
        'ventes_par_mois': ventes_par_mois,
    }
    return render(request, 'shop/dashboard_admin.html', context)

@login_required
def dashboard_gerant(request):
    aujourd_hui = datetime.now().date()
    debut_mois = aujourd_hui.replace(day=1)
    
    produits_rupture = Produit.objects.filter(quantite_stock=0)
    produits_alerte = Produit.objects.filter(quantite_stock__lte=5, quantite_stock__gt=0)
    
    context = {
        'total_produits': Produit.objects.count(),
        'mes_ventes': Vente.objects.filter(agent=request.user).count(),
        'ca_total': Vente.objects.filter(agent=request.user).aggregate(total=Sum('total'))['total'] or 0,
        'ca_jour': Vente.objects.filter(agent=request.user, date_vente__date=aujourd_hui).aggregate(total=Sum('total'))['total'] or 0,
        'ca_mois': Vente.objects.filter(agent=request.user, date_vente__date__gte=debut_mois).aggregate(total=Sum('total'))['total'] or 0,
        'produits_rupture': produits_rupture.count(),
        'produits_alerte': produits_alerte.count(),
        'produits_rupture_liste': produits_rupture[:10],
        'produits_alerte_liste': produits_alerte[:10],
        'derniers_produits': Produit.objects.all().order_by('-created_at')[:5],
        'dernieres_ventes': Vente.objects.filter(agent=request.user).order_by('-date_vente')[:5],
        'stock_min_seuil': 5,
    }
    return render(request, 'shop/dashboard_gerant.html', context)

# ==================== PRODUITS ====================

@login_required
def liste_produits(request):
    """Liste des produits avec filtres"""
    
    produits = Produit.objects.all().order_by('-created_at')
    
    # Filtre par statut
    filtre_statut = request.GET.get('statut', 'all')
    
    if filtre_statut == 'available':
        produits = produits.filter(quantite_stock__gt=0)
    elif filtre_statut == 'low':
        produits = produits.filter(quantite_stock__lte=models.F('stock_min'), quantite_stock__gt=0)
    elif filtre_statut == 'out':
        produits = produits.filter(quantite_stock=0)
    
    # Filtre par recherche
    search = request.GET.get('search', '')
    if search:
        produits = produits.filter(
            models.Q(nom__icontains=search) |
            models.Q(sku__icontains=search) |
            models.Q(code_barre__icontains=search)
        )
    
    # Compteurs pour les filtres
    total_all = Produit.objects.count()
    total_available = Produit.objects.filter(quantite_stock__gt=0).count()
    total_low_stock = Produit.objects.filter(quantite_stock__lte=models.F('stock_min'), quantite_stock__gt=0).count()
    total_out_stock = Produit.objects.filter(quantite_stock=0).count()
    
    # Pagination
    paginator = Paginator(produits, 10)
    page_number = request.GET.get('page', 1)
    produits_page = paginator.get_page(page_number)
    
    context = {
        'produits': produits_page,
        'total_all': total_all,
        'total_available': total_available,
        'total_low_stock': total_low_stock,
        'total_out_stock': total_out_stock,
        'filtre_statut': filtre_statut,
        'search': search,
    }
    return render(request, 'shop/produits/liste.html', context)
@login_required
def ajouter_produit(request):
    """Ajouter un nouveau produit"""
    # Bloque le comptable
    if hasattr(request.user, 'profil') and request.user.profil.role == 'comptable':
        messages.error(request, "Vous n'avez pas les droits pour ajouter un produit.")
        return redirect('liste_produits')
    
    from .models import Categorie, Fournisseur
    
    categories = Categorie.objects.all()
    fournisseurs = Fournisseur.objects.filter(actif=True)
    
    if request.method == 'POST':
        try:
            produit = Produit.objects.create(
                nom=request.POST.get('nom'),
                unite=request.POST.get('unite', 'pcs'),
                categorie_id=request.POST.get('categorie') or None,
                fournisseur_id=request.POST.get('fournisseur') or None,
                prix_achat=request.POST.get('prix_achat'),
                prix_vente=request.POST.get('prix_vente'),
                quantite_stock=request.POST.get('quantite_stock', 0),
                stock_min=request.POST.get('stock_min', 5),
                date_expiration=request.POST.get('date_expiration') or None,
                description=request.POST.get('description', ''),
                sku=request.POST.get('sku', ''),
                is_active=request.POST.get('is_active') == 'on'
            )
            
            # Gérer l'image
            if request.FILES.get('image'):
                produit.image = request.FILES['image']
                produit.save()
            
            messages.success(request, f'Produit "{produit.nom}" ajouté avec succès !')
            return redirect('liste_produits')
        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')
    
    context = {
        'categories': categories,
        'fournisseurs': fournisseurs,
    }
    return render(request, 'shop/produits/ajouter.html', context)
@login_required
def modifier_produit(request, produit_id):
    """Modifier un produit existant"""
    # Bloque le comptable
    if hasattr(request.user, 'profil') and request.user.profil.role == 'comptable':
        messages.error(request, "Vous n'avez pas les droits pour modifier un produit.")
        return redirect('liste_produits')
    
    from .models import Categorie, Fournisseur
    
    produit = get_object_or_404(Produit, id=produit_id)
    categories = Categorie.objects.all()
    fournisseurs = Fournisseur.objects.filter(actif=True)
    
    if request.method == 'POST':
        try:
            produit.nom = request.POST.get('nom')
            produit.unite = request.POST.get('unite', 'pcs')
            produit.categorie_id = request.POST.get('categorie') or None
            produit.fournisseur_id = request.POST.get('fournisseur') or None
            produit.prix_achat = request.POST.get('prix_achat')
            produit.prix_vente = request.POST.get('prix_vente')
            produit.quantite_stock = request.POST.get('quantite_stock', 0)
            produit.stock_min = request.POST.get('stock_min', 5)
            produit.date_expiration = request.POST.get('date_expiration') or None
            produit.description = request.POST.get('description', '')
            produit.sku = request.POST.get('sku', '')
            produit.is_active = request.POST.get('is_active') == 'on'
            
            # Gérer l'image
            if request.FILES.get('image'):
                produit.image = request.FILES['image']
            
            produit.save()
            messages.success(request, f'Produit "{produit.nom}" modifié avec succès !')
            return redirect('liste_produits')
        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')
    
    context = {
        'produit': produit,
        'categories': categories,
        'fournisseurs': fournisseurs,
    }
    return render(request, 'shop/produits/modifier.html', context)
@login_required
def supprimer_produit(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id)

    # Vérifier les droits (gérant ou admin)
    if hasattr(request.user, 'profil') and request.user.profil.role == 'comptable':
        messages.error(request, "Vous n'avez pas les droits pour supprimer un produit.")
        return redirect('liste_produits')

    if request.method == 'POST':
        # Vérifier si le produit a des ventes ou achats associés
        a_des_ventes = DetailVente.objects.filter(produit=produit).exists()
        a_des_achats = DetailAchat.objects.filter(produit=produit).exists()

        if a_des_ventes or a_des_achats:
            # Désactiver au lieu de supprimer
            produit.is_active = False
            produit.save()
            messages.warning(request, f'Produit "{produit.nom}" a été désactivé (car il a déjà été vendu ou acheté).')
        else:
            # Supprimer définitivement
            produit.delete()
            messages.success(request, f'Produit "{produit.nom}" supprimé définitivement.')
        return redirect('liste_produits')

    return render(request, 'shop/produits/supprimer.html', {'produit': produit})
@login_required
def detail_produit(request, produit_id):
    """Afficher le détail d'un produit et ses historiques"""
    produit = get_object_or_404(Produit, id=produit_id)
    
    # Dernières ventes concernant ce produit
    ventes = DetailVente.objects.filter(produit=produit).select_related('vente').order_by('-vente__date_vente')[:10]
    
    # Derniers achats concernant ce produit
    achats = DetailAchat.objects.filter(produit=produit).select_related('achat').order_by('-achat__date_commande')[:10]
    
    context = {
        'produit': produit,
        'ventes': ventes,
        'achats': achats,
    }
    return render(request, 'shop/produits/detail.html', context)

# ==================== VENTES ====================

@login_required
def liste_ventes(request):
    """Liste des ventes selon le rôle"""
    from django.db import models
    from django.core.paginator import Paginator
    from django.utils import timezone
    from datetime import timedelta

    user_role = request.user.profil.role

    # Admin et comptable voient TOUTES les ventes
    if user_role in ['admin', 'comptable']:
        ventes = Vente.objects.all().order_by('-date_vente')
    else:  # Gérant
        ventes = Vente.objects.filter(agent=request.user).order_by('-date_vente')

    # Filtres
    search = request.GET.get('search', '')
    if search:
        ventes = ventes.filter(
            models.Q(numero__icontains=search) |
            models.Q(client__icontains=search)
        )

    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    if date_debut:
        ventes = ventes.filter(date_vente__date__gte=date_debut)
    if date_fin:
        ventes = ventes.filter(date_vente__date__lte=date_fin)

    aujourd_hui = timezone.now().date()
    debut_semaine = aujourd_hui - timedelta(days=aujourd_hui.weekday())
    debut_mois = aujourd_hui.replace(day=1)

    ca_jour = ventes.filter(date_vente__date=aujourd_hui).aggregate(total=Sum('total'))['total'] or 0
    ca_semaine = ventes.filter(date_vente__date__gte=debut_semaine).aggregate(total=Sum('total'))['total'] or 0
    ca_mois = ventes.filter(date_vente__date__gte=debut_mois).aggregate(total=Sum('total'))['total'] or 0

    paginator = Paginator(ventes, 10)
    page_number = request.GET.get('page', 1)
    ventes_page = paginator.get_page(page_number)

    context = {
        'ventes': ventes_page,
        'ca_jour': ca_jour,
        'ca_semaine': ca_semaine,
        'ca_mois': ca_mois,
        'search': search,
        'date_debut': date_debut,
        'date_fin': date_fin,
    }
    return render(request, 'shop/ventes/liste.html', context)
@login_required
def nouvelle_vente(request):
    """Enregistrer une nouvelle vente (bloqué pour le comptable)"""
    # Bloque le comptable
    if hasattr(request.user, 'profil') and request.user.profil.role == 'comptable':
        messages.error(request, "Vous n'avez pas l'autorisation d'ajouter une vente.")
        return redirect('liste_ventes')
    
    produits = Produit.objects.filter(is_active=True, quantite_stock__gt=0)
    
    if request.method == 'POST':
        client = request.POST.get('client', '')
        mode_paiement = request.POST.get('mode_paiement')
        produits_ids = request.POST.getlist('produits')
        quantites = request.POST.getlist('quantites')
        
        vente = Vente.objects.create(
            client=client,
            mode_paiement=mode_paiement,
            agent=request.user,
            statut='confirmée'
        )
        
        total_vente = 0
        for i, produit_id in enumerate(produits_ids):
            if produit_id and quantites[i]:
                produit = Produit.objects.get(id=produit_id)
                qte = int(quantites[i])
                
                if produit.quantite_stock < qte:
                    messages.error(request, f'Stock insuffisant pour {produit.nom}')
                    vente.delete()
                    return redirect('nouvelle_vente')
                
                DetailVente.objects.create(
                    vente=vente,
                    produit=produit,
                    quantite=qte,
                    prix=float(produit.prix_vente)
                )
                total_vente += qte * float(produit.prix_vente)
        
        vente.total = total_vente
        vente.save()
        
        messages.success(request, f'Vente enregistrée ! Total: {total_vente} FCFA')
        return redirect('liste_ventes')
    
    return render(request, 'shop/ventes/ajouter.html', {'produits': produits})
@login_required
def detail_vente(request, vente_id):
    """Afficher le détail d'une vente"""
    vente = get_object_or_404(Vente, id=vente_id)
    user_role = request.user.profil.role

    # Autoriser admin, comptable, ou le vendeur lui-même
    if not (user_role in ['admin', 'comptable'] or vente.agent == request.user):
        messages.error(request, "Vous n'avez pas accès à cette vente.")
        return redirect('liste_ventes')

    lignes = vente.lignes.all()
    return render(request, 'shop/ventes/detail.html', {'vente': vente, 'lignes': lignes})

# ==================== ACHATS ====================

@login_required
def liste_achats(request):
    """Liste des achats selon le rôle"""
    user_role = request.user.profil.role

    # Admin et comptable voient TOUS les achats
    if user_role in ['admin', 'comptable']:
        achats = Achat.objects.all().order_by('-date_commande')
    else:  # Gérant
        achats = Achat.objects.filter(user=request.user).order_by('-date_commande')

    total_achats = achats.count()
    total_depenses = achats.aggregate(total=Sum('total'))['total'] or 0
    achats_attente = achats.filter(statut='en_attente').count()

    paginator = Paginator(achats, 10)
    page_number = request.GET.get('page', 1)
    achats_page = paginator.get_page(page_number)

    context = {
        'achats': achats_page,
        'total_achats': total_achats,
        'total_depenses': total_depenses,
        'achats_attente': achats_attente,
    }
    return render(request, 'shop/achats/liste.html', context)

@login_required
def nouvel_achat(request):
    """Créer un nouvel achat (bloqué pour le comptable)"""
    # Bloque le comptable
    if hasattr(request.user, 'profil') and request.user.profil.role == 'comptable':
        messages.error(request, "Vous n'avez pas l'autorisation d'ajouter un achat.")
        return redirect('liste_achats')
    
    produits = Produit.objects.filter(is_active=True)
    fournisseurs = Fournisseur.objects.filter(actif=True)
    
    if request.method == 'POST':
        fournisseur_id = request.POST.get('fournisseur')
        produits_ids = request.POST.getlist('produits')
        quantites = request.POST.getlist('quantites')
        prix = request.POST.getlist('prix')
        
        if not fournisseur_id:
            messages.error(request, 'Veuillez sélectionner un fournisseur')
            return redirect('nouvel_achat')
        
        fournisseur = get_object_or_404(Fournisseur, id=fournisseur_id)
        achat = Achat.objects.create(
            fournisseur=fournisseur,
            user=request.user,
            statut='en_attente'
        )
        
        total_achat = 0
        for i, produit_id in enumerate(produits_ids):
            if produit_id and quantites[i]:
                produit = Produit.objects.get(id=produit_id)
                qte = int(quantites[i])
                prix_unitaire = float(prix[i]) if prix[i] else float(produit.prix_achat)
                
                DetailAchat.objects.create(
                    achat=achat,
                    produit=produit,
                    quantite=qte,
                    prix=prix_unitaire
                )
                total_achat += qte * prix_unitaire
        
        achat.total = total_achat
        achat.save()
        
        messages.success(request, f'Achat enregistré ! Total: {total_achat:,.0f} FCFA')
        return redirect('liste_achats')
    
    return render(request, 'shop/achats/ajouter.html', {
        'produits': produits,
        'fournisseurs': fournisseurs
    })
  
@login_required
def changer_statut_achat(request, achat_id):
    """Changer le statut d'un achat (admin ou gérant)"""
    achat = get_object_or_404(Achat, id=achat_id)
    
    if request.method == 'POST':
        nouveau_statut = request.POST.get('statut')
        if nouveau_statut in dict(Achat.STATUT_CHOICES).keys():
            achat.statut = nouveau_statut
            achat.save()
            messages.success(request, f"Statut de l'achat #{achat.id} changé en '{achat.get_statut_display()}'")
        else:
            messages.error(request, "Statut invalide")
    
    return redirect('liste_achats')
@login_required
def detail_achat(request, achat_id):
    """Afficher le détail d'un achat"""
    achat = get_object_or_404(Achat, id=achat_id)
    user_role = request.user.profil.role

    if not (user_role in ['admin', 'comptable'] or achat.user == request.user):
        messages.error(request, "Vous n'avez pas accès à cet achat.")
        return redirect('liste_achats')

    lignes = achat.lignes.all()
    return render(request, 'shop/achats/detail.html', {'achat': achat, 'lignes': lignes})
# ==================== FOURNISSEURS ====================

@login_required
def liste_fournisseurs(request):
    """Liste des fournisseurs"""
    fournisseurs_list = Fournisseur.objects.all().order_by('-date_creation')
    paginator = Paginator(fournisseurs_list, 10)
    page_number = request.GET.get('page', 1)
    fournisseurs = paginator.get_page(page_number)
    return render(request, 'shop/fournisseurs/liste.html', {'fournisseurs': fournisseurs})

@login_required
def ajouter_fournisseur(request):
    if request.method == 'POST':
        fournisseur = Fournisseur.objects.create(
            nom=request.POST.get('nom'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            adresse=request.POST.get('adresse'),
            ville=request.POST.get('ville'),
            pays=request.POST.get('pays'),
            actif=request.POST.get('actif') == 'on'
        )
        messages.success(request, f'Fournisseur "{fournisseur.nom}" ajouté avec succès !')
        return redirect('liste_fournisseurs')
    return render(request, 'shop/fournisseurs/ajouter.html')

@login_required
def modifier_fournisseur(request, fournisseur_id):
    fournisseur = get_object_or_404(Fournisseur, id=fournisseur_id)
    if request.method == 'POST':
        fournisseur.nom = request.POST.get('nom')
        fournisseur.email = request.POST.get('email')
        fournisseur.phone = request.POST.get('phone')
        fournisseur.adresse = request.POST.get('adresse')
        fournisseur.ville = request.POST.get('ville')
        fournisseur.pays = request.POST.get('pays')
        fournisseur.actif = request.POST.get('actif') == 'on'
        fournisseur.save()
        messages.success(request, f'Fournisseur "{fournisseur.nom}" modifié avec succès !')
        return redirect('liste_fournisseurs')
    return render(request, 'shop/fournisseurs/modifier.html', {'fournisseur': fournisseur})

@login_required
def supprimer_fournisseur(request, fournisseur_id):
    fournisseur = get_object_or_404(Fournisseur, id=fournisseur_id)
    if request.method == 'POST':
        nom = fournisseur.nom
        fournisseur.delete()
        messages.success(request, f'Fournisseur "{nom}" supprimé avec succès !')
        return redirect('liste_fournisseurs')
    return render(request, 'shop/fournisseurs/supprimer.html', {'fournisseur': fournisseur})
# ==================== GESTION DES UTILISATEURS (ADMIN) ====================

@login_required
def liste_utilisateurs(request):
    """Liste des utilisateurs pour l'admin"""
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'admin':
        messages.error(request, 'Accès réservé à l\'administrateur')
        return redirect('dashboard_gerant')
    
    utilisateurs = User.objects.all().order_by('-date_joined')
    return render(request, 'shop/utilisateurs/liste.html', {'utilisateurs': utilisateurs})

@login_required
def ajouter_utilisateur(request):
    """Ajouter un utilisateur (gérant)"""
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'admin':
        messages.error(request, 'Accès réservé à l\'administrateur')
        return redirect('dashboard_gerant')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        role = request.POST.get('role')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Ce nom d\'utilisateur existe déjà')
            return redirect('ajouter_utilisateur')
        
        user = User.objects.create_user(username=username, password=password, email=email)
        Profil.objects.create(user=user, role=role)
        messages.success(request, f'Utilisateur {username} créé avec succès')
        return redirect('liste_utilisateurs')
    
    return render(request, 'shop/utilisateurs/ajouter.html')

@login_required
def modifier_utilisateur(request, user_id):
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'admin':
        messages.error(request, 'Accès réservé à l\'administrateur')
        return redirect('dashboard_gerant')

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        new_password = request.POST.get('password')
        if new_password:
            user.set_password(new_password)
        user.save()

        # Mise à jour du profil (rôle et avatar)
        profil, created = Profil.objects.get_or_create(user=user)
        profil.role = request.POST.get('role')
        if request.FILES.get('avatar'):
            profil.avatar = request.FILES['avatar']
        profil.save()

        messages.success(request, f'Utilisateur {user.username} modifié avec succès')
        return redirect('liste_utilisateurs')

    return render(request, 'shop/utilisateurs/modifier.html', {'utilisateur': user})
@login_required
def supprimer_utilisateur(request, user_id):
    """Supprimer un utilisateur"""
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'admin':
        messages.error(request, 'Accès réservé à l\'administrateur')
        return redirect('dashboard_gerant')
    
    user = get_object_or_404(User, id=user_id)
    
    if user == request.user:
        messages.error(request, 'Vous ne pouvez pas supprimer votre propre compte')
        return redirect('liste_utilisateurs')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'Utilisateur {username} supprimé')
        return redirect('liste_utilisateurs')
    
    return render(request, 'shop/utilisateurs/supprimer.html', {'utilisateur': user})
# ==================== CONFIGURATION DE L'APPLICATION ====================

@login_required
def config_app(request):
    """Page de configuration de l'application (Admin seulement)"""
    
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'admin':
        messages.error(request, 'Accès réservé à l\'administrateur')
        return redirect('dashboard_gerant')
    
    # Langues disponibles
    langues = [
        {'code': 'fr', 'nom': 'Français', 'flag': '🇫🇷'},
        {'code': 'en', 'nom': 'English', 'flag': '🇬🇧'},
        {'code': 'ar', 'nom': 'العربية', 'flag': '🇸🇦'},
    ]
    
    # Thèmes disponibles
    themes = [
        {'code': 'light', 'nom': 'Clair', 'icon': '☀️'},
        {'code': 'dark', 'nom': 'Sombre', 'icon': '🌙'},
        {'code': 'blue', 'nom': 'Bleu', 'icon': '💙'},
    ]
    
    context = {
        'langues': langues,
        'themes': themes,
    }
    return render(request, 'shop/config/config.html', context)
# ==================== ALERTES DE STOCK ====================
@login_required
def alertes_stock(request):
    """Voir tous les produits en alerte stock"""
    produits_rupture = Produit.objects.filter(quantite_stock=0)
    produits_alerte = Produit.objects.filter(quantite_stock__lte=5, quantite_stock__gt=0)
    
    context = {
        'produits_rupture': produits_rupture,
        'produits_alerte': produits_alerte,
        'total_rupture': produits_rupture.count(),
        'total_alerte': produits_alerte.count(),
    }
    return render(request, 'shop/alertes_stock.html', context)
# ====================la parti comptabilité de notre aplli====================


@login_required
def dashboard_comptable(request):
    """Dashboard financier réservé à l'admin et au comptable"""
    if not hasattr(request.user, 'profil') or request.user.profil.role not in ['admin', 'comptable']:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard_gerant')
    
    today = timezone.now().date()
    first_day_month = today.replace(day=1)
    first_day_year = today.replace(month=1, day=1)
    
    # Chiffre d'affaires
    ca_total = Vente.objects.aggregate(total=Sum('total'))['total'] or 0
    ca_jour = Vente.objects.filter(date_vente__date=today).aggregate(total=Sum('total'))['total'] or 0
    ca_mois = Vente.objects.filter(date_vente__date__gte=first_day_month).aggregate(total=Sum('total'))['total'] or 0
    ca_annee = Vente.objects.filter(date_vente__date__gte=first_day_year).aggregate(total=Sum('total'))['total'] or 0
    
    # Dépenses (achats reçus)
    depenses_total = Achat.objects.filter(statut='reçu').aggregate(total=Sum('total'))['total'] or 0
    depenses_mois = Achat.objects.filter(statut='reçu', date_commande__date__gte=first_day_month).aggregate(total=Sum('total'))['total'] or 0
    
    # Bénéfices
    benefice_total = ca_total - depenses_total
    benefice_mois = ca_mois - depenses_mois
    
    # Marge bénéficiaire
    marge = (benefice_total / ca_total * 100) if ca_total > 0 else 0
    
    # Panier moyen
    nb_ventes = Vente.objects.count()
    panier_moyen = ca_total / nb_ventes if nb_ventes > 0 else 0
    
    # Graphique CA sur 6 mois
    mois_noms = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
    ca_par_mois = []
    for i in range(6):
        mois_num = today.month - i
        annee_num = today.year
        if mois_num <= 0:
            mois_num += 12
            annee_num -= 1
        ca = Vente.objects.filter(
            date_vente__year=annee_num,
            date_vente__month=mois_num
        ).aggregate(total=Sum('total'))['total'] or 0
        ca_par_mois.insert(0, {
            'mois': mois_noms[mois_num-1],
            'ca': float(ca)
        })
    
    context = {
        'ca_total': ca_total,
        'ca_jour': ca_jour,
        'ca_mois': ca_mois,
        'ca_annee': ca_annee,
        'depenses_total': depenses_total,
        'depenses_mois': depenses_mois,
        'benefice_total': benefice_total,
        'benefice_mois': benefice_mois,
        'marge': marge,
        'panier_moyen': panier_moyen,
        'ca_par_mois': ca_par_mois,
    }
    return render(request, 'shop/dashboard_comptable.html', context)
# ====================la gestons des stocks====================
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Produit

@login_required
def gestion_stock(request):
    produits = Produit.objects.filter(is_active=True).order_by('categorie__nom', 'nom')
    context = {
        'produits': produits,
        'total_produits': produits.count(),
        'produits_rupture': produits.filter(quantite_stock=0).count(),
        'produits_faible': produits.filter(quantite_stock__lte=5, quantite_stock__gt=0).count(),
    }
    return render(request, 'shop/stocks/gestion.html', context)
# ====================historique des stocks====================
@login_required
def historique_stock_produit(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id)
    
    # Récupérer les achats (entrées)
    achats = DetailAchat.objects.filter(produit=produit).select_related('achat').order_by('-achat__date_commande')
    # Récupérer les ventes (sorties)
    ventes = DetailVente.objects.filter(produit=produit).select_related('vente').order_by('-vente__date_vente')
    
    # Construire une liste de mouvements
    mouvements = []
    for a in achats:
        mouvements.append({
            'date': a.achat.date_commande,
            'type': 'Entrée',
            'quantite': a.quantite,
            'reference': f"Achat #{a.achat.id}",
            'prix': a.prix,
        })
    for v in ventes:
        mouvements.append({
            'date': v.vente.date_vente,
            'type': 'Sortie',
            'quantite': -v.quantite,
            'reference': f"Vente {v.vente.numero}",
            'prix': v.prix,
        })
    # Trier par date décroissante
    mouvements.sort(key=lambda x: x['date'], reverse=True)
    
    context = {
        'produit': produit,
        'mouvements': mouvements[:50],  # 50 derniers mouvements
    }
    return render(request, 'shop/stocks/historique.html', context)
# ==================== GESTION DES CATÉGORIES ====================
# ==================== GESTION DES CATÉGORIES ====================

@login_required
def liste_categories(request):
    if request.user.profil.role == 'comptable':
        messages.error(request, "Accès non autorisé.")
        return redirect('dashboard_comptable')
    categories = Categorie.objects.all().order_by('-date_creation')
    return render(request, 'shop/categories/liste.html', {'categories': categories})

@login_required
def ajouter_categorie(request):
    if request.user.profil.role == 'comptable':
        messages.error(request, "Accès non autorisé.")
        return redirect('dashboard_comptable')
    if request.method == 'POST':
        nom = request.POST.get('nom')
        description = request.POST.get('description', '')
        image = request.FILES.get('image')
        if Categorie.objects.filter(nom=nom).exists():
            messages.error(request, "Cette catégorie existe déjà.")
            return redirect('ajouter_categorie')
        Categorie.objects.create(nom=nom, description=description, image=image)
        messages.success(request, f"Catégorie '{nom}' ajoutée.")
        return redirect('liste_categories')
    return render(request, 'shop/categories/ajouter.html')

@login_required
def modifier_categorie(request, categorie_id):
    if request.user.profil.role == 'comptable':
        messages.error(request, "Accès non autorisé.")
        return redirect('dashboard_comptable')
    categorie = get_object_or_404(Categorie, id=categorie_id)
    if request.method == 'POST':
        categorie.nom = request.POST.get('nom')
        categorie.description = request.POST.get('description', '')
        if request.FILES.get('image'):
            categorie.image = request.FILES['image']
        categorie.save()
        messages.success(request, f"Catégorie '{categorie.nom}' modifiée.")
        return redirect('liste_categories')
    return render(request, 'shop/categories/modifier.html', {'categorie': categorie})

@login_required
def supprimer_categorie(request, categorie_id):
    if request.user.profil.role == 'comptable':
        messages.error(request, "Accès non autorisé.")
        return redirect('dashboard_comptable')
    categorie = get_object_or_404(Categorie, id=categorie_id)
    if request.method == 'POST':
        if categorie.produits.count() > 0:
            messages.error(request, f"Impossible : {categorie.produits.count()} produit(s) associé(s).")
            return redirect('liste_categories')
        nom = categorie.nom
        categorie.delete()
        messages.success(request, f"Catégorie '{nom}' supprimée.")
        return redirect('liste_categories')
    return render(request, 'shop/categories/supprimer.html', {'categorie': categorie})


from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

def custom_password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # Générer le token et l'uid
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            # Construire le lien complet
            reset_url = request.build_absolute_uri(
                reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            # Passer le lien au template pour l'afficher
            return render(request, 'shop/auth/password_reset_link.html', {'reset_url': reset_url, 'email': email})
        except User.DoesNotExist:
            messages.error(request, "Aucun utilisateur avec cet email.")
    return render(request, 'shop/auth/custom_password_reset.html')