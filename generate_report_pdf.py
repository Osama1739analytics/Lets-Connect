from fpdf import FPDF

class ModulesReportPDF(FPDF):
    def header(self):
        # Arial bold 15
        self.set_font('Arial', 'B', 15)
        # Title
        self.cell(0, 10, 'Peer-2-Professional Guidance App - Modules Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

    def chapter_title(self, label):
        # Arial 12
        self.set_font('Arial', 'B', 12)
        # Background color
        self.set_fill_color(200, 220, 255)
        # Title
        self.cell(0, 10, label, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        # Times 12
        self.set_font('Times', '', 12)
        # Output justified text
        self.multi_cell(0, 10, body)
        self.ln()

def generate_pdf():
    pdf = ModulesReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Intro
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 10, "This report details the implementation status and core functionalities of the 9 working modules within the Peer-2-Professional (P2P) Guidance Platform. The application aims to facilitate seamless mentorship and professional networking.")
    pdf.ln(5)

    # Table Header
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(50, 10, 'Module Name', 1, 0, 'C', 1)
    pdf.cell(110, 10, 'Primary Functionality', 1, 0, 'C', 1)
    pdf.cell(30, 10, 'Status', 1, 1, 'C', 1)

    # Table Content
    modules = [
        ("User Auth & Profile", "OTP verification, Google OAuth, Profile Customization", "Implemented"),
        ("Session Management", "15-min rounding, Rs 500/15m pricing, Scheduling", "Implemented"),
        ("Smart Matching", "Tag-based relevance scoring, Mentor recommendations", "Implemented"),
        ("Google Meet", "Automated link generation, Personal link support", "Implemented"),
        ("Notifications", "In-app & email alerts for bookings/payments", "Implemented"),
        ("Live Chat", "WebSocket real-time messaging with AJAX fallback", "Implemented"),
        ("Payments", "Secure screenshot verification workflow", "Implemented"),
        ("Networking", "Connection requests, network hub management", "Implemented"),
        ("Feedback & Rating", "Verified 1-5 star reviews & recommendations", "Implemented"),
    ]

    pdf.set_font('Arial', '', 9)
    for name, func, status in modules:
        pdf.cell(50, 10, name, 1, 0, 'L')
        pdf.cell(110, 10, func, 1, 0, 'L')
        pdf.cell(30, 10, status, 1, 1, 'C')

    pdf.ln(10)

    # Detailed Sections
    details = {
        "1. User Authentication & Profile": "Features OTP-based email verification and Google OAuth2 integration. Users can create professional profiles as mentors or mentees, specifying skills, expertise, and availability.",
        "2. Session Management": "A robust booking system that rounds time-slots to 15-minute intervals. Sessions are priced at Rs. 500 per 15 minutes, with real-time availability tracking.",
        "3. Smart Matching Algorithm": "Uses a tag-based scoring system to match mentees with the most relevant mentors based on skills and interests.",
        "4. Google Meet Integration": "Automatically generates meeting links upon payment verification. Mentors can also provide persistent personal meeting links.",
        "5. Real-time Notifications": "Triggers automated alerts for session bookings, payment status changes, and connection requests.",
        "6. Live Chat System": "Powered by Django Channels for real-time messaging, with a robust AJAX polling fallback for consistent connectivity.",
        "7. Secure Payment Workflow": "A verification flow where mentees upload screenshots of transactions, which are then approved by mentors/admins.",
        "8. Professional Networking": "Allows users to send connection requests and build a professional network within the platform.",
        "9. Feedback & Rating System": "Enables mentees to rate mentors and provide public feedback after completed sessions to ensure quality and trust."
    }

    for title, text in details.items():
        pdf.chapter_title(title)
        pdf.chapter_body(text)

    pdf.output("P2P_Modules_Report.pdf")
    print("PDF generated successfully: P2P_Modules_Report.pdf")

if __name__ == "__main__":
    generate_pdf()
