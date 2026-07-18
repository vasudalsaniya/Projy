# CSquare — Testing & Review Guide

**Live URL:** https://c-square-d7re.vercel.app  
**Platform:** College project & placement management system  
**Roles:** Admin, HOD, Faculty, Student, Recruiter

---

## Quick Overview

CSquare connects colleges, students, faculty, and recruiters in one platform.

```
ADMIN
  └── Approves HODs and Recruiters
       └── HOD (Head of Department)
             └── Approves Faculty, assigns mentors, posts placements
                   └── FACULTY
                         └── Approves Students, reviews projects
                               └── STUDENT
                                     └── Creates projects, portfolio, resume
RECRUITER (approved by Admin)
  └── Searches verified students and their projects
```

---

## 1. Login Page (Starting Point)

**URL:** https://c-square-d7re.vercel.app

- All users log in from this single page using **email + password**
- After login, each role is redirected to their own dashboard
- Unverified users see a "Pending Verification" screen after login

---

## 2. User Roles & How to Create Accounts

### Role 1 — ADMIN (Superuser)
> Already created. Use these credentials.

| Field | Value |
|---|---|
| Email | dalsaniyavasu1234@gmail.com |
| Password | Vasu@3054 |
| Dashboard | /control-panel/ |

---

### Role 2 — HOD (Head of Department)

**Sign up at:** `/signup/college/` → select role **HOD**

**Required fields:**
- First name, Last name
- Email, Password
- College (select from list)
- Department (auto-loads after college selection)

**Verification:** Admin must approve before HOD can log in.

**To approve as Admin:**
1. Login as Admin → Control Panel
2. Find HOD in "Pending HODs" section → click **Approve**

---

### Role 3 — FACULTY

**Sign up at:** `/signup/college/` → select role **Faculty**

**Required fields:** Same as HOD

**Verification:** HOD of the same college/department must approve.

**To approve as HOD:**
1. Login as HOD → HOD Dashboard
2. See "Pending Faculty" list → click **Approve**

> Note: Faculty can only be approved if a verified HOD exists in the same department.

---

### Role 4 — STUDENT

**Sign up at:** `/signup/college/` → select role **Student**

**Required fields:**
- Name, Email, Password
- Enrollment Number
- College, Department, Semester

**Verification:** Faculty mentor (same department) must approve.

**To approve as Faculty:**
1. Login as Faculty → Faculty Dashboard
2. See "Pending Students" → click **Approve**

> Note: Students can only be approved if verified Faculty exist in the same department.

---

### Role 5 — RECRUITER

**Sign up at:** `/signup/recruiter/`

**Required fields:**
- Name, Email, Password
- Company Name, Location, Website

**Verification:** Admin must approve.

**To approve as Admin:**
1. Login as Admin → Control Panel
2. Find in "Pending Recruiters" → click **Approve**

---

## 3. Admin — Control Panel

**URL:** `/control-panel/`  
**Access:** Superuser only

### What Admin Can Do:

| Action | Where |
|---|---|
| Approve / Reject HODs | "Pending HODs" section |
| Approve / Reject Recruiters | "Pending Recruiters" section |
| Add College | "Add College" form |
| Add Department | "Add Department" form (select college first) |
| Add Company | "Add Company" form |
| Add User manually | "Add User" form |
| Delete College / Dept / Company / User | Respective tables |

### Dashboard Stats Shown:
- Total Students, Faculty, Projects
- Total Colleges, Companies
- Recent user registrations

---

## 4. HOD Dashboard

**URL:** `/college/dashboard/hod/`

### Features:

**1. Faculty Management**
- See all pending Faculty → Approve or Reject
- See all verified Faculty with their mentee counts

**2. Mentor Assignment**
- **Manual:** Select a mentor (Faculty) → select specific students → assign
- **Auto:** One click → system distributes all unassigned students equally across Faculty

**3. Placement Posting**
- Post job/internship opportunities for a specific semester
- Fields: Company name, Position, Description, Semester, Deadline
- Students of that semester will see it in their dashboard

**4. Analytics**
- Per-mentor breakdown: mentee count, verified projects, certificates, languages used
- Semester distribution chart
- Verification progress chart

**5. Settings**
- Update name and profile photo

---

## 5. Faculty Dashboard

**URL:** `/college/dashboard/faculty/`

### Features:

**1. Student Verification**
- See pending students in the department → Approve or Reject

**2. Project Review**
- See all submitted projects from mentees
- **Approve:** Mark project as verified
- **Add Remark:** Write feedback → student gets notified → must fix and resubmit

**3. Semester Change Approval**
- Students can request a semester change
- Faculty sees requests → **Approve** (updates semester) or **Reject**

**4. Placement View**
- See placement opportunities posted by HOD
- See which mentees have registered for each placement

**5. Mentee Analytics**
- Project count, certificate count, language distribution per mentee

**6. Settings**
- Update name and profile photo

---

## 6. Student Dashboard

**URL:** `/student/dashboard/`

### Features:

**1. Profile**
- Edit: Name, Bio, Skills, Job Title, Education, Location, Birthday
- Upload Resume (PDF)
- Add GitHub and LinkedIn links
- Request semester change (needs Faculty approval)

**2. Projects**
- Add project: Title, Description, Cover Image, Video Demo, GitHub Link, Source ZIP
- System auto-detects programming languages from uploaded ZIP
- Submit for faculty review → get approved or receive remarks
- If remarks received → fix and mark as "Revision Done"
- Add language breakdown manually (pie chart style, must total ≤ 100%)

**3. Blogs**
- Write blog posts with images
- Set as Public or Private
- Edit or delete anytime

**4. Certificates**
- Upload certificate image with title and description

**5. Todo List**
- Add tasks with due dates
- Mark complete / incomplete
- Get notified for overdue and due-today tasks

**6. Portfolio Builder**
- Choose theme: Modern / Minimal / Hacker
- Fill bio, skills, education details
- AI suggests improvements for bio and skills
- Generates a shareable public URL:  
  `/student/portfolio/<username>/<enrollment>/<college_name>/`

**7. Resume Generator**
- Generates resume from top 3 verified projects
- Choose style: Classic CV / Professional Modern / Focused One-Page
- AI writes career summary from your project data

**8. Placements**
- See opportunities posted by HOD for your semester
- Register or cancel registration

**9. Notifications**
- Bell icon shows unread notifications
- Click to go to the relevant page and mark as read

---

## 7. Recruiter Dashboard

**URL:** `/recruitment/dashboard/`

### Features:
- Search students by **project name** or **programming language**
- Filter by **College**
- Only sees verified students with public projects
- Can view student's:
  - Profile (skills, bio, location, job title)
  - Public projects with language breakdown
  - Public portfolio link
  - Resume

---

## 8. Recommended Testing Flow

Follow this order to test all features end to end:

```
Step 1 → Login as Admin
         → Add a College (e.g. "Test College")
         → Add a Department (e.g. "Computer Science")

Step 2 → Sign up as HOD (same college + department)
         → Login as Admin → Approve the HOD

Step 3 → Sign up as Faculty (same college + department)
         → Login as HOD → Approve the Faculty

Step 4 → Sign up as Student (same college + department)
         → Login as Faculty → Approve the Student

Step 5 → Login as HOD
         → Assign Faculty as mentor to the Student (Manual or Auto)
         → Post a placement opportunity

Step 6 → Login as Student
         → Add a project (upload a ZIP with code files)
         → Check auto-detected languages
         → Build portfolio → get share link
         → Generate resume
         → Register for the placement

Step 7 → Login as Faculty
         → Review the project → Add remark OR approve it
         → Approve student's semester change request (if any)

Step 8 → Login as Student
         → See the remark notification
         → Fix project → mark revision done (if Faculty added remark)

Step 9 → Sign up as Recruiter
         → Login as Admin → Approve the Recruiter

Step 10 → Login as Recruiter
          → Search for the student by language or project name
          → View their profile and portfolio
```

---

## 9. Key URLs Reference

| Page | URL |
|---|---|
| Login | `/` |
| College/HOD/Faculty/Student Signup | `/signup/college/` |
| Recruiter Signup | `/signup/recruiter/` |
| Admin Control Panel | `/control-panel/` |
| HOD Dashboard | `/college/dashboard/hod/` |
| Faculty Dashboard | `/college/dashboard/faculty/` |
| Student Dashboard | `/student/dashboard/` |
| Portfolio Builder | `/student/portfolio/builder/` |
| Resume Generator | `/student/generate-resume/` |
| Placements (Student) | `/student/placements/` |
| Recruiter Dashboard | `/recruitment/dashboard/` |
| Django Admin | `/admin/` |

---

## 10. Important Notes for Testing

1. **Verification is required** — new users cannot log in until approved by the right role
2. **College and Department must exist** before signing up as HOD/Faculty/Student — Admin creates these first
3. **Projects must be verified** by Faculty before they appear in Resume, Portfolio, or Recruiter search
4. **Mentor must be assigned** by HOD before Faculty can see students as mentees
5. **Portfolio is private** until you click "Save & Publish" in Portfolio Builder
6. **Media files (profile pics, project images)** may not persist on Vercel — this is a known limitation of the current hosting setup
7. **All emails** used for signup must be unique across all roles

---

*CSquare — Built with Django 6.0 + PostgreSQL (Neon) + Vercel*
