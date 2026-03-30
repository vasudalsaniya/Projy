from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import StaffProfile, Department
from accounts.models import User, Notification
from students.models import StudentProfile, Project
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
    
    # --- NEW: Bulk Assignment Logic ---
    if request.method == 'POST' and 'bulk_assign' in request.POST:
        assignments_json = request.POST.get('assignments_data', '{}')
        try:
            assignments = json.loads(assignments_json)
            for student_id, faculty_id in assignments.items():
                student = StudentProfile.objects.filter(id=student_id, college=my_college).first()
                faculty = User.objects.filter(id=faculty_id, staff_profile__college=my_college).first()
                if student and faculty:
                    student.mentor = faculty
                    student.save()
            messages.success(request, "Bulk mentor allocation saved successfully!")
        except json.JSONDecodeError:
            messages.error(request, "Invalid data submitted.")
        return redirect('hod_dashboard')
            
    # Get Data for Dashboard
    pending_faculty = User.objects.filter(role='FACULTY', is_verified=False, staff_profile__college=my_college)
    all_students = StudentProfile.objects.filter(college=my_college).select_related('user', 'mentor')
    verified_faculty = User.objects.filter(role='FACULTY', is_verified=True, staff_profile__college=my_college)
    
    context = {
        'college': my_college,
        'pending_faculty': pending_faculty,
        'all_students': all_students,
        'verified_faculty': verified_faculty
    }
    return render(request, 'college/dashboard_hod.html', context)


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