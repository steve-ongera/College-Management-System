from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q, Avg, Sum, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import *
from datetime import datetime, timedelta

# Authentication Views
def student_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user is not None and user.user_type == 'student':
            login(request, user)
            return redirect('student_dashboard')
        else:
            messages.error(request, 'Invalid credentials or not a student account')
    
    return render(request, 'student/login.html')

def student_register(request):
    if request.method == 'POST':
        # Handle student registration
        pass
    return render(request, 'student/register.html')

def student_logout(request):
    logout(request)
    return redirect('student_login')

# Dashboard View
@login_required
def student_dashboard(request):
    student = get_object_or_404(Student, user=request.user)
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get enrolled subjects for current semester
    current_enrollments = Enrollment.objects.filter(
        student=student,
        semester=current_semester,
        is_active=True
    )
    
    # Get recent grades
    recent_grades = Grade.objects.filter(
        enrollment__student=student
    ).order_by('-exam_date')[:5]
    
    # Get attendance summary
    attendance_summary = []
    for enrollment in current_enrollments:
        total_classes = Attendance.objects.filter(
            student=student,
            subject=enrollment.subject
        ).count()
        
        present_classes = Attendance.objects.filter(
            student=student,
            subject=enrollment.subject,
            status='present'
        ).count()
        
        attendance_percentage = (present_classes / total_classes * 100) if total_classes > 0 else 0
        
        attendance_summary.append({
            'subject': enrollment.subject,
            'total_classes': total_classes,
            'present_classes': present_classes,
            'attendance_percentage': attendance_percentage
        })
    
    # Get upcoming exams
    upcoming_exams = ExamSchedule.objects.filter(
        subject__in=[e.subject for e in current_enrollments],
        exam_date__gte=timezone.now().date()
    ).order_by('exam_date')[:5]
    
    # Get pending fees
    pending_fees = FeePayment.objects.filter(
        student=student,
        payment_status='pending'
    ).aggregate(total=Sum('amount_paid'))['total'] or 0
    
    # Get recent notifications
    recent_notifications = Notification.objects.filter(
        Q(target_users=request.user) | Q(is_global=True),
        is_active=True
    ).order_by('-created_at')[:5]
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'current_enrollments': current_enrollments,
        'recent_grades': recent_grades,
        'attendance_summary': attendance_summary,
        'upcoming_exams': upcoming_exams,
        'pending_fees': pending_fees,
        'recent_notifications': recent_notifications,
    }
    
    return render(request, 'student/dashboard.html', context)

# Profile Views
@login_required
def student_profile(request):
    student = get_object_or_404(Student, user=request.user)
    
    if request.method == 'POST':
        # Handle profile update
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.phone = request.POST.get('phone')
        user.address = request.POST.get('address')
        user.save()
        
        student.guardian_name = request.POST.get('guardian_name')
        student.guardian_phone = request.POST.get('guardian_phone')
        student.guardian_relation = request.POST.get('guardian_relation')
        student.emergency_contact = request.POST.get('emergency_contact')
        student.blood_group = request.POST.get('blood_group')
        student.save()
        
        messages.success(request, 'Profile updated successfully')
        return redirect('student_profile')
    
    context = {
        'student': student,
    }
    return render(request, 'student/profile.html', context)

# Academic Views
@login_required
def student_subjects(request):
    student = get_object_or_404(Student, user=request.user)
    current_semester = Semester.objects.filter(is_current=True).first()
    
    enrollments = Enrollment.objects.filter(
        student=student,
        semester=current_semester,
        is_active=True
    ).select_related('subject', 'subject__course')
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'current_semester': current_semester,
    }
    return render(request, 'student/subjects.html', context)

@login_required
def student_timetable(request):
    student = get_object_or_404(Student, user=request.user)
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get enrolled subjects for current semester
    enrolled_subjects = Enrollment.objects.filter(
        student=student,
        semester=current_semester,
        is_active=True
    ).values_list('subject', flat=True)
    
    # Get schedules for enrolled subjects
    schedules = Schedule.objects.filter(
        subject__in=enrolled_subjects,
        semester=current_semester,
        is_active=True
    ).select_related('subject', 'faculty', 'classroom', 'time_slot')
    
    # Organize by day
    timetable = {}
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    
    for day in days:
        timetable[day] = schedules.filter(time_slot__day_of_week=day).order_by('time_slot__start_time')
    
    context = {
        'student': student,
        'timetable': timetable,
        'current_semester': current_semester,
    }
    return render(request, 'student/timetable.html', context)

@login_required
def student_grades(request):
    student = get_object_or_404(Student, user=request.user)
    
    # Get all grades grouped by semester
    grades_by_semester = {}
    enrollments = Enrollment.objects.filter(student=student).select_related('subject', 'semester')
    
    for enrollment in enrollments:
        semester = enrollment.semester
        if semester not in grades_by_semester:
            grades_by_semester[semester] = []
        
        try:
            grade = Grade.objects.get(enrollment=enrollment)
            grades_by_semester[semester].append(grade)
        except Grade.DoesNotExist:
            pass
    
    # Calculate semester-wise GPA
    semester_gpa = {}
    for semester, grades in grades_by_semester.items():
        if grades:
            total_points = sum(g.grade_points * g.enrollment.subject.credits for g in grades if g.grade_points)
            total_credits = sum(g.enrollment.subject.credits for g in grades if g.grade_points)
            gpa = total_points / total_credits if total_credits > 0 else 0
            semester_gpa[semester] = gpa
    
    # Calculate overall GPA
    all_grades = Grade.objects.filter(enrollment__student=student, grade_points__isnull=False)
    if all_grades:
        total_points = sum(g.grade_points * g.enrollment.subject.credits for g in all_grades)
        total_credits = sum(g.enrollment.subject.credits for g in all_grades)
        overall_gpa = total_points / total_credits if total_credits > 0 else 0
    else:
        overall_gpa = 0
    
    context = {
        'student': student,
        'grades_by_semester': grades_by_semester,
        'semester_gpa': semester_gpa,
        'overall_gpa': overall_gpa,
    }
    return render(request, 'student/grades.html', context)

@login_required
def student_attendance(request):
    student = get_object_or_404(Student, user=request.user)
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get enrolled subjects for current semester
    enrolled_subjects = Enrollment.objects.filter(
        student=student,
        semester=current_semester,
        is_active=True
    ).values_list('subject', flat=True)
    
    # Get attendance summary for each subject
    attendance_summary = []
    for subject_id in enrolled_subjects:
        subject = Subject.objects.get(id=subject_id)
        
        total_classes = Attendance.objects.filter(
            student=student,
            subject=subject
        ).count()
        
        present_classes = Attendance.objects.filter(
            student=student,
            subject=subject,
            status='present'
        ).count()
        
        absent_classes = Attendance.objects.filter(
            student=student,
            subject=subject,
            status='absent'
        ).count()
        
        late_classes = Attendance.objects.filter(
            student=student,
            subject=subject,
            status='late'
        ).count()
        
        attendance_percentage = (present_classes / total_classes * 100) if total_classes > 0 else 0
        
        attendance_summary.append({
            'subject': subject,
            'total_classes': total_classes,
            'present_classes': present_classes,
            'absent_classes': absent_classes,
            'late_classes': late_classes,
            'attendance_percentage': attendance_percentage
        })
    
    # Get recent attendance records
    recent_attendance = Attendance.objects.filter(
        student=student
    ).order_by('-date')[:10]
    
    context = {
        'student': student,
        'attendance_summary': attendance_summary,
        'recent_attendance': recent_attendance,
        'current_semester': current_semester,
    }
    return render(request, 'student/attendance.html', context)

# Examination Views
@login_required
def student_exam_schedule(request):
    student = get_object_or_404(Student, user=request.user)
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get enrolled subjects for current semester
    enrolled_subjects = Enrollment.objects.filter(
        student=student,
        semester=current_semester,
        is_active=True
    ).values_list('subject', flat=True)
    
    # Get exam schedules
    exam_schedules = ExamSchedule.objects.filter(
        subject__in=enrolled_subjects,
        examination__semester=current_semester
    ).select_related('examination', 'subject', 'classroom').order_by('exam_date', 'start_time')
    
    context = {
        'student': student,
        'exam_schedules': exam_schedules,
        'current_semester': current_semester,
    }
    return render(request, 'student/exam_schedule.html', context)

@login_required
def student_exam_results(request):
    student = get_object_or_404(Student, user=request.user)
    
    # Get all exam results
    grades = Grade.objects.filter(
        enrollment__student=student
    ).select_related('enrollment__subject', 'enrollment__semester').order_by('-exam_date')
    
    # Group by examination type
    results_by_exam = {}
    for grade in grades:
        exam_type = grade.enrollment.semester.year  # You might want to adjust this based on your exam model
        if exam_type not in results_by_exam:
            results_by_exam[exam_type] = []
        results_by_exam[exam_type].append(grade)
    
    context = {
        'student': student,
        'results_by_exam': results_by_exam,
        'grades': grades,
    }
    return render(request, 'student/exam_results.html', context)

# Fee Management Views
@login_required
def student_fees(request):
    student = get_object_or_404(Student, user=request.user)
    
    # Get fee structure for student's course
    fee_structures = FeeStructure.objects.filter(
        course=student.course
    ).order_by('-academic_year__start_date', 'semester')
    
    # Get payment history
    payments = FeePayment.objects.filter(
        student=student
    ).order_by('-payment_date')
    
    # Calculate pending fees
    total_fees = sum(fs.total_fee() for fs in fee_structures)
    total_paid = sum(p.amount_paid for p in payments if p.payment_status == 'completed')
    pending_fees = total_fees - total_paid
    
    context = {
        'student': student,
        'fee_structures': fee_structures,
        'payments': payments,
        'total_fees': total_fees,
        'total_paid': total_paid,
        'pending_fees': pending_fees,
    }
    return render(request, 'student/fees.html', context)

# Library Views
@login_required
def student_library(request):
    student = get_object_or_404(Student, user=request.user)
    
    # Get issued books
    issued_books = BookIssue.objects.filter(
        student=student,
        is_returned=False
    ).select_related('book')
    
    # Get book history
    book_history = BookIssue.objects.filter(
        student=student
    ).select_related('book').order_by('-issue_date')
    
    # Get available books related to student's course
    available_books = Book.objects.filter(
        subject__course=student.course,
        available_copies__gt=0
    )
    
    # Calculate total fines
    total_fines = BookIssue.objects.filter(
        student=student,
        fine_amount__gt=0
    ).aggregate(total=Sum('fine_amount'))['total'] or 0
    
    context = {
        'student': student,
        'issued_books': issued_books,
        'book_history': book_history,
        'available_books': available_books,
        'total_fines': total_fines,
    }
    return render(request, 'student/library.html', context)

# Placement Views
@login_required
def student_placements(request):
    student = get_object_or_404(Student, user=request.user)
    
    # Get available placement drives
    available_drives = PlacementDrive.objects.filter(
        eligible_courses=student.course,
        is_active=True,
        registration_deadline__gte=timezone.now().date()
    ).select_related('company')
    
    # Get applied placements
    applied_placements = PlacementApplication.objects.filter(
        student=student
    ).select_related('placement_drive__company')
    
    context = {
        'student': student,
        'available_drives': available_drives,
        'applied_placements': applied_placements,
    }
    return render(request, 'student/placements.html', context)

@login_required
def apply_placement(request, drive_id):
    if request.method == 'POST':
        student = get_object_or_404(Student, user=request.user)
        drive = get_object_or_404(PlacementDrive, id=drive_id)
        
        # Check if already applied
        if PlacementApplication.objects.filter(student=student, placement_drive=drive).exists():
            messages.error(request, 'You have already applied for this placement drive')
        else:
            application = PlacementApplication.objects.create(
                student=student,
                placement_drive=drive,
                remarks=request.POST.get('remarks', '')
            )
            messages.success(request, 'Application submitted successfully')
        
        return redirect('student_placements')

# Event Views
@login_required
def student_events(request):
    student = get_object_or_404(Student, user=request.user)
    
    # Get upcoming events
    upcoming_events = Event.objects.filter(
        start_date__gte=timezone.now(),
        is_public=True
    ).order_by('start_date')
    
    # Get registered events
    registered_events = EventRegistration.objects.filter(
        user=request.user
    ).select_related('event')
    
    context = {
        'student': student,
        'upcoming_events': upcoming_events,
        'registered_events': registered_events,
    }
    return render(request, 'student/events.html', context)

@login_required
def register_event(request, event_id):
    if request.method == 'POST':
        event = get_object_or_404(Event, id=event_id)
        
        # Check if already registered
        if EventRegistration.objects.filter(user=request.user, event=event).exists():
            messages.error(request, 'You are already registered for this event')
        else:
            EventRegistration.objects.create(
                user=request.user,
                event=event
            )
            messages.success(request, 'Successfully registered for the event')
        
        return redirect('student_events')

# Document Views
@login_required
def student_documents(request):
    student = get_object_or_404(Student, user=request.user)
    
    # Get student documents
    documents = Document.objects.filter(
        student=student
    ).order_by('-upload_date')
    
    context = {
        'student': student,
        'documents': documents,
    }
    return render(request, 'student/documents.html', context)

# Notification Views
@login_required
def student_notifications(request):
    # Get all notifications for the user
    notifications = Notification.objects.filter(
        Q(target_users=request.user) | Q(is_global=True),
        is_active=True
    ).order_by('-created_at')
    
    # Mark notifications as read
    for notification in notifications:
        NotificationRead.objects.get_or_create(
            notification=notification,
            user=request.user
        )
    
    context = {
        'notifications': notifications,
    }
    return render(request, 'student/notifications.html', context)

# Change Password View
@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match')
        else:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, 'Password changed successfully')
            return redirect('student_login')
    
    return render(request, 'student/change_password.html')