
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User


# ===================== Custom User =====================


class Profil(models.Model): 
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('manager', 'Gérant'),
        ('comptable', 'Comptable'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE) 
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, 
                            default='manager')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
# ==================== Categorie ====================


class Categorie(models.Model):
    nom = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom

# ==================== Fournisseur ====================


class Fournisseur(models.Model):
    nom = models.CharField(max_length=150)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20)
    adresse = models.CharField(max_length=255)
    ville = models.CharField(max_length=100)
    pays = models.CharField(max_length=100)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom

# ==================== Produit ====================


class Produit(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogramme'),
        ('l', 'Litre'),
        ('pcs', 'Pièce'),
        ('box', 'Boîte'),
        ('pack', 'Pack'),
        ('g', 'Gramme'),
    ]

    nom = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    unite = models.CharField(max_length=10, choices=UNIT_CHOICES, 
                             default='pcs')
    
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    code_barre = models.CharField(max_length=100, unique=True, blank=True, 
                                  null=True)

    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, 
                                  null=True, blank=True, 
                                  related_name="produits")
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL,
                                    null=True, blank=True, 
                                    related_name="produits")

    prix_achat = models.DecimalField(max_digits=10, decimal_places=2,
                                     validators=[MinValueValidator(0)])
    prix_vente = models.DecimalField(max_digits=10, decimal_places=2,
                                     validators=[MinValueValidator(0)])

    quantite_stock = models.IntegerField(default=0, 
                                         validators=[MinValueValidator(0)])
    stock_min = models.IntegerField(default=5, 
                                    validators=[MinValueValidator(0)])

    image = models.ImageField(upload_to="produits/", blank=True, null=True)
    date_expiration = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['code_barre']),
            models.Index(fields=['categorie']),
        ]

    def __str__(self):
        return self.nom

    def marge_beneficiaire(self):
        if self.prix_achat and self.prix_achat > 0:
            return ((self.prix_vente - self.prix_achat) / self.prix_achat)*100
        return 0
    
    @property
    def stock_faible(self):
        return self.quantite_stock <= self.stock_min

    @property
    def est_expire(self):
        if self.date_expiration:
            return self.date_expiration < timezone.now().date()
        return False
    def derniers_mouvements(self, limit=5):
        """Retourne les derniers mouvements de stock (entrées/sorties)"""
        return self.stock_movements.all().order_by('-created_at')[:limit]   

# ==================== Stock (Mouvements) ====================


class Stock(models.Model):
    MOVEMENT_TYPE_CHOICES = [
        ('in', 'Entrée'),
        ('out', 'Sortie'),
        ('return', 'Retour'),
    ]

    produit = models.ForeignKey(Produit, on_delete=models.PROTECT,
                                related_name='stock_movements')
    type_mouvement = models.CharField(max_length=20, 
                                      choices=MOVEMENT_TYPE_CHOICES)
    quantite = models.IntegerField(validators=[MinValueValidator(1)])
    reference = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True) 
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, 
                                    on_delete=models.SET_NULL, 
                                    null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.produit.nom} - {self.type_mouvement} ({self.quantite})"

# ==================== Vente ====================


class Vente(models.Model):
    STATUT_CHOICES = [
        ('confirmée', 'Confirmée'),
        ('annulée', 'Annulée'),
    ]
    MODE_PAIEMENT = [
        ('especes', 'Espèces'),
        ('carte', 'Carte bancaire'),
        ('cheque', 'Chèque'),
        ('moneyElectronique', 'Money électronique'),
    ]
    
    numero = models.CharField(max_length=50, unique=True, blank=True)
    client = models.CharField(max_length=150, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mode_paiement = models.CharField(max_length=50, choices=MODE_PAIEMENT)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, 
                              default='confirmée')
    agent = models.ForeignKey(settings.AUTH_USER_MODEL, 
                              on_delete=models.CASCADE)
    date_vente = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.numero:
            year = timezone.now().year
            last_sale = Vente.objects.filter(
                numero__startswith=f"VTE-{year}").order_by('id').last()
            if last_sale:
                last_number = int(last_sale.numero.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.numero = f"VTE-{year}-{new_number:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.numero
    

class DetailVente(models.Model):
    vente = models.ForeignKey(Vente, on_delete=models.CASCADE, 
                              related_name="lignes")
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT)
    quantite = models.PositiveIntegerField()
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    note = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        self.total = self.quantite * self.prix
        
        with transaction.atomic():
            # Vérification et mise à jour du stock (uniquement pour les nouvelles lignes)
            if not self.pk:
                if self.produit.quantite_stock < self.quantite:
                    raise ValueError(f"Stock insuffisant pour {self.produit.nom}")
                
                # Diminuer le stock
                self.produit.quantite_stock -= self.quantite
                self.produit.save()
                
                # Enregistrer le mouvement de stock
                Stock.objects.create(
                    produit=self.produit,
                    type_mouvement='out',
                    quantite=self.quantite,
                    reference=self.vente.numero,
                    notes=self.note,
                    utilisateur=self.vente.agent
                )
            
            # Sauvegarder le détail
            super().save(*args, **kwargs)
            
            # Recalculer le total de la vente
            self.vente.total = sum(l.total for l in self.vente.lignes.all())
            self.vente.save(update_fields=['total'])

    def __str__(self):
        return f"{self.produit.nom} ({self.quantite})"

# ==================== Achat ====================


class Achat(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('commandé', 'Commandé'),
        ('partiel', 'Réception partielle'),
        ('reçu', 'Reçu'),
        ('annulé', 'Annulé'),
    ]
    
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.PROTECT)
    date_commande = models.DateTimeField(auto_now_add=True)
    date_livraison = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, 
                              default='en_attente')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    note = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    def __str__(self):
        return f"Achat {self.id} - {self.fournisseur.nom}"


class DetailAchat(models.Model):
    achat = models.ForeignKey(Achat, on_delete=models.CASCADE, 
                              related_name="lignes")
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT)
    quantite = models.PositiveIntegerField()
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    note = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        self.total = self.quantite * self.prix
        
        with transaction.atomic():
            # Sauvegarder d'abord
            super().save(*args, **kwargs)
            
            # Mise à jour du stock (uniquement pour les nouvelles lignes)
            if not self.pk:
                # Augmenter le stock
                self.produit.quantite_stock += self.quantite
                self.produit.save()
                
                # Enregistrer le mouvement de stock
                Stock.objects.create(
                    produit=self.produit,
                    type_mouvement='in',
                    quantite=self.quantite,
                    reference=f"Achat-{self.achat.id}",
                    notes=self.note,
                    utilisateur=self.achat.user
                )
            
            # Recalculer le total de l'achat
            self.achat.total = sum(l.total for l in self.achat.lignes.all())
            self.achat.save(update_fields=['total'])

    def __str__(self):
        return f"{self.produit.nom} ({self.quantite})"

# ==================== Commande Client ====================


class Commande(models.Model):
    STATUT_COMMANDE = (
        ("EN_ATTENTE", "En attente"),
        ("VALIDE", "Validée"),
        ("ANNULE", "Annulée"),
    )

    reference = models.CharField(max_length=100, unique=True)
    client = models.CharField(max_length=150, blank=True)
    date_commande = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=STATUT_COMMANDE, 
                              default="EN_ATTENTE")
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, 
                                 on_delete=models.CASCADE)

    class Meta:
        ordering = ["-date_commande"]

    def save(self, *args, **kwargs):
        if not self.reference:
            from django.utils.crypto import get_random_string
            self.reference = f"CMD-{get_random_string(8).upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Commande {self.reference}"

# ==================== Détails du produit ====================


class DetailProduit(models.Model):
    produit = models.OneToOneField(Produit, on_delete=models.CASCADE, 
                                   related_name='detail')
    poids = models.DecimalField(max_digits=10, decimal_places=2, 
                                blank=True, null=True)
    couleur = models.CharField(max_length=50, blank=True)
    taille = models.CharField(max_length=50, blank=True)
    date_fabrication = models.DateField(blank=True, null=True)
    date_expiration = models.DateField(blank=True, null=True)
    garantie = models.CharField(max_length=100, blank=True)
    description_detail = models.TextField(blank=True)

    def __str__(self):
        return f"Détails - {self.produit.nom}"

# ==================== Rapports ====================


class Rapport(models.Model):
    TYPE_RAPPORT = [
        ('vente', 'Ventes'),
        ('achat', 'Achats'),
        ('stock', 'Stock'),
        ('client', 'Clients'),
    ]
    type = models.CharField(max_length=20, choices=TYPE_RAPPORT)
    titre = models.CharField(max_length=200)
    contenu = models.TextField()
    fichier = models.FileField(upload_to='rapports/', blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, 
                             on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titre} - {self.created_at.strftime('%d/%m/%Y')}"

# ==================== Historique (Traceur générique) ====================


class Historique(models.Model):
    ACTION_CHOICES = [
        ('C', 'Création'),
        ('M', 'Modification'),
        ('S', 'Suppression'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, 
                             on_delete=models.CASCADE)
    action = models.CharField(max_length=1, choices=ACTION_CHOICES)
    date_action = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey('content_type', 'object_id')
    anciennes_valeurs = models.JSONField(null=True, blank=True)
    nouvelles_valeurs = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-date_action']

    def __str__(self):
        return f"{self.get_action_display()} - {self.target} le {self.date_action.strftime('%d/%m/%Y %H:%M:%S')} par {self.user.username}"