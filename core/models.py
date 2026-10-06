import uuid
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

ROLE_CHOICES=[('IQAC','IQAC Coordinator'),('HOD','Head of Department'),('STUDENT','Student')]
STATUS=[('PENDING','Pending'),('HOD_APPROVED','HOD Approved'),('IQAC_APPROVED','IQAC Approved'),('REJECTED','Rejected')]

class Department(models.Model):
    code=models.CharField(max_length=20, unique=True)
    name=models.CharField(max_length=120, unique=True)
    active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.code} - {self.name}'

class Profile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Used only when the account belongs to a student
    student = models.OneToOneField(
        'Student',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='login_profile'
    )

    def __str__(self):
        return f'{self.user.username} ({self.role})'

class Student(models.Model):
    register_number=models.CharField(max_length=30,unique=True)
    name=models.CharField(max_length=120)
    department=models.ForeignKey(Department,on_delete=models.PROTECT)
    batch=models.CharField(max_length=20,help_text='Example: 2025-2029')
    current_semester=models.PositiveSmallIntegerField(default=1,validators=[MinValueValidator(1),MaxValueValidator(8)])
    email=models.EmailField(blank=True); phone=models.CharField(max_length=15,blank=True)
    class12_board=models.CharField(max_length=50,blank=True)
    class12_total=models.DecimalField(max_digits=6,decimal_places=2,null=True,blank=True)
    class12_max=models.DecimalField(max_digits=6,decimal_places=2,default=600)
    class12_percentage=models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True)
    active=models.BooleanField(default=True)
    def save(self,*args,**kwargs):
        if self.class12_total is not None and self.class12_max:
            self.class12_percentage=round(float(self.class12_total)/float(self.class12_max)*100,2)
        super().save(*args,**kwargs)
    def __str__(self): return f'{self.register_number} - {self.name}'

class Subject(models.Model):
    department=models.ForeignKey(Department,on_delete=models.CASCADE)
    semester=models.PositiveSmallIntegerField(validators=[MinValueValidator(1),MaxValueValidator(8)])
    code=models.CharField(max_length=20); name=models.CharField(max_length=120)
    credits=models.DecimalField(max_digits=3,decimal_places=1,default=3)
    max_internal=models.DecimalField(max_digits=6,decimal_places=2,default=40)
    max_external=models.DecimalField(max_digits=6,decimal_places=2,default=60)
    class Meta: unique_together=('department','semester','code')
    def __str__(self): return f'{self.code} - {self.name}'

class SubjectMark(models.Model):
    student=models.ForeignKey(Student,on_delete=models.CASCADE,related_name='subject_marks')
    subject=models.ForeignKey(Subject,on_delete=models.PROTECT)
    internal=models.DecimalField(max_digits=6,decimal_places=2,default=0)
    external=models.DecimalField(max_digits=6,decimal_places=2,default=0)
    total=models.DecimalField(max_digits=6,decimal_places=2,default=0)
    status=models.CharField(max_length=15,choices=STATUS,default='PENDING')
    uploaded_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,related_name='uploaded_marks')
    updated_at=models.DateTimeField(auto_now=True)
    class Meta: unique_together=('student','subject')
    def save(self,*args,**kwargs):
        self.total=float(self.internal)+float(self.external)
        super().save(*args,**kwargs)

class SemesterResult(models.Model):
    student=models.ForeignKey(Student,on_delete=models.CASCADE,related_name='semester_results')
    semester=models.PositiveSmallIntegerField(validators=[MinValueValidator(1),MaxValueValidator(8)])
    sgpa=models.DecimalField(max_digits=4,decimal_places=2,null=True,blank=True)
    cgpa=models.DecimalField(max_digits=4,decimal_places=2,null=True,blank=True)
    credits_registered=models.DecimalField(max_digits=5,decimal_places=1,default=0)
    credits_earned=models.DecimalField(max_digits=5,decimal_places=1,default=0)
    arrears=models.PositiveSmallIntegerField(default=0)
    result=models.CharField(max_length=20,default='PASS')
    status=models.CharField(max_length=15,choices=STATUS,default='PENDING')
    uploaded_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    class Meta: unique_together=('student','semester')

class FrameworkParameter(models.Model):
    category_code=models.CharField(max_length=2)
    category_name=models.CharField(max_length=120)
    category_max=models.PositiveIntegerField()
    name=models.CharField(max_length=150)
    max_points=models.PositiveIntegerField()
    def __str__(self): return f'{self.category_code}. {self.name}'

class ActivityEvidence(models.Model):
    student=models.ForeignKey(Student,on_delete=models.CASCADE,related_name='activities')
    parameter=models.ForeignKey(FrameworkParameter,on_delete=models.PROTECT)
    title=models.CharField(max_length=180)
    activity_date=models.DateField()
    level=models.PositiveSmallIntegerField(default=0,validators=[MinValueValidator(0),MaxValueValidator(4)])
    points=models.DecimalField(max_digits=6,decimal_places=2,default=0)
    evidence=models.FileField(upload_to='evidence/',blank=True,null=True)
    remarks=models.TextField(blank=True)
    status=models.CharField(max_length=15,choices=STATUS,default='PENDING')
    created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    # ==========================================
    # +2 ACADEMIC PERFORMANCE DETAILS
    # ==========================================

    board = models.CharField(
        max_length=150,
        blank=True
    )

    school = models.CharField(
        max_length=250,
        blank=True
    )

    academic_year = models.CharField(
        max_length=20,
        blank=True
    )

    academic_group = models.CharField(
        max_length=100,
        blank=True
    )

    marks_obtained = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    maximum_marks = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    @property
    def is_plus2_academic(self):

        if not self.parameter:
            return False

        return (
            '+2 academic performance'
            in str(self.parameter).lower()
        )
    def save(self, *args, **kwargs):

        if (
            self.marks_obtained is not None
            and self.maximum_marks
            and self.maximum_marks > 0
        ):

            self.percentage = round(
                (
                    self.marks_obtained
                    / self.maximum_marks
                ) * 100,
                2
            )

        super().save(
            *args,
            **kwargs
        )

class AuditLog(models.Model):
    actor=models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    action=models.CharField(max_length=120)
    entity=models.CharField(max_length=80)
    entity_id=models.CharField(max_length=50,blank=True)
    details=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

class MarksUploadBatch(models.Model):
    file_name = models.CharField(max_length=255)

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='marks_upload_batches'
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    total_rows = models.PositiveIntegerField(default=0)
    success_rows = models.PositiveIntegerField(default=0)
    failed_rows = models.PositiveIntegerField(default=0)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Upload {self.id} - {self.file_name}"


class MarksUploadRow(models.Model):

    batch = models.ForeignKey(
        MarksUploadBatch,
        on_delete=models.CASCADE,
        related_name='rows'
    )

    excel_row = models.PositiveIntegerField()

    register_number = models.CharField(
        max_length=50,
        blank=True
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    subject_code = models.CharField(
        max_length=30,
        blank=True
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    internal = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True
    )

    external = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True
    )

    total = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True
    )

    success = models.BooleanField(default=False)

    action = models.CharField(
        max_length=20,
        blank=True
    )

    message = models.CharField(
        max_length=255,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Row {self.excel_row} - {self.register_number}"

class ScoreParameter(models.Model):

    code = models.CharField(
        max_length=30,
        unique=True
    )

    name = models.CharField(
        max_length=200
    )

    max_points = models.PositiveSmallIntegerField()

    description = models.TextField(
        blank=True
    )

    order = models.PositiveSmallIntegerField(
        default=1
    )

    active = models.BooleanField(
        default=True
    )

    def __str__(self):

        return (
            f"{self.name} — "
            f"{self.max_points} Points"
        )

    class Meta:

        ordering = [
            'order'
        ]


def progress_evidence_path(
    instance,
    filename
):

    safe_year = (
        instance.academic_year
        .replace('/', '-')
        .replace(' ', '-')
    )

    unique_name = (
        f"{uuid.uuid4().hex}_{filename}"
    )

    return (
        f"student_progress/"
        f"{instance.student.register_number}/"
        f"{safe_year}/"
        f"{unique_name}"
    )


class ProgressSubmission(models.Model):

    STATUS_CHOICES = [

        (
            'PENDING',
            'Pending Verification'
        ),

        (
            'HOD_APPROVED',
            'Verified'
        ),

        (
            'REJECTED',
            'Rejected'
        ),
    ]


    student = models.ForeignKey(
        'Student',
        on_delete=models.CASCADE,
        related_name='progress_submissions'
    )


    parameter = models.ForeignKey(
        ScoreParameter,
        on_delete=models.PROTECT,
        related_name='submissions'
    )


    academic_year = models.CharField(
        max_length=20
    )


    # Parameter-specific information
    # is stored here.
    details = models.JSONField(
        default=dict,
        blank=True
    )
    subtopic = models.CharField(
    max_length=150,
    blank=True
    )
    details = models.JSONField(
        default=dict,
        blank=True
        )
    evidence = models.FileField(
        upload_to=progress_evidence_path
        )


    remarks = models.TextField(
        blank=True
    )


    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )


    awarded_points = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(0)
        ]
    )


    verification_remarks = models.TextField(
        blank=True
    )


    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_progress'
    )


    verified_at = models.DateTimeField(
        null=True,
        blank=True
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )


    updated_at = models.DateTimeField(
        auto_now=True
    )


    def __str__(self):

        return (
            f"{self.student.register_number} - "
            f"{self.parameter.name} - "
            f"{self.academic_year}"
        )


    class Meta:

        ordering = [
            '-created_at'
        ]

        indexes = [

            models.Index(
                fields=[
                    'student',
                    'academic_year'
                ]
            ),

            models.Index(
                fields=[
                    'parameter',
                    'status'
                ]
            ),
        ]