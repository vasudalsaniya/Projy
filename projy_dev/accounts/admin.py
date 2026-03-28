from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Q 
from .models import User

class CustomUserAdmin(UserAdmin):
    # --- 1. FIELDSETS (What you see when you click a user) ---
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number', 'profile_pic', 'is_verified')}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number', 'profile_pic', 'is_verified')}),
    )

    # --- 2. LIST DISPLAY (Columns in the table) ---
    list_display = ('username', 'email', 'role', 'is_verified', 'is_superuser')
    list_filter = ('role', 'is_verified', 'is_superuser')
    search_fields = ('username', 'email', 'phone_number')

    # --- 3. FILTER LOGIC (The Magic Part) ---
    def get_queryset(self, request):
        """
        Only show Users who are ADMINS or SUPERUSERS in this specific list.
        Hide Students, Faculty, HODs, and Recruiters (they are in their own apps).
        """
        qs = super().get_queryset(request)
        # Show if role is 'ADMIN' OR if they are a Superuser
        return qs.filter(Q(role='ADMIN') | Q(is_superuser=True))

# Register the Master User model
admin.site.register(User, CustomUserAdmin)