from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

# Custom User Model
class User(AbstractUser):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    USER_TYPES = (
        ('admin', 'Admin'),
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('staff', 'Staff'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.user_type})"

# Academic Structure Models
class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    head_of_department = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_departments')
    established_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class Course(models.Model):
    COURSE_TYPES = (
        ('diploma', 'Diploma'),
        ('certificate', 'Certificate'),
        ('advanced_diploma', 'Advanced Diploma'),
    )
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    course_type = models.CharField(max_length=20, choices=COURSE_TYPES)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    duration_years = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)]) # total sem per year
    total_semesters = models.IntegerField(validators=[MinValueValidator(2), MaxValueValidator(10)])
    description = models.TextField(blank=True)
    fees_per_semester = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"
#units
class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=15, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='subjects')
    year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=1)  # 🔹 New field
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    credits = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    theory_hours = models.IntegerField(default=0)
    practical_hours = models.IntegerField(default=0)
    is_elective = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

# People Models
class Faculty(models.Model):
    DESIGNATION_CHOICES = (
        ('professor', 'Professor'),
        ('associate_professor', 'Associate Professor'),
        ('assistant_professor', 'Assistant Professor'),
        ('lecturer', 'Lecturer'),
        ('instructor', 'Instructor'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='faculty_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='faculty_members')
    designation = models.CharField(max_length=30, choices=DESIGNATION_CHOICES)
    qualification = models.CharField(max_length=200)
    experience_years = models.IntegerField(default=0)
    specialization = models.CharField(max_length=200, blank=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    joining_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_id}"

class Student(models.Model):
    ADMISSION_TYPES = (
        ('regular', 'Regular'),
        ('lateral_entry', 'Lateral Entry'),
        ('transfer', 'Transfer'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('graduated', 'Graduated'),
        ('suspended', 'Suspended'),
        ('dropped', 'Dropped'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='students')
    current_semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    current_year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    admission_date = models.DateField()
    admission_type = models.CharField(max_length=20, choices=ADMISSION_TYPES, default='regular')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    guardian_name = models.CharField(max_length=100)
    guardian_phone = models.CharField(max_length=15)
    guardian_relation = models.CharField(max_length=50)
    emergency_contact = models.CharField(max_length=15)
    blood_group = models.CharField(max_length=5, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.student_id}"

class Staff(models.Model):
    STAFF_TYPES = (
        ('administrative', 'Administrative'),
        ('technical', 'Technical'),
        ('support', 'Support'),
        ('maintenance', 'Maintenance'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    staff_type = models.CharField(max_length=20, choices=STAFF_TYPES)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    joining_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_id}"

# Academic Records Models
class AcademicYear(models.Model):
    year = models.CharField(max_length=10, unique=True)  # e.g., "2024-25"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    def __str__(self):
        return self.year

class Semester(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='semesters')
    semester_number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(2)])
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['academic_year', 'semester_number']
    
    def __str__(self):
        return f"{self.academic_year.year} - Semester {self.semester_number}"

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='enrollments')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['student', 'subject', 'semester']
    
    def __str__(self):
        return f"{self.student.student_id} - {self.subject.code}"

class Grade(models.Model):
    GRADE_CHOICES = (
        ('A+', 'A+ (90-100)'),
        ('A', 'A (80-89)'),
        ('B+', 'B+ (70-79)'),
        ('B', 'B (60-69)'),
        ('C+', 'C+ (50-59)'),
        ('C', 'C (40-49)'),
        ('D', 'D (30-39)'),
        ('F', 'F (Below 30)'),
    )
    
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='grade')
    theory_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    practical_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, blank=True)
    grade_points = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    is_passed = models.BooleanField(default=False)
    exam_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.enrollment.student.student_id} - {self.enrollment.subject.code} - {self.grade}"

# Attendance Models
class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'subject', 'date']
    
    def __str__(self):
        return f"{self.student.student_id} - {self.subject.code} - {self.date} - {self.status}"

# Timetable Models
class Classroom(models.Model):
    ROOM_TYPES = (
        ('lecture', 'Lecture Hall'),
        ('lab', 'Laboratory'),
        ('workshop', 'Workshop'),
        ('seminar', 'Seminar Room'),
    )
    
    name = models.CharField(max_length=50)
    room_number = models.CharField(max_length=20, unique=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    capacity = models.IntegerField()
    floor = models.CharField(max_length=10)
    building = models.CharField(max_length=50)
    has_projector = models.BooleanField(default=False)
    has_computer = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.room_number})"

class TimeSlot(models.Model):
    DAY_CHOICES = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    )
    
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.day_of_week} {self.start_time} - {self.end_time}"

class Schedule(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='schedules')
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='schedules')
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='schedules')
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='schedules')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='schedules')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['classroom', 'time_slot', 'semester']
    
    def __str__(self):
        return f"{self.subject.code} - {self.time_slot} - {self.classroom.name}"

# Fee Management Models
class FeeStructure(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='fee_structures')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='fee_structures')
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2)
    lab_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    library_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    exam_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    development_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['course', 'academic_year', 'semester']
    
    def total_fee(self):
        return self.tuition_fee + self.lab_fee + self.library_fee + self.exam_fee + self.development_fee + self.other_fee
    
    def __str__(self):
        return f"{self.course.code} - {self.academic_year.year} - Sem {self.semester}"

class FeePayment(models.Model):
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('online', 'Online Payment'),
        ('cheque', 'Cheque'),
        ('dd', 'Demand Draft'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_payments')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='payments')
    receipt_number = models.CharField(max_length=50, unique=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.student.student_id} - {self.receipt_number} - {self.amount_paid}"

# Examination Models
class Examination(models.Model):
    EXAM_TYPES = (
        ('mid_semester', 'Mid Semester'),
        ('end_semester', 'End Semester'),
        ('internal', 'Internal Assessment'),
        ('practical', 'Practical'),
        ('project', 'Project'),
        ('assignment', 'Assignment'),
    )
    
    name = models.CharField(max_length=100)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='examinations')
    start_date = models.DateField()
    end_date = models.DateField()
    max_marks = models.IntegerField(default=100)
    min_marks = models.IntegerField(default=40)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.semester}"

class ExamSchedule(models.Model):
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='schedules')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='exam_schedules')
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='exam_schedules')
    max_marks = models.IntegerField(default=100)
    
    def __str__(self):
        return f"{self.examination.name} - {self.subject.code} - {self.exam_date}"

# Library Management Models
class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=13, unique=True)
    publisher = models.CharField(max_length=100)
    publication_year = models.IntegerField()
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    total_copies = models.IntegerField(default=1)
    available_copies = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.title} by {self.author}"

class BookIssue(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='issues')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='book_issues')
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_returned = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.student.student_id} - {self.book.title}"

# Notification Models
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('general', 'General'),
        ('academic', 'Academic'),
        ('fee', 'Fee Related'),
        ('exam', 'Examination'),
        ('event', 'Event'),
        ('emergency', 'Emergency'),
    )
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    target_users = models.ManyToManyField(User, blank=True, related_name='notifications')
    is_global = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.title

class NotificationRead(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='reads')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_reads')
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['notification', 'user']

# Event Management Models
class Event(models.Model):
    EVENT_TYPES = (
        ('academic', 'Academic'),
        ('cultural', 'Cultural'),
        ('sports', 'Sports'),
        ('workshop', 'Workshop'),
        ('seminar', 'Seminar'),
        ('conference', 'Conference'),
        ('holiday', 'Holiday'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    venue = models.CharField(max_length=200)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    is_public = models.BooleanField(default=True)
    max_participants = models.IntegerField(null=True, blank=True)
    registration_required = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title

class EventRegistration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_registrations')
    registration_date = models.DateTimeField(auto_now_add=True)
    is_attended = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['event', 'user']

# Document Management Models
class Document(models.Model):
    DOCUMENT_TYPES = (
        ('certificate', 'Certificate'),
        ('transcript', 'Transcript'),
        ('id_card', 'ID Card'),
        ('fee_receipt', 'Fee Receipt'),
        ('bonafide', 'Bonafide Certificate'),
        ('conduct', 'Conduct Certificate'),
        ('other', 'Other'),
    )
    
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='documents/')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='documents')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_documents')
    upload_date = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    
    def __str__(self):
        return f"{self.student.student_id} - {self.title}"

# Placement Models
class Company(models.Model):
    name = models.CharField(max_length=200)
    industry = models.CharField(max_length=100)
    website = models.URLField(blank=True)
    contact_person = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=15)
    address = models.TextField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class PlacementDrive(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='placement_drives')
    title = models.CharField(max_length=200)
    description = models.TextField()
    eligible_courses = models.ManyToManyField(Course, related_name='placement_drives')
    minimum_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    salary_package = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    drive_date = models.DateField()
    registration_deadline = models.DateField()
    venue = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.company.name} - {self.title}"

class PlacementApplication(models.Model):
    APPLICATION_STATUS = (
        ('applied', 'Applied'),
        ('shortlisted', 'Shortlisted'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='placement_applications')
    placement_drive = models.ForeignKey(PlacementDrive, on_delete=models.CASCADE, related_name='applications')
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS, default='applied')
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['student', 'placement_drive']
    
    def __str__(self):
        return f"{self.student.student_id} - {self.placement_drive.title}"
    

class StudentComment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_resolved = models.BooleanField(default=False)
    admin_response = models.TextField(blank=True, null=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='responded_comments')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Student Comment'
        verbose_name_plural = 'Student Comments'
    
    def __str__(self):
        return f"Comment by {self.student.student_id} on {self.created_at.date()}"
    


class CommonQuestion(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'question']
    
    def __str__(self):
        return self.question

class QuickLink(models.Model):
    title = models.CharField(max_length=100)
    url = models.URLField()
    icon = models.CharField(max_length=50)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'title']
    
    def __str__(self):
        return self.title
    



class StudentClub(models.Model):
    CATEGORY_CHOICES = [
        ('academic', 'Academic'),
        ('cultural', 'Cultural'),
        ('sports', 'Sports'),
        ('religious', 'Religious'),
        ('social', 'Social'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    chairperson = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='chaired_clubs')
    contact_phone = models.CharField(max_length=15)
    email = models.EmailField()
    meeting_schedule = models.TextField()
    membership_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    logo = models.ImageField(upload_to='club_logos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class ClubMembership(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='club_memberships')
    club = models.ForeignKey(StudentClub, on_delete=models.CASCADE, related_name='members')
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_executive = models.BooleanField(default=False)
    position = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        unique_together = ('student', 'club')
    
    def __str__(self):
        return f"{self.student.username} in {self.club.name}"





class ClubEvent(models.Model):
    EVENT_STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    club = models.ForeignKey(StudentClub, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    location = models.CharField(max_length=100)
    organizer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='club_organized_events')
    status = models.CharField(max_length=20, choices=EVENT_STATUS_CHOICES, default='upcoming')
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    registration_required = models.BooleanField(default=False)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_datetime']
        
    def __str__(self):
        return f"{self.title} - {self.club.name}"
    
    def save(self, *args, **kwargs):
        # Automatically update status based on current time
        now = timezone.now()
        if self.start_datetime > now:
            self.status = 'upcoming'
        elif self.start_datetime <= now <= self.end_datetime:
            self.status = 'ongoing'
        elif self.end_datetime < now:
            self.status = 'completed'
        super().save(*args, **kwargs)




class NewsArticle(models.Model):
    CATEGORY_CHOICES = [
        ('academic', 'Academic'),
        ('event', 'Events'),
        ('announcement', 'Announcements'),
        ('sports', 'Sports'),
        ('general', 'General'),
    ]
    
    title = models.CharField(max_length=200)
    summary = models.TextField()
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    image = models.ImageField(upload_to='news_images/', blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    publish_date = models.DateTimeField(default=timezone.now)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-publish_date']
        verbose_name = 'News Article'
        verbose_name_plural = 'News Articles'



# Additional models to add to your existing models.py file

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError

# Student Reporting Models
class StudentReport(models.Model):
    REPORT_TYPES = (
        ('academic', 'Academic Issue'),
        ('disciplinary', 'Disciplinary Issue'),
        ('facility', 'Facility Issue'),
        ('health', 'Health Issue'),
        ('financial', 'Financial Issue'),
        ('accommodation', 'Accommodation Issue'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    )
    
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='reports')
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE, related_name='student_reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_reports')
    admin_response = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Student Report'
        verbose_name_plural = 'Student Reports'
    
    def clean(self):
        # Ensure report is for current semester in active academic year
        if self.semester and not self.semester.is_current:
            raise ValidationError("Reports can only be made for the current semester.")
        
        if self.semester and not self.semester.academic_year.is_current:
            raise ValidationError("Reports can only be made for the current academic year.")
    
    def save(self, *args, **kwargs):
        self.clean()
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student.student_id} - {self.subject} ({self.status})"


# Hostel Management Models
class Hostel(models.Model):
    HOSTEL_TYPES = (
        ('boys', 'Boys Hostel'),
        ('girls', 'Girls Hostel'),
    )
    
    name = models.CharField(max_length=100)
    hostel_type = models.CharField(max_length=10, choices=HOSTEL_TYPES)
    initials = models.CharField(max_length=5, unique=True)  # e.g., 'BH1', 'GH1'
    total_rooms = models.IntegerField()
    warden = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_hostels')
    description = models.TextField(blank=True)
    facilities = models.TextField(blank=True)
    rules = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.initials})"
    
    @property
    def available_rooms(self):
        return self.rooms.filter(is_available=True).count()
    
    @property
    def occupied_rooms(self):
        return self.rooms.filter(is_available=False).count()


class HostelRoom(models.Model):
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=10)
    room_name = models.CharField(max_length=20)  # e.g., 'BH1-101', 'GH1-201'
    floor = models.IntegerField()
    total_beds = models.IntegerField(default=4)
    is_available = models.BooleanField(default=True)
    facilities = models.TextField(blank=True)  # e.g., 'AC, WiFi, Study Table'
    
    class Meta:
        unique_together = ['hostel', 'room_number']
    
    def save(self, *args, **kwargs):
        if not self.room_name:
            self.room_name = f"{self.hostel.initials}-{self.room_number}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.room_name} ({self.hostel.name})"
    
    @property
    def available_beds(self):
        return self.total_beds - self.bookings.filter(
            is_active=True,
            academic_year__is_current=True
        ).count()
    
    @property
    def occupied_beds(self):
        return self.bookings.filter(
            is_active=True,
            academic_year__is_current=True
        ).count()


class HostelBooking(models.Model):
    BOOKING_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )
    
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='hostel_bookings')
    room = models.ForeignKey(HostelRoom, on_delete=models.CASCADE, related_name='bookings')
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE, related_name='hostel_bookings')
    bed_number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)])
    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')
    check_in_date = models.DateField(null=True, blank=True)
    check_out_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    approved_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_bookings')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=15)
    medical_info = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['student', 'academic_year']  # One booking per student per academic year
        ordering = ['-booking_date']
    
    def clean(self):
        if self.student:
            # Check if student is in year 1, semester 1
            if self.student.current_year != 1:
                raise ValidationError("Only first-year students can apply for hostel accommodation.")
            
            if self.student.current_semester != 1:
                raise ValidationError("Hostel applications are only available for first semester students.")
            
            # Check gender compatibility
            if self.room:
                student_gender = getattr(self.student.user, 'gender', None)  # Assuming gender field exists
                if self.room.hostel.hostel_type == 'boys' and student_gender == 'female':
                    raise ValidationError("Female students cannot apply for boys' hostel.")
                elif self.room.hostel.hostel_type == 'girls' and student_gender == 'male':
                    raise ValidationError("Male students cannot apply for girls' hostel.")
        
        # Check if bed is available
        if self.room and self.bed_number:
            existing_booking = HostelBooking.objects.filter(
                room=self.room,
                bed_number=self.bed_number,
                academic_year=self.academic_year,
                is_active=True,
                status='approved'
            ).exclude(id=self.id)
            
            if existing_booking.exists():
                raise ValidationError(f"Bed {self.bed_number} in room {self.room.room_name} is already occupied.")
    
    def save(self, *args, **kwargs):
        self.clean()
        if self.status == 'approved' and not self.approved_at:
            self.approved_at = timezone.now()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student.student_id} - {self.room.room_name} - Bed {self.bed_number}"


class HostelFeeStructure(models.Model):
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='fee_structures')
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE, related_name='hostel_fees')
    accommodation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    mess_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    maintenance_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['hostel', 'academic_year']
    
    def total_fee(self):
        return (self.accommodation_fee + self.mess_fee + 
                self.security_deposit + self.maintenance_fee + self.other_charges)
    
    def __str__(self):
        return f"{self.hostel.name} - {self.academic_year.year}"


class HostelFeePayment(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    booking = models.ForeignKey(HostelBooking, on_delete=models.CASCADE, related_name='fee_payments')
    fee_structure = models.ForeignKey(HostelFeeStructure, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=[
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('online', 'Online Payment'),
        ('cheque', 'Cheque'),
    ])
    transaction_id = models.CharField(max_length=100, blank=True)
    receipt_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    def __str__(self):
        return f"{self.booking.student.student_id} - {self.receipt_number}"


