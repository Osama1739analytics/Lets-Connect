from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone  # Import timezone for local conversion
from .models import Session, Notification

@receiver(post_save, sender=Session)
def session_status_notification(sender, instance, created, **kwargs):
    if created:
        pass
    else:
        # Check for status changes
        if instance.status == 'booked' and instance.participant:
            # Convert scheduled_at to local time (Pakistani Time per settings)
            if instance.scheduled_at:
                local_dt = timezone.localtime(instance.scheduled_at)
                formatted_time = local_dt.strftime('%d-%m-%Y %I:%M %p')
            else:
                formatted_time = "TBD"

            # 1. Notify Initiator
            verb_initiator = f"booked your session: {instance.subject_detail}"
            Notification.objects.create(
                recipient=instance.initiator,
                sender=instance.participant,
                verb=verb_initiator,
                target_session=instance,
                link=instance.meeting_link
            )
            
            # Email Initiator
            subject_init = f"Session Booked: {instance.subject_detail}"
            msg_init = f"Hi {instance.initiator.full_name or instance.initiator.username},\n\n" \
                       f"{instance.participant.full_name or instance.participant.username} has booked your session '{instance.subject_detail}'.\n" \
                       f"Scheduled at: {formatted_time}\n"
            
            if instance.meeting_link:
                msg_init += f"Meeting Link: {instance.meeting_link}\n"
            
            msg_init += f"\nCheck it on the portal: http://127.0.0.1:8000/"

            try:
                if instance.initiator.email:
                    send_mail(subject_init, msg_init, settings.DEFAULT_FROM_EMAIL, [instance.initiator.email])
            except Exception as e:
                print(f"Error sending email to initiator: {e}")

            # 2. Notify Participant
            verb_participant = f"You booked a session: {instance.subject_detail}"
            Notification.objects.create(
                recipient=instance.participant,
                sender=instance.initiator, # or None/System
                verb=verb_participant,
                target_session=instance,
                link=instance.meeting_link
            )

            # Email Participant
            subject_part = f"Booking Confirmed: {instance.subject_detail}"
            msg_part = f"Hi {instance.participant.full_name or instance.participant.username},\n\n" \
                       f"You have successfully booked the session '{instance.subject_detail}' with {instance.initiator.full_name or instance.initiator.username}.\n" \
                       f"Scheduled at: {formatted_time}\n"

            if instance.meeting_link:
                msg_part += f"Meeting Link: {instance.meeting_link}\n"
            
            msg_part += f"\nCheck it on the portal: http://127.0.0.1:8000/"

            try:
                if instance.participant.email:
                    send_mail(subject_part, msg_part, settings.DEFAULT_FROM_EMAIL, [instance.participant.email])
            except Exception as e:
                print(f"Error sending email to participant: {e}")

@receiver(post_save, sender=Notification)
def notification_broadcast(sender, instance, created, **kwargs):
    if created:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notify_{instance.recipient.id}',
            {
                'type': 'send_notification',
                'verb': instance.verb,
                'sender': instance.sender.username if instance.sender else 'System',
                'sender_id': instance.sender.id if instance.sender else None,
                'link': instance.link or '#'
            }
        )
