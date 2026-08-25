import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'p2p.settings')
django.setup()

from social_django.models import UserSocialAuth
from django.contrib.auth import get_user_model

User = get_user_model()

print("--- Checking Social Auth Records ---")

users = User.objects.all()
for user in users:
    print(f"\nUser: {user.username} (Email: {user.email})")
    socials = UserSocialAuth.objects.filter(user=user)
    if socials.exists():
        for sa in socials:
            print(f"  - Provider: {sa.provider}")
            print(f"    UID: {sa.uid}")
            extra = sa.extra_data
            # Check for Access Token
            has_token = 'access_token' in extra
            # Check for Refresh Token
            has_refresh = 'refresh_token' in extra
            # Check Scopes (Google sometimes returns 'scope' string in extra_data)
            scopes = extra.get('scope', 'Not found in extra_data')
            
            print(f"    Has Access Token: {has_token}")
            print(f"    Has Refresh Token: {has_refresh}")
            print(f"    Scopes Granted: {scopes}")
            
            if 'calendar' in str(scopes):
                print("    [PASS] Calendar permission detected.")
            else:
                print("    [FAIL] Calendar permission NOT detected.")
    else:
        print("  - No Social Auth linked (Manual Account or unlinked).")

print("\n--- End Check ---")
