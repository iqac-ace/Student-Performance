import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):

    help = "Create the initial production IQAC superuser."

    def handle(self, *args, **options):

        username = os.environ.get(
            "INITIAL_ADMIN_USERNAME"
        )

        email = os.environ.get(
            "INITIAL_ADMIN_EMAIL",
            ""
        )

        password = os.environ.get(
            "INITIAL_ADMIN_PASSWORD"
        )

        if not username:
            raise CommandError(
                "INITIAL_ADMIN_USERNAME is not set."
            )

        if not password:
            raise CommandError(
                "INITIAL_ADMIN_PASSWORD is not set."
            )

        User = get_user_model()

        existing_user = User.objects.filter(
            username=username
        ).first()

        if existing_user:

            if existing_user.is_superuser:

                self.stdout.write(
                    self.style.SUCCESS(
                        "Initial superuser already exists."
                    )
                )

                return

            raise CommandError(
                "A normal user already exists "
                "with this username."
            )


        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Superuser '{user.username}' created."
            )
        )