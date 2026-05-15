from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from .models import StudentProfile, Project, BlogPost, Certificate, TodoItem, CompanyPlacement, PlacementRegistration
from accounts.models import Notification, User
from .forms import ProjectForm, ProjectLanguageForm, StudentProfileEditForm
from .utils import analyze_zip_and_create_languages
from django.contrib import messages
from django.utils import timezone
import datetime
from django.http import HttpResponse
from django.template.loader import get_template
from django.template.exceptions import TemplateDoesNotExist


def generate_resume_ai_summary(profile, projects):
    skills = profile.skills_csv or ''
    top_projects = ', '.join([project.title for project in projects[:3]])
    summary_parts = [
        f"{profile.user.get_full_name() or profile.user.username} is a driven {profile.job_title or 'student'} from {profile.college.name}.",
        f"Currently in semester {profile.semester} of {profile.department.name}.",
    ]
    if skills:
        summary_parts.append(f"Key strengths include {skills}.")
    if profile.location:
        summary_parts.append(f"Based in {profile.location}.")
    if profile.bio:
        summary_parts.append(profile.bio)
    if top_projects:
        summary_parts.append(f"Recent work includes {top_projects}.")

    return ' '.join(summary_parts)


def generate_portfolio_ai_content(profile, projects):
    skills = profile.skills_csv or 'industry-relevant tools and frameworks'
    focus = profile.job_title or 'engineering roles'
    top_projects = [project.title for project in projects[:3]]
    project_line = ''
    if top_projects:
        project_line = f" Recent highlights include {', '.join(top_projects)}."

    statement = (
        f"{profile.user.get_full_name() or profile.user.username} is a {profile.job_title or 'motivated student'} from {profile.college.name}, specializing in {profile.department.name}."
        f" Skilled in {skills}.{project_line}"
    )

    return {
        'career_statement': statement,
        'bio': profile.bio or statement,
        'education_details': profile.education_details or f"Pursuing degree in {profile.department.name} at {profile.college.name}.",
        'skills_csv': skills,
        'job_title': profile.job_title or 'Aspiring Software Engineer',
        'location': profile.location or 'Gandhinagar, Gujarat',
    }

@login_required
def student_dashboard(request):
    if request.user.role != 'STUDENT':
        return redirect('login')

    profile = request.user.student_profile

    projects = Project.objects.filter(student=profile).order_by('-id').select_related('student__user')
    blogs = BlogPost.objects.filter(student=profile).order_by('-created_at')
    certificates = Certificate.objects.filter(student=profile).order_by('-created_at')
    todos = TodoItem.objects.filter(student=profile)

    if request.method == 'GET':
        today = timezone.localdate()
        today_str = str(today)

        if request.session.get('todo_notified_today') != today_str:
            overdue_count = todos.filter(is_completed=False, due_date__lt=today).count()
            due_today_count = todos.filter(is_completed=False, due_date=today).count()

            if overdue_count > 0:
                messages.error(request, f"🚨 You have {overdue_count} overdue task(s)!")
            if due_today_count > 0:
                messages.warning(request, f"📅 Reminder: You have {due_today_count} task(s) due today.")

            request.session['todo_notified_today'] = today_str

    if request.method == 'POST':
        if 'edit_profile' in request.POST:
            form = StudentProfileEditForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                user_fields = []
                first_name = request.POST.get('first_name', '').strip()
                last_name = request.POST.get('last_name', '').strip()
                if first_name:
                    request.user.first_name = first_name
                    user_fields.append('first_name')
                if last_name:
                    request.user.last_name = last_name
                    user_fields.append('last_name')
                if request.FILES.get('profile_pic'):
                    request.user.profile_pic = request.FILES['profile_pic']
                    user_fields.append('profile_pic')
                if user_fields:
                    request.user.save(update_fields=user_fields)
                new_sem = form.cleaned_data.get('new_semester')
                if new_sem and new_sem != profile.semester:
                    profile.pending_semester = new_sem
                    messages.info(request, "Semester change requested.")
                form.save()
                messages.success(request, "Profile updated successfully!")
                return redirect('student_dashboard')

        elif 'add_todo' in request.POST:
            task_text = request.POST.get('task')
            due_date_str = request.POST.get('due_date')

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
            try:
                todo = TodoItem.objects.get(id=todo_id, student=profile)
                todo.is_completed = not todo.is_completed
                todo.save(update_fields=['is_completed'])
            except TodoItem.DoesNotExist:
                pass
            return redirect('student_dashboard')

        elif 'delete_todo' in request.POST:
            todo_id = request.POST.get('todo_id')
            try:
                todo = TodoItem.objects.get(id=todo_id, student=profile)
                todo.delete()
            except TodoItem.DoesNotExist:
                pass
            return redirect('student_dashboard')

    else:
        form = StudentProfileEditForm(instance=profile)

    unread_notifications = Notification.objects.filter(
        user=request.user, is_read=False
    ).order_by('-created_at')[:10]

    context = {
        'profile': profile,
        'projects': projects,
        'blogs': blogs,
        'certificates': certificates,
        'todos': todos,
        'profile_form': form,
        'unread_notifications': unread_notifications,
    }
    return render(request, 'students/dashboard_student.html', context)

@login_required
def student_placements(request):
    if request.user.role != 'STUDENT':
        return redirect('login')

    profile = request.user.student_profile
    if request.method == 'POST':
        if 'apply_placement' in request.POST:
            placement_id = request.POST.get('apply_placement')
            try:
                placement = CompanyPlacement.objects.get(id=placement_id, department=profile.department, semester=profile.semester, is_active=True)
                PlacementRegistration.objects.get_or_create(student=profile, placement=placement)
                messages.success(request, f"Registered for {placement.company_name} placement.")
            except CompanyPlacement.DoesNotExist:
                messages.error(request, "Placement opportunity not found.")
            return redirect('student_placements')

        elif 'cancel_placement' in request.POST:
            placement_id = request.POST.get('cancel_placement')
            PlacementRegistration.objects.filter(student=profile, placement_id=placement_id).delete()
            messages.success(request, "Your placement registration has been withdrawn.")
            return redirect('student_placements')

    placements = CompanyPlacement.objects.filter(
        department=profile.department,
        semester=profile.semester,
        is_active=True
    ).annotate(registration_count=Count('registrations'))
    registered_ids = set(profile.placement_registrations.values_list('placement_id', flat=True))

    return render(request, 'students/student_placements.html', {
        'profile': profile,
        'placements': placements,
        'registered_placement_ids': registered_ids,
    })

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
    try:
        project = Project.objects.select_related('student__user').get(id=project_id)
    except Project.DoesNotExist:
        messages.error(request, "Project not found.")
        return redirect('student_dashboard')

    if project.student.user != request.user and request.user.role != 'FACULTY' and request.user.role != 'HOD':
        return render(request, 'students/error.html', {'message': "Not authorized to view this project."})

    current_total = sum(lang.percentage for lang in project.languages.all())

    if request.method == 'POST':
        lang_form = ProjectLanguageForm(request.POST)
        if lang_form.is_valid() and request.user == project.student.user:
            language = lang_form.save(commit=False)

            if current_total + language.percentage <= 100:
                language.project = project
                language.save()
                messages.success(request, f"Skill '{language.language_name}' added!")
            else:
                remaining = 100 - current_total
                messages.error(request, f"Exceeds 100% limit. {remaining}% remaining.")

            return redirect('project_detail', project_id=project.id)
    else:
        lang_form = ProjectLanguageForm()

    return render(request, 'students/project_detail.html', {
        'project': project,
        'lang_form': lang_form
    })
    
@login_required
def student_public_profile(request, student_id):
    try:
        student = StudentProfile.objects.select_related('user', 'college').get(id=student_id)
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect('login')

    can_view = False

    if request.user == student.user:
        can_view = True
    elif request.user.role == 'RECRUITER' and request.user.is_verified:
        can_view = True
    elif request.user.role in ['FACULTY', 'HOD'] and request.user.is_verified:
        try:
            if request.user.staff_profile.college == student.college:
                can_view = True
        except:
            pass

    if not can_view:
        return render(request, 'students/error.html', {'message': "Not authorized."})

    projects = student.projects.filter(is_public=True).select_related('student__user')

    return render(request, 'students/public_profile.html', {
        'student': student,
        'projects': projects
    })

@login_required
def generate_resume(request):
    profile = request.user.student_profile
    projects = Project.objects.filter(student=profile, is_verified=True).order_by('-created_at')[:3]
    selected_style = request.GET.get('style', 'classic')
    if selected_style not in ['classic', 'professional', 'focused']:
        selected_style = 'classic'

    generated_summary = generate_resume_ai_summary(profile, projects)
    resume_template_options = [
        {'key': 'classic', 'label': 'Classic CV'},
        {'key': 'professional', 'label': 'Professional Modern'},
        {'key': 'focused', 'label': 'Focused One-Page'},
    ]

    return render(request, 'students/resume_template.html', {
        'profile': profile,
        'projects': projects,
        'generated_summary': generated_summary,
        'selected_style': selected_style,
        'resume_template_options': resume_template_options,
    })

@login_required
def manage_blogs(request):
    profile = request.user.student_profile
    blogs = BlogPost.objects.filter(student=profile).order_by('-created_at')

    if request.method == 'POST':
        blog_id = request.POST.get('blog_id')

        if blog_id:
            try:
                blog = BlogPost.objects.get(id=blog_id, student=profile)
                blog.title = request.POST.get('title')
                blog.content = request.POST.get('content')

                if request.FILES.get('featured_image'):
                    blog.featured_image = request.FILES.get('featured_image')

                blog.is_private = 'is_private' in request.POST
                blog.save()
                messages.success(request, "Blog updated!")
            except BlogPost.DoesNotExist:
                messages.error(request, "Blog not found.")
        else:
            title = request.POST.get('title')
            content = request.POST.get('content')
            image = request.FILES.get('featured_image')
            is_private = 'is_private' in request.POST

            if title and content:
                BlogPost.objects.create(
                    student=profile,
                    title=title,
                    content=content,
                    featured_image=image,
                    is_private=is_private
                )
                messages.success(request, "Blog created!")
            else:
                messages.error(request, "Title and content required.")

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
            try:
                cert_id = request.POST.get('cert_id')
                cert = Certificate.objects.get(id=cert_id, student=profile)
                cert.title = request.POST.get('title')
                cert.description = request.POST.get('description')
                if request.FILES.get('certificate_photo'):
                    cert.certificate_photo = request.FILES.get('certificate_photo')
                cert.save()
                messages.success(request, "Certificate updated!")
            except Certificate.DoesNotExist:
                messages.error(request, "Certificate not found.")
        else:
            title = request.POST.get('title')
            description = request.POST.get('description')
            photo = request.FILES.get('certificate_photo')

            if title and description and photo:
                Certificate.objects.create(
                    student=profile,
                    title=title,
                    description=description,
                    certificate_photo=photo
                )
                messages.success(request, "Certificate added!")
            else:
                messages.error(request, "All fields required.")
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

@login_required
def portfolio_builder(request):
    profile = request.user.student_profile
    projects = Project.objects.filter(student=profile, is_verified=True).order_by('-created_at')[:3]
    suggestions = None

    if request.method == 'POST':
        profile.bio = request.POST.get('bio', '')
        profile.education_details = request.POST.get('education_details', '')
        profile.skills_csv = request.POST.get('skills_csv', '')
        profile.job_title = request.POST.get('job_title', '')
        profile.location = request.POST.get('location', '')

        birthday_str = request.POST.get('birthday')
        if birthday_str:
            try:
                profile.birthday = datetime.datetime.strptime(birthday_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        selected_theme = request.POST.get('portfolio_theme')
        if selected_theme in ['modern', 'minimal', 'hacker']:
            profile.portfolio_theme = selected_theme

        profile.is_profile_public = True
        profile.save()
        messages.success(request, "Portfolio saved and published successfully!")
        return redirect('live_portfolio')

    if request.GET.get('generate_ai') == '1':
        suggestions = generate_portfolio_ai_content(profile, projects)

    return render(request, 'students/portfolio_builder.html', {
        'profile': profile,
        'suggestions': suggestions,
    })


# Update your existing live_portfolio view:
@login_required
def live_portfolio(request, username=None, enrollment=None, college_name=None):
    if username:
        try:
            target_user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('login')
    else:
        target_user = request.user

    if not hasattr(target_user, 'student_profile'):
        return HttpResponse("Error: This user does not have a student profile.", status=400)

    profile = target_user.student_profile
    projects = Project.objects.filter(student=profile, is_verified=True).select_related('student__user')
    public_blogs = BlogPost.objects.filter(student=profile, is_private=False).order_by('-created_at')

    theme_choice = getattr(profile, 'portfolio_theme', 'hacker') or 'hacker'
    theme_choice = str(theme_choice).strip().lower()
    template_name = f'students/themes/theme_{theme_choice}.html'

    try:
        get_template(template_name)
    except TemplateDoesNotExist:
        try:
            fallback_theme = 'students/themes/theme_hacker.html'
            get_template(fallback_theme)
            template_name = fallback_theme
        except TemplateDoesNotExist:
            template_name = 'students/portfolio_template.html'

    career_content = generate_portfolio_ai_content(profile, projects)
    return render(request, template_name, {
        'profile': profile,
        'projects': projects,
        'blogs': public_blogs,
        'career_statement': career_content.get('career_statement'),
        'public_portfolio_url': request.build_absolute_uri(profile.public_portfolio_url),
    })