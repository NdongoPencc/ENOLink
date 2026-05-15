from django.core.management.base import BaseCommand
from accounts.models import Utilisateur


class Command(BaseCommand):
    help = 'Crée le superuser DFIP initial'

    def handle(self, *args, **options):
        if not Utilisateur.objects.filter(email='admin@unchk.edu.sn').exists():
            Utilisateur.objects.create_superuser(
                email='admin@unchk.edu.sn',
                password='Admin1234!',
                nom='Admin',
                prenom='ENOLink',
                role=Utilisateur.Role.DFIP,
            )
            self.stdout.write('✓ Superuser créé : admin@unchk.edu.sn / Admin1234!')
        else:
            self.stdout.write('✓ Superuser déjà existant.')
