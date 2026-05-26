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

    base_role = Role.ADMIN

    role = models.CharField(max_length=50, choices=Role.choices, db_index=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', default='default.jpg', blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_verified = models.BooleanField(default=False, db_index=True)

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
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"Notification for {self.user.username}"