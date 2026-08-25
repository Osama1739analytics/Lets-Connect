from django.core.management.base import BaseCommand
from django.utils.text import slugify
from home.models import CustomUser, HubCategory, BlogPost

class Command(BaseCommand):
    help = 'Seeds sample blog posts and hub categories for the Knowledge Hub'

    def handle(self, *args, **options):
        # 1. Create or get categories
        categories_data = [
            ('Programming & Development', 'programming'),
            ('Career Guidance', 'career-guidance'),
            ('Study & Exam Preparation', 'study-tips'),
            ('UI/UX Design', 'design'),
        ]
        categories = {}
        for name, slug in categories_data:
            cat, created = HubCategory.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'description': f'Resources, articles, and discussions about {name}.'}
            )
            categories[slug] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {name}'))

        # 2. Get a user to author the blogs (prefer an active mentor or admin, fallback to first user or create a system user)
        author = CustomUser.objects.filter(user_type='mentor').first()
        if not author:
            author = CustomUser.objects.filter(is_superuser=True).first()
        if not author:
            author = CustomUser.objects.first()
        if not author:
            # Create a default system mentor
            author = CustomUser.objects.create_user(
                username='system_mentor',
                email='mentor@letsconnect.com',
                password='Password123',
                full_name='System Mentor',
                user_type='mentor',
                is_onboarded=True
            )
            self.stdout.write(self.style.SUCCESS('Created default mentor user system_mentor'))

        # 3. Create Sample Blogs
        blogs = [
            {
                'title': '10 Tips for Landing Your First Software Engineering Internship',
                'content': (
                    "Landing your first internship in tech can feel like a chicken-and-egg problem: you need experience to get an internship, but you need an internship to get experience.\n\n"
                    "Here are 10 practical strategies that will make you stand out:\n\n"
                    "1. **Build personal portfolio projects**: Don't just list class assignments. Build something you care about and put it on GitHub.\n"
                    "2. **Optimize your LinkedIn profile**: Clean up your headline, write a compelling summary, and list your skills.\n"
                    "3. **Contribute to Open Source**: Find beginner-friendly issues on GitHub projects to gain real-world collaboration experience.\n"
                    "4. **Practice coding interviews**: Consistency is key. Solve 1-2 LeetCode questions daily to sharpen your problem-solving skills.\n"
                    "5. **Network at local meetups and webinars**: Connecting with professionals face-to-face leads to referrals.\n"
                    "6. **Customize your resume**: Tailor your resume bullets to map keywords from job postings.\n"
                    "7. **Start writing technical blogs**: Explaining technical concepts in writing shows deep understanding.\n"
                    "8. **Prepare questions for interviewers**: Ask insightful questions about the team structure, tooling, or business model.\n"
                    "9. **Follow up professionally**: A simple thank-you email within 24 hours goes a long way.\n"
                    "10. **Use Peer-to-Professional platforms**: Book a 15-minute mock interview session with an industry mentor right here on Let's Connect!"
                ),
                'category_slug': 'career-guidance',
            },
            {
                'title': 'Mastering Python: From Syntax to Best Practices',
                'content': (
                    "Python is known for its clean syntax, but writing truly 'Pythonic' code is an art form. This guide covers writing cleaner, faster, and more readable Python code.\n\n"
                    "**1. Leverage List Comprehensions**\n"
                    "Instead of writing bulky loops to filter or transform lists, use comprehensions:\n"
                    "```python\n# Avoid\nsquares = []\nfor x in range(10):\n    squares.append(x**2)\n\n# Pythonic\nsquares = [x**2 for x in range(10)]\n```\n\n"
                    "**2. Use generator expressions for large datasets**\n"
                    "List comprehensions create the list in memory. Generators yield items one by one, saving RAM:\n"
                    "```python\n# Generates items on the fly\nsum(x**2 for x in range(1000000))\n```\n\n"
                    "**3. Context Managers for Resource Safety**\n"
                    "Always use `with` statements when handling files, databases, or sockets to ensure resource cleanup:\n"
                    "```python\nwith open('data.txt', 'r') as file:\n    content = file.read()\n```\n\n"
                    "**4. Code Formatting and Standards**\n"
                    "Follow PEP 8 styling. Use tools like `black` and `flake8` to enforce styling guidelines automatically."
                ),
                'category_slug': 'programming',
            },
            {
                'title': 'How to Organize Your Time During Final Exams',
                'content': (
                    "Exam season is notoriously stressful, but having a solid revision strategy can dramatically improve your performance and reduce anxiety.\n\n"
                    "Here is a step-by-step framework to maximize your study hours:\n\n"
                    "**1. The Pomodoro Technique**\n"
                    "Study for 25 minutes, then take a 5-minute break. After four cycles, take a longer 20-30 minute break. This keeps your brain focused and prevents burnout.\n\n"
                    "**2. Active Recall & Spaced Repetition**\n"
                    "Don't just re-read your notes. Test yourself using flashcards or summarize key points from memory. Revisit difficult topics at increasing intervals (1 day, 3 days, 1 week).\n\n"
                    "**3. Solve Past Exam Papers**\n"
                    "Practicing with actual exam questions under timed conditions is the best way to understand the exam format and identify weak areas.\n\n"
                    "**4. Get Proper Sleep**\n"
                    "Cramming all night is counterproductive. Studies show sleep consolidation is critical for memory retrieval. Aim for at least 7-8 hours of sleep before your exam."
                ),
                'category_slug': 'study-tips',
            },
            {
                'title': 'An Introduction to Mobile-First Responsive UI/UX Design',
                'content': (
                    "With over 60% of web traffic originating from mobile devices, designing interfaces starting from desktop layouts is no longer viable.\n\n"
                    "Designing 'Mobile-First' forces you to prioritize key content and interactions:\n\n"
                    "- **Content Hierarchy**: With limited screen space, you must place the most critical information and calls-to-action (CTAs) above the fold.\n"
                    "- **Touch Targets**: Make interactive buttons large enough (at least 48x48 pixels) and leave ample spacing to prevent accidental taps.\n"
                    "- **Performance Optimization**: Mobile users often have slower data connections. Optimize graphics, use system fonts where possible, and compress assets to ensure sub-second loading.\n"
                    "- **Fluid Layouts**: Use CSS flexbox and grid layouts rather than fixed pixel widths to adapt elements smoothly to any screen size."
                ),
                'category_slug': 'design',
            }
        ]

        for b_data in blogs:
            slug = slugify(b_data['title'])
            # Ensure unique slug
            base_slug = slug
            counter = 1
            while BlogPost.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            blog, created = BlogPost.objects.get_or_create(
                slug=slug,
                defaults={
                    'title': b_data['title'],
                    'content': b_data['content'],
                    'author': author,
                    'category': categories[b_data['category_slug']],
                    'is_published': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Seeded blog post: {b_data['title']}"))
            else:
                self.stdout.write(self.style.WARNING(f"Blog post already exists: {b_data['title']}"))

        self.stdout.write(self.style.SUCCESS('Knowledge Hub seeding completed successfully!'))
