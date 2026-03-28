from django.urls import path
from . import views

urlpatterns = [
    # Dashboard & Projects
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('project/add/', views.add_project, name='add_project'),
    path('project/edit/<int:project_id>/', views.edit_project, name='edit_project'),
    path('project/delete/<int:project_id>/', views.delete_project, name='delete_project'),
    path('project/<int:project_id>/', views.project_detail, name='project_detail'),
    path('profile/<int:student_id>/', views.student_public_profile, name='student_public_profile'),
    # Portfolio & Resume
    path('my-portfolio/', views.live_portfolio, name='live_portfolio'),
    path('generate-resume/', views.generate_resume, name='generate_resume'),
    # Blogs
    path('blogs/manage/', views.manage_blogs, name='manage_blogs'),
    path('blogs/delete/<int:blog_id>/', views.delete_blog, name='delete_blog'),
    #Certificates
    path('certificates/manage/', views.manage_certificates, name='manage_certificates'),
    path('certificates/delete/<int:cert_id>/', views.delete_certificate, name='delete_certificate'),
    
    path('project/fixed/<int:project_id>/', views.mark_revision_done, name='mark_revision_done'),
    
    path('portfolio/builder/', views.portfolio_builder, name='portfolio_builder'),
    path('portfolio/live/', views.live_portfolio, name='live_portfolio'), # (Already exists)
    ]