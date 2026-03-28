"""
URL configuration for projy project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. Accounts App (Login/Signup)
    path('', include('accounts.urls')), 
    
    # 2. College App (HOD & Faculty Dashboards)
    path('college/', include('college.urls')),
    
    # 3. Students App (Student Dashboard & Portfolio)
    path('student/', include('students.urls')),
    
    # 4. Recruitment App (Recruiter Dashboard)
    path('recruitment/', include('recruitment.urls')),
    
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path('manifest.json', TemplateView.as_view(template_name="manifest.json", content_type="application/json")),
]

# This serves media files (images/zips) during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)