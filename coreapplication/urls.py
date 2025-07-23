from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.student_login, name='student_login'),
    path('register/', views.student_register, name='student_register'),
    path('logout/', views.student_logout, name='student_logout'),
    
    # Dashboard
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    
    # Profile
    path('profile/', views.student_profile, name='student_profile'),
    path('change-password/', views.change_password, name='change_password'),
    
    # Academic
    path('subjects/', views.student_subjects, name='student_subjects'),
    path('timetable/', views.student_timetable, name='student_timetable'),
    path('grades/', views.student_grades, name='student_grades'),
    path('attendance/', views.student_attendance, name='student_attendance'),
    
    # Examination
    path('exam-schedule/', views.student_exam_schedule, name='student_exam_schedule'),
    path('exam-results/', views.student_exam_results, name='student_exam_results'),
    
    # Finance
    path('fees/', views.student_fees, name='student_fees'),
    path('fees/history/', views.fee_payment_history, name='fee_payment_history'),
    
    # Library
    path('library/', views.student_library, name='student_library'),
    
    # Placement
    path('placements/', views.student_placements, name='student_placements'),
    path('placements/apply/<int:drive_id>/', views.apply_placement, name='apply_placement'),
    
    # Events
    path('events/', views.student_events, name='student_events'),
    path('events/register/<int:event_id>/', views.register_event, name='register_event'),
    path('comments/', views.student_comments, name='student_comments'),
    path('faqs/', views.faqs , name="faqs"),
    path('virtual_assistant', views.virtual_assistant , name="virtual_assistant"),
    path('process-query/', views.process_assistant_query, name='process_assistant_query'),
    
    # Documents
    path('documents/', views.student_documents, name='student_documents'),
    
    # Notifications
    path('notifications/', views.student_notifications, name='student_notifications'),

    path('news/', views.student_news, name='student_news'),
    path('clubs/', views.student_clubs, name='student_clubs'),
    path('clubs/join/<int:club_id>/', views.join_club, name='join_club'),
    path('clubs/leave/<int:club_id>/', views.leave_club, name='leave_club'),
    path('club-events/', views.club_events, name='club_events'),
    path('club-events/<int:club_id>/', views.club_events, name='club_events_detail'),

    # Student Reporting

    path('reporting/', views.student_reporting_list, name='student_reporting_list'),
    path('reporting/current/', views.student_report_current_semester, name='student_report_current_semester'),
    path('student/transcript/', views.student_transcript, name='student_transcript'),
    path('admin-marks-entry/', views.admin_marks_entry, name='admin_marks_entry'),
    path('admin-student-info/', views.get_student_info, name='get_student_info'),

    
    # Admin URLs for reporting
    path('admin/reporting/', views.admin_reporting_overview, name='admin_reporting_overview'),
  
    # Hostel Booking
    path('hostel/', views.hostel_booking_dashboard, name='hostel_booking_dashboard'),
    path('hostel/list/', views.hostel_list, name='hostel_list'),
    path('hostel/<int:hostel_id>/', views.hostel_detail, name='hostel_detail'),
    path('hostel/room/<int:room_id>/', views.room_detail, name='room_detail'),
    path('hostel/bed/<int:bed_id>/apply/', views.apply_hostel_booking, name='apply_hostel_booking'),
    path('hostel/room/<int:room_id>/beds/', views.get_room_beds, name='get_room_beds'),
    path('hostel/history/', views.booking_history, name='booking_history'),
    path('hostel/booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('hostel/quick-booking/', views.quick_bed_booking, name='quick_bed_booking'),

    # Main hostel overview
    path('hoste/overview/', views.hostel_overview, name='overview'),
    path('year/<int:year_id>/', views.hostel_year_view, name='year_view'),
    path('hostel/<int:hostel_id>/year/<int:year_id>/', views.hostel_rooms_view, name='rooms_view'),
    path('room/<int:room_id>/year/<int:year_id>/', views.room_detail_view, name='room_detail'),
    path('bookings/', views.all_bookings_view, name='all_bookings'),
    path('booking/<int:booking_id>/', views.booking_detail_view, name='booking_detail'),
    path('student/<int:student_id>/history/', views.student_hostel_history, name='student_history'),

    # Admin Hostel Management
    path('admin/hostel/bookings/', views.admin_hostel_bookings, name='admin_hostel_bookings'),
    path('admin/hostel/booking/<int:booking_id>/approve/', views.admin_approve_booking, name='admin_approve_booking'),
    path('admin/hostel/booking/<int:booking_id>/reject/', views.admin_reject_booking, name='admin_reject_booking'),

    # Admin authentication URLs
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('admin-logout/', views.admin_logout_view, name='admin_logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('students/', views.student_list, name='student_list'),
    path('students/create/', views.student_create, name='student_create'),
    path('students/<str:student_id>/', views.student_detail, name='student_detail'),
    path('students/<str:student_id>/edit/', views.student_update, name='student_update'),
    path('students/<str:student_id>/delete/', views.student_delete, name='student_delete'),

    path('faculty/', views.faculty_list, name='faculty_list'),
    path('faculty/create/', views.faculty_create, name='faculty_create'),
    path('faculty/<str:employee_id>/', views.faculty_detail, name='faculty_detail'),
    path('faculty/<str:employee_id>/update/', views.faculty_update, name='faculty_update'),
    path('faculty/<str:employee_id>/delete/', views.faculty_delete, name='faculty_delete'),

    # Schedule CRUD operations
    path('schedule/', views.schedule_list, name='schedule_list'),
    path('schedule/create/', views.schedule_create, name='schedule_create'),
    path('schedule/<int:schedule_id>/', views.schedule_detail, name='schedule_detail'),
    path('schedule/<int:schedule_id>/update/', views.schedule_update, name='schedule_update'),
    path('schedule/<int:schedule_id>/delete/', views.schedule_delete, name='schedule_delete'),
    
    # Timetable view
    path('schedule/timetable/', views.schedule_timetable, name='admin_schedule_timetable'),
    
    # AJAX endpoints
    path('api/subjects-by-course/', views.get_subjects_by_course, name='get_subjects_by_course'),

    # Course List View
    path('courses/', views.course_list_view, name='course_list'),
    path('courses/<int:course_id>/', views.course_detail_view, name='course_detail'),
    path('api/courses/<int:course_id>/subjects/', views.get_course_subjects_json, name='course_subjects_api'),
    path('courses/add/', views.add_course_view, name='add_course'),
    path('courses/<int:course_id>/edit/', views.edit_course_view, name='edit_course'),
    path('courses/<int:course_id>/delete/', views.delete_course_view, name='delete_course'),
    path('courses/check_code/', views.check_course_code, name='check_course_code'),

    # Student Performance URLs
    path('student-performance/<str:student_id>/', views.student_performance_view, name='student_performance'),
    path('student-performance-pdf/<str:student_id>/', views.student_performance_pdf_data, name='student_performance_pdf_data'),

    path('admin-subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/', views.subject_add, name='subject_add'),
    path('subjects/<int:pk>/', views.subject_detail, name='subject_detail'),
    path('subjects/<int:pk>/edit/', views.subject_update, name='subject_update'),
    path('subjects/<int:pk>/delete/', views.subject_delete, name='subject_delete'),

    # Academic Year Management
    path('admin-academic-years/', views.academic_year_management, name='academic_year_management'),
    path('admin-create-academic-year/', views.create_academic_year, name='create_academic_year'),
    path('admin-edit-academic-year/<int:year_id>/', views.edit_academic_year, name='edit_academic_year'),
    path('admin-toggle-current-year/<int:year_id>/', views.toggle_current_year, name='toggle_current_year'),
    
    # Semester Management
    path('admin-create-semester/<int:year_id>/', views.create_semester, name='create_semester'),
    path('admin-edit-semester/<int:semester_id>/', views.edit_semester, name='edit_semester'),
    path('admin-toggle-current-semester/<int:semester_id>/', views.toggle_current_semester, name='toggle_current_semester'),
    path('admin-delete-semester/<int:semester_id>/', views.delete_semester, name='delete_semester'),

    # Enrollment Management URLs
    path('enrollments/', views.enrollment_list_view, name='enrollment_list'),
    path('enrollments/student/<str:student_id>/', views.student_enrollment_detail_view, name='student_enrollment_detail'),

    path('records/', views.fee_record_list, name='fee_record_list'),
    path('records/<str:student_id>/', views.fee_record_detail, name='fee_record_detail'),
    path('payment/add/', views.add_fee_payment, name='add_fee_payment'),
    path('structure/get/', views.get_fee_structure, name='get_fee_structure'),

 ]
