import time

from django.core.management.base import BaseCommand
from django.db.utils import OperationalError
from psycopg import OperationalError as PsycopgOperationalError


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')
        db_up = False
        while not db_up:
            try:
                self.check(databases=['default'])
                db_up = True
            except (PsycopgOperationalError, OperationalError):
                self.stdout.write('Database down, waiting 1 seconds...')
                time.sleep(1)
        self.stdout.write(self.style.SUCCESS('Database available!'))
