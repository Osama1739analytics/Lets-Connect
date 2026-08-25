from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from home.models import CustomUser, Session


class Command(BaseCommand):
    help = 'Seeds sample open sessions for the browse section (6 mentor posts, 4 mentee requests)'

    def handle(self, *args, **options):
        mentor = CustomUser.objects.filter(user_type='mentor', is_superuser=False).first()
        if not mentor:
            mentor = CustomUser.objects.create_user(
                username='demo_mentor',
                email='demo.mentor@letsconnect.com',
                password='Password123',
                full_name='Demo Mentor',
                user_type='mentor',
                is_onboarded=True,
                mentor_expertise='Python, Career Coaching, Public Speaking',
            )
            self.stdout.write(self.style.SUCCESS('Created demo mentor account: demo_mentor'))

        mentees = list(CustomUser.objects.filter(user_type='mentee', is_superuser=False)[:2])
        if not mentees:
            mentees = [
                CustomUser.objects.create_user(
                    username='demo_mentee',
                    email='demo.mentee@letsconnect.com',
                    password='Password123',
                    full_name='Demo Mentee',
                    user_type='mentee',
                    is_onboarded=True,
                    learning_goals='Career growth and technical skills',
                )
            ]
            self.stdout.write(self.style.SUCCESS('Created demo mentee account: demo_mentee'))

        mentee_a = mentees[0]
        mentee_b = mentees[1] if len(mentees) > 1 else mentee_a
        now = timezone.now()

        mentor_posts = [
            {
                'subject_detail': 'Python Data Structures Deep Dive',
                'nature': 'course',
                'description': (
                    'Walk through lists, dictionaries, sets, and algorithmic thinking with practical '
                    'coding exercises. Ideal for CS students preparing for technical interviews.'
                ),
                'duration_minutes': 60,
                'days_ahead': 7,
                'hour': 10,
                'tags': ['python', 'data-structures', 'programming'],
            },
            {
                'subject_detail': 'Machine Learning Foundations Workshop',
                'nature': 'course',
                'description': (
                    'Intro session covering supervised learning, model evaluation, and scikit-learn basics. '
                    'Bring your laptop and a dataset you want to explore.'
                ),
                'duration_minutes': 90,
                'days_ahead': 10,
                'hour': 14,
                'tags': ['machine-learning', 'python', 'ai'],
            },
            {
                'subject_detail': 'Resume & LinkedIn Profile Review',
                'nature': 'career',
                'description': (
                    'Get actionable feedback on your CV layout, bullet points, and LinkedIn headline. '
                    'We will tailor your profile for internship and graduate role applications.'
                ),
                'duration_minutes': 45,
                'days_ahead': 13,
                'hour': 11,
                'tags': ['resume', 'linkedin', 'career'],
            },
            {
                'subject_detail': 'Technical Interview Prep (FAANG Style)',
                'nature': 'career',
                'description': (
                    'Mock interview covering data structures, system design basics, and behavioral questions. '
                    'Practice communicating your thought process under time pressure.'
                ),
                'duration_minutes': 75,
                'days_ahead': 15,
                'hour': 16,
                'tags': ['interview', 'career', 'coding'],
            },
            {
                'subject_detail': 'Public Speaking & Presentation Skills',
                'nature': 'general',
                'description': (
                    'Build confidence delivering project demos, thesis defenses, and team updates. '
                    'Includes structure tips, voice control, and handling Q&A sessions.'
                ),
                'duration_minutes': 30,
                'days_ahead': 17,
                'hour': 9,
                'tags': ['communication', 'presentation', 'soft-skills'],
            },
            {
                'subject_detail': 'Work-Life Balance for Final-Year Students',
                'nature': 'general',
                'description': (
                    'Strategies for managing FYP deadlines, part-time work, and personal wellbeing. '
                    'We will build a realistic weekly plan you can follow through exam season.'
                ),
                'duration_minutes': 45,
                'days_ahead': 20,
                'hour': 15,
                'flexibility_comments': 'Can start 30 minutes earlier if needed.',
                'tags': ['productivity', 'wellbeing', 'study'],
            },
        ]

        mentee_requests = [
            {
                'initiator': mentee_a,
                'subject_detail': 'Help with Django REST Framework APIs',
                'nature': 'course',
                'description': (
                    'I am building a final-year project with DRF and need guidance on serializers, '
                    'authentication, and nested routes. Looking for a mentor who has shipped Django apps.'
                ),
                'duration_minutes': 60,
                'days_ahead': 9,
                'hour': 13,
                'tags': ['django', 'python', 'web-development'],
            },
            {
                'initiator': mentee_b,
                'subject_detail': 'Calculus II Exam Preparation',
                'nature': 'course',
                'description': (
                    'Need support with integration techniques, series, and past paper problem solving. '
                    'Prefer step-by-step explanations and weekly accountability check-ins.'
                ),
                'duration_minutes': 45,
                'days_ahead': 11,
                'hour': 17,
                'tags': ['mathematics', 'calculus', 'exam-prep'],
            },
            {
                'initiator': mentee_a,
                'subject_detail': 'Career Switch from Finance to Tech',
                'nature': 'career',
                'description': (
                    'I have two years in banking and want to move into software engineering. '
                    'Looking for a roadmap, portfolio advice, and honest feedback on my transition plan.'
                ),
                'duration_minutes': 90,
                'days_ahead': 14,
                'hour': 10,
                'flexibility_comments': 'Available weekday evenings as an alternative.',
                'tags': ['career-change', 'finance', 'tech'],
            },
            {
                'initiator': mentee_b,
                'subject_detail': 'Time Management for Final Year',
                'nature': 'general',
                'description': (
                    'Balancing coursework, job applications, and family commitments has been overwhelming. '
                    'I want help prioritizing tasks and building sustainable daily habits.'
                ),
                'duration_minutes': 30,
                'days_ahead': 19,
                'hour': 18,
                'tags': ['productivity', 'planning', 'student-life'],
            },
        ]

        created_count = 0
        updated_count = 0

        for entry in mentor_posts:
            scheduled_at = now + timedelta(days=entry['days_ahead'])
            scheduled_at = scheduled_at.replace(
                hour=entry['hour'], minute=0, second=0, microsecond=0
            )
            session, created = Session.objects.update_or_create(
                subject_detail=entry['subject_detail'],
                session_type='post',
                defaults={
                    'initiator': mentor,
                    'nature': entry['nature'],
                    'description': entry['description'],
                    'scheduled_at': scheduled_at,
                    'duration_minutes': entry['duration_minutes'],
                    'flexibility_comments': entry.get('flexibility_comments', ''),
                    'status': 'open',
                    'payment_status': 'unpaid',
                },
            )
            session.tags.set(entry['tags'])
            if created:
                created_count += 1
            else:
                updated_count += 1

        for entry in mentee_requests:
            scheduled_at = now + timedelta(days=entry['days_ahead'])
            scheduled_at = scheduled_at.replace(
                hour=entry['hour'], minute=0, second=0, microsecond=0
            )
            session, created = Session.objects.update_or_create(
                subject_detail=entry['subject_detail'],
                session_type='request',
                defaults={
                    'initiator': entry['initiator'],
                    'nature': entry['nature'],
                    'description': entry['description'],
                    'scheduled_at': scheduled_at,
                    'duration_minutes': entry['duration_minutes'],
                    'flexibility_comments': entry.get('flexibility_comments', ''),
                    'status': 'open',
                    'payment_status': 'unpaid',
                },
            )
            session.tags.set(entry['tags'])
            if created:
                created_count += 1
            else:
                updated_count += 1

        open_posts = Session.objects.filter(status='open', session_type='post').count()
        open_requests = Session.objects.filter(status='open', session_type='request').count()

        self.stdout.write(
            self.style.SUCCESS(
                f'Seed complete: {created_count} created, {updated_count} updated. '
                f'Open browse sessions — mentor posts: {open_posts}, mentee requests: {open_requests}.'
            )
        )
