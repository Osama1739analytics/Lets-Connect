import os

template_path = r"c:\Users\Shary\Desktop\FYP - P2P\Peer2ProfessionalGuidanceApp\Peer-2-Professional Guidance App\templates\session_form_v2.html"

# Read the file
with open(template_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix all the spacing issues
content = content.replace("form.nature.value=='course'", "form.nature.value == 'course'")
content = content.replace("form.nature.value=='career'", "form.nature.value == 'career'")
content = content.replace("form.nature.value=='general'", "form.nature.value == 'general'")

# Write it back
with open(template_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("FORCE FIXED: session_form_v2.html")
print("Fixed all == spacing issues")
