from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/hod/', views.hod_dashboard, name='hod_dashboard'),
    path('dashboard/faculty/', views.faculty_dashboard, name='faculty_dashboard'),
    path('approve/<int:user_id>/', views.approve_user, name='approve_user'),
    path('ajax/load-departments/', views.load_departments, name='ajax_load_departments'),
    path('approve-project/<int:project_id>/', views.approve_project, name='approve_project'),
    path('approve-semester/<int:student_id>/<str:action>/', views.approve_semester_change, name='approve_semester_change'),
    path('project/remark/<int:project_id>/', views.add_project_remark, name='add_project_remark'),
    path('dashboard/faculty/settings/', views.faculty_settings_update, name='faculty_settings_update'),
    path('dashboard/hod/settings/', views.hod_settings_update, name='hod_settings_update'),
    path('dashboard/hod/placements/add/', views.hod_add_placement, name='hod_add_placement'),
    path('dashboard/hod/placements/delete/<int:placement_id>/', views.hod_delete_placement, name='hod_delete_placement'),
    
    # NEW: Mentor Assignment URLs
    path('dashboard/hod/assign/manual/', views.manual_assign, name='manual_assign'),
    path('dashboard/hod/assign/auto/', views.auto_assign, name='auto_assign'),
]