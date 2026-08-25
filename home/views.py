from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db import models
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.urls import reverse
from django.core.mail import send_mail
import random
from datetime import timedelta

from .forms import (
    EmailSignupStartForm,
    EmailVerificationForm,
    LoginForm,
    GoogleProfileConfirmForm,
    SessionForm,
    ProfileEditForm,
)
from .models import EmailOTP, PendingSignup, Session, Notification, ConnectionRequest, DirectMessage

User = get_user_model()

@login_required
def profile_view(request):
    """Simple profile view to render the profile template."""
    return render(request, 'profile.html', {'user': request.user})


# Utility functions

def _get_connection_user_ids(user):
    from django.db.models import Q

    connected_user_ids = set()
    pending_user_ids = set()
    for conn in ConnectionRequest.objects.filter(Q(sender=user) | Q(receiver=user)):
        other_id = conn.receiver_id if conn.sender_id == user.id else conn.sender_id
        if conn.status == 'accepted':
            connected_user_ids.add(other_id)
        elif conn.status == 'pending':
            pending_user_ids.add(other_id)
    return connected_user_ids, pending_user_ids


def _get_platform_users(user, name_query='', user_type_filter=''):
    from django.db.models import Q

    queryset = User.objects.filter(is_active=True).exclude(id=user.id).exclude(
        Q(is_superuser=True) | Q(is_staff=True)
    )
    if user_type_filter in ('mentor', 'mentee'):
        queryset = queryset.filter(user_type=user_type_filter)
    if name_query:
        queryset = queryset.filter(
            Q(full_name__icontains=name_query)
            | Q(username__icontains=name_query)
            | Q(first_name__icontains=name_query)
            | Q(last_name__icontains=name_query)
        )
    return queryset.order_by('full_name', 'username')


def _filter_sessions(queryset, session_q='', session_type=''):
    from django.db.models import Q

    if session_type == 'post':
        queryset = queryset.filter(session_type='post')
    elif session_type == 'request':
        queryset = queryset.filter(session_type='request')
    if session_q:
        queryset = queryset.filter(
            Q(subject_detail__icontains=session_q)
            | Q(initiator__full_name__icontains=session_q)
            | Q(initiator__username__icontains=session_q)
            | Q(tags__name__icontains=session_q)
        ).distinct()
    return queryset


def _generate_otp(length: int = None) -> str:
    length = length or getattr(settings, 'OTP_CODE_LENGTH', 6)
    return f"{random.randint(0, 10**length - 1):0{length}d}"


def _send_otp_email(email: str, code: str):
    subject = "Your Let's Connect verification code"
    message = f"Your verification code is: {code}\nThis code expires in 5 minutes."
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
    except Exception as e:
        print(f"Error sending email: {e}")
        raise e


def _otp_expiry_dt():
    seconds = getattr(settings, 'OTP_EXPIRY_SECONDS', 300)
    return timezone.now() + timedelta(seconds=seconds)


# Email/password signup with OTP verification

def signup_start(request):
    if request.method == 'POST':
        form = EmailSignupStartForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower().strip()
            password = form.cleaned_data['password']
            username = form.cleaned_data['username'].strip()
            full_name = form.cleaned_data['full_name'].strip()
            gender = form.cleaned_data['gender']
            contact_number = form.cleaned_data.get('contact_number', '').strip()
            user_type = form.cleaned_data['user_type']
            age = form.cleaned_data.get('age')

            if User.objects.filter(email__iexact=email).exists():
                messages.error(request, 'An account with this email already exists. Please log in instead.')
                return redirect('home:login')
            if User.objects.filter(username__iexact=username).exists():
                messages.error(request, 'This username is already taken. Please choose another.')
                return render(request, 'signup.html', {'form': form, 'google_begin_url': reverse('social:begin', args=['google-oauth2'])})

            with transaction.atomic():
                PendingSignup.create_or_update(
                    email=email,
                    username=username,
                    raw_password=password,
                    full_name=full_name,
                    gender=gender,
                    contact_number=contact_number,
                    user_type=user_type,
                    age=age,
                )
                code = _generate_otp()
                EmailOTP.objects.create(email=email, code=code, purpose='signup', expires_at=_otp_expiry_dt())
                _send_otp_email(email, code)

            request.session['pending_email'] = email
            messages.info(request, 'We sent a 6-digit code to your email. Enter it below to verify.')
            return redirect('home:verify_email')
    else:
        form = EmailSignupStartForm()

    return render(request, 'signup.html', {
        'form': form,
        'google_begin_url': reverse('social:begin', args=['google-oauth2']) + '?prompt=consent&access_type=offline'
    })


def verify_email(request):
    # Default email prefilled from session
    initial_email = request.session.get('pending_email', '')
    if request.method == 'POST':
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower().strip()
            otp = form.cleaned_data['otp'].strip()

            try:
                otp_obj = EmailOTP.objects.filter(email__iexact=email, purpose='signup', is_used=False).latest('created_at')
            except EmailOTP.DoesNotExist:
                messages.error(request, 'Please request a new code.')
                return redirect('home:resend_otp')

            if otp_obj.is_expired():
                messages.error(request, 'Code expired. We can resend a new one.')
                return redirect('home:resend_otp')

            otp_obj.attempts += 1
            if otp_obj.code != otp:
                otp_obj.save(update_fields=['attempts'])
                messages.error(request, 'Invalid code. Please try again.')
                return render(request, 'verify_email.html', {'form': form})

            # Correct OTP
            otp_obj.is_used = True
            otp_obj.save(update_fields=['is_used'])

            try:
                pending = PendingSignup.objects.get(email__iexact=email)
            except PendingSignup.DoesNotExist:
                messages.error(request, 'No pending signup found. Please start again.')
                return redirect('home:signup')

            # Create user now using the stored pending data
            # Ensure username uniqueness just in case
            desired_username = pending.username
            username = desired_username
            i = 1
            while User.objects.filter(username=username).exists():
                username = f"{desired_username}{i}"
                i += 1

            user = User.objects.create(
                username=username,
                email=email,
                password=pending.password_hash,
                full_name=pending.full_name,
                gender=pending.gender,
                contact_number=pending.contact_number,
                user_type=pending.user_type,
                age=pending.age,
            )

            pending.delete()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            messages.success(request, 'Email verified! Your account has been created.')
            return redirect('home:onboarding_setup')
    else:
        form = EmailVerificationForm(initial={'email': initial_email})

    return render(request, 'verify_email.html', {'form': form})


def resend_otp(request):
    email = request.session.get('pending_email') or request.GET.get('email', '')
    if not email:
        messages.error(request, 'Enter your email to receive a code.')
        return redirect('home:verify_email')

    # Create and send new OTP
    code = _generate_otp()
    EmailOTP.objects.create(email=email, code=code, purpose='signup', expires_at=_otp_expiry_dt())
    _send_otp_email(email, code)
    messages.info(request, 'We sent you a new code.')
    return redirect('home:verify_email')


# Login and logout

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_username()}!')
                return redirect('home:index')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {
        'form': form,
        'google_begin_url': reverse('social:begin', args=['google-oauth2']) + '?prompt=consent&access_type=offline'
    })


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('home:login')


# Google OAuth profile confirmation (pipeline)
from social_core.pipeline.partial import partial

# Pipeline step is implemented in home/social_pipeline.py


def google_profile_confirm(request):
    # Prefill from session-stored partial details
    partial_data = request.session.get('saved_profile', {})
    # Email comes from Google and should be read-only
    email = partial_data.get('email', '')
    initial = {
        'full_name': partial_data.get('full_name', ''),
        'email': email,
        'username': (email.split('@')[0][:20] if email else ''),
        'contact_number': partial_data.get('contact_number', ''),
        'gender': 'male',
        'user_type': 'mentee',
    }

    if request.method == 'POST':
        form = GoogleProfileConfirmForm(request.POST, initial=initial)
        if form.is_valid():
            profile = {
                'full_name': form.cleaned_data.get('full_name', ''),
                'email': email,
                'username': form.cleaned_data['username'],
                'contact_number': form.cleaned_data.get('contact_number', ''),
                'gender': form.cleaned_data.get('gender'),
                'user_type': form.cleaned_data['user_type'],
                'age': form.cleaned_data.get('age'),
                'password': form.cleaned_data['password'],
            }
            request.session['saved_profile'] = profile
            # Resume pipeline
            return redirect(reverse('social:complete', args=['google-oauth2']))
    else:
        form = GoogleProfileConfirmForm(initial=initial)
    return render(request, 'google_profile_confirm.html', {'form': form, 'email': email})

@login_required
def onboarding_setup(request):
    """View to collect additional profile info and connect calendar after signup."""
    user = request.user
    if request.method == 'POST':
        user.age = request.POST.get('age')
        user.contact_number = request.POST.get('contact_number')
        user.mentor_bio = request.POST.get('mentor_bio')
        user.mentor_expertise = request.POST.get('mentor_expertise')
        user.learning_goals = request.POST.get('learning_goals')
        user.save()
        messages.success(request, "Welcome! Your profile is now set up.")
        return redirect('home:index')
    
    return render(request, 'onboarding_setup.html')


@login_required
def create_session(request):
    """View for both Mentees to request and Mentors to post sessions."""
    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.initiator = request.user
            # Symmetrical logic: Mentee -> Request, Mentor -> Post
            if request.user.user_type == 'mentee':
                session.session_type = 'request'
            else:
                session.session_type = 'post'
            
            # Pricing logic: Rs. 500 per 15 minutes
            duration = form.cleaned_data.get('duration_minutes', 15)
            session.total_price = (duration / 15) * 500
            session.status = 'open'
            session.save()
            form.save_m2m()  # Required for Taggit
            messages.success(request, f'Session {session.session_type} created successfully! Total Price: Rs. {session.total_price}')
            return redirect('home:browse_sessions')
    else:
        form = SessionForm()
    
    context = {
        'form': form,
        'title': 'Request a Session' if request.user.user_type == 'mentee' else 'Post a Session'
    }
    return render(request, 'session_form_v2.html', context)


@login_required
def browse_sessions(request):
    """View to see all active requests and posts with smart matching."""
    from django.db.models import Count, Q
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    user = request.user

    # Base query: Open sessions
    all_open_sessions = Session.objects.filter(status='open').select_related('initiator').order_by('scheduled_at')

    # 1. Your own sessions (active)
    your_sessions = all_open_sessions.filter(initiator=user)

    # 2. Others' sessions (base for recommendations)
    others_sessions = all_open_sessions.exclude(initiator=user)

    # 3. Matching Logic (Recommended among others' sessions)
    recommended_sessions = Session.objects.none()
    
    # Extract user skills
    user_skill_names = list(user.skills.names())
    
    if user_skill_names:
        # Build filter condition
        # Exact tag overlap
        match_filters = Q(tags__name__in=user_skill_names)
        
        # Weighted match for difficulty/skill_level if provided
        if user.current_skill_level:
            match_filters |= Q(tags__name__iexact=user.current_skill_level)
            
        recommended_sessions = others_sessions.annotate(
            match_count=Count('tags', filter=match_filters)
        ).filter(match_count__gt=0).order_by('-match_count', 'scheduled_at').distinct()

    # 4. Recommended Mentors (For Mentees)
    recommended_mentors = None
    if user.is_mentee() and user_skill_names:
        recommended_mentors = User.objects.filter(
            user_type='mentor',
            is_available_for_mentoring=True
        ).exclude(id=user.id).annotate(
            match_count=Count('skills', filter=Q(skills__name__in=user_skill_names))
        ).filter(match_count__gt=0).order_by('-match_count').distinct()[:3]

    connected_user_ids, pending_user_ids = _get_connection_user_ids(user)

    section = request.GET.get('section', 'sessions')
    if section not in ('sessions', 'people'):
        section = 'sessions'

    people_q = request.GET.get('people_q', '').strip()
    people_type = request.GET.get('people_type', '').strip()
    platform_users = _get_platform_users(user, people_q, people_type)

    session_q = request.GET.get('session_q', '').strip()
    session_type = request.GET.get('session_type', '').strip()

    your_sessions = _filter_sessions(your_sessions, session_q, session_type)
    recommended_sessions = _filter_sessions(recommended_sessions, session_q, session_type)
    mentor_posts = _filter_sessions(others_sessions.filter(session_type='post'), session_q, session_type)
    mentee_requests = _filter_sessions(others_sessions.filter(session_type='request'), session_q, session_type)

    has_session_results = (
        your_sessions.exists()
        or (recommended_sessions.exists() if recommended_sessions else False)
        or mentor_posts.exists()
        or mentee_requests.exists()
    )

    return render(request, 'browse_sessions_v2.html', {
        'mentor_posts': mentor_posts,
        'mentee_requests': mentee_requests,
        'your_sessions': your_sessions,
        'recommended_sessions': recommended_sessions,
        'has_recommendations': recommended_sessions.exists() if recommended_sessions else False,
        'has_your_sessions': your_sessions.exists(),
        'has_session_results': has_session_results,
        'recommended_mentors': recommended_mentors,
        'connected_user_ids': connected_user_ids,
        'pending_user_ids': pending_user_ids,
        'platform_users': platform_users,
        'people_q': people_q,
        'people_type': people_type,
        'session_q': session_q,
        'session_type': session_type,
        'section': section,
    })


@login_required
def book_session(request, session_id):
    """Logic to accept/book an open session."""
    session = get_object_or_404(Session, id=session_id, status='open')
    
    # Prevent booking own session
    if session.initiator == request.user:
        messages.error(request, "You cannot book your own session.")
        return redirect('home:browse_sessions')
        
    # Symmetrical logic: Mentee books Mentor Post, Mentor books Mentee Request
    if session.session_type == 'request' and request.user.user_type != 'mentor':
        messages.error(request, "Only mentors can accept session requests.")
        return redirect('home:browse_sessions')
        
    if session.session_type == 'post' and request.user.user_type != 'mentee':
        messages.error(request, "Only mentees can book available session posts.")
        return redirect('home:browse_sessions')

    # Assign participant and change status
    session.participant = request.user
    session.status = 'booked'
    
    # Remove immediate Meet link generation upon booking. 
    # Link generation is now handled in verify_payment view only after payment confirmation.
    session.save()
    
    # Redirection logic:
    # If a Mentee books a Mentor Post (session_type='post'), they should go to payment.
    # If a Mentor accepts a Mentee Request (session_type='request'), the Mentee should be notified to pay, 
    # but the Mentor shouldn't be sent to the payment page.
    
    if session.session_type == 'post':
        # Notify the mentee
        Notification.objects.create(
            recipient=request.user,
            sender=session.initiator,
            verb="Your session booking is pending please make the payment to confirm the booking and get link.",
            target_session=session,
            link=reverse('home:submit_payment', args=[session.id])
        )
        # Notify the mentor
        Notification.objects.create(
            recipient=session.initiator,
            sender=request.user,
            verb=f"booked your session: {session.subject_detail}. Waiting for payment.",
            target_session=session,
            link=reverse('home:index')
        )
        messages.success(request, f'Successfully booked the session: {session.subject_detail}. Please complete the payment to receive the meeting link.')
        return redirect('home:submit_payment', session_id=session.id)
    else:
        # It's a request accepted by a mentor
        # Notify the mentee
        Notification.objects.create(
            recipient=session.initiator,
            sender=request.user,
            verb="Your session booking is pending please make the payment to confirm the booking and get link.",
            target_session=session,
            link=reverse('home:submit_payment', args=[session.id])
        )
        messages.success(request, f'You have accepted the session request: {session.subject_detail}. The student has been notified to proceed with payment.')
        return redirect('home:index')


@login_required
def submit_payment(request, session_id):
    """View for Mentee to see Mentor's bank info and upload screenshot."""
    session = get_object_or_404(Session, id=session_id)
    
    # Identify Payer (Mentee) and Payee (Mentor)
    if session.session_type == 'post':
        mentor = session.initiator
        mentee = session.participant
    else:
        # Request
        mentee = session.initiator
        mentor = session.participant
        
    # Security: Only the Mentee (payer) should see this
    if request.user != mentee:
        messages.error(request, "Access denied. Only the student can submit payment.")
        return redirect('home:index')

    if request.method == 'POST':
        screenshot = request.FILES.get('payment_screenshot')
        if screenshot:
            session.payment_screenshot = screenshot
            session.payment_status = 'submitted'
            session.save()
            
            # Notify the Mentor
            Notification.objects.create(
                recipient=mentor,
                sender=request.user,
                verb="View Payment Screenshot",
                target_session=session,
                link=reverse('home:verify_payment', args=[session.id])
            )
            
            messages.success(request, "Screenshot submitted successfully! The mentor will notify you once verified.")
            return redirect('home:index')
        else:
            messages.error(request, "Please upload a valid screenshot.")
            
    return render(request, 'submit_payment.html', {
        'session': session,
        'mentor': mentor,
    })


@login_required
def verify_payment(request, session_id):
    """View for Mentor to approve payment and trigger Meet link generation."""
    session = get_object_or_404(Session, id=session_id)
    
    # Identify the Mentor (the one receiving payment)
    if session.session_type == 'post':
        mentor = session.initiator
    else:
        mentor = session.participant if session.participant.user_type == 'mentor' else session.initiator
        
    if request.user != mentor:
        messages.error(request, "Only the mentor can verify payments.")
        return redirect('home:index')

    if request.method == 'POST':
        if 'approve' in request.POST:
            # Check for manual link first
            manual_link = request.POST.get('manual_link', '').strip()
            if manual_link:
                session.payment_status = 'verified'
                session.meeting_link = manual_link
                session.save()
                messages.success(request, "Payment verified and manual meeting link saved!")
            else:
                try:
                    from .services import generate_meeting_link, MeetingLinkError

                    meet_link, link_source = generate_meeting_link(session)
                    session.payment_status = 'verified'
                    session.meeting_link = meet_link
                    session.save()

                    source_labels = {
                        'personal': 'your saved personal meeting link',
                        'google_meet': 'Google Meet',
                        'daily': 'Daily.co',
                    }
                    messages.success(
                        request,
                        f"Payment verified. Meeting link created via {source_labels.get(link_source, 'automatic generation')}.",
                    )
                except MeetingLinkError as e:
                    detail = f" Details: {e.details}" if e.details else ''
                    messages.error(
                        request,
                        f"Failed to generate a meeting link automatically: {e}.{detail} "
                        "Please paste a Google Meet or Zoom link in the manual field and approve again.",
                    )
                    return redirect('home:verify_payment', session_id=session.id)
                except Exception as e:
                    messages.error(
                        request,
                        f"Failed to verify payment: {e}. Please paste a manual meeting link and approve again.",
                    )
                    return redirect('home:verify_payment', session_id=session.id)
            
            # Notify the Mentee (Join Session)
            mentee = session.participant if session.participant != mentor else session.initiator
            rate_url = reverse('home:leave_review', args=[session.id])
            join_tracking_url = reverse('home:join_session_meeting', args=[session.id])
            
            Notification.objects.create(
                recipient=mentee,
                sender=request.user,
                verb=f"Congratulations! Your payment for '{session.subject_detail}' is verified. You can now join the session.",
                target_session=session,
                link=join_tracking_url
            )

            # Also notify the Mentor (so they have the link too)
            Notification.objects.create(
                recipient=request.user,
                sender=mentee,
                verb=f"Payment for '{session.subject_detail}' is verified. Your meeting link is ready to join.",
                target_session=session,
                link=join_tracking_url
            )
            
            # Notify the Mentee (Rate Session)
            Notification.objects.create(
                recipient=mentee,
                sender=request.user,
                verb=f"Please provide feedback and rate your session: '{session.subject_detail}'.",
                target_session=session,
                link=rate_url
            )
            
            # Send Email via Gmail
            if mentee.email and session.meeting_link:
                try:
                    subject = f"Congratulations! Session Verified: {session.subject_detail}"
                    msg = f"Hi {mentee.username},\n\nYour payment for the session '{session.subject_detail}' has been verified.\n\nMeeting Link: {session.meeting_link}\n\nYou can also leave a review here: http://127.0.0.1:8000{rate_url}\n\nHappy learning!"
                    send_mail(subject, msg, settings.DEFAULT_FROM_EMAIL, [mentee.email])
                except Exception as e:
                    print(f"Email error: {e}")
                    pass

            return redirect('home:index')
            
        elif 'reject' in request.POST:
            reason = request.POST.get('rejection_reason', '').strip()
            session.payment_status = 'unpaid'
            session.payment_screenshot = None
            session.save()
            
            # Notify the Mentee
            mentee = session.participant if session.participant != mentor else session.initiator
            verb = f"Unfortunately, your payment for '{session.subject_detail}' was rejected and the booking is cancelled."
            if reason:
                verb += f" Reason: {reason}"
            else:
                verb += " Please check your payment details and try again."
                
            Notification.objects.create(
                recipient=mentee,
                sender=request.user,
                verb=verb,
                target_session=session,
                link=reverse('home:index')
            )
            
            messages.warning(request, "Payment rejected. The user has been notified.")
            return redirect('home:index')

    return render(request, 'verify_payment.html', {'session': session})


@login_required
def send_connect_request(request, user_id):
    """Create a connection request to another user."""
    receiver = get_object_or_404(User, id=user_id)
    if receiver == request.user:
        messages.error(request, "You cannot connect with yourself.")
        return redirect(request.META.get('HTTP_REFERER', 'home:index'))
        
    from django.db.models import Q
    existing = ConnectionRequest.objects.filter(
        (Q(sender=request.user, receiver=receiver) | Q(sender=receiver, receiver=request.user))
    ).first()
    
    if existing:
        if existing.status == 'accepted':
            messages.info(request, "You are already connected with this user.")
            return redirect(request.META.get('HTTP_REFERER', 'home:index'))
        elif existing.status == 'pending':
            messages.info(request, "Connection request is already pending.")
            return redirect(request.META.get('HTTP_REFERER', 'home:index'))
        else:
            # It was rejected, so we reset it to pending
            existing.sender = request.user
            existing.receiver = receiver
            existing.status = 'pending'
            existing.save()
            created = True # Treat as new for notification logic
    else:
        conn, created = ConnectionRequest.objects.get_or_create(sender=request.user, receiver=receiver)
    if created:
        Notification.objects.create(
            recipient=receiver,
            sender=request.user,
            verb="sent you a connection request",
            link=reverse('home:manage_connect_requests')
        )
        messages.success(request, f"Connection request sent to {receiver.username}!")
    else:
        messages.info(request, "You already have a pending or existing connection with this user.")
        
    referer = request.META.get('HTTP_REFERER', '')
    if 'requests' in referer or 'browse' in referer:
        return redirect(referer)
    if 'profile' in referer:
        return redirect('home:manage_connect_requests')
    return redirect(referer or 'home:index')


@login_required
def manage_connect_requests(request):
    """Requests Hub: View incoming requests with profile previews."""
    tab = request.GET.get('tab', 'pending')
    if tab == 'discover':
        return redirect(f"{reverse('home:browse_sessions')}?section=people")

    incoming = ConnectionRequest.objects.filter(receiver=request.user, status='pending').select_related('sender')
    
    from django.db.models import Q
    my_connections = ConnectionRequest.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user),
        status='accepted'
    ).select_related('sender', 'receiver')
    
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')
        conn = get_object_or_404(ConnectionRequest, id=request_id, receiver=request.user)
        
        if action == 'accept':
            conn.status = 'accepted'
            conn.save()
            Notification.objects.create(
                recipient=conn.sender,
                sender=request.user,
                verb="accepted your connection request",
                link=reverse('home:public_profile', args=[request.user.username]) # Corrected URL name
            )
            messages.success(request, f"You are now connected with {conn.sender.username}!")
        elif action == 'reject':
            conn.status = 'rejected'
            conn.save()
            messages.info(request, "Request declined.")
            
        return redirect('home:manage_connect_requests')

    return render(request, 'connect_requests_v2.html', {
        'incoming': incoming,
        'my_connections': my_connections,
        'tab': tab,
    })

def page_not_found(request, exception=None, unused_path=None):
    return render(request, '404.html', {'requested_path': request.path}, status=404)


def server_error(request):
    return render(request, '500.html', status=500)


def index(request):
    """Enhanced index view showing user stats or dashboard."""
    if not request.user.is_authenticated:
        return render(request, 'index.html', {'user_sessions': []})

    # Get user's sessions
    user_sessions = Session.objects.filter(
        (models.Q(initiator=request.user) | models.Q(participant=request.user))
    ).order_by('scheduled_at')

    return render(request, 'index.html', {
        'user_sessions': user_sessions
    })


@login_required
def update_session(request, session_id):
    """Allow initiator to update their session."""
    session = get_object_or_404(Session, id=session_id)
    
    # Ensure only the initiator can edit
    if session.initiator != request.user:
        messages.error(request, "You are not authorized to edit this session.")
        return redirect('home:index')
        
    if request.method == 'POST':
        form = SessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, 'Session updated successfully!')
            return redirect('home:browse_sessions')
    else:
        form = SessionForm(instance=session)
    
    return render(request, 'session_form_v2.html', {
        'form': form,
        'title': 'Edit Session'
    })


@login_required
def delete_session(request, session_id):
    """Allow initiator to delete their session."""
    session = get_object_or_404(Session, id=session_id)
    
    # Ensure only the initiator can delete
    if session.initiator != request.user:
        messages.error(request, "You are not authorized to delete this session.")
        return redirect('home:browse_sessions')
        
    if request.method == 'POST':
        session.delete()
        messages.success(request, 'Session deleted successfully.')
        return redirect('home:browse_sessions')
        
    return redirect('home:browse_sessions')

@login_required
def notifications_view(request):
    notifications = request.user.notifications.all()
    return render(request, 'notifications.html', {'notifications': notifications})

@login_required
def mark_notification_read(request, notification_id):
    from .models import Notification
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return redirect('home:notifications')

@login_required
def mark_all_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('home:notifications')

@login_required
def delete_all_notifications(request):
    """Delete all notifications for the current user."""
    if request.method == 'POST':
        request.user.notifications.all().delete()
        messages.success(request, "All notifications cleared.")
    return redirect('home:notifications')

@login_required
def update_presence(request):
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(User.PRESENCE_STATUS_CHOICES):
            request.user.presence_status = status
            request.user.save()
            messages.success(request, f"Status updated to {status.capitalize()}.")
    return redirect(request.META.get('HTTP_REFERER', 'home:index'))

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('/profile/')
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'edit_profile.html', {
        'form': form,
        'user': request.user
    })

@login_required
def edit_payment_details(request):
    """View to edit ONLY payment details for mentors."""
    from .forms import PaymentDetailsForm
    if request.user.user_type != 'mentor':
        messages.error(request, "Only mentors can set payment details.")
        return redirect('home:profile')
        
    if request.method == 'POST':
        form = PaymentDetailsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment details updated successfully!')
            return redirect('home:profile')
    else:
        form = PaymentDetailsForm(instance=request.user)
        
    return render(request, 'edit_payment_details.html', {
        'form': form,
        'title': 'Edit Payment Details'
    })

@login_required
def chat_inbox(request):
    """View to list all active conversations."""
    from django.db.models import Q, Max
    from .models import DirectMessage

    # Get distinct users the current user has chatted with
    user_id = request.user.id
    
    # We want the latest message for each conversation
    messages = DirectMessage.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).order_by('-timestamp')
    
    # Simple manual deduplication to find unique conversations
    threads = []
    seen_users = set()
    
    for msg in messages:
        other_user = msg.recipient if msg.sender == request.user else msg.sender
        if other_user.id not in seen_users:
            seen_users.add(other_user.id)
            unread_count = DirectMessage.objects.filter(sender=other_user, recipient=request.user, is_read=False).count()
            threads.append({
                'other_user': other_user,
                'last_message': msg,
                'unread_count': unread_count
            })
            
    return render(request, 'chat.html', {
        'threads': threads,
        'active_user': None
    })

@login_required
def chat_room(request, user_id):
    """View to render the specific chat between user and user_id."""
    from django.db.models import Q
    from .models import DirectMessage
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    other_user = get_object_or_404(User, id=user_id)
    
    # Fetch previous messages
    chat_messages = DirectMessage.objects.filter(
        Q(sender=request.user, recipient=other_user) | 
        Q(sender=other_user, recipient=request.user)
    ).order_by('timestamp')
    
    # Update is_read state for incoming messages
    DirectMessage.objects.filter(
        sender=other_user, recipient=request.user, is_read=False
    ).update(is_read=True)
    
    # Get inbox threads
    messages_all = DirectMessage.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).order_by('-timestamp')
    
    threads = []
    seen_users = set()
    
    for msg in messages_all:
        ou = msg.recipient if msg.sender == request.user else msg.sender
        if ou.id not in seen_users:
            seen_users.add(ou.id)
            unread_count = DirectMessage.objects.filter(sender=ou, recipient=request.user, is_read=False).count()
            threads.append({
                'other_user': ou,
                'last_message': msg,
                'unread_count': unread_count
            })
            
    # If the user_id isn't in threads (new chat), add them manually
    if other_user.id not in seen_users:
        threads.insert(0, {
            'other_user': other_user,
            'last_message': None,
            'unread_count': 0
        })

    return render(request, 'chat.html', {
        'threads': threads,
        'active_user': other_user,
        'chat_messages': chat_messages
    })

def public_profile(request, username):
    """View to show public profile and reviews for a user."""
    target_user = get_object_or_404(User, username=username)
    reviews = target_user.received_reviews.select_related('reviewer').all()
    
    connection = None
    if request.user.is_authenticated and request.user != target_user:
        from django.db.models import Q
        connection = ConnectionRequest.objects.filter(
            Q(sender=request.user, receiver=target_user) | 
            Q(sender=target_user, receiver=request.user)
        ).first()
    
    status = connection.status if connection else None
    
    return render(request, 'public_profile.html', {
        'target_user': target_user,
        'reviews': reviews,
        'connection_status': status,
        'connection_id': connection.id if connection else None,
        'is_receiver': (connection.receiver == request.user) if connection else False,
    })

@login_required
def leave_review(request, session_id):
    """View to leave a review for a mentor after a session."""
    session = get_object_or_404(Session, id=session_id)
    
    # Identify the Mentor (receiver) and Mentee (reviewer)
    if session.session_type == 'post':
        mentor = session.initiator
        mentee = session.participant
    else:
        # Request
        mentee = session.initiator
        mentor = session.participant
        
    if request.user != mentee:
        messages.error(request, "Only the mentee can leave a review.")
        return redirect('home:index')
        
    if session.status not in ['booked', 'completed']:
        messages.error(request, "You can only review sessions that are booked or completed.")
        return redirect('home:index')
        
    if hasattr(session, 'review'):
        messages.error(request, "You have already reviewed this session.")
        return redirect('home:public_profile', username=mentor.username)
        
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
                
            from .models import Review
            review = Review.objects.create(
                reviewer=request.user,
                receiver=mentor,
                session=session,
                rating=rating,
                comment=comment
            )
            
            # If 5 stars, notify mentor
            if rating == 5:
                Notification.objects.create(
                    recipient=mentor,
                    sender=request.user,
                    verb="left you a glowing 5-star review!",
                    link=reverse('home:public_profile', args=[mentor.username])
                )
                
            messages.success(request, f"Review submitted for {mentor.username}!")
            return redirect('home:public_profile', username=mentor.username)
        except (ValueError, TypeError):
            messages.error(request, "Invalid rating value.")
            
    return render(request, 'leave_review.html', {
        'session': session,
        'mentor': mentor,
    })

@login_required
def disconnect_user(request, user_id):
    """Remove connection with another user."""
    other_user = get_object_or_404(User, id=user_id)
    from django.db.models import Q
    # Delete any accepted connection in either direction
    ConnectionRequest.objects.filter(
        (Q(sender=request.user, receiver=other_user) | Q(sender=other_user, receiver=request.user)),
        status='accepted'
    ).delete()
    
    # Also delete pending requests to be thorough
    ConnectionRequest.objects.filter(
        (Q(sender=request.user, receiver=other_user) | Q(sender=other_user, receiver=request.user)),
        status='pending'
    ).delete()
    
    messages.success(request, f"You have disconnected from {other_user.username}.")
    # Redirect specifically to the connections tab
    return redirect(reverse('home:manage_connect_requests') + '?tab=connections')

@login_required
def delete_chat_thread(request, user_id):
    """Delete all messages in a conversation."""
    other_user = get_object_or_404(User, id=user_id)
    from django.db.models import Q
    DirectMessage.objects.filter(
        (Q(sender=request.user, recipient=other_user) | Q(sender=other_user, recipient=request.user))
    ).delete()
    messages.success(request, "Conversation deleted successfully.")
    return redirect('home:chat_inbox')

@login_required
def delete_message(request, message_id):
    """Delete a single message sent by the user."""
    message = get_object_or_404(DirectMessage, id=message_id, sender=request.user)
    message.delete()
    return redirect(request.META.get('HTTP_REFERER', 'home:chat_inbox'))

@login_required
def edit_message(request, message_id):
    """Edit a single message sent by the user."""
    message = get_object_or_404(DirectMessage, id=message_id, sender=request.user)
    if request.method == 'POST':
        new_content = request.POST.get('content')
        if new_content:
            message.content = new_content
            message.save()
            messages.success(request, "Message updated.")
    return redirect(request.META.get('HTTP_REFERER', 'home:chat_inbox'))

@login_required
def send_message_ajax(request):
    """Handle message sending via AJAX."""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        recipient_id = data.get('recipient_id')
        content = data.get('content')
        if recipient_id and content:
            recipient = get_object_or_404(User, id=recipient_id)
            msg = DirectMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content
            )
            return JsonResponse({
                'status': 'success',
                'message': msg.content,
                'sender_id': msg.sender.id,
                'timestamp': msg.timestamp.strftime('%I:%M %p')
            })
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def fetch_messages_ajax(request, user_id):
    """Fetch new messages since a certain timestamp for AJAX polling."""
    other_user = get_object_or_404(User, id=user_id)
    last_id = request.GET.get('last_id', 0)
    
    from django.db.models import Q
    messages = DirectMessage.objects.filter(
        Q(sender=request.user, recipient=other_user) | Q(sender=other_user, recipient=request.user),
        id__gt=last_id
    ).order_by('timestamp')
    
    msg_list = []
    for m in messages:
        msg_list.append({
            'id': m.id,
            'content': m.content,
            'sender_id': m.sender.id,
            'timestamp': m.timestamp.strftime('%I:%M %p'),
            'is_sent': m.sender == request.user
        })
    
    return JsonResponse({'messages': msg_list})


@login_required
def join_session_meeting(request, session_id):
    """Logs session join times and early starts before redirecting to the video call."""
    session = get_object_or_404(Session, id=session_id)
    
    # Check permissions (only initiator or participant can join)
    if request.user != session.initiator and request.user != session.participant:
        messages.error(request, "You are not authorized to join this session.")
        return redirect('home:index')
        
    if not session.meeting_link:
        messages.error(request, "No meeting link has been generated for this session yet.")
        return redirect('home:index')
        
    # Log early start tracking
    now = timezone.now()
    if not session.actual_started_at:
        session.actual_started_at = now
        # If joining more than 5 minutes before scheduled start time
        if session.scheduled_at and now < (session.scheduled_at - timedelta(minutes=5)):
            session.is_started_early = True
            messages.info(request, "Starting early! This session has been flagged as taken earlier than scheduled.")
        session.save()
        
    return redirect(session.meeting_link)


@login_required
def complete_session(request, session_id):
    """Marks a session as officially completed and logs end time."""
    session = get_object_or_404(Session, id=session_id)
    
    # Check permissions (only mentor or participant can complete)
    mentor = session.initiator if session.session_type == 'post' else session.participant
    if request.user != mentor:
        messages.error(request, "Only the mentor can mark a session as completed.")
        return redirect('home:index')
        
    session.status = 'completed'
    session.actual_ended_at = timezone.now()
    session.save()
    
    messages.success(request, "Session marked as completed successfully!")
    return redirect('home:profile')


@login_required
def reschedule_session(request, session_id):
    """Allows shifting a session to a different date and time, automatically regenerating the Daily.co link."""
    session = get_object_or_404(Session, id=session_id)
    
    # Check permissions (mentor or mentee of the booked session)
    if request.user != session.initiator and request.user != session.participant:
        messages.error(request, "You are not authorized to reschedule this session.")
        return redirect('home:index')
        
    if request.method == 'POST':
        new_time_str = request.POST.get('new_time')
        if new_time_str:
            try:
                from django.utils.dateparse import parse_datetime
                # parse datetime from the html input (e.g. 2026-05-18T14:30)
                new_time = parse_datetime(new_time_str)
                if new_time:
                    # Make aware if naive
                    if timezone.is_naive(new_time):
                        new_time = timezone.make_aware(new_time, timezone.get_current_timezone())
                        
                    if new_time < timezone.now():
                        messages.error(request, "Cannot reschedule to a past date/time.")
                        return redirect(request.META.get('HTTP_REFERER', 'home:profile'))
                        
                    session.scheduled_at = new_time
                    
                    from .services import generate_meeting_link, MeetingLinkError

                    try:
                        new_meet_link, _ = generate_meeting_link(session)
                        session.meeting_link = new_meet_link
                    except MeetingLinkError as exc:
                        print(f"Error regenerating meeting link: {exc}")
                        
                    session.save()
                    
                    # Notify the other party
                    other_party = session.participant if request.user == session.initiator else session.initiator
                    if other_party:
                        Notification.objects.create(
                            recipient=other_party,
                            sender=request.user,
                            verb=f"rescheduled your session '{session.subject_detail}' to {new_time.strftime('%d %b %Y at %I:%M %p')}.",
                            target_session=session,
                            link=reverse('home:profile')
                        )
                        
                    messages.success(request, f"Session successfully rescheduled to {new_time.strftime('%d %b %Y, %I:%M %p')}!")
                else:
                    messages.error(request, "Invalid date/time format.")
            except Exception as e:
                messages.error(request, f"Error rescheduling: {str(e)}")
                
    return redirect('home:profile')

# Knowledge Hub Views

@login_required
def knowledge_hub_dashboard(request):
    from .models import BlogPost, Resource, ForumThread, HubCategory
    categories = HubCategory.objects.all()
    latest_blogs = BlogPost.objects.filter(is_published=True).order_by('-created_at')[:3]
    latest_resources = Resource.objects.order_by('-created_at')[:4]
    active_threads = ForumThread.objects.order_by('-created_at')[:4]
    
    return render(request, 'knowledge_hub/dashboard.html', {
        'categories': categories,
        'latest_blogs': latest_blogs,
        'latest_resources': latest_resources,
        'active_threads': active_threads,
    })

@login_required
def resource_list(request):
    from .models import Resource, HubCategory
    from .forms import ResourceForm
    from django.db.models import Q
    
    query = request.GET.get('q', '')
    cat_slug = request.GET.get('category', '')
    
    resources = Resource.objects.all()
    if query:
        resources = resources.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if cat_slug:
        resources = resources.filter(category__slug=cat_slug)
        
    categories = HubCategory.objects.all()
    
    return render(request, 'knowledge_hub/resource_list.html', {
        'resources': resources,
        'categories': categories,
        'query': query,
        'selected_category': cat_slug,
    })

@login_required
def upload_resource(request):
    from .forms import ResourceForm
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.uploaded_by = request.user
            resource.save()
            messages.success(request, "Resource uploaded successfully!")
            return redirect('home:resource_list')
    else:
        form = ResourceForm()
    return render(request, 'knowledge_hub/resource_form.html', {'form': form})

@login_required
def blog_list(request):
    from .models import BlogPost, HubCategory
    from django.db.models import Q
    
    query = request.GET.get('q', '')
    cat_slug = request.GET.get('category', '')
    
    blogs = BlogPost.objects.filter(is_published=True)
    if query:
        blogs = blogs.filter(Q(title__icontains=query) | Q(content__icontains=query))
    if cat_slug:
        blogs = blogs.filter(category__slug=cat_slug)
        
    categories = HubCategory.objects.all()
    
    return render(request, 'knowledge_hub/blog_list.html', {
        'blogs': blogs,
        'categories': categories,
        'query': query,
        'selected_category': cat_slug,
    })

@login_required
def blog_detail(request, slug):
    from .models import BlogPost
    blog = get_object_or_404(BlogPost, slug=slug, is_published=True)
    return render(request, 'knowledge_hub/blog_detail.html', {'blog': blog})

@login_required
def forum_list(request):
    from .models import ForumThread, HubCategory
    from django.db.models import Q
    
    query = request.GET.get('q', '')
    cat_slug = request.GET.get('category', '')
    
    threads = ForumThread.objects.all().order_by('-created_at')
    if query:
        threads = threads.filter(Q(title__icontains=query) | Q(content__icontains=query))
    if cat_slug:
        threads = threads.filter(category__slug=cat_slug)
        
    categories = HubCategory.objects.all()
    
    return render(request, 'knowledge_hub/forum_list.html', {
        'threads': threads,
        'categories': categories,
        'query': query,
        'selected_category': cat_slug,
    })

@login_required
def create_forum_thread(request):
    from .forms import ForumThreadForm
    if request.method == 'POST':
        form = ForumThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.author = request.user
            thread.save()
            messages.success(request, "Discussion thread created successfully!")
            return redirect('home:forum_list')
    else:
        form = ForumThreadForm()
    return render(request, 'knowledge_hub/forum_thread_form.html', {'form': form})

@login_required
def forum_thread_detail(request, thread_id):
    from .models import ForumThread, ForumComment
    from .forms import ForumCommentForm
    
    thread = get_object_or_404(ForumThread, id=thread_id)
    comments = thread.comments.all().order_by('created_at')
    
    if request.method == 'POST':
        form = ForumCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.thread = thread
            comment.author = request.user
            comment.save()
            messages.success(request, "Comment added!")
            return redirect('home:forum_thread_detail', thread_id=thread.id)
    else:
        form = ForumCommentForm()
        
    return render(request, 'knowledge_hub/forum_thread_detail.html', {
        'thread': thread,
        'comments': comments,
        'form': form,
    })

@login_required
def create_blog(request):
    from .forms import BlogPostForm
    from django.utils.text import slugify
    from .models import BlogPost
    
    if request.method == 'POST':
        form = BlogPostForm(request.POST)
        if form.is_valid():
            blog = form.save(commit=False)
            blog.author = request.user
            
            # Generate unique slug
            base_slug = slugify(blog.title)
            slug = base_slug
            counter = 1
            while BlogPost.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            blog.slug = slug
            blog.save()
            messages.success(request, "Blog post created successfully!")
            return redirect('home:blog_list')
    else:
        form = BlogPostForm()
    return render(request, 'knowledge_hub/blog_form.html', {'form': form})

@login_required
def delete_blog(request, blog_id):
    from .models import BlogPost
    from django.core.exceptions import PermissionDenied
    
    blog = get_object_or_404(BlogPost, id=blog_id)
    if not (request.user == blog.author or request.user.is_staff):
        raise PermissionDenied("You do not have permission to delete this blog post.")
        
    if request.method == 'POST':
        blog.delete()
        messages.success(request, "Blog post deleted successfully.")
        return redirect('home:blog_list')
    return redirect('home:blog_detail', slug=blog.slug)

@login_required
def delete_resource(request, resource_id):
    from .models import Resource
    from django.core.exceptions import PermissionDenied
    
    resource = get_object_or_404(Resource, id=resource_id)
    if not (request.user == resource.uploaded_by or request.user.is_staff):
        raise PermissionDenied("You do not have permission to delete this resource.")
        
    if request.method == 'POST':
        resource.delete()
        messages.success(request, "Resource deleted successfully.")
    return redirect('home:resource_list')

@login_required
def delete_forum_thread(request, thread_id):
    from .models import ForumThread
    from django.core.exceptions import PermissionDenied
    
    thread = get_object_or_404(ForumThread, id=thread_id)
    if not (request.user == thread.author or request.user.is_staff):
        raise PermissionDenied("You do not have permission to delete this discussion thread.")
        
    if request.method == 'POST':
        thread.delete()
        messages.success(request, "Discussion thread deleted successfully.")
        return redirect('home:forum_list')
    return redirect('home:forum_thread_detail', thread_id=thread.id)

# Help & Support Center Views

@login_required
def support_home(request):
    from .models import FAQ, SupportTicket
    from django.db.models import Q
    
    query = request.GET.get('q', '')
    cat = request.GET.get('category', '')
    
    faqs = FAQ.objects.all()
    if query:
        faqs = faqs.filter(Q(question__icontains=query) | Q(answer__icontains=query))
    if cat:
        faqs = faqs.filter(category=cat)
        
    if request.user.is_staff:
        user_tickets = SupportTicket.objects.all()
    else:
        user_tickets = SupportTicket.objects.filter(user=request.user)
        
    return render(request, 'support/home.html', {
        'faqs': faqs,
        'user_tickets': user_tickets,
        'query': query,
        'selected_category': cat,
        'faq_categories': FAQ.FAQ_CATEGORY_CHOICES,
    })

@login_required
def create_ticket(request):
    from .forms import SupportTicketForm
    if request.method == 'POST':
        form = SupportTicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.status = 'open'
            ticket.save()
            messages.success(request, "Support ticket created successfully! Support staff will review it shortly.")
            return redirect('home:support_home')
    else:
        form = SupportTicketForm()
    return render(request, 'support/ticket_form.html', {'form': form})

@login_required
def ticket_detail(request, ticket_id):
    from .models import SupportTicket, TicketMessage
    from .forms import TicketMessageForm
    
    # Restrict to ticket creator or admin
    if request.user.is_staff:
        ticket = get_object_or_404(SupportTicket, id=ticket_id)
    else:
        ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
        
    messages_list = ticket.messages.all().order_by('created_at')
    
    if request.method == 'POST':
        form = TicketMessageForm(request.POST, request.FILES)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.ticket = ticket
            msg.sender = request.user
            msg.save()
            
            # Auto-update status
            if request.user.is_staff:
                ticket.status = 'in_progress'
            else:
                ticket.status = 'open'
            ticket.save()
            
            messages.success(request, "Response submitted successfully!")
            return redirect('home:ticket_detail', ticket_id=ticket.id)
    else:
        form = TicketMessageForm()
        
    return render(request, 'support/ticket_detail.html', {
        'ticket': ticket,
        'ticket_messages': messages_list,
        'form': form,
    })

@login_required
def close_ticket(request, ticket_id):
    from .models import SupportTicket
    
    # Restrict to ticket creator or admin
    if request.user.is_staff:
        ticket = get_object_or_404(SupportTicket, id=ticket_id)
    else:
        ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
        
    if request.method == 'POST':
        ticket.status = 'resolved'
        ticket.save()
        messages.success(request, "Ticket has been successfully marked as resolved.")
        
    return redirect('home:ticket_detail', ticket_id=ticket.id)

# AI Agent / Smart Assistant Views

@login_required
def ai_assistant_home(request):
    return render(request, 'support/ai_assistant.html')

@login_required
def ai_assistant_chat_ajax(request):
    import json
    import os
    import requests
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.http import JsonResponse
    from .models import CustomUser, Session
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
        except Exception:
            return JsonResponse({'status': 'error', 'reply': 'Invalid request body.'}, status=400)
            
        if not user_message:
            return JsonResponse({'status': 'error', 'reply': 'Message cannot be empty.'}, status=400)
            
        # Get GROQ_API_KEY from settings or environment variables
        api_key = getattr(settings, 'GROQ_API_KEY', os.environ.get('GROQ_API_KEY', ''))
        
        # If API key is available, call GROQ completions endpoint
        if api_key:
            try:
                # Add database context as system instructions to make it smart!
                mentors = CustomUser.objects.filter(user_type='mentor')
                mentor_info = []
                for m in mentors:
                    skills_list = ", ".join([t.name for t in m.skills.all()])
                    mentor_info.append(f"Mentor: {m.full_name or m.username} (Skills: {skills_list}, Bio: {m.mentor_bio or 'No bio'})")
                mentor_context = "\n".join(mentor_info)
                
                system_instruction = (
                    "You are the official AI Assistant for 'Let's Connect' — a Peer-to-Professional Guidance Platform "
                    "built as a Final Year Project (FYP). You are knowledgeable, professional, warm, and helpful.\n\n"
                    
                    "=== PLATFORM OVERVIEW ===\n"
                    "Let's Connect is a web-based mentoring platform where students and professionals can connect with experienced mentors "
                    "for guidance, career advice, and skill development. Built with Django, Bootstrap 5, and integrated AI.\n\n"
                    
                    "=== THE 12 MODULES ===\n"
                    "1. **User Authentication & Profile Management**: Users can register as 'Mentor' or 'Mentee'. Profiles include bio, "
                    "skills (tags), profile picture, location, and social links. OTP-based email verification is supported.\n"
                    "2. **Mentor–Mentee Matching System**: Mentees can browse mentors, filter by skills/expertise, and view detailed profiles. "
                    "Smart skill-based matching recommends the best mentors.\n"
                    "3. **Session Booking & Scheduling**: Mentees book 15-minute slots with mentors. Sessions go through a lifecycle: "
                    "Pending → Approved → Completed/Cancelled. Mentors manage their availability.\n"
                    "4. **Chat & Messaging Module**: Real-time messaging between matched mentor-mentee pairs using AJAX polling. "
                    "Supports text messages with timestamps and read receipts.\n"
                    "5. **Meeting Link Integration (Daily.co)**: Approved sessions get auto-generated video meeting rooms via Daily.co API. "
                    "One-click join from the session detail page.\n"
                    "6. **Feedback & Rating System**: After completing a session, mentees can rate mentors (1-5 stars) and leave reviews. "
                    "Average ratings are displayed on mentor profiles.\n"
                    "7. **Notification System**: In-app notifications for session bookings, approvals, new messages, and payment updates. "
                    "Bell icon with unread count in the navbar.\n"
                    "8. **Admin Dashboard**: Staff can manage users, sessions, payments, support tickets, and platform analytics. "
                    "Custom Django admin with filters and inline editing.\n"
                    "9. **Knowledge Hub**: Resources section with articles, blog posts, and community forum. Users can browse and contribute "
                    "educational content organized by categories.\n"
                    "10. **Help & Support Center**: FAQ page, support ticket system where users can create tickets, attach details, "
                    "and track ticket status (Open → In Progress → Resolved).\n"
                    "11. **Payment / Reward Module**: Session fee is Rs. 500 per 15-minute slot. Mentees upload payment screenshot proofs. "
                    "Admins verify payments before sessions are approved. Transaction history tracking.\n"
                    "12. **AI Agent / Smart Assistant (YOU!)**: You are this module! You use GROQ's Llama 3.3 70B model to provide "
                    "intelligent responses about the platform, recommend mentors, and guide users.\n\n"
                    
                    "=== TECH STACK ===\n"
                    "- Backend: Django 5.x (Python)\n"
                    "- Frontend: HTML5, Bootstrap 5, CSS3, JavaScript\n"
                    "- Database: SQLite (development)\n"
                    "- Video Calls: Daily.co API\n"
                    "- AI: GROQ API (Llama 3.3 70B Versatile)\n"
                    "- Forms: Django Crispy Forms with Bootstrap 5\n\n"
                    
                    "=== PRICING & RULES ===\n"
                    "- Session cost: Rs. 500 per 15-minute slot\n"
                    "- Payment method: Upload transaction screenshot for admin verification\n"
                    "- Sessions must be approved by the mentor before they are confirmed\n"
                    "- Video meetings are auto-created once a session is approved\n"
                    "- Users must be logged in to book sessions, chat, or access the assistant\n\n"
                    
                    "=== CURRENT MENTORS ON PLATFORM ===\n"
                    f"{mentor_context}\n\n"
                    
                    "=== YOUR BEHAVIOR GUIDELINES ===\n"
                    "- Always be helpful, polite, and encouraging\n"
                    "- If a user asks for a mentor, match them with available mentors from the list above\n"
                    "- If you don't know something specific, say so honestly and suggest contacting support\n"
                    "- You can help with: finding mentors, explaining features, booking guidance, payment info, technical help\n"
                    "- Keep responses concise but informative (2-4 paragraphs max)\n"
                    "- Use emojis sparingly for friendliness 😊\n"
                )
                
                response = requests.post(
                    'https://api.groq.com/openai/v1/chat/completions',
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': 'llama-3.3-70b-versatile',
                        'messages': [
                            {'role': 'system', 'content': system_instruction},
                            {'role': 'user', 'content': user_message}
                        ],
                        'temperature': 0.7,
                        'max_tokens': 1024
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    resp_data = response.json()
                    ai_reply = resp_data['choices'][0]['message']['content'].strip()
                    return JsonResponse({'status': 'success', 'reply': ai_reply})
                else:
                    # Fallback to local rule engine if API returns error
                    print(f"Groq API Error: {response.text}")
                    ai_reply = f"I encountered an issue contacting the GROQ AI service (Code: {response.status_code}). Here is my local assistant answer:\n\n"
            except Exception as e:
                print(f"Groq API Exception: {e}")
                ai_reply = "I had trouble connecting to the GROQ API. Here is a simulated response:\n\n"
        else:
            ai_reply = "GROQ API Key is not configured. To enable full AI intelligence, please set GROQ_API_KEY in your settings.py. Meanwhile, here is a rule-based matching reply:\n\n"

        # Local Smart Rule-Based Engine (Fallback & Local testing)
        user_message_lower = user_message.lower()
        if "mentor" in user_message_lower or "recommend" in user_message_lower or "find" in user_message_lower:
            # Query mentors matching query or skills
            from django.db.models import Q
            matching_mentors = CustomUser.objects.filter(user_type='mentor')
            
            # Simple keyword search on bio or skills
            found_mentors = []
            for m in matching_mentors:
                skills_list = [t.name.lower() for t in m.skills.all()]
                matched_skill = any(word in user_message_lower for word in skills_list)
                if matched_skill or (m.mentor_bio and any(word in m.mentor_bio.lower() for word in user_message_lower.split())):
                    found_mentors.append(m)
            
            if found_mentors:
                recs = ", ".join([f"{m.full_name or m.username} (Expertise: {', '.join([t.name for t in m.skills.all()])})" for m in found_mentors])
                ai_reply += f"Based on your query, I recommend connecting with the following mentors: {recs}."
            else:
                all_recs = ", ".join([m.full_name or m.username for m in matching_mentors[:3]])
                ai_reply += f"I couldn't find a mentor specifically matching that skill. However, here are some of our popular mentors: {all_recs}."
                
        elif "price" in user_message_lower or "cost" in user_message_lower or "fee" in user_message_lower or "pay" in user_message_lower:
            ai_reply += "Sessions on Let's Connect are priced at Rs. 500 per 15-minute slot. You can book sessions, upload payment transaction screenshots for verification, and join meeting links after approval."
        else:
            ai_reply += f"Hello! I am the Let's Connect Smart Assistant. I can help you find mentors, answer questions about bookings, or guide you through the platform. You asked: '{user_message}'. Please let me know how I can assist you further!"
            
        return JsonResponse({'status': 'success', 'reply': ai_reply})
        
    return JsonResponse({'status': 'error', 'reply': 'Invalid request method.'}, status=400)

