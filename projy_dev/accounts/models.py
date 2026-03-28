from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom User Model acting as the base for all roles.
    """
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        HOD = "HOD", "HOD"
        FACULTY = "FACULTY", "Faculty"
        STUDENT = "STUDENT", "Student"
        RECRUITER = "RECRUITER", "Recruiter"

    # Default role if none is specified
    base_role = Role.ADMIN 
    
    role = models.CharField(max_length=50, choices=Role.choices)
    
    # Common fields
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    # Verification status
    is_verified = models.BooleanField(default=False)
    
    # profile pic upload
    profile_pic = models.ImageField(upload_to='profile_pics/', default='default.jpg', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.pk: 
            if not self.role:
                self.role = self.base_role
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True, null=True) # Where to go when clicked
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}"