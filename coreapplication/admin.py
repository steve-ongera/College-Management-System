from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    User, Department, Course, Subject, Faculty, Student, Staff,
    AcademicYear, Semester, Enrollment, Grade, Attendance,
    Classroom, TimeSlot, Schedule, FeeStructure, FeePayment,
    Examination, ExamSchedule, Book, BookIssue, Notification,
    NotificationRead, Event, EventRegistration, Document,
    Company, PlacementDrive, PlacementApplication
)

# Custom User Admin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone', 'address', 'date_of_birth', 'profile_picture')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone', 'address', 'date_of_birth', 'profile_picture')
        }),
    )

# Department Admin
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'head_of_department', 'established_date', 'is_active')
    list_filter = ('is_active', 'established_date')
    search_fields = ('name', 'code', 'description')
    list_editable = ('is_active',)
    date_hierarchy = 'established_date'

# Course Admin
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'course_type', 'department', 'duration_years', 'total_semesters', 'fees_per_semester', 'is_active')
    list_filter = ('course_type', 'department', 'is_active', 'duration_years')
    search_fields = ('name', 'code', 'description')
    list_editable = ('is_active',)
    raw_id_fields = ('department',)

# Subject Admin
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'code', 'course', 'year', 'semester',
        'credits', 'theory_hours', 'practical_hours', 'is_elective'
    )
    list_filter = ('course', 'semester', 'is_elective', 'credits')
    search_fields = ('name', 'code')
    list_editable = ('is_elective',)
    raw_id_fields = ('course',)
    filter_horizontal = ('prerequisites',)

    # 🔽 Order subjects by year ASC then semester ASC
    ordering = ('year', 'semester', 'name')
# Faculty Admin
@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'employee_id', 'department', 'designation', 'experience_years', 'joining_date', 'is_active')
    list_filter = ('department', 'designation', 'is_active', 'joining_date')
    search_fields = ('user__first_name', 'user__last_name', 'employee_id', 'qualification', 'specialization')
    list_editable = ('is_active',)
    raw_id_fields = ('user', 'department')
    date_hierarchy = 'joining_date'
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'

# Student Admin
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'student_id', 'course', 'current_semester', 'status', 'admission_date')
    list_filter = ('course', 'status', 'admission_type', 'current_semester', 'admission_date')
    search_fields = ('user__first_name', 'user__last_name', 'student_id', 'guardian_name')
    list_editable = ('status', 'current_semester')
    raw_id_fields = ('user', 'course')
    date_hierarchy = 'admission_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'student_id', 'course', 'current_semester', 'admission_date', 'admission_type', 'status')
        }),
        ('Guardian Information', {
            'fields': ('guardian_name', 'guardian_phone', 'guardian_relation', 'emergency_contact')
        }),
        ('Additional Information', {
            'fields': ('blood_group',)
        }),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'

# Staff Admin
@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'employee_id', 'staff_type', 'department', 'designation', 'joining_date', 'is_active')
    list_filter = ('staff_type', 'department', 'is_active', 'joining_date')
    search_fields = ('user__first_name', 'user__last_name', 'employee_id', 'designation')
    list_editable = ('is_active',)
    raw_id_fields = ('user', 'department')
    date_hierarchy = 'joining_date'
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'

# Academic Year Admin
@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('year', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)
    search_fields = ('year',)
    list_editable = ('is_current',)

# Semester Admin
@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'semester_number', 'start_date', 'end_date', 'is_current')
    list_filter = ('academic_year', 'semester_number', 'is_current')
    list_editable = ('is_current',)
    raw_id_fields = ('academic_year',)

# Enrollment Admin
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('get_student_name', 'get_student_id', 'subject', 'semester', 'enrollment_date', 'is_active')
    list_filter = ('subject__course', 'semester', 'is_active', 'enrollment_date')
    search_fields = ('student__student_id', 'student__user__first_name', 'student__user__last_name', 'subject__name')
    list_editable = ('is_active',)
    raw_id_fields = ('student', 'subject', 'semester')
    date_hierarchy = 'enrollment_date'
    
    def get_student_name(self, obj):
        return obj.student.user.get_full_name()
    get_student_name.short_description = 'Student Name'
    
    def get_student_id(self, obj):
        return obj.student.student_id
    get_student_id.short_description = 'Student ID'

# Grade Admin
@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('get_student_id', 'get_subject', 'theory_marks', 'practical_marks', 'total_marks', 'grade', 'is_passed')
    list_filter = ('grade', 'is_passed', 'enrollment__subject__course')
    search_fields = ('enrollment__student__student_id', 'enrollment__subject__name')
    list_editable = ('is_passed',)
    raw_id_fields = ('enrollment',)
    
    def get_student_id(self, obj):
        return obj.enrollment.student.student_id
    get_student_id.short_description = 'Student ID'
    
    def get_subject(self, obj):
        return obj.enrollment.subject.name
    get_subject.short_description = 'Subject'

# Attendance Admin
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('get_student_id', 'get_student_name', 'subject', 'date', 'status', 'marked_by')
    list_filter = ('status', 'subject', 'date', 'marked_by')
    search_fields = ('student__student_id', 'student__user__first_name', 'student__user__last_name')
    list_editable = ('status',)
    raw_id_fields = ('student', 'subject', 'marked_by')
    date_hierarchy = 'date'
    
    def get_student_id(self, obj):
        return obj.student.student_id
    get_student_id.short_description = 'Student ID'
    
    def get_student_name(self, obj):
        return obj.student.user.get_full_name()
    get_student_name.short_description = 'Student Name'

# Classroom Admin
@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'room_number', 'room_type', 'capacity', 'floor', 'building', 'has_projector', 'has_computer', 'is_active')
    list_filter = ('room_type', 'floor', 'building', 'has_projector', 'has_computer', 'is_active')
    search_fields = ('name', 'room_number')
    list_editable = ('is_active',)

# TimeSlot Admin
@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('day_of_week', 'start_time', 'end_time', 'is_active')
    list_filter = ('day_of_week', 'is_active')
    list_editable = ('is_active',)

# Schedule Admin
@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('subject', 'faculty', 'classroom', 'time_slot', 'semester', 'is_active')
    list_filter = ('subject__course', 'faculty', 'classroom', 'time_slot__day_of_week', 'is_active')
    search_fields = ('subject__name', 'faculty__user__first_name', 'faculty__user__last_name')
    list_editable = ('is_active',)
    raw_id_fields = ('subject', 'faculty', 'classroom', 'time_slot', 'semester')

# Fee Structure Admin
@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('course', 'academic_year', 'semester', 'tuition_fee', 'total_fee_display')
    list_filter = ('course', 'academic_year', 'semester')
    search_fields = ('course__name', 'course__code')
    raw_id_fields = ('course', 'academic_year')
    
    def total_fee_display(self, obj):
        return f"₹{obj.total_fee():,.2f}"
    total_fee_display.short_description = 'Total Fee'

# Fee Payment Admin
@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('get_student_id', 'get_student_name', 'receipt_number', 'amount_paid', 'payment_date', 'payment_method', 'payment_status')
    list_filter = ('payment_method', 'payment_status', 'payment_date')
    search_fields = ('student__student_id', 'receipt_number', 'transaction_id')
    list_editable = ('payment_status',)
    raw_id_fields = ('student', 'fee_structure')
    date_hierarchy = 'payment_date'
    
    def get_student_id(self, obj):
        return obj.student.student_id
    get_student_id.short_description = 'Student ID'
    
    def get_student_name(self, obj):
        return obj.student.user.get_full_name()
    get_student_name.short_description = 'Student Name'

# Examination Admin
@admin.register(Examination)
class ExaminationAdmin(admin.ModelAdmin):
    list_display = ('name', 'exam_type', 'semester', 'start_date', 'end_date', 'max_marks', 'is_active')
    list_filter = ('exam_type', 'semester', 'is_active')
    search_fields = ('name',)
    list_editable = ('is_active',)
    raw_id_fields = ('semester',)
    date_hierarchy = 'start_date'

# Exam Schedule Admin
@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = ('examination', 'subject', 'exam_date', 'start_time', 'end_time', 'classroom', 'max_marks')
    list_filter = ('examination', 'exam_date', 'classroom')
    search_fields = ('subject__name', 'examination__name')
    raw_id_fields = ('examination', 'subject', 'classroom')
    date_hierarchy = 'exam_date'

# Book Admin
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'publisher', 'publication_year', 'total_copies', 'available_copies', 'price')
    list_filter = ('publisher', 'publication_year', 'subject')
    search_fields = ('title', 'author', 'isbn')
    raw_id_fields = ('subject',)

# Book Issue Admin
@admin.register(BookIssue)
class BookIssueAdmin(admin.ModelAdmin):
    list_display = ('get_student_id', 'get_book_title', 'issue_date', 'due_date', 'return_date', 'fine_amount', 'is_returned')
    list_filter = ('is_returned', 'issue_date', 'due_date')
    search_fields = ('student__student_id', 'book__title')
    list_editable = ('is_returned',)
    raw_id_fields = ('book', 'student')
    date_hierarchy = 'issue_date'
    
    def get_student_id(self, obj):
        return obj.student.student_id
    get_student_id.short_description = 'Student ID'
    
    def get_book_title(self, obj):
        return obj.book.title
    get_book_title.short_description = 'Book Title'

# Notification Admin
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'is_global', 'is_active', 'created_by', 'created_at', 'expires_at')
    list_filter = ('notification_type', 'is_global', 'is_active', 'created_at')
    search_fields = ('title', 'message')
    list_editable = ('is_active',)
    raw_id_fields = ('created_by',)
    filter_horizontal = ('target_users',)
    date_hierarchy = 'created_at'

# Notification Read Admin
@admin.register(NotificationRead)
class NotificationReadAdmin(admin.ModelAdmin):
    list_display = ('notification', 'user', 'read_at')
    list_filter = ('read_at',)
    search_fields = ('notification__title', 'user__username')
    raw_id_fields = ('notification', 'user')
    date_hierarchy = 'read_at'

# Event Admin
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_date', 'end_date', 'venue', 'organizer', 'is_public', 'max_participants')
    list_filter = ('event_type', 'is_public', 'start_date')
    search_fields = ('title', 'description', 'venue')
    raw_id_fields = ('organizer',)
    date_hierarchy = 'start_date'

# Event Registration Admin
@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'registration_date', 'is_attended')
    list_filter = ('is_attended', 'registration_date')
    search_fields = ('event__title', 'user__username')
    list_editable = ('is_attended',)
    raw_id_fields = ('event', 'user')
    date_hierarchy = 'registration_date'

# Document Admin
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'document_type', 'get_student_id', 'uploaded_by', 'upload_date', 'is_verified', 'verified_by')
    list_filter = ('document_type', 'is_verified', 'upload_date')
    search_fields = ('title', 'student__student_id')
    list_editable = ('is_verified',)
    raw_id_fields = ('student', 'uploaded_by', 'verified_by')
    date_hierarchy = 'upload_date'
    
    def get_student_id(self, obj):
        return obj.student.student_id
    get_student_id.short_description = 'Student ID'

# Company Admin
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'contact_person', 'contact_email', 'contact_phone', 'is_active')
    list_filter = ('industry', 'is_active')
    search_fields = ('name', 'industry', 'contact_person')
    list_editable = ('is_active',)

# Placement Drive Admin
@admin.register(PlacementDrive)
class PlacementDriveAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'drive_date', 'registration_deadline', 'minimum_percentage', 'salary_package', 'is_active')
    list_filter = ('company', 'drive_date', 'is_active')
    search_fields = ('title', 'company__name', 'description')
    list_editable = ('is_active',)
    raw_id_fields = ('company',)
    filter_horizontal = ('eligible_courses',)
    date_hierarchy = 'drive_date'

# Placement Application Admin
@admin.register(PlacementApplication)
class PlacementApplicationAdmin(admin.ModelAdmin):
    list_display = ('get_student_id', 'get_student_name', 'placement_drive', 'application_date', 'status')
    list_filter = ('status', 'placement_drive', 'application_date')
    search_fields = ('student__student_id', 'placement_drive__title')
    list_editable = ('status',)
    raw_id_fields = ('student', 'placement_drive')
    date_hierarchy = 'application_date'
    
    def get_student_id(self, obj):
        return obj.student.student_id
    get_student_id.short_description = 'Student ID'
    
    def get_student_name(self, obj):
        return obj.student.user.get_full_name()
    get_student_name.short_description = 'Student Name'

# Customize Admin Site
admin.site.site_header = "Polytechnic Management System"
admin.site.site_title = "Polytechnic Admin"
admin.site.index_title = "Welcome to Polytechnic Management System"