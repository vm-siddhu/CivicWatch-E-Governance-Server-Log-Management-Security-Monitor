import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    # 16:9 Widescreen
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Color Palette
    BG_DARK = RGBColor(28, 36, 64)       # #1C2440
    PRIMARY = RGBColor(99, 102, 241)     # #6366F1
    TEXT_DARK = RGBColor(30, 41, 59)     # #1E293B
    TEXT_MUTED = RGBColor(100, 116, 139) # #64748B
    CARD_BG = RGBColor(255, 255, 255)    # #FFFFFF
    CARD_BORDER = RGBColor(226, 232, 240)# #E2E8F0
    ACCENT_GREEN = RGBColor(16, 185, 129)# #10B981
    ACCENT_AMBER = RGBColor(245, 158, 11)# #F59E0B
    ACCENT_RED = RGBColor(239, 68, 68)   # #EF4444
    ACCENT_PURPLE = RGBColor(139, 92, 246)

    def add_header(slide, title_text, category_text="CIVICWATCH · COLLEGE PROJECT PRESENTATION"):
        # Category Eyebrow
        tb_cat = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(0.4))
        p_cat = tb_cat.text_frame.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = PRIMARY

        # Title
        tb_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(11.7), Inches(0.8))
        p_title = tb_title.text_frame.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(26)
        p_title.font.bold = True
        p_title.font.color.rgb = BG_DARK

    def add_card(slide, left, top, width, height, title, items, badge_color=PRIMARY):
        # Card shape
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = CARD_BG
        shape.line.color.rgb = CARD_BORDER
        shape.line.width = Pt(1)

        # Content
        tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.2), width - Inches(0.4), height - Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True

        p0 = tf.paragraphs[0]
        p0.text = title
        p0.font.size = Pt(16)
        p0.font.bold = True
        p0.font.color.rgb = badge_color
        p0.space_after = Pt(12)

        for item in items:
            p = tf.add_paragraph()
            p.text = f"•  {item}"
            p.font.size = Pt(13)
            p.font.color.rgb = TEXT_DARK
            p.space_after = Pt(8)

    # ==========================================
    # SLIDE 1: Title Slide (Dark Background)
    # ==========================================
    slide1 = prs.slides.add_slide(blank_layout)
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = BG_DARK
    bg1.line.fill.background()

    tb1 = slide1.shapes.add_textbox(Inches(1.2), Inches(1.8), Inches(11), Inches(4.5))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p = tf1.paragraphs[0]
    p.text = "🏛 E-GOVERNANCE INFRASTRUCTURE & MONITORING"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = PRIMARY
    p.space_after = Pt(14)

    p = tf1.add_paragraph()
    p.text = "CivicWatch"
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)

    p = tf1.add_paragraph()
    p.text = "Server Log Management & Threat Monitoring System"
    p.font.size = Pt(24)
    p.font.color.rgb = RGBColor(199, 210, 254)
    p.space_after = Pt(28)

    p = tf1.add_paragraph()
    p.text = "A Full-Stack College Project · React 18 SPA + Django REST Backend"
    p.font.size = Pt(15)
    p.font.color.rgb = RGBColor(148, 163, 184)
    p.space_after = Pt(6)

    p = tf1.add_paragraph()
    p.text = "Real-Time Telemetry · Automated Content Classification · Incident Alerting · RBAC"
    p.font.size = Pt(13)
    p.font.color.rgb = RGBColor(100, 116, 139)

    # ==========================================
    # SLIDE 2: Problem Statement & Objectives
    # ==========================================
    slide2 = prs.slides.add_slide(blank_layout)
    add_header(slide2, "Problem Statement & Project Objectives")

    add_card(slide2, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.9), "The Challenge in E-Governance", [
        "Multiple Public Portals: Student, exam, fee, and registry services run concurrently, producing high log volumes.",
        "Manual Review Bottlenecks: Identifying critical errors, database locks, and security exploits by hand is slow and reactive.",
        "Silent Security Exploits: Brute force login bursts and SQL injection attempts often go unnoticed until downtime occurs.",
        "Citizen & Student Privacy: External third-party AI APIs can leak sensitive citizen credentials and personal information."
    ], ACCENT_RED)

    add_card(slide2, Inches(6.8), Inches(1.8), Inches(5.6), Inches(4.9), "CivicWatch Core Objectives", [
        "Centralized Real-Time Logging: Collect and store server telemetry with IP addresses and status codes.",
        "Automated Content Classification: Locally analyze message keywords into INFO, WARNING, and ERROR tiers.",
        "Instant Incident Alerts: Automatically notify administrators upon critical outages and repeated auth failures.",
        "Search, Filter & Audit: Multi-criteria filtering by level and date with CSV exports for compliance.",
        "Simple Role-Based Access: Dedicated Administrator and Regular User access controls."
    ], PRIMARY)

    # ==========================================
    # SLIDE 3: System Architecture & Workflow
    # ==========================================
    slide3 = prs.slides.add_slide(blank_layout)
    add_header(slide3, "System Architecture & Request Workflow")

    add_card(slide3, Inches(0.8), Inches(1.8), Inches(3.6), Inches(4.9), "1. React Frontend (SPA)", [
        "React 18 & Vite: High performance, clean and minimal single page interface.",
        "Sidebar Navigation: Dashboard, All Logs, Notifications, and Settings.",
        "Interactive Charts: Visual log level breakdown and 7-day volume trends.",
        "Modal Views: Add Log form and detailed log event inspection."
    ], PRIMARY)

    add_card(slide3, Inches(4.8), Inches(1.8), Inches(3.6), Inches(4.9), "2. Django REST Backend", [
        "REST API Layer: Endpoints for auth, dashboard stats, logs, and alerts.",
        "Credential Redaction: Regex filters strip passwords, tokens, and Bearer keys.",
        "Local Rule Classifier: Heuristic pattern matcher deriving severity and category.",
        "Threshold Trigger Engine: Evaluates repeated failures to raise incident alerts."
    ], ACCENT_AMBER)

    add_card(slide3, Inches(8.8), Inches(1.8), Inches(3.6), Inches(4.9), "3. Storage & Alerts", [
        "SQLite Engine: Structured persistence in LogEntry, Alert, and AuditEvent models.",
        "In-App Incident Feed: Active vs resolved notification state management.",
        "Unified Serving: Django serves the production-compiled React SPA at / with zero hassle.",
        "Optional Ingestion API: Public services can push logs via POST /api/logs/ingest/."
    ], ACCENT_GREEN)

    # ==========================================
    # SLIDE 4: Automated Content Classification
    # ==========================================
    slide4 = prs.slides.add_slide(blank_layout)
    add_header(slide4, "Automated Content-Based Classification")

    add_card(slide4, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.9), "Classification Severity Levels", [
        "INFO (Normal Operations): User actions, successful logins, fee payment receipts, catalog updates (HTTP 200/201).",
        "WARNING (Potential Issues): Single failed logins, password retries, high memory, disk space threshold warnings.",
        "ERROR (Application Failures): Unhandled exceptions, 5xx server errors, gateway timeouts, network unreachable.",
        "CRITICAL (System Outages / Threats): Kernel panics, database connection pool exhaustion, SQL injections, brute force attacks."
    ], ACCENT_PURPLE)

    add_card(slide4, Inches(6.8), Inches(1.8), Inches(5.6), Inches(4.9), "How the Engine Operates", [
        "Keyword Pattern Matching: Inspects incoming messages against categorized heuristic dictionaries.",
        "HTTP Status Code Mapping: Status 500+ triggers ERROR; 401/403 triggers WARNING/SECURITY.",
        "Confidence & Reason Scoring: Assigns confidence estimates (e.g. 85%) and records matched rule reasons.",
        "Privacy-Preserving & Local: Operates entirely inside the server; zero log content sent to third parties.",
        "Audit Preservation: Administrators can override classifications while original predictions remain tracked."
    ], PRIMARY)

    # ==========================================
    # SLIDE 5: Key Functional Modules
    # ==========================================
    slide5 = prs.slides.add_slide(blank_layout)
    add_header(slide5, "Key Functional Modules & UI Features")

    add_card(slide5, Inches(0.8), Inches(1.8), Inches(5.6), Inches(2.35), "1. Dashboard Overview", [
        "4 Stat Cards: Total Logs, Info, Warnings, Errors/Critical.",
        "Visual Analytics: 7-day activity curve & level distribution.",
        "Recent activity stream with live incident notifications."
    ], PRIMARY)

    add_card(slide5, Inches(6.8), Inches(1.8), Inches(5.6), Inches(2.35), "2. All Logs Explorer", [
        "Multi-filter search: keyword, source app, log level, and dates.",
        "Color-coded badges highlighting critical errors in red.",
        "CSV export download and log detail inspection modal."
    ], ACCENT_GREEN)

    add_card(slide5, Inches(0.8), Inches(4.35), Inches(5.6), Inches(2.35), "3. Add New Log & Auto-Classify", [
        "Application selector with custom application support.",
        "Message input with 'Auto-classify based on content'.",
        "Instant classification toast & real-time DB storage."
    ], ACCENT_AMBER)

    add_card(slide5, Inches(6.8), Inches(4.35), Inches(5.6), Inches(2.35), "4. Notifications & Settings", [
        "Incident alerts with 'Mark as Resolved' workflow.",
        "Configurable brute-force alert threshold (e.g. 5 attempts).",
        "College demo tools: 'Quick Seed 10 Logs' & 'Reset DB'."
    ], ACCENT_RED)

    # ==========================================
    # SLIDE 6: Role-Based Access Control & Security
    # ==========================================
    slide6 = prs.slides.add_slide(blank_layout)
    add_header(slide6, "Role-Based Access Control (RBAC) & Security")

    add_card(slide6, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.9), "Two Distinct User Roles", [
        "Regular User (Auditor / Staff):",
        "  • Access the system monitoring dashboard and telemetry charts.",
        "  • Search and filter logs across all applications.",
        "  • Record and auto-classify new server events.",
        "  • View incident notifications.",
        "Administrator (Full Access):",
        "  • All regular user permissions.",
        "  • Permanently delete individual log entries.",
        "  • Acknowledge and resolve incident notifications.",
        "  • Modify anomaly detection thresholds & reset database."
    ], PRIMARY)

    add_card(slide6, Inches(6.8), Inches(1.8), Inches(5.6), Inches(4.9), "Security & Compliance Controls", [
        "Pre-Storage Credential Sanitization: Automatic regex replaces 'password', 'token', and 'secret' with [REDACTED].",
        "Brute Force Detection: Threshold tracking flags 5+ auth failures from the same IP within 10 minutes as a CRITICAL alert.",
        "Django Session Authentication: Secure session cookies with role badges (ADMIN / USER) displayed in the topbar.",
        "CORS & API Security: Configured for secure local Vite proxy and same-origin production requests."
    ], ACCENT_GREEN)

    # ==========================================
    # SLIDE 7: Technical Stack & Implementation
    # ==========================================
    slide7 = prs.slides.add_slide(blank_layout)
    add_header(slide7, "Technical Stack & Implementation")

    add_card(slide7, Inches(0.8), Inches(1.8), Inches(3.6), Inches(4.9), "Frontend Technology", [
        "React 18: Modern component-based single page application.",
        "Vite 5: Lightning fast development and build tool.",
        "Clean Minimal CSS: Custom responsive design without heavy bloat.",
        "SVG Visualizations: Lightweight area trend & donut charts."
    ], PRIMARY)

    add_card(slide7, Inches(4.8), Inches(1.8), Inches(3.6), Inches(4.9), "Backend Technology", [
        "Django 6.1: Robust, secure Python web framework.",
        "Django REST Framework: Clean RESTful endpoints.",
        "Python 3.11 / 3.14: Asynchronous & synchronous support.",
        "Custom Middleware: Request error interception & CORS."
    ], ACCENT_AMBER)

    add_card(slide7, Inches(8.8), Inches(1.8), Inches(3.6), Inches(4.9), "Standards & Compliance", [
        "AICTE Guidelines Aligned: System reliability, proactive issue resolution, and accountability.",
        "SQLite Storage: Simple, zero-configuration local database.",
        "Unified Deployment: Single command 'python manage.py runserver' serves both API and React frontend."
    ], ACCENT_GREEN)

    # ==========================================
    # SLIDE 8: Conclusion & Future Scope
    # ==========================================
    slide8 = prs.slides.add_slide(blank_layout)
    bg8 = slide8.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg8.fill.solid()
    bg8.fill.fore_color.rgb = BG_DARK
    bg8.line.fill.background()

    tb8 = slide8.shapes.add_textbox(Inches(1.2), Inches(1.2), Inches(11), Inches(5.2))
    tf8 = tb8.text_frame
    tf8.word_wrap = True

    p = tf8.paragraphs[0]
    p.text = "CONCLUSION & FUTURE ENHANCEMENTS"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = PRIMARY
    p.space_after = Pt(12)

    p = tf8.add_paragraph()
    p.text = "Project Summary"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.space_after = Pt(8)

    p = tf8.add_paragraph()
    p.text = "• Successfully built a full-stack server log management system for public e-governance platforms."
    p.font.size = Pt(14)
    p.font.color.rgb = RGBColor(203, 213, 225)
    p.space_after = Pt(6)

    p = tf8.add_paragraph()
    p.text = "• Achieved automated content classification (INFO, WARNING, ERROR, CRITICAL) without external API leaks."
    p.font.size = Pt(14)
    p.font.color.rgb = RGBColor(203, 213, 225)
    p.space_after = Pt(6)

    p = tf8.add_paragraph()
    p.text = "• Provided intuitive visual dashboards, multi-filter search, CSV reporting, and incident resolution."
    p.font.size = Pt(14)
    p.font.color.rgb = RGBColor(203, 213, 225)
    p.space_after = Pt(20)

    p = tf8.add_paragraph()
    p.text = "Future Scope"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.space_after = Pt(6)

    p = tf8.add_paragraph()
    p.text = "• Distributed background task workers with Celery & Redis for high-throughput government portals."
    p.font.size = Pt(13)
    p.font.color.rgb = RGBColor(148, 163, 184)
    p.space_after = Pt(4)

    p = tf8.add_paragraph()
    p.text = "• Machine Learning anomaly models for advanced threat prediction and Prometheus/Grafana metric exports."
    p.font.size = Pt(13)
    p.font.color.rgb = RGBColor(148, 163, 184)
    p.space_after = Pt(24)

    p = tf8.add_paragraph()
    p.text = "Thank You! Questions & Discussion."
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = PRIMARY

    output_path = r"D:\SEM-7\INT253\DjangoProject\CivicWatch_Project_Presentation.pptx"
    prs.save(output_path)
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    create_presentation()
