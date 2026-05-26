# Register your models here.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import College, Department, StudentUser, FacultyUser, HODUser

# 1. College & Department Setup
class DepartmentInline(admin.TabularInline):
    model = Department
    extra = 1

class CollegeAdmin(admin.ModelAdmin):
    inlines = [DepartmentInline]
    list_display = ('name', 'website')

# 2. Custom Admin Views for Roles
class StudentUserAdmin(UserAdmin):
    # Only show users who are Students
    def get_queryset(self, request):
        return super().get_queryset(request).filter(role='STUDENT')
    
    list_display = ('username', 'email', 'is_verified', 'date_joined')
    list_filter = ('is_verified', 'date_joined')
    search_fields = ('username', 'email')

class HODUserAdmin(UserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(role='HOD')
    
    list_display = ('username', 'email', 'is_verified')
    list_editable = ('is_verified',)  # <--- THIS ALLOWS EDITING IN THE LIST
    list_filter = ('is_verified',)

class FacultyUserAdmin(UserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(role='FACULTY')
    
    list_display = ('username', 'email', 'is_verified')
    list_editable = ('is_verified',)  # <--- THIS ALLOWS EDITING IN THE LIST
    list_filter = ('is_verified',)

# 3. Register everything
admin.site.register(College, CollegeAdmin)
admin.site.register(Department)
admin.site.register(StudentUser, StudentUserAdmin)
admin.site.register(FacultyUser, FacultyUserAdmin)
admin.site.register(HODUser, HODUserAdmin)