from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from students.models import StudentProfile
from college.models import College

@login_required
def recruiter_dashboard(request):
    # Security: Only verified Recruiters can see this
    if request.user.role != 'RECRUITER' or not request.user.is_verified:
        return redirect('login')

    # 1. Get Search Parameters
    query = request.GET.get('q', '') # e.g., "Python"
    college_filter = request.GET.get('college', '')

    # 2. Base Query: Only show verified students who have at least one public project
    students = StudentProfile.objects.filter(
        user__is_verified=True,
        projects__is_public=True
    ).distinct()

    # 3. Apply Filters
    if query:
        # Search inside Project Titles OR Project Languages (Skills)
        students = students.filter(
            Q(projects__title__icontains=query) | 
            Q(projects__languages__language_name__icontains=query)
        ).distinct()

    if college_filter:
        students = students.filter(college__id=college_filter)

    # 4. Get List of Colleges for the dropdown
    all_colleges = College.objects.all()

    context = {
        'students': students,
        'all_colleges': all_colleges,
        'query': query, # Pass back so search bar keeps the text
        'selected_college': int(college_filter) if college_filter else None
    }
    return render(request, 'recruitment/dashboard_recruiter.html', context)