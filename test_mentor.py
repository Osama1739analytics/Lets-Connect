import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'p2p.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Test the mentor user
try:
    mentor = User.objects.get(username='mentor')
    print(f"Username: {mentor.username}")
    print(f"user_type field: {mentor.user_type}")
    print(f"is_mentor() method: {mentor.is_mentor()}")
    print(f"is_mentee() method: {mentor.is_mentee()}")
except User.DoesNotExist:
    # Try admin
    try:
        mentor = User.objects.get(username='admin')
        print(f"Username: {mentor.username}")
        print(f"user_type field: {mentor.user_type}")
        print(f"is_mentor() method: {mentor.is_mentor()}")
        print(f"is_mentee() method: {mentor.is_mentee()}")
    except:
        print("No mentor user found")
