from django import forms
from .models import StudentComment

class StudentCommentForm(forms.ModelForm):
    class Meta:
        model = StudentComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter your comment or question here...'
            })
        }


# forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import HostelBooking, HostelRoom, AcademicYear



# forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import HostelBooking, HostelBed, HostelRoom, Hostel


class HostelBookingForm(forms.ModelForm):
    class Meta:
        model = HostelBooking
        fields = ['emergency_contact', 'medical_info']
        widgets = {
            'emergency_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency contact number'
            }),
            'medical_info': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any medical information or conditions'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['emergency_contact'].required = True
        self.fields['medical_info'].required = False


class BedSelectionForm(forms.Form):
    """Form for bed selection in hostel booking"""
    
    hostel = forms.ModelChoiceField(
        queryset=Hostel.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'hostel-select',
            'onchange': 'loadRooms(this.value)'
        }),
        label='Select Hostel',
        help_text='Choose your preferred hostel'
    )
    
    room = forms.ModelChoiceField(
        queryset=HostelRoom.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'room-select',
            'onchange': 'loadBeds(this.value)',
            'disabled': True
        }),
        label='Select Room',
        help_text='Choose your preferred room'
    )
    
    bed = forms.ModelChoiceField(
        queryset=HostelBed.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'bed-select',
            'disabled': True
        }),
        label='Select Bed',
        help_text='Choose your preferred bed'
    )
    
    def __init__(self, *args, **kwargs):
        student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        
        if student:
            # Filter hostels based on student's gender
            student_gender = getattr(student.user, 'gender', None)
            if student_gender == 'male':
                self.fields['hostel'].queryset = Hostel.objects.filter(
                    hostel_type='boys', is_active=True
                )
            elif student_gender == 'female':
                self.fields['hostel'].queryset = Hostel.objects.filter(
                    hostel_type='girls', is_active=True
                )
    
    def clean_bed(self):
        bed = self.cleaned_data.get('bed')
        if bed and not bed.is_available:
            raise ValidationError("This bed is not available for booking.")
        return bed


class HostelFilterForm(forms.Form):
    """Form for filtering hostels and rooms"""
    
    hostel_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Hostel.HOSTEL_TYPES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    has_available_beds = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    floor = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Floor number'
        })
    )
    
    bed_type = forms.ChoiceField(
        choices=[('', 'All Bed Types')] + [
            ('single', 'Single Bed'),
            ('bunk_top', 'Bunk Bed (Top)'),
            ('bunk_bottom', 'Bunk Bed (Bottom)'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class RoomFilterForm(forms.Form):
    """Form for filtering rooms within a hostel"""
    
    floor = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Floor number'
        })
    )
    
    available_beds_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    min_available_beds = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=4,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum available beds'
        })
    )


class BedFilterForm(forms.Form):
    """Form for filtering beds within a room"""
    
    bed_type = forms.ChoiceField(
        choices=[('', 'All Bed Types')] + [
            ('single', 'Single Bed'),
            ('bunk_top', 'Bunk Bed (Top)'),
            ('bunk_bottom', 'Bunk Bed (Bottom)'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    available_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    exclude_maintenance = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class QuickBedBookingForm(forms.ModelForm):
    """Form for quick bed booking with integrated selection"""
    
    hostel = forms.ModelChoiceField(
        queryset=Hostel.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'quick-hostel-select',
            'onchange': 'loadQuickRooms(this.value)'
        }),
        label='Select Hostel'
    )
    
    room = forms.ModelChoiceField(
        queryset=HostelRoom.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'quick-room-select',
            'onchange': 'loadQuickBeds(this.value)',
            'disabled': True
        }),
        label='Select Room'
    )
    
    bed = forms.ModelChoiceField(
        queryset=HostelBed.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'quick-bed-select',
            'disabled': True
        }),
        label='Select Bed'
    )
    
    class Meta:
        model = HostelBooking
        fields = ['emergency_contact', 'medical_info']
        widgets = {
            'emergency_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter emergency contact number',
                'required': True
            }),
            'medical_info': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter any medical conditions or allergies (optional)',
                'rows': 3
            }),
        }
    
    def __init__(self, *args, **kwargs):
        student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        
        if student:
            # Filter hostels based on student's gender
            student_gender = getattr(student.user, 'gender', None)
            if student_gender == 'male':
                self.fields['hostel'].queryset = Hostel.objects.filter(
                    hostel_type='boys', is_active=True
                )
            elif student_gender == 'female':
                self.fields['hostel'].queryset = Hostel.objects.filter(
                    hostel_type='girls', is_active=True
                )
    
    def clean_bed(self):
        bed = self.cleaned_data.get('bed')
        if bed and not bed.is_available:
            raise ValidationError("This bed is not available for booking.")
        return bed
    
    def clean_emergency_contact(self):
        contact = self.cleaned_data.get('emergency_contact')
        if contact:
            # Remove any non-digit characters
            cleaned_contact = ''.join(filter(str.isdigit, contact))
            if len(cleaned_contact) < 10:
                raise ValidationError("Please enter a valid 10-digit contact number.")
            return cleaned_contact
        return contact


class AdminBookingFilterForm(forms.Form):
    """Form for admin to filter hostel bookings"""
    
    status = forms.ChoiceField(
       choices=[('', 'All Status')] + list(HostelBooking.BOOKING_STATUS),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    hostel = forms.ModelChoiceField(
        queryset=Hostel.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'loadAdminRooms(this.value)'
        })
    )
    
    room = forms.ModelChoiceField(
        queryset=HostelRoom.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    academic_year = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    

# forms.py
# Updated forms.py
# Updated forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.validators import UnicodeUsernameValidator
from .models import Student, Course
import re

User = get_user_model()

class CustomUsernameValidator:
    """Custom validator that allows more characters in username including forward slashes"""
    
    def __call__(self, value):
        # Allow letters, numbers, and these special characters: @/./+/-/_ and forward slash
        pattern = r'^[\w.@+\-/]+$'  # Fixed: Added closing quote and $ anchor
        
        if not re.match(pattern, value):
            raise ValidationError(
                "Username can only contain letters, numbers, and the characters @/./+/-/_",
                code='invalid_username'
            )
        return value

class UserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True,
        min_length=4,  # Allow simple passwords
        help_text="Enter a simple password (minimum 4 characters)"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True,
        help_text="Confirm your password"
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'password',
            'phone', 'address', 'gender', 'date_of_birth', 'profile_picture'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'required': True}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Completely override the username field to remove default validators
        self.fields['username'] = forms.CharField(
            max_length=150,
            validators=[CustomUsernameValidator()],
            widget=forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            help_text="Username can contain letters, numbers, and @/./+/-/_ characters including forward slashes"
        )
        
        # Make required fields explicit
        self.fields['username'].required = True
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['password'].required = True
        self.fields['confirm_password'].required = True

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Check for existing username, excluding current instance if editing
            if self.instance and self.instance.pk:
                if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
                    raise ValidationError("Username already exists. Please choose a different username.")
            else:
                if User.objects.filter(username=username).exists():
                    raise ValidationError("Username already exists. Please choose a different username.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check for existing email, excluding current instance if editing
            if self.instance and self.instance.pk:
                if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                    raise ValidationError("Email already exists. Please use a different email.")
            else:
                if User.objects.filter(email=email).exists():
                    raise ValidationError("Email already exists. Please use a different email.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password:
            if password != confirm_password:
                raise ValidationError("Passwords don't match")
            
            # Allow simple passwords for development
            if len(password) < 4:
                raise ValidationError("Password must be at least 4 characters long")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        # Set the password properly
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        
        if commit:
            user.save()
        return user


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'student_id', 'course', 'current_semester', 'current_year',
            'admission_date', 'admission_type', 'status', 'guardian_name',
            'guardian_phone', 'guardian_relation', 'emergency_contact', 'blood_group'
        ]
        widgets = {
            'student_id': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'admission_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'current_semester': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 8}),
            'current_year': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 4}),
            'admission_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_relation': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'blood_group': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make sure course queryset is available
        if Course.objects.exists():
            self.fields['course'].queryset = Course.objects.filter(is_active=True)
        else:
            self.fields['course'].queryset = Course.objects.all()
        
        # Make required fields explicit
        self.fields['student_id'].required = True
        self.fields['course'].required = True

    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        if not student_id:
            raise ValidationError("Student ID is required")
        
        # Check for duplicate student ID
        if self.instance and self.instance.pk:
            if Student.objects.filter(student_id=student_id).exclude(pk=self.instance.pk).exists():
                raise ValidationError("Student ID already exists")
        else:
            if Student.objects.filter(student_id=student_id).exists():
                raise ValidationError("Student ID already exists")
        return student_id

# forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Course, Department

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'name', 'code', 'course_type', 'department', 
            'duration_years', 'total_semesters', 'description', 
            'fees_per_semester', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter course name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter course code (e.g., CSE101)',
                'style': 'text-transform: uppercase;'
            }),
            'course_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'department': forms.Select(attrs={
                'class': 'form-select'
            }),
            'duration_years': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '5',
                'placeholder': 'Number of years'
            }),
            'total_semesters': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '2',
                'max': '10',
                'placeholder': 'Total semesters'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': 'Enter course description...'
            }),
            'fees_per_semester': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Fee amount per semester'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active departments only
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        
        # Set initial value for is_active
        if not self.instance.pk:
            self.fields['is_active'].initial = True
        
        # Add required indicator to labels
        required_fields = ['name', 'code', 'course_type', 'department', 'duration_years', 'total_semesters', 'fees_per_semester']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].label = f"{self.fields[field_name].label} *"

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper()
            # Check if code already exists (excluding current instance if editing)
            existing = Course.objects.filter(code=code)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("A course with this code already exists.")
        return code

    def clean(self):
        cleaned_data = super().clean()
        duration_years = cleaned_data.get('duration_years')
        total_semesters = cleaned_data.get('total_semesters')
        
        if duration_years and total_semesters:
            # Basic validation: semesters should be reasonable for the duration
            min_semesters = duration_years * 2  # 2 semesters per year minimum
            max_semesters = duration_years * 2  # 2 semesters per year maximum
            
            if total_semesters < min_semesters or total_semesters > max_semesters:
                raise ValidationError(
                    f"For {duration_years} years, total semesters should be {min_semesters} to {max_semesters}."
                )
        
        return cleaned_data


# forms.py
from django import forms
from .models import Subject, Course

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = [
            'name', 'code', 'course', 'year', 'semester', 'credits',
            'theory_hours', 'practical_hours', 'is_elective', 'is_active',
            'prerequisites'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject Name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject Code'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'semester': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'credits': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'theory_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'practical_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'is_elective': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'prerequisites': forms.CheckboxSelectMultiple(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only show active courses
        self.fields['course'].queryset = Course.objects.filter(is_active=True).order_by('name')
        
        # Filter prerequisites to exclude self and inactive subjects
        if self.instance and self.instance.pk:
            self.fields['prerequisites'].queryset = Subject.objects.filter(
                is_active=True
            ).exclude(pk=self.instance.pk).order_by('course__name', 'year', 'semester', 'name')
        else:
            self.fields['prerequisites'].queryset = Subject.objects.filter(
                is_active=True
            ).order_by('course__name', 'year', 'semester', 'name')
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper()
            
            # Check for duplicate codes
            existing = Subject.objects.filter(code=code)
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError('A subject with this code already exists.')
        
        return code
    
    def clean(self):
        cleaned_data = super().clean()
        year = cleaned_data.get('year')
        semester = cleaned_data.get('semester')
        course = cleaned_data.get('course')
        
        # Validate year and semester against course limits
        if course and year and semester:
            if year > course.duration_years:
                raise forms.ValidationError(
                    f'Year cannot be greater than {course.duration_years} for this course.'
                )
            
            if semester > course.total_semesters:
                raise forms.ValidationError(
                    f'Semester cannot be greater than {course.total_semesters} for this course.'
                )
        
        return cleaned_data