import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'p2p.settings')
django.setup()

from social_django.models import UserSocialAuth

auths = UserSocialAuth.objects.filter(provider='google-oauth2')
for auth in auths:
    print(f"User: {auth.user.username}")
    print(f"Extra Data: {auth.extra_data}")
    print("-" * 40)
