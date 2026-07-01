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