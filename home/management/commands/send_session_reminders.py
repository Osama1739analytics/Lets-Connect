from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from home.models import Session, Notification
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Sends reminders to mentor and mentee 15 minutes before the session starts'

    def handle(self, *args, **options):
        now = timezone.now()
        # We look for sessions starting in the next 15-20 minutes
        # to ensure we catch them within a 5-minute cron window.
        remind_window_start = now + timedelta(minutes=10)
        remind_window_end = now + timedelta(minutes=20)

        # Filter sessions that are booked, not yet reminded, and starting soon
        sessions = Session.objects.filter(
            status='booked',
            reminder_sent=False,
            scheduled_at__gte=remind_window_start,
            scheduled_at__lte=remind_window_end
        )

        for session in sessions:
            # The initiator could be mentor OR mentee
            # The participant is the one who booked it
            mentor = session.initiator if session.session_type == 'post' else session.participant
            mentee = session.participant if session.session_type == 'post' else session.initiator

            if not mentor or not mentee:
                continue

            msg = f"Reminder: Your session '{session.subject_detail}' starts in 15 minutes!"
            link = session.meeting_link or ""

            # Create In-app Notifications
            # We add the link so the "Join Meeting" button appears in the UI
            Notification.objects.create(
                recipient=mentor,
                verb=msg,
                link=link,
                target_session=session
            )
            Notification.objects.create(
                recipient=mentee,
                verb=msg,
                link=link,
                target_session=session
            )

            # Send Emails
            recipients = [mentor.email, mentee.email]
            subject = f"Upcoming Session Reminder: {session.subject_detail}"
            email_body = f"Hi,\n\nThis is a reminder that your session '{session.subject_detail}' starts in 15 minutes.\n\n"
            if link:
                email_body += f"Meeting Link: {link}\n\n"
            else:
                email_body += "Meeting Link: No link provided yet. Please check the portal.\n\n"
            
            email_body += f"Scheduled Start: {session.scheduled_at}\n\nGood luck!"

            try:
                send_mail(
                    subject,
                    email_body,
                    settings.DEFAULT_FROM_EMAIL,
                    recipients,
                    fail_silently=False,
                )
                self.stdout.write(self.style.SUCCESS(f"Sent reminder for session: {session.id}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error sending email for session {session.id}: {e}"))

            # Mark reminder as sent
            session.reminder_sent = True
            session.save()
