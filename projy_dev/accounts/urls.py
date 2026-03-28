from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('control-panel/', views.admin_control_panel, name='admin_control_panel'),
    path('signup/recruiter/', views.recruiter_signup, name='signup_recruiter'),
    path('signup/college/', views.college_signup, name='signup_college'),
    path('control-panel/', views.admin_control_panel, name='admin_control_panel'),
    path('notification/read/<int:notif_id>/', views.read_notification, name='read_notification'),
]