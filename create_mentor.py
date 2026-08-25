import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'p2p.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

try:
    User.objects.get(username='mentor')
    print("User 'mentor' already exists.")
    # Reset anyway just in case
    u = User.objects.get(username='mentor')
    u.set_password('shary123')
    u.save()
    print("Reset password for 'mentor'.")
except User.DoesNotExist:
    User.objects.create_user(username='mentor', email='mentor@test.com', password='shary123', user_type='mentor')
    print("Created user 'mentor' with password 'shary123'.")
