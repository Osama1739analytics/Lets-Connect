from django.contrib import admin
from django.http import HttpResponseRedirect
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.shortcuts import render
from django.contrib.admin.views.main import ChangeList
from .models import CustomUser, Session, Notification

# Register your models here.
from .models import EmailOTP, PendingSignup

class CustomAdminSite(admin.AdminSite):
    site_header = "Let's Connect Administration"
    site_title = "Let's Connect Admin"
    index_title = "Welcome to Let's Connect Administration Portal"
    
    def index(self, request, extra_context=None):
        """Custom admin index with statistics"""
        # Get statistics
        mentee_count = CustomUser.objects.filter(user_type='mentee').count()
        mentor_count = CustomUser.objects.filter(user_type='mentor').count()
        total_sessions = Session.objects.count()
        completed_sessions = Session.objects.filter(status='completed').count()
        recent_sessions = Session.objects.select_related('initiator', 'participant').order_by('-scheduled_at')[:10]
        total_notifications = Notification.objects.count()
        unread_notifications = Notification.objects.filter(is_read=False).count()
        
        extra_context = extra_context or {}
        extra_context.update({
            'mentee_count': mentee_count,
            'mentor_count': mentor_count,
            'total_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'recent_sessions': recent_sessions,
            'notification_stats': {
                'total': total_notifications,
                'unread': unread_notifications
            }
        })
        
        return super().index(request, extra_context)

    def logout(self, request, extra_context=None):
        """Custom logout to handle GET and redirect to login"""
        from django.contrib.auth import logout
        logout(request)
        return HttpResponseRedirect(reverse('p2p_admin:login'))

# Create custom admin site instance
admin_site = CustomAdminSite(name='p2p_admin')

@admin.register(CustomUser, site=admin_site)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'full_name', 'user_type_display', 'presence_display', 'session_stats', 'unread_notif_count', 'is_staff', 'date_joined')
    list_filter = ('user_type', 'presence_status', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'full_name', 'contact_number')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Information', {
            'fields': ('full_name', 'contact_number', 'age', 'user_type', 'presence_status')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Information', {
            'fields': ('full_name', 'contact_number', 'age', 'email', 'user_type')
        }),
    )
    
    def user_type_display(self, obj):
        """Display user type with colored badge"""
        if obj.user_type == 'mentee':
            return mark_safe(
                '<span style="background: #4facfe; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">🎓 MENTEE</span>'
            )
        elif obj.user_type == 'mentor':
            return mark_safe(
                '<span style="background: #fa709a; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">👨‍🏫 MENTOR</span>'
            )
        else:
            return mark_safe(
                '<span style="background: #6c757d; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">👤 MEMBER</span>'
            )
    user_type_display.short_description = 'User Type'
    user_type_display.admin_order_field = 'user_type'

    def presence_display(self, obj):
        """Display presence status with colored dot"""
        colors = {
            'online': '#28a745',
            'away': '#ffc107',
            'busy': '#dc3545',
            'offline': '#6c757d'
        }
        color = colors.get(obj.presence_status, '#6c757d')
        return format_html(
            '<span style="height: 10px; width: 10px; background-color: {}; border-radius: 50%; display: inline-block; margin-right: 5px;"></span> {}',
            color,
            obj.presence_status.capitalize()
        )
    presence_display.short_description = 'Presence'
    presence_display.admin_order_field = 'presence_status'

    def unread_notif_count(self, obj):
        """Display count of unread notifications"""
        return obj.unread_notifications_count
    unread_notif_count.short_description = 'Unread Notifications'
    
    def session_stats(self, obj):
        """Display session statistics"""
        total_initiated = obj.initiated_sessions.count()
        total_joined = obj.joined_sessions.count()
        completed = obj.initiated_sessions.filter(status='completed').count() + \
                    obj.joined_sessions.filter(status='completed').count()
        return format_html(
            '<div style="font-size: 12px;">'
            '<div><strong>Initiated:</strong> {}</div>'
            '<div><strong>Joined:</strong> {}</div>'
            '<div><strong>Completed:</strong> {}</div>'
            '</div>',
            total_initiated,
            total_joined,
            completed
        )
    session_stats.short_description = 'Session Stats'
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch_related for session counts"""
        return super().get_queryset(request).prefetch_related('initiated_sessions', 'joined_sessions')

@admin.register(Session, site=admin_site)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('subject_detail', 'nature', 'session_type', 'initiator', 'participant', 'status', 'scheduled_at')
    list_filter = ('nature', 'session_type', 'status', 'scheduled_at', 'created_at')
    search_fields = ('subject_detail', 'initiator__full_name', 'participant__full_name')
    ordering = ('-scheduled_at',)
    date_hierarchy = 'scheduled_at'
    
    fieldsets = (
        ('Session Info', {
            'fields': ('initiator', 'participant', 'session_type', 'nature', 'subject_detail', 'status')
        }),
        ('Schedule & Flexibility', {
            'fields': ('scheduled_at', 'flexibility_comments')
        }),
        ('Description', {
            'fields': ('description',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('initiator', 'participant')


@admin.register(EmailOTP, site=admin_site)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ('email', 'code', 'purpose', 'created_at', 'expires_at', 'is_used', 'attempts', 'resend_count')
    list_filter = ('purpose', 'is_used', 'created_at')
    search_fields = ('email',)

@admin.register(PendingSignup, site=admin_site)
class PendingSignupAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at')
    search_fields = ('email',)

@admin.register(Notification, site=admin_site)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'sender', 'verb', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at', 'verb')
    search_fields = ('recipient__username', 'sender__username', 'verb')
    ordering = ('-created_at',)
    
# Register standard sites for safety if needed, but we use admin_site

from .models import FAQ, SupportTicket, TicketMessage

@admin.register(FAQ, site=admin_site)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'order', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('question', 'answer')
    ordering = ('category', 'order')

class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 1

@admin.register(SupportTicket, site=admin_site)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'subject', 'priority', 'status', 'created_at')
    list_filter = ('priority', 'status', 'created_at')
    search_fields = ('subject', 'message', 'user__username')
    inlines = [TicketMessageInline]
    ordering = ('-created_at',)
