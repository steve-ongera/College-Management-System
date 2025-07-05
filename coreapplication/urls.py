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
]