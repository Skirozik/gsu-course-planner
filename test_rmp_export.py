"""
Test RMP Integration and Export Features

Quick test to verify Rate My Professor integration and export utilities work.
"""

print("=" * 70)
print("TESTING RMP INTEGRATION & EXPORT FEATURES")
print("=" * 70 + "\n")

# Test 1: RMP Integration
print("Test 1: Rate My Professor Integration")
print("-" * 70)

try:
    from utils.rmp_integration import get_rmp_api, format_rmp_display

    api = get_rmp_api()
    print("✅ RMP API initialized")

    # Test with a famous professor (Ashok Goel - AI professor at GT)
    test_prof = "Ashok Goel"
    print(f"\nSearching for: {test_prof}")

    rmp_data = api.get_professor_rating(test_prof, "Georgia Tech")

    if rmp_data:
        print(f"✅ Found: {rmp_data['name']}")
        print(f"   Department: {rmp_data['department']}")
        print(f"   {format_rmp_display(rmp_data)}")
    else:
        print(f"⚠️  Professor not found (this is okay - just means no data)")

    # Test enrichment function
    from utils.rmp_integration import enrich_courses_with_rmp

    test_courses = [
        {"course_code": "CSC 3320", "course_name": "System Programming", "professor": "Ashok Goel"},
        {"course_code": "CSC 4520", "course_name": "Algorithms", "professor": "Staff"}
    ]

    enriched = enrich_courses_with_rmp(test_courses, "Georgia State University")
    print(f"\n✅ Course enrichment works - enriched {len(enriched)} courses")

    print("\n✅ RMP Integration: PASSED")

except Exception as e:
    print(f"\n❌ RMP Integration: FAILED - {e}")
    import traceback
    traceback.print_exc()

print("\n")

# Test 2: Export Utilities
print("Test 2: Export Utilities")
print("-" * 70)

try:
    from utils.export_utils import generate_text_schedule, generate_ics_calendar

    sample_courses = [
        {
            "course_code": "CSC 3320",
            "course_name": "System Level Programming",
            "credits": 3,
            "professor": "John Smith",
            "rmp_data": {"rating": 4.2, "difficulty": 3.5, "num_ratings": 45}
        },
        {
            "course_code": "CSC 4520",
            "course_name": "Design and Analysis of Algorithms",
            "credits": 3,
            "professor": "Jane Doe",
            "rmp_data": {"rating": 3.8, "difficulty": 4.2, "num_ratings": 32}
        }
    ]

    student_info = {
        "name": "Test Student",
        "major": "Computer Science",
        "semester": "Spring 2026"
    }

    # Test text export
    text_output = generate_text_schedule(sample_courses, student_info)
    print("✅ Text export works")
    print(f"   Generated {len(text_output)} characters")

    # Test calendar export
    ics_output = generate_ics_calendar(sample_courses)
    print("✅ Calendar export works")
    print(f"   Generated {len(ics_output)} characters")

    # Test PDF export
    try:
        from utils.export_utils import generate_pdf_schedule
        pdf_buffer = generate_pdf_schedule(sample_courses, student_info)
        print("✅ PDF export works")
        print(f"   Generated {pdf_buffer.getbuffer().nbytes} bytes")
    except ImportError:
        print("⚠️  PDF export requires reportlab (install with: pip install reportlab)")

    print("\n✅ Export Utilities: PASSED")

except Exception as e:
    print(f"\n❌ Export Utilities: FAILED - {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("TESTING COMPLETE")
print("=" * 70)
print("\n✨ If you see checkmarks above, everything is working!")
print("\n📝 Note: Some professors may not have RMP data - this is normal.")
print("   The app will gracefully handle missing data.\n")
