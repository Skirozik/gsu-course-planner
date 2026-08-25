"""
LLM Integration Module
Handles communication with the Anthropic Claude API for course recommendations
Designed for reliability and multi-environment support (local + Streamlit Cloud)
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

from anthropic import Anthropic, APIError, AuthenticationError, RateLimitError

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
        Get the Anthropic API key from available sources
        Priority: Streamlit secrets > Environment variables > .env file

        Returns:
            API key string or None if not found
        """
        # Environment variable, set by the host dashboard or a local .env file.
        # A Streamlit-secrets branch used to sit above this and shadowed it: on a
        # machine with a secrets file but no ANTHROPIC_API_KEY in it, st.secrets.get
        # returned None and that None was returned directly, never reaching here.
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            return api_key

        logger.warning("⚠️ No Anthropic API key found")
        return None

    @staticmethod
    def validate_api_key(api_key: Optional[str]) -> Tuple[bool, str]:
        """
        Validate that an API key exists and has the correct format

        Returns:
            Tuple of (is_valid, message)
        """
        if not api_key:
            return False, "API key not found"

        # Anthropic keys are formatted like "sk-ant-...".
        if not api_key.startswith("sk-"):
            return False, "Invalid format. Anthropic keys start with 'sk-ant-'"

        if len(api_key) < 20:
            return False, "API key too short"

        return True, "Valid"


class CourseRecommender:
    """Generate course recommendations using Anthropic's Claude models"""

    DEFAULT_MODEL = "claude-sonnet-4-6"
    FALLBACK_MODEL = "claude-haiku-4-5-20251001"
    MAX_TOKENS = 1500
    TEMPERATURE = 0.7
    REQUEST_TIMEOUT = float(os.getenv("ANTHROPIC_TIMEOUT", "20"))
    SYSTEM_PROMPT = (
        "You are an academic advisor. Respond with valid JSON only — "
        "no prose, no explanations, and no markdown code fences."
    )

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize CourseRecommender with API key

        Args:
            api_key: Anthropic API key (if None, will attempt to retrieve automatically)

        Raises:
            ValueError: If API key cannot be found or is invalid
        """
        # Get API key
        self.api_key = api_key or APIKeyManager.get_api_key()

        # Validate API key
        is_valid, message = APIKeyManager.validate_api_key(self.api_key)
        if not is_valid:
            raise ValueError(f"Invalid API Key: {message}")

        # Initialize Anthropic client.
        # The SDK defaults to a 600s read timeout and 2 retries, and it retries
        # timeouts — so an unbounded call can occupy a request for 30 minutes.
        # generate_schedule also walks two models, so the wall clock is
        # timeout x (max_retries + 1) x 2. Budgeted to stay well inside that.
        try:
            self.client = Anthropic(
                api_key=self.api_key,
                timeout=self.REQUEST_TIMEOUT,
                max_retries=0,
            )
            logger.info("✅ Anthropic client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Anthropic client: {e}")
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
            logger.error(f"Anthropic error: {e}")
            return self._get_error_response(f"Anthropic error: {str(e)[:100]}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return self._get_error_response(f"Error: {str(e)[:100]}")

    def _call_api(self, prompt: str) -> Optional[str]:
        """Call the Claude API, falling back to a cheaper model on failure"""
        for model in [self.model, self.FALLBACK_MODEL]:
            try:
                logger.info(f"Trying {model}...")
                response = self.client.messages.create(
                    model=model,
                    max_tokens=self.MAX_TOKENS,
                    temperature=self.TEMPERATURE,
                    system=self.SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}],
                )
                logger.info(f"✅ Got response from {model}")
                # Claude returns a list of content blocks; concatenate any text blocks.
                return "".join(
                    block.text for block in response.content
                    if getattr(block, "type", None) == "text"
                )
            except (AuthenticationError, RateLimitError):
                # These are not recoverable by switching models; let the caller handle them.
                raise
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
- Credits: {student_data.get('total_credits', 0)}/{student_data.get('credits_required', 120)}
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

IMPORTANT: Use the EXACT course codes and course names from the AVAILABLE COURSES list above. Do NOT make up or guess course names.

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

        formatted = [f"- {c.get('course_code', '?')} - {c.get('course_name', 'Unknown')} ({c.get('credits', 3)} cr)" for c in courses[:15]]
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
        """Parse the Claude response and extract JSON"""
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
