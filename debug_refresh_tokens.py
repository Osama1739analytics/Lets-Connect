import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'p2p.settings')
django.setup()

from django.contrib.auth import get_user_model
from social_django.models import UserSocialAuth

User = get_user_model()

print("Checking Google Auth for all users...")
for user in User.objects.all():
    auth = user.social_auth.filter(provider='google-oauth2').first()
    if auth:
        has_refresh = 'refresh_token' in auth.extra_data
        print(f"User: {user.username} - Google Auth: YES - Refresh Token: {'YES' if has_refresh else 'MISSING'}")
    else:
        print(f"User: {user.username} - Google Auth: NO")
