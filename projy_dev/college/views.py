from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import StaffProfile, Department
from accounts.models import User, Notification
from students.models import StudentProfile, Project, ProjectLanguage, Certificate, CompanyPlacement, PlacementRegistration
from django.contrib import messages
from django.db.models import Count, Q
import json


@login_required
def hod_dashboard(request):
    if request.user.role != 'HOD' or not request.user.is_verified:
        return redirect('login')

    try:
        my_college = request.user.staff_profile.college
        my_department = request.user.staff_profile.department
    except StaffProfile.DoesNotExist:
        return render(request, 'college/error.html', {'message': "No College Assigned"})

    pending_faculty = User.objects.filter(
        role='FACULTY', is_verified=False,
        staff_profile__college=my_college,
        staff_profile__department=my_department
    ).only('id', 'username', 'email')

    verified_faculty = User.objects.filter(
        role='FACULTY', is_verified=True,
        staff_profile__college=my_college,
        staff_profile__department=my_department
    ).only('id', 'username', 'email', 'first_name', 'last_name')

    all_students = StudentProfile.objects.filter(
        college=my_college,
        department=my_department
    ).select_related('user', 'mentor')

    unassigned_students_count = all_students.filter(mentor__isnull=True).count()
    total_verified_projects = Project.objects.filter(
        student__college=my_college,
        student__department=my_department,
        is_verified=True
    ).count()
    total_hod_verifications = verified_faculty.count()

    placements = CompanyPlacement.objects.filter(
        department=my_department
    ).annotate(registration_count=Count('registrations'))

    verification_chart = {
        'labels': ['Verified Faculty', 'Pending Faculty'],
        'values': [total_hod_verifications, pending_faculty.count()],
    }

    mentor_analytics = {}
    for mentor in verified_faculty:
        mentees_qs = all_students.filter(mentor=mentor).select_related('user')
        mentees_count = mentees_qs.count()
        verified_projects_count = Project.objects.filter(student__in=mentees_qs, is_verified=True).count()
        verified_certificates_count = Certificate.objects.filter(student__in=mentees_qs).count()

        from django.db.models import Sum
        lang_counts = (
            ProjectLanguage.objects
            .filter(project__student__in=mentees_qs)
            .values('language_name')
            .annotate(total=Sum('percentage'))
            .order_by('-total')[:6]
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
        'total_faculty_count': verified_faculty.count(),
        'dept_mentee_count': all_students.count(),
        'unassigned_count': unassigned_students_count,
        'pending_faculty': pending_faculty,
        'dept_pending_verifications': pending_faculty.count(),
        'dept_total_verified': total_hod_verifications,
        'placements': placements,
        'verification_chart': verification_chart,
        'verification_chart_json': json.dumps(verification_chart),
        'mentor_analytics_json': json.dumps(mentor_analytics),
        'activity_logs': activity_logs,
        'total_verified_projects': total_verified_projects,
    }
    return render(request, 'college/dashboard_hod.html', context)


@login_required
def hod_add_placement(request):
    if request.method == 'POST' and request.user.role == 'HOD':
        company_name = request.POST.get('company_name', '').strip()
        position = request.POST.get('position', '').strip()
        description = request.POST.get('description', '').strip()
        semester = request.POST.get('semester')
        application_deadline = request.POST.get('application_deadline')

        try:
            semester = int(semester)
        except (TypeError, ValueError):
            semester = 1

        try:
            my_college = request.user.staff_profile.college
            my_department = request.user.staff_profile.department
            placement = CompanyPlacement.objects.create(
                hod=request.user,
                company_name=company_name or 'New Company',
                position=position,
                department=my_department,
                semester=semester,
                description=description,
                application_deadline=application_deadline or None,
                is_active=True,
            )
            messages.success(request, f"Placement posted for {placement.company_name}.")
            Notification.objects.create(
                user=request.user,
                message=f"Added placement opportunity: {placement.company_name}.",
                link="/college/dashboard/hod/"
            )
        except Exception:
            messages.error(request, "Unable to add placement opportunity. Please check the details.")

    return redirect('hod_dashboard')


@login_required
def hod_delete_placement(request, placement_id):
    if request.method == 'POST' and request.user.role == 'HOD':
        try:
            placement = CompanyPlacement.objects.get(id=placement_id, hod=request.user)
            placement.delete()
            messages.success(request, f"Removed {placement.company_name} from placement listings.")
        except CompanyPlacement.DoesNotExist:
            messages.error(request, "Placement not found or cannot be removed.")

    return redirect('hod_dashboard')


@login_required
def manual_assign(request):
    if request.method == 'POST' and request.user.role == 'HOD':
        mentor_id = request.POST.get('selected_mentor')
        student_ids = request.POST.getlist('student_ids')

        if mentor_id and student_ids:
            try:
                my_college = request.user.staff_profile.college
                my_department = request.user.staff_profile.department
                mentor = User.objects.get(
                    id=mentor_id, role='FACULTY',
                    staff_profile__college=my_college,
                    staff_profile__department=my_department
                )

                updated_count = StudentProfile.objects.filter(
                    id__in=student_ids,
                    college=my_college,
                    department=my_department
                ).update(mentor=mentor)

                messages.success(request, f"Assigned {updated_count} students to {mentor.get_full_name() or mentor.username}.")
                Notification.objects.create(
                    user=request.user,
                    message=f"Assigned {updated_count} student(s) to {mentor.get_full_name() or mentor.username}.",
                    link="/college/dashboard/hod/"
                )
            except User.DoesNotExist:
                messages.error(request, "Mentor not found.")
        else:
            messages.error(request, "Select mentor and students.")

    return redirect('hod_dashboard')


@login_required
def auto_assign(request):
    if request.method == 'POST' and request.user.role == 'HOD':
        my_college = request.user.staff_profile.college
        my_department = request.user.staff_profile.department
        mentors = list(
            User.objects.filter(
                role='FACULTY', is_verified=True,
                staff_profile__college=my_college,
                staff_profile__department=my_department
            ).values_list('id', flat=True)
        )
        unassigned_students = StudentProfile.objects.filter(
            college=my_college,
            department=my_department,
            mentor__isnull=True
        ).values_list('id', flat=True)

        if not mentors:
            messages.error(request, "No active mentors available.")
            return redirect('hod_dashboard')

        assignments = [
            StudentProfile(id=student_id, mentor_id=mentors[i % len(mentors)])
            for i, student_id in enumerate(unassigned_students)
        ]

        StudentProfile.objects.bulk_update(assignments, ['mentor'], batch_size=100)

        count = len(assignments)
        messages.success(request, f"Auto-assigned {count} students!")
        Notification.objects.create(
            user=request.user,
            message=f"Auto-assigned {count} student(s).",
            link="/college/dashboard/hod/"
        )

    return redirect('hod_dashboard')


@login_required
def faculty_dashboard(request):
    if request.user.role != 'FACULTY':
        return redirect('login')

    mentees = StudentProfile.objects.filter(mentor=request.user).annotate(
        verified_project_count=Count('projects', filter=Q(projects__is_verified=True)),
        pending_request_count=Count('projects', filter=Q(projects__is_verified=False))
    ).select_related('user', 'college')

    pending_projects = Project.objects.filter(
        student__in=mentees, is_verified=False
    ).select_related('student__user').prefetch_related('languages').order_by('-created_at')

    total_verified_projects = Project.objects.filter(
        student__in=mentees, is_verified=True
    ).count()

    semester_requests = StudentProfile.objects.filter(
        mentor=request.user, pending_semester__isnull=False
    ).select_related('user')

    my_college = None
    try:
        my_college = request.user.staff_profile.college
    except StaffProfile.DoesNotExist:
        if mentees.exists():
            my_college = mentees.first().college

    pending_students = []
    placements = []
    if my_college:
        try:
            my_department = request.user.staff_profile.department
            pending_students = StudentProfile.objects.filter(
                college=my_college,
                department=my_department,
                user__is_verified=False
            ).select_related('user')
            placements = CompanyPlacement.objects.filter(
                department=my_department,
                is_active=True
            ).annotate(
                registration_count=Count('registrations'),
                mentee_registrations=Count('registrations', filter=Q(registrations__student__mentor=request.user))
            )
        except StaffProfile.DoesNotExist:
            pending_students = []
            placements = []

    context = {
        'college': my_college,
        'mentees': mentees,
        'pending_students': pending_students,
        'semester_requests': semester_requests,
        'pending_projects': pending_projects,
        'total_verified_projects': total_verified_projects,
        'department_placements': placements,
    }

    return render(request, 'college/dashboard_faculty.html', context)


@login_required
def faculty_settings_update(request):
    if request.method == 'POST' and request.user.role == 'FACULTY':
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)

        if 'profile_pic' in request.FILES:
            request.user.profile_pic = request.FILES['profile_pic']

        request.user.save(update_fields=['first_name', 'last_name', 'profile_pic'])
        messages.success(request, "Profile updated.")

    return redirect('faculty_dashboard')


@login_required
def hod_settings_update(request):
    if request.method == 'POST' and request.user.role == 'HOD':
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)

        if 'profile_pic' in request.FILES:
            request.user.profile_pic = request.FILES['profile_pic']

        request.user.save(update_fields=['first_name', 'last_name', 'profile_pic'])
        messages.success(request, "Profile updated.")

    return redirect('hod_dashboard')

@login_required
def approve_semester_change(request, student_id, action):
    try:
        student = StudentProfile.objects.select_related('user', 'mentor').get(id=student_id)
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect('faculty_dashboard')

    if request.user != student.mentor:
        return redirect('faculty_dashboard')

    if action == 'approve':
        student.semester = student.pending_semester
        student.pending_semester = None
        student.save(update_fields=['semester', 'pending_semester'])
        messages.success(request, f"Updated semester for {student.user.first_name}.")
    elif action == 'reject':
        student.pending_semester = None
        student.save(update_fields=['pending_semester'])
        messages.error(request, "Semester change rejected.")

    return redirect('faculty_dashboard')


@login_required
def approve_user(request, user_id):
    try:
        target_user = User.objects.select_related('staff_profile').get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('login')

    current_user = request.user

    if current_user.role == 'HOD' and target_user.role == 'FACULTY':
        try:
            if (
                current_user.staff_profile.college == target_user.staff_profile.college and
                current_user.staff_profile.department == target_user.staff_profile.department
            ):
                target_user.is_verified = True
                target_user.save(update_fields=['is_verified'])
                Notification.objects.create(
                    user=current_user,
                    message=f"Verified faculty {target_user.get_full_name() or target_user.username}.",
                    link="/college/dashboard/hod/"
                )
                return redirect('hod_dashboard')
        except StaffProfile.DoesNotExist:
            messages.error(request, "Staff profile not found.")

    elif current_user.role == 'FACULTY' and target_user.role == 'STUDENT':
        try:
            if (
                current_user.staff_profile.college == target_user.student_profile.college and
                current_user.staff_profile.department == target_user.student_profile.department
            ):
                target_user.is_verified = True
                target_user.save(update_fields=['is_verified'])
                return redirect('faculty_dashboard')
        except (StaffProfile.DoesNotExist, AttributeError):
            messages.error(request, "Authorization failed.")

    return redirect('login') 


def load_departments(request):
    college_id = request.GET.get('college')
    if not college_id:
        return JsonResponse([], safe=False)
    try:
        college_id = int(college_id)
    except (ValueError, TypeError):
        return JsonResponse([], safe=False)
    departments = Department.objects.filter(college_id=college_id).values('id', 'name').order_by('name')
    return JsonResponse(list(departments), safe=False)


@login_required
def approve_project(request, project_id):
    try:
        project = Project.objects.select_related('student__user', 'student__mentor').get(id=project_id)
    except Project.DoesNotExist:
        messages.error(request, "Project not found.")
        return redirect('faculty_dashboard')

    if not project.student.mentor:
        messages.error(request, "Project has no assigned mentor.")
        return redirect('faculty_dashboard')

    if request.user == project.student.mentor:
        project.is_verified = True
        project.needs_revision = False
        project.save(update_fields=['is_verified', 'needs_revision'])

        Notification.objects.create(
            user=project.student.user,
            message=f"✅ Your project '{project.title}' was verified!",
            link="/student/dashboard/"
        )
        messages.success(request, "Project approved!")
        return redirect('faculty_dashboard')
    else:
        messages.error(request, "You are not the mentor for this student.")
        return redirect('faculty_dashboard')


@login_required
def add_project_remark(request, project_id):
    try:
        project = Project.objects.select_related('student__user').get(id=project_id)
    except Project.DoesNotExist:
        messages.error(request, "Project not found.")
        return redirect('faculty_dashboard')

    if request.method == 'POST':
        remarks = request.POST.get('remarks', '').strip()
        if remarks:
            project.faculty_remarks = remarks
            project.needs_revision = True
            project.save(update_fields=['faculty_remarks', 'needs_revision'])

            Notification.objects.create(
                user=project.student.user,
                message=f"📝 Faculty left remarks on '{project.title}'",
                link="/student/dashboard/"
            )
            messages.warning(request, "Remarks sent to student.")
        else:
            messages.error(request, "Remarks cannot be empty.")

    return redirect('faculty_dashboard')