import os

template_path = r"c:\Users\Shary\Desktop\FYP - P2P\Peer2ProfessionalGuidanceApp\Peer-2-Professional Guidance App\templates\session_form_v2.html"

# Read the file
with open(template_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the button logic - make sure it's correct
# Find and replace the button section
old_button = '''                                <button type="submit"
                                    class="btn btn-primary w-100 py-3 rounded-pill fw-bold shadow-sm hover-scale">
                                    <i class="fas fa-paper-plane me-2"></i>
                                    {% if title == 'Edit Session' %}Update Session{% elif user.user_type == 'mentor' %}Post Session{% else %}Request Session{% endif %}
                                </button>'''

new_button = '''                                <button type="submit" class="btn btn-primary w-100 py-3 rounded-pill fw-bold shadow-sm hover-scale">
                                    <i class="fas fa-paper-plane me-2"></i>
                                    {% if title == 'Edit Session' %}
                                        Update Session
                                    {% elif user.is_mentor %}
                                        Post Session
                                    {% else %}
                                        Request Session
                                    {% endif %}
                                </button>'''

content = content.replace(old_button, new_button)

# Write back
with open(template_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed session_form_v2.html button logic")
