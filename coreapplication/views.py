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
    current_semester = Semester.objects.filter(is_current=True).first()
    
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

    # Get hostel booking information
    current_hostel_booking = HostelBooking.objects.filter(
        student=student,
        is_active=True,
        status='approved',
        academic_year=current_academic_year
    ).select_related('bed__room__hostel').first()
    
    # Calculate current semester fee balance
    current_semester_fee_balance = 0
    current_semester_fee_status = 'no_structure'
    
    if current_academic_year and current_semester:
        try:
            # Get fee structure for current semester
            current_fee_structure = FeeStructure.objects.get(
                course=student.course,
                academic_year=current_academic_year,
                semester=current_semester.semester_number
            )
            
            # Get total fee for current semester
            total_current_fee = current_fee_structure.total_fee()
            
            # Get payments made for current semester
            current_semester_payments = FeePayment.objects.filter(
                student=student,
                fee_structure=current_fee_structure,
                payment_status='completed'
            ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
            
            # Calculate balance for current semester
            current_semester_fee_balance = total_current_fee - current_semester_payments
            
            # Determine status
            if current_semester_fee_balance > 0:
                current_semester_fee_status = 'pending'
            elif current_semester_fee_balance < 0:
                current_semester_fee_status = 'overpaid'
            else:
                current_semester_fee_status = 'paid'
                
        except FeeStructure.DoesNotExist:
            current_semester_fee_balance = 0
            current_semester_fee_status = 'no_structure'
    
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
        'current_semester': current_semester,
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
        'hostel_booking': current_hostel_booking,
        'current_semester_fee_balance': current_semester_fee_balance,
        'current_semester_fee_status': current_semester_fee_status,
    }
    
    return render(request, 'student/dashboard.html', context)

# Profile Views
@login_required
def student_profile(request):
    student = get_object_or_404(Student, user=request.user)
    
    if request.method == 'POST':
        # Handle profile update
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.address = request.POST.get('address', user.address)
        user.save()
        
        # Get or use existing values for required fields
        student.guardian_name = request.POST.get('guardian_name', student.guardian_name)
        student.guardian_phone = request.POST.get('guardian_phone', student.guardian_phone)
        student.guardian_relation = request.POST.get('guardian_relation', student.guardian_relation)
        student.emergency_contact = request.POST.get('emergency_contact', student.emergency_contact)
        student.blood_group = request.POST.get('blood_group', student.blood_group)
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
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from decimal import Decimal
from .models import Student, FeeStructure, FeePayment, AcademicYear, Semester

@login_required
def student_fees(request):
    student = get_object_or_404(Student, user=request.user)
    
    # Get current academic year and semester
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get all fee structures for student's course ordered by academic year and semester
    fee_structures = FeeStructure.objects.filter(
        course=student.course
    ).order_by('academic_year__start_date', 'semester')
    
    # Get all payments for this student
    payments = FeePayment.objects.filter(
        student=student,
        payment_status='completed'
    ).order_by('-payment_date')
    
    # Calculate semester-wise fee details
    semester_fee_details = []
    running_balance = Decimal('0.00')
    
    for fee_structure in fee_structures:
        # Get payments for this specific semester
        semester_payments = payments.filter(
            fee_structure=fee_structure
        )
        
        total_fee = fee_structure.total_fee()
        total_paid = semester_payments.aggregate(
            total=Sum('amount_paid')
        )['total'] or Decimal('0.00')
        
        # Calculate balance for this semester (including carry forward)
        semester_balance = total_fee - total_paid + running_balance
        
        # Update running balance for next semester
        if semester_balance < 0:
            running_balance = semester_balance
        else:
            running_balance = Decimal('0.00')
        
        semester_fee_details.append({
            'fee_structure': fee_structure,
            'total_fee': total_fee,
            'total_paid': total_paid,
            'semester_balance': semester_balance,
            'carry_forward': running_balance if semester_balance < 0 else Decimal('0.00'),
            'payments': semester_payments,
            'is_current': (current_academic_year and current_semester and 
                          fee_structure.academic_year == current_academic_year and 
                          fee_structure.semester == current_semester.semester_number)
        })
    
    # Calculate overall totals
    total_fees = sum(detail['total_fee'] for detail in semester_fee_details)
    total_paid = sum(detail['total_paid'] for detail in semester_fee_details)
    overall_balance = total_fees - total_paid
    
    # Get current semester details if exists
    current_semester_details = None
    if current_academic_year and current_semester:
        current_fee_structure = FeeStructure.objects.filter(
            course=student.course,
            academic_year=current_academic_year,
            semester=current_semester.semester_number
        ).first()
        
        if current_fee_structure:
            current_semester_details = next(
                (detail for detail in semester_fee_details 
                 if detail['fee_structure'] == current_fee_structure), 
                None
            )
    
    # Get recent payment history (last 10 payments)
    recent_payments = FeePayment.objects.filter(
        student=student
    ).order_by('-payment_date')[:10]
    
    context = {
        'student': student,
        'semester_fee_details': semester_fee_details,
        'recent_payments': recent_payments,
        'total_fees': total_fees,
        'total_paid': total_paid,
        'overall_balance': overall_balance,
        'current_semester_details': current_semester_details,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
    }
    return render(request, 'student/fees.html', context)

@login_required
def fee_payment_history(request):
    student = get_object_or_404(Student, user=request.user)
    
    # Get all payments with related fee structure details
    payments = FeePayment.objects.filter(
        student=student
    ).select_related('fee_structure__course', 'fee_structure__academic_year').order_by('-payment_date')
    
    # Group payments by academic year and semester
    payment_groups = {}
    for payment in payments:
        key = f"{payment.fee_structure.academic_year.year}-{payment.fee_structure.semester}"
        if key not in payment_groups:
            payment_groups[key] = {
                'academic_year': payment.fee_structure.academic_year,
                'semester': payment.fee_structure.semester,
                'payments': []
            }
        payment_groups[key]['payments'].append(payment)
    
    context = {
        'student': student,
        'payment_groups': payment_groups,
        'payments': payments,
    }
    return render(request, 'student/payment_history.html', context)


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
    Student,  Hostel, HostelRoom, HostelBooking, 
    HostelFeeStructure, AcademicYear, Semester
)


# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from .models import Student, Semester, AcademicYear, StudentReporting

@login_required
def student_reporting_list(request):
    """View to display all reporting records for the current student"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "You must be a student to access this page.")
        return redirect('home')
    
    student = request.user.student_profile
    reports = StudentReporting.objects.filter(student=student).order_by('-reported_date')
    
    # Get current semester for reporting button
    current_semester = Semester.objects.filter(is_current=True).first()
    can_report = False
    
    if current_semester:
        # Check if student has already reported for current semester
        existing_report = StudentReporting.objects.filter(
            student=student, 
            semester=current_semester
        ).exists()
        can_report = not existing_report
    
    context = {
        'reports': reports,
        'current_semester': current_semester,
        'can_report': can_report,
        'student': student,
    }
    
    return render(request, 'student/reporting_list.html', context)

@login_required
def student_report_current_semester(request):
    """View to handle student reporting for current semester"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "You must be a student to access this page.")
        return redirect('home')
    
    student = request.user.student_profile
    current_semester = Semester.objects.filter(is_current=True).first()
    
    if not current_semester:
        messages.error(request, "No current semester found. Please contact administrator.")
        return redirect('student_reporting_list')
    
    # Check if student has already reported for current semester
    existing_report = StudentReporting.objects.filter(
        student=student, 
        semester=current_semester
    ).first()
    
    if existing_report:
        messages.warning(request, f"You have already reported for {existing_report.semester_display}")
        return redirect('student_reporting_list')
    
    if request.method == 'POST':
        # Create new reporting record
        StudentReporting.objects.create(
            student=student,
            semester=current_semester,
            reporting_type='online',
            status='confirmed',
            remarks=request.POST.get('remarks', '')
        )
        
        messages.success(request, f"Successfully reported for {current_semester.academic_year.year} Semester {current_semester.semester_number}")
        return redirect('student_reporting_list')
    
    context = {
        'current_semester': current_semester,
        'student': student,
    }
    
    return render(request, 'student/report_semester.html', context)

@login_required
def admin_reporting_overview(request):
    """View for admin to see all student reporting records"""
    if request.user.user_type != 'admin':
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('home')
    
    # Get filter parameters
    semester_id = request.GET.get('semester')
    status = request.GET.get('status')
    
    reports = StudentReporting.objects.all()
    
    if semester_id:
        reports = reports.filter(semester_id=semester_id)
    
    if status:
        reports = reports.filter(status=status)
    
    reports = reports.order_by('-reported_date')
    
    # Get all semesters for filter dropdown
    semesters = Semester.objects.all().order_by('-start_date')
    
    context = {
        'reports': reports,
        'semesters': semesters,
        'selected_semester': semester_id,
        'selected_status': status,
    }
    
    return render(request, 'admin/reporting_overview.html', context)

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


# views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from collections import defaultdict
from .models import Student, Enrollment, Grade, AcademicYear, Semester

@login_required
def student_transcript(request):
    # Check if user is a student
    if not hasattr(request.user, 'student_profile'):
        return HttpResponseForbidden("Access denied. Students only.")
    
    student = request.user.student_profile
    
    # Get all enrollments for this student with related data
    enrollments = Enrollment.objects.filter(
        student=student,
        is_active=True
    ).select_related(
        'subject',
        'semester',
        'semester__academic_year'
    ).prefetch_related(
        'grade'
    ).order_by('semester__academic_year__year', 'semester__semester_number', 'subject__code')
    
    # Organize data by academic year and semester
    transcript_data = defaultdict(lambda: defaultdict(list))
    
    for enrollment in enrollments:
        year = enrollment.semester.academic_year.year
        semester_num = enrollment.semester.semester_number
        
        # Get grade information
        grade_info = None
        if hasattr(enrollment, 'grade'):
            grade_info = enrollment.grade
        
        # Calculate total marks if both theory and practical exist
        total_marks = 0
        if grade_info:
            theory = grade_info.theory_marks or 0
            practical = grade_info.practical_marks or 0
            total_marks = theory + practical
        
        subject_data = {
            'subject': enrollment.subject,
            'enrollment': enrollment,
            'grade': grade_info,
            'theory_marks': grade_info.theory_marks if grade_info else None,
            'practical_marks': grade_info.practical_marks if grade_info else None,
            'total_marks': total_marks if grade_info else None,
            'grade_letter': grade_info.grade if grade_info else 'N/A',
            'grade_points': grade_info.grade_points if grade_info else None,
            'is_passed': grade_info.is_passed if grade_info else False,
            'status': 'Passed' if (grade_info and grade_info.is_passed) else 'Failed' if grade_info else 'Pending'
        }
        
        transcript_data[year][semester_num].append(subject_data)
    
    # Convert to regular dict and sort
    transcript_data = dict(transcript_data)
    for year in transcript_data:
        transcript_data[year] = dict(transcript_data[year])
        for semester in transcript_data[year]:
            transcript_data[year][semester].sort(key=lambda x: x['subject'].code)
    
    # Calculate GPA for each semester and overall
    semester_gpas = {}
    overall_credits = 0
    overall_grade_points = 0
    
    for year in transcript_data:
        for semester_num in transcript_data[year]:
            semester_credits = 0
            semester_grade_points = 0
            
            for subject_data in transcript_data[year][semester_num]:
                if subject_data['grade_points'] is not None:
                    credits = subject_data['subject'].credits
                    grade_points = subject_data['grade_points']
                    
                    semester_credits += credits
                    semester_grade_points += (grade_points * credits)
                    
                    overall_credits += credits
                    overall_grade_points += (grade_points * credits)
            
            if semester_credits > 0:
                semester_gpa = semester_grade_points / semester_credits
                semester_gpas[f"{year}-{semester_num}"] = {
                    'gpa': round(semester_gpa, 2),
                    'credits': semester_credits
                }
    
    overall_gpa = round(overall_grade_points / overall_credits, 2) if overall_credits > 0 else 0
    
    context = {
        'student': student,
        'transcript_data': transcript_data,
        'semester_gpas': semester_gpas,
        'overall_gpa': overall_gpa,
        'total_credits': overall_credits,
    }
    
    return render(request, 'student/student_transcript.html', context)


# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db import transaction
from django.forms import modelformset_factory
from django.core.exceptions import ValidationError
from .models import Student, Subject, Enrollment, Grade, Semester, AcademicYear
import json

@login_required
def admin_marks_entry(request):
    # Check if user is admin
    if request.user.user_type != 'admin':
        return HttpResponseForbidden("Access denied. Admins only.")
    
    # Get current academic year and semester
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    if not current_academic_year or not current_semester:
        messages.error(request, "Please set current academic year and semester first.")
        return render(request, 'admin_marks_entry.html', {'error': 'No current academic year/semester set'})
    
    student = None
    enrollments = []
    grades_data = {}
    
    # Handle student search
    if request.method == 'GET' and 'student_id' in request.GET:
        student_id = request.GET.get('student_id')
        if student_id:
            try:
                student = Student.objects.get(student_id=student_id, status='active')
                
                # Get enrollments for current semester
                enrollments = Enrollment.objects.filter(
                    student=student,
                    semester=current_semester,
                    is_active=True
                ).select_related('subject').order_by('subject__code')
                
                # Get existing grades
                for enrollment in enrollments:
                    try:
                        grade = Grade.objects.get(enrollment=enrollment)
                        grades_data[enrollment.id] = {
                            'theory_marks': grade.theory_marks,
                            'practical_marks': grade.practical_marks,
                            'total_marks': grade.total_marks,
                            'grade': grade.grade,
                            'grade_points': grade.grade_points,
                            'is_passed': grade.is_passed,
                            'exam_date': grade.exam_date.strftime('%Y-%m-%d') if grade.exam_date else ''
                        }
                    except Grade.DoesNotExist:
                        grades_data[enrollment.id] = {
                            'theory_marks': None,
                            'practical_marks': None,
                            'total_marks': None,
                            'grade': '',
                            'grade_points': None,
                            'is_passed': False,
                            'exam_date': ''
                        }
                
            except Student.DoesNotExist:
                messages.error(request, f"Student with ID '{student_id}' not found or not active.")
    
    # Handle marks submission
    if request.method == 'POST' and 'save_marks' in request.POST:
        student_id = request.POST.get('student_id')
        if not student_id:
            messages.error(request, "Student ID is required.")
            return render(request, 'admin_marks_entry.html', {})
        
        try:
            student = Student.objects.get(student_id=student_id, status='active')
            enrollments = Enrollment.objects.filter(
                student=student,
                semester=current_semester,
                is_active=True
            ).select_related('subject')
            
            with transaction.atomic():
                for enrollment in enrollments:
                    enrollment_id = str(enrollment.id)
                    
                    # Get form data
                    theory_marks = request.POST.get(f'theory_marks_{enrollment_id}')
                    practical_marks = request.POST.get(f'practical_marks_{enrollment_id}')
                    exam_date = request.POST.get(f'exam_date_{enrollment_id}')
                    
                    # Convert to appropriate types
                    theory_marks = float(theory_marks) if theory_marks else None
                    practical_marks = float(practical_marks) if practical_marks else None
                    exam_date = exam_date if exam_date else None
                    
                    # Calculate total marks
                    total_marks = 0
                    if theory_marks is not None:
                        total_marks += theory_marks
                    if practical_marks is not None:
                        total_marks += practical_marks
                    
                    # Determine grade and grade points
                    grade_letter, grade_points, is_passed = calculate_grade(total_marks)
                    
                    # Create or update grade
                    grade, created = Grade.objects.get_or_create(
                        enrollment=enrollment,
                        defaults={
                            'theory_marks': theory_marks,
                            'practical_marks': practical_marks,
                            'total_marks': total_marks,
                            'grade': grade_letter,
                            'grade_points': grade_points,
                            'is_passed': is_passed,
                            'exam_date': exam_date
                        }
                    )
                    
                    if not created:
                        grade.theory_marks = theory_marks
                        grade.practical_marks = practical_marks
                        grade.total_marks = total_marks
                        grade.grade = grade_letter
                        grade.grade_points = grade_points
                        grade.is_passed = is_passed
                        grade.exam_date = exam_date
                        grade.save()
                
                messages.success(request, f"Marks saved successfully for student {student.student_id}")
                
        except Student.DoesNotExist:
            messages.error(request, f"Student with ID '{student_id}' not found.")
        except Exception as e:
            messages.error(request, f"Error saving marks: {str(e)}")
    
    # Get all students for dropdown (optional)
    all_students = Student.objects.filter(status='active').order_by('student_id')
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'grades_data': grades_data,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        'all_students': all_students,
    }
    
    return render(request, 'admin/admin_marks_entry.html', context)

def calculate_grade(total_marks):
    """Calculate grade letter, grade points, and pass status based on total marks"""
    if total_marks is None or total_marks == 0:
        return '', None, False
    
    if total_marks >= 90:
        return 'A+', 4.0, True
    elif total_marks >= 80:
        return 'A', 3.7, True
    elif total_marks >= 70:
        return 'B+', 3.3, True
    elif total_marks >= 60:
        return 'B', 3.0, True
    elif total_marks >= 50:
        return 'C+', 2.7, True
    elif total_marks >= 40:
        return 'C', 2.0, True
    elif total_marks >= 30:
        return 'D', 1.0, False
    else:
        return 'F', 0.0, False

@login_required
def get_student_info(request):
    """AJAX endpoint to get student information"""
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    student_id = request.GET.get('student_id')
    if not student_id:
        return JsonResponse({'error': 'Student ID required'}, status=400)
    
    try:
        student = Student.objects.get(student_id=student_id, status='active')
        current_semester = Semester.objects.filter(is_current=True).first()
        
        enrollments = Enrollment.objects.filter(
            student=student,
            semester=current_semester,
            is_active=True
        ).select_related('subject')
        
        data = {
            'student': {
                'id': student.student_id,
                'name': student.user.get_full_name(),
                'course': student.course.name,
                'current_year': student.current_year,
                'current_semester': student.current_semester,
            },
            'enrollments': [
                {
                    'id': enrollment.id,
                    'subject_code': enrollment.subject.code,
                    'subject_name': enrollment.subject.name,
                    'credits': enrollment.subject.credits,
                    'theory_hours': enrollment.subject.theory_hours,
                    'practical_hours': enrollment.subject.practical_hours,
                }
                for enrollment in enrollments
            ]
        }
        
        return JsonResponse(data)
        
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)
    
#admin module 
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum
from .models import (
    User, Student, Faculty, Staff, Department, Course, 
    Subject, Enrollment, FeePayment, Attendance, 
    Notification, Event, Hostel, HostelBooking,
    NewsArticle, StudentClub, ClubEvent
)
from datetime import datetime, timedelta


# views.py
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.utils import timezone
from django.shortcuts import render

# Import your models (adjust the import path based on your app structure)
from .models import (
    Student, Faculty, Staff, Department, Course, Subject,
    FeePayment, Hostel, HostelBooking, Notification, Event,
    NewsArticle, StudentClub, ClubEvent, Attendance
)

# Grab the swapped-in user model
User = get_user_model()

# Define the is_admin function or import it
def is_admin(user):
    """Check if user is an admin/superuser"""
    return user.is_superuser or user.is_staff

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    User = get_user_model()  # Call it inside the function
    today = timezone.localdate()            # e.g. 2025-07-14
    now = timezone.now()

    # ─────────── User statistics ───────────
    total_users      = User.objects.count()
    active_users     = User.objects.filter(is_active=True).count()
    new_users_today  = User.objects.filter(date_joined__date=today).count()

    # ─────────── Student statistics ───────────
    total_students       = Student.objects.count()
    active_students      = Student.objects.filter(status='active').count()
    new_students_today   = Student.objects.filter(user__date_joined__date=today).count()

    # ─────────── Faculty statistics ───────────
    total_faculty   = Faculty.objects.count()
    active_faculty  = Faculty.objects.filter(is_active=True).count()

    # ─────────── Staff statistics ───────────
    total_staff   = Staff.objects.count()
    active_staff  = Staff.objects.filter(is_active=True).count()

    # ─────────── Academic statistics ───────────
    total_departments = Department.objects.count()
    total_courses     = Course.objects.count()
    total_subjects    = Subject.objects.count()

    # ─────────── Financial statistics ───────────
    total_fee_payments  = FeePayment.objects.count()
    today_fee_payments = FeePayment.objects.filter(payment_date=today).count()
    recent_payments     = FeePayment.objects.order_by('-payment_date')[:5]

    # ─────────── Hostel statistics ───────────
    total_hostels            = Hostel.objects.count()
    total_hostel_bookings    = HostelBooking.objects.count()
    pending_hostel_bookings  = HostelBooking.objects.filter(status='pending').count()

    # ─────────── Recent activities ───────────
    recent_notifications = Notification.objects.order_by('-created_at')[:5]
    recent_events        = Event.objects.order_by('-start_date')[:5]
    recent_news          = NewsArticle.objects.order_by('-publish_date')[:3]

    # ─────────── Club statistics ───────────
    total_clubs        = StudentClub.objects.count()
    active_club_events = ClubEvent.objects.filter(status='ongoing').count()

    # ─────────── Attendance summary (last 7 days) ───────────
    attendance_summary = (
        Attendance.objects
        .filter(date__gte=now - timedelta(days=7))
        .values('status')
        .annotate(count=Count('status'))
    )

    context = {
        # User stats
        'total_users': total_users,
        'active_users': active_users,
        'new_users_today': new_users_today,

        # Student stats
        'total_students': total_students,
        'active_students': active_students,
        'new_students_today': new_students_today,

        # Faculty stats
        'total_faculty': total_faculty,
        'active_faculty': active_faculty,

        # Staff stats
        'total_staff': total_staff,
        'active_staff': active_staff,

        # Academic stats
        'total_departments': total_departments,
        'total_courses': total_courses,
        'total_subjects': total_subjects,

        # Financial stats
        'total_fee_payments': total_fee_payments,
        'today_fee_payments': today_fee_payments,
        'recent_payments': recent_payments,

        # Hostel stats
        'total_hostels': total_hostels,
        'total_hostel_bookings': total_hostel_bookings,
        'pending_hostel_bookings': pending_hostel_bookings,

        # Activities
        'recent_notifications': recent_notifications,
        'recent_events': recent_events,
        'recent_news': recent_news,

        # Clubs
        'total_clubs': total_clubs,
        'active_club_events': active_club_events,

        # Attendance
        'attendance_summary': attendance_summary,

        # Current date (formatted)
        'current_date': now.strftime("%B %d, %Y"),
    }

    return render(request, "admin/admin_dashboard.html", context)

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import logging

logger = logging.getLogger(__name__)

@csrf_protect
@require_http_methods(["GET", "POST"])
def admin_login_view(request):
    """
    Admin login view with enhanced security and validation
    """
    # Redirect if already authenticated and is staff/admin
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_dashboard')  # Replace with your admin dashboard URL
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        remember_me = request.POST.get('RememberMe') == 'on'
        
        # Basic validation
        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return render(request, 'admin/admin_login.html')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user is admin/staff
            if user.is_staff or user.is_superuser:
                if user.is_active:
                    login(request, user)
                    
                    # Handle remember me functionality
                    if remember_me:
                        request.session.set_expiry(1209600)  # 2 weeks
                    else:
                        request.session.set_expiry(0)  # Browser close
                    
                    # Log successful login
                    logger.info(f"Admin login successful for user: {username}")
                    
                    messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                    
                    # Redirect to next page or dashboard
                    next_url = request.GET.get('next', 'admin_dashboard')
                    return redirect(next_url)
                else:
                    messages.error(request, 'Your account has been deactivated. Please contact support.')
            else:
                messages.error(request, 'Access denied. Admin privileges required.')
                logger.warning(f"Non-admin user attempted admin login: {username}")
        else:
            messages.error(request, 'Invalid username or password.')
            logger.warning(f"Failed admin login attempt for username: {username}")
    
    return render(request, 'admin/admin_login.html')

@login_required
def admin_logout_view(request):
    """
    Admin logout view
    """
    username = request.user.username
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    logger.info(f"Admin logout for user: {username}")
    return redirect('admin_login')


# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.paginator import Paginator
from django.urls import reverse
from .models import Student, Course, Department
from .forms import StudentForm, UserForm  # You'll need to create these forms

User = get_user_model()

@login_required
def student_list(request):
    """List all students with pagination and search"""
    students = Student.objects.select_related('user', 'course', 'course__department').all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        students = students.filter(
            models.Q(user__first_name__icontains=search_query) |
            models.Q(user__last_name__icontains=search_query) |
            models.Q(student_id__icontains=search_query) |
            models.Q(course__name__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        students = students.filter(status=status_filter)
    
    # Filter by course
    course_filter = request.GET.get('course', '')
    if course_filter:
        students = students.filter(course_id=course_filter)
    
    # Pagination
    paginator = Paginator(students, 20)  # 20 students per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all courses for filter dropdown
    courses = Course.objects.filter(is_active=True)
    
    context = {
        'students': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'course_filter': course_filter,
        'courses': courses,
        'status_choices': Student.STATUS_CHOICES,
    }
    
    return render(request, 'admin/students/student_list.html', context)

@login_required
def student_detail(request, student_id):
    """View student details"""
    student = get_object_or_404(Student, student_id=student_id)
    
    context = {
        'student': student,
    }
    
    return render(request, 'admin/students/student_detail.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

@login_required
@transaction.atomic
def student_create(request):
    """Create a new student"""
    if request.method == 'POST':
        user_form = UserForm(request.POST, request.FILES)
        student_form = StudentForm(request.POST)
        
        # Debug: Print form data
        print("POST data:", request.POST)
        print("FILES data:", request.FILES)
        
        # Check if both forms are valid
        user_form_valid = user_form.is_valid()
        student_form_valid = student_form.is_valid()
        
        # Debug: Print form errors
        if not user_form_valid:
            print("User form errors:", user_form.errors)
        if not student_form_valid:
            print("Student form errors:", student_form.errors)
        
        if user_form_valid and student_form_valid:
            try:
                # Create user first
                user = user_form.save(commit=False)
                user.user_type = 'student'
                user.is_active = True  # Make sure user is active
                user.save()
                
                print(f"User created: {user.username} (ID: {user.id})")
                
                # Create student profile
                student = student_form.save(commit=False)
                student.user = user
                student.save()
                
                print(f"Student created: {student.student_id} (ID: {student.id})")
                
                messages.success(request, f'Student {student.student_id} created successfully!')
                return redirect('student_detail', student_id=student.student_id)
                
            except Exception as e:
                logger.error(f'Error creating student: {str(e)}')
                print(f"Exception occurred: {str(e)}")
                messages.error(request, f'Error creating student: {str(e)}')
                # Rollback will happen automatically due to @transaction.atomic
        else:
            # Add form errors to messages
            if user_form.errors:
                for field, errors in user_form.errors.items():
                    for error in errors:
                        messages.error(request, f"User {field}: {error}")
            
            if student_form.errors:
                for field, errors in student_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Student {field}: {error}")
    
    else:
        user_form = UserForm()
        student_form = StudentForm()
    
    context = {
        'user_form': user_form,
        'student_form': student_form,
        'action': 'Create',
    }
    
    return render(request, 'admin/students/student_form.html', context)

@login_required
@transaction.atomic
def student_update(request, student_id):
    """Update student information"""
    student = get_object_or_404(Student, student_id=student_id)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, request.FILES, instance=student.user)
        student_form = StudentForm(request.POST, instance=student)
        
        if user_form.is_valid() and student_form.is_valid():
            try:
                user_form.save()
                student_form.save()
                
                messages.success(request, f'Student {student.student_id} updated successfully!')
                return redirect('student_detail', student_id=student.student_id)
                
            except Exception as e:
                messages.error(request, f'Error updating student: {str(e)}')
    else:
        user_form = UserForm(instance=student.user)
        student_form = StudentForm(instance=student)
    
    context = {
        'user_form': user_form,
        'student_form': student_form,
        'student': student,
        'action': 'Update',
    }
    
    return render(request, 'admin/students/student_form.html', context)

@login_required
def student_delete(request, student_id):
    """Delete a student"""
    student = get_object_or_404(Student, student_id=student_id)
    
    if request.method == 'POST':
        try:
            student_name = student.user.get_full_name()
            student.user.delete()  # This will cascade delete the student
            messages.success(request, f'Student {student_name} deleted successfully!')
            return redirect('student_list')
        except Exception as e:
            messages.error(request, f'Error deleting student: {str(e)}')
    
    context = {
        'student': student,
    }
    
    return render(request, 'admin/students/student_confirm_delete.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Faculty, User, Department, AcademicYear, Semester, Schedule

@login_required
def faculty_list(request):
    """Display list of all faculty members with search and pagination"""
    search_query = request.GET.get('search', '')
    department_filter = request.GET.get('department', '')
    designation_filter = request.GET.get('designation', '')
    
    faculties = Faculty.objects.select_related('user', 'department').filter(is_active=True)
    
    # Search functionality
    if search_query:
        faculties = faculties.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(employee_id__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    # Department filter
    if department_filter:
        faculties = faculties.filter(department_id=department_filter)
    
    # Designation filter
    if designation_filter:
        faculties = faculties.filter(designation=designation_filter)
    
    # Pagination
    paginator = Paginator(faculties, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get departments and designations for filters
    departments = Department.objects.filter(is_active=True)
    designations = Faculty.DESIGNATION_CHOICES
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'departments': departments,
        'designations': designations,
        'department_filter': department_filter,
        'designation_filter': designation_filter,
    }
    
    return render(request, 'faculty/faculty_list.html', context)

@login_required
def faculty_detail(request, employee_id):
    """Display detailed information about a specific faculty member"""
    faculty = get_object_or_404(Faculty, employee_id=employee_id, is_active=True)
    
    # Get current academic year and semester
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = None
    
    if current_academic_year:
        current_semester = Semester.objects.filter(
            academic_year=current_academic_year,
            is_current=True
        ).first()
    
    # Get subjects scheduled for current semester
    scheduled_subjects = []
    if current_semester:
        schedules = Schedule.objects.select_related(
            'subject', 'classroom', 'time_slot'
        ).filter(
            faculty=faculty,
            semester=current_semester,
            is_active=True
        ).order_by('time_slot__day_of_week', 'time_slot__start_time')
        
        scheduled_subjects = schedules
    
    context = {
        'faculty': faculty,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        'scheduled_subjects': scheduled_subjects,
    }
    
    return render(request, 'faculty/faculty_detail.html', context)

@login_required
def faculty_create(request):
    """Create a new faculty member"""
    if request.method == 'POST':
        try:
            # Create User first
            user = User.objects.create_user(
                username=request.POST['username'],
                email=request.POST['email'],
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                user_type='faculty',
                phone=request.POST.get('phone', ''),
                address=request.POST.get('address', ''),
                gender=request.POST.get('gender', ''),
                date_of_birth=request.POST.get('date_of_birth') or None,
            )
            
            # Set password
            user.set_password(request.POST['password'])
            user.save()
            
            # Create Faculty profile
            faculty = Faculty.objects.create(
                user=user,
                employee_id=request.POST['employee_id'],
                department_id=request.POST['department'],
                designation=request.POST['designation'],
                qualification=request.POST['qualification'],
                experience_years=int(request.POST.get('experience_years', 0)),
                specialization=request.POST.get('specialization', ''),
                salary=request.POST.get('salary') or None,
                joining_date=request.POST['joining_date'],
            )
            
            messages.success(request, f'Faculty member {faculty.user.get_full_name()} created successfully!')
            return redirect('faculty_detail', employee_id=faculty.employee_id)
            
        except Exception as e:
            messages.error(request, f'Error creating faculty: {str(e)}')
    
    departments = Department.objects.filter(is_active=True)
    designations = Faculty.DESIGNATION_CHOICES
    
    context = {
        'departments': departments,
        'designations': designations,
    }
    
    return render(request, 'faculty/faculty_form.html', context)

@login_required
def faculty_update(request, employee_id):
    """Update an existing faculty member"""
    faculty = get_object_or_404(Faculty, employee_id=employee_id, is_active=True)
    
    if request.method == 'POST':
        try:
            # Update User information
            user = faculty.user
            user.username = request.POST['username']
            user.email = request.POST['email']
            user.first_name = request.POST['first_name']
            user.last_name = request.POST['last_name']
            user.phone = request.POST.get('phone', '')
            user.address = request.POST.get('address', '')
            user.gender = request.POST.get('gender', '')
            user.date_of_birth = request.POST.get('date_of_birth') or None
            
            # Update password if provided
            if request.POST.get('password'):
                user.set_password(request.POST['password'])
            
            user.save()
            
            # Update Faculty information
            faculty.employee_id = request.POST['employee_id']
            faculty.department_id = request.POST['department']
            faculty.designation = request.POST['designation']
            faculty.qualification = request.POST['qualification']
            faculty.experience_years = int(request.POST.get('experience_years', 0))
            faculty.specialization = request.POST.get('specialization', '')
            faculty.salary = request.POST.get('salary') or None
            faculty.joining_date = request.POST['joining_date']
            
            faculty.save()
            
            messages.success(request, f'Faculty member {faculty.user.get_full_name()} updated successfully!')
            return redirect('faculty_detail', employee_id=faculty.employee_id)
            
        except Exception as e:
            messages.error(request, f'Error updating faculty: {str(e)}')
    
    departments = Department.objects.filter(is_active=True)
    designations = Faculty.DESIGNATION_CHOICES
    
    context = {
        'faculty': faculty,
        'departments': departments,
        'designations': designations,
    }
    
    return render(request, 'faculty/faculty_form.html', context)

@login_required
def faculty_delete(request, employee_id):
    """Delete (deactivate) a faculty member"""
    faculty = get_object_or_404(Faculty, employee_id=employee_id, is_active=True)
    
    if request.method == 'POST':
        # Soft delete - just deactivate
        faculty.is_active = False
        faculty.user.is_active = False
        faculty.save()
        faculty.user.save()
        
        messages.success(request, f'Faculty member {faculty.user.get_full_name()} has been deactivated.')
        return redirect('faculty_list')
    
    # Check if faculty has any active schedules
    active_schedules = Schedule.objects.filter(faculty=faculty, is_active=True).count()
    
    context = {
        'faculty': faculty,
        'active_schedules': active_schedules,
    }
    
    return render(request, 'faculty/faculty_confirm_delete.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import (
    Schedule, Subject, Faculty, Classroom, TimeSlot, Semester, 
    AcademicYear, Course, Department
)

@login_required
def schedule_list(request):
    """Display list of all schedules with comprehensive filtering"""
    # Get filter parameters
    course_filter = request.GET.get('course', '')
    department_filter = request.GET.get('department', '')
    faculty_filter = request.GET.get('faculty', '')
    semester_filter = request.GET.get('semester', '')
    day_filter = request.GET.get('day', '')
    classroom_filter = request.GET.get('classroom', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    schedules = Schedule.objects.select_related(
        'subject', 'subject__course', 'subject__course__department',
        'faculty', 'faculty__user', 'classroom', 'time_slot', 'semester'
    ).filter(is_active=True)
    
    # Apply filters
    if course_filter:
        schedules = schedules.filter(subject__course_id=course_filter)
    
    if department_filter:
        schedules = schedules.filter(subject__course__department_id=department_filter)
    
    if faculty_filter:
        schedules = schedules.filter(faculty_id=faculty_filter)
    
    if semester_filter:
        schedules = schedules.filter(semester_id=semester_filter)
    
    if day_filter:
        schedules = schedules.filter(time_slot__day_of_week=day_filter)
    
    if classroom_filter:
        schedules = schedules.filter(classroom_id=classroom_filter)
    
    # Search functionality
    if search_query:
        schedules = schedules.filter(
            Q(subject__name__icontains=search_query) |
            Q(subject__code__icontains=search_query) |
            Q(faculty__user__first_name__icontains=search_query) |
            Q(faculty__user__last_name__icontains=search_query) |
            Q(classroom__name__icontains=search_query)
        )
    
    # Order by day and time
    schedules = schedules.order_by(
        'time_slot__day_of_week', 
        'time_slot__start_time',
        'subject__course__name'
    )
    
    # Pagination
    paginator = Paginator(schedules, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    courses = Course.objects.filter(is_active=True).select_related('department')
    departments = Department.objects.filter(is_active=True)
    faculties = Faculty.objects.filter(is_active=True).select_related('user')
    semesters = Semester.objects.all().select_related('academic_year')
    classrooms = Classroom.objects.filter(is_active=True)
    days = TimeSlot.DAY_CHOICES
    
    context = {
        'page_obj': page_obj,
        'courses': courses,
        'departments': departments,
        'faculties': faculties,
        'semesters': semesters,
        'classrooms': classrooms,
        'days': days,
        'course_filter': course_filter,
        'department_filter': department_filter,
        'faculty_filter': faculty_filter,
        'semester_filter': semester_filter,
        'day_filter': day_filter,
        'classroom_filter': classroom_filter,
        'search_query': search_query,
    }
    
    return render(request, 'schedule/schedule_list.html', context)

@login_required
def schedule_detail(request, schedule_id):
    """Display detailed information about a specific schedule"""
    schedule = get_object_or_404(Schedule, id=schedule_id, is_active=True)
    
    # Get related schedules (same subject, different time slots)
    related_schedules = Schedule.objects.filter(
        subject=schedule.subject,
        semester=schedule.semester,
        is_active=True
    ).exclude(id=schedule.id).select_related(
        'faculty', 'faculty__user', 'classroom', 'time_slot'
    )
    
    # Get students enrolled in this subject for this semester
    from .models import Enrollment
    enrolled_students = Enrollment.objects.filter(
        subject=schedule.subject,
        semester=schedule.semester,
        is_active=True
    ).select_related('student', 'student__user').count()
    
    context = {
        'schedule': schedule,
        'related_schedules': related_schedules,
        'enrolled_students': enrolled_students,
    }
    
    return render(request, 'schedule/schedule_detail.html', context)

@login_required
def schedule_create(request):
    """Create a new schedule entry"""
    if request.method == 'POST':
        try:
            # Check for conflicts
            classroom_id = request.POST['classroom']
            time_slot_id = request.POST['time_slot']
            semester_id = request.POST['semester']
            
            # Check classroom-time conflict
            existing_schedule = Schedule.objects.filter(
                classroom_id=classroom_id,
                time_slot_id=time_slot_id,
                semester_id=semester_id,
                is_active=True
            ).first()
            
            if existing_schedule:
                messages.error(request, f'Conflict: {existing_schedule.classroom.name} is already booked for this time slot.')
                return redirect('schedule_create')
            
            # Check faculty availability
            faculty_id = request.POST['faculty']
            faculty_conflict = Schedule.objects.filter(
                faculty_id=faculty_id,
                time_slot_id=time_slot_id,
                semester_id=semester_id,
                is_active=True
            ).first()
            
            if faculty_conflict:
                messages.error(request, f'Conflict: Faculty is already scheduled for another subject at this time.')
                return redirect('schedule_create')
            
            # Create schedule
            schedule = Schedule.objects.create(
                subject_id=request.POST['subject'],
                faculty_id=faculty_id,
                classroom_id=classroom_id,
                time_slot_id=time_slot_id,
                semester_id=semester_id,
            )
            
            messages.success(request, f'Schedule created successfully for {schedule.subject.code}!')
            return redirect('schedule_detail', schedule_id=schedule.id)
            
        except Exception as e:
            messages.error(request, f'Error creating schedule: {str(e)}')
    
    # Get form options
    subjects = Subject.objects.filter(is_active=True).select_related('course')
    faculties = Faculty.objects.filter(is_active=True).select_related('user')
    classrooms = Classroom.objects.filter(is_active=True)
    time_slots = TimeSlot.objects.filter(is_active=True)
    semesters = Semester.objects.all().select_related('academic_year')
    courses = Course.objects.filter(is_active=True)
    
    context = {
        'subjects': subjects,
        'faculties': faculties,
        'classrooms': classrooms,
        'time_slots': time_slots,
        'semesters': semesters,
        'courses': courses,
    }
    
    return render(request, 'schedule/schedule_form.html', context)

@login_required
def schedule_update(request, schedule_id):
    """Update an existing schedule"""
    schedule = get_object_or_404(Schedule, id=schedule_id, is_active=True)
    
    if request.method == 'POST':
        try:
            # Check for conflicts (excluding current schedule)
            classroom_id = request.POST['classroom']
            time_slot_id = request.POST['time_slot']
            semester_id = request.POST['semester']
            
            # Check classroom-time conflict
            existing_schedule = Schedule.objects.filter(
                classroom_id=classroom_id,
                time_slot_id=time_slot_id,
                semester_id=semester_id,
                is_active=True
            ).exclude(id=schedule.id).first()
            
            if existing_schedule:
                messages.error(request, f'Conflict: {existing_schedule.classroom.name} is already booked for this time slot.')
                return redirect('schedule_update', schedule_id=schedule.id)
            
            # Check faculty availability
            faculty_id = request.POST['faculty']
            faculty_conflict = Schedule.objects.filter(
                faculty_id=faculty_id,
                time_slot_id=time_slot_id,
                semester_id=semester_id,
                is_active=True
            ).exclude(id=schedule.id).first()
            
            if faculty_conflict:
                messages.error(request, f'Conflict: Faculty is already scheduled for another subject at this time.')
                return redirect('schedule_update', schedule_id=schedule.id)
            
            # Update schedule
            schedule.subject_id = request.POST['subject']
            schedule.faculty_id = faculty_id
            schedule.classroom_id = classroom_id
            schedule.time_slot_id = time_slot_id
            schedule.semester_id = semester_id
            schedule.save()
            
            messages.success(request, f'Schedule updated successfully!')
            return redirect('schedule_detail', schedule_id=schedule.id)
            
        except Exception as e:
            messages.error(request, f'Error updating schedule: {str(e)}')
    
    # Get form options
    subjects = Subject.objects.filter(is_active=True).select_related('course')
    faculties = Faculty.objects.filter(is_active=True).select_related('user')
    classrooms = Classroom.objects.filter(is_active=True)
    time_slots = TimeSlot.objects.filter(is_active=True)
    semesters = Semester.objects.all().select_related('academic_year')
    courses = Course.objects.filter(is_active=True)
    
    context = {
        'schedule': schedule,
        'subjects': subjects,
        'faculties': faculties,
        'classrooms': classrooms,
        'time_slots': time_slots,
        'semesters': semesters,
        'courses': courses,
    }
    
    return render(request, 'schedule/schedule_form.html', context)

@login_required
def schedule_delete(request, schedule_id):
    """Delete a schedule entry"""
    schedule = get_object_or_404(Schedule, id=schedule_id, is_active=True)
    
    if request.method == 'POST':
        schedule.is_active = False
        schedule.save()
        messages.success(request, f'Schedule for {schedule.subject.code} has been deleted.')
        return redirect('schedule_list')
    
    context = {
        'schedule': schedule,
    }
    
    return render(request, 'schedule/schedule_confirm_delete.html', context)

@login_required
def get_subjects_by_course(request):
    """AJAX endpoint to get subjects for a specific course"""
    course_id = request.GET.get('course_id')
    if course_id:
        subjects = Subject.objects.filter(course_id=course_id, is_active=True)
        subjects_data = [{'id': s.id, 'name': f'{s.code} - {s.name}'} for s in subjects]
        return JsonResponse({'subjects': subjects_data})
    return JsonResponse({'subjects': []})

@login_required
def schedule_timetable(request):
    """Display timetable view for a specific course and semester"""
    course_id = request.GET.get('course')
    semester_id = request.GET.get('semester')
    
    if not course_id or not semester_id:
        courses = Course.objects.filter(is_active=True)
        semesters = Semester.objects.all().select_related('academic_year')
        return render(request, 'schedule/timetable_filter.html', {
            'courses': courses,
            'semesters': semesters,
        })
    
    course = get_object_or_404(Course, id=course_id)
    semester = get_object_or_404(Semester, id=semester_id)
    
    # Get all schedules for this course and semester
    schedules = Schedule.objects.filter(
        subject__course=course,
        semester=semester,
        is_active=True
    ).select_related(
        'subject', 'faculty', 'faculty__user', 'classroom', 'time_slot'
    ).order_by('time_slot__day_of_week', 'time_slot__start_time')
    
    # Organize by day and time
    timetable = {}
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    for day in days:
        timetable[day] = schedules.filter(time_slot__day_of_week=day)
    
    # Get all time slots for reference
    time_slots = TimeSlot.objects.filter(is_active=True).order_by('start_time')
    
    context = {
        'course': course,
        'semester': semester,
        'timetable': timetable,
        'time_slots': time_slots,
        'schedules': schedules,
    }
    
    return render(request, 'schedule/timetable.html', context)



# views.py
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Course, Subject, Department
import json

def course_list_view(request):
    """
    Display all courses with filtering and pagination
    """
    # Get filter parameters
    department_id = request.GET.get('department')
    course_type = request.GET.get('course_type')
    search = request.GET.get('search', '')
    
    # Base queryset
    courses = Course.objects.filter(is_active=True).select_related('department')
    
    # Apply filters
    if department_id:
        courses = courses.filter(department_id=department_id)
    
    if course_type:
        courses = courses.filter(course_type=course_type)
    
    if search:
        courses = courses.filter(
            Q(name__icontains=search) | 
            Q(code__icontains=search) |
            Q(department__name__icontains=search)
        )
    
    # Annotate with subject count
    courses = courses.annotate(
        subject_count=Count('subjects', filter=Q(subjects__is_active=True))
    )
    
    # Pagination
    paginator = Paginator(courses, 12)  # Show 12 courses per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get departments for filter dropdown
    departments = Department.objects.filter(is_active=True).order_by('name')
    
    context = {
        'courses': page_obj,
        'departments': departments,
        'course_types': Course.COURSE_TYPES,
        'current_department': department_id,
        'current_course_type': course_type,
        'search_query': search,
        'total_courses': courses.count(),
    }
    
    return render(request, 'courses/course_list.html', context)


def course_detail_view(request, course_id):
    """
    Display course details with subjects organized by year and semester
    """
    course = get_object_or_404(Course, id=course_id, is_active=True)
    
    # Get all subjects for this course
    subjects = Subject.objects.filter(
        course=course, 
        is_active=True
    ).select_related('course').prefetch_related('prerequisites')
    
    # Organize subjects by year and semester
    subjects_by_year = {}
    
    for subject in subjects:
        year = subject.year
        semester = subject.semester
        
        if year not in subjects_by_year:
            subjects_by_year[year] = {}
        
        if semester not in subjects_by_year[year]:
            subjects_by_year[year][semester] = []
        
        subjects_by_year[year][semester].append(subject)
    
    # Sort years and semesters
    for year in subjects_by_year:
        subjects_by_year[year] = dict(sorted(subjects_by_year[year].items()))
    
    subjects_by_year = dict(sorted(subjects_by_year.items()))
    
    # Calculate totals
    total_credits = sum(subject.credits for subject in subjects)
    total_theory_hours = sum(subject.theory_hours for subject in subjects)
    total_practical_hours = sum(subject.practical_hours for subject in subjects)
    
    # Get course statistics
    course_stats = {
        'total_subjects': subjects.count(),
        'total_credits': total_credits,
        'total_theory_hours': total_theory_hours,
        'total_practical_hours': total_practical_hours,
        'elective_subjects': subjects.filter(is_elective=True).count(),
        'core_subjects': subjects.filter(is_elective=False).count(),
    }
    
    context = {
        'course': course,
        'subjects_by_year': subjects_by_year,
        'course_stats': course_stats,
        'years': sorted(subjects_by_year.keys()),
    }
    
    return render(request, 'courses/course_detail.html', context)


def get_course_subjects_json(request, course_id):
    """
    API endpoint to get course subjects in JSON format for AJAX calls
    """
    course = get_object_or_404(Course, id=course_id, is_active=True)
    
    subjects = Subject.objects.filter(
        course=course, 
        is_active=True
    ).select_related('course').prefetch_related('prerequisites')
    
    subjects_data = {}
    
    for subject in subjects:
        year = subject.year
        semester = subject.semester
        
        if year not in subjects_data:
            subjects_data[year] = {}
        
        if semester not in subjects_data[year]:
            subjects_data[year][semester] = []
        
        # Get prerequisites
        prerequisites = [
            {'id': prereq.id, 'name': prereq.name, 'code': prereq.code}
            for prereq in subject.prerequisites.all()
        ]
        
        subjects_data[year][semester].append({
            'id': subject.id,
            'name': subject.name,
            'code': subject.code,
            'credits': subject.credits,
            'theory_hours': subject.theory_hours,
            'practical_hours': subject.practical_hours,
            'is_elective': subject.is_elective,
            'prerequisites': prerequisites,
        })
    
    return JsonResponse({
        'course': {
            'id': course.id,
            'name': course.name,
            'code': course.code,
            'course_type': course.course_type,
            'department': course.department.name,
        },
        'subjects': subjects_data
    })


def department_courses_view(request, department_id):
    """
    Display all courses in a specific department
    """
    department = get_object_or_404(Department, id=department_id, is_active=True)
    
    courses = Course.objects.filter(
        department=department,
        is_active=True
    ).annotate(
        subject_count=Count('subjects', filter=Q(subjects__is_active=True))
    ).order_by('name')
    
    context = {
        'department': department,
        'courses': courses,
    }
    
    return render(request, 'courses/department_courses.html', context)



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import CourseForm
from .models import Course, Department

@login_required
def add_course_view(request):
    """
    View to add a new course
    """
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course "{course.name}" has been added successfully!')
            
            # Redirect based on user preference
            if 'save_and_continue' in request.POST:
                return redirect('add_course')
            else:
                return redirect('course_detail', course_id=course.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CourseForm()
    
    context = {
        'form': form,
        'title': 'Add New Course',
        'departments': Department.objects.filter(is_active=True).count(),
    }
    
    return render(request, 'courses/add_course.html', context)

@login_required
def edit_course_view(request, course_id):
    """
    View to edit an existing course
    """
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            updated_course = form.save()
            messages.success(request, f'Course "{updated_course.name}" has been updated successfully!')
            return redirect('course_detail', course_id=updated_course.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CourseForm(instance=course)
    
    context = {
        'form': form,
        'course': course,
        'title': f'Edit Course - {course.name}',
        'is_editing': True,
    }
    
    return render(request, 'courses/add_course.html', context)

@login_required
def delete_course_view(request, course_id):
    """
    View to delete a course
    """
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        course_name = course.name
        course.delete()
        messages.success(request, f'Course "{course_name}" has been deleted successfully!')
        return redirect('course_list')
    
    context = {
        'course': course,
        'students_count': course.students.count(),
        'subjects_count': course.subjects.count(),
    }
    
    return render(request, 'courses/delete_course.html', context)

def check_course_code(request):
    """
    AJAX view to check if course code is available
    """
    code = request.GET.get('code', '').upper()
    course_id = request.GET.get('course_id')
    
    if not code:
        return JsonResponse({'available': True})
    
    existing = Course.objects.filter(code=code)
    if course_id:
        existing = existing.exclude(pk=course_id)
    
    return JsonResponse({'available': not existing.exists()})

# views.py
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Avg, Count, Sum
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import (
    Student, Enrollment, Grade, Subject, AcademicYear, 
    Semester, Course, Department
)
from collections import defaultdict
from decimal import Decimal

@login_required
def student_performance_view(request, student_id):
    """View specific student performance with all academic records"""
    
    # Get the student
    student = get_object_or_404(Student, student_id=student_id)
    
    # Get all enrollments for this student
    enrollments = Enrollment.objects.filter(
        student=student
    ).select_related(
        'subject', 'semester', 'semester__academic_year'
    ).prefetch_related('grade').order_by(
        'semester__academic_year__start_date', 'semester__semester_number'
    )
    
    # Organize data by academic year and semester
    academic_data = []
    
    current_year = None
    current_semester = None
    year_data = None
    semester_data = None
    
    overall_stats = {
        'total_subjects': 0,
        'passed_subjects': 0,
        'failed_subjects': 0,
        'total_credits': 0,
        'earned_credits': 0,
        'overall_gpa': 0,
        'total_grade_points': 0
    }
    
    for enrollment in enrollments:
        academic_year = enrollment.semester.academic_year
        semester = enrollment.semester
        
        # Create new year data if needed
        if current_year != academic_year:
            if year_data:
                academic_data.append(year_data)
            year_data = {
                'academic_year': academic_year,
                'semesters': []
            }
            current_year = academic_year
            current_semester = None
        
        # Create new semester data if needed
        if current_semester != semester:
            if semester_data:
                # Calculate semester statistics
                total_subjects = len(semester_data['subjects'])
                passed_subjects = sum(1 for s in semester_data['subjects'] if s['is_passed'])
                failed_subjects = total_subjects - passed_subjects
                
                total_credits = sum(s['subject'].credits for s in semester_data['subjects'])
                earned_credits = sum(s['subject'].credits for s in semester_data['subjects'] if s['is_passed'])
                
                # Calculate GPA for semester
                total_grade_points = sum(
                    (s['grade_points'] or 0) * s['subject'].credits 
                    for s in semester_data['subjects'] if s['grade_points'] is not None
                )
                semester_gpa = total_grade_points / total_credits if total_credits > 0 else 0
                
                semester_data['stats'] = {
                    'total_subjects': total_subjects,
                    'passed_subjects': passed_subjects,
                    'failed_subjects': failed_subjects,
                    'total_credits': total_credits,
                    'earned_credits': earned_credits,
                    'semester_gpa': round(semester_gpa, 2),
                    'total_grade_points': total_grade_points
                }
                
                year_data['semesters'].append(semester_data)
            
            semester_data = {
                'semester': semester,
                'subjects': [],
                'stats': {}
            }
            current_semester = semester
        
        # Get grade information
        grade_info = {
            'enrollment': enrollment,
            'subject': enrollment.subject,
            'theory_marks': None,
            'practical_marks': None,
            'total_marks': None,
            'grade': None,
            'grade_points': None,
            'is_passed': False,
            'exam_date': None
        }
        
        # Check if grade exists
        if hasattr(enrollment, 'grade'):
            grade = enrollment.grade
            grade_info.update({
                'theory_marks': grade.theory_marks,
                'practical_marks': grade.practical_marks,
                'total_marks': grade.total_marks,
                'grade': grade.grade,
                'grade_points': grade.grade_points,
                'is_passed': grade.is_passed,
                'exam_date': grade.exam_date
            })
        
        semester_data['subjects'].append(grade_info)
        
        # Add to overall statistics
        overall_stats['total_subjects'] += 1
        if grade_info['is_passed']:
            overall_stats['passed_subjects'] += 1
        else:
            overall_stats['failed_subjects'] += 1
        
        overall_stats['total_credits'] += enrollment.subject.credits
        if grade_info['is_passed']:
            overall_stats['earned_credits'] += enrollment.subject.credits
        
        if grade_info['grade_points'] is not None:
            overall_stats['total_grade_points'] += grade_info['grade_points'] * enrollment.subject.credits
    
    # Don't forget the last semester and year
    if semester_data:
        # Calculate final semester statistics
        total_subjects = len(semester_data['subjects'])
        passed_subjects = sum(1 for s in semester_data['subjects'] if s['is_passed'])
        failed_subjects = total_subjects - passed_subjects
        
        total_credits = sum(s['subject'].credits for s in semester_data['subjects'])
        earned_credits = sum(s['subject'].credits for s in semester_data['subjects'] if s['is_passed'])
        
        total_grade_points = sum(
            (s['grade_points'] or 0) * s['subject'].credits 
            for s in semester_data['subjects'] if s['grade_points'] is not None
        )
        semester_gpa = total_grade_points / total_credits if total_credits > 0 else 0
        
        semester_data['stats'] = {
            'total_subjects': total_subjects,
            'passed_subjects': passed_subjects,
            'failed_subjects': failed_subjects,
            'total_credits': total_credits,
            'earned_credits': earned_credits,
            'semester_gpa': round(semester_gpa, 2),
            'total_grade_points': total_grade_points
        }
        
        year_data['semesters'].append(semester_data)
    
    if year_data:
        academic_data.append(year_data)
    
    # Calculate overall GPA
    if overall_stats['total_credits'] > 0:
        overall_stats['overall_gpa'] = round(
            overall_stats['total_grade_points'] / overall_stats['total_credits'], 2
        )
    
    # Calculate completion percentage
    overall_stats['completion_percentage'] = round(
        (overall_stats['earned_credits'] / overall_stats['total_credits']) * 100, 2
    ) if overall_stats['total_credits'] > 0 else 0
    
    context = {
        'student': student,
        'academic_data': academic_data,
        'overall_stats': overall_stats,
        'course': student.course,
        'department': student.course.department,
    }
    
    return render(request, 'admin/students/student_performance.html', context)


@login_required
def student_performance_pdf_data(request, student_id):
    """API endpoint to get student performance data for PDF generation"""
    
    student = get_object_or_404(Student, student_id=student_id)
    
    # Get academic year and semester filters from request
    academic_year_id = request.GET.get('academic_year_id')
    semester_id = request.GET.get('semester_id')
    
    # Build query filters
    filters = Q(student=student)
    
    if academic_year_id:
        filters &= Q(semester__academic_year_id=academic_year_id)
    
    if semester_id:
        filters &= Q(semester_id=semester_id)
    
    # Get filtered enrollments
    enrollments = Enrollment.objects.filter(filters).select_related(
        'subject', 'semester', 'semester__academic_year'
    ).prefetch_related('grade').order_by(
        'semester__academic_year__start_date', 'semester__semester_number'
    )
    
    # Format data for PDF
    pdf_data = []
    
    for enrollment in enrollments:
        grade_data = {
            'academic_year': enrollment.semester.academic_year.year,
            'semester': f"Semester {enrollment.semester.semester_number}",
            'subject_code': enrollment.subject.code,
            'subject_name': enrollment.subject.name,
            'credits': enrollment.subject.credits,
            'theory_marks': None,
            'practical_marks': None,
            'total_marks': None,
            'grade': None,
            'grade_points': None,
            'is_passed': False,
            'exam_date': None
        }
        
        if hasattr(enrollment, 'grade'):
            grade = enrollment.grade
            grade_data.update({
                'theory_marks': str(grade.theory_marks) if grade.theory_marks else '-',
                'practical_marks': str(grade.practical_marks) if grade.practical_marks else '-',
                'total_marks': str(grade.total_marks) if grade.total_marks else '-',
                'grade': grade.grade or '-',
                'grade_points': str(grade.grade_points) if grade.grade_points else '-',
                'is_passed': grade.is_passed,
                'exam_date': grade.exam_date.strftime('%Y-%m-%d') if grade.exam_date else '-'
            })
        else:
            grade_data.update({
                'theory_marks': '-',
                'practical_marks': '-',
                'total_marks': '-',
                'grade': '-',
                'grade_points': '-',
                'is_passed': False,
                'exam_date': '-'
            })
        
        pdf_data.append(grade_data)
    
    return JsonResponse({
        'student': {
            'student_id': student.student_id,
            'full_name': student.user.get_full_name(),
            'course': student.course.name,
            'department': student.course.department.name,
            'current_semester': student.current_semester,
            'current_year': student.current_year,
            'admission_date': student.admission_date.strftime('%Y-%m-%d')
        },
        'performance_data': pdf_data
    })

# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Subject, Course
from .forms import SubjectForm

def subject_list(request):
    """List all subjects with filtering options"""
    subjects = Subject.objects.select_related('course', 'course__department').all()
    
    # Get filter parameters
    course_id = request.GET.get('course')
    year = request.GET.get('year')
    semester = request.GET.get('semester')
    search = request.GET.get('search')
    
    # Apply filters
    if course_id:
        subjects = subjects.filter(course_id=course_id)
    
    if year:
        subjects = subjects.filter(year=year)
    
    if semester:
        subjects = subjects.filter(semester=semester)
    
    if search:
        subjects = subjects.filter(
            Q(name__icontains=search) | 
            Q(code__icontains=search) |
            Q(course__name__icontains=search)
        )
    
    # Order by course, year, semester
    subjects = subjects.order_by('course__name', 'year', 'semester', 'name')
    
    # Pagination
    paginator = Paginator(subjects, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get options for filters
    courses = Course.objects.filter(is_active=True).order_by('name')
    years = Subject.objects.values_list('year', flat=True).distinct().order_by('year')
    semesters = Subject.objects.values_list('semester', flat=True).distinct().order_by('semester')
    
    context = {
        'page_obj': page_obj,
        'courses': courses,
        'years': years,
        'semesters': semesters,
        'current_course': course_id,
        'current_year': year,
        'current_semester': semester,
        'search_query': search,
    }
    
    return render(request, 'subjects/subject_list.html', context)

def subject_detail(request, pk):
    """Display detailed view of a subject"""
    subject = get_object_or_404(Subject.objects.select_related('course', 'course__department'), pk=pk)
    
    # Get prerequisites and subjects that have this as prerequisite
    prerequisites = subject.prerequisites.all()
    required_for = Subject.objects.filter(prerequisites=subject)
    
    context = {
        'subject': subject,
        'prerequisites': prerequisites,
        'required_for': required_for,
    }
    
    return render(request, 'subjects/subject_detail.html', context)

def subject_add(request):
    """Add a new subject"""
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f'Subject "{subject.name}" has been added successfully.')
            return redirect('subject_detail', pk=subject.pk)
    else:
        form = SubjectForm()
    
    context = {
        'form': form,
        'title': 'Add New Subject',
        'action': 'Add',
    }
    
    return render(request, 'subjects/subject_form.html', context)

def subject_update(request, pk):
    """Update an existing subject"""
    subject = get_object_or_404(Subject, pk=pk)
    
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f'Subject "{subject.name}" has been updated successfully.')
            return redirect('subject_detail', pk=subject.pk)
    else:
        form = SubjectForm(instance=subject)
    
    context = {
        'form': form,
        'subject': subject,
        'title': f'Update {subject.name}',
        'action': 'Update',
    }
    
    return render(request, 'subjects/subject_form.html', context)

def subject_delete(request, pk):
    """Delete a subject"""
    subject = get_object_or_404(Subject, pk=pk)
    
    if request.method == 'POST':
        subject_name = subject.name
        subject.delete()
        messages.success(request, f'Subject "{subject_name}" has been deleted successfully.')
        return redirect('subject_list')
    
    context = {
        'subject': subject,
    }
    
    return render(request, 'subjects/subject_confirm_delete.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.urls import reverse
from .models import AcademicYear, Semester

@login_required
def academic_year_management(request):
    """Display academic years and semesters management page"""
    academic_years = AcademicYear.objects.all().order_by('-year')
    
    context = {
        'academic_years': academic_years,
    }
    
    return render(request, 'admin/academic_year_management.html', context)

@login_required
def create_academic_year(request):
    """Create a new academic year"""
    if request.method == 'POST':
        year = request.POST.get('year')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_current = request.POST.get('is_current') == 'on'
        
        try:
            with transaction.atomic():
                # If this is set as current, make all others non-current
                if is_current:
                    AcademicYear.objects.filter(is_current=True).update(is_current=False)
                
                academic_year = AcademicYear.objects.create(
                    year=year,
                    start_date=start_date,
                    end_date=end_date,
                    is_current=is_current
                )
                
                messages.success(request, f'Academic year {year} created successfully!')
                
        except Exception as e:
            messages.error(request, f'Error creating academic year: {str(e)}')
    
    return redirect('academic_year_management')

@login_required
def edit_academic_year(request, year_id):
    """Edit an existing academic year"""
    academic_year = get_object_or_404(AcademicYear, id=year_id)
    
    if request.method == 'POST':
        year = request.POST.get('year')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_current = request.POST.get('is_current') == 'on'
        
        try:
            with transaction.atomic():
                # If this is set as current, make all others non-current
                if is_current:
                    AcademicYear.objects.exclude(id=year_id).filter(is_current=True).update(is_current=False)
                
                academic_year.year = year
                academic_year.start_date = start_date
                academic_year.end_date = end_date
                academic_year.is_current = is_current
                academic_year.save()
                
                messages.success(request, f'Academic year {year} updated successfully!')
                
        except Exception as e:
            messages.error(request, f'Error updating academic year: {str(e)}')
    
    return redirect('academic_year_management')

@login_required
def toggle_current_year(request, year_id):
    """Toggle current status of an academic year"""
    academic_year = get_object_or_404(AcademicYear, id=year_id)
    
    if request.method == 'POST':
        is_current = request.POST.get('is_current') == 'on'
        
        try:
            with transaction.atomic():
                if is_current:
                    # Make all others non-current
                    AcademicYear.objects.exclude(id=year_id).update(is_current=False)
                    # Also make all semesters in other years non-current
                    Semester.objects.exclude(academic_year_id=year_id).update(is_current=False)
                
                academic_year.is_current = is_current
                academic_year.save()
                
                status = 'current' if is_current else 'non-current'
                messages.success(request, f'Academic year {academic_year.year} set as {status}!')
                
        except Exception as e:
            messages.error(request, f'Error updating academic year status: {str(e)}')
    
    return redirect('academic_year_management')

@login_required
def create_semester(request, year_id):
    """Create a new semester for an academic year"""
    academic_year = get_object_or_404(AcademicYear, id=year_id)
    
    if request.method == 'POST':
        semester_number = request.POST.get('semester_number')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_current = request.POST.get('is_current') == 'on'
        
        try:
            with transaction.atomic():
                # Check if semester already exists
                if Semester.objects.filter(academic_year=academic_year, semester_number=semester_number).exists():
                    messages.error(request, f'Semester {semester_number} already exists for {academic_year.year}!')
                    return redirect('academic_year_management')
                
                # If this is set as current, make all others non-current
                if is_current:
                    Semester.objects.filter(is_current=True).update(is_current=False)
                    # Also make the academic year current if semester is current
                    if not academic_year.is_current:
                        AcademicYear.objects.filter(is_current=True).update(is_current=False)
                        academic_year.is_current = True
                        academic_year.save()
                
                semester = Semester.objects.create(
                    academic_year=academic_year,
                    semester_number=semester_number,
                    start_date=start_date,
                    end_date=end_date,
                    is_current=is_current
                )
                
                messages.success(request, f'Semester {semester_number} created successfully for {academic_year.year}!')
                
        except Exception as e:
            messages.error(request, f'Error creating semester: {str(e)}')
    
    return redirect('academic_year_management')

@login_required
def edit_semester(request, semester_id):
    """Edit an existing semester"""
    semester = get_object_or_404(Semester, id=semester_id)
    
    if request.method == 'POST':
        semester_number = request.POST.get('semester_number')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_current = request.POST.get('is_current') == 'on'
        
        try:
            with transaction.atomic():
                # Check if semester number already exists (excluding current semester)
                if Semester.objects.filter(
                    academic_year=semester.academic_year, 
                    semester_number=semester_number
                ).exclude(id=semester_id).exists():
                    messages.error(request, f'Semester {semester_number} already exists for {semester.academic_year.year}!')
                    return redirect('academic_year_management')
                
                # If this is set as current, make all others non-current
                if is_current:
                    Semester.objects.exclude(id=semester_id).filter(is_current=True).update(is_current=False)
                    # Also make the academic year current if semester is current
                    if not semester.academic_year.is_current:
                        AcademicYear.objects.filter(is_current=True).update(is_current=False)
                        semester.academic_year.is_current = True
                        semester.academic_year.save()
                
                semester.semester_number = semester_number
                semester.start_date = start_date
                semester.end_date = end_date
                semester.is_current = is_current
                semester.save()
                
                messages.success(request, f'Semester {semester_number} updated successfully!')
                
        except Exception as e:
            messages.error(request, f'Error updating semester: {str(e)}')
    
    return redirect('academic_year_management')

@login_required
def toggle_current_semester(request, semester_id):
    """Toggle current status of a semester"""
    semester = get_object_or_404(Semester, id=semester_id)
    
    if request.method == 'POST':
        is_current = request.POST.get('is_current') == 'on'
        
        try:
            with transaction.atomic():
                if is_current:
                    # Make all other semesters non-current
                    Semester.objects.exclude(id=semester_id).update(is_current=False)
                    # Make the academic year current as well
                    if not semester.academic_year.is_current:
                        AcademicYear.objects.filter(is_current=True).update(is_current=False)
                        semester.academic_year.is_current = True
                        semester.academic_year.save()
                
                semester.is_current = is_current
                semester.save()
                
                status = 'current' if is_current else 'non-current'
                messages.success(request, f'Semester {semester.semester_number} set as {status}!')
                
        except Exception as e:
            messages.error(request, f'Error updating semester status: {str(e)}')
    
    return redirect('academic_year_management')

@login_required
def delete_semester(request, semester_id):
    """Delete a semester"""
    semester = get_object_or_404(Semester, id=semester_id)
    
    if request.method == 'POST':
        try:
            semester_info = f"Semester {semester.semester_number} for {semester.academic_year.year}"
            semester.delete()
            messages.success(request, f'{semester_info} deleted successfully!')
            
        except Exception as e:
            messages.error(request, f'Error deleting semester: {str(e)}')
    
    return redirect('academic_year_management')


# views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.db.models import Count, Q
from .models import (
    Hostel, HostelRoom, HostelBed, HostelBooking, 
    AcademicYear, Student, HostelRoomTransfer
)


@login_required
def hostel_overview(request):
    """Main hostel overview showing all hostels and academic years"""
    hostels = Hostel.objects.filter(is_active=True).order_by('name')
    academic_years = AcademicYear.objects.all().order_by('-year')
    
    # Get booking statistics
    hostel_stats = {}
    for hostel in hostels:
        stats = {
            'total_rooms': hostel.total_rooms,
            'available_rooms': hostel.available_rooms,
            'occupied_rooms': hostel.occupied_rooms,
            'total_beds': hostel.total_beds,
            'available_beds': hostel.available_beds,
            'occupied_beds': hostel.occupied_beds,
        }
        hostel_stats[hostel.id] = stats
    
    context = {
        'hostels': hostels,
        'academic_years': academic_years,
        'hostel_stats': hostel_stats,
    }
    return render(request, 'hostel/overview.html', context)


@login_required
def hostel_year_view(request, year_id):
    """View hostels for a specific academic year"""
    academic_year = get_object_or_404(AcademicYear, id=year_id)
    hostels = Hostel.objects.filter(is_active=True).order_by('name')
    
    # Get booking statistics for this year
    hostel_data = []
    for hostel in hostels:
        # Get bookings for this hostel in this academic year
        bookings = HostelBooking.objects.filter(
            bed__room__hostel=hostel,
            academic_year=academic_year
        )
        
        approved_bookings = bookings.filter(status='approved')
        pending_bookings = bookings.filter(status='pending')
        
        hostel_info = {
            'hostel': hostel,
            'total_bookings': bookings.count(),
            'approved_bookings': approved_bookings.count(),
            'pending_bookings': pending_bookings.count(),
            'available_beds': hostel.available_beds,
            'occupied_beds': hostel.occupied_beds,
        }
        hostel_data.append(hostel_info)
    
    context = {
        'academic_year': academic_year,
        'hostel_data': hostel_data,
    }
    return render(request, 'hostel/year_view.html', context)


@login_required
def hostel_rooms_view(request, hostel_id, year_id):
    """View all rooms in a specific hostel for a specific year"""
    hostel = get_object_or_404(Hostel, id=hostel_id, is_active=True)
    academic_year = get_object_or_404(AcademicYear, id=year_id)
    
    # Get all rooms for this hostel
    rooms = HostelRoom.objects.filter(hostel=hostel).order_by('floor', 'room_number')
    
    room_data = []
    for room in rooms:
        # Get bookings for this room in this academic year
        bookings = HostelBooking.objects.filter(
            bed__room=room,
            academic_year=academic_year
        ).select_related('student__user', 'bed')
        
        approved_bookings = bookings.filter(status='approved')
        pending_bookings = bookings.filter(status='pending')
        
        room_info = {
            'room': room,
            'total_beds': room.total_beds,
            'available_beds': room.available_beds,
            'occupied_beds': room.occupied_beds,
            'approved_bookings': approved_bookings.count(),
            'pending_bookings': pending_bookings.count(),
            'bookings': bookings.order_by('bed__bed_number'),
        }
        room_data.append(room_info)
    
    context = {
        'hostel': hostel,
        'academic_year': academic_year,
        'room_data': room_data,
    }
    return render(request, 'hostel/rooms_view.html', context)


@login_required
def room_detail_view(request, room_id, year_id):
    """Detailed view of a specific room showing all beds and bookings"""
    room = get_object_or_404(HostelRoom, id=room_id)
    academic_year = get_object_or_404(AcademicYear, id=year_id)
    
    # Get all beds in this room
    beds = HostelBed.objects.filter(room=room).order_by('bed_number')
    
    bed_data = []
    for bed in beds:
        # Get booking for this bed in this academic year
        booking = HostelBooking.objects.filter(
            bed=bed,
            academic_year=academic_year
        ).select_related('student__user').first()
        
        # Get all bookings history for this bed
        booking_history = HostelBooking.objects.filter(
            bed=bed,
            academic_year=academic_year
        ).select_related('student__user').order_by('-booking_date')
        
        bed_info = {
            'bed': bed,
            'current_booking': booking,
            'booking_history': booking_history,
            'is_available': bed.is_available,
            'is_maintenance': bed.is_maintenance,
        }
        bed_data.append(bed_info)
    
    context = {
        'room': room,
        'academic_year': academic_year,
        'bed_data': bed_data,
    }
    return render(request, 'hostel/admin-room_detail.html', context)


@login_required
def all_bookings_view(request):
    """View all bookings across all hostels and years"""
    # Get filter parameters
    hostel_id = request.GET.get('hostel')
    year_id = request.GET.get('year')
    status = request.GET.get('status')
    
    # Base queryset
    bookings = HostelBooking.objects.select_related(
        'student__user', 'bed__room__hostel', 'academic_year'
    ).order_by('-booking_date')
    
    # Apply filters
    if hostel_id:
        bookings = bookings.filter(bed__room__hostel__id=hostel_id)
    if year_id:
        bookings = bookings.filter(academic_year__id=year_id)
    if status:
        bookings = bookings.filter(status=status)
    
    # Get filter options
    hostels = Hostel.objects.filter(is_active=True).order_by('name')
    academic_years = AcademicYear.objects.all().order_by('-year')
    
    # Pagination (optional)
    from django.core.paginator import Paginator
    paginator = Paginator(bookings, 50)  # Show 50 bookings per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'bookings': page_obj,
        'hostels': hostels,
        'academic_years': academic_years,
        'current_filters': {
            'hostel': hostel_id,
            'year': year_id,
            'status': status,
        },
        'status_choices': HostelBooking.BOOKING_STATUS,
    }
    return render(request, 'hostel/all_bookings.html', context)


@login_required
def booking_detail_view(request, booking_id):
    """Detailed view of a specific booking"""
    booking = get_object_or_404(
        HostelBooking.objects.select_related(
            'student__user', 'bed__room__hostel', 'academic_year', 'approved_by'
        ),
        id=booking_id
    )
    
    # Get related transfers
    transfers = HostelRoomTransfer.objects.filter(
        student=booking.student
    ).order_by('-created_at')
    
    # Get payment history if exists
    payments = booking.fee_payments.all().order_by('-payment_date')
    
    context = {
        'booking': booking,
        'transfers': transfers,
        'payments': payments,
    }
    return render(request, 'hostel/booking_detail.html', context)


@login_required
def student_hostel_history(request, student_id):
    """View all hostel bookings for a specific student"""
    student = get_object_or_404(Student, id=student_id)
    
    # Get all bookings for this student
    bookings = HostelBooking.objects.filter(
        student=student
    ).select_related(
        'bed__room__hostel', 'academic_year'
    ).order_by('-booking_date')
    
    # Get transfers
    transfers = HostelRoomTransfer.objects.filter(
        student=student
    ).order_by('-created_at')
    
    context = {
        'student': student,
        'bookings': bookings,
        'transfers': transfers,
    }
    return render(request, 'hostel/student_history.html', context)



from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Prefetch
from .models import Student, Enrollment, Course, AcademicYear, Semester, Subject

@login_required
def enrollment_list_view(request):
    """
    Display grouped enrollments by student with filters and search
    """
    # Get filter parameters
    search_query = request.GET.get('search', '')
    course_filter = request.GET.get('course', '')
    year_filter = request.GET.get('year', '')
    semester_filter = request.GET.get('semester', '')
    status_filter = request.GET.get('status', '')
    
    # Base queryset - get students with their enrollments
    students_query = Student.objects.select_related(
        'user', 'course', 'course__department'
    ).prefetch_related(
        Prefetch(
            'enrollments',
            queryset=Enrollment.objects.select_related(
                'subject', 'semester', 'semester__academic_year'
            ).filter(is_active=True).order_by(
                'semester__academic_year__year', 'semester__semester_number'
            )
        )
    ).annotate(
        total_enrollments=Count('enrollments', filter=Q(enrollments__is_active=True))
    ).filter(total_enrollments__gt=0)
    
    # Apply filters
    if search_query:
        students_query = students_query.filter(
            Q(student_id__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )
    
    if course_filter:
        students_query = students_query.filter(course_id=course_filter)
    
    if status_filter:
        students_query = students_query.filter(status=status_filter)
    
    if year_filter:
        students_query = students_query.filter(
            enrollments__semester__academic_year_id=year_filter
        )
    
    if semester_filter:
        students_query = students_query.filter(
            enrollments__semester_id=semester_filter
        )
    
    # Get data for filter dropdowns
    courses = Course.objects.filter(is_active=True).order_by('name')
    academic_years = AcademicYear.objects.all().order_by('-year')
    semesters = Semester.objects.select_related('academic_year').order_by(
        '-academic_year__year', 'semester_number'
    )
    
    # Pagination
    paginator = Paginator(students_query.distinct(), 10)
    page_number = request.GET.get('page')
    students = paginator.get_page(page_number)
    
    context = {
        'students': students,
        'courses': courses,
        'academic_years': academic_years,
        'semesters': semesters,
        'search_query': search_query,
        'course_filter': course_filter,
        'year_filter': year_filter,
        'semester_filter': semester_filter,
        'status_filter': status_filter,
        'status_choices': Student.STATUS_CHOICES,
    }
    
    return render(request, 'enrollments/enrollment_list.html', context)


@login_required
def student_enrollment_detail_view(request, student_id):
    """
    Display detailed enrollment information for a specific student
    organized by academic year and semester
    """
    student = get_object_or_404(
        Student.objects.select_related('user', 'course', 'course__department'),
        student_id=student_id
    )
    
    # Get all enrollments for this student grouped by academic year and semester
    enrollments = Enrollment.objects.filter(
        student=student, is_active=True
    ).select_related(
        'subject', 'semester', 'semester__academic_year'
    ).order_by(
        'semester__academic_year__year',
        'semester__semester_number',
        'subject__name'
    )
    
    # Group enrollments by academic year and semester
    enrollment_data = {}
    total_credits = 0
    
    for enrollment in enrollments:
        year = enrollment.semester.academic_year.year
        sem_num = enrollment.semester.semester_number
        
        if year not in enrollment_data:
            enrollment_data[year] = {}
        
        if sem_num not in enrollment_data[year]:
            enrollment_data[year][sem_num] = {
                'semester': enrollment.semester,
                'enrollments': [],
                'total_credits': 0,
                'total_subjects': 0
            }
        
        enrollment_data[year][sem_num]['enrollments'].append(enrollment)
        enrollment_data[year][sem_num]['total_credits'] += enrollment.subject.credits
        enrollment_data[year][sem_num]['total_subjects'] += 1
        total_credits += enrollment.subject.credits
    
    # Calculate summary statistics
    total_subjects = enrollments.count()
    total_years = len(enrollment_data)
    
    context = {
        'student': student,
        'enrollment_data': enrollment_data,
        'total_subjects': total_subjects,
        'total_credits': total_credits,
        'total_years': total_years,
    }
    
    return render(request, 'enrollments/student_enrollment_detail.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .models import Student, FeePayment, FeeStructure, AcademicYear, Course
import json
from decimal import Decimal
from datetime import datetime

@login_required
def fee_record_list(request):
    """
    View to display list of all students with their fee payment summary
    """
    search_query = request.GET.get('search', '')
    course_filter = request.GET.get('course', '')
    year_filter = request.GET.get('year', '')
    status_filter = request.GET.get('status', '')
    
    # Get all students with fee payment summary
    students = Student.objects.select_related('user', 'course').filter(
        status='active'
    )
    
    # Apply filters
    if search_query:
        students = students.filter(
            Q(student_id__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )
    
    if course_filter:
        students = students.filter(course_id=course_filter)
    
    if year_filter:
        students = students.filter(current_year=year_filter)
    
    # Calculate fee payment summary for each student
    student_fee_data = []
    for student in students:
        # Get total fees paid
        total_paid = FeePayment.objects.filter(
            student=student,
            payment_status='completed'
        ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
        
        # Get current semester fee structure
        current_fee_structure = FeeStructure.objects.filter(
            course=student.course,
            semester=student.current_semester
        ).first()
        
        # Calculate outstanding amount
        if current_fee_structure:
            total_due = current_fee_structure.total_fee()
            outstanding = max(0, total_due - total_paid)
            fee_status = 'Paid' if outstanding == 0 else 'Pending'
        else:
            total_due = 0
            outstanding = 0
            fee_status = 'No Structure'
        
        student_fee_data.append({
            'student': student,
            'total_paid': total_paid,
            'total_due': total_due,
            'outstanding': outstanding,
            'fee_status': fee_status
        })
    
    # Apply status filter
    if status_filter:
        if status_filter == 'paid':
            student_fee_data = [s for s in student_fee_data if s['outstanding'] == 0]
        elif status_filter == 'pending':
            student_fee_data = [s for s in student_fee_data if s['outstanding'] > 0]
        elif status_filter == 'no_structure':
            student_fee_data = [s for s in student_fee_data if s['fee_status'] == 'No Structure']
    
    # Pagination
    paginator = Paginator(student_fee_data, 20)
    page_number = request.GET.get('page')
    students_page = paginator.get_page(page_number)
    
    # Get filter options
    courses = Course.objects.filter(is_active=True)
    years = range(1, 6)  # 1 to 5 years
    
    context = {
        'students': students_page,
        'search_query': search_query,
        'course_filter': course_filter,
        'year_filter': year_filter,
        'status_filter': status_filter,
        'courses': courses,
        'years': years,
        'status_choices': [
            ('paid', 'Paid'),
            ('pending', 'Pending'),
            ('no_structure', 'No Fee Structure')
        ]
    }
    
    return render(request, 'fee/fee_record_list.html', context)


@login_required
def fee_record_detail(request, student_id):
    """
    View to display detailed fee records for a specific student
    with academic year and semester tabs
    """
    student = get_object_or_404(Student, student_id=student_id)
    
    # Get all academic years
    academic_years = AcademicYear.objects.all().order_by('-start_date')
    
    # Get fee payments for this student
    fee_payments = FeePayment.objects.filter(student=student).select_related(
        'fee_structure', 'fee_structure__academic_year'
    ).order_by('-payment_date')
    
    # Group payments by academic year and semester
    payment_data = {}
    for payment in fee_payments:
        year_key = payment.fee_structure.academic_year.year
        semester_key = payment.fee_structure.semester
        
        if year_key not in payment_data:
            payment_data[year_key] = {}
        if semester_key not in payment_data[year_key]:
            payment_data[year_key][semester_key] = {
                'payments': [],
                'total_paid': 0,
                'fee_structure': payment.fee_structure
            }
        
        payment_data[year_key][semester_key]['payments'].append(payment)
        if payment.payment_status == 'completed':
            payment_data[year_key][semester_key]['total_paid'] += payment.amount_paid
    
    # Get fee structures for the student's course
    fee_structures = FeeStructure.objects.filter(
        course=student.course
    ).select_related('academic_year').order_by('-academic_year__start_date', 'semester')
    
    # Group fee structures by academic year
    structure_data = {}
    for structure in fee_structures:
        year_key = structure.academic_year.year
        if year_key not in structure_data:
            structure_data[year_key] = {}
        structure_data[year_key][structure.semester] = structure
    
    # Calculate payment summary for each year/semester and prepare for template
    summary_data_list = []
    for year_key in structure_data:
        year_semesters = []
        for semester in structure_data[year_key]:
            structure = structure_data[year_key][semester]
            paid_amount = 0
            
            if year_key in payment_data and semester in payment_data[year_key]:
                paid_amount = payment_data[year_key][semester]['total_paid']
            
            outstanding = max(0, structure.total_fee() - paid_amount)
            
            semester_info = {
                'semester_number': semester,
                'structure': structure,
                'paid': paid_amount,
                'outstanding': outstanding,
                'payments': payment_data.get(year_key, {}).get(semester, {}).get('payments', [])
            }
            year_semesters.append(semester_info)
        
        # Find the academic year object for this year
        academic_year_obj = next((ay for ay in academic_years if ay.year == year_key), None)
        
        summary_data_list.append({
            'academic_year': academic_year_obj,
            'semesters': year_semesters
        })
    
    # Sort by academic year (most recent first)
    summary_data_list.sort(key=lambda x: x['academic_year'].start_date if x['academic_year'] else datetime.min.date(), reverse=True)
    
    # Get payment methods and status choices for the form
    payment_methods = FeePayment.PAYMENT_METHODS
    payment_status_choices = FeePayment.PAYMENT_STATUS
    
    context = {
        'student': student,
        'academic_years': academic_years,
        'summary_data_list': summary_data_list,  # This replaces summary_data
        'payment_methods': payment_methods,
        'payment_status_choices': payment_status_choices,
        'recent_payments': fee_payments[:10]  # Last 10 payments for quick view
    }
    
    return render(request, 'fee/fee_record_detail.html', context)


@login_required
@csrf_exempt
def add_fee_payment(request):
    """
    AJAX view to add a new fee payment record
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            student_id = data.get('student_id')
            fee_structure_id = data.get('fee_structure_id')
            amount_paid = Decimal(str(data.get('amount_paid', 0)))
            payment_method = data.get('payment_method')
            payment_date = data.get('payment_date')
            transaction_id = data.get('transaction_id', '')
            remarks = data.get('remarks', '')
            
            # Validate required fields
            if not all([student_id, fee_structure_id, amount_paid, payment_method, payment_date]):
                return JsonResponse({
                    'success': False,
                    'message': 'All required fields must be filled.'
                })
            
            # Get student and fee structure
            student = get_object_or_404(Student, student_id=student_id)
            fee_structure = get_object_or_404(FeeStructure, id=fee_structure_id)
            
            # Generate receipt number
            last_payment = FeePayment.objects.filter(
                student=student
            ).order_by('-id').first()
            
            if last_payment:
                last_receipt = last_payment.receipt_number
                receipt_num = int(last_receipt.split('-')[-1]) + 1
            else:
                receipt_num = 1
            
            receipt_number = f"RCP-{student.student_id}-{receipt_num:04d}"
            
            # Create payment record
            payment = FeePayment.objects.create(
                student=student,
                fee_structure=fee_structure,
                receipt_number=receipt_number,
                amount_paid=amount_paid,
                payment_date=datetime.strptime(payment_date, '%Y-%m-%d').date(),
                payment_method=payment_method,
                payment_status='completed',  # Default to completed
                transaction_id=transaction_id,
                remarks=remarks
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Fee payment recorded successfully!',
                'receipt_number': receipt_number,
                'payment_id': payment.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })


@login_required
def get_fee_structure(request):
    """
    AJAX view to get fee structure details for a specific course and semester
    """
    course_id = request.GET.get('course_id')
    academic_year_id = request.GET.get('academic_year_id')
    semester = request.GET.get('semester')
    
    if not all([course_id, academic_year_id, semester]):
        return JsonResponse({'success': False, 'message': 'Missing parameters'})
    
    try:
        fee_structure = FeeStructure.objects.get(
            course_id=course_id,
            academic_year_id=academic_year_id,
            semester=semester
        )
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': fee_structure.id,
                'tuition_fee': float(fee_structure.tuition_fee),
                'lab_fee': float(fee_structure.lab_fee),
                'library_fee': float(fee_structure.library_fee),
                'exam_fee': float(fee_structure.exam_fee),
                'development_fee': float(fee_structure.development_fee),
                'other_fee': float(fee_structure.other_fee),
                'total_fee': float(fee_structure.total_fee())
            }
        })
        
    except FeeStructure.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Fee structure not found for the selected criteria.'
        })