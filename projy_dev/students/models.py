from django.db import models
from django.conf import settings
from django.utils.text import slugify
from college.models import College, Department
import os
from django.dispatch import receiver
from django.db.models.signals import post_delete, pre_save
from django.utils import timezone


class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    college = models.ForeignKey(College, on_delete=models.CASCADE, db_index=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    enrollment_number = models.CharField(max_length=20, db_index=True)

    bio = models.TextField(blank=True, null=True, help_text="Short professional summary")
    education_details = models.TextField(blank=True, null=True)
    skills_csv = models.CharField(max_length=500, blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True, default="Software Developer")
    birthday = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)

    THEME_CHOICES = (
        ('modern', 'Modern Business'),
        ('minimal', 'Clean Minimalist'),
        ('hacker', 'Terminal Developer'),
    )
    portfolio_theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='modern')

    semester = models.IntegerField(default=1, db_index=True)
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
    is_profile_public = models.BooleanField(default=False, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['college', 'semester']),
            models.Index(fields=['mentor', '-is_profile_public']),
        ]

    def __str__(self):
        return f"{self.user.username} ({self.enrollment_number})"

    @property
    def public_portfolio_url(self):
        from django.urls import reverse
        return reverse(
            'live_portfolio_shared',
            args=[
                self.user.username,
                self.enrollment_number,
                slugify(self.college.name or 'college')
            ]
        )

class Project(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    is_public = models.BooleanField(default=True, db_index=True)

    cover_image = models.ImageField(upload_to='project_covers/', blank=True, null=True)
    video_demo = models.FileField(upload_to='project_videos/', blank=True, null=True)

    github_repo_link = models.URLField(blank=True)
    source_code_zip = models.FileField(upload_to='project_code/', blank=True, null=True)

    is_verified = models.BooleanField(default=False, db_index=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_projects')

    faculty_remarks = models.TextField(blank=True, null=True)
    needs_revision = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class ProjectLanguage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='languages')
    language_name = models.CharField(max_length=50)
    percentage = models.IntegerField()

    def __str__(self):
        return f"{self.language_name} ({self.percentage}%)"

    def get_color(self):
        colors = {
            # Web
            'Python': '#3572A5',
            'JavaScript': '#f1e05a',
            'HTML': '#e34c26',
            'CSS': '#563d7c',
            'SCSS': '#c6538c',
            'Sass': '#a53b70',
            'TypeScript': '#2b7489',
            'PHP': '#4F5D95',
            'Vue': '#41b883',
            # Systems
            'Java': '#b07219',
            'C++': '#f34b7d',
            'C': '#555555',
            'C#': '#178600',
            'Go': '#00ADD8',
            'Rust': '#dea584',
            'Shell': '#89e051',
            'PowerShell': '#012456',
            # Mobile
            'Swift': '#F05138',
            'Kotlin': '#A97BFF',
            'Dart': '#00B4AB',
            'Objective-C': '#438eff',
            # Data / other
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
        return colors.get(self.language_name, '#8b9cb0')

@receiver(post_delete, sender=Project)
def delete_project_files_on_delete(sender, instance, **kwargs):
    files = [instance.cover_image, instance.source_code_zip, instance.video_demo]
    for file_field in files:
        if file_field and hasattr(file_field, 'path'):
            try:
                if os.path.isfile(file_field.path):
                    file_field.close()
                    os.remove(file_field.path)
            except (OSError, PermissionError):
                pass


@receiver(pre_save, sender=Project)
def delete_old_files_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_project = Project.objects.get(pk=instance.pk)
    except Project.DoesNotExist:
        return

    def check_and_delete(old_file, new_file):
        if old_file and old_file != new_file and hasattr(old_file, 'path'):
            try:
                if os.path.isfile(old_file.path):
                    old_file.close()
                    os.remove(old_file.path)
            except (OSError, PermissionError):
                pass

    check_and_delete(old_project.cover_image, instance.cover_image)
    check_and_delete(old_project.source_code_zip, instance.source_code_zip)
    check_and_delete(old_project.video_demo, instance.video_demo)

class BlogPost(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='blogs')
    title = models.CharField(max_length=255, db_index=True)
    content = models.TextField()
    featured_image = models.ImageField(upload_to='blog_media/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_private = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', '-created_at']),
            models.Index(fields=['is_private', '-created_at']),
        ]

    def __str__(self):
        return self.title

class Certificate(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='certificates')
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    certificate_photo = models.ImageField(upload_to='certificates/')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', '-created_at']),
        ]

    def __str__(self):
        return self.title

class TodoItem(models.Model):
    student = models.ForeignKey('StudentProfile', on_delete=models.CASCADE, related_name='todos')
    task = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False, db_index=True)
    due_date = models.DateField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_completed', 'due_date', '-created_at']
        indexes = [
            models.Index(fields=['student', 'is_completed', 'due_date']),
        ]

    def __str__(self):
        return self.task

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


class CompanyPlacement(models.Model):
    hod = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posted_placements',
        limit_choices_to={'role': 'HOD'}
    )
    company_name = models.CharField(max_length=255, db_index=True)
    position = models.CharField(max_length=150, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    semester = models.IntegerField(default=1, db_index=True)
    description = models.TextField(blank=True, null=True)
    application_deadline = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['department', 'semester', 'is_active']),
        ]

    def __str__(self):
        return f"{self.company_name} ({self.department.name})"

    @property
    def public_link(self):
        from django.urls import reverse
        return reverse('placement_detail', args=[self.id])

    @property
    def eligible_semester_label(self):
        return f"Semester {self.semester}"


class PlacementRegistration(models.Model):
    student = models.ForeignKey('StudentProfile', on_delete=models.CASCADE, related_name='placement_registrations')
    placement = models.ForeignKey(CompanyPlacement, on_delete=models.CASCADE, related_name='registrations')
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'placement')
        ordering = ['-registered_at']
        indexes = [
            models.Index(fields=['student', 'placement']),
        ]

    def __str__(self):
        return f"{self.student.user.username} -> {self.placement.company_name}"
