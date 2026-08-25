from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from home.models import CustomUser, Session

class Command(BaseCommand):
    help = 'Create sample sessions for testing admin functionality'

    def handle(self, *args, **options):
        # Get mentors and mentees
        mentors = CustomUser.objects.filter(user_type='mentor')
        mentees = CustomUser.objects.filter(user_type='mentee')
        
        if not mentors.exists():
            self.stdout.write(
                self.style.WARNING('No mentors found. Please create some mentor users first.')
            )
            return
            
        if not mentees.exists():
            self.stdout.write(
                self.style.WARNING('No mentees found. Please create some mentee users first.')
            )
            return
        
        # Create sample sessions
        sample_sessions = [
            {
                'title': 'Career Guidance Session',
                'description': 'One-on-one career guidance and planning session',
                'session_type': 'one_on_one',
                'status': 'completed',
                'duration_minutes': 60,
                'days_from_now': -7
            },
            {
                'title': 'Technical Skills Workshop',
                'description': 'Workshop on advanced programming concepts',
                'session_type': 'workshop',
                'status': 'completed',
                'duration_minutes': 120,
                'days_from_now': -5
            },
            {
                'title': 'Leadership Development',
                'description': 'Group session on leadership skills',
                'session_type': 'group',
                'status': 'scheduled',
                'duration_minutes': 90,
                'days_from_now': 3
            },
            {
                'title': 'Project Management Consultation',
                'description': 'Consultation on project management best practices',
                'session_type': 'consultation',
                'status': 'scheduled',
                'duration_minutes': 45,
                'days_from_now': 7
            },
            {
                'title': 'Resume Review Session',
                'description': 'One-on-one resume review and improvement',
                'session_type': 'one_on_one',
                'status': 'in_progress',
                'duration_minutes': 30,
                'days_from_now': 0
            }
        ]
        
        sessions_created = 0
        
        for i, session_data in enumerate(sample_sessions):
            # Cycle through mentors and mentees
            mentor = mentors[i % mentors.count()]
            mentee = mentees[i % mentees.count()]
            
            scheduled_date = timezone.now() + timedelta(days=session_data['days_from_now'])
            
            session, created = Session.objects.get_or_create(
                mentor=mentor,
                mentee=mentee,
                title=session_data['title'],
                defaults={
                    'description': session_data['description'],
                    'session_type': session_data['session_type'],
                    'status': session_data['status'],
                    'scheduled_date': scheduled_date,
                    'duration_minutes': session_data['duration_minutes']
                }
            )
            
            if created:
                sessions_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created session: {session.title}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {sessions_created} sample sessions!')
        )


