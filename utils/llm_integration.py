"""
LLM Integration
Handles communication with OpenAI API for course recommendations
"""

import os
import streamlit as st
from openai import OpenAI
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class CourseRecommender:
    def __init__(self):
        """Initialize the OpenAI API client"""
        # Try to get API key from Streamlit secrets first (for Streamlit Cloud)
        api_key = None
        
        try:
            api_key = st.secrets["OPENAI_API_KEY"]
        except (KeyError, AttributeError):
            # Fall back to environment variables (for local development)
            api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in Streamlit secrets or environment variables")

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"
    
    def generate_schedule(
        self,
        student_data: Dict,
        preferences: Dict,
        available_courses: List[Dict],
        degree_requirements: Dict,
        allow_retakes: bool = False
    ) -> Dict:
        """
        Generate personalized course schedule using OpenAI
        
        Args:
            student_data: Parsed transcript data
            preferences: User preferences (major, career goals, etc.)
            available_courses: List of available courses for next semester
            degree_requirements: Required courses for the major
            allow_retakes: Whether to recommend retaking courses (default: False)
        
        Returns:
            Dictionary with:
            - recommended_courses: List of recommended courses
            - reasoning: Explanation for recommendations
            - alternatives: Backup course options
            - graduation_timeline: Estimated graduation date
        """
        
        # Build the prompt
        prompt = self._build_prompt(
            student_data,
            preferences,
            available_courses,
            degree_requirements,
            allow_retakes
        )
        
        # Call OpenAI API
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response
            recommendations = self._parse_response(response.choices[0].message.content)
            return recommendations

        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return self._get_fallback_response()
    
    def _build_prompt(
        self,
        student_data: Dict,
        preferences: Dict,
        available_courses: List[Dict],
        degree_requirements: Dict,
        allow_retakes: bool = False
    ) -> str:
        """
        Build the prompt for OpenAI with all necessary context
        """
        
        retake_instruction = ""
        if not allow_retakes:
            retake_instruction = """
IMPORTANT: DO NOT recommend retaking any courses the student has already completed.
Only recommend NEW courses that the student has not yet taken.
Focus on courses that satisfy degree requirements or prerequisites for future courses.
"""
        
        prompt = f"""You are an expert academic advisor for Georgia State University students.

STUDENT INFORMATION:
- Name: {student_data.get('student_name', 'Student')}
- Major: {preferences.get('major', 'Not specified')}
- GPA: {student_data.get('gpa', 'N/A')}
- Credits Completed: {student_data.get('total_credits', 0)} / 120

COMPLETED COURSES:
{self._format_completed_courses(student_data.get('completed_courses', []))}

STUDENT PREFERENCES:
- Career Goals: {preferences.get('career_goals', 'Not specified')}
- Has Job: {preferences.get('has_job', False)}
- Preferred Times: {preferences.get('preferred_times', ['No preference'])}
- Max Courses Per Semester: {preferences.get('max_courses', 4)}
- Learning Style: {preferences.get('learning_style', 'No preference')}
- Prioritize: {preferences.get('prioritize_courses', 'None')}
- Avoid: {preferences.get('avoid_courses', 'None')}

AVAILABLE COURSES FOR NEXT SEMESTER:
{self._format_available_courses(available_courses)}

DEGREE REQUIREMENTS:
{self._format_requirements(degree_requirements)}

{retake_instruction}

TASK:
Based on the above information, recommend up to {preferences.get('max_courses', 4)} courses for the student's next semester.

For each recommended course, provide:
1. Course code and name
2. Why this course is recommended
3. How it fits the student's preferences and goals
4. Difficulty level (Easy/Medium/Hard)
5. Prerequisites satisfied (if any)

Also provide:
- Overall schedule difficulty balance
- Estimated graduation timeline (semesters remaining)
- {max(1, preferences.get('max_courses', 4) // 2)} alternative courses in case recommendations are full

Format your response as JSON with this structure:
{{
    "recommended_courses": [
        {{
            "course_code": "CSC 4520",
            "course_name": "Design and Analysis of Algorithms",
            "reason": "...",
            "difficulty": "Medium",
            "prerequisites_met": true
        }}
    ],
    "reasoning": "Overall explanation...",
    "difficulty_balance": "Medium",
    "semesters_remaining": 3,
    "alternatives": [...]
}}
"""
        return prompt
    
    def _format_completed_courses(self, courses: List[Dict]) -> str:
        """Format completed courses for the prompt"""
        if not courses:
            return "No courses completed yet"
        
        formatted = []
        for course in courses[:20]:  # Limit to avoid token overflow
            formatted.append(f"- {course['course_code']}: {course['course_name']} (Grade: {course['grade']})")
        
        return "\n".join(formatted)
    
    def _format_available_courses(self, courses: List[Dict]) -> str:
        """Format available courses for the prompt"""
        if not courses:
            return "No courses with met prerequisites found."

        formatted = []
        for course in courses:
            prereqs = course.get('prerequisites', [])
            prereq_str = f" (Prerequisites: {', '.join(prereqs)})" if prereqs else ""
            formatted.append(f"- {course['course_code']}: {course.get('credits', 3)} credits{prereq_str}")

        return "\n".join(formatted)
    
    def _format_requirements(self, requirements: Dict) -> str:
        """Format degree requirements for the prompt"""
        if not requirements:
            return "No requirements data available"

        formatted = []

        # Format required courses
        if "required_courses" in requirements:
            formatted.append("COURSES STILL NEEDED:")
            for req in requirements["required_courses"]:
                if req.get("is_elective"):
                    formatted.append(f"- {req['credits']} credits of electives: {req['courses'][0]}")
                elif req.get("is_choice"):
                    formatted.append(f"- {req['credits']} credits: Choose from {' OR '.join(req['courses'])}")
                else:
                    formatted.append(f"- {req['courses'][0]} ({req['credits']} credits)")

        # Format summary if available
        if "summary" in requirements:
            summary = requirements["summary"]
            if summary.get("degree_name"):
                formatted.insert(0, f"DEGREE: {summary['degree_name']}")

        return "\n".join(formatted) if formatted else "No specific requirements found"
    
    def _parse_response(self, response_text: str) -> Dict:
        """
        Parse Claude's JSON response
        """
        import json
        
        try:
            # Try to extract JSON from response
            # Claude might wrap it in markdown code blocks
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            else:
                json_str = response_text
            
            return json.loads(json_str.strip())
        
        except:
            # If parsing fails, return the raw text
            return {
                "recommended_courses": [],
                "reasoning": response_text,
                "difficulty_balance": "Unknown",
                "semesters_remaining": "Unknown",
                "alternatives": []
            }
    
    def _get_fallback_response(self) -> Dict:
        """
        Fallback response if API call fails
        """
        return {
            "recommended_courses": [
                {
                    "course_code": "ERROR",
                    "course_name": "API Error - Please try again",
                    "reason": "Unable to connect to AI service",
                    "difficulty": "N/A",
                    "prerequisites_met": False
                }
            ],
            "reasoning": "There was an error generating recommendations. Please check your API key and try again.",
            "difficulty_balance": "Unknown",
            "semesters_remaining": "Unknown",
            "alternatives": []
        }


# Example usage
if __name__ == "__main__":
    # This would be called from the main app
    recommender = CourseRecommender()
    
    # Test with mock data
    student_data = {
        "student_name": "Test Student",
        "gpa": 3.5,
        "total_credits": 90,
        "completed_courses": [
            {"course_code": "CSC 1301", "course_name": "Intro to CS", "grade": "A", "credits": 3}
        ]
    }
    
    preferences = {
        "major": "Computer Science",
        "career_goals": "Software Engineering",
        "has_job": True,
        "max_courses": 4
    }
    
    # schedule = recommender.generate_schedule(student_data, preferences, [], {})
    # print(schedule)
