from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .forms import UserLoginForm, RecruiterSignupForm, CollegeSignupForm
from django.contrib.admin.views.decorators import staff_member_required
from .models import Notification
from students.models import Project
from college.models import College
from recruitment.models import Company
from accounts.models import User
from django.contrib import messages
from accounts.forms import QuickCollegeForm, QuickDeptForm, QuickCompanyForm, QuickUserForm


@staff_member_required
def admin_control_panel(request):
    # --- 1. HANDLE POST ACTIONS ---
    if request.method == 'POST':
        # A. APPROVE/REJECT LOGIC
        if 'action' in request.POST:
            user_id = request.POST.get('user_id')
            action = request.POST.get('action')
            user_to_act_on = get_object_or_404(User, id=user_id)
            
            if action == 'approve':
                user_to_act_on.is_verified = True
                user_to_act_on.save()
                messages.success(request, f"✅ Approved {user_to_act_on.username}")
            elif action == 'reject':
                user_to_act_on.delete()
                messages.error(request, "❌ User Rejected & Deleted")
        
        # B. ADD COLLEGE
        elif 'add_college' in request.POST:
            form = QuickCollegeForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "🏫 College Added Successfully!")
            else:
                messages.error(request, "Error adding college.")

        # C. ADD DEPARTMENT
        elif 'add_dept' in request.POST:
            form = QuickDeptForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "📚 Department Added Successfully!")
            else:
                messages.error(request, "Error adding department.")

        # D. ADD COMPANY
        elif 'add_company' in request.POST:
            form = QuickCompanyForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "🏢 Company Added Successfully!")
            else:
                messages.error(request, "Error adding company.")

        # E. ADD USER
        elif 'add_user' in request.POST:
            form = QuickUserForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "👤 User Created Successfully!")
            else:
                messages.error(request, "Error creating user. Username might exist.")

        return redirect('admin_control_panel')

    # --- 2. PREPARE DATA & FORMS ---
    pending_hods = User.objects.filter(role='HOD', is_verified=False)
    pending_recruiters = User.objects.filter(role='RECRUITER', is_verified=False)
    
    context = {
        'pending_hods_list': pending_hods,
        'pending_recruiters_list': pending_recruiters,
        
        'total_students': User.objects.filter(role='STUDENT').count(),
        'total_faculty': User.objects.filter(role='FACULTY').count(),
        'total_projects': Project.objects.count(),
        'college_count': College.objects.count(),
        'company_count': Company.objects.count(),
        'recent_users': User.objects.order_by('-date_joined')[:5],
        
        # Empty forms for the modals
        'college_form': QuickCollegeForm(),
        'dept_form': QuickDeptForm(),
        'company_form': QuickCompanyForm(),
        'user_form': QuickUserForm(),
    }
    return render(request, 'accounts/admin_control_panel.html', context)

# --- LOGIN VIEW ---
def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # 1. Attempt to authenticate the user
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                # 2. SECURITY CHECK: Is user verified?
                # Superusers bypass this check.
                if not user.is_verified and not user.is_superuser:
                    return render(request, 'accounts/pending_verification.html')

                # 3. Success: Log the user in
                login(request, user)
                
                # 4. Role-based Redirection
                if user.is_superuser or user.role == 'ADMIN':
                    return redirect('admin_control_panel') # Use the name defined in urls.py
                elif user.role == 'RECRUITER':
                    return redirect('recruiter_dashboard')
                elif user.role == 'HOD':
                    return redirect('hod_dashboard')
                elif user.role == 'FACULTY':
                    return redirect('faculty_dashboard')
                elif user.role == 'STUDENT':
                    return redirect('student_dashboard')
            else:
                # 5. Handle Wrong Credentials
                messages.error(request, "Invalid Email or Password. Please try again.")
        else:
            # Handle form validation errors (e.g., empty fields)
            messages.error(request, "Please fill in all fields correctly.")
            
    else:
        form = UserLoginForm()
        
    return render(request, 'accounts/login.html', {'form': form})

# --- RECRUITER SIGNUP VIEW ---
def recruiter_signup(request):
    if request.method == 'POST':
        form = RecruiterSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Note: We do NOT log them in automatically anymore, 
            # because they need to be verified first.
            return render(request, 'accounts/pending_verification.html')
    else:
        form = RecruiterSignupForm()
    return render(request, 'accounts/signup_recruiter.html', {'form': form})

# --- COLLEGE SIGNUP VIEW ---
def college_signup(request):
    if request.method == 'POST':
        form = CollegeSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            return render(request, 'accounts/pending_verification.html')
    else:
        form = CollegeSignupForm()
    return render(request, 'accounts/signup_college.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def read_notification(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, user=request.user)
    notif.is_read = True
    notif.save()
    # Redirect to the link if it exists, otherwise back to dashboard
    return redirect(notif.link if notif.link else '/')