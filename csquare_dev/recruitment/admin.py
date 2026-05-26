from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Company, RecruiterUser

class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'hr_manager')

class RecruiterUserAdmin(UserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(role='RECRUITER')
    
    list_display = ('username', 'email', 'company_managed', 'is_verified')
    list_editable = ('is_verified',) # <--- THIS ALLOWS EDITING IN THE LIST
    
    def company_managed(self, obj):
        return obj.company_managed.name if hasattr(obj, 'company_managed') else '-'

admin.site.register(Company, CompanyAdmin)
admin.site.register(RecruiterUser, RecruiterUserAdmin)