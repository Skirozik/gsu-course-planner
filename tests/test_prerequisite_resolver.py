"""
Test Prerequisite Resolver

Tests the prerequisite resolution layer with various prerequisite formats
and student transcript scenarios.
"""

from utils.prerequisite_resolver import PrerequisiteResolver, check_course_eligibility


def test_simple_prerequisite():
    """Test: CSC 1301 with a C or higher"""
    print("=" * 70)
    print("TEST 1: Simple Prerequisite")
    print("=" * 70)

    prereq_text = "CSC 1301 with a C or higher"
    resolver = PrerequisiteResolver()

    # Parse
    groups = resolver.parse_prerequisites(prereq_text)
    print(f"\nPrerequisite text: {prereq_text}")
    print(f"Parsed groups: {groups}")

    # Test Case 1: Student has CSC 1301 with B
    completed = [
        {"course_code": "CSC 1301", "grade": "B"}
    ]
    result = resolver.evaluate_eligibility(prereq_text, completed)
    print(f"\nStudent has CSC 1301 with B:")
    print(f"  Eligible: {result['eligible']}")
    print(f"  Reason: {result['reason']}")
    assert result['eligible'] == True

    # Test Case 2: Student has CSC 1301 with D
    completed = [
        {"course_code": "CSC 1301", "grade": "D"}
    ]
    result = resolver.evaluate_eligibility(prereq_text, completed)
    print(f"\nStudent has CSC 1301 with D:")
    print(f"  Eligible: {result['eligible']}")
    print(f"  Reason: {result['reason']}")
    assert result['eligible'] == False

    # Test Case 3: Student hasn't taken CSC 1301
    completed = []
    result = resolver.evaluate_eligibility(prereq_text, completed)
    print(f"\nStudent hasn't taken CSC 1301:")
    print(f"  Eligible: {result['eligible']}")
    print(f"  Reason: {result['reason']}")
    assert result['eligible'] == False

    print("\n✅ TEST 1 PASSED\n")


def test_or_prerequisite():
    """Test: (CSC 2720 or DSCI 2720) with a C or higher"""
    print("=" * 70)
    print("TEST 2: OR Prerequisite")
    print("=" * 70)

    prereq_text = "(CSC 2720 or DSCI 2720) with a C or higher"
    resolver = PrerequisiteResolver()

    groups = resolver.parse_prerequisites(prereq_text)
    print(f"\nPrerequisite text: {prereq_text}")
    print(f"Parsed groups: {groups}")

    # Test Case 1: Student has CSC 2720 with B
    completed = [
        {"course_code": "CSC 2720", "grade": "B"}
    ]
    result = resolver.evaluate_eligibility(prereq_text, completed)
    print(f"\nStudent has CSC 2720 with B:")
    print(f"  Eligible: {result['eligible']}")
    print(f"  Reason: {result['reason']}")
    assert result['eligible'] == True

    # Test Case 2: Student has DSCI 2720 with A
    completed = [
        {"course_code": "DSCI 2720", "grade": "A"}
    ]
    result = resolver.evaluate_eligibility(prereq_text, completed)
    print(f"\nStudent has DSCI 2720 with A:")
    print(f"  Eligible: {result['eligible']}")
    print(f"  Reason: {result['reason']}")
    assert result['eligible'] == True

    # Test Case 3: Student has neither
    completed = []
    result = resolver.evaluate_eligibility(prereq_text, completed)
    print(f"\nStudent has neither:")
    print(f"  Eligible: {result['eligible']}")
    print(f"  Reason: {result['reason']}")
    assert result['eligible'] == False

    print("\n✅ TEST 2 PASSED\n")


def test_complex_prerequisite():
    """Test: (CSC 2720 or DSCI 2720) and either MATH 3020 or MATH 3030 with a C or higher"""
    print("=" * 70)
    print("TEST 3: Complex AND/OR Prerequisite")
    print("=" * 70)

    prereq_text = "(CSC 2720 or DSCI 2720) and either MATH 3020 or MATH 3030 with a C or higher"
    resolver = PrerequisiteResolver()

    groups = resolver.parse_prerequisites(prereq_text)
    print(f"\nPrerequisite text: {prereq_text}")
    print(f"Parsed groups: {groups}")

    # Test Case 1: Student has CSC 2720 and MATH 3020
    completed = [
        {"course_code": "CSC 2720", "grade": "B"},
        {"course_code": "MATH 3020", "grade": "A"}
    ]
    result = resolver.evaluate_eligibility(prereq_text, completed)
    print(f"\nStudent has CSC 2720 (B) and MATH 3020 (A):")
    print(f"  Eligible: {result['eligible']}")
    print(f"  Reason: {result['reason']}")
    assert result['eligible'] == True

    # Test Case 2: Student has DSCI 2720 and MATH 3030
    completed = [
        {"course_code": "DSCI 2720", "grade": "C"},
        {"course_code": "MATH 3030", "grade": "B"}
    ]
    result = resolver.evaluate_eligibility(prereq_text, completed)
    print(f"\nStudent has DSCI 2720 (C) and MATH 3030 (B):")
    print(f"  Eligible: {result['eligible']}")
    print(f"  Reason: {result['reason']}")
    assert result['eligible'] == True

    # Test Case 3: Student has CSC 2720 but no math
    completed = [
        {"course_code": "CSC 2720", "grade": "B"}
    ]
    result = resolver.evaluate_eligibility(prereq_text, completed)
    print(f"\nStudent has CSC 2720 but no math:")
    print(f"  Eligible: {result['eligible']}")
    print(f"  Reason: {result['reason']}")
    assert result['eligible'] == False

    # Test Case 4: Student has MATH 3020 but no CSC/DSCI
    completed = [
        {"course_code": "MATH 3020", "grade": "A"}
    ]
    result = resolver.evaluate_eligibility(prereq_text, completed)
    print(f"\nStudent has MATH 3020 but no CSC/DSCI:")
    print(f"  Eligible: {result['eligible']}")
    print(f"  Reason: {result['reason']}")
    assert result['eligible'] == False

    print("\n✅ TEST 3 PASSED\n")


def test_multiple_and_prerequisites():
    """Test: CSC 2720, CSC 3210, and CSC 3320 with a C or higher"""
    print("=" * 70)
    print("TEST 4: Multiple AND Prerequisites")
    print("=" * 70)

    prereq_text = "CSC 2720, CSC 3210, and CSC 3320 with a C or higher"
    resolver = PrerequisiteResolver()

    groups = resolver.parse_prerequisites(prereq_text)
    print(f"\nPrerequisite text: {prereq_text}")
    print(f"Parsed groups: {groups}")

    # Test Case 1: Student has all three
    completed = [
        {"course_code": "CSC 2720", "grade": "B"},
        {"course_code": "CSC 3210", "grade": "A"},
        {"course_code": "CSC 3320", "grade": "C"}
    ]
    result = resolver.evaluate_eligibility(prereq_text, completed)
    print(f"\nStudent has all three courses:")
    print(f"  Eligible: {result['eligible']}")
    print(f"  Reason: {result['reason']}")
    assert result['eligible'] == True

    # Test Case 2: Student missing one course
    completed = [
        {"course_code": "CSC 2720", "grade": "B"},
        {"course_code": "CSC 3210", "grade": "A"}
    ]
    result = resolver.evaluate_eligibility(prereq_text, completed)
    print(f"\nStudent missing CSC 3320:")
    print(f"  Eligible: {result['eligible']}")
    print(f"  Reason: {result['reason']}")
    assert result['eligible'] == False

    print("\n✅ TEST 4 PASSED\n")


def test_in_progress_courses():
    """In-progress courses DO satisfy prerequisites for the next semester.

    The app plans the semester *after* the current one, so a course in progress
    will be finished by then, and Banner permits registering on an in-progress
    prerequisite. The plan is therefore contingent on the student passing.
    """
    print("=" * 70)
    print("TEST 5: In-Progress Courses")
    print("=" * 70)

    prereq_text = "CSC 1301 with a C or higher"
    resolver = PrerequisiteResolver()

    # Test Case: Student is currently taking CSC 1301
    completed = []
    in_progress = ["CSC 1301"]
    result = resolver.evaluate_eligibility(prereq_text, completed, in_progress)
    print(f"\nStudent currently taking CSC 1301:")
    print(f"  Eligible: {result['eligible']}")
    print(f"  Reason: {result['reason']}")
    assert result['eligible'] == True

    # But a finished attempt below the minimum still does not satisfy it.
    below = resolver.evaluate_eligibility(
        prereq_text, [{"course_code": "CSC 1301", "grade": "D"}], []
    )
    assert below['eligible'] == False

    # A retake: failed once, currently enrolled again. The in-progress attempt
    # supersedes the earlier grade rather than being shadowed by it.
    retake = resolver.evaluate_eligibility(
        prereq_text, [{"course_code": "CSC 1301", "grade": "D"}], ["CSC 1301"]
    )
    assert retake['eligible'] == True

    print("\n✅ TEST 5 PASSED\n")


def test_real_world_examples():
    """Test with actual prerequisites from GSU catalog"""
    print("=" * 70)
    print("TEST 6: Real World Examples from GSU Catalog")
    print("=" * 70)

    resolver = PrerequisiteResolver()

    # Example 1: CSC 3210 from catalog
    prereq_text = "CSC 1302, and CSC 2510 or MATH 2420 with a C or higher. Students must meet the Computer Science Major Eligibility"
    print(f"\nExample 1: CSC 3210")
    print(f"Prerequisite: {prereq_text}")

    groups = resolver.parse_prerequisites(prereq_text)
    print(f"Parsed: {groups}")

    completed = [
        {"course_code": "CSC 1302", "grade": "B"},
        {"course_code": "MATH 2420", "grade": "A"}
    ]
    result = resolver.evaluate_eligibility(prereq_text, completed)
    print(f"Student has CSC 1302 (B) and MATH 2420 (A):")
    print(f"  Eligible: {result['eligible']}")
    print(f"  Reason: {result['reason']}")

    # Example 2: CSC 4320 from catalog
    prereq_text = "CSC 3320 with grade of C or higher. Students must meet the Computer Science Major Eligibility"
    print(f"\nExample 2: CSC 4320")
    print(f"Prerequisite: {prereq_text}")

    groups = resolver.parse_prerequisites(prereq_text)
    print(f"Parsed: {groups}")

    completed = [
        {"course_code": "CSC 3320", "grade": "B"}
    ]
    result = resolver.evaluate_eligibility(prereq_text, completed)
    print(f"Student has CSC 3320 (B):")
    print(f"  Eligible: {result['eligible']}")
    print(f"  Reason: {result['reason']}")

    print("\n✅ TEST 6 PASSED\n")


def main():
    print("\n" + "=" * 70)
    print("PREREQUISITE RESOLVER TEST SUITE")
    print("=" * 70 + "\n")

    try:
        test_simple_prerequisite()
        test_or_prerequisite()
        test_complex_prerequisite()
        test_multiple_and_prerequisites()
        test_in_progress_courses()
        test_real_world_examples()

        print("=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
