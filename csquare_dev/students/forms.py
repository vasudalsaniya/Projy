from django import forms
from .models import Project, ProjectLanguage, StudentProfile
from accounts.models import User

class ProjectForm(forms.ModelForm):
    class Meta:     
        model = Project
        fields = ['title', 'description', 'cover_image', 'video_demo', 'github_repo_link', 'source_code_zip', 'is_public']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ProjectLanguageForm(forms.ModelForm):
    class Meta:
        model = ProjectLanguage
        fields = ['language_name', 'percentage']
        help_texts = {
            'percentage': 'Enter a number from 1 to 100',
        }

class StudentProfileEditForm(forms.ModelForm):
    """Allows students to update Photo and Request Semester Change"""
    profile_pic = forms.ImageField(required=False)
    new_semester = forms.IntegerField(required=False, min_value=1, max_value=8, label="Request New Semester")

    class Meta:
        model = StudentProfile
        fields = ['github_url', 'linkedin_url', 'is_profile_public']
