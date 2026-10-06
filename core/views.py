import json
from decimal import Decimal, InvalidOperation
import os
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render,redirect,get_object_or_404
from django.db.models import Avg,Count,Q
from django.db import transaction
from django.utils import timezone
from django.views.decorators.http import require_POST
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, Alignment
from datetime import datetime
from datetime import timedelta 
from .models import *
from .forms import *
from .progress_rules import PROGRESS_RULES
from .utils import student_spi
from .models import (Profile,Department,Student,AuditLog,ProgressSubmission,ScoreParameter)
from .forms import StaffCreateForm
from .scoring import (calculate_submission_points, student_scorecard)
from .forms import (StudentForm,SubjectForm,SemesterResultForm,ActivityForm,ExcelUploadForm,StaffCreateForm,StudentProgressForm,ProgressSubmissionForm)

def role(user):

    if user.is_superuser:
        return 'IQAC'

    try:
        return user.profile.role
    except Profile.DoesNotExist:
        return None

def current_academic_year():

    today = timezone.localdate()

    if today.month >= 6:
        return f"{today.year}-{today.year + 1}"

    return f"{today.year - 1}-{today.year}"

def dept_scope(user, qs):

    r = role(user)

    # IQAC can see every student
    if r == 'IQAC' or user.is_superuser:
        return qs

    # Student can see ONLY their own record
    if r == 'STUDENT':

        try:

            if user.profile.student_id:

                return qs.filter(
                    pk=user.profile.student_id
                )

        except Profile.DoesNotExist:
            pass

        return qs.none()

    # HOD / Faculty see only their department
    try:

        return qs.filter(
            department=user.profile.department
        )

    except Profile.DoesNotExist:

        return qs.none()


@login_required
def dashboard(request):

    current_role = role(request.user)

    # =====================================
    # STUDENT LOGIN
    # =====================================

    if current_role == 'STUDENT':

        try:
            student = request.user.profile.student
        except:
            student = None

        if not student:
            return HttpResponseForbidden(
                'Student account is not linked to a student record.'
            )

        return redirect(
            'student_detail',
            pk=student.pk
        )


    # =====================================
    # IQAC / HOD / FACULTY STUDENT SCOPE
    # =====================================

    students_qs = dept_scope(
        request.user,
        Student.objects.filter(
            active=True
        )
    )


    # =====================================
    # DEPARTMENT SCOPE
    # =====================================

    departments = Department.objects.filter(
        active=True
    )

    if (
        current_role != 'IQAC'
        and not request.user.is_superuser
    ):

        departments = departments.filter(
            id=request.user.profile.department_id
        )


    # =====================================
    # BASIC COUNTS
    # =====================================

    total_students = students_qs.count()

    total_departments = departments.count()

    total_semester_results = SemesterResult.objects.filter(
        student__in=students_qs
    ).count()

    total_marks = SubjectMark.objects.filter(
        student__in=students_qs
    ).count()

    total_activities = ActivityEvidence.objects.filter(
        student__in=students_qs
    ).count()


    # =====================================
    # PENDING APPROVALS
    # =====================================

    pending_marks = SubjectMark.objects.filter(
        student__in=students_qs,
        status='PENDING'
    ).count()

    pending_semesters = SemesterResult.objects.filter(
        student__in=students_qs,
        status='PENDING'
    ).count()

    pending_activities = ActivityEvidence.objects.filter(
        student__in=students_qs,
        status='PENDING'
    ).count()

    total_pending = (
        pending_marks
        + pending_semesters
        + pending_activities
    )


    # =====================================
    # APPROVED RECORDS
    # =====================================

    approved_marks = SubjectMark.objects.filter(
        student__in=students_qs,
        status='IQAC_APPROVED'
    ).count()

    approved_semesters = SemesterResult.objects.filter(
        student__in=students_qs,
        status='IQAC_APPROVED'
    ).count()

    approved_activities = ActivityEvidence.objects.filter(
        student__in=students_qs,
        status='IQAC_APPROVED'
    ).count()


    # =====================================
    # AVERAGE CGPA
    # =====================================

    avg_cgpa = SemesterResult.objects.filter(
        student__in=students_qs
    ).aggregate(
        value=Avg('cgpa')
    )['value'] or 0


    # =====================================
    # AVERAGE 12TH %
    # =====================================

    avg_class12 = students_qs.aggregate(
        value=Avg('class12_percentage')
    )['value'] or 0


    # =====================================
    # DEPARTMENT PERFORMANCE
    # =====================================

    department_stats = []

    for department in departments:

        department_students = students_qs.filter(
            department=department
        )

        dept_avg_12 = department_students.aggregate(
            value=Avg('class12_percentage')
        )['value'] or 0

        dept_avg_cgpa = SemesterResult.objects.filter(
            student__in=department_students
        ).aggregate(
            value=Avg('cgpa')
        )['value'] or 0

        dept_results = SemesterResult.objects.filter(
            student__in=department_students
        ).count()

        department_stats.append(
            {
                'id': department.id,
                'code': department.code,
                'name': department.name,
                'students': department_students.count(),
                'avg12': round(
                    float(dept_avg_12),
                    2
                ),
                'avgcgpa': round(
                    float(dept_avg_cgpa),
                    2
                ),
                'results': dept_results
            }
        )


    # =====================================
    # PREVIOUS / RECENT SEMESTER RESULTS
    # =====================================

    recent_semester_results = SemesterResult.objects.filter(
        student__in=students_qs
    ).select_related(
        'student',
        'student__department'
    ).order_by(
        '-id'
    )[:10]


    # =====================================
    # PREVIOUS MARK RECORDS
    # =====================================

    recent_marks = SubjectMark.objects.filter(
        student__in=students_qs
    ).select_related(
        'student',
        'subject'
    ).order_by(
        '-id'
    )[:10]


    # =====================================
    # PREVIOUS ACTIVITIES
    # =====================================

    recent_activities = ActivityEvidence.objects.filter(
        student__in=students_qs
    ).select_related(
        'student',
        'parameter'
    ).order_by(
        '-id'
    )[:10]


    # =====================================
    # EXCEL UPLOAD HISTORY
    # =====================================

    uploads = MarksUploadBatch.objects.all()

    if (
        current_role != 'IQAC'
        and not request.user.is_superuser
    ):

        uploads = uploads.filter(
            department=request.user.profile.department
        )

    recent_uploads = uploads.select_related(
        'uploaded_by',
        'department'
    ).order_by(
        '-uploaded_at'
    )[:5]


    # =====================================
    # DASHBOARD CARDS
    # =====================================

    cards = {

        'students': total_students,

        'departments': total_departments,

        'results': total_semester_results,

        'marks': total_marks,

        'activities': total_activities,

        'pending': total_pending,

        'avg_cgpa': round(
            float(avg_cgpa),
            2
        ),

        'avg_class12': round(
            float(avg_class12),
            2
        ),

        'approved_marks': approved_marks,

        'approved_semesters': approved_semesters,

        'approved_activities': approved_activities,
    }


    return render(
        request,
        'core/dashboard.html',
        {

            'cards': cards,

            'department_stats': department_stats,

            'recent_semester_results':
                recent_semester_results,

            'recent_marks':
                recent_marks,

            'recent_activities':
                recent_activities,

            'recent_uploads':
                recent_uploads,

            'role':
                current_role
        }
    ) 
@login_required
def download_score_report(request):

    current_role = portal_role(request.user)

    if current_role not in ['IQAC', 'HOD']:
        return HttpResponseForbidden(
            'Not authorized.'
        )

    academic_year = (
        request.GET.get('academic_year')
        or current_academic_year()
    )

    students = (
        Student.objects
        .filter(active=True)
        .select_related('department')
    )

    # HOD gets only own department
    if current_role == 'HOD':

        students = students.filter(
            department=request.user.profile.department
        )


    from openpyxl import Workbook
    from openpyxl.styles import Font


    wb = Workbook()

    ws = wb.active

    ws.title = 'Student Score Report'


    headers = [

        'Register Number',

        'Student Name',

        'Department',

        'Year',

        'Academic /20',

        'Attendance /10',

        'Learning /10',

        'Technical /15',

        'Internship /10',

        'Research /10',

        'Career /10',

        'Leadership /5',

        'Social /5',

        'Sports & Cultural /5',

        'Total /100',

        'Performance'
    ]


    ws.append(headers)


    for cell in ws[1]:
        cell.font = Font(bold=True)


    for student in students:

        card = student_scorecard(
            student,
            academic_year
        )


        scores = {

            row['parameter'].code:
                row['points']

            for row in card['rows']
        }


        ws.append([

            student.register_number,

            student.name,

            student.department.code,

            getattr(student, 'year_of_study', ''),

            scores.get('ACADEMIC', 0),

            scores.get('ATTENDANCE', 0),

            scores.get('LEARNING', 0),

            scores.get('TECHNICAL', 0),

            scores.get('INTERNSHIP', 0),

            scores.get('RESEARCH', 0),

            scores.get('CAREER', 0),

            scores.get('LEADERSHIP', 0),

            scores.get('SOCIAL', 0),

            scores.get('SPORTS', 0),

            card['total'],

            card['category'],

        ])


    response = HttpResponse(

        content_type=(
            'application/vnd.openxmlformats-'
            'officedocument.spreadsheetml.sheet'
        )
    )


    response[
        'Content-Disposition'
    ] = (
        f'attachment; '
        f'filename="ACE_EduCampus_'
        f'{academic_year}_Report.xlsx"'
    )


    wb.save(response)

    return response  
@login_required
def student_score_overview(request):

    current_role = portal_role(
        request.user
    )


    # Only IQAC and HOD
    if current_role not in [
        'IQAC',
        'HOD'
    ]:

        return HttpResponseForbidden(
            'You are not authorized '
            'to view student scores.'
        )


    academic_year = (
        request.GET.get(
            'academic_year'
        )
        or current_academic_year()
    )


    students_qs = (
        Student.objects
        .filter(
            active=True
        )
        .select_related(
            'department'
        )
        .order_by(
            'department__code',
            'register_number'
        )
    )


    # HOD can see only own department
    if current_role == 'HOD':

        department = getattr(
            request.user.profile,
            'department',
            None
        )


        if not department:

            return HttpResponseForbidden(
                'HOD is not assigned '
                'to a department.'
            )


        students_qs = (
            students_qs.filter(
                department=department
            )
        )


    rows = []


    for student in students_qs:

        card = student_scorecard(
            student,
            academic_year
        )


        rows.append(
            {
                'student':
                    student,

                'scorecard':
                    card,

                'total':
                    card['total'],

                'category':
                    card['category'],
            }
        )


    return render(
        request,
        'core/student_score_overview.html',
        {
            'rows':
                rows,

            'academic_year':
                academic_year,

            'current_role':
                current_role,
        }
    )
@login_required
def download_dashboard_report(request):

    current_role = role(request.user)

    if request.user.is_superuser:
        current_role = 'IQAC'

    # Only IQAC and HOD
    if current_role not in ['IQAC', 'HOD']:
        return HttpResponseForbidden(
            'You are not authorized to download this report.'
        )


    # ==========================================
    # STUDENT SCOPE
    # ==========================================

    students = Student.objects.filter(
        active=True
    ).select_related(
        'department'
    )

    if current_role == 'HOD':

        students = students.filter(
            department=request.user.profile.department
        )


    # ==========================================
    # CREATE EXCEL FILE
    # ==========================================

    wb = Workbook()

    ws = wb.active

    ws.title = 'Dashboard Summary'


    # ==========================================
    # REPORT TITLE
    # ==========================================

    ws['A1'] = 'ADHIYAMAAN COLLEGE OF ENGINEERING, HOSUR'

    ws['A2'] = 'ACE EduCampus - Student Performance Report'


    if current_role == 'HOD':

        department = request.user.profile.department

        ws['A3'] = (
            f'Department: '
            f'{department.code} - {department.name}'
        )

    else:

        ws['A3'] = 'Institution Level Report'


    ws['A4'] = (
        'Generated on: '
        + datetime.now().strftime(
            '%d-%m-%Y %I:%M %p'
        )
    )


    for cell in ['A1', 'A2']:

        ws[cell].font = Font(
            bold=True,
            size=14
        )


    # ==========================================
    # DASHBOARD SUMMARY
    # ==========================================

    ws['A6'] = 'SUMMARY'

    ws['A6'].font = Font(
        bold=True,
        size=12
    )


    total_students = students.count()


    semester_results = SemesterResult.objects.filter(
        student__in=students
    )


    activities = ActivityEvidence.objects.filter(
        student__in=students
    )


    marks = SubjectMark.objects.filter(
        student__in=students
    )


    avg_cgpa = semester_results.aggregate(
        value=Avg('cgpa')
    )['value'] or 0


    avg_12 = students.aggregate(
        value=Avg('class12_percentage')
    )['value'] or 0


    summary = [

        ['Total Students', total_students],

        [
            'Total Semester Results',
            semester_results.count()
        ],

        [
            'Total Subject Mark Records',
            marks.count()
        ],

        [
            'Total Activities / Evidence',
            activities.count()
        ],

        [
            'Average 12th Percentage',
            round(float(avg_12), 2)
        ],

        [
            'Average CGPA',
            round(float(avg_cgpa), 2)
        ],
    ]


    row = 7

    for label, value in summary:

        ws.cell(
            row=row,
            column=1,
            value=label
        )

        ws.cell(
            row=row,
            column=2,
            value=value
        )

        row += 1


    # ==========================================
    # STUDENT DETAILS SHEET
    # ==========================================

    student_sheet = wb.create_sheet(
        'Students'
    )


    headers = [

        'Register Number',
        'Student Name',
        'Department',
        'Batch',
        'Current Semester',
        '12th Percentage',
        'Email',
        'Phone',
    ]


    student_sheet.append(
        headers
    )


    for cell in student_sheet[1]:

        cell.font = Font(
            bold=True
        )

        cell.alignment = Alignment(
            horizontal='center'
        )


    for student in students:

        student_sheet.append([

            student.register_number,

            student.name,

            student.department.code
            if student.department
            else '',

            student.batch,

            student.current_semester,

            student.class12_percentage,

            student.email,

            student.phone,
        ])


    # ==========================================
    # SEMESTER RESULTS SHEET
    # ==========================================

    semester_sheet = wb.create_sheet(
        'Semester Results'
    )


    semester_sheet.append([

        'Register Number',
        'Student',
        'Department',
        'Semester',
        'SGPA',
        'CGPA',
        'Arrears',
        'Status',
    ])


    for cell in semester_sheet[1]:

        cell.font = Font(
            bold=True
        )


    semester_results = semester_results.select_related(
        'student',
        'student__department'
    ).order_by(
        'student__register_number',
        'semester'
    )


    for result in semester_results:

        semester_sheet.append([

            result.student.register_number,

            result.student.name,

            result.student.department.code
            if result.student.department
            else '',

            result.semester,

            result.sgpa,

            result.cgpa,

            result.arrears,

            result.status,
        ])


    # ==========================================
    # ACTIVITIES / PROGRESS SHEET
    # ==========================================

    activity_sheet = wb.create_sheet(
        'Activities'
    )


    activity_sheet.append([

        'Register Number',
        'Student',
        'Department',
        'Framework Parameter',
        'Activity',
        'Level',
        'Points',
        'Status',
    ])


    for cell in activity_sheet[1]:

        cell.font = Font(
            bold=True
        )


    activities = activities.select_related(
        'student',
        'student__department',
        'parameter'
    )


    for activity in activities:

        activity_sheet.append([

            activity.student.register_number,

            activity.student.name,

            activity.student.department.code
            if activity.student.department
            else '',

            activity.parameter.name
            if activity.parameter
            else '',

            activity.title,

            activity.level,

            activity.points,

            activity.status,
        ])


    # ==========================================
    # AUTO WIDTH
    # ==========================================

    for sheet in wb.worksheets:

        for column in sheet.columns:

            max_length = 0

            column_letter = (
                column[0].column_letter
            )

            for cell in column:

                try:

                    length = len(
                        str(
                            cell.value
                            if cell.value is not None
                            else ''
                        )
                    )

                    if length > max_length:
                        max_length = length

                except:
                    pass

            sheet.column_dimensions[
                column_letter
            ].width = min(
                max_length + 3,
                40
            )


    # ==========================================
    # FILE NAME
    # ==========================================

    today = datetime.now().strftime(
        '%Y-%m-%d'
    )


    if current_role == 'HOD':

        code = (
            request.user.profile.department.code
        )

        filename = (
            f'ACE_EduCampus_'
            f'{code}_Report_{today}.xlsx'
        )

    else:

        filename = (
            f'ACE_EduCampus_'
            f'IQAC_Report_{today}.xlsx'
        )


    # ==========================================
    # DOWNLOAD
    # ==========================================

    response = HttpResponse(
        content_type=(
            'application/'
            'vnd.openxmlformats-officedocument.'
            'spreadsheetml.sheet'
        )
    )


    response[
        'Content-Disposition'
    ] = (
        f'attachment; '
        f'filename="{filename}"'
    )


    wb.save(
        response
    )


    return response

@login_required
def students(request):

    current_role = role(request.user)

    # Students should not open the full student list
    if current_role == 'STUDENT':

        if request.user.profile.student:
            return redirect(
                'student_detail',
                pk=request.user.profile.student.id
            )

        return HttpResponseForbidden(
            'Student account is not linked.'
        )


    # ---------------------------------
    # STUDENTS AVAILABLE TO USER
    # ---------------------------------

    base_students = dept_scope(
        request.user,
        Student.objects.filter(
            active=True
        ).select_related(
            'department'
        )
    )


    # ---------------------------------
    # FILTER VALUES
    # ---------------------------------

    search = request.GET.get(
        'q',
        ''
    ).strip()

    department_id = request.GET.get(
        'department',
        ''
    ).strip()

    batch = request.GET.get(
        'batch',
        ''
    ).strip()

    semester = request.GET.get(
        'semester',
        ''
    ).strip()


    students_qs = base_students


    # ---------------------------------
    # SEARCH
    # ---------------------------------

    if search:

        students_qs = students_qs.filter(

            Q(
                register_number__icontains=search
            )

            |

            Q(
                name__icontains=search
            )

            |

            Q(
                email__icontains=search
            )

            |

            Q(
                phone__icontains=search
            )

            |

            Q(
                department__code__icontains=search
            )
        )


    # ---------------------------------
    # DEPARTMENT FILTER
    # ---------------------------------

    if department_id:

        students_qs = students_qs.filter(
            department_id=department_id
        )


    # ---------------------------------
    # BATCH FILTER
    # ---------------------------------

    if batch:

        students_qs = students_qs.filter(
            batch=batch
        )


    # ---------------------------------
    # SEMESTER FILTER
    # ---------------------------------

    if semester:

        students_qs = students_qs.filter(
            current_semester=semester
        )


    students_qs = students_qs.order_by(
        'department__code',
        'register_number'
    )


    # ---------------------------------
    # FILTER OPTIONS
    # ---------------------------------

    departments = Department.objects.filter(
        active=True
    )

    if (
        current_role != 'IQAC'
        and not request.user.is_superuser
    ):

        departments = departments.filter(
            id=request.user.profile.department_id
        )


    batches = (
        base_students
        .values_list(
            'batch',
            flat=True
        )
        .distinct()
        .order_by(
            '-batch'
        )
    )


    # ---------------------------------
    # SUMMARY
    # ---------------------------------

    total_students = base_students.count()

    filtered_students = students_qs.count()

    department_count = (
        base_students
        .values(
            'department'
        )
        .distinct()
        .count()
    )


    return render(
        request,
        'core/students.html',
        {

            'students':
                students_qs,

            'departments':
                departments,

            'batches':
                batches,

            'q':
                search,

            'selected_department':
                department_id,

            'selected_batch':
                batch,

            'selected_semester':
                semester,

            'total_students':
                total_students,

            'filtered_students':
                filtered_students,

            'department_count':
                department_count,

            'role':
                current_role,
        }
    )
     
@login_required
def student_detail(request, pk):

    s = get_object_or_404(
        dept_scope(
            request.user,
            Student.objects.select_related(
                'department'
            )
        ),
        pk=pk

    )
    current_role = portal_role(
    request.user
    )
    if current_role == 'STUDENT':
        profile_student = getattr(
            request.user.profile,
            'student',
            None
            )

    if (
        not profile_student
        or profile_student.id != s.id
    ):
        return HttpResponseForbidden(
            'You cannot view another student profile.'
            )
    elif current_role == 'HOD':
        if (
                s.department_id
                != request.user.profile.department_id
                ):
                return HttpResponseForbidden(
            'You cannot view students '
            'from another department.'
        )
        elif current_role == 'IQAC':
                pass
        else:
                return HttpResponseForbidden(
                    'Not authorized.'
                    )

    marks = s.subject_marks.select_related(
        'subject'
    )

    semesters = s.semester_results.all()

    activities = s.activities.select_related(
        'parameter'
    )

    # Students see only fully approved information
    if role(request.user) == 'STUDENT':

        marks = marks.filter(
            status='IQAC_APPROVED'
        )

        semesters = semesters.filter(
            status='IQAC_APPROVED'
        )

        activities = activities.filter( Q(status='HOD_APPROVED')|Q(status='IQAC_APPROVED')
        )

    marks = marks.order_by(
        'subject__semester',
        'subject__code'
    )

    semesters = semesters.order_by(
        'semester'
    )

    activities = activities.order_by(
        '-activity_date'
    )

    scores, total, level = student_spi(s)

    trend = [
        {
            'semester': r.semester,
            'sgpa': float(r.sgpa or 0),
            'cgpa': float(r.cgpa or 0)
        }
        for r in semesters
    ]
    academic_year = (
    request.GET.get(
        'academic_year'
    )
    or current_academic_year()
    )
    scorecard = student_scorecard(
        s,
        academic_year
        )
    return render(
        request,
        'core/student_detail.html',
        {
            's': s,
            'marks': marks,
            'semesters': semesters,
            'activities': activities,
            'scores': scores,
            'spi': total,
            'level': level,
            'trend': trend,
            'student': s,
            'scorecard': scorecard,
            'academic_year': academic_year,

        }
    )
@login_required
def student_add(request):

    current_role = role(request.user)

    if current_role not in [
        'IQAC',
        'HOD',
    ] and not request.user.is_superuser:

        return HttpResponseForbidden(
            'Not authorized.'
        )


    form = StudentForm(
        request.POST or None
    )


    if form.is_valid():

        student = form.save(
            commit=False
        )


        # HOD and Faculty can create students
        # only inside their department
        if current_role in [
            'HOD',
            'FACULTY'
        ]:

            student.department = (
                request.user.profile.department
            )


        student.save()


        messages.success(
            request,
            'Student added successfully.'
        )

        return redirect(
            'students'
        )


    return render(
        request,
        'core/form.html',
        {
            'form': form,
            'title': 'Add Student'
        }
    )
@login_required
def student_progress_upload(
    request
):

    if portal_role(
        request.user
    ) != 'STUDENT':

        return HttpResponseForbidden(
            'Only students can submit progress.'
        )


    profile = (
        request.user.profile
    )


    student = getattr(
        profile,
        'student',
        None
    )


    if not student:

        return HttpResponseForbidden(
            'This login is not linked '
            'to a student record.'
        )


    form = ProgressSubmissionForm(
        request.POST or None,
        request.FILES or None
    )


    if (
        request.method == 'POST'
        and form.is_valid()
    ):

        submission = (
            form.save(
                commit=False
            )
        )


        submission.student = (
            student
        )

        submission.status = (
            'PENDING'
        )

        submission.awarded_points = 0

        submission.save()


        messages.success(
            request,
            'Progress submitted successfully. '
            'It is waiting for HOD verification.'
        )


        return redirect(
            'student_scorecard'
        )


    parameter_codes = {

        str(parameter.id):
            parameter.code

        for parameter
        in ScoreParameter.objects.filter(
            active=True
        )
    }
    rules_json = json.dumps(PROGRESS_RULES)
    parameters = (
        ScoreParameter.objects
          .filter(active=True)
          .order_by('order')
          )

    return render(
        request,
        'core/progress_upload.html',
        {

            'form': form,

            'student': student,
            'parameters': parameters,
            'rules_json': rules_json,

            'parameter_codes_json':
                json.dumps(
                    parameter_codes
                ),
        }
    )
@login_required
def student_edit(request, pk):
    # Only IQAC and HOD can edit student details
    if role(request.user) not in ['IQAC', 'HOD'] and not request.user.is_superuser:
        return HttpResponseForbidden('Not authorized')

    student = get_object_or_404(Student, pk=pk)

    # HOD can edit only students from their own department
    if role(request.user) == 'HOD':
        if student.department_id != request.user.profile.department_id:
            return HttpResponseForbidden(
                'You cannot edit students from another department'
            )

    form = StudentForm(
        request.POST or None,
        instance=student
    )
    if form.is_valid():
        progress = form.save(
        commit=False
        )
        progress.student = student
        progress.status = 'PENDING'
        progress.subtopic = (
            request.POST.get(
                'subtopic',
                ''
        )
        )
        progress.details = {
            'detail_1':
            request.POST.get(
                 'detail_1',
                ''
            ),

           'detail_2':
            request.POST.get(
                'detail_2',
                ''
            ),

           'detail_3':
            request.POST.get(
                'detail_3',
                ''
            ),
            }
        progress.save()
        messages.success(
            request,
            'Progress submitted for verification.'
            )
        return redirect(
            'student_scorecard'
            )
        return render(
            request,
            'core/form.html',
            {
                'form': form,
                'title': f'Edit Student - {student.name}'
                }
                )

@login_required
def departments(request):
    return render(request,'core/departments.html',{'departments':Department.objects.all()})

@login_required
def department_add(request):
    if role(request.user)!='IQAC' and not request.user.is_superuser:return HttpResponseForbidden('IQAC only')
    form=DepartmentForm(request.POST or None)
    if form.is_valid():form.save();messages.success(request,'Department created.');return redirect('departments')
    return render(request,'core/form.html',{'form':form,'title':'Create Department'})

@login_required
def staff_add(request):

    # ==========================================
    # 1. IDENTIFY WHO IS CREATING THE LOGIN
    # ==========================================

    creator_role = role(request.user)

    # Superuser is treated as IQAC
    if request.user.is_superuser:
        creator_role = 'IQAC'


    # ==========================================
    # 2. DEFINE ROLE CREATION PERMISSIONS
    # ==========================================

    allowed_roles = {

        'IQAC': [
            'IQAC',
            'HOD',
            'STUDENT',
        ],

        'HOD': [
            'STUDENT',
        ]
    }


    # Student or invalid user cannot create accounts
    if creator_role not in allowed_roles:

        return HttpResponseForbidden(
            'You are not authorized to create login accounts.'
        )


    # ==========================================
    # 3. LOAD FORM
    # ==========================================

    form = StaffCreateForm(
        request.POST or None
    )
   

    # ==========================================
    # 4. SHOW ONLY ALLOWED ROLES IN DROPDOWN
    # ==========================================

    role_labels = {
        'IQAC': 'IQAC Coordinator',
        'HOD': 'Head of Department',
        'STUDENT': 'Student',
    }

    form.fields['role'].choices = [

        (
            role_name,
            role_labels[role_name]
        )

        for role_name in allowed_roles[creator_role]
    ]


    # ==========================================
    # 5. LIMIT DEPARTMENT / STUDENT OPTIONS
    # ==========================================

    if creator_role in [
        'HOD',
        'FACULTY'
    ]:

        creator_department = (
            request.user.profile.department
        )

        # They can see only their own department
        form.fields['department'].queryset = (
            Department.objects.filter(
                id=creator_department.id,
                active=True
            )
        )

        # They can create student login only
        # for their own department students
        form.fields['student'].queryset = (
            Student.objects.filter(
                department=creator_department,
                active=True
            ).order_by(
                'register_number'
            )
        )


    else:

        # IQAC sees all departments
        form.fields['department'].queryset = (
            Department.objects.filter(
                active=True
            ).order_by(
                'code'
            )
        )

        # IQAC sees all students
        form.fields['student'].queryset = (
            Student.objects.filter(
                active=True
            ).select_related(
                'department'
            ).order_by(
                'department__code',
                'register_number'
            )
        )


    # ==========================================
    # 6. PROCESS FORM
    # ==========================================

    if request.method == 'POST' and form.is_valid():

        new_role = form.cleaned_data[
            'role'
        ]


        # --------------------------------------
        # SECURITY CHECK
        # --------------------------------------

        if new_role not in allowed_roles[
            creator_role
        ]:

            return HttpResponseForbidden(
                'You cannot create this type of account.'
            )


        username = (
            form.cleaned_data[
                'username'
            ].strip()
        )

        password = form.cleaned_data[
            'password'
        ]

        first_name = form.cleaned_data.get(
            'first_name',
            ''
        )

        last_name = form.cleaned_data.get(
            'last_name',
            ''
        )

        email = form.cleaned_data.get(
            'email',
            ''
        )


        selected_department = (
            form.cleaned_data.get(
                'department'
            )
        )

        selected_student = (
            form.cleaned_data.get(
                'student'
            )
        )


        # ======================================
        # 7. USERNAME DUPLICATE CHECK
        # ======================================

        if User.objects.filter(
            username__iexact=username
        ).exists():

            messages.error(
                request,
                'Username already exists.'
            )

            return render(
                request,
                'core/form.html',
                {
                    'form': form,
                    'title': 'Create Login'
                }
            )


        # ======================================
        # 8. HOD / FACULTY DEPARTMENT SECURITY
        # ======================================

        if creator_role in [
            'HOD',
            'FACULTY'
        ]:

            creator_department = (
                request.user.profile.department
            )

            # Force department automatically
            selected_department = (
                creator_department
            )


        # ======================================
        # 9. STUDENT ACCOUNT
        # ======================================

        if new_role == 'STUDENT':

            if not selected_student:

                messages.error(
                    request,
                    'Please select the student record.'
                )

                return render(
                    request,
                    'core/form.html',
                    {
                        'form': form,
                        'title': 'Create Login'
                    }
                )


            # HOD / Faculty cannot create
            # another department student's login

            if creator_role in [
                'HOD',
                'FACULTY'
            ]:

                if (
                    selected_student.department_id
                    !=
                    request.user.profile.department_id
                ):

                    return HttpResponseForbidden(
                        'You cannot create a login '
                        'for another department student.'
                    )


            # Prevent duplicate login for student

            if Profile.objects.filter(
                student=selected_student
            ).exists():

                messages.error(
                    request,
                    'This student already has a login account.'
                )

                return render(
                    request,
                    'core/form.html',
                    {
                        'form': form,
                        'title': 'Create Login'
                    }
                )


            # Student department is automatically
            # taken from Student Master

            selected_department = (
                selected_student.department
            )


            # If name/email are empty,
            # take them from Student Master

            if not first_name:
                first_name = (
                    selected_student.name
                )

            if not email:
                email = (
                    selected_student.email
                    or ''
                )


        # ======================================
        # 10. HOD / FACULTY REQUIRE DEPARTMENT
        # ======================================

        if new_role in [
            'HOD',
            'FACULTY'
        ]:

            if not selected_department:

                messages.error(
                    request,
                    'Department is required '
                    'for HOD and Faculty accounts.'
                )

                return render(
                    request,
                    'core/form.html',
                    {
                        'form': form,
                        'title': 'Create Login'
                    }
                )


        # ======================================
        # 11. IQAC ACCOUNT
        # ======================================

        if new_role == 'IQAC':

            # IQAC does not need department
            selected_department = None

            selected_student = None


        # ======================================
        # 12. NON-STUDENT ACCOUNTS
        # ======================================

        if new_role != 'STUDENT':

            selected_student = None


        # ======================================
        # 13. CREATE USER + PROFILE SAFELY
        # ======================================

        try:

            with transaction.atomic():

                new_user = (
                    User.objects.create_user(

                        username=username,

                        password=password,

                        first_name=first_name,

                        last_name=last_name,

                        email=email
                    )
                )


                Profile.objects.create(

                    user=new_user,

                    role=new_role,

                    department=selected_department,

                    student=selected_student
                )


                # Optional audit history
                AuditLog.objects.create(

                    actor=request.user,

                    action='Login account created',

                    entity='User',

                    entity_id=str(
                        new_user.id
                    ),

                    details=(
                        f'Created {new_role} account: '
                        f'{username}'
                    )
                )


        except Exception as e:

            messages.error(
                request,
                f'Unable to create account: {e}'
            )

            return render(
                request,
                'core/form.html',
                {
                    'form': form,
                    'title': 'Create Login'
                }
            )


        # ======================================
        # 14. SUCCESS
        # ======================================

        messages.success(
            request,
            f'{new_role} login '
            f'"{username}" created successfully.'
        )


        return redirect(
            'dashboard'
        )


    # ==========================================
    # 15. DISPLAY FORM
    # ==========================================

    return render(
        request,
        'core/form.html',
        {
            'form': form,
            'title': 'Create Login'
        }
    )

@login_required
def subjects(request):
    qs=Subject.objects.select_related('department').order_by('department','semester','code')
    if role(request.user)!='IQAC' and not request.user.is_superuser: qs=qs.filter(department=request.user.profile.department)
    return render(request,'core/subjects.html',{'subjects':qs})

@login_required
def subject_add(request):
    if role(request.user) not in ['IQAC','HOD']:return HttpResponseForbidden('Not authorized')
    form=SubjectForm(request.POST or None)
    if form.is_valid():form.save();messages.success(request,'Subject added.');return redirect('subjects')
    return render(request,'core/form.html',{'form':form,'title':'Add Subject'})

@login_required
def marks_template(request):
    if role(request.user) not in [
    'IQAC',
    'HOD',
    'FACULTY'
]:
        return HttpResponseForbidden(
        'Not authorized.'
    )
    wb=Workbook();ws=wb.active;ws.title='Marks'
    ws.append(['Register Number','Subject Code','Internal','External'])
    ws.append(['21CSE001','CS401','35','54'])
    response=HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition']='attachment; filename="ACE_Marks_Upload_Template.xlsx"';wb.save(response);return response

def normalize_register(value):
    """
    Makes register numbers from Excel easier to match.
    Examples:
    21CSE001 -> 21CSE001
    ' 21cse001 ' -> 21CSE001
    21001.0 -> 21001
    """

    if value is None:
        return ''

    if isinstance(value, float) and value.is_integer():
        value = int(value)

    return str(value).strip().upper().replace(' ', '')


def normalize_subject_code(value):

    if value is None:
        return ''

    return str(value).strip().upper().replace(' ', '')


def normalize_header(value):

    if value is None:
        return ''

    return (
        str(value)
        .strip()
        .lower()
        .replace(' ', '')
        .replace('_', '')
        .replace('-', '')
    )


def decimal_value(value):

    if value is None or value == '':
        raise ValueError('Mark is empty')

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(
            f'Invalid mark value: {value}'
        )

@login_required
def marks_upload(request):
    if role(request.user) not in [
    'IQAC',
    'HOD',
    'FACULTY'
]:
        return HttpResponseForbidden(
        'Students cannot upload marks.'
    )

    form = ExcelUploadForm(
        request.POST or None,
        request.FILES or None
    )

    if request.method == 'POST' and form.is_valid():

        uploaded_file = form.cleaned_data['file']

        # ------------------------------
        # CHECK FILE TYPE
        # ------------------------------

        if not uploaded_file.name.lower().endswith('.xlsx'):

            messages.error(
                request,
                'Please upload only an Excel .xlsx file.'
            )

            return redirect('marks_upload')


        # ------------------------------
        # CREATE UPLOAD BATCH
        # ------------------------------

        upload_department = None

        if (
            role(request.user) != 'IQAC'
            and not request.user.is_superuser
        ):
            upload_department = request.user.profile.department


        batch = MarksUploadBatch.objects.create(

            file_name=uploaded_file.name,

            uploaded_by=request.user,

            department=upload_department
        )


        try:

            wb = load_workbook(
                uploaded_file,
                data_only=True,
                read_only=True
            )

            ws = wb.active

        except Exception as e:

            batch.delete()

            messages.error(
                request,
                f'Unable to read Excel file: {e}'
            )

            return redirect('marks_upload')


        # ------------------------------
        # READ HEADER ROW
        # ------------------------------

        first_row = next(
            ws.iter_rows(
                min_row=1,
                max_row=1,
                values_only=True
            ),
            None
        )

        if not first_row:

            batch.delete()

            messages.error(
                request,
                'The Excel file is empty.'
            )

            return redirect('marks_upload')


        headers = {}

        for index, heading in enumerate(first_row):

            key = normalize_header(heading)

            if key:
                headers[key] = index


        required_headers = {
            'registernumber': 'Register Number',
            'subjectcode': 'Subject Code',
            'internal': 'Internal',
            'external': 'External',
        }


        missing = []

        for key, display_name in required_headers.items():

            if key not in headers:
                missing.append(display_name)


        if missing:

            batch.delete()

            messages.error(
                request,
                'Missing required column(s): '
                + ', '.join(missing)
            )

            return redirect('marks_upload')


        # ------------------------------
        # STUDENT LOOKUP CACHE
        # ------------------------------

        student_queryset = dept_scope(
            request.user,
            Student.objects.filter(active=True)
        )


        student_map = {

            normalize_register(student.register_number): student

            for student in student_queryset
        }


        # ------------------------------
        # SUBJECT LOOKUP CACHE
        # ------------------------------

        subject_queryset = Subject.objects.select_related(
            'department'
        )


        if (
            role(request.user) != 'IQAC'
            and not request.user.is_superuser
        ):

            subject_queryset = subject_queryset.filter(
                department=request.user.profile.department
            )


        subject_map = {

            (
                subject.department_id,
                normalize_subject_code(subject.code)
            ): subject

            for subject in subject_queryset
        }


        success_count = 0
        failed_count = 0
        total_count = 0


        # ------------------------------
        # PROCESS EXCEL ROWS
        # ------------------------------

        for row_number, row in enumerate(
            ws.iter_rows(
                min_row=2,
                values_only=True
            ),
            start=2
        ):

            # Ignore completely blank rows

            if not row or not any(
                value not in (None, '')
                for value in row
            ):
                continue


            total_count += 1


            register_number = normalize_register(
                row[
                    headers['registernumber']
                ]
            )


            subject_code = normalize_subject_code(
                row[
                    headers['subjectcode']
                ]
            )


            upload_row = MarksUploadRow.objects.create(

                batch=batch,

                excel_row=row_number,

                register_number=register_number,

                subject_code=subject_code
            )


            try:

                # --------------------------
                # VALIDATE REGISTER NUMBER
                # --------------------------

                if not register_number:

                    raise ValueError(
                        'Register Number is empty.'
                    )


                student = student_map.get(
                    register_number
                )


                if not student:

                    raise ValueError(
                        f'Student {register_number} '
                        f'not found in Student Master.'
                    )


                upload_row.student = student


                # --------------------------
                # VALIDATE SUBJECT
                # --------------------------

                if not subject_code:

                    raise ValueError(
                        'Subject Code is empty.'
                    )


                subject = subject_map.get(

                    (
                        student.department_id,
                        subject_code
                    )
                )


                if not subject:

                    raise ValueError(

                        f'Subject {subject_code} '
                        f'not found for '
                        f'{student.department.code}.'
                    )


                upload_row.subject = subject


                # --------------------------
                # READ MARKS
                # --------------------------

                internal = decimal_value(

                    row[
                        headers['internal']
                    ]
                )


                external = decimal_value(

                    row[
                        headers['external']
                    ]
                )


                # --------------------------
                # VALIDATE MARK RANGE
                # --------------------------

                if internal < 0:

                    raise ValueError(
                        'Internal mark cannot be negative.'
                    )


                if external < 0:

                    raise ValueError(
                        'External mark cannot be negative.'
                    )


                if internal > subject.max_internal:

                    raise ValueError(

                        f'Internal mark {internal} '
                        f'exceeds maximum '
                        f'{subject.max_internal}.'
                    )


                if external > subject.max_external:

                    raise ValueError(

                        f'External mark {external} '
                        f'exceeds maximum '
                        f'{subject.max_external}.'
                    )


                total = internal + external


                # --------------------------
                # SAVE / UPDATE MARK
                # --------------------------

                mark, created = SubjectMark.objects.update_or_create(

                    student=student,

                    subject=subject,

                    defaults={

                        'internal': internal,

                        'external': external,

                        # Re-upload requires approval again
                        'status': 'PENDING',

                        'uploaded_by': request.user
                    }
                )


                upload_row.internal = internal
                upload_row.external = external
                upload_row.total = total

                upload_row.success = True

                upload_row.action = (
                    'CREATED'
                    if created
                    else 'UPDATED'
                )

                upload_row.message = (
                    'Imported successfully. '
                    'Pending HOD approval.'
                )

                upload_row.save()


                AuditLog.objects.create(

                    actor=request.user,

                    action='Excel mark upload',

                    entity='SubjectMark',

                    entity_id=str(mark.id),

                    details=(
                        f'{student.register_number} | '
                        f'{subject.code} | '
                        f'Internal {internal} | '
                        f'External {external}'
                    )
                )


                success_count += 1


            except Exception as e:

                upload_row.success = False

                upload_row.message = str(e)

                upload_row.save()

                failed_count += 1


        # ------------------------------
        # UPDATE BATCH COUNTS
        # ------------------------------

        batch.total_rows = total_count
        batch.success_rows = success_count
        batch.failed_rows = failed_count

        batch.save()


        # ------------------------------
        # OPEN RESULT DASHBOARD
        # ------------------------------

        return redirect(
            'marks_upload_result',
            batch_id=batch.id
        )


    return render(
        request,
        'core/upload.html',
        {
            'form': form
        }
    )
@login_required
def marks_upload_result(request, batch_id):

    batch = get_object_or_404(
        MarksUploadBatch.objects.select_related(
            'uploaded_by',
            'department'
        ),
        pk=batch_id
    )


    # Faculty/HOD cannot see uploads
    # belonging to another department

    if (
        role(request.user) != 'IQAC'
        and not request.user.is_superuser
    ):

        if (
            batch.department_id
            != request.user.profile.department_id
        ):

            return HttpResponseForbidden(
                'You cannot view this upload.'
            )


    rows = batch.rows.select_related(
        'student',
        'subject',
        'student__department'
    ).order_by('excel_row')


    successful_rows = rows.filter(
        success=True
    )


    failed_rows = rows.filter(
        success=False
    )


    return render(
        request,
        'core/marks_upload_result.html',
        {
            'batch': batch,
            'rows': rows,
            'successful_rows': successful_rows,
            'failed_rows': failed_rows
        }
    )

@login_required
def semester_add(request):
    if role(request.user) not in [
    'IQAC',
    'HOD',
    'FACULTY'
]:
        return HttpResponseForbidden(
        'Not authorized.'
    )
    form=SemesterResultForm(request.POST or None)
    if form.is_valid():
        obj=form.save(commit=False)
        if role(request.user)!='IQAC' and obj.student.department_id!=request.user.profile.department_id:return HttpResponseForbidden('Wrong department')
        obj.uploaded_by=request.user;obj.status='PENDING';obj.save();messages.success(request,'Semester result saved for approval.');return redirect('student_detail',pk=obj.student_id)
    return render(request,'core/form.html',{'form':form,'title':'Add Semester Result'})

@login_required
def activity_add(request):
    current_role = portal_role(request.user)
    if role(request.user) not in [
    'IQAC',
    'HOD',
    
]:
        return HttpResponseForbidden(
        'Not authorized.'
    )
    form=ActivityEvidenceForm(request.POST or None,request.FILES or None)
    if form.is_valid():
        obj=form.save(commit=False)
        if role(request.user)!='IQAC' and obj.student.department_id!=request.user.profile.department_id:return HttpResponseForbidden('Wrong department')
        obj.created_by=request.user;obj.status='PENDING'
        # 0-4 mapped to achievement bands by midpoint; assessor can edit points later via admin if needed.
        ratios={0:0,1:.37,2:.62,3:.82,4:.95};obj.points=round(obj.parameter.max_points*ratios.get(obj.level,0),2)
        obj.save();messages.success(request,'Activity/evidence submitted.');return redirect('student_detail',pk=obj.student_id)
    return render(request,'core/form.html',{'form':form,'title':'Add Activity / Evidence'})

@login_required
def approvals(request):
    r=role(request.user)
    if r not in ['IQAC','HOD'] and not request.user.is_superuser:return HttpResponseForbidden('Not authorized')
    students=dept_scope(request.user,Student.objects.all())
    activities=ActivityEvidence.objects.filter(student__in=students)
    semesters=SemesterResult.objects.filter(student__in=students)
    marks=SubjectMark.objects.filter(student__in=students)
    if r=='HOD': activities=activities.filter(status='PENDING');semesters=semesters.filter(status='PENDING');marks=marks.filter(status='PENDING')
    else: activities=activities.filter(status='HOD_APPROVED');semesters=semesters.filter(status='HOD_APPROVED');marks=marks.filter(status='HOD_APPROVED')
    return render(request,'core/approvals.html',{'activities':activities.select_related('student','parameter'),'semesters':semesters.select_related('student'),'marks':marks.select_related('student','subject'),'role':r})

@login_required
def progress_approvals(request):

    current_role = portal_role(
        request.user
    )


    if current_role not in [
        'HOD',
        'IQAC'
    ]:

        return HttpResponseForbidden(
            'Only HOD and IQAC can '
            'verify student progress.'
        )


    submissions = (
        ProgressSubmission.objects
        .filter(
            status='PENDING'
        )
        .select_related(
            'student',
            'student__department',
            'parameter'
        )
        .order_by(
            'student__department__code',
            'student__register_number',
            'created_at'
        )
    )


    # HOD sees only their department
    if current_role == 'HOD':

        department = getattr(
            request.user.profile,
            'department',
            None
        )


        if not department:

            return HttpResponseForbidden(
                'HOD department '
                'is not configured.'
            )


        submissions = (
            submissions.filter(
                student__department=
                    department
            )
        )


    items = []


    for submission in submissions:

        calculated_points = min(

            calculate_submission_points(
                submission
            ),

            submission.parameter.max_points
        )


        items.append(
            {
                'submission':
                    submission,

                'calculated_points':
                    calculated_points,
            }
        )


    return render(
        request,
        'core/progress_approvals.html',
        {
            'items':
                items,

            'current_role':
                current_role,
        }
    )
@login_required
def delete_progress_submission(
    request,
    pk
):

    if portal_role(
        request.user
    ) != 'STUDENT':

        return HttpResponseForbidden(
            'Student access only.'
        )


    submission = get_object_or_404(
        ProgressSubmission,
        pk=pk,
        student__user=request.user
    )


    # Only pending submission can be deleted
    if submission.status != 'PENDING':

        messages.error(
            request,
            'Verified or rejected records '
            'cannot be deleted here.'
        )

        return redirect(
            'student_scorecard'
        )


    # Only within first 24 hours
    expiry_time = (
        submission.created_at
        + timedelta(hours=24)
    )


    if timezone.now() > expiry_time:

        messages.error(
            request,
            'The 24-hour deletion period '
            'has expired.'
        )

        return redirect(
            'student_scorecard'
        )


    if request.method == 'POST':

        # Delete actual uploaded file
        if submission.evidence:

            submission.evidence.delete(
                save=False
            )


        submission.delete()


        messages.success(
            request,
            'Submission and evidence '
            'deleted successfully.'
        )


    return redirect(
        'student_scorecard'
    )
@login_required
def verify_progress(
    request,
    pk,
    decision
):

    current_role = portal_role(
        request.user
    )


    if current_role not in [
        'HOD',
        'IQAC'
    ]:

        return HttpResponseForbidden(
            'You are not authorized '
            'to verify progress.'
        )


    if request.method != 'POST':

        return HttpResponseForbidden(
            'POST request required.'
        )


    submission = get_object_or_404(

        ProgressSubmission.objects
        .select_related(
            'student',
            'student__department',
            'parameter'
        ),

        pk=pk
    )


    # ---------------------------------------
    # HOD department security
    # ---------------------------------------

    if current_role == 'HOD':

        hod_department = getattr(
            request.user.profile,
            'department',
            None
        )


        if (
            not hod_department
            or
            submission.student.department_id
            != hod_department.id
        ):

            return HttpResponseForbidden(
                'You cannot verify a '
                'student from another department.'
            )


    # ---------------------------------------
    # IQAC can verify any department
    # ---------------------------------------


    if submission.status != 'PENDING':

        messages.warning(
            request,
            'This submission has '
            'already been processed.'
        )

        return redirect(
            'progress_approvals'
        )


    verification_remarks = (
        request.POST.get(
            'verification_remarks',
            ''
        ).strip()
    )


    # =======================================
    # APPROVE
    # =======================================

    if decision == 'approve':

        calculated_points = (
            calculate_submission_points(
                submission
            )
        )


        calculated_points = min(
            calculated_points,
            submission.parameter.max_points
        )


        submission.awarded_points = (
            calculated_points
        )


        # Keep existing code so old scoring
        # queries continue working.
        submission.status = (
            'HOD_APPROVED'
        )


        messages.success(
            request,
            (
                f'Progress verified successfully. '
                f'{calculated_points}/'
                f'{submission.parameter.max_points} '
                f'points awarded.'
            )
        )


    # =======================================
    # REJECT
    # =======================================

    elif decision == 'reject':

        submission.awarded_points = 0

        submission.status = (
            'REJECTED'
        )


        messages.success(
            request,
            'Submission rejected.'
        )


    else:

        return HttpResponseForbidden(
            'Invalid verification decision.'
        )


    submission.verification_remarks = (
        verification_remarks
    )


    submission.verified_by = (
        request.user
    )


    submission.verified_at = (
        timezone.now()
    )


    submission.save()


    return redirect(
        'progress_approvals'
    )
@login_required
def student_scorecard_view(
    request
):

    if portal_role(
        request.user
    ) != 'STUDENT':

        return HttpResponseForbidden(
            'Student access only.'
        )


    student = (
        request.user
        .profile
        .student
    )


    academic_year = (
        request.GET.get(
            'academic_year'
        )
        or
        ProgressSubmission.objects
        .filter(
            student=student
        )
        .order_by(
            '-academic_year'
        )
        .values_list(
            'academic_year',
            flat=True
        )
        .first()
        or '2026-2027'
    )


    scorecard = (
        student_scorecard(
            student,
            academic_year
        )
    )


    submissions = (
        ProgressSubmission.objects
        .filter(
            student=student,
            academic_year=
                academic_year
        )
        .select_related(
            'parameter'
        )
    )


    return render(
        request,
        'core/student_scorecard.html',
        {

            'student':
                student,

            'academic_year':
                academic_year,

            'scorecard':
                scorecard,

            'submissions':
                submissions,
        }
    )
@login_required
def iqac_score_overview(
    request
):

    if portal_role(
        request.user
    ) != 'IQAC':

        return HttpResponseForbidden(
            'IQAC access only.'
        )


    academic_year = (
        request.GET.get(
            'academic_year',
            '2026-2027'
        )
    )


    students = (
        Student.objects
        .filter(
            active=True
        )
        .select_related(
            'department'
        )
    )


    rows = []


    for student in students:

        card = (
            student_scorecard(
                student,
                academic_year
            )
        )


        rows.append({

            'student':
                student,

            'total':
                card['total'],

            'category':
                card['category'],
        })


    return render(
        request,
        'core/student_score_overview.html',
        {

            'rows':
                rows,

            'academic_year':
                academic_year,
        }
    )

@login_required
@require_POST
def approve(request, model, pk, decision):

    current_role = role(request.user)

    modelmap = {
        'activity': ActivityEvidence,
        'semester': SemesterResult,
        'mark': SubjectMark
    }


    if model not in modelmap:

        return HttpResponseForbidden(
            'Invalid record.'
        )


    obj = get_object_or_404(
        modelmap[model],
        pk=pk
    )


    # ==============================
    # HOD
    # ==============================

    if current_role == 'HOD':


        # Own department only
        if (
            obj.student.department_id
            != request.user.profile.department_id
        ):

            return HttpResponseForbidden(
                'You cannot verify another department.'
            )


        if obj.status != 'PENDING':

            return HttpResponseForbidden(
                'Already processed.'
            )


        if decision == 'reject':

            obj.status = 'REJECTED'

            # Rejected evidence gets no score
            if model == 'activity':
                obj.points = 0

            obj.save()


        elif decision == 'approve':


            # Student progress evidence
            if model == 'activity':

                try:

                    level = int(
                        request.POST.get(
                            'level'
                        )
                    )

                except:

                    messages.error(
                        request,
                        'Please select a performance level.'
                    )

                    return redirect(
                        'approvals'
                    )


                if level not in [
                    0,
                    1,
                    2,
                    3,
                    4
                ]:

                    messages.error(
                        request,
                        'Invalid performance level.'
                    )

                    return redirect(
                        'approvals'
                    )


                # Rubric midpoint calculation
                ratios = {
                    0: 0,
                    1: 0.37,
                    2: 0.62,
                    3: 0.82,
                    4: 0.95
                }


                obj.level = level

                obj.points = round(

                    obj.parameter.max_points
                    * ratios[level],

                    2
                )


            obj.status = 'HOD_APPROVED'

            obj.save()


        else:

            return HttpResponseForbidden(
                'Invalid decision.'
            )


    # ==============================
    # IQAC
    # ==============================

    elif (
        current_role == 'IQAC'
        or request.user.is_superuser
    ):

        if obj.status != 'HOD_APPROVED':

            return HttpResponseForbidden(
                'HOD verification required first.'
            )


        if decision == 'approve':

            obj.status = 'IQAC_APPROVED'

        elif decision == 'reject':

            obj.status = 'REJECTED'

        else:

            return HttpResponseForbidden(
                'Invalid decision.'
            )


        obj.save()


    else:

        return HttpResponseForbidden(
            'Not authorized.'
        )


    AuditLog.objects.create(

        actor=request.user,

        action=decision,

        entity=model,

        entity_id=str(pk),

        details=obj.status
    )


    return redirect(
        'approvals'
    )
def portal_role(user):

    if user.is_superuser:
        return 'IQAC'

    profile = getattr(
        user,
        'profile',
        None
    )

    return getattr(
        profile,
        'role',
        ''
    )

@login_required
def reports(request):
    if role(request.user) not in [
    'IQAC',
    'HOD'
] and not request.user.is_superuser:
        return HttpResponseForbidden(
        'Only IQAC and HOD can view reports.'
    )
    depts=Department.objects.filter(active=True); rows=[]
    if role(request.user)!='IQAC' and not request.user.is_superuser:depts=depts.filter(id=request.user.profile.department_id)
    for d in depts:
        sts=Student.objects.filter(department=d,active=True); rows.append({'department':d,'students':sts.count(),'avg12':sts.aggregate(x=Avg('class12_percentage'))['x'] or 0,'avgcgpa':SemesterResult.objects.filter(student__in=sts,status='IQAC_APPROVED').aggregate(x=Avg('cgpa'))['x'] or 0})
    return render(request,'core/reports.html',{'rows':rows})
