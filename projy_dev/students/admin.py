# Register your models here.

from django.contrib import admin
from .models import StudentProfile, Project, ProjectLanguage, BlogPost

class ProjectLanguageInline(admin.TabularInline):
    model = ProjectLanguage
    extra = 1

class ProjectAdmin(admin.ModelAdmin):
    inlines = [ProjectLanguageInline]
    list_display = ('title', 'student', 'is_public', 'is_verified')
    list_filter = ('is_verified', 'is_public')

class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'college', 'department', 'enrollment_number')
    search_fields = ('user__username', 'enrollment_number')

admin.site.register(StudentProfile, StudentProfileAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectLanguage)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'is_private', 'created_at')
    list_filter = ('is_private', 'created_at')
    search_fields = ('title', 'content', 'student__user__username')
    date_hierarchy = 'created_at'