from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .forms import UserLoginForm, RecruiterSignupForm, CollegeSignupForm
from django.contrib.admin.views.decorators import staff_member_required
from .models import Notification
from students.models import Project
from college.models import College, Department
from recruitment.models import Company
from accounts.models import User
from django.contrib import messages
from accounts.forms import QuickCollegeForm, QuickDeptForm, QuickCompanyForm, QuickUserForm


@staff_member_required
def admin_control_panel(request):
    if not request.user.is_superuser:
        return redirect('login')

    if request.method == 'POST':
        if 'action' in request.POST:
            user_id = request.POST.get('user_id')
            action = request.POST.get('action')

            try:
                user_to_act_on = User.objects.get(id=user_id)
            except User.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect('admin_control_panel')

            if action == 'approve':
                user_to_act_on.is_verified = True
                user_to_act_on.save(update_fields=['is_verified'])
                messages.success(request, f"✅ Approved {user_to_act_on.username}")
            elif action == 'reject':
                user_id_for_delete = user_to_act_on.id
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

        # F. DELETE COLLEGE
        elif 'delete_college' in request.POST:
            college_id = request.POST.get('college_id')
            try:
                College.objects.get(id=college_id).delete()
                messages.success(request, "College deleted.")
            except College.DoesNotExist:
                messages.error(request, "College not found.")

        # G. DELETE DEPARTMENT
        elif 'delete_dept' in request.POST:
            dept_id = request.POST.get('dept_id')
            try:
                Department.objects.get(id=dept_id).delete()
                messages.success(request, "Department deleted.")
            except Department.DoesNotExist:
                messages.error(request, "Department not found.")

        # H. DELETE COMPANY
        elif 'delete_company' in request.POST:
            company_id = request.POST.get('company_id')
            try:
                Company.objects.get(id=company_id).delete()
                messages.success(request, "Company deleted.")
            except Company.DoesNotExist:
                messages.error(request, "Company not found.")

        # I. DELETE USER
        elif 'delete_user' in request.POST:
            user_id = request.POST.get('user_id')
            try:
                target = User.objects.get(id=user_id)
                if target.is_superuser:
                    messages.error(request, "Cannot delete a superuser.")
                else:
                    target.delete()
                    messages.success(request, "User deleted.")
            except User.DoesNotExist:
                messages.error(request, "User not found.")

        return redirect('admin_control_panel')

    pending_hods = User.objects.filter(role='HOD', is_verified=False).only('id', 'username', 'email')
    pending_recruiters = User.objects.filter(role='RECRUITER', is_verified=False).only('id', 'username', 'email')

    all_colleges = College.objects.all().order_by('name')
    all_departments = Department.objects.select_related('college').order_by('college__name', 'name')
    all_companies = Company.objects.all().order_by('name')
    all_users = User.objects.filter(is_superuser=False).order_by('-date_joined').values('id', 'username', 'email', 'role', 'is_verified')

    context = {
        'pending_hods_list': pending_hods,
        'pending_recruiters_list': pending_recruiters,
        'total_students': User.objects.filter(role='STUDENT').values('id').count(),
        'total_faculty': User.objects.filter(role='FACULTY').values('id').count(),
        'total_projects': Project.objects.values('id').count(),
        'college_count': all_colleges.count(),
        'company_count': all_companies.count(),
        'recent_users': User.objects.order_by('-date_joined').values('id', 'username', 'email', 'role')[:5],
        'college_form': QuickCollegeForm(),
        'dept_form': QuickDeptForm(),
        'company_form': QuickCompanyForm(),
        'user_form': QuickUserForm(),
        'all_colleges': all_colleges,
        'all_departments': all_departments,
        'all_companies': all_companies,
        'all_users': all_users,
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
        form = RecruiterSignupForm(request.POST, request.FILES)
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

            if user.role == 'FACULTY':
                hod_exists = User.objects.filter(
                    role='HOD', is_verified=True,
                    staff_profile__department=user.staff_profile.department,
                    staff_profile__college=user.staff_profile.college
                ).exists()
                if not hod_exists:
                    messages.info(request, "Your account is pending. There is no verified HOD in this department yet. Please wait until an HOD account is created and verifies you.")
                else:
                    messages.info(request, "Your account is pending. A department HOD will verify your registration.")

            elif user.role == 'STUDENT':
                faculty_exists = User.objects.filter(
                    role='FACULTY', is_verified=True,
                    staff_profile__department=user.student_profile.department,
                    staff_profile__college=user.student_profile.college
                ).exists()
                if not faculty_exists:
                    messages.info(request, "Your account is pending. There is no verified faculty in your department yet. Please wait until a faculty account is created.")
                else:
                    messages.info(request, "Your account is pending. A faculty member in your department will verify your registration.")

            elif user.role == 'HOD':
                messages.info(request, "Your account is pending. An Admin will verify your HOD registration.")

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