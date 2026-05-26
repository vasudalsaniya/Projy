from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0012_studentprofile_birthday_studentprofile_job_title_and_more'),
    ]

    operations = [
        # Add created_at and updated_at to Project
        migrations.AddField(
            model_name='project',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),

        # Add db_index to frequently filtered fields
        migrations.AlterField(
            model_name='studentprofile',
            name='enrollment_number',
            field=models.CharField(db_index=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='studentprofile',
            name='semester',
            field=models.IntegerField(db_index=True, default=1),
        ),
        migrations.AlterField(
            model_name='studentprofile',
            name='is_profile_public',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='project',
            name='title',
            field=models.CharField(db_index=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='project',
            name='is_public',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='is_verified',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='project',
            name='needs_revision',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='title',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='is_private',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='certificate',
            name='title',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='certificate',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='todoitem',
            name='is_completed',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='todoitem',
            name='due_date',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),

        # Composite indexes — all must have a name
        migrations.AddIndex(
            model_name='studentprofile',
            index=models.Index(fields=['college', 'semester'], name='sp_college_semester_idx'),
        ),
        migrations.AddIndex(
            model_name='studentprofile',
            index=models.Index(fields=['mentor', 'is_profile_public'], name='sp_mentor_public_idx'),
        ),
        migrations.AddIndex(
            model_name='project',
            index=models.Index(fields=['student', '-created_at'], name='proj_student_created_idx'),
        ),
        migrations.AddIndex(
            model_name='project',
            index=models.Index(fields=['is_verified', 'is_public'], name='proj_verified_public_idx'),
        ),
        migrations.AddIndex(
            model_name='blogpost',
            index=models.Index(fields=['student', '-created_at'], name='blog_student_created_idx'),
        ),
        migrations.AddIndex(
            model_name='blogpost',
            index=models.Index(fields=['is_private', '-created_at'], name='blog_private_created_idx'),
        ),
        migrations.AddIndex(
            model_name='certificate',
            index=models.Index(fields=['student', '-created_at'], name='cert_student_created_idx'),
        ),
        migrations.AddIndex(
            model_name='todoitem',
            index=models.Index(fields=['student', 'is_completed', 'due_date'], name='todo_student_status_idx'),
        ),
    ]
