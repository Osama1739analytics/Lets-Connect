from social_core.pipeline.partial import partial
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()

# This step pauses the pipeline until the user confirms profile data.
@partial
def require_profile(strategy, backend, details, response, user=None, is_new=False, *args, **kwargs):
    # If user already exists, continue (allow login)
    if user:
        return {}

    # Save initial details from provider
    email = details.get('email') or ''
    full_name = details.get('fullname') or details.get('name') or details.get('first_name') or ''

    saved = strategy.session_get('saved_profile')
    if not saved or not saved.get('user_type'):
        strategy.session_set('saved_profile', {
            'email': email,
            'full_name': full_name,
        })
        # Redirect to our confirmation page to collect username, age, role
        return strategy.redirect(reverse('home:google_profile_confirm'))

    # Merge confirmed data back into details for user creation
    details['email'] = saved.get('email') or email
    details['full_name'] = saved.get('full_name') or full_name
    details['username'] = saved.get('username')
    if saved.get('gender'):
        details['gender'] = saved.get('gender')
    if saved.get('user_type'):
        details['user_type'] = saved.get('user_type')
    if saved.get('age'):
        details['age'] = saved.get('age')
    
    # Store password in details to be used by set_password step
    if saved.get('password'):
        details['set_password'] = saved.get('password')

    # Clear after use
    strategy.session_pop('saved_profile')
    return {}

def set_password(strategy, backend, user, details, is_new=False, *args, **kwargs):
    """
    Set password for the user if provided in details (from profile confirmation).
    Only set if user is new or explicitly requested.
    """
    password = details.get('set_password')
    if user and password:
        user.set_password(password)
        user.save()

def check_existing_email(backend, details, user=None, *args, **kwargs):
    """
    If no user is associated with this social account yet, check if the email
    is already taken by another account.
    """
    if user:
        return
    
    email = details.get('email')
    if email:
        if User.objects.filter(email__iexact=email).exists():
            messages.error(backend.strategy.request, f"An account with the email {email} already exists. Please log in with your password.")
            return redirect('home:login')

def update_calendar_status(backend, user, response, *args, **kwargs):
    """Update user's calendar connection status after social auth and verify refresh token."""
    if backend.name == 'google-oauth2':
        if user:
            # Check if we got a refresh token in this response
            refresh_token = response.get('refresh_token')
            
            # Or if it's already in the stored extra_data (from a previous login)
            auth = user.social_auth.filter(provider='google-oauth2').first()
            has_refresh = (refresh_token is not None) or (auth and auth.extra_data and 'refresh_token' in auth.extra_data)
            
            if has_refresh:
                user.is_calendar_connected = True
                user.save()
            else:
                # We don't have a refresh token - this is bad for future meeting creation
                user.is_calendar_connected = False # Mark as disconnected so they try again
                user.save()
                messages.warning(backend.strategy.request, "Google Calendar connected, but 'Offline Access' was not granted. Automatic meeting links may fail. Please disconnect and reconnect, ensuring you approve all permissions.")