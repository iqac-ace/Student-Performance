from django.core.management.base import BaseCommand

from core.models import ScoreParameter


PARAMETERS = [

    {
        'code': 'ACADEMIC',
        'name': 'Academic Performance',
        'max_points': 20,
        'order': 1,
        'description':
            'Based on CGPA/SGPA. '
            '+2 percentage may be used provisionally '
            'until first semester result is available.'
    },

    {
        'code': 'ATTENDANCE',
        'name': 'Attendance & Academic Discipline',
        'max_points': 10,
        'order': 2,
        'description':
            'Attendance percentage and regularity.'
    },

    {
        'code': 'LEARNING',
        'name': 'Learning & Certification',
        'max_points': 10,
        'order': 3,
        'description':
            'NPTEL, SWAYAM, Coursera, '
            'industry certifications and ODL.'
    },

    {
        'code': 'TECHNICAL',
        'name': 'Technical Skills & Projects',
        'max_points': 15,
        'order': 4,
        'description':
            'Projects, engineering exploration, '
            'hackathons and technical competitions.'
    },

    {
        'code': 'INTERNSHIP',
        'name': 'Internship & Industry Exposure',
        'max_points': 10,
        'order': 5,
        'description':
            'Internships, industry projects, '
            'industrial visits and expert interaction.'
    },

    {
        'code': 'RESEARCH',
        'name': 'Research, Innovation & IPR',
        'max_points': 10,
        'order': 6,
        'description':
            'Research, publications, patents, '
            'presentations and IIC.'
    },

    {
        'code': 'CAREER',
        'name': 'Placement & Career Readiness',
        'max_points': 10,
        'order': 7,
        'description':
            'Placement, aptitude, coding, '
            'communication and higher studies.'
    },

    {
        'code': 'LEADERSHIP',
        'name': 'Leadership & Student Engagement',
        'max_points': 5,
        'order': 8,
        'description':
            'Domain clubs, societies, mentoring '
            'and student leadership.'
    },

    {
        'code': 'SOCIAL',
        'name':
            'Social Responsibility & '
            'Institutional Contribution',
        'max_points': 5,
        'order': 9,
        'description':
            'NSS, UBA, SDG, outreach, IQAC '
            'and institutional activities.'
    },

    {
        'code': 'SPORTS',
        'name': 'Sports, Cultural & Achievements',
        'max_points': 5,
        'order': 10,
        'description':
            'Sports, cultural activities, '
            'awards and recognitions.'
    },
]


class Command(BaseCommand):

    help = (
        'Create/update the official '
        '100-point score parameters.'
    )


    def handle(
        self,
        *args,
        **options
    ):

        for item in PARAMETERS:

            ScoreParameter.objects.update_or_create(

                code=item['code'],

                defaults={

                    'name':
                        item['name'],

                    'max_points':
                        item['max_points'],

                    'order':
                        item['order'],

                    'description':
                        item['description'],

                    'active': True,
                }
            )


        self.stdout.write(

            self.style.SUCCESS(
                '10 score parameters configured.'
            )
        )