
import os
import django
from django.test import Client
from django.urls import reverse

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'p2p.settings')
django.setup()

from home.models import CustomUser

def verify_signup():
    client = Client()
    print("Verifying Signup Page Rendering...")
    try:
        response = client.get(reverse('home:signup'))
        if response.status_code == 200:
            print("SUCCESS: Signup page rendered with status 200.")
            if "Join Let's Connect" in str(response.content):
                 print("SUCCESS: Content 'Join Let's Connect' found.")
            else:
                 print("WARNING: Expected content not found.")
        else:
            print(f"FAILURE: Signup page returned status {response.status_code}")
            return
    except Exception as e:
        print(f"EXCEPTION during rendering verification: {e}")
        return

    print("\nVerifying User Registration (dry run)...")
    # We won't actually create a user to avoid polluting the DB endlessly, 
    # but we can try to post valid data and see if we get a redirect (success) or form errors.
    # Actually, let's create one and then delete it.
    
    test_email = "test_script_user@example.com"
    test_username = "test_script_user"
    
    # Cleanup if exists
    CustomUser.objects.filter(email=test_email).delete()
    
    data = {
        'full_name': 'Test Script User',
        'username': test_username,
        'email': test_email,
        'contact_number': '1231231234',
        'password': 'Password123!',
        'gender': 'Male',
        'user_type': 'mentee'
    }
    
    try:
        # Note: CSRF is disabled by default in Test Client
        response = client.post(reverse('home:signup'), data, follow=True)
        
        # Expecting redirect to verify_email
        if response.redirect_chain:
            print(f"SUCCESS: Redirected to {response.redirect_chain[0][0]}")
            users = CustomUser.objects.filter(email=test_email)
            if users.exists():
                print("SUCCESS: User created in database.")
                users.delete()
                print("Cleanup: User deleted.")
            else:
                 print("FAILURE: User not found in database.")
        else:
             print("FAILURE: No redirection. Form errors likely.")
             print(f"Context form errors: {response.context['form'].errors if 'form' in response.context else 'No form context'}")
             
    except Exception as e:
        print(f"EXCEPTION during registration verification: {e}")

if __name__ == "__main__":
    verify_signup()
