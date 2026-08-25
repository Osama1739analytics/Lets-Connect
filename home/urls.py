from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_start, name='signup'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('profile/google-confirm/', views.google_profile_confirm, name='google_profile_confirm'),
    path('onboarding/', views.onboarding_setup, name='onboarding_setup'),
    
    # Session Booking System
    path('sessions/create/', views.create_session, name='create_session'),
    path('sessions/browse/', views.browse_sessions, name='browse_sessions'),
    path('sessions/book/<int:session_id>/', views.book_session, name='book_session'),
    path('sessions/<int:session_id>/edit/', views.update_session, name='update_session'),
    path('sessions/<int:session_id>/delete/', views.delete_session, name='delete_session'),
    path('sessions/join/<int:session_id>/', views.join_session_meeting, name='join_session_meeting'),
    path('sessions/complete/<int:session_id>/', views.complete_session, name='complete_session'),
    path('sessions/reschedule/<int:session_id>/', views.reschedule_session, name='reschedule_session'),

    # Profile Management
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/edit-payment/', views.edit_payment_details, name='edit_payment_details'),

    # Notifications & Presence
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/delete-all/', views.delete_all_notifications, name='delete_all_notifications'),
    path('notifications/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('presence/update/', views.update_presence, name='update_presence'),
    
    # Real-Time Chat & Message Management
    path('chat/', views.chat_inbox, name='chat_inbox'),
    path('chat/<int:user_id>/', views.chat_room, name='chat_room'),
    path('chat/delete-thread/<int:user_id>/', views.delete_chat_thread, name='delete_chat_thread'),
    path('chat/message/delete/<int:message_id>/', views.delete_message, name='delete_message'),
    path('chat/message/edit/<int:message_id>/', views.edit_message, name='edit_message'),
    path('chat/send-ajax/', views.send_message_ajax, name='send_message_ajax'),
    path('chat/fetch-ajax/<int:user_id>/', views.fetch_messages_ajax, name='fetch_messages_ajax'),

    # Payment Workflow
    path('sessions/<int:session_id>/payment/', views.submit_payment, name='submit_payment'),
    path('sessions/<int:session_id>/verify/', views.verify_payment, name='verify_payment'),

    # Networking / Connect Requests
    path('connect/<int:user_id>/', views.send_connect_request, name='send_connect_request'),
    path('connect/disconnect/<int:user_id>/', views.disconnect_user, name='disconnect_user'),
    path('requests/', views.manage_connect_requests, name='manage_connect_requests'),

    # Public Profile & Reviews
    path('u/<str:username>/', views.public_profile, name='public_profile'),
    path('sessions/<int:session_id>/review/', views.leave_review, name='leave_review'),

    # Knowledge Hub URLs
    path('hub/', views.knowledge_hub_dashboard, name='hub_dashboard'),
    path('hub/resources/', views.resource_list, name='resource_list'),
    path('hub/resources/upload/', views.upload_resource, name='upload_resource'),
    path('hub/resources/delete/<int:resource_id>/', views.delete_resource, name='delete_resource'),
    path('hub/blogs/', views.blog_list, name='blog_list'),
    path('hub/blogs/new/', views.create_blog, name='create_blog'),
    path('hub/blogs/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('hub/blogs/delete/<int:blog_id>/', views.delete_blog, name='delete_blog'),
    path('hub/forum/', views.forum_list, name='forum_list'),
    path('hub/forum/new/', views.create_forum_thread, name='create_forum_thread'),
    path('hub/forum/<int:thread_id>/', views.forum_thread_detail, name='forum_thread_detail'),
    path('hub/forum/delete/<int:thread_id>/', views.delete_forum_thread, name='delete_forum_thread'),

    # Help & Support Center URLs
    path('support/', views.support_home, name='support_home'),
    path('support/ticket/new/', views.create_ticket, name='create_ticket'),
    path('support/ticket/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('support/ticket/<int:ticket_id>/close/', views.close_ticket, name='close_ticket'),

    # AI Assistant URLs
    path('support/assistant/', views.ai_assistant_home, name='ai_assistant_home'),
    path('support/assistant/chat-ajax/', views.ai_assistant_chat_ajax, name='ai_assistant_chat_ajax'),

    # Fallback for unknown app routes
    path('<path:unused_path>', views.page_not_found, name='page_not_found'),
]