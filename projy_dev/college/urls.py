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
]