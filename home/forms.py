from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Session, HubCategory, Resource, BlogPost, ForumThread, ForumComment, SupportTicket, TicketMessage

class CustomUserCreationForm(UserCreationForm):
    """Legacy form (kept for reference)"""
    full_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        })
    )
    contact_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your contact number'
        })
    )
    age = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your age'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    user_type = forms.ChoiceField(
        choices=CustomUser.USER_TYPE_CHOICES,
        required=True,
        widget=forms.RadioSelect(attrs={
            'class': 'user-type-radio'
        }),
        help_text='Choose your role in the platform'
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'full_name', 'contact_number', 'age', 'user_type', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })

class LoginForm(forms.Form):
    """Login form"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

# New forms for OTP and Google profile confirmation
class EmailSignupStartForm(forms.Form):
    full_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Enter your full name'
    }))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Choose a unique username'
    }))
    gender = forms.ChoiceField(choices=(('male','Male'),('female','Female'),('other','Other')), widget=forms.Select(attrs={
        'class': 'form-control'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'Enter your email'
    }))
    contact_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Enter your contact number'
    }))
    user_type = forms.ChoiceField(choices=CustomUser.USER_TYPE_CHOICES, widget=forms.RadioSelect(attrs={
        'class': 'user-type-radio'
    }))
    age = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={
        'class': 'form-control', 'placeholder': 'Optional: Your age'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Enter a strong password'
    }))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Confirm your password'
    }))

    def clean_username(self):
        username = self.cleaned_data['username']
        if CustomUser.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password')
        p2 = cleaned.get('password_confirm')
        if p1 and p2 and p1 != p2:
            self.add_error('password_confirm', 'Passwords do not match.')
        return cleaned

class EmailVerificationForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'your@email.com',
        'autocomplete': 'email',
    }))
    otp = forms.CharField(max_length=6, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': '000000',
        'maxlength': '6',
        'inputmode': 'numeric',
        'autocomplete': 'one-time-code',
        'pattern': '[0-9]{6}',
    }))

class GoogleProfileConfirmForm(forms.Form):
    full_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Your full name'
    }))
    email = forms.EmailField(disabled=True, widget=forms.EmailInput(attrs={
        'class': 'form-control'
    }))
    contact_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your contact number'
    }))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Choose a username'
    }))
    gender = forms.ChoiceField(choices=(('male','Male'),('female','Female'),('other','Other')), widget=forms.Select(attrs={
        'class': 'form-control'
    }))
    user_type = forms.ChoiceField(choices=CustomUser.USER_TYPE_CHOICES, widget=forms.RadioSelect(attrs={
        'class': 'user-type-radio'
    }))
    age = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={
        'class': 'form-control', 'placeholder': 'Optional'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Set a password for standard login'
    }))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Confirm your password'
    }))

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password')
        p2 = cleaned.get('password_confirm')
        if p1 and p2 and p1 != p2:
            self.add_error('password_confirm', 'Passwords do not match.')
        return cleaned

class ProfileEditForm(forms.ModelForm):
    """Form for editing user profile with skills/expertise tags"""
    class Meta:
        model = CustomUser
        fields = [
            'full_name', 'contact_number', 'age', 'gender',
            # Mentee fields
            'learning_goals', 'subjects_interested_in', 'current_skill_level',
            # Mentor fields
            'mentor_expertise', 'mentor_availability', 'mentor_bio',
            # Payment fields
            'payment_method', 'account_title', 'account_number_or_iban',
            # Tags
            'skills'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your full name'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Your age'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'learning_goals': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'What do you want to learn?'}),
            'subjects_interested_in': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Topics you want to learn (e.g., Python, Web Development)'}),
            'current_skill_level': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Beginner, Intermediate, Advanced'}),
            'mentor_expertise': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Your areas of expertise'}),
            'mentor_availability': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Weekdays 6-8 PM'}),
            'mentor_bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell others about yourself and your experience'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Bank Deposit, JazzCash...'}),
            'account_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name as on account'}),
            'account_number_or_iban': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Account Number or IBAN'}),
            'skills': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'i.e., Python, HTML, etc'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Safely unpack tags so they show as cleanly comma-separated strings
            self.initial['skills'] = ", ".join(t.name for t in self.instance.skills.all())

class PaymentDetailsForm(forms.ModelForm):
    """Specific form for editing ONLY payment details."""
    class Meta:
        model = CustomUser
        fields = ['payment_method', 'account_title', 'account_number_or_iban']
        widgets = {
            'payment_method': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Bank Deposit, JazzCash...'}),
            'account_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Official name on your account'}),
            'account_number_or_iban': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Account Number or IBAN'}),
        }

class SessionForm(forms.ModelForm):
    """Unified form for both Mentor Posts and Mentee Requests"""
    class Meta:
        model = Session
        fields = ['nature', 'subject_detail', 'description', 'duration_minutes', 'scheduled_at', 'flexibility_comments', 'tags']
        widgets = {
            'nature': forms.Select(attrs={'class': 'form-control', 'id': 'nature-select'}),
            'subject_detail': forms.TextInput(attrs={'class': 'form-control', 'id': 'subject-detail-input', 'placeholder': 'Enter Name (Course/Career/Topic)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe what you want to learn or teach...'}),
            'duration_minutes': forms.Select(attrs={'class': 'form-control', 'id': 'duration-select'}),
            'scheduled_at': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local', 'step': '900'},
                format='%Y-%m-%dT%H:%M'
            ),
            'flexibility_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'e.g. Can start 30 mins before or after'}),
            'meeting_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://meet.google.com/xyz-abc-123'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python, Design, Career (Comma Separated)'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure subject_detail label is clear
        self.fields['subject_detail'].label = "Course / Career / Topic Name"
        self.fields['scheduled_at'].help_text = "Select your preferred date and time."

class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'description', 'file', 'link', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter resource title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe what this resource is about'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Optional: URL link (e.g. YouTube, GitHub)'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }

class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'content', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter blog title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': 'Write your article here...'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }

class ForumThreadForm(forms.ModelForm):
    class Meta:
        model = ForumThread
        fields = ['title', 'content', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter topic / question title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Provide detail about your question or discussion topic...'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }

class ForumCommentForm(forms.ModelForm):
    class Meta:
        model = ForumComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Type your comment/reply here...'}),
        }

class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['subject', 'message', 'priority', 'attachment']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'What is the issue about?'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Provide details about your query or technical issue...'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }

class TicketMessageForm(forms.ModelForm):
    class Meta:
        model = TicketMessage
        fields = ['message', 'attachment']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Type your response here...'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }
