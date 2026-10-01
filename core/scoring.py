from decimal import Decimal

from django.db.models import Max

from .models import (
    ProgressSubmission,
    ScoreParameter
)


# ============================================================
# SCORING TABLES
# ============================================================

LEVEL_POINTS = {

    # Learning & Certification /10
    'LEARNING': {

        'CERT_3_PLUS': 10,
        'CERT_2': 8,
        'CERT_1': 6,
        'MOOC': 4,
        'STRUCTURED': 2,
        'NONE': 0,
    },


    # Technical Skills & Projects /15
    'TECHNICAL': {

        'NATIONAL_INTL': 15,
        'MAJOR_ACHIEVEMENT': 12,
        'FUNCTIONAL_PROJECT': 10,
        'ENGINEERING_EXPLORATION': 8,
        'PARTICIPATION': 5,
        'BASIC': 3,
        'NONE': 0,
    },


    # Internship & Industry Exposure /10
    'INTERNSHIP': {

        'EXCELLENT_PPO': 10,
        'SIX_PLUS_WEEKS': 8,
        'FOUR_FIVE_WEEKS': 6,
        'SHORT_TERM': 4,
        'VISIT_INTERACTION': 2,
        'NONE': 0,
    },


    # Research / Innovation / IPR /10
    'RESEARCH': {

        'GRANTED_PATENT': 10,
        'PATENT_SCOPUS_WOS': 9,
        'PUBLICATION_PROJECT': 7,
        'PAPER_IIC': 5,
        'PROTOTYPE_IDEA': 3,
        'AWARENESS': 1,
        'NONE': 0,
    },


    # Placement & Career /10
    'CAREER': {

        'PLACED_HIGHER_STUDIES': 10,
        'ADVANCED_READINESS': 8,
        'STRONG_ASSESSMENT': 6,
        'TRAINING_COMPLETED': 4,
        'CAREER_PROGRAMME': 2,
        'NONE': 0,
    },


    # Leadership /5
    'LEADERSHIP': {

        'MAJOR_LEADER': 5,
        'CLUB_LEADER': 4,
        'REGULAR_PARTICIPATION': 3,
        'MENTOR_ACTIVITY': 2,
        'MEMBERSHIP': 1,
        'NONE': 0,
    },


    # Social responsibility /5
    'SOCIAL': {

        'LED_MAJOR': 5,
        'THREE_PLUS': 4,
        'TWO_ACTIVITIES': 3,
        'ONE_ACTIVITY': 2,
        'AWARENESS': 1,
        'NONE': 0,
    },


    # Sports / Cultural /5
    'SPORTS': {

        'NATIONAL_INTL': 5,
        'STATE_UNIVERSITY': 4,
        'DISTRICT_REGIONAL': 3,
        'INSTITUTIONAL': 2,
        'PARTICIPATION': 1,
        'NONE': 0,
    },
}


# ============================================================
# ACADEMIC PERFORMANCE /20
# ============================================================

def academic_points(value):

    value = Decimal(
        str(value)
    )

    if value >= Decimal('9.0'):
        return 20

    if value >= Decimal('8.0'):
        return 17

    if value >= Decimal('7.0'):
        return 14

    if value >= Decimal('6.0'):
        return 10

    if value >= Decimal('5.0'):
        return 6

    return 3


# ============================================================
# ATTENDANCE /10
# ============================================================

def attendance_points(
    percentage
):

    percentage = Decimal(
        str(percentage)
    )

    if percentage >= 95:
        return 10

    if percentage >= 90:
        return 8

    if percentage >= 85:
        return 6

    if percentage >= 80:
        return 4

    return 0


# ============================================================
# CALCULATE ONE SUBMISSION
# ============================================================

def calculate_submission_points(
    submission
):

    code = (
        submission.parameter.code
    )

    details = (
        submission.details or {}
    )


    # ----------------------------------------
    # ACADEMIC PERFORMANCE
    # ----------------------------------------

    if code == 'ACADEMIC':

        basis = details.get(
            'basis'
        )


        if basis in [
            'CGPA',
            'SGPA'
        ]:

            value = details.get(
                'academic_value'
            )

            return academic_points(
                value
            )


        if basis == 'PLUS2':

            percentage = Decimal(
                str(
                    details.get(
                        'plus2_percentage',
                        0
                    )
                )
            )

            # Provisional conversion:
            # +2 percentage / 10
            equivalent = (
                percentage / Decimal('10')
            )

            return academic_points(
                equivalent
            )


        return 0


    # ----------------------------------------
    # ATTENDANCE
    # ----------------------------------------

    if code == 'ATTENDANCE':

        return attendance_points(
            details.get(
                'attendance_percentage',
                0
            )
        )


    # ----------------------------------------
    # ALL ACHIEVEMENT-LEVEL PARAMETERS
    # ----------------------------------------

    level = details.get(
        'level'
    )

    return LEVEL_POINTS.get(
        code,
        {}
    ).get(
        level,
        0
    )


# ============================================================
# OVERALL STUDENT SCORECARD
# Highest approved score only for each parameter.
# ============================================================

def student_scorecard(
    student,
    academic_year
):

    rows = []

    total = Decimal('0')


    parameters = (
        ScoreParameter.objects
        .filter(
            active=True
        )
        .order_by(
            'order'
        )
    )


    for parameter in parameters:

        result = (
            ProgressSubmission.objects
            .filter(
                student=student,
                academic_year=academic_year,
                parameter=parameter,
                status='HOD_APPROVED'
            )
            .aggregate(
                highest=Max(
                    'awarded_points'
                )
            )
        )


        points = (
            result['highest']
            or Decimal('0')
        )


        total += points


        rows.append({

            'parameter': parameter,

            'points': points,

            'max_points':
                parameter.max_points,
        })


    return {

        'rows': rows,

        'total': total,

        'category':
            performance_category(
                total
            ),
    }


def performance_category(
    total
):

    total = Decimal(
        str(total)
    )

    if total >= 90:
        return 'Exceptional'

    if total >= 80:
        return 'Excellent'

    if total >= 70:
        return 'Very Good'

    if total >= 60:
        return 'Good'

    if total >= 50:
        return 'Developing'

    return 'Needs Improvement'