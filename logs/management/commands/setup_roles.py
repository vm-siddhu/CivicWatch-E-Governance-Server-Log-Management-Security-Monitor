from django.core.management.base import BaseCommand
from logs.roles import ensure_roles_exist

class Command(BaseCommand):
    help = "Create the standard monitoring roles and grant their baseline permissions."

    def handle(self, *args, **options):
        ensure_roles_exist()
        self.stdout.write(self.style.SUCCESS("Monitoring roles created and synchronized successfully."))
