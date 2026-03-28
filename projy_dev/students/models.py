# Create your models here.
from django.db import models
from django.conf import settings
from college.models import College, Department
import os
from django.dispatch import receiver
from django.db.models.signals import post_delete, pre_save
from django.utils import timezone


class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    enrollment_number = models.CharField(max_length=20)
    
    # Portfolio Content Fields
    bio = models.TextField(blank=True, null=True, help_text="Short professional summary")
    education_details = models.TextField(blank=True, null=True, help_text="e.g. B.Tech in Computer Science")
    skills_csv = models.CharField(max_length=500, blank=True, null=True, help_text="Comma separated skills like: Django, React, Python")
    job_title = models.CharField(max_length=100, blank=True, null=True, default="Software Developer")
    birthday = models.DateField(blank=True, null=True, help_text="Format: YYYY-MM-DD")
    location = models.CharField(max_length=200, blank=True, null=True, help_text="e.g. Gandhinagar, Gujarat, India")
    
    # NEW: Theme Selection
    THEME_CHOICES = (
        ('modern', 'Modern Business'),
        ('minimal', 'Clean Minimalist'),
        ('hacker', 'Terminal Developer'),
    )
    portfolio_theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='modern')

    semester = models.IntegerField(default=1)
    pending_semester = models.IntegerField(blank=True, null=True)
    
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='mentored_students',
        limit_choices_to={'role': 'FACULTY'}
    )
    
    github_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    is_profile_public = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} ({self.enrollment_number})"

class Project(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    description = models.TextField()
    is_public = models.BooleanField(default=True)
    
    cover_image = models.ImageField(upload_to='project_covers/', blank=True, null=True)
    video_demo = models.FileField(upload_to='project_videos/', blank=True, null=True)
    
    github_repo_link = models.URLField(blank=True)
    source_code_zip = models.FileField(upload_to='project_code/', blank=True, null=True)

    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_projects')
    
    faculty_remarks = models.TextField(blank=True, null=True)
    needs_revision = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class ProjectLanguage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='languages')
    language_name = models.CharField(max_length=50)
    percentage = models.IntegerField()

    def __str__(self):
        return f"{self.language_name} ({self.percentage}%)"

    # --- ADD THIS METHOD ---
    def get_color(self):
        """Returns the GitHub-like color for the language."""
        colors = {
            # --- WEB ---
            'Python': '#3572A5',
            'JavaScript': '#f1e05a',
            'HTML': '#e34c26',
            'CSS': '#563d7c',
            'TypeScript': '#2b7489',
            'PHP': '#4F5D95',
            'Vue': '#2c3e50',
            'React': '#61dafb',
            
            # --- SYSTEMS & CORE ---
            'Java': '#b07219',
            'C++': '#f34b7d',
            'C': '#555555',
            'C#': '#178600',   
            'Go': '#00ADD8',
            'Rust': '#dea584',
            'Shell': '#89e051',
            'PowerShell': '#012456',
            
            # --- MOBILE ---
            'Swift': '#F05138',
            'Kotlin': '#A97BFF', 
            'Dart': '#00B4AB',
            'Objective-C': '#438eff',

            # --- DATA & OTHERS ---
            'Ruby': '#701516',
            'R': '#198CE7', 
            'SQL': '#e38c00',
            'Lua': '#000080',
            'Perl': '#0298c3',
            'Scala': '#c22d40',
            'Haskell': '#5e5086',
            'Arduino': '#bd79d1',
            'Assembly': '#6E4C13',
            'MATLAB': '#e16737',
        }
        # Default to grey if language not found
        return colors.get(self.language_name, '#ccc')

@receiver(post_delete, sender=Project)
def delete_project_files_on_delete(sender, instance, **kwargs):
    """
    When a Project is deleted from the DB, delete its files from the PC.
    """
    files_to_delete = [
        instance.cover_image,
        instance.source_code_zip, 
        instance.video_demo
    ]

    for file_field in files_to_delete:
        if file_field and os.path.isfile(file_field.path):
            try:
                os.remove(file_field.path)
                print(f"Deleted file: {file_field.path}")
            except Exception as e:
                print(f"Error deleting file: {e}")

@receiver(pre_save, sender=Project)
def delete_old_files_on_update(sender, instance, **kwargs):
    """
    When a Project is edited (e.g. new zip uploaded), delete the old zip.
    """
    if not instance.pk:
        return False

    try:
        old_project = Project.objects.get(pk=instance.pk)
    except Project.DoesNotExist:
        return False

    def check_and_delete(old_file, new_file):
        if old_file and old_file != new_file:
            if os.path.isfile(old_file.path):
                os.remove(old_file.path)
                print(f"Replaced/Deleted old file: {old_file.path}")

    check_and_delete(old_project.cover_image, instance.cover_image)
    check_and_delete(old_project.source_code_zip, instance.source_code_zip)
    check_and_delete(old_project.video_demo, instance.video_demo)

class BlogPost(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='blogs')
    title = models.CharField(max_length=255)
    content = models.TextField()
    featured_image = models.ImageField(upload_to='blog_media/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Logic for Private/Public
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

class Certificate(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='certificates')
    title = models.CharField(max_length=255)
    description = models.TextField()
    # Image uploaded by student
    certificate_photo = models.ImageField(upload_to='certificates/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

class TodoItem(models.Model):
    student = models.ForeignKey('StudentProfile', on_delete=models.CASCADE, related_name='todos')
    task = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)
    
    # NEW: Due Date Field
    due_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Order by uncompleted, then closest due dates first
        ordering = ['is_completed', 'due_date', '-created_at'] 

    def __str__(self):
        return self.task

    # Smart properties to help color code tasks in the template
    @property
    def is_overdue(self):
        if self.due_date and not self.is_completed:
            return self.due_date < timezone.localdate()
        return False

    @property
    def is_due_today(self):
        if self.due_date and not self.is_completed:
            return self.due_date == timezone.localdate()
        return False