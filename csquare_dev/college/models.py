from django.db import models
from django.conf import settings
from accounts.models import User

class College(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    website = models.URLField(blank=True)

    def __str__(self):
        return self.name

class Department(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=100)
    hod = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='hod_department'
    )

    def __str__(self):
        return f"{self.name} - {self.college.name}"

# --- This is where StaffProfile belongs ---
class StaffProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='staff_profile')
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.college.name}"

# --- Proxy Models ---
class StudentUser(User):
    class Meta:
        proxy = True
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

class FacultyUser(User):
    class Meta:
        proxy = True
        verbose_name = 'Faculty'
        verbose_name_plural = 'Faculty Members'

class HODUser(User):
    class Meta:
        proxy = True
        verbose_name = 'HOD'
        verbose_name_plural = 'HODs'