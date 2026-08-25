import os

templates_dir = r"c:\Users\Shary\Desktop\FYP - P2P\Peer2ProfessionalGuidanceApp\Peer-2-Professional Guidance App\templates"

replacements = [
    (".value=='mentee'", ".value == 'mentee'"),
    (".value=='mentor'", ".value == 'mentor'"),
    (".value=='course'", ".value == 'course'"),
    (".value=='career'", ".value == 'career'"),
    (".value=='general'", ".value == 'general'"),
]

for root, dirs, files in os.walk(templates_dir):
    for file in files:
        if file.endswith('.html'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content
            for old, new in replacements:
                new_content = new_content.replace(old, new)
            
            if new_content != content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Fixed {path}")
