from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import StudentProfile, Project, BlogPost, Certificate, TodoItem
from accounts.models import Notification
from .forms import ProjectForm, ProjectLanguageForm, StudentProfileEditForm
from .utils import analyze_zip_and_create_languages
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils import timezone
import datetime

@login_required
def student_dashboard(request):
    profile = request.user.student_profile

    # FETCH DATA
    projects = Project.objects.filter(student=profile).order_by('-id')
    blogs = BlogPost.objects.filter(student=profile).order_by('-created_at')
    certificates = Certificate.objects.filter(student=profile).order_by('-created_at')
    todos = TodoItem.objects.filter(student=profile)

    # --- NEW: DAILY NOTIFICATION LOGIC ---
    if request.method == 'GET':
        today = timezone.localdate()
        today_str = str(today)

        # Check if we already notified them today during this session
        if request.session.get('todo_notified_today') != today_str:
            overdue_count = todos.filter(is_completed=False, due_date__lt=today).count()
            due_today_count = todos.filter(is_completed=False, due_date=today).count()
            
            if overdue_count > 0:
                messages.error(request, f"🚨 You have {overdue_count} overdue task(s) in your To-Do list!")
            if due_today_count > 0:
                messages.warning(request, f"📅 Reminder: You have {due_today_count} task(s) due today.")
                
            # Set session variable so we don't spam them until tomorrow (or next login)
            request.session['todo_notified_today'] = today_str


    # HANDLE POST REQUESTS
    if request.method == 'POST':
        if 'edit_profile' in request.POST:
            form = StudentProfileEditForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                if request.FILES.get('profile_pic'):
                    request.user.profile_pic = request.FILES['profile_pic']
                    request.user.save()
                new_sem = form.cleaned_data.get('new_semester')
                if new_sem and new_sem != profile.semester:
                    profile.pending_semester = new_sem
                    messages.info(request, "Semester change requested.")
                form.save() 
                messages.success(request, "Profile updated successfully!")
                return redirect('student_dashboard')

        # --- UPDATED: Add To-Do (Now accepts due_date) ---
        elif 'add_todo' in request.POST:
            task_text = request.POST.get('task')
            due_date_str = request.POST.get('due_date') # Format: YYYY-MM-DD
            
            due_date = None
            if due_date_str:
                try:
                    due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass

            if task_text:
                TodoItem.objects.create(student=profile, task=task_text, due_date=due_date)
            return redirect('student_dashboard')

        elif 'toggle_todo' in request.POST:
            todo_id = request.POST.get('todo_id')
            todo = get_object_or_404(TodoItem, id=todo_id, student=profile)
            todo.is_completed = not todo.is_completed
            todo.save()
            return redirect('student_dashboard')

        elif 'delete_todo' in request.POST:
            todo_id = request.POST.get('todo_id')
            todo = get_object_or_404(TodoItem, id=todo_id, student=profile)
            todo.delete()
            return redirect('student_dashboard')

    else:
        form = StudentProfileEditForm(instance=profile)

    context = {
        'profile': profile,
        'projects': projects,
        'blogs': blogs,
        'certificates': certificates,
        'todos': todos, 
        'profile_form': form
    }
    return render(request, 'students/dashboard_student.html', context)

@login_required
def add_project(request):
    if request.user.role != 'STUDENT':
        return redirect('login')

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.student = request.user.student_profile
            project.save()

            # --- AUTO-DETECT LOGIC ---
            # If they uploaded a zip, analyze it now
            if project.source_code_zip:
                analyze_zip_and_create_languages(project.source_code_zip, project)

            return redirect('student_dashboard')
    else:
        form = ProjectForm()
    
    return render(request, 'students/add_project.html', {'form': form})

@login_required
def edit_project(request, project_id):
    # Get project and ensure it belongs to the logged-in student
    project = get_object_or_404(Project, id=project_id, student__user=request.user)

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            project = form.save()
            
            # Re-analyze if a new zip was uploaded
            if 'source_code_zip' in request.FILES:
                analyze_zip_and_create_languages(project.source_code_zip, project)
                
            return redirect('student_dashboard')
    else:
        form = ProjectForm(instance=project)
    
    return render(request, 'students/edit_project.html', {'form': form, 'project': project})

@login_required
def delete_project(request, project_id):
    # Fetch the project, ensuring it belongs to the currently logged-in student
    project = get_object_or_404(Project, id=project_id, student=request.user.student_profile)
    
    if request.method == 'POST':
        project.delete()  # This removes it from the database entirely
        messages.success(request, "Project deleted successfully!")
        return redirect('student_dashboard')
        
    # If someone tries to access this via GET (typing in the URL), redirect them back safely
    return redirect('student_dashboard')

@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    # Logic to add languages to this specific project
    if request.method == 'POST':
        lang_form = ProjectLanguageForm(request.POST)
        if lang_form.is_valid():
            language = lang_form.save(commit=False)
            language.project = project
            language.save()
            return redirect('project_detail', project_id=project.id)
    else:
        lang_form = ProjectLanguageForm()

    return render(request, 'students/project_detail.html', {
        'project': project, 
        'lang_form': lang_form
    })

@login_required
def student_public_profile(request, student_id):   
    # Fetch the student profile
    student = get_object_or_404(StudentProfile, id=student_id)
    # Security Check: Who is allowed to see this?
    # 1. The Student themselves
    # 2. A verified Recruiter
    # 3. A Faculty/HOD from the SAME college
    can_view = False
    user = request.user

    if user == student.user:
        can_view = True
    elif user.role == 'RECRUITER' and user.is_verified:
        can_view = True
    elif user.role in ['FACULTY', 'HOD'] and user.is_verified:
        # Check if they are from the same college
        if hasattr(user, 'staff_profile') and user.staff_profile.college == student.college:
            can_view = True

    if not can_view:
        return render(request, 'students/error.html', {'message': "You are not authorized to view this profile."})

    # Get only PUBLIC projects
    projects = student.projects.filter(is_public=True)

    return render(request, 'students/public_profile.html', {
        'student': student,
        'projects': projects
    })
    
@login_required
def live_portfolio(request):
    profile = request.user.student_profile
    projects = Project.objects.filter(student=profile, is_verified=True)
    # ONLY show public blogs
    public_blogs = BlogPost.objects.filter(student=profile, is_private=False)
    return render(request, 'students/portfolio_template.html', {
        'profile': profile,
        'projects': projects,
        'blogs': public_blogs,
    })
    
@login_required
def generate_resume(request):
    profile = request.user.student_profile
    projects = Project.objects.filter(student=profile, is_verified=True)[:3] # Top 3 projects
    return render(request, 'students/resume_template.html', {
        'profile': profile,
        'projects': projects,
    })

@login_required
def manage_blogs(request):
    profile = request.user.student_profile
    blogs = BlogPost.objects.filter(student=profile).order_by('-created_at')
    
    if request.method == 'POST':
        blog_id = request.POST.get('blog_id')
        
        # FIX: Check if blog_id has a value (is not empty)
        if blog_id:
            # --- EDIT EXISTING BLOG ---
            blog = get_object_or_404(BlogPost, id=blog_id, student=profile)
            
            blog.title = request.POST.get('title')
            blog.content = request.POST.get('content')
            
            if request.FILES.get('featured_image'):
                blog.featured_image = request.FILES.get('featured_image')
            
            blog.is_private = 'is_private' in request.POST
            blog.save()
            messages.success(request, "Blog updated successfully!")
            
        else:
            # --- CREATE NEW BLOG ---
            # (blog_id was empty, so we create a new one)
            title = request.POST.get('title')
            content = request.POST.get('content')
            image = request.FILES.get('featured_image')
            is_private = 'is_private' in request.POST
            
            BlogPost.objects.create(
                student=profile,
                title=title,
                content=content,
                featured_image=image,
                is_private=is_private
            )
            messages.success(request, "Blog created successfully!")
            
        return redirect('manage_blogs')

    return render(request, 'students/manage_blogs.html', {'blogs': blogs})

@login_required
def delete_blog(request, blog_id):
    # Get the blog, ensuring it belongs to the logged-in student
    blog = get_object_or_404(BlogPost, id=blog_id, student=request.user.student_profile)
    
    if request.method == 'POST':
        blog.delete()
        messages.success(request, "Blog post deleted successfully!")
    
    return redirect('manage_blogs')

@login_required
def manage_certificates(request):
    profile = request.user.student_profile
    certificates = Certificate.objects.filter(student=profile).order_by('-created_at')
    
    if request.method == 'POST':
        if 'cert_id' in request.POST and request.POST.get('cert_id'):
            # EDIT
            cert_id = request.POST.get('cert_id')
            cert = get_object_or_404(Certificate, id=cert_id, student=profile)
            cert.title = request.POST.get('title')
            cert.description = request.POST.get('description')
            if request.FILES.get('certificate_photo'):
                cert.certificate_photo = request.FILES.get('certificate_photo')
            cert.save()
            messages.success(request, "Certificate updated successfully!")
        else:
            # CREATE
            Certificate.objects.create(
                student=profile,
                title=request.POST.get('title'),
                description=request.POST.get('description'),
                certificate_photo=request.FILES.get('certificate_photo')
            )
            messages.success(request, "Certificate added successfully!")
        return redirect('manage_certificates')

    return render(request, 'students/manage_certificates.html', {'certificates': certificates})

# 3. Add Delete Certificate View:
@login_required
def delete_certificate(request, cert_id):
    cert = get_object_or_404(Certificate, id=cert_id, student=request.user.student_profile)
    if request.method == 'POST':
        cert.delete()
        messages.success(request, "Certificate deleted successfully!")
    return redirect('manage_certificates')

@login_required
def mark_revision_done(request, project_id):
    project = get_object_or_404(Project, id=project_id, student=request.user.student_profile)
    project.needs_revision = False
    project.save()
    
    # Notify Mentor
    if project.student.mentor:
        Notification.objects.create(
            user=project.student.mentor,
            message=f"{request.user.first_name} fixed revisions for project '{project.title}'.",
            link="/college/dashboard/faculty/"
        )
    messages.success(request, "Project marked as fixed and sent to faculty for review.")
    return redirect('student_dashboard')

# Add this new view for the Builder
@login_required
def portfolio_builder(request):
    profile = request.user.student_profile
    
    if request.method == 'POST':
        # Update Profile Content
        profile.bio = request.POST.get('bio')
        profile.education_details = request.POST.get('education_details')
        profile.skills_csv = request.POST.get('skills_csv')
        
        # --- NEW FIELDS ---
        profile.job_title = request.POST.get('job_title')
        profile.location = request.POST.get('location')
        
        birthday_str = request.POST.get('birthday')
        if birthday_str:
            try:
                from datetime import datetime
                profile.birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Update Theme
        selected_theme = request.POST.get('portfolio_theme')
        if selected_theme in ['modern', 'minimal', 'hacker']:
            profile.portfolio_theme = selected_theme
            
        profile.save()
        messages.success(request, "Portfolio updated and saved!")
        return redirect('live_portfolio')

    return render(request, 'students/portfolio_builder.html', {'profile': profile})


# Update your existing live_portfolio view:
@login_required
def live_portfolio(request):
    profile = request.user.student_profile
    projects = Project.objects.filter(student=profile, is_verified=True)
    blogs = BlogPost.objects.filter(student=profile, is_private=False)
    
    context = {
        'profile': profile,
        'projects': projects,
        'blogs': blogs,
    }
    
    # dynamically render the selected theme template
    theme = profile.portfolio_theme
    if theme == 'minimal':
        return render(request, 'students/themes/theme_minimal.html', context)
    elif theme == 'hacker':
        return render(request, 'students/themes/theme_hacker.html', context)
    else:
        return render(request, 'students/themes/theme_modern.html', context)