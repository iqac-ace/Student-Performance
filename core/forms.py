from django import forms
from django.contrib.auth.models import User
from .models import (Department, Student, Subject, SemesterResult, ActivityEvidence, Profile,ROLE_CHOICES)

class DepartmentForm(forms.ModelForm):
    class Meta: model=Department; fields=['code','name','active']
class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'register_number',
            'name',
            'department',
            'batch',
            'current_semester',
            'email',
            'phone',
            'class12_board',
            'class12_total',
            'class12_max',
            'active',
        ]

        widgets = {
            'register_number': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Register Number'
                }
            ),

            'name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Student Name'
                }
            ),

            'department': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'batch': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Example: 2025-2029'
                }
            ),

            'current_semester': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 1,
                    'max': 8
                }
            ),

            'email': forms.EmailInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Student Email'
                }
            ),

            'phone': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Phone Number'
                }
            ),

            'class12_board': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '12th Board'
                }
            ),

            'class12_total': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01'
                }
            ),

            'class12_max': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01'
                }
            ),
        }
class SubjectForm(forms.ModelForm):
    class Meta: model=Subject; fields='__all__'
class SemesterResultForm(forms.ModelForm):
    class Meta: model=SemesterResult; exclude=['uploaded_by','status']
class ActivityEvidenceForm(forms.ModelForm):
    class Meta: model=ActivityEvidence; exclude=['created_by','status']
class ActivityForm(forms.ModelForm):

    class Meta:
        model = ActivityEvidence

        fields = [
            'student',
            'parameter',
            'title',
            'activity_date',
            'evidence',
            'remarks',
        ]

        widgets = {

            'student': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'parameter': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'title': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'activity_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),

            'evidence': forms.ClearableFileInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'remarks': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3
                }
            ),
        }
class ExcelUploadForm(forms.Form):
    file=forms.FileField(help_text='Upload .xlsx file using the provided template')
class StaffCreateForm(forms.Form):

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control'}
        )
    )

    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        )
    )

    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        )
    )

    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(
            attrs={'class': 'form-control'}
        )
    )

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(
            attrs={'class': 'form-select'}
        )
    )

    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(active=True),
        required=False,
        widget=forms.Select(
            attrs={'class': 'form-select'}
        ),
        help_text='Required for HOD and Faculty accounts.'
    )

    student = forms.ModelChoiceField(
        queryset=Student.objects.filter(
            active=True
        ).select_related('department'),
        required=False,
        widget=forms.Select(
            attrs={'class': 'form-select'}
        ),
        help_text='Select only when creating a Student login.'
    )
class StudentProgressForm(forms.ModelForm):

    # We control these requirements dynamically
    title = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control'
            }
        )
    )

    activity_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control'
            }
        )
    )


    class Meta:

        model = ActivityEvidence

        fields = [
            'student',
            'parameter',
            'title',
            'activity_date',
            'board',
            'school',
            'academic_year',
            'academic_group',
            'marks_obtained',
            'maximum_marks',
            'remarks',
        ]


        widgets = {

            'student': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'parameter': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'board': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Example: State Board / CBSE'
                }
            ),

            'school': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'School name'
                }
            ),

            'academic_year': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Example: 2023-2024'
                }
            ),

            'academic_group': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Example: Maths Biology'
                }
            ),

            'marks_obtained': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01',
                    'min': '0'
                }
            ),

            'maximum_marks': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01',
                    'min': '1'
                }
            ),

            'remarks': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3
                }
            ),
        }


    def __init__(
        self,
        *args,
        user=None,
        **kwargs
    ):

        super().__init__(
            *args,
            **kwargs
        )

        if not user:
            return


        if user.is_superuser:

            current_role = 'IQAC'

        else:

            current_role = getattr(
                user.profile,
                'role',
                ''
            )


        # ======================================
        # STUDENT
        # ======================================

        if current_role == 'STUDENT':

            self.fields[
                'student'
            ].required = False

            self.fields[
                'student'
            ].widget = forms.HiddenInput()


        # ======================================
        # HOD / FACULTY
        # ======================================

        elif current_role in [
            'HOD',
            'FACULTY'
        ]:

            self.fields[
                'student'
            ].queryset = (
                Student.objects.filter(
                    department=user.profile.department,
                    active=True
                ).order_by(
                    'register_number'
                )
            )


        # ======================================
        # IQAC
        # ======================================

        else:

            self.fields[
                'student'
            ].queryset = (
                Student.objects.filter(
                    active=True
                ).select_related(
                    'department'
                ).order_by(
                    'department__code',
                    'register_number'
                )
            )


    def clean(self):

        cleaned = super().clean()

        parameter = cleaned.get(
            'parameter'
        )


        parameter_text = (
            str(parameter).lower()
            if parameter
            else ''
        )


        is_plus2 = (
            '+2 academic performance'
            in parameter_text
        )


        # ======================================
        # +2 ACADEMIC PERFORMANCE
        # ======================================

        if is_plus2:

            required_fields = {

                'board':
                    'Board is required.',

                'school':
                    'School is required.',

                'academic_year':
                    'Academic year is required.',

                'academic_group':
                    'Group is required.',

                'marks_obtained':
                    'Marks obtained is required.',

                'maximum_marks':
                    'Maximum marks is required.',

            }


            for field, message in (
                required_fields.items()
            ):

                if not cleaned.get(field):

                    self.add_error(
                        field,
                        message
                    )


            obtained = cleaned.get(
                'marks_obtained'
            )

            maximum = cleaned.get(
                'maximum_marks'
            )


            if (
                obtained is not None
                and maximum is not None
            ):

                if maximum <= 0:

                    self.add_error(
                        'maximum_marks',
                        'Maximum marks must be greater than zero.'
                    )

                elif obtained > maximum:

                    self.add_error(
                        'marks_obtained',
                        'Marks obtained cannot exceed maximum marks.'
                    )


        # ======================================
        # OTHER ACTIVITIES
        # ======================================

        else:

            if not cleaned.get(
                'title'
            ):

                self.add_error(
                    'title',
                    'Activity title is required.'
                )


            if not cleaned.get(
                'activity_date'
            ):

                self.add_error(
                    'activity_date',
                    'Activity date is required.'
                )


        return cleaned