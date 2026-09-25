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
    class Meta:
        model = ActivityEvidence

        fields = [
            'parameter',
            'title',
            'activity_date',
            'evidence',
            'remarks',
        ]

        widgets = {
            'activity_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
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

            'remarks': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3
                }
            ),
        }

    def clean_username(self):

        username = self.cleaned_data['username'].strip()

        if User.objects.filter(
            username__iexact=username
        ).exists():

            raise forms.ValidationError(
                'This username already exists.'
            )

        return username

    def clean(self):

        cleaned = super().clean()

        selected_role = cleaned.get('role')
        department = cleaned.get('department')
        student = cleaned.get('student')

        if selected_role in ['HOD', 'FACULTY']:

            if not department:

                self.add_error(
                    'department',
                    'Department is required.'
                )

        if selected_role == 'STUDENT':

            if not student:

                self.add_error(
                    'student',
                    'Select the student for this login.'
                )

            elif Profile.objects.filter(
                student=student
            ).exists():

                self.add_error(
                    'student',
                    'This student already has a login account.'
                )

        return cleaned