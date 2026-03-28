from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import StaffProfile, Department
from accounts.models import User, Notification
from students.models import StudentProfile, Project
from django.contrib import messages


# --- HOD DASHBOARD ---
@login_required
def hod_dashboard(request):
    if request.user.role != 'HOD' or not request.user.is_verified:
        return redirect('login')
    try:
        my_college = request.user.staff_profile.college
    except StaffProfile.DoesNotExist:
        return render(request, 'college/error.html', {'message': "No College Assigned"})
    
    # 1. Handle Mentor Allocation (POST Request)
    if request.method == 'POST' and 'assign_mentor' in request.POST:
        student_id = request.POST.get('student_id')
        faculty_id = request.POST.get('faculty_id')

        student = get_object_or_404(StudentProfile, id=student_id)
        faculty = get_object_or_404(User, id=faculty_id)
        if student.college == my_college and faculty.staff_profile.college == my_college:
            student.mentor = faculty
            student.save()
            return redirect('hod_dashboard')
            
    # 2. Get Data for Dashboard
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
    # Basic Security Check
    if request.user.role != 'FACULTY':
        return redirect('login')

    # Get mentees assigned to this faculty
    mentees = StudentProfile.objects.filter(mentor=request.user)

    # Get pending projects ONLY for these mentees
    pending_projects = Project.objects.filter(
        student__in=mentees, 
        is_verified=False
    ).order_by('-id')

    # Get semester update requests for mentees
    semester_requests = StudentProfile.objects.filter(
        mentor=request.user,
        pending_semester__isnull=False
    )

    # Safely find the college
    my_college = None
    try:
        my_college = request.user.staff_profile.college
    except:
        if mentees.exists():
            my_college = mentees.first().college 

    pending_students = []
    if my_college:
        pending_students = StudentProfile.objects.filter(
            college=my_college, 
            user__is_verified=False
        )

    context = {
        'college': my_college,
        'pending_students': pending_students,
        'semester_requests': semester_requests,
        'pending_projects': pending_projects,
    }
    
    return render(request, 'college/dashboard_faculty.html', context)


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