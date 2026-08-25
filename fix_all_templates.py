import os

# Fix session_form_v2.html spacing errors
template_path = r"c:\Users\Shary\Desktop\FYP - P2P\Peer2ProfessionalGuidanceApp\Peer-2-Professional Guidance App\templates\session_form_v2.html"

with open(template_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix all spacing issues
content = content.replace("form.nature.value=='course'", "form.nature.value == 'course'")
content = content.replace("form.nature.value=='career'", "form.nature.value == 'career'")
content = content.replace("form.nature.value=='general'", "form.nature.value == 'general'")

with open(template_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("FIXED: session_form_v2.html spacing errors")

# Fix session_card.html broken template tags
card_path = r"c:\Users\Shary\Desktop\FYP - P2P\Peer2ProfessionalGuidanceApp\Peer-2-Professional Guidance App\templates\includes\session_card.html"

with open(card_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the broken full_name tag (lines 13-14)
content = content.replace(
    "{{ session.initiator.full_name|default:session.initiator.username\r\n                        }}",
    "{{ session.initiator.full_name|default:session.initiator.username }}"
)

# Fix the broken description tag (lines 48-49)
content = content.replace(
    "{{\r\n                session.description|truncatewords:20 }}",
    "{{ session.description|truncatewords:20 }}"
)

with open(card_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("FIXED: session_card.html broken template tags")
print("All template issues resolved!")
