"""
LLM Integration Module
Handles communication with OpenAI API for course recommendations
Redesigned for reliability and multi-environment support (local + Streamlit Cloud)
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Try to import streamlit, but don't fail if it's not available
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

from openai import OpenAI, APIError, AuthenticationError, RateLimitError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


class APIKeyManager:
    """Centralized API key management for local and cloud environments"""
    
    @staticmethod
    def get_api_key() -> Optional[str]:
        """
        Get OpenAI API key from available sources
        Priority: Streamlit secrets > Environment variables > .env file
        
        Returns:
            API key string or None if not found
        """
        # Try Streamlit secrets (for Streamlit Cloud)
        if HAS_STREAMLIT:
            try:
                return st.secrets.get("OPENAI_API_KEY")
            except (KeyError, AttributeError, FileNotFoundError):
                pass
        
        # Try environment variables (set via system or .env)
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            return api_key
        
        logger.warning("⚠️ No OpenAI API key found")
        return None
    
    @staticmethod
    def validate_api_key(api_key: Optional[str]) -> Tuple[bool, str]:
        """
        Validate that an API key exists and has correct format
        
        Returns:
            Tuple of (is_valid, message)
        """
        if not api_key:
            return False, "API key not found"
        
        if not api_key.startswith("sk-"):
            return False, "Invalid format. Should start with 'sk-'"
        
        if len(api_key) < 20:
            return False, "API key too short"
        
        return True, "Valid"


class CourseRecommender:
    """Generate course recommendations using OpenAI's GPT model"""
    
    DEFAULT_MODEL = "gpt-4o-mini"
    FALLBACK_MODEL = "gpt-3.5-turbo"
    MAX_TOKENS = 1500
    TEMPERATURE = 0.7
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize CourseRecommender with API key
        
        Args:
            api_key: OpenAI API key (if None, will attempt to retrieve automatically)
        
        Raises:
            ValueError: If API key cannot be found
        """
        # Get API key
        self.api_key = api_key or APIKeyManager.get_api_key()
        
        # Validate API key
        is_valid, message = APIKeyManager.validate_api_key(self.api_key)
        if not is_valid:
            raise ValueError(f"Invalid API Key: {message}")
        
        # Initialize OpenAI client
        try:
            self.client = OpenAI(api_key=self.api_key)
            logger.info("✅ OpenAI client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI: {e}")
            raise
        
        self.model = self.DEFAULT_MODEL
    
    def generate_schedule(
        self,
        student_data: Dict,
        preferences: Dict,
        available_courses: List[Dict],
        degree_requirements: Dict,
        allow_retakes: bool = False
    ) -> Dict:
        """
        Generate personalized course schedule recommendations
        
        Args:
            student_data: Student academic information
            preferences: Student preferences and constraints
            available_courses: List of courses student can take
            degree_requirements: Degree requirements structure
            allow_retakes: Whether to allow course retakes
        
        Returns:
            Dictionary with recommendations or fallback response
        """
        try:
            # Build prompt
            prompt = self._build_prompt(
                student_data,
                preferences,
                available_courses,
                degree_requirements,
                allow_retakes
            )
            
            if not prompt:
                logger.warning("Prompt generation failed")
                return self._get_error_response("Unable to generate recommendation prompt")
            
            # Call API
            response = self._call_api(prompt)
            
            if response:
                recommendations = self._parse_response(response)
                logger.info("✅ Generated recommendations")
                return recommendations
            else:
                return self._get_error_response("API call failed")
        
        except AuthenticationError:
            logger.error("Invalid API key")
            return self._get_error_response("Invalid API key. Check your credentials.")
        except RateLimitError:
            logger.error("Rate limit exceeded")
            return self._get_error_response("Rate limit reached. Try again later.")
        except APIError as e:
            logger.error(f"OpenAI error: {e}")
            return self._get_error_response(f"OpenAI error: {str(e)[:100]}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return self._get_error_response(f"Error: {str(e)[:100]}")
    
    def generate_course_explanation(
        self,
        course_code: str,
        course_name: str,
        student_data: Dict,
        preferences: Dict,
        available_courses: List[Dict],
        degree_requirements: Dict
    ) -> str:
        """
        Generate AI explanation for why a course was recommended

        Args:
            course_code: Course code (e.g., "CS 1332")
            course_name: Course name (e.g., "Data Structures")
            student_data: Student academic information
            preferences: Student preferences
            available_courses: List of available courses
            degree_requirements: Degree requirements

        Returns:
            Formatted explanation string (2-3 bullet points)
        """
        try:
            # Build explanation prompt
            prompt = self._build_explanation_prompt(
                course_code,
                course_name,
                student_data,
                preferences,
                available_courses,
                degree_requirements
            )

            if not prompt:
                return "Unable to generate explanation at this time."

            # Call API with shorter timeout for explanations
            response = self.client.chat.completions.create(
                model=self.DEFAULT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,  # Shorter for concise explanations
                temperature=0.5,  # Lower temperature for more focused responses
                timeout=15
            )

            explanation = response.choices[0].message.content.strip()
            logger.info(f"✅ Generated explanation for {course_code}")
            return explanation

        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return "Unable to generate explanation at this time. This course was recommended based on your academic progress and degree requirements."

    def _build_explanation_prompt(
        self,
        course_code: str,
        course_name: str,
        student_data: Dict,
        preferences: Dict,
        available_courses: List[Dict],
        degree_requirements: Dict
    ) -> Optional[str]:
        """Build prompt for course explanation"""
        try:
            # Find course info from available courses
            course_info = next(
                (c for c in available_courses if c.get('course_code') == course_code),
                None
            )

            # Get prerequisites from requirements
            required_courses = degree_requirements.get("required_courses", [])
            is_required = any(
                course_code in req.get("courses", [])
                for req in required_courses
            )

            # Format completed courses
            completed = [c.get('course_code', '') for c in student_data.get('completed_courses', [])]
            completed_str = ", ".join(completed[:10]) if completed else "None"

            prompt = f"""Explain in 2-3 concise bullet points why {course_code} ({course_name}) was recommended to this student.

STUDENT BACKGROUND:
- Completed courses: {completed_str}
- GPA: {student_data.get('gpa', 'N/A')}
- Credits earned: {student_data.get('total_credits', 0)}
- Major: {student_data.get('major', 'Computer Science')}

COURSE STATUS:
- Required course: {"Yes" if is_required else "No (elective)"}
- Credits: {course_info.get('credits', 3) if course_info else 3}

STUDENT PREFERENCES:
- Career goals: {preferences.get('career_goals', 'Not specified')}

Focus on:
1. Prerequisites the student has met that make them ready for this course
2. How this course fits into their degree requirements
3. What future courses or opportunities this unlocks

Keep it brief, specific, and helpful. Use bullet points starting with •."""

            return prompt

        except Exception as e:
            logger.error(f"Error building explanation prompt: {e}")
            return None

    def _call_api(self, prompt: str) -> Optional[str]:
        """Call OpenAI API with fallback model"""
        for model in [self.model, self.FALLBACK_MODEL]:
            try:
                logger.info(f"Trying {model}...")
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=self.MAX_TOKENS,
                    temperature=self.TEMPERATURE,
                    timeout=30
                )
                logger.info(f"✅ Got response from {model}")
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"{model} failed: {e}")
                continue
        
        return None
    
    def _build_prompt(
        self,
        student_data: Dict,
        preferences: Dict,
        available_courses: List[Dict],
        degree_requirements: Dict,
        allow_retakes: bool = False
    ) -> Optional[str]:
        """Build the recommendation prompt"""
        
        try:
            completed = self._format_completed_courses(student_data.get("completed_courses", []))
            available = self._format_available_courses(available_courses)
            reqs = self._format_requirements(degree_requirements)
            
            max_courses = preferences.get('max_courses', 4)
            
            prompt = f"""Academic Advisor - Recommend {max_courses} courses for next semester.

STUDENT:
- GPA: {student_data.get('gpa', 'N/A')}
- Credits: {student_data.get('total_credits', 0)}/120
- Completed: {completed}

PREFERENCES:
- Max Courses: {max_courses}
- Goals: {preferences.get('career_goals', 'N/A')}
- Working: {preferences.get('has_job', False)}

AVAILABLE COURSES (Prerequisites Met):
{available}

REQUIREMENTS:
{reqs}

{"⚠️ Only recommend NEW courses, not retakes." if not allow_retakes else ""}

Respond with JSON only:
{{
    "recommended_courses": [
        {{"course_code": "...", "course_name": "...", "reason": "...", "difficulty": "Easy/Medium/Hard"}}
    ],
    "reasoning": "Brief explanation",
    "difficulty_balance": "Light/Balanced/Challenging",
    "semesters_remaining": 3,
    "alternatives": []
}}"""
            
            return prompt
        except Exception as e:
            logger.error(f"Error building prompt: {e}")
            return None
    
    def _format_completed_courses(self, courses: List[Dict]) -> str:
        """Format completed courses"""
        if not courses:
            return "None"
        
        formatted = [f"{c.get('course_code', '?')}: {c.get('course_name', '?')}" for c in courses[:8]]
        return "; ".join(formatted) if formatted else "None"
    
    def _format_available_courses(self, courses: List[Dict]) -> str:
        """Format available courses"""
        if not courses:
            return "No courses available"
        
        formatted = [f"- {c.get('course_code', '?')} ({c.get('credits', 3)} cr)" for c in courses[:15]]
        return "\n".join(formatted) if formatted else "No courses"
    
    def _format_requirements(self, requirements: Dict) -> str:
        """Format degree requirements"""
        if not requirements:
            return "No requirements"
        
        formatted = []
        required = requirements.get("required_courses", [])
        
        if required:
            for req in required[:8]:
                code = req.get("courses", ["Unknown"])[0]
                creds = req.get("credits", 3)
                formatted.append(f"- {code} ({creds} cr)")
        
        return "\n".join(formatted) if formatted else "No requirements"
    
    def _parse_response(self, response_text: str) -> Dict:
        """Parse OpenAI response and extract JSON"""
        try:
            json_str = response_text
            
            # Remove markdown code blocks
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            
            data = json.loads(json_str.strip())
            
            # Validate structure
            if "recommended_courses" in data:
                logger.info("✅ Parsed response successfully")
                return data
            else:
                return self._get_error_response("Invalid response structure")
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON error: {e}")
            return self._get_error_response(f"Parse error: {str(e)[:50]}")
        except Exception as e:
            logger.error(f"Error: {e}")
            return self._get_error_response(str(e)[:50])
    
    def _get_error_response(self, error_msg: str = "Error") -> Dict:
        """Return error response"""
        return {
            "recommended_courses": [],
            "reasoning": f"❌ {error_msg}",
            "difficulty_balance": "N/A",
            "semesters_remaining": "N/A",
            "alternatives": []
        }


def get_course_recommender(api_key: Optional[str] = None) -> Optional[CourseRecommender]:
    """Factory function to safely create a recommender"""
    try:
        return CourseRecommender(api_key=api_key)
    except ValueError as e:
        logger.error(f"Cannot create recommender: {e}")
        return None
