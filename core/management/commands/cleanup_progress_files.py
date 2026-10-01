from datetime import timedelta

from django.core.management.base import (
    BaseCommand
)

from django.utils import timezone

from core.models import ProgressSubmission


class Command(BaseCommand):

    help = (
        'Delete evidence files belonging '
        'to rejected submissions older '
        'than 24 hours.'
    )


    def handle(
        self,
        *args,
        **options
    ):

        cutoff = (
            timezone.now()
            - timedelta(hours=24)
        )


        submissions = (
            ProgressSubmission.objects
            .filter(
                status='REJECTED',
                verified_at__lte=cutoff
            )
            .exclude(
                evidence=''
            )
        )


        deleted = 0


        for submission in submissions:

            if submission.evidence:

                submission.evidence.delete(
                    save=False
                )

                submission.evidence = ''

                submission.save(
                    update_fields=[
                        'evidence'
                    ]
                )

                deleted += 1


        self.stdout.write(

            self.style.SUCCESS(
                f'{deleted} old rejected '
                f'evidence file(s) deleted.'
            )
        )