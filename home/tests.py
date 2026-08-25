from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Session, ConnectionRequest, Notification
from decimal import Decimal

User = get_user_model()

class PaymentModuleTest(TestCase):
    def setUp(self):
        self.mentor = User.objects.create_user(username='mentor', email='mentor@test.com', password='password', user_type='mentor')
        self.mentee = User.objects.create_user(username='mentee', email='mentee@test.com', password='password', user_type='mentee')

    def test_session_pricing_logic(self):
        """Test that Session.total_price is auto-calculated correctly."""
        # Test 15 mins (Rs. 500)
        session15 = Session.objects.create(
            initiator=self.mentor,
            subject_detail="Test 15",
            duration_minutes=15
        )
        self.assertEqual(session15.total_price, Decimal('500.00'))

        # Test 30 mins (Rs. 1000)
        session30 = Session.objects.create(
            initiator=self.mentor,
            subject_detail="Test 30",
            duration_minutes=30
        )
        self.assertEqual(session30.total_price, Decimal('1000.00'))

        # Test 2 hours (Rs. 4000)
        session120 = Session.objects.create(
            initiator=self.mentor,
            subject_detail="Test 120",
            duration_minutes=120
        )
        self.assertEqual(session120.total_price, Decimal('4000.00'))

class NetworkingModuleTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='u1@test.com', password='password')
        self.user2 = User.objects.create_user(username='user2', email='u2@test.com', password='password')

    def test_connection_request_creation(self):
        """Test that ConnectionRequest stores the correct status."""
        req = ConnectionRequest.objects.create(sender=self.user1, receiver=self.user2)
        self.assertEqual(req.status, 'pending')
        
    def test_connection_notification_logic(self):
        """Verify that notification creation works with the new model."""
        # Simple verification of Notification model integration
        notif = Notification.objects.create(
            recipient=self.user2,
            sender=self.user1,
            verb="sent you a connection request"
        )
        self.assertEqual(notif.recipient, self.user2)
        self.assertEqual(notif.verb, "sent you a connection request")

from .models import HubCategory, Resource, BlogPost, ForumThread, ForumComment

class KnowledgeHubTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='hubuser', email='hub@test.com', password='password')
        self.category = HubCategory.objects.create(name="Python", slug="python", description="Python topics")
        self.client.force_login(self.user)

    def test_hub_dashboard_status_code(self):
        response = self.client.get('/hub/')
        self.assertEqual(response.status_code, 200)

    def test_resource_list_view(self):
        Resource.objects.create(
            title="Python Basics",
            description="Intro to Python",
            link="https://python.org",
            category=self.category,
            uploaded_by=self.user
        )
        response = self.client.get('/hub/resources/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python Basics")

    def test_blog_list_view(self):
        BlogPost.objects.create(
            title="Django vs FastAPI",
            slug="django-vs-fastapi",
            content="Comparing frameworks.",
            author=self.user,
            category=self.category
        )
        response = self.client.get('/hub/blogs/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Django vs FastAPI")

    def test_forum_thread_views(self):
        thread = ForumThread.objects.create(
            title="How to learn Django?",
            content="Looking for recommended tutorials.",
            author=self.user,
            category=self.category
        )
        # Test thread list
        response = self.client.get('/hub/forum/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "How to learn Django?")

        # Test thread detail & comment submission
        response = self.client.post(f'/hub/forum/{thread.id}/', {'content': 'Use the official docs!'})
        self.assertEqual(response.status_code, 302) # Redirects back to detail page
        self.assertTrue(ForumComment.objects.filter(thread=thread, content='Use the official docs!').exists())

    def test_create_blog_view(self):
        response = self.client.post('/hub/blogs/new/', {
            'title': 'Test Blog Creation',
            'content': 'This is a test blog creation article content.',
            'category': self.category.id
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(BlogPost.objects.filter(title='Test Blog Creation').exists())

    def test_delete_blog_view_permissions(self):
        blog = BlogPost.objects.create(
            title="Temp Blog",
            slug="temp-blog",
            content="Content",
            author=self.user,
            category=self.category
        )
        
        # Another user cannot delete
        other_user = User.objects.create_user(username='otheruser', email='other@test.com', password='password')
        self.client.force_login(other_user)
        response = self.client.post(f'/hub/blogs/delete/{blog.id}/')
        self.assertEqual(response.status_code, 403) # Forbidden / PermissionDenied
        self.assertTrue(BlogPost.objects.filter(id=blog.id).exists())
        
        # Author can delete
        self.client.force_login(self.user)
        response = self.client.post(f'/hub/blogs/delete/{blog.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(BlogPost.objects.filter(id=blog.id).exists())

    def test_delete_resource_view_permissions(self):
        res = Resource.objects.create(
            title="Temp Resource",
            link="https://temp.org",
            category=self.category,
            uploaded_by=self.user
        )
        
        # Another user cannot delete
        other_user = User.objects.create_user(username='otheruser2', email='other2@test.com', password='password')
        self.client.force_login(other_user)
        response = self.client.post(f'/hub/resources/delete/{res.id}/')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Resource.objects.filter(id=res.id).exists())
        
        # Author can delete
        self.client.force_login(self.user)
        response = self.client.post(f'/hub/resources/delete/{res.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Resource.objects.filter(id=res.id).exists())

    def test_delete_forum_thread_view_permissions(self):
        thread = ForumThread.objects.create(
            title="Temp Thread",
            content="Content",
            author=self.user,
            category=self.category
        )
        
        # Another user cannot delete
        other_user = User.objects.create_user(username='otheruser3', email='other3@test.com', password='password')
        self.client.force_login(other_user)
        response = self.client.post(f'/hub/forum/delete/{thread.id}/')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(ForumThread.objects.filter(id=thread.id).exists())
        
        # Author can delete
        self.client.force_login(self.user)
        response = self.client.post(f'/hub/forum/delete/{thread.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ForumThread.objects.filter(id=thread.id).exists())

from .models import FAQ, SupportTicket, TicketMessage

class SupportCenterTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='supportuser', email='support@test.com', password='password')
        self.faq = FAQ.objects.create(question="How to reset password?", answer="Go to settings.", category="accounts")
        self.client.force_login(self.user)

    def test_support_home_status_code(self):
        response = self.client.get('/support/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "How to reset password?")

    def test_create_ticket_view(self):
        response = self.client.post('/support/ticket/new/', {
            'subject': 'Billing error',
            'message': 'Charged twice for session.',
            'priority': 'high'
        })
        self.assertEqual(response.status_code, 302) # Redirects back to support home
        self.assertTrue(SupportTicket.objects.filter(user=self.user, subject='Billing error').exists())

    def test_ticket_detail_and_reply_view(self):
        ticket = SupportTicket.objects.create(
            user=self.user,
            subject="Technical bug",
            message="Chat is not loading.",
            priority="medium"
        )
        response = self.client.get(f'/support/ticket/{ticket.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chat is not loading.")

        # Post reply message
        response = self.client.post(f'/support/ticket/{ticket.id}/', {
            'message': 'Still not loading today.'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(TicketMessage.objects.filter(ticket=ticket, message='Still not loading today.').exists())

    def test_close_ticket_view(self):
        ticket = SupportTicket.objects.create(
            user=self.user,
            subject="Bug to close",
            message="Please close.",
            priority="low",
            status="open"
        )
        response = self.client.post(f'/support/ticket/{ticket.id}/close/')
        self.assertEqual(response.status_code, 302)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'resolved')

    def test_create_ticket_with_attachment(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        mock_file = SimpleUploadedFile("proof.txt", b"Mock file content", content_type="text/plain")
        response = self.client.post('/support/ticket/new/', {
            'subject': 'Ticket with attachment',
            'message': 'Check this file.',
            'priority': 'medium',
            'attachment': mock_file
        })
        self.assertEqual(response.status_code, 302)
        ticket = SupportTicket.objects.get(subject='Ticket with attachment')
        self.assertTrue(bool(ticket.attachment))
        self.assertTrue(ticket.attachment.name.endswith('.txt'))
        self.assertIn('proof', ticket.attachment.name)

    def test_reply_with_attachment(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        ticket = SupportTicket.objects.create(
            user=self.user,
            subject="Reply attachment",
            message="Check replies.",
            priority="low"
        )
        mock_file = SimpleUploadedFile("reply_proof.png", b"Mock image content", content_type="image/png")
        response = self.client.post(f'/support/ticket/{ticket.id}/', {
            'message': 'Here is the proof screenshot.',
            'attachment': mock_file
        })
        self.assertEqual(response.status_code, 302)
        reply = TicketMessage.objects.get(ticket=ticket, message='Here is the proof screenshot.')
        self.assertTrue(bool(reply.attachment))
        self.assertTrue(reply.attachment.name.endswith('.png'))
        self.assertIn('reply_proof', reply.attachment.name)

class AIAssistantTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='aiuser', email='ai@test.com', password='password')
        self.client.force_login(self.user)

    def test_assistant_home_view(self):
        response = self.client.get('/support/assistant/')
        self.assertEqual(response.status_code, 200)

    def test_assistant_chat_ajax_view(self):
        import json
        response = self.client.post(
            '/support/assistant/chat-ajax/',
            data=json.dumps({'message': 'Explain cost details'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        resp_data = response.json()
        self.assertEqual(resp_data['status'], 'success')
        self.assertIn('reply', resp_data)
