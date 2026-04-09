from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import StaffProfile, Department
from accounts.models import User, Notification
from students.models import StudentProfile, Project, ProjectLanguage, Certificate
from django.contrib import messages
from django.db.models import Count, Q
import json


# --- HOD DASHBOARD ---
@login_required
def hod_dashboard(request):
    if request.user.role != 'HOD' or not request.user.is_verified:
        return redirect('login')
        
    try:
        my_college = request.user.staff_profile.college
    except StaffProfile.DoesNotExist:
        return render(request, 'college/error.html', {'message': "No College Assigned"})
            
    # Fetch Real Data for the Dashboard Context
    pending_faculty = User.objects.filter(role='FACULTY', is_verified=False, staff_profile__college=my_college)
    verified_faculty = User.objects.filter(role='FACULTY', is_verified=True, staff_profile__college=my_college)
    all_students = StudentProfile.objects.filter(college=my_college).select_related('user', 'mentor')
    pending_students = all_students.filter(user__is_verified=False)
    
    unassigned_students_count = all_students.filter(mentor__isnull=True).count()

    total_verified_projects = Project.objects.filter(student__college=my_college, is_verified=True).count()

    # HOD-facing verifications: currently this dashboard approves faculty records.
    total_hod_verifications = verified_faculty.count()

    # Overview chart data
    verification_chart = {
        'labels': ['Verified Faculty', 'Pending Faculty'],
        'values': [total_hod_verifications, pending_faculty.count()],
    }

    # Faculty profile stats + charts (mentor-wise)
    mentor_analytics = {}
    for mentor in verified_faculty:
        mentees_qs = all_students.filter(mentor=mentor).select_related('user')
        mentees_count = mentees_qs.count()
        verified_projects_count = Project.objects.filter(student__in=mentees_qs, is_verified=True).count()
        verified_certificates_count = Certificate.objects.filter(student__in=mentees_qs).count()

        lang_counts = (
            ProjectLanguage.objects
            .filter(project__student__in=mentees_qs)
            .values('language_name')
            .annotate(total=Count('id'))
            .order_by('-total')[:5]
        )
        lang_labels = [item['language_name'] for item in lang_counts] or ['No Data']
        lang_values = [item['total'] for item in lang_counts] or [1]

        semester_counts = (
            mentees_qs.values('semester')
            .annotate(total=Count('id'))
            .order_by('semester')
        )
        field_labels = [f"Sem {item['semester']}" for item in semester_counts] or ['No Data']
        field_values = [item['total'] for item in semester_counts] or [1]

        mentor_analytics[str(mentor.id)] = {
            'mentees': mentees_count,
            'verified_projects': verified_projects_count,
            'verified_certificates': verified_certificates_count,
            'lang_labels': lang_labels,
            'lang_values': lang_values,
            'field_labels': field_labels,
            'field_values': field_values,
            'email': mentor.email or '',
        }

    activity_logs = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]

    context = {
        'profile': request.user.staff_profile,
        'college': my_college,
        'mentors': verified_faculty,
        'students': all_students,
        'pending_students': pending_students,
        'total_faculty_count': verified_faculty.count(),
        'dept_mentee_count': all_students.count(),
        'unassigned_count': unassigned_students_count,
        'pending_faculty': pending_faculty,
        'dept_pending_verifications': pending_faculty.count(),
        'dept_total_verified': total_hod_verifications,
        'verification_chart': verification_chart,
        'verification_chart_json': json.dumps(verification_chart),
        'mentor_analytics_json': json.dumps(mentor_analytics),
        'activity_logs': activity_logs,
        'total_verified_projects': total_verified_projects,
    }
    return render(request, 'college/dashboard_hod.html', context)


@login_required
def manual_assign(request):
    if request.method == 'POST' and request.user.role == 'HOD':
        mentor_id = request.POST.get('selected_mentor')
        student_ids = request.POST.getlist('student_ids') # Gets all checked checkboxes
        
        if mentor_id and student_ids:
            mentor = get_object_or_404(User, id=mentor_id, role='FACULTY')
            my_college = request.user.staff_profile.college
            updated_count = StudentProfile.objects.filter(
                id__in=student_ids,
                college=my_college
            ).update(mentor=mentor)
            messages.success(request, f"Successfully assigned {len(student_ids)} students to Prof. {mentor.last_name}.")
            Notification.objects.create(
                user=request.user,
                message=f"You assigned {updated_count} student(s) to {mentor.get_full_name() or mentor.username}.",
                link="/college/dashboard/hod/"
            )
        else:
            messages.error(request, "Please select a mentor and at least one student.")
            
    return redirect('hod_dashboard')


@login_required
def auto_assign(request):
    if request.method == 'POST' and request.user.role == 'HOD':
        my_college = request.user.staff_profile.college
        mentors = list(User.objects.filter(role='FACULTY', is_verified=True, staff_profile__college=my_college))
        unassigned_students = StudentProfile.objects.filter(college=my_college, mentor__isnull=True)
        
        if not mentors:
            messages.error(request, "No active mentors available for assignment.")
            return redirect('hod_dashboard')
            
        count = 0
        for i, student in enumerate(unassigned_students):
            # Round Robin logic
            mentor = mentors[i % len(mentors)]
            student.mentor = mentor
            student.save()
            count += 1
            
        messages.success(request, f"Auto-assigned {count} students using Round Robin!")
        Notification.objects.create(
            user=request.user,
            message=f"You auto-assigned {count} unassigned student(s).",
            link="/college/dashboard/hod/"
        )
    return redirect('hod_dashboard')


# --- FACULTY DASHBOARD ---
@login_required
def faculty_dashboard(request):
    if request.user.role != 'FACULTY':
        return redirect('login')

    # Annotate mentees with dynamic counts
    mentees = StudentProfile.objects.filter(mentor=request.user).annotate(
        verified_project_count=Count('projects', filter=Q(projects__is_verified=True)),
        pending_request_count=Count('projects', filter=Q(projects__is_verified=False))
    )

    pending_projects = Project.objects.filter(student__in=mentees, is_verified=False).order_by('-id')
    
    # Calculate Total Verified Projects for all mentees
    total_verified_projects = Project.objects.filter(student__in=mentees, is_verified=True).count()

    semester_requests = StudentProfile.objects.filter(mentor=request.user, pending_semester__isnull=False)

    my_college = None
    try:
        my_college = request.user.staff_profile.college
    except:
        if mentees.exists():
            my_college = mentees.first().college 

    pending_students = []
    if my_college:
        pending_students = StudentProfile.objects.filter(college=my_college, user__is_verified=False)

    context = {
        'college': my_college,
        'mentees': mentees,
        'pending_students': pending_students,
        'semester_requests': semester_requests,
        'pending_projects': pending_projects,
        'total_verified_projects': total_verified_projects, # Pass total to template
    }
    
    return render(request, 'college/dashboard_faculty.html', context)


# --- NEW: Faculty Settings View ---
@login_required
def faculty_settings_update(request):
    if request.method == 'POST' and request.user.role == 'FACULTY':
        # Update User fields
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        
        # Handle Profile Picture
        if 'profile_pic' in request.FILES:
            request.user.profile_pic = request.FILES['profile_pic']
            
        request.user.save()
        messages.success(request, "Your profile settings have been updated.")
        
    return redirect('faculty_dashboard')

@login_required
def approve_semester_change(request, student_id, action):
    student = get_object_or_404(StudentProfile, id=student_id)
    
    # Security: Only mentor can approve
    if request.user != student.mentor:
        return redirect('faculty_dashboard')

    if action == 'approve':
        student.semester = student.pending_semester
        student.pending_semester = None
        student.save()
        messages.success(request, f"Updated semester for {student.user.first_name}.")
    elif action == 'reject':
        student.pending_semester = None
        student.save()
        messages.error(request, "Semester change request rejected.")
        
    return redirect('faculty_dashboard')


# --- APPROVAL ACTIONS ---
@login_required
def approve_user(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    current_user = request.user

    # Logic 1: HOD approving Faculty
    if current_user.role == 'HOD' and target_user.role == 'FACULTY':
        if current_user.staff_profile.college == target_user.staff_profile.college:
            target_user.is_verified = True
            target_user.save()
            Notification.objects.create(
                user=current_user,
                message=f"You verified faculty {target_user.get_full_name() or target_user.username}.",
                link="/college/dashboard/hod/"
            )
            return redirect('hod_dashboard')

    # Logic 2: Faculty approving Student
    elif current_user.role == 'FACULTY' and target_user.role == 'STUDENT':
        if current_user.staff_profile.college == target_user.student_profile.college:
            target_user.is_verified = True
            target_user.save()
            return redirect('faculty_dashboard')

    return redirect('login') 


def load_departments(request):
    college_id = request.GET.get('college')
    departments = Department.objects.filter(college_id=college_id).order_by('name')
    return JsonResponse(list(departments.values('id', 'name')), safe=False)


# Combined and fixed project approval function
@login_required
def approve_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    # Security: Only the assigned MENTOR can approve
    if request.user == project.student.mentor:
        project.is_verified = True
        project.needs_revision = False
        project.save()
        
        # Notify the student
        Notification.objects.create(
            user=project.student.user,
            message=f"Success! Your project '{project.title}' was verified.",
            link="/student/dashboard/"
        )
        messages.success(request, "Project Approved successfully.")
        return redirect('faculty_dashboard')
    else:
        messages.error(request, "You are not the assigned mentor for this student.")
        return redirect('faculty_dashboard')


@login_required
def add_project_remark(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        remarks = request.POST.get('remarks')
        project.faculty_remarks = remarks
        project.needs_revision = True
        project.save()
        
        # Send Notification to Student
        Notification.objects.create(
            user=project.student.user,
            message=f"Faculty left remarks on your project: {project.title}",
            link="/student/dashboard/"
        )
        messages.warning(request, "Remarks sent. Project pushed back to student.")
        
    return redirect('faculty_dashboard')