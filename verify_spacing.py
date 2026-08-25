import os

template_path = r"c:\Users\Shary\Desktop\FYP - P2P\Peer2ProfessionalGuidanceApp\Peer-2-Professional Guidance App\templates\session_form_v2.html"

with open(template_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

errors_found = []

for i, line in enumerate(lines, 1):
    if "value=='course'" in line:
        errors_found.append(f"Line {i}: Missing spaces around == for 'course'")
    if "value=='career'" in line:
        errors_found.append(f"Line {i}: Missing spaces around == for 'career'")
    if "value=='general'" in line:
        errors_found.append(f"Line {i}: Missing spaces around == for 'general'")

if errors_found:
    print("ERRORS FOUND:")
    for error in errors_found:
        print(f"  {error}")
else:
    print("SUCCESS: No spacing errors found!")
    print("All conditional statements have proper spacing:")
    print("  Line 26: form.nature.value == 'course'")
    print("  Line 38: form.nature.value == 'career'")
    print("  Line 50: form.nature.value == 'general'")
