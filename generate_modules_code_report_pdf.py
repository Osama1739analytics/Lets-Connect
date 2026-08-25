"""Generate PDF report: 12 modules and their code locations in the P2P app."""

from fpdf import FPDF

OUTPUT_FILE = "P2P_12_Modules_Code_Report.pdf"


class CodeReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(42, 93, 132)
        self.cell(0, 10, "Peer-2-Professional Guidance App", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(80, 80, 80)
        self.cell(0, 6, "12 Modules - Code Location Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)
        self.set_draw_color(42, 93, 132)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        if self.get_y() > 250:
            self.add_page()
        self.set_font("Helvetica", "B", 12)
        self.set_fill_color(42, 93, 132)
        self.set_text_color(255, 255, 255)
        self.cell(0, 9, title, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_text_color(0, 0, 0)

    def sub_heading(self, label):
        if self.get_y() > 265:
            self.add_page()
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(42, 93, 132)
        self.cell(0, 7, label, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)

    def body_text(self, text):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 9)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def bullet_list(self, items):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 9)
        for item in items:
            if self.get_y() > 270:
                self.add_page()
            self.set_x(self.l_margin)
            self.multi_cell(0, 5, f"  - {item}")
        self.ln(2)


MODULES = [
    {
        "title": "1. User Authentication & Profile Management",
        "purpose": (
            "Handles email/password signup with OTP verification, Google OAuth login, "
            "onboarding, profile editing, mentor payment account setup, and presence status."
        ),
        "models": ["CustomUser", "EmailOTP", "PendingSignup (home/models.py)"],
        "views": [
            "signup_start, verify_email, resend_otp, login_view, logout_view",
            "google_profile_confirm, onboarding_setup, profile_view",
            "edit_profile, edit_payment_details, update_presence (home/views.py)",
        ],
        "urls": [
            "/signup/, /verify-email/, /login/, /logout/, /onboarding/",
            "/profile/, /profile/edit/, /profile/edit-payment/",
            "Google OAuth: /auth/ (p2p/urls.py)",
        ],
        "templates": [
            "signup.html, verify_email.html, login.html",
            "google_profile_confirm.html, onboarding_setup.html",
            "profile.html, edit_profile.html, edit_payment_details.html",
        ],
        "other": [
            "Forms: home/forms.py (EmailSignupStartForm, LoginForm, etc.)",
            "Social pipeline: home/social_pipeline.py",
            "Admin: CustomUserAdmin, EmailOTPAdmin (home/admin.py)",
            "Settings: AUTH_USER_MODEL, SOCIAL_AUTH_*, EMAIL_*, OTP_* (p2p/settings.py)",
        ],
    },
    {
        "title": "2. Mentor-Mentee Matching System",
        "purpose": (
            "Skill-based session and mentor recommendations, people discovery with search/filter, "
            "connection requests, and public profile pages."
        ),
        "models": ["CustomUser (skills, availability)", "ConnectionRequest", "Session tags (home/models.py)"],
        "views": [
            "browse_sessions, send_connect_request, manage_connect_requests",
            "disconnect_user, public_profile (home/views.py)",
            "Helpers: _get_platform_users, _get_connection_user_ids, _filter_sessions",
        ],
        "urls": [
            "/sessions/browse/, /connect/<id>/, /requests/",
            "/connect/disconnect/<id>/, /u/<username>/",
        ],
        "templates": [
            "browse_sessions_v2.html, connect_requests_v2.html, public_profile.html",
            "includes/user_card.html, people_search_form.html, session_card.html",
        ],
        "other": [
            "Seed command: home/management/commands/seed_sessions.py",
        ],
    },
    {
        "title": "3. Session Booking & Scheduling",
        "purpose": (
            "Mentees post session requests; mentors post open sessions. Supports browse, book, "
            "edit, delete, reschedule, join, and complete. Pricing: Rs. 500 per 15 minutes."
        ),
        "models": ["Session (home/models.py)"],
        "views": [
            "create_session, browse_sessions, book_session, update_session",
            "delete_session, join_session_meeting, complete_session, reschedule_session, index",
        ],
        "urls": [
            "/sessions/create/, /sessions/browse/, /sessions/book/<id>/",
            "/sessions/<id>/edit/, /sessions/join/<id>/, /sessions/reschedule/<id>/",
        ],
        "templates": [
            "index.html, session_form_v2.html, browse_sessions_v2.html, includes/session_card.html",
        ],
        "other": [
            "Forms: SessionForm (home/forms.py)",
            "Signals: session_status_notification (home/signals.py)",
            "Commands: send_session_reminders.py, seed_sessions.py",
            "Admin: SessionAdmin (home/admin.py)",
        ],
    },
    {
        "title": "4. Chat & Messaging Module",
        "purpose": (
            "One-to-one direct messaging with inbox, chat rooms, AJAX send/fetch, "
            "WebSocket real-time delivery, and message edit/delete."
        ),
        "models": ["DirectMessage (home/models.py)"],
        "views": [
            "chat_inbox, chat_room, send_message_ajax, fetch_messages_ajax",
            "delete_chat_thread, delete_message, edit_message (home/views.py)",
        ],
        "urls": ["/chat/, /chat/<user_id>/, /chat/send-ajax/, /chat/fetch-ajax/<user_id>/"],
        "templates": ["chat.html"],
        "other": [
            "WebSocket: home/consumers.py (ChatConsumer)",
            "Routing: home/routing.py (ws/chat/<user_id>/)",
            "ASGI: p2p/asgi.py | Settings: CHANNEL_LAYERS, daphne, channels",
        ],
    },
    {
        "title": "5. Meeting Link Integration (Google Meet)",
        "purpose": (
            "Generates meeting links after payment approval. Priority: personal link, "
            "Google Calendar Meet API, then Daily.co fallback."
        ),
        "models": [
            "Session.meeting_link, CustomUser.personal_meeting_link",
            "CustomUser.is_calendar_connected (home/models.py)",
        ],
        "views": ["verify_payment, join_session_meeting, reschedule_session (home/views.py)"],
        "urls": ["/sessions/<id>/verify/, /sessions/join/<id>/, /sessions/reschedule/<id>/"],
        "templates": ["verify_payment.html, session cards in index.html"],
        "other": [
            "Services: home/services.py (generate_meeting_link, generate_google_meet_link)",
            "Social: update_calendar_status (home/social_pipeline.py)",
            "Settings: SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE, DAILY_API_KEY",
        ],
    },
    {
        "title": "6. Feedback & Rating System",
        "purpose": (
            "Mentees submit 1-5 star reviews with comments after sessions. "
            "Average ratings displayed on public profiles."
        ),
        "models": ["Review (home/models.py)", "CustomUser.average_rating property"],
        "views": ["leave_review, public_profile (home/views.py)"],
        "urls": ["/sessions/<id>/review/, /u/<username>/"],
        "templates": ["leave_review.html, public_profile.html"],
        "other": ["Notifications created on 5-star reviews in leave_review view"],
    },
    {
        "title": "7. Notification System",
        "purpose": (
            "In-app notifications for bookings, payments, messages, connections, reviews, "
            "and session reminders. Real-time push via WebSocket."
        ),
        "models": ["Notification (home/models.py)"],
        "views": [
            "notifications_view, mark_notification_read",
            "mark_all_notifications_read, delete_all_notifications",
        ],
        "urls": ["/notifications/, /notifications/read-all/, /notifications/read/<id>/"],
        "templates": ["notifications.html, notification bell in base.html"],
        "other": [
            "WebSocket: NotificationConsumer (home/consumers.py, ws/notifications/)",
            "Signals: notification_broadcast (home/signals.py)",
            "Command: send_session_reminders.py | Admin: NotificationAdmin",
        ],
    },
    {
        "title": "8. Admin Dashboard",
        "purpose": (
            "Custom Django admin site with dashboard statistics and CRUD for core platform entities."
        ),
        "models": [
            "Managed: CustomUser, Session, EmailOTP, PendingSignup",
            "Notification, FAQ, SupportTicket, TicketMessage",
        ],
        "views": ["CustomAdminSite in home/admin.py"],
        "urls": ["/admin/ (p2p/urls.py)"],
        "templates": ["templates/admin/index.html, templates/admin/base_site.html"],
        "other": ["Admin site name: p2p_admin | Custom stats on admin index page"],
    },
    {
        "title": "9. Knowledge Hub (Resources, Blog, Forum)",
        "purpose": (
            "Educational hub with categorized resources, blog posts, and community forum threads."
        ),
        "models": [
            "HubCategory, Resource, BlogPost, ForumThread, ForumComment (home/models.py)",
        ],
        "views": [
            "knowledge_hub_dashboard, resource_list, upload_resource, delete_resource",
            "blog_list, create_blog, blog_detail, delete_blog",
            "forum_list, create_forum_thread, forum_thread_detail, delete_forum_thread",
        ],
        "urls": ["/hub/, /hub/resources/, /hub/blogs/, /hub/forum/ and sub-routes"],
        "templates": ["templates/knowledge_hub/*.html (dashboard, blog, forum, resource)"],
        "other": [
            "Forms: ResourceForm, BlogPostForm, ForumThreadForm (home/forms.py)",
            "Seed: home/management/commands/seed_blogs.py",
        ],
    },
    {
        "title": "10. Help & Support Center",
        "purpose": (
            "FAQ browsing with search, support ticket creation with attachments, "
            "threaded replies, and ticket close workflow."
        ),
        "models": ["FAQ, SupportTicket, TicketMessage (home/models.py)"],
        "views": ["support_home, create_ticket, ticket_detail, close_ticket (home/views.py)"],
        "urls": ["/support/, /support/ticket/new/, /support/ticket/<id>/"],
        "templates": ["support/home.html, ticket_form.html, ticket_detail.html"],
        "other": [
            "Forms: SupportTicketForm, TicketMessageForm (home/forms.py)",
            "Admin: FAQAdmin, SupportTicketAdmin (home/admin.py)",
        ],
    },
    {
        "title": "11. Payment Module",
        "purpose": (
            "Mentee uploads payment screenshot; mentor verifies or rejects. "
            "On approval, meeting link is generated and both parties are notified."
        ),
        "models": [
            "Session.payment_status, payment_screenshot, total_price",
            "CustomUser payment bank fields (home/models.py)",
        ],
        "views": [
            "submit_payment, verify_payment, edit_payment_details, book_session",
        ],
        "urls": [
            "/sessions/<id>/payment/, /sessions/<id>/verify/, /profile/edit-payment/",
        ],
        "templates": ["submit_payment.html, verify_payment.html, edit_payment_details.html"],
        "other": [
            "Forms: PaymentDetailsForm (home/forms.py)",
            "Services: generate_meeting_link called from verify_payment",
        ],
    },
    {
        "title": "12. AI Agent Smart Assistant Module",
        "purpose": (
            "Groq-powered in-app assistant with platform-aware system prompt. "
            "Falls back to rule-based mentor matching if API is unavailable."
        ),
        "models": ["Uses CustomUser and Session data for context (read-only)"],
        "views": ["ai_assistant_home, ai_assistant_chat_ajax (home/views.py)"],
        "urls": ["/support/assistant/, /support/assistant/chat-ajax/"],
        "templates": ["support/ai_assistant.html"],
        "other": [
            "Settings: GROQ_API_KEY (p2p/settings.py)",
            "API: Groq llama-3.3-70b-versatile via api.groq.com",
        ],
    },
]


def generate_pdf():
    pdf = CodeReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        0,
        5,
        "This document maps the twelve functional modules of the Peer-2-Professional (P2P) "
        "Guidance Platform to their implementation locations in the Django codebase. "
        "Primary application code resides in the home/ app; project configuration is in p2p/; "
        "UI templates are in templates/.",
    )
    pdf.ln(4)

    pdf.section_title("Module Summary")
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(230, 240, 250)
    col_w = [8, 62, 85, 35]
    headers = ["#", "Module", "Primary Purpose", "Status"]
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 8, h, border=1, fill=True, new_x="RIGHT", new_y="TOP")
    pdf.ln()

    summaries = [
        ("1", "Auth & Profile", "OTP, OAuth, profiles", "Implemented"),
        ("2", "Matching System", "Skills, connections, discover", "Implemented"),
        ("3", "Session Booking", "Create, book, schedule", "Implemented"),
        ("4", "Chat & Messaging", "WebSocket + AJAX chat", "Implemented"),
        ("5", "Google Meet Links", "Calendar / Daily.co links", "Implemented"),
        ("6", "Feedback & Rating", "Star reviews", "Implemented"),
        ("7", "Notifications", "In-app + WebSocket alerts", "Implemented"),
        ("8", "Admin Dashboard", "Custom Django admin", "Implemented"),
        ("9", "Knowledge Hub", "Resources, blog, forum", "Implemented"),
        ("10", "Help & Support", "FAQ + tickets", "Implemented"),
        ("11", "Payment Module", "Screenshot verification", "Implemented"),
        ("12", "AI Assistant", "Groq smart assistant", "Implemented"),
    ]
    pdf.set_font("Helvetica", "", 8)
    for num, name, purpose, status in summaries:
        pdf.cell(col_w[0], 7, num, border=1)
        pdf.cell(col_w[1], 7, name, border=1)
        pdf.cell(col_w[2], 7, purpose, border=1)
        pdf.cell(col_w[3], 7, status, border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)
    pdf.section_title("Cross-Cutting Infrastructure")
    pdf.bullet_list([
        "home/urls.py - All user-facing routes (namespace: home)",
        "p2p/urls.py - Root routing: admin, home app, Google OAuth",
        "p2p/settings.py - Auth, email, channels, OTP, Daily.co, Groq API keys",
        "p2p/asgi.py - HTTP + WebSocket ASGI application",
        "home/apps.py - Loads signals on application startup",
        "templates/base.html - Shared layout, navigation, notification WebSocket",
        "templates/404.html, 500.html - Custom error pages",
    ])

    for module in MODULES:
        pdf.add_page()
        pdf.section_title(module["title"])
        pdf.sub_heading("Purpose")
        pdf.body_text(module["purpose"])
        pdf.sub_heading("Models")
        pdf.bullet_list(module["models"])
        pdf.sub_heading("Views")
        pdf.bullet_list(module["views"])
        pdf.sub_heading("URLs")
        pdf.bullet_list(module["urls"])
        pdf.sub_heading("Templates")
        pdf.bullet_list(module["templates"])
        pdf.sub_heading("Other Key Files")
        pdf.bullet_list(module["other"])

    pdf.output(OUTPUT_FILE)
    print(f"PDF generated successfully: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_pdf()
