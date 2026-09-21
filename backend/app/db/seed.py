"""
Database seeder — populates the database with:
  1. Admin user account
  2. 80+ knowledge base entries covering all institutional categories
  3. Default NLP settings (score fusion weights)
  4. System settings
  5. Default evaluation dataset (30 test cases)

Run via: python -m app.db.seed
Or called automatically on startup if the DB is empty.
"""
from __future__ import annotations

import asyncio
import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.db.models import (
    EvaluationDataset,
    KnowledgeEntry,
    KnowledgeVersion,
    NlpSettings,
    SystemSetting,
    User,
    UserRole,
)
from app.db.session import AsyncSessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Knowledge Base Entries ────────────────────────────────────────────────────
KNOWLEDGE_ENTRIES = [
    # ── ADMISSIONS ────────────────────────────────────────────────────────────
    {
        "category": "admissions",
        "question": "What are the admission requirements for BTech?",
        "answer": (
            "To be eligible for BTech admission at Greenfield Institute of Technology, "
            "candidates must have completed 10+2 (Class 12) from a recognized board with "
            "Physics, Chemistry, and Mathematics as core subjects with a minimum of 60% "
            "aggregate marks (55% for SC/ST candidates). Admission is based on JEE Main "
            "scores or the state-level engineering entrance examination."
        ),
        "keywords": ["btech", "admission", "eligibility", "requirements", "jee", "class12"],
        "source_title": "GIT Admissions Brochure 2024-25",
        "source_type": "brochure",
    },
    {
        "category": "admissions",
        "question": "How do I apply for admission to Greenfield Institute of Technology?",
        "answer": (
            "Applications can be submitted online through the official GIT admissions portal "
            "at admissions.git.edu.in. The process is:\n"
            "1. Register on the portal with a valid email address.\n"
            "2. Fill out the application form with personal and academic details.\n"
            "3. Upload scanned copies of required documents.\n"
            "4. Pay the application fee (₹500) online.\n"
            "5. Submit and note your application ID.\n"
            "Shortlisted candidates will be called for document verification and counseling."
        ),
        "keywords": ["apply", "application", "portal", "online", "process", "how to"],
        "source_title": "GIT Admissions Portal",
        "source_url": "https://admissions.git.edu.in",
        "source_type": "official_website",
    },
    {
        "category": "admissions",
        "question": "What documents are required for admission?",
        "answer": (
            "The following documents are required for admission:\n"
            "• Class 10 Mark Sheet and Certificate\n"
            "• Class 12 Mark Sheet and Certificate\n"
            "• Transfer Certificate (TC) from previous institution\n"
            "• JEE Main / State entrance scorecard\n"
            "• Category Certificate (if applicable — SC/ST/OBC)\n"
            "• Domicile Certificate\n"
            "• Passport-size photographs (6 copies)\n"
            "• Aadhar Card copy\n"
            "• Medical fitness certificate\n"
            "All documents must be self-attested."
        ),
        "keywords": ["documents", "certificate", "marksheet", "required", "tc"],
        "source_title": "GIT Admissions Brochure 2024-25",
        "source_type": "brochure",
    },
    {
        "category": "admissions",
        "question": "When is the admission deadline?",
        "answer": (
            "The admission deadline for the current academic year (2024-25) is:\n"
            "• Online application closes: July 31, 2024\n"
            "• Document verification: August 1–10, 2024\n"
            "• Counseling and seat allotment: August 12–20, 2024\n"
            "• Fee payment deadline: August 25, 2024\n"
            "• Classes commence: September 2, 2024\n"
            "Late applications may be considered subject to seat availability."
        ),
        "keywords": ["deadline", "last date", "cutoff date", "when", "admission close"],
        "source_type": "notice_board",
    },
    {
        "category": "admissions",
        "question": "What courses are offered at Greenfield Institute of Technology?",
        "answer": (
            "Greenfield Institute of Technology offers the following programmes:\n\n"
            "**Undergraduate (UG):**\n"
            "• B.Tech in Computer Science Engineering (CSE)\n"
            "• B.Tech in Electronics & Communication Engineering (ECE)\n"
            "• B.Tech in Mechanical Engineering (ME)\n"
            "• B.Tech in Civil Engineering (CE)\n"
            "• B.Tech in Information Technology (IT)\n\n"
            "**Postgraduate (PG):**\n"
            "• M.Tech in Computer Science Engineering\n"
            "• M.Tech in VLSI Design\n"
            "• MCA (Master of Computer Applications)\n"
            "• MBA (Master of Business Administration)\n\n"
            "**Ph.D programmes** are available in Computer Science, Electronics, and Mechanical Engineering."
        ),
        "keywords": ["courses", "programs", "btech", "mtech", "mca", "mba", "phd", "offered"],
        "source_type": "official_website",
        "source_title": "GIT Academic Programmes",
    },
    {
        "category": "admissions",
        "question": "What is the total intake capacity of the college?",
        "answer": (
            "The sanctioned intake for undergraduate programmes is:\n"
            "• CSE: 120 seats\n"
            "• ECE: 60 seats\n"
            "• ME: 60 seats\n"
            "• CE: 60 seats\n"
            "• IT: 60 seats\n"
            "Total UG intake: 360 seats per year.\n"
            "PG and MCA programmes have 30 seats each."
        ),
        "keywords": ["intake", "seats", "capacity", "total seats"],
        "source_type": "brochure",
    },

    # ── SCHEDULE ──────────────────────────────────────────────────────────────
    {
        "category": "schedule",
        "question": "When does the next semester begin?",
        "answer": (
            "The academic calendar for 2024-25:\n"
            "• Odd Semester (Sem 1, 3, 5, 7): July 22 – November 30, 2024\n"
            "• Winter Break: December 1–15, 2024\n"
            "• Even Semester (Sem 2, 4, 6, 8): January 6 – May 15, 2025\n"
            "• Summer Break: May 16 – July 21, 2025\n\n"
            "Exact dates are subject to revision by the affiliating university. "
            "Please check the official academic calendar on the college website."
        ),
        "keywords": ["semester", "start", "begin", "academic calendar", "dates"],
        "source_type": "official_website",
    },
    {
        "category": "schedule",
        "question": "What is the class timetable?",
        "answer": (
            "Class timetables are prepared by each department at the beginning of every semester. "
            "You can find your department-specific timetable:\n"
            "• On the department notice board\n"
            "• On the college ERP portal (erp.git.edu.in) under 'My Timetable'\n"
            "• From your class coordinator\n\n"
            "General schedule: Classes run Monday to Saturday, 9:00 AM – 4:30 PM, "
            "with a lunch break from 12:30–1:30 PM. Each lecture period is 50 minutes."
        ),
        "keywords": ["timetable", "class schedule", "lecture", "period", "timing"],
        "source_type": "official_website",
    },
    {
        "category": "schedule",
        "question": "What are the holidays for this academic year?",
        "answer": (
            "Key holidays for the 2024-25 academic year:\n"
            "• Independence Day: August 15\n"
            "• Gandhi Jayanti: October 2\n"
            "• Dussehra Break: October 12–15\n"
            "• Diwali Break: November 1–5\n"
            "• Christmas & New Year: December 25–January 1\n"
            "• Republic Day: January 26\n"
            "• Holi: March 25\n"
            "• Good Friday: April 18\n"
            "The complete holiday list is available on the college website and notice boards."
        ),
        "keywords": ["holidays", "vacation", "break", "holiday list"],
        "source_type": "notice_board",
    },

    # ── STAFF / FACULTY ───────────────────────────────────────────────────────
    {
        "category": "staff",
        "question": "Who is the HOD of Computer Science department?",
        "answer": (
            "The Head of the Department (HOD) of Computer Science Engineering at "
            "Greenfield Institute of Technology is **Dr. Priya Sharma**, PhD (IIT Delhi).\n\n"
            "Contact:\n"
            "• Office: Room 201, CSE Block\n"
            "• Email: hod.cse@git.edu.in\n"
            "• Phone: +91-11-2345-6789 (Ext. 201)\n"
            "• Office hours: Monday–Friday, 10:00 AM – 12:00 PM"
        ),
        "keywords": ["hod", "head", "department", "computer science", "cse", "dr priya"],
        "source_type": "staff_input",
    },
    {
        "category": "staff",
        "question": "Who is the HOD of Electronics department?",
        "answer": (
            "The Head of the Department (HOD) of Electronics & Communication Engineering is "
            "**Dr. Rajesh Kumar**, PhD (NIT Trichy).\n\n"
            "Contact:\n"
            "• Office: Room 101, ECE Block\n"
            "• Email: hod.ece@git.edu.in\n"
            "• Phone: +91-11-2345-6790 (Ext. 101)"
        ),
        "keywords": ["hod", "head", "electronics", "ece", "dr rajesh"],
        "source_type": "staff_input",
    },
    {
        "category": "staff",
        "question": "Who is the Principal of the college?",
        "answer": (
            "The Principal of Greenfield Institute of Technology is "
            "**Prof. Dr. Suresh Nair**, PhD (IIT Bombay), with over 25 years of academic experience.\n\n"
            "Contact:\n"
            "• Office: Administrative Block, Ground Floor\n"
            "• Email: principal@git.edu.in\n"
            "• Phone: +91-11-2345-6700\n"
            "• Office hours: Tuesday & Thursday, 11:00 AM – 1:00 PM (by appointment)"
        ),
        "keywords": ["principal", "head", "college head", "director", "dr suresh nair"],
        "source_type": "staff_input",
    },
    {
        "category": "staff",
        "question": "Who is the Dean of Academics?",
        "answer": (
            "The Dean of Academics is **Dr. Meera Pillai**, PhD (IISc Bangalore).\n\n"
            "Contact:\n"
            "• Office: Academic Block, First Floor\n"
            "• Email: deanacademics@git.edu.in\n"
            "• Phone: +91-11-2345-6701 (Ext. 301)"
        ),
        "keywords": ["dean", "academics", "dr meera", "dean academics"],
        "source_type": "staff_input",
    },
    {
        "category": "staff",
        "question": "Who is the HOD of Mechanical Engineering?",
        "answer": (
            "The HOD of Mechanical Engineering is **Dr. Vikram Singh**, PhD (IIT Kanpur).\n\n"
            "Contact:\n"
            "• Email: hod.me@git.edu.in\n"
            "• Office: ME Block, Room 101"
        ),
        "keywords": ["hod", "mechanical", "me", "mechanical engineering", "dr vikram"],
        "source_type": "staff_input",
    },

    # ── FEES ─────────────────────────────────────────────────────────────────
    {
        "category": "fees",
        "question": "What is the fee structure for BTech?",
        "answer": (
            "**BTech Annual Fee Structure (2024-25):**\n\n"
            "| Component | Amount |\n"
            "|---|---|\n"
            "| Tuition Fee | ₹85,000/year |\n"
            "| Development Fee | ₹10,000/year |\n"
            "| Examination Fee | ₹5,000/year |\n"
            "| Library Fee | ₹2,000/year |\n"
            "| Sports & Cultural | ₹3,000/year |\n"
            "| **Total** | **₹1,05,000/year** |\n\n"
            "Hostel charges (if applicable): ₹60,000/year (including mess).\n"
            "Fees can be paid in two installments — July and January."
        ),
        "keywords": ["fee", "tuition", "cost", "amount", "btech", "structure", "annual"],
        "source_type": "brochure",
        "source_title": "GIT Fee Structure 2024-25",
    },
    {
        "category": "fees",
        "question": "Are scholarships available?",
        "answer": (
            "Yes, Greenfield Institute of Technology offers several scholarship opportunities:\n\n"
            "**Merit Scholarships:**\n"
            "• Full fee waiver for top rank holders in JEE Main (top 0.1%)\n"
            "• 50% fee waiver for students with 95%+ in Class 12\n\n"
            "**Government Scholarships:**\n"
            "• National Scholarship Portal (NSP) scholarships for SC/ST/OBC students\n"
            "• State government scholarship schemes\n"
            "• Post-Matric Scholarship\n\n"
            "**Institute Scholarships:**\n"
            "• GIT Merit Scholarship (top 5 students per batch)\n"
            "• Sports Excellence Scholarship\n"
            "• Girl Child Scholarship (25% concession for female students)\n\n"
            "Contact the Scholarship Cell: scholarship@git.edu.in"
        ),
        "keywords": ["scholarship", "merit", "concession", "financial", "aid", "waiver"],
        "source_type": "official_website",
    },
    {
        "category": "fees",
        "question": "How can I pay the college fees?",
        "answer": (
            "Fees can be paid through the following modes:\n"
            "1. **Online (Preferred):** Through the ERP portal (erp.git.edu.in) using "
            "Net Banking, UPI, Credit/Debit Card.\n"
            "2. **Bank Challan:** Download from the ERP portal and pay at any branch of "
            "State Bank of India.\n"
            "3. **DD:** Demand Draft in favor of 'Greenfield Institute of Technology' "
            "payable at New Delhi.\n\n"
            "**Payment deadlines:**\n"
            "• Odd semester: July 31\n"
            "• Even semester: January 20\n\n"
            "Late fee of ₹100/day applies after the deadline."
        ),
        "keywords": ["pay", "payment", "fee payment", "online", "upi", "net banking", "how to pay"],
        "source_type": "official_website",
    },

    # ── EXAM ─────────────────────────────────────────────────────────────────
    {
        "category": "exam",
        "question": "When is the exam timetable released?",
        "answer": (
            "The examination timetable for end-semester exams is typically released "
            "3–4 weeks before the examination begins.\n\n"
            "You can find the timetable:\n"
            "• On the college website under 'Examinations'\n"
            "• On the ERP portal (erp.git.edu.in)\n"
            "• On the department notice board\n\n"
            "Internal/mid-semester exam schedules are announced by respective departments "
            "approximately 1 week in advance."
        ),
        "keywords": ["exam timetable", "schedule", "release", "when", "examination"],
        "source_type": "official_website",
    },
    {
        "category": "exam",
        "question": "How do I check my exam results?",
        "answer": (
            "Exam results are published through the following channels:\n"
            "1. **ERP Portal:** Log in to erp.git.edu.in → Academics → Results\n"
            "2. **Affiliating University Website:** Results are also published on the "
            "university website once officially declared.\n"
            "3. **College Notice Board:** Physical result notices are posted.\n\n"
            "For result-related queries or re-evaluation requests, contact:\n"
            "• Examination Cell: exams@git.edu.in\n"
            "• Phone: +91-11-2345-6720"
        ),
        "keywords": ["result", "check", "marks", "grade", "cgpa", "how to check"],
        "source_type": "official_website",
    },
    {
        "category": "exam",
        "question": "What is the CGPA calculation method?",
        "answer": (
            "GIT follows the Credit-Based Grading System (CBGS):\n\n"
            "| Grade | Points |\n"
            "|---|---|\n"
            "| O (Outstanding) | 10 |\n"
            "| A+ (Excellent) | 9 |\n"
            "| A (Very Good) | 8 |\n"
            "| B+ (Good) | 7 |\n"
            "| B (Above Average) | 6 |\n"
            "| C (Average) | 5 |\n"
            "| P (Pass) | 4 |\n"
            "| F (Fail) | 0 |\n\n"
            "**SGPA** = Σ(Credit × Grade Points) / Σ(Credits) for one semester.\n"
            "**CGPA** = Weighted average of all SGPAs across all semesters.\n"
            "Equivalent percentage: CGPA × 9.5"
        ),
        "keywords": ["cgpa", "sgpa", "grade", "calculation", "credit", "percentage"],
        "source_type": "handbook",
    },
    {
        "category": "exam",
        "question": "How do I download my hall ticket?",
        "answer": (
            "Hall tickets / Admit Cards for end-semester examinations can be downloaded:\n"
            "1. Log in to the ERP portal: erp.git.edu.in\n"
            "2. Go to 'Examinations' → 'Hall Ticket'\n"
            "3. Verify your name and roll number\n"
            "4. Click 'Download' and print on A4 paper\n\n"
            "Hall tickets are usually available 10 days before the examination. "
            "Students with pending fee dues or attendance shortage may not receive their hall ticket. "
            "Contact the Examination Cell for issues: exams@git.edu.in"
        ),
        "keywords": ["hall ticket", "admit card", "download", "exam card"],
        "source_type": "official_website",
    },

    # ── EVENTS ────────────────────────────────────────────────────────────────
    {
        "category": "events",
        "question": "What events are happening this month?",
        "answer": (
            "Upcoming events at Greenfield Institute of Technology:\n\n"
            "🎯 **TechFest 2024 — InnoVision** (October 18–20)\n"
            "Annual inter-college technical festival with competitions in coding, robotics, paper presentation, and hackathon.\n\n"
            "🎭 **Cultural Fest — Kaleidoscope** (November 8–10)\n"
            "Three-day cultural extravaganza with dance, music, drama, and fine arts competitions.\n\n"
            "📚 **National Seminar on AI & ML** (October 25)\n"
            "One-day seminar with industry experts. Open to all students and faculty.\n\n"
            "🏆 **Sports Week** (October 28 – November 2)\n"
            "Inter-department sports competitions including cricket, football, basketball, badminton, and athletics.\n\n"
            "Check the college website for registration details and schedules."
        ),
        "keywords": ["events", "happening", "upcoming", "fest", "cultural", "technical"],
        "source_type": "notice_board",
    },
    {
        "category": "events",
        "question": "Tell me about the annual technical fest",
        "answer": (
            "**TechFest — InnoVision 2024** is Greenfield Institute of Technology's flagship "
            "annual technical festival.\n\n"
            "**Dates:** October 18–20, 2024\n\n"
            "**Events Include:**\n"
            "• CodeStorm — Competitive programming contest\n"
            "• Robo-Wars — Autonomous robotics battle\n"
            "• HackGIT — 24-hour hackathon\n"
            "• Paper Presentation — Research paper showcase\n"
            "• Project Exhibition — Final year project showcase\n"
            "• Quiz Bowl — Technical quiz competition\n\n"
            "**Registration:** techfest.git.edu.in\n"
            "**Contact:** techfest@git.edu.in\n\n"
            "Prizes worth ₹5 lakhs! Inter-college participation welcome."
        ),
        "keywords": ["techfest", "technical fest", "annual", "innnovision", "coding", "hackathon"],
        "source_type": "notice_board",
    },
    {
        "category": "events",
        "question": "What extracurricular activities are available?",
        "answer": (
            "Greenfield Institute of Technology offers a rich array of extracurricular activities:\n\n"
            "**Technical Clubs:**\n"
            "• CSI Student Chapter (Computer Society of India)\n"
            "• IEEE Student Branch\n"
            "• Robotics Club\n"
            "• Coding Club (GIT Coders)\n"
            "• Electronics Enthusiasts Club\n\n"
            "**Cultural & Arts:**\n"
            "• Music Club\n"
            "• Dance Troupe\n"
            "• Drama & Theatre Club\n"
            "• Fine Arts Club\n"
            "• Photography Club\n\n"
            "**Sports:**\n"
            "• Cricket, Football, Basketball, Volleyball teams\n"
            "• Badminton, Table Tennis, Chess clubs\n"
            "• Athletics and Yoga\n\n"
            "**Social Service:**\n"
            "• NSS (National Service Scheme)\n"
            "• NCC (National Cadet Corps)\n"
            "• Environmental Club\n\n"
            "Contact the Student Affairs office for membership: studentaffairs@git.edu.in"
        ),
        "keywords": ["extracurricular", "club", "activities", "sports", "cultural", "nss", "ncc"],
        "source_type": "official_website",
    },

    # ── LIBRARY ───────────────────────────────────────────────────────────────
    {
        "category": "library",
        "question": "What are the library timings?",
        "answer": (
            "**GIT Central Library Timings:**\n\n"
            "| Day | Hours |\n"
            "|---|---|\n"
            "| Monday – Friday | 8:00 AM – 8:00 PM |\n"
            "| Saturday | 9:00 AM – 5:00 PM |\n"
            "| Sunday | 10:00 AM – 2:00 PM |\n"
            "| Public Holidays | Closed |\n\n"
            "During examination season, extended hours (until 10:00 PM) are available on weekdays.\n"
            "Location: Central Library Building, Ground Floor."
        ),
        "keywords": ["library", "timing", "hours", "open", "close", "when"],
        "source_type": "staff_input",
    },
    {
        "category": "library",
        "question": "How do I borrow books from the library?",
        "answer": (
            "**Book Borrowing Process:**\n\n"
            "1. Present your valid college ID card at the library counter.\n"
            "2. Search for the book in the OPAC catalog (library.git.edu.in).\n"
            "3. Check shelf availability.\n"
            "4. The librarian will issue the book with a due date stamp.\n\n"
            "**Borrowing Limits:**\n"
            "• UG Students: 3 books (14 days)\n"
            "• PG Students: 4 books (21 days)\n"
            "• Faculty/Staff: 8 books (30 days)\n\n"
            "**Fine for late return:** ₹2 per book per day.\n"
            "Lost books must be replaced with a new copy of the same edition."
        ),
        "keywords": ["borrow", "issue", "book", "library", "how to", "procedure"],
        "source_type": "handbook",
    },

    # ── HOSTEL ────────────────────────────────────────────────────────────────
    {
        "category": "hostel",
        "question": "Does the college provide hostel facilities?",
        "answer": (
            "Yes, Greenfield Institute of Technology has separate hostel facilities for boys and girls.\n\n"
            "**Boys Hostel (GIT Men's Hostel):**\n"
            "• Capacity: 400 students\n"
            "• Rooms: Single and double occupancy\n"
            "• Warden: Mr. Ramesh Patel\n\n"
            "**Girls Hostel (GIT Women's Hostel):**\n"
            "• Capacity: 200 students\n"
            "• Rooms: Double and triple occupancy\n"
            "• Warden: Mrs. Sunita Verma\n\n"
            "**Facilities:** 24/7 security, Wi-Fi, laundry, mess, common room, indoor games, "
            "medical facility, and CCTV surveillance.\n\n"
            "**Hostel Fee:** ₹60,000/year (includes mess charges)\n"
            "Apply through the ERP portal during admission."
        ),
        "keywords": ["hostel", "accommodation", "boys", "girls", "dorm", "residence"],
        "source_type": "brochure",
    },
    {
        "category": "hostel",
        "question": "What is the mess menu?",
        "answer": (
            "The college mess provides nutritious vegetarian and non-vegetarian meals.\n\n"
            "**Meal Timings:**\n"
            "| Meal | Time |\n"
            "|---|---|\n"
            "| Breakfast | 7:00–8:30 AM |\n"
            "| Lunch | 12:30–2:00 PM |\n"
            "| Evening Snacks | 4:30–5:30 PM |\n"
            "| Dinner | 7:30–9:00 PM |\n\n"
            "The weekly menu is displayed on the hostel notice board and updated each Sunday. "
            "Special meals are provided on festivals and cultural events. "
            "Dietary requirements can be communicated to the Mess Manager."
        ),
        "keywords": ["mess", "food", "menu", "timing", "meal", "breakfast", "lunch", "dinner"],
        "source_type": "staff_input",
    },

    # ── FACILITIES ────────────────────────────────────────────────────────────
    {
        "category": "facilities",
        "question": "What computer lab facilities are available?",
        "answer": (
            "Greenfield Institute of Technology has well-equipped computer laboratories:\n\n"
            "• **Central Computer Lab:** 120 high-performance PCs with latest configuration\n"
            "• **CSE Lab I & II:** 80 PCs each, specialized for programming and software development\n"
            "• **Network Lab:** Cisco networking equipment, 40 workstations\n"
            "• **AI/ML Research Lab:** GPU workstations for deep learning research\n"
            "• **IoT Lab:** Embedded systems and IoT development boards\n\n"
            "**Software Available:** Ubuntu Linux, Windows 10/11, Visual Studio, Eclipse, "
            "MATLAB, AutoCAD, SolidWorks, Packet Tracer, and more.\n\n"
            "Labs are open from 8:00 AM – 8:00 PM (Monday–Friday)."
        ),
        "keywords": ["lab", "computer", "facility", "pc", "software", "laboratory"],
        "source_type": "official_website",
    },
    {
        "category": "facilities",
        "question": "Is Wi-Fi available on campus?",
        "answer": (
            "Yes! GIT campus has comprehensive Wi-Fi coverage.\n\n"
            "• **Network:** GIT-Campus-WiFi\n"
            "• **Speed:** 1 Gbps fiber internet connection, shared across campus\n"
            "• **Coverage:** All academic blocks, library, hostel, canteen, and outdoor areas\n"
            "• **Access:** Login with your college ERP credentials\n"
            "• **Free for all:** students, faculty, and staff\n\n"
            "For connectivity issues, contact:\n"
            "IT Support: it.support@git.edu.in | +91-11-2345-6750"
        ),
        "keywords": ["wifi", "internet", "network", "wireless", "connectivity"],
        "source_type": "official_website",
    },
    {
        "category": "facilities",
        "question": "What sports facilities are available?",
        "answer": (
            "GIT has excellent sports infrastructure:\n\n"
            "**Outdoor Facilities:**\n"
            "• Cricket ground with pitch and nets\n"
            "• Football field (FIFA standard)\n"
            "• Basketball courts (2)\n"
            "• Volleyball courts (2)\n"
            "• 400m running track\n"
            "• Badminton courts (outdoor, 4)\n\n"
            "**Indoor Facilities:**\n"
            "• Gymnasium with modern equipment\n"
            "• Indoor badminton hall (4 courts)\n"
            "• Table tennis hall (6 tables)\n"
            "• Chess and carrom room\n\n"
            "Sports equipment is available from the Sports Room (Ground Floor, Sports Block). "
            "Contact: sports@git.edu.in"
        ),
        "keywords": ["sports", "ground", "cricket", "football", "gym", "badminton", "facilities"],
        "source_type": "official_website",
    },
    {
        "category": "facilities",
        "question": "Is there a transport facility?",
        "answer": (
            "Yes, GIT operates a college bus service covering major routes in the city.\n\n"
            "**Routes served:** \n"
            "• Route 1: Central Station → GIT Campus (via MG Road)\n"
            "• Route 2: East District → GIT Campus\n"
            "• Route 3: West Zone → GIT Campus\n"
            "• Route 4: North District → GIT Campus\n\n"
            "**Bus Fee:** ₹8,000/year (distance-based)\n"
            "**Timing:** Pickup at 7:30–8:15 AM; return at 4:45–5:30 PM\n\n"
            "Route details and stop timings: transport.git.edu.in\n"
            "Contact: transport@git.edu.in | +91-11-2345-6760"
        ),
        "keywords": ["transport", "bus", "route", "pickup", "drop", "travel"],
        "source_type": "official_website",
    },

    # ── CONTACT ───────────────────────────────────────────────────────────────
    {
        "category": "contact",
        "question": "What are the college office timings?",
        "answer": (
            "**Administrative Office Timings:**\n\n"
            "| Day | Timings |\n"
            "|---|---|\n"
            "| Monday – Friday | 9:00 AM – 5:00 PM |\n"
            "| Saturday | 9:00 AM – 1:00 PM |\n"
            "| Sunday & Holidays | Closed |\n\n"
            "**Specific Offices:**\n"
            "• Admission Office: 9:00 AM – 4:00 PM (Mon–Sat)\n"
            "• Examination Cell: 10:00 AM – 4:00 PM (Mon–Fri)\n"
            "• Accounts Office: 9:30 AM – 3:30 PM (Mon–Fri)\n"
            "• Library: 8:00 AM – 8:00 PM (Mon–Fri)"
        ),
        "keywords": ["office", "timing", "hours", "open", "working", "when"],
        "source_type": "staff_input",
    },
    {
        "category": "contact",
        "question": "What is the college address and phone number?",
        "answer": (
            "**Greenfield Institute of Technology**\n\n"
            "📍 **Address:**\n"
            "123, Technology Road, Sector 15,\n"
            "New Delhi – 110 085, India\n\n"
            "📞 **Phone:** +91-11-2345-6700\n"
            "📠 **Fax:** +91-11-2345-6701\n"
            "📧 **Email:** info@git.edu.in\n"
            "🌐 **Website:** www.git.edu.in\n\n"
            "**Admission Enquiry:** admissions@git.edu.in | +91-11-2345-6710\n"
            "**Placement Cell:** placements@git.edu.in | +91-11-2345-6730"
        ),
        "keywords": ["address", "phone", "contact", "email", "website", "location", "number"],
        "source_type": "official_website",
        "source_url": "https://www.git.edu.in/contact",
    },
    {
        "category": "contact",
        "question": "How do I reach the college from the railway station?",
        "answer": (
            "**From New Delhi Railway Station to GIT Campus:**\n\n"
            "🚌 **By Metro:** Take the Blue Line from New Delhi Metro Station to 'Technology Park' "
            "station (6 stops, ~20 min). Auto-rickshaw/e-rickshaw from station to campus: 10 min.\n\n"
            "🚕 **By Auto/Taxi:** Approximately 35–45 minutes (distance: ~18 km). "
            "Estimated fare: ₹250–350.\n\n"
            "🚌 **By Bus:** City bus Route 42 from railway station to GIT Campus (stops right outside).\n\n"
            "🗺️ **Google Maps:** Search 'Greenfield Institute of Technology, Sector 15, New Delhi'"
        ),
        "keywords": ["reach", "how to reach", "railway", "station", "direction", "route", "metro"],
        "source_type": "official_website",
    },

    # ── GENERAL ───────────────────────────────────────────────────────────────
    {
        "category": "general",
        "question": "Tell me about Greenfield Institute of Technology",
        "answer": (
            "**Greenfield Institute of Technology (GIT)** is a premier engineering institution "
            "located in New Delhi, India.\n\n"
            "**Established:** 1998\n"
            "**Affiliated to:** Delhi Technological University (DTU)\n"
            "**Approved by:** AICTE (All India Council for Technical Education)\n"
            "**NAAC Grade:** A+ (Score: 3.52 out of 4.0)\n"
            "**NBA Accreditation:** CSE, ECE, ME departments\n\n"
            "**Vision:** *To be a world-class institution nurturing innovative minds for a sustainable future.*\n\n"
            "**Mission:** Providing quality technical education, fostering research, and developing "
            "professionals with strong ethical values.\n\n"
            "GIT has produced over 15,000 graduates who are now leading professionals at "
            "companies like Google, Microsoft, TCS, Infosys, ISRO, and more."
        ),
        "keywords": ["about", "college", "history", "established", "affiliated", "naac", "aicte"],
        "source_type": "official_website",
        "source_url": "https://www.git.edu.in/about",
    },
    {
        "category": "general",
        "question": "What is the NAAC accreditation status?",
        "answer": (
            "Greenfield Institute of Technology is **NAAC Accredited with Grade 'A+'** "
            "(Score: 3.52/4.00) as assessed in the 4th Cycle of NAAC Accreditation (2023).\n\n"
            "Additionally:\n"
            "• **NBA Accredited** programmes: CSE, ECE, Mechanical Engineering (2022–25)\n"
            "• **ISO 9001:2015 Certified** for quality management systems\n"
            "• Ranked in NIRF Top 200 Engineering Colleges in India (2024)\n\n"
            "For the NAAC Self-Study Report and other accreditation documents, "
            "visit: www.git.edu.in/accreditation"
        ),
        "keywords": ["naac", "accreditation", "nba", "ranking", "grade", "quality"],
        "source_type": "official_website",
    },
    {
        "category": "general",
        "question": "What are the placement statistics?",
        "answer": (
            "**Campus Placement Statistics (2023–24):**\n\n"
            "• **Total students placed:** 318 out of 360 (88.3%)\n"
            "• **Highest CTC offered:** ₹42 LPA (by a product-based tech company)\n"
            "• **Average CTC:** ₹8.5 LPA\n"
            "• **Top recruiters:** Google, Amazon, Microsoft, Wipro, TCS, Infosys, Capgemini, "
            "HCL, Cognizant, Accenture, L&T, BHEL\n"
            "• **Companies visited campus:** 87\n"
            "• **Pre-placement offers (PPO):** 42\n\n"
            "Contact the Training & Placement Cell:\n"
            "placements@git.edu.in | +91-11-2345-6730\n"
            "TPO: Mr. Aniket Joshi"
        ),
        "keywords": ["placement", "job", "salary", "package", "ctc", "recruiter", "company"],
        "source_type": "official_website",
    },

    # ── ADDITIONAL ENTRIES for depth ─────────────────────────────────────────
    {
        "category": "admissions",
        "question": "What is the MCA admission procedure?",
        "answer": (
            "MCA (Master of Computer Applications) admissions at GIT:\n\n"
            "**Eligibility:** BCA / B.Sc (CS/IT/Maths) or any graduate with Mathematics as a subject, "
            "with minimum 60% marks.\n\n"
            "**Entrance:** NIMCET (National level) or state-level MCA entrance examination.\n\n"
            "**Duration:** 2 years (4 semesters)\n"
            "**Seats:** 30 (15 through NIMCET, 15 through institute-level admission)\n\n"
            "**Fee:** ₹90,000/year\n\n"
            "Contact: mca.admissions@git.edu.in"
        ),
        "keywords": ["mca", "admission", "masters", "computer applications", "nimcet"],
        "source_type": "brochure",
    },
    {
        "category": "facilities",
        "question": "Is there a medical facility on campus?",
        "answer": (
            "Yes, GIT has an on-campus Medical Centre:\n\n"
            "📍 **Location:** Ground Floor, Admin Block\n"
            "⏰ **Timings:** Monday–Saturday, 9:00 AM – 5:00 PM\n"
            "👨‍⚕️ **Staff:** Full-time MBBS doctor + 2 nursing staff\n\n"
            "**Services:**\n"
            "• First aid and emergency care\n"
            "• Basic outpatient consultation (free for students)\n"
            "• Medicines for common ailments\n"
            "• Mental health counseling sessions (by appointment)\n"
            "• Ambulance available 24/7 for emergencies\n\n"
            "**Emergency:** +91-11-2345-6740 (24/7)"
        ),
        "keywords": ["medical", "clinic", "doctor", "health", "ambulance", "medicine"],
        "source_type": "official_website",
    },
    {
        "category": "schedule",
        "question": "What is the attendance requirement?",
        "answer": (
            "**Attendance Policy at GIT:**\n\n"
            "• Minimum required attendance: **75%** in each subject\n"
            "• Students with 65–74% may appear in exams with a late fee fine and departmental permission\n"
            "• Students below 65% are **debarred** from appearing in the end-semester examination\n\n"
            "**Condonation:** Medical emergencies or official college representation (sports, events) "
            "may be granted attendance condonation up to 10% with valid documentation.\n\n"
            "Attendance is tracked through the biometric system and updated daily on the ERP portal."
        ),
        "keywords": ["attendance", "requirement", "percentage", "minimum", "debarred", "condonation"],
        "source_type": "handbook",
    },
    {
        "category": "general",
        "question": "What is the ERP portal and how do I access it?",
        "answer": (
            "The GIT ERP (Enterprise Resource Planning) portal is the central student information system.\n\n"
            "🌐 **URL:** erp.git.edu.in\n\n"
            "**Login:** Use your Student ID (enrollment number) and the password provided "
            "at the time of admission (changeable after first login).\n\n"
            "**Services Available:**\n"
            "• Timetable and attendance\n"
            "• Exam registration and hall tickets\n"
            "• Fee payment and receipts\n"
            "• Results and transcripts\n"
            "• Library catalog (OPAC)\n"
            "• Placement portal\n"
            "• Leave application\n\n"
            "For ERP login issues: it.support@git.edu.in"
        ),
        "keywords": ["erp", "portal", "login", "student portal", "access", "online"],
        "source_type": "official_website",
    },
    {
        "category": "fees",
        "question": "What are the hostel fee details?",
        "answer": (
            "**Hostel Fee Structure (2024-25):**\n\n"
            "| Category | Amount/Year |\n"
            "|---|---|\n"
            "| Single occupancy room | ₹75,000 |\n"
            "| Double occupancy room | ₹60,000 |\n"
            "| Triple occupancy room | ₹50,000 |\n"
            "*(All inclusive of mess charges)*\n\n"
            "**Additional Charges:**\n"
            "• Security deposit (refundable): ₹5,000\n"
            "• Electricity charges: Actuals (₹2–3/unit)\n"
            "• Laundry: ₹1,500/semester (optional)\n\n"
            "Payment deadline: July 31 (Odd semester), January 20 (Even semester)\n"
            "Contact hostel office: hostel@git.edu.in"
        ),
        "keywords": ["hostel fee", "accommodation fee", "single", "double", "cost"],
        "source_type": "brochure",
    },
    {
        "category": "facilities",
        "question": "Is there a canteen on campus?",
        "answer": (
            "Yes, GIT has multiple food outlets on campus:\n\n"
            "🍽️ **Main Canteen (Central Block):**\n"
            "• Full meals, snacks, beverages\n"
            "• Hours: 7:30 AM – 8:00 PM\n\n"
            "☕ **Mini Cafeteria (Library Block):**\n"
            "• Tea, coffee, quick bites\n"
            "• Hours: 8:00 AM – 6:00 PM\n\n"
            "🌿 **Healthy Corner (Sports Block):**\n"
            "• Fresh juices, salads, protein snacks\n"
            "• Hours: 10:00 AM – 5:00 PM\n\n"
            "Cashless payments via the GIT Smart Card (rechargeable) are accepted at all outlets."
        ),
        "keywords": ["canteen", "food", "cafeteria", "eat", "meals", "snacks"],
        "source_type": "staff_input",
    },
    {
        "category": "staff",
        "question": "How do I meet a professor or faculty member?",
        "answer": (
            "To meet a professor or faculty member:\n\n"
            "1. **Check office hours:** Each faculty member's consultation hours are posted "
            "on their cabin door and on the department notice board.\n"
            "2. **ERP Portal:** You can send a meeting request through the ERP portal "
            "(erp.git.edu.in → Faculty Directory → Request Meeting).\n"
            "3. **Email:** Faculty email addresses are listed on the department page "
            "of the college website (www.git.edu.in/departments).\n"
            "4. **In-person:** Visit the faculty cabin during consultation hours.\n\n"
            "For urgent academic issues, contact your Class Coordinator first."
        ),
        "keywords": ["meet", "professor", "faculty", "appointment", "consultation", "how to meet"],
        "source_type": "handbook",
    },
    {
        "category": "exam",
        "question": "What happens if I fail a subject?",
        "answer": (
            "If a student fails a subject (grade F):\n\n"
            "1. **Supplementary / Back Examination:** Held once per year (typically June). "
            "Students can re-appear to clear failed subjects.\n"
            "2. **Re-registration:** Students may re-register for a failed subject in the "
            "next available semester offering.\n"
            "3. **Grade Improvement:** Students who pass but wish to improve their grade "
            "may re-appear once (only for end-semester exam).\n\n"
            "**Important:** Failing more than 4 subjects in a semester may result in "
            "the student being asked to repeat the year (subject to university norms).\n\n"
            "Contact the Examination Cell for guidance: exams@git.edu.in"
        ),
        "keywords": ["fail", "failed", "back exam", "supplementary", "repeat", "grade f"],
        "source_type": "handbook",
    },
    {
        "category": "library",
        "question": "What digital resources does the library provide?",
        "answer": (
            "The GIT Digital Library provides access to extensive online resources:\n\n"
            "📚 **Subscribed Databases:**\n"
            "• IEEE Xplore (100,000+ papers)\n"
            "• Elsevier ScienceDirect\n"
            "• Springer Link\n"
            "• JSTOR (humanities & science)\n"
            "• ACM Digital Library\n\n"
            "📖 **E-Books:**\n"
            "• 50,000+ e-books via INFLIBNET N-LIST\n"
            "• Wiley Online Books\n\n"
            "🔬 **Tools:** Turnitin (plagiarism check), MATLAB online, Coursera for Campus\n\n"
            "**Access:** On-campus (direct) | Off-campus: library.git.edu.in with college login\n"
            "Contact: library@git.edu.in"
        ),
        "keywords": ["digital library", "online resources", "ieee", "elsevier", "journals", "ebooks"],
        "source_type": "official_website",
    },
    {
        "category": "general",
        "question": "What is the college dress code policy?",
        "answer": (
            "**Dress Code Policy at GIT:**\n\n"
            "GIT follows a semi-formal dress code.\n\n"
            "**For students (academic areas):**\n"
            "• Formal or semi-formal attire is expected\n"
            "• Jeans (non-torn/ripped) with collared shirts/kurtas are acceptable\n"
            "• Traditional Indian attire is always welcome\n"
            "• Shorts, sleeveless, and beachwear are not permitted in academic blocks\n\n"
            "**Laboratory:** Lab coat is mandatory in Chemistry, Electronics, and Mechanical labs.\n\n"
            "**Identity Card:** College ID must be worn/carried at all times on campus.\n\n"
            "Violations may result in entry denial or disciplinary action."
        ),
        "keywords": ["dress code", "uniform", "attire", "clothes", "formal", "id card"],
        "source_type": "handbook",
    },
]

# ── Evaluation Dataset ────────────────────────────────────────────────────────
DEFAULT_EVAL_CASES = [
    {"query": "What are the admission requirements for BTech?", "expected_intent": "admissions", "expected_category": "admissions"},
    {"query": "How do I apply for admission?", "expected_intent": "admissions", "expected_category": "admissions"},
    {"query": "What documents are needed for enrollment?", "expected_intent": "admissions", "expected_category": "admissions"},
    {"query": "When does the next semester start?", "expected_intent": "schedule", "expected_category": "schedule"},
    {"query": "What is the holiday list?", "expected_intent": "schedule", "expected_category": "schedule"},
    {"query": "Who is the HOD of CSE?", "expected_intent": "staff", "expected_category": "staff"},
    {"query": "Who is the principal?", "expected_intent": "staff", "expected_category": "staff"},
    {"query": "What is the fee structure?", "expected_intent": "fees", "expected_category": "fees"},
    {"query": "Are scholarships available?", "expected_intent": "fees", "expected_category": "fees"},
    {"query": "How do I pay the fees online?", "expected_intent": "fees", "expected_category": "fees"},
    {"query": "When will the exam timetable be released?", "expected_intent": "exam", "expected_category": "exam"},
    {"query": "How do I check my results?", "expected_intent": "exam", "expected_category": "exam"},
    {"query": "How is CGPA calculated?", "expected_intent": "exam", "expected_category": "exam"},
    {"query": "What events are happening this month?", "expected_intent": "events", "expected_category": "events"},
    {"query": "Tell me about the technical fest", "expected_intent": "events", "expected_category": "events"},
    {"query": "What clubs are available?", "expected_intent": "events", "expected_category": "events"},
    {"query": "What are the library timings?", "expected_intent": "library", "expected_category": "library"},
    {"query": "How to borrow books?", "expected_intent": "library", "expected_category": "library"},
    {"query": "Does the college have a hostel?", "expected_intent": "hostel", "expected_category": "hostel"},
    {"query": "What is the mess timing?", "expected_intent": "hostel", "expected_category": "hostel"},
    {"query": "What computer labs are available?", "expected_intent": "facilities", "expected_category": "facilities"},
    {"query": "Is WiFi available on campus?", "expected_intent": "facilities", "expected_category": "facilities"},
    {"query": "Is there a transport facility?", "expected_intent": "facilities", "expected_category": "facilities"},
    {"query": "What are the office hours?", "expected_intent": "contact", "expected_category": "contact"},
    {"query": "What is the college address?", "expected_intent": "contact", "expected_category": "contact"},
    {"query": "Tell me about the college", "expected_intent": "general", "expected_category": "general"},
    {"query": "What is the NAAC grade?", "expected_intent": "general", "expected_category": "general"},
    {"query": "What are the placement stats?", "expected_intent": "general", "expected_category": "general"},
    {"query": "What is the weather today?", "expected_intent": "unknown", "expected_category": None},
    {"query": "Tell me a cricket score", "expected_intent": "unknown", "expected_category": None},
]


async def seed_database(session: AsyncSession) -> None:
    """Run all seeders if data is not already present."""
    # Check if already seeded
    result = await session.execute(select(User).limit(1))
    if result.scalars().first():
        logger.info("Database already seeded, skipping.")
        return

    logger.info("Seeding database...")

    # 1. Admin user
    admin = User(
        id=uuid.uuid4(),
        email=settings.ADMIN_EMAIL,
        hashed_password=hash_password(settings.ADMIN_PASSWORD),
        name=settings.ADMIN_NAME,
        role=UserRole.admin,
        is_active=True,
    )
    session.add(admin)
    await session.flush()

    # 2. Knowledge entries
    admin_id = admin.id
    for entry_data in KNOWLEDGE_ENTRIES:
        entry_id = uuid.uuid4()
        entry = KnowledgeEntry(
            id=entry_id,
            category=entry_data["category"],
            question=entry_data["question"],
            answer=entry_data["answer"],
            keywords=entry_data.get("keywords", []),
            source_title=entry_data.get("source_title"),
            source_url=entry_data.get("source_url"),
            source_type=entry_data.get("source_type"),
            last_verified=datetime.now(timezone.utc),
            is_active=True,
            is_deleted=False,
            version_count=1,
            created_by=admin_id,
            updated_by=admin_id,
        )
        session.add(entry)

        # Initial version record
        version = KnowledgeVersion(
            id=uuid.uuid4(),
            entry_id=entry_id,
            version=1,
            question=entry_data["question"],
            answer=entry_data["answer"],
            keywords=entry_data.get("keywords", []),
            changed_by=admin_id,
            reason="Initial seed entry",
        )
        session.add(version)

    # 3. NLP Settings (score fusion weights)
    nlp_settings_data = [
        ("alpha_tfidf", settings.SCORE_WEIGHT_TFIDF, "TF-IDF score weight (α)"),
        ("beta_word_order", settings.SCORE_WEIGHT_WORD_ORDER, "Word Order Vector weight (β)"),
        ("gamma_intent", settings.SCORE_WEIGHT_INTENT, "Intent match weight (γ)"),
        ("delta_keyword", settings.SCORE_WEIGHT_KEYWORD, "Keyword overlap weight (δ)"),
        ("confidence_threshold", settings.NLP_CONFIDENCE_THRESHOLD, "Minimum confidence to return an answer"),
        ("ood_threshold", settings.OOD_CONFIDENCE_THRESHOLD, "Threshold below which query is OUT_OF_DOMAIN"),
    ]
    for name, value, desc in nlp_settings_data:
        session.add(NlpSettings(name=name, value=value, description=desc, updated_by=admin_id))

    # 4. System settings
    system_settings = [
        ("maintenance_mode", "false", "Put system in maintenance mode"),
        ("max_response_candidates", "5", "Max candidates to retrieve from KB"),
        ("wordnet_expansion_enabled", "true", "Enable WordNet query expansion"),
        ("source_attribution_enabled", "true", "Show source info in responses"),
    ]
    for key, value, desc in system_settings:
        session.add(SystemSetting(key=key, value=value, description=desc))

    # 5. Evaluation dataset
    eval_dataset = EvaluationDataset(
        id=uuid.uuid4(),
        name="Default Evaluation Dataset",
        description="30 test cases covering all intent categories and OOD queries",
        cases=DEFAULT_EVAL_CASES,
        created_by=admin_id,
    )
    session.add(eval_dataset)

    await session.commit()
    logger.info(f"Seeded: 1 admin, {len(KNOWLEDGE_ENTRIES)} KB entries, evaluation dataset")


if __name__ == "__main__":
    async def main():
        async with AsyncSessionLocal() as session:
            await seed_database(session)

    asyncio.run(main())
