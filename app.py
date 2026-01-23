import streamlit as st
import json
import os
from datetime import datetime

# Import our custom modules
from utils.academic_eval_parser import parse_academic_eval, get_next_semester_recommendations
from utils.prerequisites import (
    get_course_info, get_prerequisites, get_corequisites,
    get_all_prerequisites, check_prerequisites_met, get_courses_unlocked_by,
    search_courses, format_prerequisite_chain, get_all_cs_courses, get_all_math_courses,
    COURSE_DATABASE
)
from utils.catalog_loader import get_catalog_loader
from utils.rmp_integration import get_rmp_api, enrich_courses_with_rmp, format_rmp_display
from utils.export_utils import generate_pdf_schedule, generate_ics_calendar, generate_text_schedule
from utils.demo_professors import add_demo_professors
from utils.section_recommender import get_ranked_sections

# Cached PDF parsing to avoid re-parsing the same file multiple times
@st.cache_data
def parse_academic_eval_cached(file_content: bytes) -> dict:
    """
    Cached wrapper for parse_academic_eval to avoid re-parsing the same PDF.
    Uses file content as cache key.
    """
    return parse_academic_eval(file_content)


def generate_sample_sections(course_code: str, num_sections: int = 3) -> list:
    """
    Generate sample section data for a course

    In production, this would come from:
    - GSU course schedule scraper
    - PAWS/Banner API
    - Manual section database

    Args:
        course_code: Course code (e.g., "CSC 3320")
        num_sections: Number of sections to generate

    Returns:
        List of section dicts
    """
    from utils.demo_professors import DEMO_PROFESSORS
    import random
    import hashlib

    # Sample times and locations
    times = ["MWF 10:00-10:50", "TTh 2:00-3:15", "MW 6:00-7:15", "TTh 10:00-11:15"]
    locations = ["Classroom South 101", "Langdale Hall 200", "Online", "Library 305", "Science Building 201"]

    # Get primary professor from demo data
    primary_professor = DEMO_PROFESSORS.get(course_code, "Staff")

    # Create department-specific professor pools
    # Extract department code (e.g., "CSC" from "CSC 3320")
    dept = course_code.split()[0] if ' ' in course_code else course_code[:3]

    # Professor pools by department
    professor_pools = {
        "CSC": ["Robert Robinson", "Sarah Chen", "David Kim", "Emily Rodriguez", "Daniel Taylor"],
        "CIS": ["Andrew King", "Rebecca Wright", "Matthew Adams", "Michelle Scott", "Joshua Green"],
        "FI": ["Christina Edwards", "William Turner", "Gregory Campbell", "Rachel Parker"],
        "MGT": ["Jonathan Collins", "Timothy Evans", "Nicholas Morris", "Samantha Stewart"],
        "MK": ["Samantha Stewart", "Brandon Perez", "Victoria Roberts"],
        "ACCT": ["Victoria Roberts", "William Turner", "Lauren Nelson"],
        "ECON": ["Stephanie Phillips", "Gregory Campbell", "Timothy Evans"],
        "MATH": ["Robert Davis", "Nancy Clark", "Steven Hall", "Amy Allen", "Brian Young"],
        "HS": ["Elizabeth Rogers", "Charles Reed", "Paul Morgan", "Barbara Bell"],
        "BIOL": ["George Rivera", "Helen Cooper", "Margaret Cook"],
        "CS": ["David Joyner", "Monica Sweat", "Thad Starner", "Charles Isbell"],
    }

    # Get professor pool for this department, or use generic pool
    dept_professors = professor_pools.get(dept, [
        "Anderson, James", "Baker, Susan", "Carter, Michael",
        "Davis, Jennifer", "Evans, Robert"
    ])

    # Create deterministic but varied selection based on course code
    # This ensures same course always gets same professors
    seed = int(hashlib.md5(course_code.encode()).hexdigest(), 16) % (10**8)
    random.seed(seed)

    # Build professor list for this course
    available_professors = dept_professors.copy()
    random.shuffle(available_professors)

    # Ensure primary professor from demo data is included if available
    sample_professors = []
    if primary_professor and primary_professor != "Staff":
        sample_professors.append(primary_professor)

    # Add additional professors from the pool
    for prof in available_professors:
        if prof not in sample_professors:
            sample_professors.append(prof)
        if len(sample_professors) >= num_sections:
            break

    # Add Staff/TBA as fallback
    if len(sample_professors) < num_sections:
        sample_professors.append("Staff")

    sections = []
    for i in range(min(num_sections, len(times))):
        section_num = f"{i+1:03d}"  # 001, 002, 003, etc.

        # Get professor for this section
        instructor = sample_professors[i] if i < len(sample_professors) else "Staff"

        sections.append({
            "section": section_num,
            "instructor": instructor,
            "crn": f"{random.randint(10000, 99999)}",  # Varied CRNs
            "time": times[i],
            "days": times[i].split()[0],  # Extract days
            "location": locations[i % len(locations)]
        })

    # Reset random seed to avoid affecting other random operations
    random.seed()

    return sections

# Page config
st.set_page_config(
    page_title="GSU Course Planner",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS for GSU colors - Enhanced Modern Design
st.markdown("""
    <style>
    /* Main theme colors */
    :root {
        --gsu-blue: #0039A6;
        --gsu-gold: #FFB81C;
        --gsu-light: #E8F0FF;
        --gsu-dark: #1a1a2e;
    }
    
    /* Main header styling */
    .main-header {
        background: linear-gradient(135deg, #0039A6 0%, #003d85 100%);
        color: white;
        text-align: center;
        padding: 2.5rem 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0, 57, 166, 0.15);
        margin-bottom: 1rem;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5em;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    
    .tagline {
        color: #FFB81C;
        font-size: 1.1em;
        font-weight: 500;
        margin-top: 0.5rem;
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #0039A6 0%, #003d85 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0, 57, 166, 0.2);
        width: 100%;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #003d85 0%, #002d5a 100%);
        box-shadow: 0 6px 16px rgba(0, 57, 166, 0.3);
        transform: translateY(-2px);
    }
    
    /* Card styling */
    .course-card {
        background: linear-gradient(135deg, #f8f9ff 0%, #f0f2f6 100%);
        padding: 1.25rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border-left: 4px solid #0039A6;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
    }
    
    .course-card:hover {
        box-shadow: 0 4px 16px rgba(0, 57, 166, 0.12);
        transform: translateY(-2px);
    }
    
    /* Info box styling */
    .info-box {
        background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
        border-left: 4px solid #0039A6;
        padding: 1.25rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .success-box {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border-left: 4px solid #4CAF50;
        padding: 1.25rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
        border-left: 4px solid #FF9800;
        padding: 1.25rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Section headers */
    .section-header {
        color: #0039A6;
        font-size: 1.4em;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 3px solid #FFB81C;
    }
    
    .subsection-header {
        color: #003d85;
        font-size: 1.15em;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        font-weight: 600;
        color: #666;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #0039A6;
        color: white;
    }
    
    /* Expander styling */
    .streamlit-expander {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background-color: #0039A6;
    }
    
    /* Metric card styling */
    .metric-card {
        background: linear-gradient(135deg, #f8f9ff 0%, #f0f2f6 100%);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        border-top: 4px solid #0039A6;
    }
    
    /* List styling */
    .course-list {
        list-style: none;
        padding-left: 0;
    }
    
    .course-list li {
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9ff;
        border-left: 3px solid #0039A6;
        border-radius: 4px;
    }
    
    /* Footer styling */
    .footer {
        text-align: center;
        color: #999;
        padding: 2rem 0;
        margin-top: 3rem;
        border-top: 2px solid #e0e0e0;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main-header {
            padding: 1.5rem 1rem;
        }
        
        .main-header h1 {
            font-size: 1.8em;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Header with improved design
st.markdown("""
<div class="main-header">
    <h1>🎓 GSU Course Planner</h1>
    <p class="tagline">AI-Powered Academic Planning Assistant</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background: linear-gradient(90deg, #E8F0FF 0%, #FFF8E1 100%); padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
    <p style="margin: 0; color: #333; font-size: 1em;"><strong>Welcome!</strong> Upload your DegreeWorks academic evaluation to get personalized course recommendations, track your progress, and plan your path to graduation.</p>
</div>
""", unsafe_allow_html=True)

# Disclaimer with improved styling
with st.expander("⚠️ Important Disclaimer", expanded=False):
    st.markdown("""
    <div class="warning-box">
    <strong>⚠️ Important Notice</strong><br>
    This is <strong>NOT official GSU software</strong>. Always verify course plans with your academic advisor. 
    This tool is for planning purposes only and should not replace official academic advising. 
    Recommendations are based on publicly available course catalogs and may not reflect current availability or prerequisite changes.
    </div>
    """, unsafe_allow_html=True)

# Initialize session state
if 'eval_data' not in st.session_state:
    st.session_state.eval_data = None
if 'processing_state' not in st.session_state:
    st.session_state.processing_state = 'idle'  # idle, processing, complete, error
if 'ai_recommendations' not in st.session_state:
    st.session_state.ai_recommendations = None
if 'selected_major' not in st.session_state:
    st.session_state.selected_major = None
if 'selected_school' not in st.session_state:
    st.session_state.selected_school = None
if 'last_file_hash' not in st.session_state:
    st.session_state.last_file_hash = None

# Initialize catalog loader
catalog_loader = get_catalog_loader()

# Main content in tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Upload & Plan", "🔍 Prerequisite Lookup", "📚 Catalog Explorer", "ℹ️ How It Works", "📊 About"])

with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("<div class='section-header'>📄 Step 1: Upload Your Academic Evaluation</div>", unsafe_allow_html=True)
        
        st.markdown("""
        <div class="info-box">
        <strong>How to get your Academic Evaluation:</strong><br>
        1. Log into <strong>PAWS</strong> (paws.gsu.edu)<br>
        2. Go to <strong>Student</strong> tab<br>
        3. Click <strong>DegreeWorks</strong><br>
        4. Click <strong>Print/Export</strong> and save as PDF
        </div>
        """, unsafe_allow_html=True)

        # File uploader
        uploaded_file = st.file_uploader(
            "Upload your DegreeWorks PDF",
            type=['pdf'],
            help="Your academic evaluation showing completed and required courses"
        )

        if uploaded_file:
            # Detect if this is a new file upload
            import hashlib
            file_content = uploaded_file.read()
            file_hash = hashlib.md5(file_content).hexdigest()

            # Check if this is a different file than before
            if file_hash != st.session_state.last_file_hash:
                # New file detected - reset all state
                st.session_state.last_file_hash = file_hash
                st.session_state.processing_state = 'idle'
                st.session_state.ai_recommendations = None
                st.session_state.selected_major = None
                st.session_state.selected_school = None

                st.markdown("""
                <div class="success-box">
                ✅ <strong>New file detected!</strong><br>
                Analyzing your academic evaluation...
                </div>
                """, unsafe_allow_html=True)

                # Parse the academic evaluation (using cached version)
                with st.spinner("📊 Analyzing your academic evaluation..."):
                    try:
                        st.session_state.eval_data = parse_academic_eval_cached(file_content)

                    except Exception as e:
                        st.error(f"Error parsing file: {str(e)}")
                        st.session_state.eval_data = None
                        st.session_state.processing_state = 'error'
            else:
                # Same file as before
                st.markdown("""
                <div class="info-box">
                ✅ <strong>File loaded!</strong>
                </div>
                """, unsafe_allow_html=True)

            # Display eval data if available
            if st.session_state.eval_data:
                eval_data = st.session_state.eval_data

                # Show parsed info with better layout
                with st.expander("📋 Your Academic Summary", expanded=True):
                    info = eval_data["student_info"]

                    # Student info cards
                    st.markdown("<div class='subsection-header'>👤 Student Information</div>", unsafe_allow_html=True)
                    metric_cols = st.columns(4)

                    with metric_cols[0]:
                        st.markdown(f"""
                        <div class="metric-card">
                        <strong>Name</strong><br>
                        {info['student_name']}
                        </div>
                        """, unsafe_allow_html=True)

                    with metric_cols[1]:
                        st.markdown(f"""
                        <div class="metric-card">
                        <strong>Major</strong><br>
                        {info['major']}
                        </div>
                        """, unsafe_allow_html=True)

                    with metric_cols[2]:
                        st.markdown(f"""
                        <div class="metric-card">
                        <strong>GPA</strong><br>
                        {info['gpa']:.2f}
                        </div>
                        """, unsafe_allow_html=True)

                    with metric_cols[3]:
                        progress_pct = (info['credits_applied'] / info['credits_required']) * 100
                        st.markdown(f"""
                        <div class="metric-card">
                        <strong>Progress</strong><br>
                        {progress_pct:.1f}%
                        </div>
                        """, unsafe_allow_html=True)

                    # Progress bar
                    st.markdown("<div class='subsection-header'>📈 Credits Progress</div>", unsafe_allow_html=True)
                    st.progress(info['credits_applied'] / info['credits_required'])
                    st.markdown(f"**{info['credits_applied']}/{info['credits_required']} credits** ({progress_pct:.1f}%)")

                    # Show completed courses with better styling
                    with st.expander(f"✅ Completed Courses ({len(eval_data['completed_courses'])})"):
                        st.markdown("<div class='subsection-header'>Successfully Completed</div>", unsafe_allow_html=True)
                        for course in eval_data["completed_courses"]:
                            st.markdown(f"""
                            <div class="course-card">
                            <strong>{course['course_code']}</strong> — {course['course_name']}<br>
                            <small>Grade: <span style="color: #0039A6; font-weight: bold;">{course['grade']}</span> | 
                            Credits: <span style="color: #0039A6; font-weight: bold;">{course['credits']}</span> | 
                            Completed: {course['term']}</small>
                            </div>
                            """, unsafe_allow_html=True)

                    # Show in-progress courses
                    if eval_data["in_progress_courses"]:
                        with st.expander(f"📚 Currently Enrolled ({len(eval_data['in_progress_courses'])})"):
                            st.markdown("<div class='subsection-header'>Currently Taking</div>", unsafe_allow_html=True)
                            for course in eval_data["in_progress_courses"]:
                                st.markdown(f"""
                                <div class="course-card" style="border-left-color: #FF9800;">
                                <strong>{course['course_code']}</strong> — {course['course_name']}<br>
                                <small>Credits: <span style="color: #FF9800; font-weight: bold;">{course['credits']}</span> | 
                                Term: {course['term']}</small>
                                </div>
                                """, unsafe_allow_html=True)

                    # Show required courses
                    with st.expander(f"📝 Courses Still Needed ({len(eval_data['required_courses'])})"):
                        st.markdown("<div class='subsection-header'>Remaining Requirements</div>", unsafe_allow_html=True)
                        for req in eval_data["required_courses"]:
                            if req.get("is_elective"):
                                st.markdown(f"""
                                <div class="course-card" style="border-left-color: #4CAF50;">
                                📋 <strong>{req['credits']} credits</strong> of electives<br>
                                <small>{req['courses'][0]}</small>
                                </div>
                                """, unsafe_allow_html=True)
                            elif req.get("is_choice"):
                                st.write(f"- {req['credits']} credits: {' OR '.join(req['courses'])}")
                            else:
                                st.write(f"- **{req['courses'][0]}** ({req['credits']} credits)")

        # Major Detection Display - After PDF is parsed
        if st.session_state.eval_data:
            st.markdown("---")
            detected_major = st.session_state.eval_data["student_info"]["major"]

            if detected_major:
                st.markdown(f"""
                <div class="success-box">
                ✅ <strong>Detected Major from PDF:</strong> {detected_major}<br>
                <small>You can confirm or change this in the preferences form below.</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="warning-box">
                ⚠️ <strong>Major not automatically detected</strong><br>
                <small>Please select your major in the preferences form below.</small>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        st.subheader("🎯 Step 2: Your Preferences")

        # Student preferences form
        with st.form("preferences_form"):
            # Select school first
            available_schools = catalog_loader.get_available_schools()
            selected_school = st.selectbox(
                "Select Your School",
                options=available_schools,
                help="Choose your institution to get accurate course recommendations"
            )

            # Select major based on school
            available_majors = catalog_loader.get_majors_for_school(selected_school)

            # Check if we already have major from PDF
            if st.session_state.eval_data and st.session_state.eval_data["student_info"].get("major"):
                # Major already known from uploaded PDF - display as read-only
                confirmed_major = st.session_state.eval_data["student_info"]["major"]
                st.markdown(f"**📚 Your Major:** {confirmed_major}")
                st.caption("Detected from your DegreeWorks file")
                selected_major = confirmed_major
            else:
                # No major in PDF - ask user to select
                selected_major = st.selectbox(
                    "Select Your Major",
                    options=available_majors,
                    help="Choose your degree program to get tailored recommendations"
                )

            # Note: selected_major and selected_school are local variables
            # They will only be saved to session state when form is submitted

            # Career goals
            career_goals = st.text_area(
                "Career Goals & Interests (Optional)",
                placeholder="E.g., I want to work in data science, interested in AI/ML, cybersecurity...",
                height=80
            )

            # Work schedule
            has_job = st.checkbox("I have a job/significant time commitments")

            # Preferred class times
            preferred_times = st.multiselect(
                "Preferred Class Times",
                ["Morning (8am-12pm)", "Afternoon (12pm-5pm)", "Evening (5pm+)", "No preference"],
                default=["No preference"]
            )

            # Course load
            max_courses = st.slider(
                "Maximum Courses Per Semester",
                min_value=3,
                max_value=6,
                value=4,
                help="How many courses do you want to take?"
            )

            # Difficulty preference
            difficulty_pref = st.radio(
                "Semester Difficulty Preference",
                ["Light (easier courses)", "Balanced", "Challenging (harder courses)"],
                index=1,
                horizontal=True
            )

            # Specific preferences
            col_a, col_b = st.columns(2)
            with col_a:
                prioritize_courses = st.text_input(
                    "Courses to Prioritize",
                    placeholder="E.g., CSC 3210, MATH 2641"
                )
            with col_b:
                avoid_courses = st.text_input(
                    "Courses to Avoid",
                    placeholder="E.g., early morning classes"
                )

            # Submit button
            submit_button = st.form_submit_button("🚀 Generate My Schedule", use_container_width=True)

    with col2:
        st.subheader("📅 Your Personalized Schedule")

        if submit_button and st.session_state.eval_data:
            # NOW save the form values to session state (after submission)
            st.session_state.selected_major = selected_major
            st.session_state.selected_school = selected_school
            st.session_state.processing_state = 'processing'

            eval_data = st.session_state.eval_data

            try:
                # Get recommendations based on prerequisites
                recs = get_next_semester_recommendations(eval_data)

                # Build preferences dict
                preferences = {
                    "career_goals": career_goals,
                    "has_job": has_job,
                    "preferred_times": preferred_times,
                    "max_courses": max_courses,
                    "difficulty_preference": difficulty_pref,
                    "prioritize_courses": prioritize_courses,
                    "avoid_courses": avoid_courses
                }

                # Try to get AI recommendations
                with st.spinner("🤖 AI is analyzing your evaluation and generating recommendations..."):
                    try:
                        from utils.llm_integration import CourseRecommender

                        recommender = CourseRecommender()

                        # Prepare data for LLM
                        student_data = {
                            "student_name": eval_data["student_info"]["student_name"],
                            "gpa": eval_data["student_info"]["gpa"],
                            "total_credits": eval_data["student_info"]["credits_applied"],
                            "credits_required": eval_data["student_info"]["credits_required"],
                            "completed_courses": eval_data["completed_courses"],
                            "in_progress_courses": eval_data["in_progress_courses"]
                        }

                        # Get courses that can be taken (prerequisites met)
                        available_courses = recs["available_courses"]
                        # Degree requirements
                        degree_requirements = {
                            "required_courses": eval_data["required_courses"],
                            "summary": eval_data["requirements_summary"]
                        }

                        ai_result = recommender.generate_schedule(
                            student_data=student_data,
                            preferences=preferences,
                            available_courses=available_courses,
                            degree_requirements=degree_requirements,
                            allow_retakes=False
                        )
                        st.session_state.ai_recommendations = ai_result
                        use_ai = True

                    except Exception as e:
                        st.warning(f"AI recommendations unavailable: {str(e)}")
                        st.info("Showing basic recommendations based on prerequisites.")
                        use_ai = False

                # Mark as complete if we got here
                st.session_state.processing_state = 'complete'

            except Exception as e:
                st.error(f"❌ Error generating schedule: {str(e)}")
                import traceback
                st.error(f"Debug info: {traceback.format_exc()}")
                st.session_state.processing_state = 'error'
                use_ai = False

            # Only show success and results if no error occurred
            if st.session_state.processing_state == 'complete':
                st.success("✅ Schedule Generated!")

                # Display student info summary
                info = eval_data["student_info"]
                st.markdown(f"#### 🎓 Recommendations for {info['student_name']}")

                # Show AI recommendations or fallback
                if use_ai and st.session_state.ai_recommendations:
                    ai_recs = st.session_state.ai_recommendations

                    if ai_recs.get("recommended_courses"):
                        st.markdown("##### 📋 Recommended Courses")

                        # Demo mode info
                        st.info("🎭 **Demo Mode:** Showing sample professor data to demonstrate RMP integration. In production, this would pull from GSU's course schedule.")

                        # Get recommended courses
                        recommended_courses = ai_recs["recommended_courses"][:max_courses]

                        # Add demo professors (so we can see RMP integration working)
                        recommended_courses = add_demo_professors(recommended_courses, use_demo_mode=True)

                        # Enrich courses with RMP data
                        try:
                            school_name = info.get('school', 'Georgia State University')
                            enriched_courses = enrich_courses_with_rmp(recommended_courses, school_name)
                        except Exception as e:
                            st.warning(f"⚠️ Rate My Professor data temporarily unavailable")
                            enriched_courses = recommended_courses

                        for course in enriched_courses:
                            with st.container():
                                # Course header
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.markdown(f"""
                                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                                padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
                                        <h4 style="color: white; margin: 0;">
                                            {course.get('course_code', 'N/A')} - {course.get('course_name', 'N/A')}
                                        </h4>
                                    </div>
                                    """, unsafe_allow_html=True)

                                with col2:
                                    difficulty = course.get('difficulty', 'Medium')
                                    if difficulty.lower() == 'easy':
                                        diff_color = "#28a745"
                                        diff_emoji = "😊"
                                    elif difficulty.lower() == 'hard':
                                        diff_color = "#dc3545"
                                        diff_emoji = "💪"
                                    else:
                                        diff_color = "#ffc107"
                                        diff_emoji = "📚"

                                    st.markdown(f"""
                                    <div style="background: {diff_color}; color: white;
                                                padding: 0.5rem; border-radius: 8px; text-align: center;">
                                        <strong>{diff_emoji} {difficulty}</strong>
                                    </div>
                                    """, unsafe_allow_html=True)

                                # Course details
                                col_a, col_b = st.columns(2)

                                with col_a:
                                    st.write(f"**📝 Reason:** {course.get('reason', 'Required for major')}")
                                    credits = course.get('credits', 3)
                                    st.write(f"**⭐ Credits:** {credits}")

                                with col_b:
                                    # RMP ratings
                                    rmp_data = course.get('rmp_data')
                                    if rmp_data:
                                        rating = rmp_data.get('rating')
                                        difficulty_rmp = rmp_data.get('difficulty')
                                        num_ratings = rmp_data.get('num_ratings', 0)

                                        if rating:
                                            rating_emoji = "🌟" if rating >= 4.5 else "⭐" if rating >= 4.0 else "✨" if rating >= 3.5 else "💫"
                                            st.write(f"**👨‍🏫 Professor Rating:** {rating_emoji} {rating}/5.0")

                                        if difficulty_rmp:
                                            diff_rmp_emoji = "😊" if difficulty_rmp <= 2.0 else "😐" if difficulty_rmp <= 3.0 else "😰" if difficulty_rmp <= 4.0 else "💀"
                                            st.write(f"**🎯 Prof Difficulty:** {diff_rmp_emoji} {difficulty_rmp}/5.0")

                                        if num_ratings:
                                            st.caption(f"📊 Based on {num_ratings} reviews")
                                    else:
                                        professor = course.get('professor', 'TBA')
                                        st.write(f"**👨‍🏫 Professor:** {professor}")
                                        if professor.lower() not in ['tba', 'staff', 'tbd']:
                                            st.caption("🔍 Looking up rating...")

                                # Section rankings (NEW FEATURE!)
                                with st.expander("📊 Available Sections (Ranked by Professor Quality)"):
                                    st.caption("Sections are ranked using Rate My Professor data - best professors first!")

                                    # Generate sample sections for this course
                                    course_code = course.get('course_code', '')
                                    if course_code:
                                        try:
                                            # Get sample sections
                                            sample_sections = generate_sample_sections(course_code, num_sections=4)

                                            # Rank sections
                                            school_name = info.get('school', 'Georgia State University')
                                            ranked_sections = get_ranked_sections(
                                                course_code=course_code,
                                                sections_data=sample_sections,
                                                school=school_name
                                            )

                                            # Display ranked sections
                                            for section in ranked_sections[:3]:  # Show top 3
                                                # Rank badge
                                                if section.rank == 1:
                                                    rank_emoji = "🥇"
                                                    rank_color = "#FFD700"
                                                elif section.rank == 2:
                                                    rank_emoji = "🥈"
                                                    rank_color = "#C0C0C0"
                                                elif section.rank == 3:
                                                    rank_emoji = "🥉"
                                                    rank_color = "#CD7F32"
                                                else:
                                                    rank_emoji = f"#{section.rank}"
                                                    rank_color = "#666666"

                                                # Section card
                                                st.markdown(f"""
                                                <div style="background: linear-gradient(90deg, {rank_color}22 0%, {rank_color}11 100%);
                                                            padding: 0.75rem; border-radius: 8px; margin: 0.5rem 0;
                                                            border-left: 4px solid {rank_color};">
                                                    <strong>{rank_emoji} Section {section.section}</strong> - {section.instructor_normalized}
                                                </div>
                                                """, unsafe_allow_html=True)

                                                # Section details
                                                col_s1, col_s2 = st.columns(2)

                                                with col_s1:
                                                    if section.time:
                                                        st.caption(f"🕐 {section.time}")
                                                    if section.location:
                                                        st.caption(f"📍 {section.location}")

                                                with col_s2:
                                                    if section.rating:
                                                        rating_emoji_s = "🌟" if section.rating >= 4.5 else "⭐" if section.rating >= 4.0 else "✨" if section.rating >= 3.5 else "💫"
                                                        st.caption(f"{rating_emoji_s} {section.rating}/5.0 ({section.num_reviews} reviews)")
                                                        st.caption(f"📊 Quality Score: {section.score}")
                                                    else:
                                                        st.caption("⚠️ No RMP data")

                                            # Show note about fallback
                                            if len(ranked_sections) > 3:
                                                st.info(f"💡 **Tip:** If the top section fills, try Section {ranked_sections[1].section} next!")

                                        except Exception as e:
                                            st.warning("Section ranking temporarily unavailable")

                                st.markdown("---")

                    # AI reasoning
                    with st.expander("🤔 AI Reasoning", expanded=True):
                        st.markdown(ai_recs.get("reasoning", "No detailed reasoning available."))

                        if ai_recs.get("difficulty_balance"):
                            st.write(f"**Difficulty Balance:** {ai_recs['difficulty_balance']}")

                        if ai_recs.get("semesters_remaining"):
                            st.write(f"**Estimated Semesters Remaining:** {ai_recs['semesters_remaining']}")

                    # Alternative options
                    if ai_recs.get("alternatives"):
                        with st.expander("🔄 Alternative Courses"):
                            for alt in ai_recs["alternatives"]:
                                st.write(f"- {alt.get('course_code', alt)}: {alt.get('course_name', '')}")

                else:
                    # Fallback: show courses with prerequisites met
                    st.markdown("##### Available Courses (Prerequisites Met)")

                    if recs["available_courses"]:
                        for i, course in enumerate(recs["available_courses"][:max_courses]):
                            st.markdown(f"""
                            **{course['course_code']}** ({course['credits']} credits)
                            - Prerequisites: ✅ All met
                            """)
                    else:
                        st.info("Complete your current courses to unlock more options.")

                    # Show courses needing prerequisites
                    if recs["prerequisites_needed"]:
                        with st.expander("🔒 Courses Needing Prerequisites"):
                            for course in recs["prerequisites_needed"][:5]:
                                missing = ", ".join(course.get("missing_prerequisites", []))
                                st.write(f"- **{course['course_code']}**: Needs {missing}")

                # Progress visualization
                st.markdown("#### 📊 Degree Progress")
                credits_done = info['credits_applied']
                credits_total = info['credits_required']
                progress_pct = (credits_done / credits_total) * 100
                st.progress(progress_pct / 100)
                st.write(f"**{credits_done}/{credits_total} credits** ({progress_pct:.1f}% complete)")

                # Estimate remaining semesters
                credits_remaining = credits_total - credits_done
                avg_credits_per_sem = max_courses * 3  # Assume 3 credits per course
                semesters_remaining = max(1, credits_remaining // avg_credits_per_sem)
                st.info(f"📅 **Estimated {semesters_remaining} semesters remaining** at {max_courses} courses/semester")

                # Export options
                st.markdown("---")
                st.markdown("""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 1.5rem; border-radius: 15px; margin: 1rem 0;">
                    <h3 style="color: white; margin: 0; text-align: center;">📥 Export Your Schedule</h3>
                    <p style="color: rgba(255,255,255,0.9); text-align: center; margin: 0.5rem 0;">
                        Download your personalized course plan in multiple formats
                    </p>
                </div>
                """, unsafe_allow_html=True)

                if st.session_state.ai_recommendations:
                    export_courses = st.session_state.ai_recommendations.get("recommended_courses", [])[:max_courses]

                    # Prepare student info for export
                    student_export_info = {
                        "name": info.get('student_name', 'Student'),
                        "major": info.get('major', 'Computer Science'),
                        "semester": datetime.now().strftime("%B %Y")
                    }

                    # Create three columns for export buttons
                    exp_col1, exp_col2, exp_col3 = st.columns(3)

                    with exp_col1:
                        st.markdown("""
                        <div style="text-align: center; padding: 1rem;">
                            <h4 style="color: #0039A6; margin: 0;">📄 PDF</h4>
                            <p style="font-size: 0.85em; color: #666;">Professional format</p>
                        </div>
                        """, unsafe_allow_html=True)

                        try:
                            pdf_buffer = generate_pdf_schedule(export_courses, student_export_info)
                            st.download_button(
                                label="⬇️ Download PDF",
                                data=pdf_buffer,
                                file_name=f"gsu_schedule_{datetime.now().strftime('%Y%m%d')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"PDF export unavailable: {str(e)[:50]}")

                    with exp_col2:
                        st.markdown("""
                        <div style="text-align: center; padding: 1rem;">
                            <h4 style="color: #0039A6; margin: 0;">📅 Calendar</h4>
                            <p style="font-size: 0.85em; color: #666;">Import to Google</p>
                        </div>
                        """, unsafe_allow_html=True)

                        try:
                            ics_content = generate_ics_calendar(export_courses)
                            st.download_button(
                                label="⬇️ Download .ics",
                                data=ics_content,
                                file_name=f"gsu_schedule_{datetime.now().strftime('%Y%m%d')}.ics",
                                mime="text/calendar",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"Calendar export unavailable")

                    with exp_col3:
                        st.markdown("""
                        <div style="text-align: center; padding: 1rem;">
                            <h4 style="color: #0039A6; margin: 0;">📋 Text</h4>
                            <p style="font-size: 0.85em; color: #666;">Copy & paste</p>
                        </div>
                        """, unsafe_allow_html=True)

                        try:
                            text_schedule = generate_text_schedule(export_courses, student_export_info)

                            # Copy to clipboard using text area
                            if st.button("📋 Copy to Clipboard", use_container_width=True):
                                st.code(text_schedule, language=None)
                                st.success("✅ Schedule displayed! Copy the text above.")

                            # Also offer as download
                            st.download_button(
                                label="⬇️ Download .txt",
                                data=text_schedule,
                                file_name=f"gsu_schedule_{datetime.now().strftime('%Y%m%d')}.txt",
                                mime="text/plain",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"Text export unavailable")

                    # JSON export (keep for developers/debugging)
                    with st.expander("🔧 Advanced: JSON Export"):
                        export_data = json.dumps(st.session_state.ai_recommendations, indent=2)
                        st.download_button(
                            "Download Full Data (JSON)",
                            data=export_data,
                            file_name=f"gsu_schedule_data_{datetime.now().strftime('%Y%m%d')}.json",
                            mime="application/json"
                        )

        elif submit_button and not st.session_state.eval_data:
            st.warning("⚠️ Please upload your academic evaluation first.")

        elif st.session_state.processing_state == 'idle':
            st.info("👆 Upload your academic evaluation and click 'Generate My Schedule' to get started.")

        elif st.session_state.processing_state == 'error':
            st.error("❌ An error occurred. Please try uploading your file again.")

    # Add catalog-based recommendations section ONLY after form submission
    if (st.session_state.eval_data and
        st.session_state.selected_major and
        st.session_state.processing_state == 'complete'):
        st.markdown("---")
        st.markdown("### 📚 Catalog-Based Course Requirements")
        st.markdown("*These recommendations are based on your selected major's course catalog.*")

        eval_data = st.session_state.eval_data
        major = st.session_state.selected_major
        school = st.session_state.selected_school

        # Get completed courses and currently enrolled courses
        completed_courses = [c['course_code'] for c in eval_data['completed_courses']]
        in_progress_courses = [c['course_code'] for c in eval_data['in_progress_courses']]
        all_taken_courses = completed_courses + in_progress_courses

        # Show degree progress
        col_prog1, col_prog2, col_prog3 = st.columns(3)

        with col_prog1:
            progress_info = catalog_loader.get_degree_progress(school, major, completed_courses)
            st.metric("Core Courses", progress_info['core_progress'])

        with col_prog2:
            st.metric("Math Courses", progress_info['math_progress'])

        with col_prog3:
            st.metric("Completion", f"{progress_info['completion_percentage']}%")

        # Show next available courses based on catalog
        st.markdown("#### 🟢 Courses You Can Take Now")

        # Show info about currently enrolled courses
        if in_progress_courses:
            st.info(f"📚 Excluding {len(in_progress_courses)} course(s) you're currently enrolled in")

        next_courses = catalog_loader.get_recommended_next_courses(school, major, all_taken_courses, limit=8)

        if next_courses:
            cols = st.columns(2)
            for i, course in enumerate(next_courses):
                with cols[i % 2]:
                    st.markdown(f"""
                    **{course['course_code']}**  
                    {course['course_name']}  
                    *{course['credits']} credits*  
                    _{course['description'][:100]}..._
                    """)
        else:
            st.info("Complete more prerequisites to unlock additional courses.")

        # Show degree requirements
        st.markdown("#### 📋 Major Requirements")

        req_tab1, req_tab2, req_tab3 = st.tabs(["Core Courses", "Electives", "Math"])

        with req_tab1:
            core_courses = catalog_loader.get_core_courses(school, major)
            completed_core = [c for c in core_courses if c['course_code'] in completed_courses]
            in_progress_core = [c for c in core_courses if c['course_code'] in in_progress_courses]
            pending_core = [c for c in core_courses if c['course_code'] not in all_taken_courses]

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Completed:**")
                if completed_core:
                    for course in completed_core:
                        st.markdown(f"✅ {course['course_code']}: {course['course_name']}")
                else:
                    st.markdown("*None yet*")

            with col2:
                st.markdown("**Currently Enrolled:**")
                if in_progress_core:
                    for course in in_progress_core:
                        st.markdown(f"📚 {course['course_code']}: {course['course_name']}")
                else:
                    st.markdown("*None*")

            with col3:
                st.markdown("**Still Needed:**")
                if pending_core:
                    for course in pending_core:
                        st.markdown(f"⏳ {course['course_code']}: {course['course_name']}")
                else:
                    st.success("✅ All core courses done!")

        with req_tab2:
            electives = catalog_loader.get_elective_courses(school, major)
            if electives:
                st.markdown("Choose electives based on your interests:")
                for elective in electives:
                    # Check if already taking or completed
                    if elective['course_code'] in all_taken_courses:
                        if elective['course_code'] in completed_courses:
                            status = "✅ Completed"
                        else:
                            status = "📚 Currently Enrolled"
                    else:
                        can_take = catalog_loader.check_prerequisites_met(
                            school, major, elective['course_code'], all_taken_courses
                        )['can_take']
                        status = "✅ Available" if can_take else "🔒 Prerequisites needed"
                    st.markdown(f"- **{elective['course_code']}**: {elective['course_name']} - {status}")
            else:
                st.info("No electives defined for this major.")

        with req_tab3:
            math_reqs = catalog_loader.get_math_requirements(school, major)
            if math_reqs:
                completed_math = [m for m in math_reqs if m['course_code'] in completed_courses]
                in_progress_math = [m for m in math_reqs if m['course_code'] in in_progress_courses]
                pending_math = [m for m in math_reqs if m['course_code'] not in all_taken_courses]

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("**Completed:**")
                    if completed_math:
                        for course in completed_math:
                            st.markdown(f"✅ {course['course_code']}: {course['course_name']}")
                    else:
                        st.markdown("*None yet*")

                with col2:
                    st.markdown("**Currently Enrolled:**")
                    if in_progress_math:
                        for course in in_progress_math:
                            st.markdown(f"📚 {course['course_code']}: {course['course_name']}")
                    else:
                        st.markdown("*None*")

                with col3:
                    st.markdown("**Still Needed:**")
                    if pending_math:
                        for course in pending_math:
                            st.markdown(f"⏳ {course['course_code']}: {course['course_name']}")
                    else:
                        st.success("✅ All math done!")

with tab3:
    st.markdown("### 📚 Catalog Explorer")
    st.markdown("Browse and explore courses for each major program.")

    # School and Major selectors
    col_sch, col_maj = st.columns(2)
    
    with col_sch:
        explorer_school = st.selectbox(
            "Select a School",
            options=catalog_loader.get_available_schools(),
            key="catalog_explorer_school"
        )
    
    with col_maj:
        if explorer_school:
            majors_for_school = catalog_loader.get_majors_for_school(explorer_school)
            explorer_major = st.selectbox(
                "Select a Major to Explore",
                options=majors_for_school,
                key="catalog_explorer_major"
            )
        else:
            explorer_major = None

    if explorer_major and explorer_school:
        # Get catalog info
        catalog = catalog_loader.get_catalog(explorer_school, explorer_major)
        metadata = catalog.get("metadata", {}) if catalog else {}

        # Header
        st.markdown(f"## {metadata.get('major', explorer_major)}")
        st.markdown(f"**Degree Type:** {metadata.get('degree_type', 'N/A')} | "
                    f"**Total Credits Required:** {metadata.get('total_credits_required', 'N/A')}")

        st.markdown("---")

        # Tabs for different course types
        cat_tab1, cat_tab2, cat_tab3 = st.tabs(["Core Courses", "Electives", "All Courses"])

        with cat_tab1:
            core_courses = catalog_loader.get_core_courses(explorer_school, explorer_major)
            st.markdown(f"### Required Core Courses ({len(core_courses)} courses)")

            for course in core_courses:
                with st.expander(f"**{course['course_code']}**: {course['course_name']} ({course['credits']} credits)"):
                    st.markdown(course['description'])

                    prereqs = catalog_loader.get_prerequisites(explorer_school, explorer_major, course['course_code'])
                    if prereqs:
                        st.markdown(f"**Prerequisites:** {', '.join(prereqs)}")
                    else:
                        st.markdown("**Prerequisites:** None")

        with cat_tab2:
            electives = catalog_loader.get_elective_courses(explorer_school, explorer_major)
            st.markdown(f"### Elective Courses ({len(electives)} courses)")

            for course in electives:
                with st.expander(f"**{course['course_code']}**: {course['course_name']} ({course['credits']} credits)"):
                    st.markdown(course['description'])

                    prereqs = catalog_loader.get_prerequisites(explorer_school, explorer_major, course['course_code'])
                    if prereqs:
                        st.markdown(f"**Prerequisites:** {', '.join(prereqs)}")
                    else:
                        st.markdown("**Prerequisites:** None")

        with cat_tab3:
            all_courses = catalog_loader.get_all_courses_for_major(explorer_school, explorer_major)
            st.markdown(f"### All Courses in {explorer_major} ({len(all_courses)} courses)")

            # Search within catalog
            search_term = st.text_input("Search courses (by code or name):")

            filtered_courses = {}
            for code, info in all_courses.items():
                if search_term.lower() in code.lower() or search_term.lower() in info.get('name', '').lower():
                    filtered_courses[code] = info

            st.markdown(f"**Showing {len(filtered_courses)} course(s)**")

            # Display as cards
            for code, info in sorted(filtered_courses.items()):
                col_c1, col_c2, col_c3 = st.columns([2, 1, 1])

                with col_c1:
                    st.markdown(f"**{code}**: {info.get('name', 'Unknown')}")

                with col_c2:
                    st.markdown(f"**Credits:** {info.get('credits', '?')}")

                with col_c3:
                    prereq_count = len(info.get('prerequisites', []))
                    st.markdown(f"**Prereqs:** {prereq_count}")

                # Expandable details
                with st.expander(f"Details for {code}"):
                    st.markdown(f"**Description:** {info.get('description', 'No description')}")

                    if info.get('prerequisites'):
                        st.markdown(f"**Prerequisites:** {', '.join(info['prerequisites'])}")

                    if info.get('corequisites'):
                        st.markdown(f"**Corequisites:** {', '.join(info['corequisites'])}")

                    st.markdown(f"**Minimum Grade:** {info.get('min_grade', 'C')}")

with tab2:
    st.markdown("### 🔍 Course Prerequisite Lookup")
    st.markdown("Search for any course to see its prerequisites, what it unlocks, and the full prerequisite chain.")

    # Search section
    col_search1, col_search2 = st.columns([2, 1])

    with col_search1:
        # Course search/select
        all_courses = list(COURSE_DATABASE.keys())
        selected_course = st.selectbox(
            "Select or search for a course",
            options=[""] + sorted(all_courses),
            format_func=lambda x: f"{x}: {COURSE_DATABASE[x]['name']}" if x and x in COURSE_DATABASE else "-- Select a course --",
            help="Start typing to search by course code"
        )

    with col_search2:
        # Quick filter by department
        dept_filter = st.selectbox(
            "Filter by department",
            options=["All", "CSC (Computer Science)", "MATH (Mathematics)", "Science"],
            index=0
        )

    # Display course information
    if selected_course and selected_course in COURSE_DATABASE:
        course_info = COURSE_DATABASE[selected_course]

        st.markdown("---")

        # Course header
        st.markdown(f"## 📚 {selected_course}: {course_info['name']}")

        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric("Credits", course_info['credits'])
        with col_info2:
            st.metric("Min Grade Required", course_info.get('min_grade', 'C'))
        with col_info3:
            prereq_count = len(course_info.get('prerequisites', []))
            st.metric("Prerequisites", prereq_count)

        # Description
        st.markdown(f"**Description:** {course_info['description']}")

        st.markdown("---")

        # Prerequisites section
        col_prereq, col_unlock = st.columns(2)

        with col_prereq:
            st.markdown("### 📋 Prerequisites")
            prereqs = course_info.get('prerequisites', [])

            if prereqs:
                st.markdown("**Direct prerequisites (must complete first):**")
                for prereq in prereqs:
                    prereq_info = COURSE_DATABASE.get(prereq, {})
                    prereq_name = prereq_info.get('name', 'Unknown')
                    prereq_credits = prereq_info.get('credits', '?')

                    # Check if prereq has its own prereqs
                    deeper_prereqs = prereq_info.get('prerequisites', [])

                    st.markdown(f"- **{prereq}**: {prereq_name} ({prereq_credits} credits)")
                    if deeper_prereqs:
                        st.markdown(f"  - *Requires: {', '.join(deeper_prereqs)}*")
            else:
                st.success("✅ No prerequisites! You can take this course anytime.")

            # Corequisites
            coreqs = course_info.get('corequisites', [])
            if coreqs:
                st.markdown("**Corequisites (take at same time):**")
                for coreq in coreqs:
                    coreq_info = COURSE_DATABASE.get(coreq, {})
                    st.markdown(f"- **{coreq}**: {coreq_info.get('name', 'Unknown')}")

        with col_unlock:
            st.markdown("### 🔓 What This Course Unlocks")
            unlocked = get_courses_unlocked_by(selected_course)

            if unlocked:
                st.markdown("**Completing this course allows you to take:**")
                for unlock in unlocked:
                    unlock_info = COURSE_DATABASE.get(unlock, {})
                    st.markdown(f"- **{unlock}**: {unlock_info.get('name', 'Unknown')}")
            else:
                st.info("This course doesn't directly unlock any other courses in our database.")

        # Full prerequisite chain
        st.markdown("---")
        st.markdown("### 📍 Full Prerequisite Chain")

        full_chain = get_all_prerequisites(selected_course)
        if full_chain:
            st.markdown("**Complete the courses in this order:**")

            # Create a visual chain
            chain_display = " → ".join(full_chain + [selected_course])
            st.code(chain_display)

            # Detailed breakdown
            with st.expander("View detailed breakdown"):
                for i, course in enumerate(full_chain, 1):
                    course_data = COURSE_DATABASE.get(course, {})
                    st.markdown(f"{i}. **{course}**: {course_data.get('name', 'Unknown')} ({course_data.get('credits', '?')} credits)")
                st.markdown(f"{len(full_chain) + 1}. **{selected_course}**: {course_info['name']} ({course_info['credits']} credits) ✅ TARGET")

            # Calculate total credits in chain
            total_credits = sum(COURSE_DATABASE.get(c, {}).get('credits', 0) for c in full_chain)
            total_credits += course_info['credits']
            st.info(f"📊 **Total credits in this chain:** {total_credits} credits across {len(full_chain) + 1} courses")
        else:
            st.success("✅ No prerequisite chain - you can take this course directly!")

        # Check against your completed courses (if evaluation uploaded)
        if st.session_state.eval_data:
            st.markdown("---")
            st.markdown("### 🎯 Can You Take This Course?")

            completed_codes = [c['course_code'] for c in st.session_state.eval_data['completed_courses']]
            in_progress_codes = [c['course_code'] for c in st.session_state.eval_data['in_progress_courses']]
            all_taken = completed_codes + in_progress_codes

            check_result = check_prerequisites_met(selected_course, all_taken)

            if check_result['can_take']:
                st.success(f"✅ **Yes!** You have completed all prerequisites for {selected_course}.")
            else:
                st.warning(f"⚠️ **Not yet.** You need to complete these courses first:")
                for missing in check_result['missing']:
                    missing_info = COURSE_DATABASE.get(missing, {})
                    st.markdown(f"- **{missing}**: {missing_info.get('name', 'Unknown')}")

    # Course catalog browser
    st.markdown("---")
    st.markdown("### 📖 Browse Course Catalog")

    browse_dept = st.radio(
        "Select department",
        ["Computer Science (CSC)", "Mathematics (MATH)"],
        horizontal=True
    )

    if browse_dept == "Computer Science (CSC)":
        courses_to_show = get_all_cs_courses()
    else:
        courses_to_show = get_all_math_courses()

    # Display as expandable cards
    for course in courses_to_show:
        with st.expander(f"**{course['course_code']}**: {course['name']} ({course['credits']} credits)"):
            st.markdown(f"**Description:** {course['description']}")

            prereqs = course.get('prerequisites', [])
            if prereqs:
                st.markdown(f"**Prerequisites:** {', '.join(prereqs)}")
            else:
                st.markdown("**Prerequisites:** None")

            coreqs = course.get('corequisites', [])
            if coreqs:
                st.markdown(f"**Corequisites:** {', '.join(coreqs)}")

with tab4:
    st.markdown("<div class='section-header'>🔍 How This Works</div>", unsafe_allow_html=True)

    st.markdown("""
    This AI-powered tool helps you plan your course schedule by:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="course-card">
        <h3 style="color: #0039A6; margin-top: 0;">📄 Analyzing Your Evaluation</h3>
        • Extracts completed courses and grades<br>
        • Identifies remaining degree requirements<br>
        • Checks which prerequisites you've satisfied<br>
        • Finds courses you're eligible to take
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="course-card">
        <h3 style="color: #0039A6; margin-top: 0;">🎯 Understanding Preferences</h3>
        • Career goals and interests<br>
        • Schedule constraints (work, preferred times)<br>
        • Course load preferences<br>
        • Difficulty preferences
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="course-card">
        <h3 style="color: #0039A6; margin-top: 0;">🤖 AI Recommendations</h3>
        • Uses GPT to analyze your situation<br>
        • Matches courses to your goals<br>
        • Balances difficulty across semester<br>
        • Shows Rate My Professor ratings<br>
        • Optimizes path to graduation
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="course-card">
        <h3 style="color: #0039A6; margin-top: 0;">📊 Smart Planning</h3>
        • Shows degree progress<br>
        • Predicts graduation timeline<br>
        • Suggests alternative courses<br>
        • Respects prerequisites chains
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div class='section-header'>📥 How to Get Your Academic Evaluation</div>", unsafe_allow_html=True)
    
    steps = [
        "Log into **PAWS** (paws.gsu.edu)",
        "Go to the **Student** tab",
        "Click **DegreeWorks**",
        "Click **Print** or **Export** and save as PDF",
        "Upload the PDF to get started!"
    ]
    
    for i, step in enumerate(steps, 1):
        st.markdown(f"""
        <div class="course-card">
        <strong style="color: #0039A6;">Step {i}</strong><br>
        {step}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div class='section-header'>🔒 Privacy & Data</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
    • Your data is processed in your browser session only<br>
    • We don't permanently store your personal information<br>
    • The AI sees only what's needed for recommendations<br>
    • Close the browser to clear all data
    </div>
    """, unsafe_allow_html=True)

with tab5:
    st.markdown("<div class='section-header'>📊 About This Project</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <h3 style="color: #0039A6; margin-top: 0;">GSU Course Planning AI</h3>
    A student-built tool designed to help Georgia State University students make better course planning decisions.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
        <h4 style="color: #0039A6; margin: 0;">🎯 What It Does</h4>
        <ul style="margin: 1rem 0; padding-left: 1.5rem;">
        <li>Parses DegreeWorks evaluations</li>
        <li>Identifies eligible courses</li>
        <li>AI course recommendations</li>
        <li>Rate My Professor ratings</li>
        <li>PDF/Calendar exports</li>
        <li>Tracks graduation progress</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
        <h4 style="color: #0039A6; margin: 0;">⚠️ Limitations</h4>
        <ul style="margin: 1rem 0; padding-left: 1.5rem;">
        <li>Not official GSU software</li>
        <li>Verify with advisors</li>
        <li>Availability changes</li>
        <li>Suggestions only</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
        <h4 style="color: #0039A6; margin: 0;">🚀 Version Info</h4>
        <ul style="margin: 1rem 0; padding-left: 1.5rem;">
        <li><strong>Version:</strong> 0.2.0</li>
        <li><strong>Updated:</strong> January 2026</li>
        <li><strong>Majors:</strong> 6+</li>
        <li><strong>Courses:</strong> 500+</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div class='section-header'>📧 Feedback & Support</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="success-box">
    Found a bug? Have a suggestion? Want to contribute? Let us know!<br><br>
    This tool is built by and for GSU students. Your feedback helps us improve it.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='section-header'>❤️ Credits</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="course-card">
    Built with ❤️ by a GSU student, for GSU students.<br><br>
    Thanks to:<br>
    • Georgia State University for the course data<br>
    • OpenAI for AI-powered recommendations<br>
    • Rate My Professor for professor ratings<br>
    • Streamlit for the web framework<br>
    • The GSU community for feedback and support
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div class="footer">
    <p style="margin: 0.5rem 0;">⚠️ <strong>Not affiliated with Georgia State University</strong></p>
    <p style="margin: 0.5rem 0;">Always verify course plans with your academic advisor before registration</p>
    <p style="margin: 1rem 0; font-size: 0.9em; color: #999;">
    Built with ❤️ by a GSU student | v0.2.0 | Last Updated: January 2026
    </p>
</div>
""", unsafe_allow_html=True)
