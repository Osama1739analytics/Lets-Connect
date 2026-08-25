import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'p2p.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("--- User Debug ---")
users = User.objects.all()
target_user = None

# Check for username 'mentor'
try:
    mentor_user = User.objects.get(username='mentor')
    print(f"User 'mentor' FOUND. Email: {mentor_user.email}")
    target_user = mentor_user
except User.DoesNotExist:
    print("User 'mentor' NOT FOUND.")

# Check for any user with type 'mentor'
mentors = User.objects.filter(user_type='mentor')
for m in mentors:
    print(f"Found Mentor-Type User: {m.username} (Email: {m.email})")
    if not target_user:
        target_user = m

# Action
if target_user:
    print(f"Resetting password for user: {target_user.username} to 'shary123'")
    target_user.set_password('shary123')
    target_user.save()
    print("Password reset successful.")
else:
    print("No mentor account found to fix. Creating 'mentor' user...")
    User.objects.create_user(username='mentor', email='mentor@example.com', password='shary123', user_type='mentor')
    print("Created user 'mentor' with password 'shary123'.")
