import os
import re

card_path = r"c:\Users\Shary\Desktop\FYP - P2P\Peer2ProfessionalGuidanceApp\Peer-2-Professional Guidance App\templates\includes\session_card.html"

with open(card_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("Fixing broken template tags...")

# Fix Line 13-14: {{ session.initiator.full_name|default:session.initiator.username\r\n                        }}
content = re.sub(
    r'\{\{\s*session\.initiator\.full_name\|default:session\.initiator\.username\s*\r?\n\s*\}\}',
    '{{ session.initiator.full_name|default:session.initiator.username }}',
    content
)

# Fix Line 48-49: {{\r\n                session.description|truncatewords:20 }}
content = re.sub(
    r'\{\{\s*\r?\n\s*session\.description\|truncatewords:20\s*\}\}',
    '{{ session.description|truncatewords:20 }}',
    content
)

with open(card_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("FIXED: All broken template tags in session_card.html")
print("No more raw template code will show on browse sessions page")
