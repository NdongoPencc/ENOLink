from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import ENO, Specialite
from algorithm.data_generator import ENO_DATA, SPECIALITES_DATA


class Command(BaseCommand):
    help = 'Initialise la base de données avec les 18 ENO et les spécialités de l\'UN-CHK'

    def add_arguments(self, parser):
        parser.add_argument('--superuser', action='store_true', help='Créer un superuser DFIP')
        parser.add_argument('--email', default='admin@unchk.edu.sn')
        parser.add_argument('--password', default='Admin1234!')
        parser.add_argument('--nom', default='Admin')
        parser.add_argument('--prenom', default='ENOLink')

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=== Initialisation ENOLink ==='))

        with transaction.atomic():
            # Créer les ENO
            nb_eno_crees = 0
            for data in ENO_DATA:
                eno, created = ENO.objects.get_or_create(
                    code=data['code'],
                    defaults={
                        'nom': data['nom'],
                        'region': data['region'],
                        'ville': data['ville'],
                        'latitude': data['latitude'],
                        'longitude': data['longitude'],
                        'est_actif': True,
                    }
                )
                if created:
                    nb_eno_crees += 1

            self.stdout.write(self.style.SUCCESS(
                f'✓ {nb_eno_crees} ENO créés ({ENO.objects.count()} au total)'
            ))

            # Créer les spécialités
            nb_spec_crees = 0
            for data in SPECIALITES_DATA:
                spec, created = Specialite.objects.get_or_create(
                    code=data['code'],
                    defaults={
                        'nom': data['nom'],
                        'niveau': data['niveau'],
                        'est_active': True,
                    }
                )
                if created:
                    nb_spec_crees += 1

            self.stdout.write(self.style.SUCCESS(
                f'✓ {nb_spec_crees} spécialités créées ({Specialite.objects.count()} au total)'
            ))

        # Pas de superuser dans core-service (géré par auth-service)
        if options['superuser']:
            self.stdout.write(self.style.WARNING('Le superuser est géré par auth-service.'))

        self.stdout.write(self.style.SUCCESS('\n=== Initialisation terminée ==='))
        self.stdout.write('ENO disponibles :')
        for eno in ENO.objects.all():
            self.stdout.write(f'  - {eno.code} : {eno.nom} ({eno.region})')
