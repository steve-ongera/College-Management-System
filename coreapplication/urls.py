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
    path('student/reporting/', views.student_reporting_dashboard, name='student_reporting_dashboard'),
    path('student/reporting/create/', views.create_student_report, name='create_student_report'),
    path('student/reporting/<int:report_id>/', views.report_detail, name='report_detail'),

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

    # Admin Hostel Management
    path('admin/hostel/bookings/', views.admin_hostel_bookings, name='admin_hostel_bookings'),
    path('admin/hostel/booking/<int:booking_id>/approve/', views.admin_approve_booking, name='admin_approve_booking'),
    path('admin/hostel/booking/<int:booking_id>/reject/', views.admin_reject_booking, name='admin_reject_booking'),

 ]