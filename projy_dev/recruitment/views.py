from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from students.models import StudentProfile, ProjectLanguage
from college.models import College

@login_required
def recruiter_dashboard(request):
    if request.user.role != 'RECRUITER' or not request.user.is_verified:
        return redirect('login')

    query = request.GET.get('q', '')
    college_filter = request.GET.get('college', '')

    students_qs = StudentProfile.objects.filter(
        user__is_verified=True,
        projects__is_public=True
    ).select_related('user', 'college', 'department').distinct()

    if query:
        students_qs = students_qs.filter(
            Q(projects__title__icontains=query) |
            Q(projects__languages__language_name__icontains=query)
        ).distinct()

    if college_filter:
        students_qs = students_qs.filter(college__id=college_filter)

    # Materialise queryset and attach unique language names to avoid N+1 and duplicates
    students = list(students_qs)
    ids = [s.id for s in students]
    lang_map = {}
    for row in (
        ProjectLanguage.objects
        .filter(project__student_id__in=ids, project__is_public=True)
        .values('project__student_id', 'language_name')
        .distinct()
    ):
        lang_map.setdefault(row['project__student_id'], set()).add(row['language_name'])

    for student in students:
        student.unique_langs = sorted(lang_map.get(student.id, []))

    all_colleges = College.objects.all().order_by('name')

    context = {
        'students': students,
        'all_colleges': all_colleges,
        'query': query,
        'selected_college': int(college_filter) if college_filter else None,
    }
    return render(request, 'recruitment/dashboard_recruiter.html', context)
