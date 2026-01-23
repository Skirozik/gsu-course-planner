"""
Export Utilities

Provides functions to export course schedules in various formats:
- PDF download
- iCalendar (.ics) for Google Calendar
- Plain text for clipboard
"""

from datetime import datetime, timedelta
from typing import List, Dict
import json
from io import BytesIO

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️  reportlab not installed. PDF export will not be available.")
    print("   Install with: pip install reportlab")


def generate_pdf_schedule(courses: List[Dict], student_info: Dict = None) -> BytesIO:
    """
    Generate a PDF of the course schedule

    Args:
        courses: List of course dicts with course_code, course_name, credits, etc.
        student_info: Optional dict with student name, major, semester

    Returns:
        BytesIO buffer containing PDF data
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab not installed. Cannot generate PDF.")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)

    # Container for document elements
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0039A6'),  # GSU Blue
        alignment=TA_CENTER,
        spaceAfter=12
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=20
    )

    # Title
    elements.append(Paragraph("📚 Course Schedule", title_style))

    # Student info
    if student_info:
        info_text = []
        if student_info.get('name'):
            info_text.append(f"Student: {student_info['name']}")
        if student_info.get('major'):
            info_text.append(f"Major: {student_info['major']}")
        if student_info.get('semester'):
            info_text.append(f"Semester: {student_info['semester']}")

        elements.append(Paragraph(" | ".join(info_text), subtitle_style))

    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", subtitle_style))
    elements.append(Spacer(1, 0.2*inch))

    # Course table
    if courses:
        # Table headers
        table_data = [['Course', 'Title', 'Credits', 'Professor', 'Rating']]

        total_credits = 0

        for course in courses:
            course_code = course.get('course_code', 'N/A')
            course_name = course.get('course_name', 'N/A')
            credits = course.get('credits', 3)
            professor = course.get('professor', 'TBA')

            # RMP data
            rmp_data = course.get('rmp_data')
            if rmp_data and rmp_data.get('rating'):
                rating = f"{rmp_data['rating']}/5.0"
            else:
                rating = "N/A"

            # Truncate long names
            if len(course_name) > 40:
                course_name = course_name[:37] + "..."

            table_data.append([
                course_code,
                course_name,
                str(credits),
                professor,
                rating
            ])

            total_credits += credits

        # Add total row
        table_data.append(['', '', f'Total: {total_credits}', '', ''])

        # Create table
        table = Table(table_data, colWidths=[1.2*inch, 3*inch, 0.8*inch, 1.5*inch, 1*inch])

        # Style table
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0039A6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            # Data rows
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),

            # Total row
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#D3D3D3')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),

            # Grid
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        elements.append(table)
    else:
        elements.append(Paragraph("No courses to display", styles['Normal']))

    # Footer
    elements.append(Spacer(1, 0.3*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    elements.append(Paragraph(
        "Generated by GSU Course Planner | Verify all information with official academic advisor",
        footer_style
    ))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_ics_calendar(courses: List[Dict], semester_start: datetime = None) -> str:
    """
    Generate iCalendar (.ics) file for importing into Google Calendar

    Args:
        courses: List of course dicts
        semester_start: Start date of semester (defaults to next Monday)

    Returns:
        String containing .ics file content
    """
    if semester_start is None:
        # Default to next Monday
        today = datetime.now()
        days_until_monday = (7 - today.weekday()) % 7
        semester_start = today + timedelta(days=days_until_monday if days_until_monday > 0 else 7)

    # Semester typically runs 15 weeks
    semester_end = semester_start + timedelta(weeks=15)

    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//GSU Course Planner//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:My Course Schedule",
        "X-WR-TIMEZONE:America/New_York",
    ]

    for course in courses:
        course_code = course.get('course_code', 'Unknown')
        course_name = course.get('course_name', 'Course')
        professor = course.get('professor', 'TBA')
        location = course.get('location', 'TBA')

        # Try to parse class times (if available)
        # For now, we'll create placeholder events
        # In a real implementation, you'd parse actual meeting times

        # Create a recurring event (placeholder - meets MW 10:00-11:15)
        # This would need to be customized based on actual course times

        event_id = f"{course_code.replace(' ', '')}-{semester_start.strftime('%Y%m%d')}"

        ics_content.extend([
            "BEGIN:VEVENT",
            f"UID:{event_id}@gsucourseplanner.com",
            f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART:{semester_start.strftime('%Y%m%dT100000')}",
            f"DTEND:{semester_start.strftime('%Y%m%dT111500')}",
            f"RRULE:FREQ=WEEKLY;UNTIL={semester_end.strftime('%Y%m%dT235959Z')};BYDAY=MO,WE",
            f"SUMMARY:{course_code} - {course_name}",
            f"DESCRIPTION:Professor: {professor}\\nCourse: {course_code}",
            f"LOCATION:{location}",
            "STATUS:CONFIRMED",
            "TRANSP:OPAQUE",
            "END:VEVENT",
        ])

    ics_content.append("END:VCALENDAR")

    return "\n".join(ics_content)


def generate_text_schedule(courses: List[Dict], student_info: Dict = None) -> str:
    """
    Generate plain text schedule for clipboard

    Args:
        courses: List of course dicts
        student_info: Optional student information

    Returns:
        Formatted text string
    """
    lines = []
    lines.append("=" * 70)
    lines.append("MY COURSE SCHEDULE")
    lines.append("=" * 70)
    lines.append("")

    if student_info:
        if student_info.get('major'):
            lines.append(f"Major: {student_info['major']}")
        if student_info.get('semester'):
            lines.append(f"Semester: {student_info['semester']}")
        lines.append("")

    lines.append(f"Generated: {datetime.now().strftime('%B %d, %Y')}")
    lines.append("")
    lines.append("-" * 70)

    total_credits = 0

    for i, course in enumerate(courses, 1):
        course_code = course.get('course_code', 'N/A')
        course_name = course.get('course_name', 'N/A')
        credits = course.get('credits', 3)
        professor = course.get('professor', 'TBA')

        lines.append(f"\n{i}. {course_code} - {course_name}")
        lines.append(f"   Credits: {credits}")
        lines.append(f"   Professor: {professor}")

        # RMP data
        rmp_data = course.get('rmp_data')
        if rmp_data:
            if rmp_data.get('rating'):
                lines.append(f"   Rating: {rmp_data['rating']}/5.0 ({rmp_data.get('num_ratings', 0)} reviews)")
            if rmp_data.get('difficulty'):
                lines.append(f"   Difficulty: {rmp_data['difficulty']}/5.0")
            if rmp_data.get('would_take_again'):
                lines.append(f"   Would Take Again: {rmp_data['would_take_again']}%")

        total_credits += credits

    lines.append("")
    lines.append("-" * 70)
    lines.append(f"TOTAL CREDITS: {total_credits}")
    lines.append("=" * 70)
    lines.append("")
    lines.append("Generated by GSU Course Planner")
    lines.append("Verify all information with official academic advisor")

    return "\n".join(lines)


def generate_json_export(courses: List[Dict], student_info: Dict = None) -> str:
    """
    Generate JSON export of schedule

    Args:
        courses: List of course dicts
        student_info: Optional student information

    Returns:
        JSON string
    """
    export_data = {
        "generated_at": datetime.now().isoformat(),
        "student_info": student_info or {},
        "courses": courses,
        "total_credits": sum(c.get('credits', 3) for c in courses)
    }

    return json.dumps(export_data, indent=2)


if __name__ == "__main__":
    # Demo
    sample_courses = [
        {
            "course_code": "CSC 3320",
            "course_name": "System Level Programming",
            "credits": 3,
            "professor": "John Smith",
            "rmp_data": {"rating": 4.2, "difficulty": 3.5, "num_ratings": 45, "would_take_again": 85}
        },
        {
            "course_code": "CSC 4520",
            "course_name": "Design and Analysis of Algorithms",
            "credits": 3,
            "professor": "Jane Doe",
            "rmp_data": {"rating": 3.8, "difficulty": 4.2, "num_ratings": 32, "would_take_again": 72}
        }
    ]

    student_info = {
        "name": "Test Student",
        "major": "Computer Science",
        "semester": "Spring 2026"
    }

    print("Text Export:")
    print(generate_text_schedule(sample_courses, student_info))
