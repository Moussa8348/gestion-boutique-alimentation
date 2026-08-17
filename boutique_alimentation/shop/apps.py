from django.apps import AppConfig

class ShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop'

    def ready(self):
        # Importer Session ici, après le chargement des apps
        try:
            from django.contrib.sessions.models import Session
            Session.objects.all().delete()
            print("✅ Toutes les sessions ont été supprimées. Les utilisateurs doivent se reconnecter.")
        except Exception as e:
            print(f"⚠️ Erreur lors du nettoyage des sessions : {e}")



from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_superuser(sender, **kwargs):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='Admin123!'
        )
        print("✅ Superutilisateur 'admin' créé avec succès !")


class ShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop'

    def ready(self):
        post_migrate.connect(create_superuser, sender=self)