import logging
import uuid
from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class MeetingLinkError(Exception):
    """Raised when no meeting link could be generated."""

    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details


def _get_session_mentor(session):
    if session.session_type == 'post':
        return session.initiator
    if session.participant and session.participant.user_type == 'mentor':
        return session.participant
    return session.initiator


def _get_google_access_token(user):
    try:
        from social_django.models import UserSocialAuth
        from social_django.utils import load_strategy

        social = UserSocialAuth.objects.filter(user=user, provider='google-oauth2').first()
        if not social:
            return None
        strategy = load_strategy()
        return social.get_access_token(strategy)
    except Exception as exc:
        logger.warning("Could not get Google access token for %s: %s", user.username, exc)
        return None


def _session_time_bounds(session):
    """Return start/end datetimes, ensuring end is in the future for API providers."""
    now = timezone.now()
    duration = session.duration_minutes or 15
    start_time = session.scheduled_at or now
    end_time = start_time + timedelta(minutes=duration)

    if end_time <= now:
        start_time = now
        end_time = now + timedelta(minutes=duration)

    return start_time, end_time


def generate_google_meet_link(session, mentor):
    """Create a Google Calendar event with an attached Google Meet link."""
    if not mentor or not mentor.is_calendar_connected:
        return None

    access_token = _get_google_access_token(mentor)
    if not access_token:
        return None

    start_time, end_time = _session_time_bounds(session)
    event = {
        'summary': f"P2P Session: {session.subject_detail}",
        'description': (
            f"Mentoring session via Peer2Professional Guidance App (Session #{session.id})"
        ),
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': settings.TIME_ZONE,
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': settings.TIME_ZONE,
        },
        'conferenceData': {
            'createRequest': {
                'requestId': f'p2p-{session.id}-{uuid.uuid4().hex[:12]}',
                'conferenceSolutionKey': {'type': 'hangoutsMeet'},
            }
        },
    }

    try:
        response = requests.post(
            'https://www.googleapis.com/calendar/v3/calendars/primary/events',
            params={'conferenceDataVersion': 1},
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            },
            json=event,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        meet_link = data.get('hangoutLink')
        if not meet_link:
            for entry_point in data.get('conferenceData', {}).get('entryPoints', []):
                if entry_point.get('entryPointType') == 'video':
                    meet_link = entry_point.get('uri')
                    break

        if meet_link:
            logger.info("Generated Google Meet link for session %s", session.id)
        return meet_link
    except requests.HTTPError as exc:
        body = exc.response.text[:500] if exc.response is not None else str(exc)
        logger.error("Google Calendar Meet creation failed for session %s: %s", session.id, body)
        return None
    except Exception as exc:
        logger.error("Google Meet link generation failed for session %s: %s", session.id, exc)
        return None


def generate_daily_room_link(session):
    """Create a Daily.co room for the session."""
    api_key = getattr(settings, 'DAILY_API_KEY', None) or __import__('os').environ.get('DAILY_API_KEY')
    if not api_key:
        raise MeetingLinkError(
            "Daily.co API key is missing. Set DAILY_API_KEY in settings or use a manual meeting link.",
        )

    _, end_time = _session_time_bounds(session)
    min_exp_time = timezone.now() + timedelta(hours=2)
    if end_time < min_exp_time:
        end_time = min_exp_time

    exp_timestamp = int(end_time.timestamp())
    room_name = f"p2p-session-{session.id}-{uuid.uuid4().hex[:6]}"
    payload = {
        'name': room_name,
        'privacy': 'public',
        'properties': {
            'exp': exp_timestamp,
            'enable_chat': True,
            'enable_screenshare': True,
            'enable_knocking': False,
            'start_video_off': False,
            'start_audio_off': False,
        },
    }

    try:
        response = requests.post(
            'https://api.daily.co/v1/rooms',
            json=payload,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            timeout=10,
        )
        response.raise_for_status()
        room_url = response.json().get('url')
        if not room_url:
            raise MeetingLinkError('Daily.co did not return a room URL.')
        logger.info("Generated Daily.co room for session %s: %s", session.id, room_url)
        return room_url
    except requests.HTTPError as exc:
        details = exc.response.text[:500] if exc.response is not None else str(exc)
        logger.error("Daily.co room creation failed for session %s: %s", session.id, details)
        raise MeetingLinkError(
            'Daily.co could not create a meeting room.',
            details=details,
        ) from exc
    except MeetingLinkError:
        raise
    except Exception as exc:
        logger.error("Daily.co room creation failed for session %s: %s", session.id, exc)
        raise MeetingLinkError('Daily.co could not create a meeting room.', details=str(exc)) from exc


def generate_meeting_link(session):
    """
    Resolve the best available meeting link for a session.
    Priority: mentor personal link -> Google Meet -> Daily.co room.
    """
    mentor = _get_session_mentor(session)

    if mentor and mentor.personal_meeting_link:
        logger.info("Using mentor personal meeting link for session %s", session.id)
        return mentor.personal_meeting_link, 'personal'

    meet_link = generate_google_meet_link(session, mentor)
    if meet_link:
        return meet_link, 'google_meet'

    daily_link = generate_daily_room_link(session)
    return daily_link, 'daily'
