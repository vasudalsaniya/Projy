from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User
from college.models import College, Department, StaffProfile
from recruitment.models import Company
from students.models import StudentProfile

# --- 1. LOGIN FORM ---
class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': 'name@example.com',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Password'
        })
    )

# --- 2. RECRUITER SIGNUP FORM ---
class RecruiterSignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    company = forms.ModelChoiceField(queryset=Company.objects.all(), empty_label="Select Company")

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'profile_pic']
        help_texts = {'username': None}

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = User.Role.RECRUITER

        if commit:
            user.save()
            company = self.cleaned_data['company']
            company.hr_manager = user
            company.save()
        return user

# --- 3. COLLEGE SIGNUP FORM ---
class CollegeSignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    college = forms.ModelChoiceField(queryset=College.objects.all(), empty_label="Select College")
    department = forms.ModelChoiceField(queryset=Department.objects.all(), empty_label="Select Department", required=False)

    role_choice = forms.ChoiceField(choices=[
        ('STUDENT', 'Student'),
        ('FACULTY', 'Faculty'),
        ('HOD', 'HOD')
    ])

    enrollment_number = forms.CharField(required=False, help_text="Required if Student")

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'profile_pic']
        help_texts = {'username': None}


    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = self.cleaned_data['role_choice']

        if commit:
            user.save()

            # Logic for Students
            if user.role == 'STUDENT':
                selected_dept = self.cleaned_data.get('department')
                if not selected_dept:
                    selected_dept = Department.objects.filter(college=self.cleaned_data['college']).first()

                StudentProfile.objects.create(
                    user=user,
                    college=self.cleaned_data['college'],
                    department=selected_dept, 
                    enrollment_number=self.cleaned_data.get('enrollment_number', 'TEMP')
                )

            # Logic for Faculty/HOD
            elif user.role in ['FACULTY', 'HOD']:
                StaffProfile.objects.create(
                    user=user,
                    college=self.cleaned_data['college'],
                    department=self.cleaned_data.get('department')
                )

        return user

# --- QUICK ADD FORMS FOR ADMIN PANEL ---

class QuickCollegeForm(forms.ModelForm):
    class Meta:
        model = College
        fields = ['name', 'website', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'College Name'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Address'}),
        }

class QuickDeptForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'college']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department Name'}),
            'college': forms.Select(attrs={'class': 'form-control'}),
        }

class QuickCompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'website', 'location']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Website'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'}),
        }

class QuickUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    role = forms.ChoiceField(choices=User.Role.choices, widget=forms.Select(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }
        # --- ADD THIS TO REMOVE THE LONG TEXT ---
        help_texts = {
            'username': None,
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user