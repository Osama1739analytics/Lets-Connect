from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from taggit.managers import TaggableManager

class CustomUser(AbstractUser):
    """Custom User model with additional fields"""
    USER_TYPE_CHOICES = [
        ('mentee', 'Mentee (Student)'),
        ('mentor', 'Mentor (Professional)'),
    ]
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    PRESENCE_STATUS_CHOICES = [
        ('online', 'Online'),
        ('away', 'Away'),
        ('busy', 'Busy'),
        ('offline', 'Offline'),
    ]

    email = models.EmailField(unique=True, blank=True, null=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='mentee',
        help_text='Choose whether you are a Mentee (seeking guidance) or Mentor (providing guidance)'
    )
    presence_status = models.CharField(
        max_length=10,
        choices=PRESENCE_STATUS_CHOICES,
        default='offline'
    )
    last_activity = models.DateTimeField(auto_now=True)
    is_calendar_connected = models.BooleanField(default=False)
    is_onboarded = models.BooleanField(default=False)
    personal_meeting_link = models.URLField(blank=True, null=True, help_text="Your permanent meeting link (Zoom, Google Meet, etc.)")

    # Payment details (for mentors)
    payment_method = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. Bank Deposit, EasyPaisa, JazzCash")
    account_title = models.CharField(max_length=100, blank=True, null=True, help_text="Official name on your account")
    account_number_or_iban = models.CharField(max_length=50, blank=True, null=True, help_text="Your bank account number or IBAN")

    @property
    def unread_notifications_count(self):
        return self.notifications.filter(is_read=False).count()

    @property
    def unread_messages_count(self):
        return self.received_messages.filter(is_read=False).count()

    @property
    def pending_connections_count(self):
        return self.received_connections.filter(status='pending').count()

    @property
    def average_rating(self):
        reviews = self.received_reviews.all()
        if reviews:
            # For better performance on larger datasets, we should use aggregate(Avg('rating')) but this is fine for now
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0.0

    @property
    def total_reviews(self):
        return self.received_reviews.count()

    @property
    def total_connections(self):
        from .models import ConnectionRequest
        from django.db.models import Q
        return ConnectionRequest.objects.filter(
            Q(sender=self) | Q(receiver=self),
            status='accepted'
        ).count()

    @property
    def total_sessions(self):
        from .models import Session
        from django.db.models import Q
        return Session.objects.filter(
            Q(initiator=self) | Q(participant=self),
            status='completed'
        ).count()

    @property
    def total_hours(self):
        from .models import Session
        from django.db.models import Q
        total_minutes = Session.objects.filter(
            Q(initiator=self) | Q(participant=self),
            status='completed'
        ).aggregate(models.Sum('duration_minutes'))['duration_minutes__sum'] or 0
        return round(total_minutes / 60, 1)

    # Mentor-specific profile fields
    mentor_expertise = models.TextField(
        blank=True,
        null=True,
        help_text="Short description of your domains of expertise (for mentors).",
    )
    mentor_availability = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Typical days/times or availability notes (for mentors).",
    )
    mentor_bio = models.TextField(
        blank=True,
        null=True,
        help_text="Longer biography or introduction (for mentors).",
    )
    is_available_for_mentoring = models.BooleanField(
        default=True,
        help_text="If checked, you will appear in 'Find a Mentor' results.",
    )

    # Mentee-specific profile fields
    learning_goals = models.TextField(
        blank=True,
        null=True,
        help_text="What you want to learn or achieve (for mentees).",
    )
    subjects_interested_in = models.TextField(
        blank=True,
        null=True,
        help_text="Subjects or topics where you want mentorship (for mentees).",
    )
    current_skill_level = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g. Beginner, Intermediate, Advanced (for mentees).",
    )
    is_seeking_mentorship = models.BooleanField(
        default=True,
        help_text="If checked, you will appear in 'View Mentees' results.",
    )
    
    # Skills/Interests Tags
    skills = TaggableManager(blank=True, help_text="A comma-separated list of skills/interests.")

    def __str__(self):
        return self.full_name or self.username

    def is_mentee(self):
        return self.user_type == 'mentee'

    def is_mentor(self):
        return self.user_type == 'mentor'

    def get_sessions_as_mentor(self):
        """Get sessions where this user is the mentor"""
        return self.mentor_sessions.all()

    def get_sessions_as_mentee(self):
        """Get sessions where this user is the mentee"""
        return self.mentee_sessions.all()

    def get_total_sessions_as_mentor(self):
        """Get total number of sessions as mentor"""
        return self.mentor_sessions.count()

    def get_total_sessions_as_mentee(self):
        """Get total number of sessions as mentee"""
        return self.mentee_sessions.count()

class Session(models.Model):
    """Model to track mentoring sessions (Requests and Posts)"""
    SESSION_TYPE_CHOICES = [
        ('request', 'Session Request (by Mentee)'),
        ('post', 'Session Post (by Mentor)'),
    ]

    SESSION_NATURE_CHOICES = [
        ('course', 'Course Guidance'),
        ('career', 'Career Guidance'),
        ('general', 'General Guidance'),
    ]

    SESSION_STATUS_CHOICES = [
        ('open', 'Open'),
        ('booked', 'Booked'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('submitted', 'Proof Submitted'),
        ('verified', 'Payment Verified'),
    ]

    DURATION_CHOICES = [
        (15, '15 Minutes (Rs. 500)'),
        (30, '30 Minutes (Rs. 1000)'),
        (45, '45 Minutes (Rs. 1500)'),
        (60, '1 Hour (Rs. 2000)'),
        (75, '1 Hour 15 Mins (Rs. 2500)'),
        (90, '1 Hour 30 Mins (Rs. 3000)'),
        (105, '1 Hour 45 Mins (Rs. 3500)'),
        (120, '2 Hours (Rs. 4000)'),
    ]

    initiator = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='initiated_sessions',
        null=True,
        blank=True,
        help_text="The person who created this session entry."
    )
    participant = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='joined_sessions',
        help_text="The person who accepts/books the session."
    )
    session_type = models.CharField(
        max_length=10,
        choices=SESSION_TYPE_CHOICES,
        null=True,
        blank=True
    )
    nature = models.CharField(
        max_length=20,
        choices=SESSION_NATURE_CHOICES,
        null=True,
        blank=True
    )
    subject_detail = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Name of Course, Career, or Topic"
    )
    description = models.TextField(blank=True, help_text="Additional details about the session.")
    scheduled_at = models.DateTimeField(null=True, blank=True)
    flexibility_comments = models.TextField(
        blank=True,
        help_text="e.g., 'I can start 30 mins before or after the given time.'"
    )
    status = models.CharField(
        max_length=20,
        choices=SESSION_STATUS_CHOICES,
        default='open'
    )
    
    # New Pricing and Payment Fields
    duration_minutes = models.PositiveIntegerField(
        choices=DURATION_CHOICES,
        default=15,
        help_text="Session duration in minutes."
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=500.00
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='unpaid'
    )
    payment_screenshot = models.ImageField(
        upload_to='payment_proofs/',
        null=True,
        blank=True,
        help_text="Upload the transaction confirmation screenshot."
    )
    meeting_link = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Paste the Google Meet or Zoom link here."
    )
    actual_started_at = models.DateTimeField(null=True, blank=True)
    actual_ended_at = models.DateTimeField(null=True, blank=True)
    is_started_early = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(
        default=False,
        help_text="Indicates if the 15-minute reminder has been sent."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    tags = TaggableManager(blank=True)

    def save(self, *args, **kwargs):
        # Auto-calculate price: Rs. 500 per 15 minutes
        if self.duration_minutes:
            self.total_price = (self.duration_minutes / 15) * 500
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-scheduled_at']
        verbose_name = 'Mentoring Session'
        verbose_name_plural = 'Mentoring Sessions'

    def __str__(self):
        return f"{self.get_nature_display()}: {self.subject_detail} ({self.session_type})"

    @property
    def is_open(self):
        return self.status == 'open'

class EmailOTP(models.Model):
    """One-time passcodes for email verification."""
    PURPOSE_CHOICES = [
        ('signup', 'Signup Verification'),
        ('login', 'Login Verification'),
    ]
    email = models.EmailField()
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES, default='signup')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    resend_count = models.PositiveIntegerField(default=0)
    last_sent_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.expires_at

class PendingSignup(models.Model):
    """Temporarily stores user credentials/data until email is verified."""
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, default='')
    full_name = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    user_type = models.CharField(max_length=10, default='mentee')
    age = models.PositiveIntegerField(blank=True, null=True)
    password_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def create_or_update(cls, *, email: str, username: str, raw_password: str, full_name: str = '', gender: str = '', contact_number: str = '', user_type: str = 'mentee', age: int = None):
        obj, _ = cls.objects.update_or_create(
            email=email,
            defaults={
                'username': username,
                'password_hash': make_password(raw_password),
                'full_name': full_name,
                'gender': gender,
                'contact_number': contact_number,
                'user_type': user_type,
                'age': age,
            }
        )
        return obj

class Notification(models.Model):
    """Model for in-app notifications"""
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    verb = models.CharField(max_length=255)  # e.g. "booked your session"
    target_session = models.ForeignKey('Session', on_delete=models.CASCADE, null=True, blank=True)
    link = models.URLField(max_length=500, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.verb}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class DirectMessage(models.Model):
    """Model for real-time one-on-one chat messages"""
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username} @ {self.timestamp}"

class ConnectionRequest(models.Model):
    """Model for networking connection requests between users"""
    CONNECTION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_connections')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_connections')
    status = models.CharField(max_length=10, choices=CONNECTION_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('sender', 'receiver')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username} ({self.status})"

class Review(models.Model):
    """Model to store ratings and feedback from Mentees for Mentors"""
    reviewer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='given_reviews')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_reviews')
    session = models.OneToOneField('Session', on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.reviewer.username} for {self.receiver.username} ({self.rating} Stars)"

class HubCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Hub Categories"

    def __str__(self):
        return self.name

class Resource(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='hub_resources/', blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    category = models.ForeignKey(HubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='resources')
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='uploaded_resources')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=255)
    content = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='blog_posts')
    category = models.ForeignKey(HubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='blog_posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class ForumThread(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='forum_threads')
    category = models.ForeignKey(HubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='forum_threads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class ForumComment(models.Model):
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='forum_comments')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.thread.title}"

class FAQ(models.Model):
    FAQ_CATEGORY_CHOICES = [
        ('general', 'General'),
        ('accounts', 'Account & Profiles'),
        ('sessions', 'Bookings & Sessions'),
        ('payments', 'Payments & Fees'),
    ]
    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=20, choices=FAQ_CATEGORY_CHOICES, default='general')
    order = models.PositiveIntegerField(default=0, help_text="Order in which FAQ is displayed.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'order', 'question']

    def __str__(self):
        return self.question

class SupportTicket(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=200)
    message = models.TextField(help_text="Describe your issue or query.")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    attachment = models.FileField(upload_to='support_attachments/', null=True, blank=True, help_text="Upload any screenshots or proof (optional).")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Ticket #{self.id}: {self.subject} ({self.get_status_display()})"

class TicketMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField()
    attachment = models.FileField(upload_to='support_attachments/', null=True, blank=True, help_text="Upload any screenshots or proof (optional).")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message by {self.sender.username} on Ticket #{self.ticket.id}"
