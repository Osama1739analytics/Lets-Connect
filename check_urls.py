import os
import django
from django.urls import reverse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'p2p.settings')
django.setup()

try:
    print(f"social:begin: {reverse('social:begin', args=['google-oauth2'])}")
    print(f"social:complete: {reverse('social:complete', args=['google-oauth2'])}")
except Exception as e:
    print(f"Error: {e}")
