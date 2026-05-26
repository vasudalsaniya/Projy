from django.db import models
from django.conf import settings
from accounts.models import User

class Company(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    website = models.URLField(blank=True)
    hr_manager = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='company_managed'
    )

    def __str__(self):
        return self.name

class RecruiterUser(User):
    """Virtual model to display only Recruiters"""
    class Meta:
        proxy = True
        verbose_name = 'Recruiter'
        verbose_name_plural = 'Recruiters'