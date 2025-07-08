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
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
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
    messages.success(request, "You have been logged out successfully.")
    return redirect('student_login')

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.utils import timezone
from .models import Student, Enrollment, Grade, Subject, Semester, AcademicYear

@login_required
def student_dashboard(request):
    student = get_object_or_404(Student, user=request.user)
    
    # Get current academic year
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Get enrolled subjects for student's current semester and year
    # Filter subjects based on student's current year and semester
    current_subjects = Subject.objects.filter(
        course=student.course,
        year=student.current_year,
        semester=student.current_semester,
        is_active=True
    )
    
    # Get current enrollments for the student's current semester
    current_enrollments = Enrollment.objects.filter(
        student=student,
        subject__in=current_subjects,
        is_active=True
    ).select_related('subject')
    
    # If no enrollments found, you might want to show available subjects for enrollment
    available_subjects = []
    if not current_enrollments.exists():
        available_subjects = current_subjects
    
    # Get recent grades
    recent_grades = Grade.objects.filter(
        enrollment__student=student
    ).select_related('enrollment__subject').order_by('-exam_date')[:5]
    
    # Get attendance summary (assuming you have an Attendance model)
    attendance_summary = []
    for enrollment in current_enrollments:
        # You'll need to uncomment these lines if you have an Attendance model
        # total_classes = Attendance.objects.filter(
        #     student=student,
        #     subject=enrollment.subject
        # ).count()
        
        # present_classes = Attendance.objects.filter(
        #     student=student,
        #     subject=enrollment.subject,
        #     status='present'
        # ).count()
        
        # attendance_percentage = (present_classes / total_classes * 100) if total_classes > 0 else 0
        
        attendance_summary.append({
            'subject': enrollment.subject,
            'total_classes': 0,  # Replace with actual count
            'present_classes': 0,  # Replace with actual count
            'attendance_percentage': 0  # Replace with actual percentage
        })
    
    # Get upcoming exams (assuming you have an ExamSchedule model)
    upcoming_exams = []
    # upcoming_exams = ExamSchedule.objects.filter(
    #     subject__in=[e.subject for e in current_enrollments],
    #     exam_date__gte=timezone.now().date()
    # ).order_by('exam_date')[:5]
    
    # Get pending fees (assuming you have a FeePayment model)
    pending_fees = 0
    # pending_fees = FeePayment.objects.filter(
    #     student=student,
    #     payment_status='pending'
    # ).aggregate(total=Sum('amount_paid'))['total'] or 0
    
    # Get recent notifications (assuming you have a Notification model)
    recent_notifications = []
    # recent_notifications = Notification.objects.filter(
    #     Q(target_users=request.user) | Q(is_global=True),
    #     is_active=True
    # ).order_by('-created_at')[:5]
    
    # Calculate overall progress
    total_subjects_in_course = Subject.objects.filter(
        course=student.course,
        is_active=True
    ).count()
    
    completed_subjects = Grade.objects.filter(
        enrollment__student=student,
        is_passed=True
    ).count()
    
    progress_percentage = (completed_subjects / total_subjects_in_course * 100) if total_subjects_in_course > 0 else 0
    
    # Calculate current semester progress
    current_semester_subjects = Subject.objects.filter(
        course=student.course,
        year=student.current_year,
        semester=student.current_semester,
        is_active=True
    ).count()
    
    current_semester_completed = Grade.objects.filter(
        enrollment__student=student,
        enrollment__subject__year=student.current_year,
        enrollment__subject__semester=student.current_semester,
        is_passed=True
    ).count()
    
    current_semester_progress = (current_semester_completed / current_semester_subjects * 100) if current_semester_subjects > 0 else 0
    
    # Format registrations for template compatibility
    registrations = []
    for enrollment in current_enrollments:
        registrations.append({
            'unit': {
                'name': enrollment.subject.name
            },
            'unitCode': {
                'code': enrollment.subject.code
            },
            'approved': enrollment.is_active  # Assuming active means approved
        })
    
    context = {
        'student': student,
        'current_academic_year': current_academic_year,
        'current_subjects': current_subjects,
        'current_enrollments': current_enrollments,
        'available_subjects': available_subjects,
        'recent_grades': recent_grades,
        'attendance_summary': attendance_summary,
        'upcoming_exams': upcoming_exams,
        'pending_fees': pending_fees,
        'recent_notifications': recent_notifications,
        'progress_percentage': progress_percentage,
        'total_subjects_in_course': total_subjects_in_course,
        'completed_subjects': completed_subjects,
        'registrations': registrations,
        'current_semester_progress': current_semester_progress,
        'current_semester_subjects': current_semester_subjects,
        'current_semester_completed': current_semester_completed,
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

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
import logging

# Set up logging to help debug
logger = logging.getLogger(__name__)

@login_required
def student_subjects(request):
    student = get_object_or_404(Student, user=request.user)
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Handle POST request for subject registration
    if request.method == 'POST':
        logger.info(f"POST request received for student: {student.user.username}")
        
        selected_subjects = request.POST.getlist('subjects')
        logger.info(f"Selected subjects: {selected_subjects}")
        
        if not selected_subjects:
            messages.error(request, 'Please select at least one subject to register.')
            logger.warning("No subjects selected")
            return redirect('student_subjects')
        
        if not current_semester:
            messages.error(request, 'No active semester found. Please contact administration.')
            logger.error("No active semester found")
            return redirect('student_subjects')
        
        try:
            with transaction.atomic():
                # Check if student already has enrollments for this semester
                existing_enrollments = Enrollment.objects.filter(
                    student=student,
                    semester=current_semester,
                    is_active=True
                )
                
                logger.info(f"Existing enrollments count: {existing_enrollments.count()}")
                
                if existing_enrollments.exists():
                    messages.error(request, 'You are already registered for subjects this semester.')
                    logger.warning("Student already has enrollments")
                    return redirect('student_subjects')
                
                # Get selected subjects and validate them
                subjects_to_register = Subject.objects.filter(
                    id__in=selected_subjects,
                    course=student.course,
                    is_active=True
                )
                
                logger.info(f"Valid subjects found: {subjects_to_register.count()}")
                logger.info(f"Subject IDs: {[s.id for s in subjects_to_register]}")
                
                if len(subjects_to_register) != len(selected_subjects):
                    messages.error(request, 'Some selected subjects are not valid for registration.')
                    logger.error("Mismatch between selected and valid subjects")
                    return redirect('student_subjects')
                
                # Check prerequisites for each subject
                for subject in subjects_to_register:
                    logger.info(f"Checking prerequisites for subject: {subject.code}")
                    if subject.prerequisites.exists():
                        for prereq in subject.prerequisites.all():
                            prereq_enrollment = Enrollment.objects.filter(
                                student=student,
                                subject=prereq,
                                is_active=True
                            ).first()
                            
                            if not prereq_enrollment:
                                error_msg = f'You must complete {prereq.code} - {prereq.name} before registering for {subject.code}.'
                                messages.error(request, error_msg)
                                logger.error(f"Prerequisite not met: {prereq.code} for {subject.code}")
                                return redirect('student_subjects')
                
                # Create enrollments for selected subjects
                enrollments_created = []
                for subject in subjects_to_register:
                    logger.info(f"Creating enrollment for subject: {subject.code}")
                    
                    # Check if enrollment already exists (double check)
                    existing = Enrollment.objects.filter(
                        student=student,
                        subject=subject,
                        semester=current_semester
                    ).first()
                    
                    if existing:
                        logger.warning(f"Enrollment already exists for {subject.code}")
                        # Update existing enrollment to active
                        existing.is_active = True
                        existing.enrollment_date = timezone.now().date()
                        existing.save()
                        enrollments_created.append(existing)
                    else:
                        # Create new enrollment
                        enrollment = Enrollment.objects.create(
                            student=student,
                            subject=subject,
                            semester=current_semester,
                            enrollment_date=timezone.now().date(),
                            is_active=True
                        )
                        enrollments_created.append(enrollment)
                        logger.info(f"Created enrollment with ID: {enrollment.id}")
                
                logger.info(f"Total enrollments created: {len(enrollments_created)}")
                
                messages.success(
                    request, 
                    f'Successfully registered for {len(enrollments_created)} subjects.'
                )
                
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            messages.error(request, f'An error occurred during registration: {str(e)}')
            return redirect('student_subjects')
        
        return redirect('student_subjects')
    
    # GET request handling
    logger.info(f"GET request for student: {student.user.username}")
    
    # Get all enrollments grouped by year and semester
    all_enrollments = Enrollment.objects.filter(
        student=student,
        is_active=True
    ).select_related('subject', 'semester').order_by('subject__year', 'subject__semester')
    
    # Organize enrollments by year and semester
    enrollment_groups = {}
    for enrollment in all_enrollments:
        year = enrollment.subject.year
        semester = enrollment.subject.semester
        if year not in enrollment_groups:
            enrollment_groups[year] = {}
        if semester not in enrollment_groups[year]:
            enrollment_groups[year][semester] = []
        enrollment_groups[year][semester].append(enrollment)
    
    # Get available subjects for current year and semester if no enrollments for current semester
    available_subjects = []
    show_registration = False
    
    if current_semester:
        # Check if student has enrollments for current semester
        current_semester_enrollments = all_enrollments.filter(semester=current_semester)
        
        if not current_semester_enrollments.exists():
            available_subjects = Subject.objects.filter(
                course=student.course,
                year=student.current_year,
                semester=student.current_semester,
                is_active=True
            ).select_related('course').prefetch_related('prerequisites')
            
            show_registration = True
            logger.info(f"Available subjects for registration: {available_subjects.count()}")
        else:
            logger.info("Student already has enrollments for current semester")
    
    # Get curriculum structure - all subjects organized by year and semester
    curriculum = {}
    all_subjects = Subject.objects.filter(
        course=student.course,
        is_active=True
    ).order_by('year', 'semester')
    
    for subject in all_subjects:
        year = subject.year
        semester = subject.semester
        if year not in curriculum:
            curriculum[year] = {}
        if semester not in curriculum[year]:
            curriculum[year][semester] = []
        curriculum[year][semester].append(subject)
    
    logger.info(f"Show registration: {show_registration}")
    logger.info(f"Available subjects count: {len(available_subjects)}")
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'enrollment_groups': enrollment_groups,
        'available_subjects': available_subjects,
        'show_registration': show_registration,
        'curriculum': curriculum,
    }
    return render(request, 'student/subjects.html', context)

# views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import Student, Schedule, Subject, TimeSlot, Semester, AcademicYear
from collections import defaultdict
from datetime import datetime, time

@login_required
def student_timetable(request):
    """
    Generate timetable for the logged-in student based on their current year and semester
    """
    try:
        # Get the student profile for the logged-in user
        student = get_object_or_404(Student, user=request.user)
        
        # Get current academic year and semester
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        current_semester = Semester.objects.filter(
            academic_year=current_academic_year,
            is_current=True
        ).first()
        
        if not current_semester:
            return render(request, 'timetable/error.html', {
                'error_message': 'No current semester found. Please contact administration.'
            })
        
        # Get subjects for the student's current year and semester
        subjects = Subject.objects.filter(
            course=student.course,
            year=student.current_year,
            semester=student.current_semester,
            is_active=True
        )
        
        # Get schedules for these subjects in the current semester
        schedules = Schedule.objects.filter(
            subject__in=subjects,
            semester=current_semester,
            is_active=True
        ).select_related(
            'subject', 'faculty', 'classroom', 'time_slot'
        ).order_by('time_slot__day_of_week', 'time_slot__start_time')
        
        # Create a grid-based timetable
        timetable_grid = create_timetable_grid(schedules)
        
        context = {
            'student': student,
            'current_semester': current_semester,
            'timetable_grid': timetable_grid,
            'subjects': subjects,
            'total_subjects': subjects.count(),
        }
        
        return render(request, 'student/timetable.html', context)
        
    except Student.DoesNotExist:
        return render(request, 'timetable/error.html', {
            'error_message': 'Student profile not found. Please contact administration.'
        })

def create_timetable_grid(schedules):
    """
    Create a grid-based timetable structure
    """
    # Define days and time slots
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    # Get all unique time slots from schedules
    time_slots = set()
    for schedule in schedules:
        time_slots.add((schedule.time_slot.start_time, schedule.time_slot.end_time))
    
    # Sort time slots by start time
    time_slots = sorted(list(time_slots))
    
    # Create a dictionary to store schedule data by day and time
    schedule_dict = {}
    for schedule in schedules:
        day = schedule.time_slot.day_of_week
        time_key = (schedule.time_slot.start_time, schedule.time_slot.end_time)
        
        if day not in schedule_dict:
            schedule_dict[day] = {}
        
        schedule_dict[day][time_key] = {
            'subject': schedule.subject,
            'faculty': schedule.faculty,
            'classroom': schedule.classroom,
        }
    
    # Build the grid
    grid = {
        'days': day_names,
        'time_slots': time_slots,
        'schedule_dict': schedule_dict,
        'cells': []
    }
    
    # Create cells for each time slot and day combination
    for time_slot in time_slots:
        row = {
            'time_slot': time_slot,
            'time_display': f"{time_slot[0].strftime('%H:%M')} - {time_slot[1].strftime('%H:%M')}",
            'days_data': []
        }
        
        for day in days:
            cell_data = schedule_dict.get(day, {}).get(time_slot, None)
            row['days_data'].append(cell_data)
        
        grid['cells'].append(row)
    
    return grid

@login_required
def timetable_by_course_year_semester(request):
    """
    Generate timetable for a specific course, year, and semester
    Accessible by faculty and admin
    """
    if request.user.user_type not in ['faculty', 'admin']:
        return render(request, 'timetable/error.html', {
            'error_message': 'You do not have permission to access this page.'
        })
    
    course_id = request.GET.get('course')
    year = request.GET.get('year')
    semester_num = request.GET.get('semester')
    
    if not all([course_id, year, semester_num]):
        return render(request, 'timetable/course_timetable_form.html')
    
    try:
        year = int(year)
        semester_num = int(semester_num)
        
        # Get current academic year and semester
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        current_semester = Semester.objects.filter(
            academic_year=current_academic_year,
            is_current=True
        ).first()
        
        # Get subjects for the specified course, year, and semester
        subjects = Subject.objects.filter(
            course_id=course_id,
            year=year,
            semester=semester_num,
            is_active=True
        )
        
        # Get schedules for these subjects
        schedules = Schedule.objects.filter(
            subject__in=subjects,
            semester=current_semester,
            is_active=True
        ).select_related(
            'subject', 'faculty', 'classroom', 'time_slot'
        ).order_by('time_slot__day_of_week', 'time_slot__start_time')
        
        # Create grid-based timetable
        timetable_grid = create_timetable_grid(schedules)
        
        context = {
            'timetable_grid': timetable_grid,
            'course': subjects.first().course if subjects.exists() else None,
            'year': year,
            'semester': semester_num,
            'current_semester': current_semester,
            'subjects': subjects,
            'total_subjects': subjects.count(),
        }
        
        return render(request, 'timetable/course_timetable.html', context)
        
    except (ValueError, TypeError):
        return render(request, 'timetable/error.html', {
            'error_message': 'Invalid parameters provided.'
        })

@login_required
def get_timetable_json(request):
    """
    API endpoint to get timetable data as JSON
    """
    try:
        student = get_object_or_404(Student, user=request.user)
        
        # Get current semester
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        current_semester = Semester.objects.filter(
            academic_year=current_academic_year,
            is_current=True
        ).first()
        
        if not current_semester:
            return JsonResponse({'error': 'No current semester found'}, status=400)
        
        # Get subjects and schedules
        subjects = Subject.objects.filter(
            course=student.course,
            year=student.current_year,
            semester=student.current_semester,
            is_active=True
        )
        
        schedules = Schedule.objects.filter(
            subject__in=subjects,
            semester=current_semester,
            is_active=True
        ).select_related('subject', 'faculty', 'classroom', 'time_slot')
        
        # Format data for JSON response
        timetable_data = []
        for schedule in schedules:
            timetable_data.append({
                'day': schedule.time_slot.day_of_week,
                'start_time': schedule.time_slot.start_time.strftime('%H:%M'),
                'end_time': schedule.time_slot.end_time.strftime('%H:%M'),
                'subject_name': schedule.subject.name,
                'subject_code': schedule.subject.code,
                'faculty_name': schedule.faculty.user.get_full_name(),
                'classroom': schedule.classroom.name,
                'room_number': schedule.classroom.room_number,
            })
        
        return JsonResponse({
            'student_id': student.student_id,
            'course': student.course.name,
            'year': student.current_year,
            'semester': student.current_semester,
            'timetable': timetable_data
        })
        
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
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


from .models import Student, StudentComment
from .forms import StudentCommentForm

@login_required
def student_comments(request):
    student = get_object_or_404(Student, user=request.user)
    
    if request.method == 'POST':
        form = StudentCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.student = student
            comment.save()
            messages.success(request, 'Your comment has been submitted successfully!')
            return redirect('student_comments')
    else:
        form = StudentCommentForm()
    
    comments = StudentComment.objects.filter(student=student).order_by('-created_at')
    
    context = {
        'student': student,
        'form': form,
        'comments': comments,
    }
    return render(request, 'comments/comments.html', context)

@login_required
def faqs(request): 
    return render(request, 'settings/faqs.html')



from django.views.decorators.http import require_POST
import json
from .models import CommonQuestion, QuickLink

@login_required
def virtual_assistant(request):
    # Get the current user
    user = request.user
    
    # Fetch data from database models
    common_questions = CommonQuestion.objects.all()
    quick_links = QuickLink.objects.all()
    
    # Prepare context
    context = {
        'user': user,
        'common_questions': common_questions,
        'quick_links': quick_links,
    }
    
    return render(request, 'assistant/virtual_assistant.html', context)

@login_required
@require_POST
def process_assistant_query(request):
    try:
        data = json.loads(request.body)
        query = data.get('query', '').lower()
        
        # Simple response logic - would normally integrate with NLP/AI
        responses = {
            'results': 'Exam results are available on the student portal under "Academic Records".',
            'lecture': 'Lecture materials can be found on the LMS or by contacting your lecturer.',
            'hostel': 'Hostel applications open twice a year. Check the accommodation office for dates.',
            'fee': 'Fee payment can be made via MPesa or bank deposit. See the finance office for details.',
            'library': 'The library is open from 8am to 9pm weekdays, 9am to 4pm weekends.',
            'default': "I'm sorry, I didn't understand that. Could you rephrase your question?"
        }
        
        response_text = responses['default']
        for keyword in responses:
            if keyword in query and keyword != 'default':
                response_text = responses[keyword]
                break
        
        return JsonResponse({'response': response_text})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    


@login_required
def student_clubs(request):
    clubs = StudentClub.objects.filter(is_active=True).order_by('name')
    user_memberships = ClubMembership.objects.filter(student=request.user, is_active=True)
    
    # Create a dictionary to hold executive members for each club
    club_executives = {}
    for club in clubs:
        club_executives[club.id] = club.members.filter(is_executive=True)
    
    context = {
        'clubs': clubs,
        'user_memberships': user_memberships,
        'categories': dict(StudentClub.CATEGORY_CHOICES),
        'club_executives': club_executives
    }
    return render(request, 'clubs/student_clubs.html', context)


@login_required
def join_club(request, club_id):
    club = StudentClub.objects.get(id=club_id)
    if not ClubMembership.objects.filter(student=request.user, club=club).exists():
        ClubMembership.objects.create(student=request.user, club=club)
    return redirect('student_clubs')

@login_required
def leave_club(request, club_id):
    membership = ClubMembership.objects.filter(student=request.user, club_id=club_id).first()
    if membership:
        membership.delete()
    return redirect('student_clubs')


@login_required
def club_events(request, club_id=None):
    now = timezone.now()
    
    # Get events based on club_id or all clubs
    if club_id:
        club = StudentClub.objects.get(id=club_id)
        events = ClubEvent.objects.filter(club=club)
    else:
        club = None
        events = ClubEvent.objects.all()
    
    # Categorize events
    upcoming_events = events.filter(start_datetime__gt=now).order_by('start_datetime')
    latest_events = events.filter(start_datetime__lte=now, end_datetime__gte=now).order_by('start_datetime')
    past_events = events.filter(end_datetime__lt=now).order_by('-start_datetime')[:10]  # Last 10 past events
    
    context = {
        'club': club,
        'upcoming_events': upcoming_events,
        'latest_events': latest_events,
        'past_events': past_events,
    }
    
    return render(request, 'events/club_events.html', context)


@login_required
def student_news(request):
    # Get all news articles, ordered by most recent first
    news_articles = NewsArticle.objects.filter(is_published=True).order_by('-publish_date')
    
    context = {
        'news_articles': news_articles,
        'featured_article': news_articles.first() if news_articles.exists() else None,
        'regular_articles': news_articles[1:4] if news_articles.count() > 1 else [],
        'older_articles': news_articles[4:] if news_articles.count() > 4 else []
    }
    return render(request, 'news/student_news.html', context)


# views.py - Add these views to your existing views.py file

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from .models import (
    Student, StudentReport, Hostel, HostelRoom, HostelBooking, 
    HostelFeeStructure, AcademicYear, Semester
)
from .forms import StudentReportForm  # You'll need to create these forms


# Student Reporting Views
@login_required
def student_reporting_dashboard(request):
    """View for student to see their reports and create new ones"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can access this page.")
        return redirect('home')
    
    student = request.user.student_profile
    
    # Get current semester
    current_semester = Semester.objects.filter(
        is_current=True,
        academic_year__is_current=True
    ).first()
    
    if not current_semester:
        messages.error(request, "No active semester found.")
        return redirect('home')
    
    # Get student's reports for current semester
    reports = StudentReport.objects.filter(
        student=student,
        semester=current_semester
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'reports': page_obj,
        'total_reports': reports.count(),
        'pending_reports': reports.filter(status='pending').count(),
        'resolved_reports': reports.filter(status='resolved').count(),
    }
    
    return render(request, 'student_reporting/dashboard.html', context)


@login_required
def create_student_report(request):
    """View for creating a new student report"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can access this page.")
        return redirect('home')
    
    student = request.user.student_profile
    
    # Get current semester
    current_semester = Semester.objects.filter(
        is_current=True,
        academic_year__is_current=True
    ).first()
    
    if not current_semester:
        messages.error(request, "No active semester found.")
        return redirect('student_reporting_dashboard')
    
    if request.method == 'POST':
        form = StudentReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.student = student
            report.semester = current_semester
            report.save()
            messages.success(request, "Your report has been submitted successfully.")
            return redirect('student_reporting_dashboard')
    else:
        form = StudentReportForm()
    
    context = {
        'form': form,
        'student': student,
        'current_semester': current_semester,
    }
    
    return render(request, 'student_reporting/create_report.html', context)


@login_required
def report_detail(request, report_id):
    """View for viewing a specific report"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can access this page.")
        return redirect('home')
    
    student = request.user.student_profile
    report = get_object_or_404(StudentReport, id=report_id, student=student)
    
    context = {
        'report': report,
        'student': student,
    }
    
    return render(request, 'student_reporting/report_detail.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .models import (
    Hostel, HostelRoom, HostelBed, HostelBooking, 
    HostelFeeStructure, AcademicYear
)
from .forms import HostelBookingForm


@login_required
def hostel_booking_dashboard(request):
    """Main dashboard for hostel booking"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can access this page.")
        return redirect('home')
    
    student = request.user.student_profile
    
    # Check if student is eligible (Year 1, Semester 1)
    eligible = student.current_year == 1 and student.current_semester == 1
    
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Get student's current booking
    current_booking = None
    if current_academic_year:
        current_booking = HostelBooking.objects.filter(
            student=student,
            academic_year=current_academic_year
        ).first()
    
    # Get available hostels based on student's gender
    student_gender = getattr(student.user, 'gender', None)
    available_hostels = []
    
    if student_gender == 'male':
        available_hostels = Hostel.objects.filter(hostel_type='boys', is_active=True)
    elif student_gender == 'female':
        available_hostels = Hostel.objects.filter(hostel_type='girls', is_active=True)
    
    context = {
        'student': student,
        'eligible': eligible,
        'current_booking': current_booking,
        'available_hostels': available_hostels,
        'current_academic_year': current_academic_year,
    }
    
    return render(request, 'hostel/dashboard.html', context)


@login_required
def hostel_list(request):
    """View to display all available hostels"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can access this page.")
        return redirect('home')
    
    student = request.user.student_profile
    student_gender = getattr(student.user, 'gender', None)
    
    # Filter hostels based on gender
    if student_gender == 'male':
        hostels = Hostel.objects.filter(hostel_type='boys', is_active=True)
    elif student_gender == 'female':
        hostels = Hostel.objects.filter(hostel_type='girls', is_active=True)
    else:
        hostels = Hostel.objects.none()
    
    context = {
        'hostels': hostels,
        'student': student,
    }
    
    return render(request, 'hostel/hostel_list.html', context)


@login_required
def hostel_detail(request, hostel_id):
    """View to display hostel details and available rooms"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can access this page.")
        return redirect('home')
    
    student = request.user.student_profile
    hostel = get_object_or_404(Hostel, id=hostel_id, is_active=True)
    
    # Check if student can access this hostel
    student_gender = getattr(student.user, 'gender', None)
    if ((hostel.hostel_type == 'boys' and student_gender != 'male') or 
        (hostel.hostel_type == 'girls' and student_gender != 'female')):
        messages.error(request, "You cannot access this hostel.")
        return redirect('hostel_list')
    
    # Get available rooms
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    rooms = hostel.rooms.filter(is_available=True)
    
    # Calculate bed availability for each room
    room_availability = []
    for room in rooms:
        room_info = {
            'room': room,
            'available_beds': room.available_beds,
            'occupied_beds': room.occupied_beds,
            'beds': room.beds.all().order_by('bed_number')
        }
        room_availability.append(room_info)
    
    # Get fee structure
    fee_structure = None
    if current_academic_year:
        fee_structure = HostelFeeStructure.objects.filter(
            hostel=hostel,
            academic_year=current_academic_year
        ).first()
    
    context = {
        'hostel': hostel,
        'room_availability': room_availability,
        'fee_structure': fee_structure,
        'student': student,
    }
    
    return render(request, 'hostel/hostel_detail.html', context)


@login_required
def room_detail(request, room_id):
    """View to display room details and available beds"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can access this page.")
        return redirect('home')
    
    student = request.user.student_profile
    room = get_object_or_404(HostelRoom, id=room_id, is_available=True)
    
    # Check if student can access this room
    student_gender = getattr(student.user, 'gender', None)
    if ((room.hostel.hostel_type == 'boys' and student_gender != 'male') or 
        (room.hostel.hostel_type == 'girls' and student_gender != 'female')):
        messages.error(request, "You cannot access this room.")
        return redirect('hostel_list')
    
    # Get bed details with availability
    beds = room.beds.all().order_by('bed_number')
    bed_details = []
    
    for bed in beds:
        bed_info = {
            'bed': bed,
            'is_available': bed.is_available,
            'current_occupant': bed.current_occupant,
            'can_book': bed.can_be_booked(student)[0] if bed.is_available else False
        }
        bed_details.append(bed_info)
    
    context = {
        'room': room,
        'bed_details': bed_details,
        'student': student,
    }
    
    return render(request, 'hostel/room_detail.html', context)


@login_required
def apply_hostel_booking(request, bed_id):
    """View for applying for hostel booking for a specific bed"""
    
    # Check if user has student profile
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can access this page.")
        return redirect('home')
    
    student = request.user.student_profile
    bed = get_object_or_404(HostelBed, id=bed_id)
    
    # Check eligibility
    if student.current_year != 1 or student.current_semester != 1:
        messages.error(request, "Only first-year, first-semester students can apply for hostel.")
        return redirect('hostel_list')
    
    # Check if bed can be booked
    can_book, message = bed.can_be_booked(student)
    if not can_book:
        messages.error(request, message)
        return redirect('room_detail', room_id=bed.room.id)
    
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    if not current_academic_year:
        messages.error(request, "No current academic year is set. Please contact administration.")
        return redirect('hostel_list')
    
    # Check if student already has a booking
    existing_booking = HostelBooking.objects.filter(
        student=student,
        academic_year=current_academic_year
    ).first()
    
    if existing_booking:
        messages.error(request, "You already have a hostel booking for this academic year.")
        return redirect('hostel_booking_dashboard')
    
    if request.method == 'POST':
        form = HostelBookingForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create booking object manually with all required fields
                    booking = HostelBooking(
                        student=student,
                        bed=bed,
                        academic_year=current_academic_year,
                        emergency_contact=form.cleaned_data['emergency_contact'],
                        medical_info=form.cleaned_data.get('medical_info', ''),
                        status='pending',
                        is_active=True
                    )
                    
                    # Now validate and save
                    booking.full_clean()
                    booking.save()
                    
                    # Mark bed as occupied
                    bed.is_available = False
                    bed.save()
                    
                    messages.success(request, f"Your hostel booking application for bed {bed.bed_name} has been submitted successfully.")
                    return redirect('hostel_booking_dashboard')
                    
            except ValidationError as e:
                if hasattr(e, 'message_dict'):
                    for field, errors in e.message_dict.items():
                        for error in errors:
                            messages.error(request, f"{field}: {error}")
                else:
                    messages.error(request, f"Validation error: {str(e)}")
            except Exception as e:
                messages.error(request, f"Error submitting application: {str(e)}")
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = HostelBookingForm()
    
    # Get fee structure
    fee_structure = HostelFeeStructure.objects.filter(
        hostel=bed.room.hostel,
        academic_year=current_academic_year
    ).first()
    
    context = {
        'form': form,
        'bed': bed,
        'room': bed.room,
        'hostel': bed.room.hostel,
        'fee_structure': fee_structure,
        'student': student,
    }
    
    return render(request, 'hostel/apply_booking.html', context)


@login_required
def get_room_beds(request, room_id):
    """AJAX view to get available beds for a room"""
    if not hasattr(request.user, 'student_profile'):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    student = request.user.student_profile
    room = get_object_or_404(HostelRoom, id=room_id)
    
    # Check if student can access this room
    student_gender = getattr(student.user, 'gender', None)
    if ((room.hostel.hostel_type == 'boys' and student_gender != 'male') or 
        (room.hostel.hostel_type == 'girls' and student_gender != 'female')):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    beds = room.beds.all().order_by('bed_number')
    bed_data = []
    
    for bed in beds:
        can_book, message = bed.can_be_booked(student)
        bed_info = {
            'id': bed.id,
            'bed_number': bed.bed_number,
            'bed_name': bed.bed_name,
            'is_available': bed.is_available,
            'is_maintenance': bed.is_maintenance,
            'bed_type': bed.bed_type,
            'facilities': bed.facilities,
            'can_book': can_book,
            'message': message,
            'current_occupant': bed.current_occupant.user.get_full_name() if bed.current_occupant else None
        }
        bed_data.append(bed_info)
    
    return JsonResponse({'beds': bed_data})


@login_required
def booking_history(request):
    """View to display student's booking history"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can access this page.")
        return redirect('home')
    
    student = request.user.student_profile
    
    bookings = HostelBooking.objects.filter(student=student).order_by('-booking_date')
    
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'bookings': page_obj,
        'student': student,
    }
    
    return render(request, 'hostel/booking_history.html', context)


@login_required
@require_http_methods(["POST"])
def cancel_booking(request, booking_id):
    """View to cancel a hostel booking"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can access this page.")
        return redirect('home')
    
    student = request.user.student_profile
    booking = get_object_or_404(HostelBooking, id=booking_id, student=student)
    
    if booking.status in ['approved', 'pending']:
        booking.status = 'cancelled'
        booking.is_active = False
        booking.save()
        messages.success(request, "Your booking has been cancelled successfully.")
    else:
        messages.error(request, "This booking cannot be cancelled.")
    
    return redirect('hostel_booking_dashboard')


# Quick booking view for direct bed selection
@login_required
def quick_bed_booking(request):
    """View for quick bed booking with filters"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can access this page.")
        return redirect('home')
    
    student = request.user.student_profile
    
    # Check eligibility
    if student.current_year != 1 or student.current_semester != 1:
        messages.error(request, "Only first-year, first-semester students can apply for hostel.")
        return redirect('hostel_list')
    
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Check if student already has a booking
    existing_booking = HostelBooking.objects.filter(
        student=student,
        academic_year=current_academic_year
    ).first()
    
    if existing_booking:
        messages.error(request, "You already have a hostel booking for this academic year.")
        return redirect('hostel_booking_dashboard')
    
    # Get available beds for student
    from .models import get_available_beds_for_student
    available_beds = get_available_beds_for_student(student, current_academic_year)
    
    # Apply filters
    hostel_filter = request.GET.get('hostel')
    room_filter = request.GET.get('room')
    bed_type_filter = request.GET.get('bed_type')
    floor_filter = request.GET.get('floor')
    
    if hostel_filter:
        available_beds = available_beds.filter(room__hostel_id=hostel_filter)
    
    if room_filter:
        available_beds = available_beds.filter(room_id=room_filter)
    
    if bed_type_filter:
        available_beds = available_beds.filter(bed_type=bed_type_filter)
    
    if floor_filter:
        available_beds = available_beds.filter(room__floor=floor_filter)
    
    # Get filter options
    student_gender = getattr(student.user, 'gender', None)
    if student_gender == 'male':
        hostels = Hostel.objects.filter(hostel_type='boys', is_active=True)
    elif student_gender == 'female':
        hostels = Hostel.objects.filter(hostel_type='girls', is_active=True)
    else:
        hostels = Hostel.objects.none()
    
    bed_types = HostelBed.objects.values_list('bed_type', flat=True).distinct()
    floors = HostelRoom.objects.values_list('floor', flat=True).distinct().order_by('floor')
    
    # Pagination
    paginator = Paginator(available_beds, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'available_beds': page_obj,
        'hostels': hostels,
        'bed_types': bed_types,
        'floors': floors,
        'student': student,
        'filters': {
            'hostel': hostel_filter,
            'room': room_filter,
            'bed_type': bed_type_filter,
            'floor': floor_filter,
        }
    }
    
    return render(request, 'hostel/quick_bed_booking.html', context)


# Admin Views
@login_required
def admin_hostel_bookings(request):
    """Admin view to manage hostel bookings"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    bookings = HostelBooking.objects.all().order_by('-booking_date')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    # Filter by hostel
    hostel_filter = request.GET.get('hostel')
    if hostel_filter:
        bookings = bookings.filter(bed__room__hostel_id=hostel_filter)
    
    # Filter by room
    room_filter = request.GET.get('room')
    if room_filter:
        bookings = bookings.filter(bed__room_id=room_filter)
    
    # Search
    search = request.GET.get('search')
    if search:
        bookings = bookings.filter(
            Q(student__student_id__icontains=search) |
            Q(student__user__first_name__icontains=search) |
            Q(student__user__last_name__icontains=search) |
            Q(bed__bed_name__icontains=search)
        )
    
    paginator = Paginator(bookings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    hostels = Hostel.objects.filter(is_active=True)
    
    context = {
        'bookings': page_obj,
        'hostels': hostels,
        'status_filter': status_filter,
        'hostel_filter': hostel_filter,
        'room_filter': room_filter,
        'search': search,
    }
    
    return render(request, 'admin/hostel_bookings.html', context)


@login_required
@require_http_methods(["POST"])
def admin_approve_booking(request, booking_id):
    """Admin view to approve a hostel booking"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    booking = get_object_or_404(HostelBooking, id=booking_id)
    
    if booking.status == 'pending':
        booking.status = 'approved'
        booking.approved_by = request.user
        booking.save()
        messages.success(request, f"Booking for {booking.student.student_id} has been approved.")
    else:
        messages.error(request, "This booking cannot be approved.")
    
    return redirect('admin_hostel_bookings')


@login_required
@require_http_methods(["POST"])
def admin_reject_booking(request, booking_id):
    """Admin view to reject a hostel booking"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    booking = get_object_or_404(HostelBooking, id=booking_id)
    rejection_reason = request.POST.get('rejection_reason', '')
    
    if booking.status == 'pending':
        booking.status = 'rejected'
        booking.rejection_reason = rejection_reason
        booking.save()
        messages.success(request, f"Booking for {booking.student.student_id} has been rejected.")
    else:
        messages.error(request, "This booking cannot be rejected.")
    
    return redirect('admin_hostel_bookings')