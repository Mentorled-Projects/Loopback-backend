# Generated by Django 5.2 on 2025-06-23 07:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='mentorshipfeedback',
            old_name='comments',
            new_name='review',
        ),
        migrations.RemoveField(
            model_name='mentorshipfeedback',
            name='successful',
        ),
        migrations.AlterField(
            model_name='mentorshipfeedback',
            name='rate',
            field=models.CharField(choices=[('excellent', 'Excellent'), ('very good', 'Very good'), ('good', 'Good'), ('fair', 'Fair')], default='good', max_length=10),
        ),
    ]
