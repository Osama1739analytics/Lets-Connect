
import os

path = r"c:\Users\Shary\Desktop\FYP - P2P\Peer2ProfessionalGuidanceApp\Peer-2-Professional Guidance App\templates\session_form.html"
dir_path = r"c:\Users\Shary\Desktop\FYP - P2P\Peer2ProfessionalGuidanceApp\Peer-2-Professional Guidance App\templates"

print(f"Checking path: {path}")
if os.path.exists(path):
    print("File EXISTS.")
    with open(path, 'r') as f:
        print(f.read()[:100])
else:
    print("File DOES NOT EXIST.")

print(f"\nListing directory: {dir_path}")
try:
    for f in os.listdir(dir_path):
        print(f)
except Exception as e:
    print(f"Error listing dir: {e}")
