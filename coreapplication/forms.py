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
from .models import StudentReport, HostelBooking, HostelRoom, AcademicYear

class StudentReportForm(forms.ModelForm):
    class Meta:
        model = StudentReport
        fields = ['report_type', 'subject', 'description', 'priority']
        widgets = {
            'report_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a brief subject for your report',
                'maxlength': '200',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Provide detailed description of your issue...',
                'rows': 5,
                'required': True
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['report_type'].empty_label = "Select Report Type"
        self.fields['priority'].empty_label = "Select Priority Level"
        
        # Add help text
        self.fields['subject'].help_text = "Brief summary of your issue (max 200 characters)"
        self.fields['description'].help_text = "Provide as much detail as possible to help us understand and resolve your issue"
        self.fields['priority'].help_text = "Select the urgency level of your issue"

    def clean_subject(self):
        subject = self.cleaned_data.get('subject')
        if subject and len(subject.strip()) < 5:
            raise ValidationError("Subject must be at least 5 characters long.")
        return subject.strip() if subject else subject

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description and len(description.strip()) < 10:
            raise ValidationError("Description must be at least 10 characters long.")
        return description.strip() if description else description

# forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import HostelBooking, HostelBed, HostelRoom, Hostel


class HostelBookingForm(forms.ModelForm):
    """Form for hostel booking application"""
    
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
        labels = {
            'emergency_contact': 'Emergency Contact Number',
            'medical_info': 'Medical Information',
        }
        help_texts = {
            'emergency_contact': 'Please provide a valid contact number for emergencies.',
            'medical_info': 'Please mention any medical conditions, allergies, or special requirements.',
        }
    
    def clean_emergency_contact(self):
        contact = self.cleaned_data.get('emergency_contact')
        if contact:
            # Remove any non-digit characters
            cleaned_contact = ''.join(filter(str.isdigit, contact))
            if len(cleaned_contact) < 10:
                raise ValidationError("Please enter a valid 10-digit contact number.")
            return cleaned_contact
        return contact


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
    
   