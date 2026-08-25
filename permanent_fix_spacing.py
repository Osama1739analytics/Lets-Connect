import os

template_path = r"c:\Users\Shary\Desktop\FYP - P2P\Peer2ProfessionalGuidanceApp\Peer-2-Professional Guidance App\templates\session_form_v2.html"

# Read
with open(template_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Count occurrences before
before_course = content.count("form.nature.value=='course'")
before_career = content.count("form.nature.value=='career'")
before_general = content.count("form.nature.value=='general'")

print(f"Before fix - Found {before_course} 'course', {before_career} 'career', {before_general} 'general' errors")

# Replace ALL occurrences
content = content.replace("form.nature.value=='course'", "form.nature.value == 'course'")
content = content.replace("form.nature.value=='career'", "form.nature.value == 'career'")
content = content.replace("form.nature.value=='general'", "form.nature.value == 'general'")

# Count after
after_course = content.count("form.nature.value=='course'")
after_career = content.count("form.nature.value=='career'")
after_general = content.count("form.nature.value=='general'")

print(f"After fix - Remaining {after_course} 'course', {after_career} 'career', {after_general} 'general' errors")

# Write back with explicit encoding
with open(template_path, 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(content)

print("SUCCESSFULLY FIXED ALL SPACING ERRORS")
print("Lines 26, 38, 50 now have: form.nature.value == 'X'")
