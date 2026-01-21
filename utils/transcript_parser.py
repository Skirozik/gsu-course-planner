"""
Transcript Parser
Extracts course information from uploaded transcript files (PDF or TXT)
"""

import PyPDF2
import re
from typing import Dict, List


def parse_transcript(file_content: bytes, file_type: str) -> Dict:
    """
    Parse uploaded transcript file and extract course information
    
    Args:
        file_content: Raw file content as bytes
        file_type: 'pdf' or 'txt'
    
    Returns:
        Dictionary containing:
        - student_name: str
        - student_id: str
        - gpa: float
        - total_credits: int
        - completed_courses: List[Dict] with course_code, course_name, grade, credits
    """
    
    if file_type == 'pdf':
        return parse_pdf_transcript(file_content)
    elif file_type == 'txt':
        return parse_txt_transcript(file_content)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def parse_pdf_transcript(pdf_content: bytes) -> Dict:
    """
    Parse PDF transcript
    GSU transcript format (this needs to be customized based on actual format)
    """
    # TODO: Implement actual PDF parsing
    # This is a placeholder implementation
    
    return {
        "student_name": "Sample Student",
        "student_id": "001234567",
        "gpa": 3.5,
        "total_credits": 90,
        "completed_courses": [
            {
                "course_code": "CSC 1301",
                "course_name": "Intro to Computer Science",
                "grade": "A",
                "credits": 3,
                "semester": "Fall 2023"
            },
            {
                "course_code": "MATH 1111",
                "course_name": "College Algebra",
                "grade": "B",
                "credits": 3,
                "semester": "Fall 2023"
            },
            # More courses would be extracted here
        ]
    }


def parse_txt_transcript(txt_content: bytes) -> Dict:
    """
    Parse TXT transcript
    """
    # TODO: Implement actual TXT parsing
    # This is a placeholder implementation
    
    text = txt_content.decode('utf-8')
    
    return {
        "student_name": "Sample Student",
        "student_id": "001234567",
        "gpa": 3.5,
        "total_credits": 90,
        "completed_courses": [
            {
                "course_code": "CSC 1301",
                "course_name": "Intro to Computer Science",
                "grade": "A",
                "credits": 3,
                "semester": "Fall 2023"
            },
        ]
    }


def extract_course_codes(completed_courses: List[Dict]) -> List[str]:
    """
    Extract just the course codes from completed courses
    Useful for checking prerequisites
    """
    return [course['course_code'] for course in completed_courses]


def calculate_progress(completed_courses: List[Dict], total_required_credits: int = 120) -> float:
    """
    Calculate degree completion percentage
    """
    total_credits = sum(course.get('credits', 0) for course in completed_courses)
    return (total_credits / total_required_credits) * 100


# Example usage:
if __name__ == "__main__":
    # This would be called from the main app
    # with actual file content
    pass
