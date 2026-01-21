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

# Page config
st.set_page_config(
    page_title="GSU Course Planner",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS for GSU colors
st.markdown("""
    <style>
    .main-header {
        color: #0039A6;
        text-align: center;
        padding: 1rem 0;
    }
    .stButton>button {
        background-color: #0039A6;
        color: white;
        width: 100%;
    }
    .course-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Header
st.markdown("<h1 class='main-header'>🎓 GSU Course Planning Assistant</h1>", unsafe_allow_html=True)
st.markdown("### AI-powered course recommendations based on your academic evaluation")

# Disclaimer
with st.expander("⚠️ Important Disclaimer"):
    st.warning("""
    This is NOT official GSU software. Always verify course plans with your academic advisor.
    This tool is for planning purposes only and should not replace official academic advising.
    """)

# Initialize session state
if 'eval_data' not in st.session_state:
    st.session_state.eval_data = None
if 'schedule_generated' not in st.session_state:
    st.session_state.schedule_generated = False
if 'ai_recommendations' not in st.session_state:
    st.session_state.ai_recommendations = None
if 'selected_major' not in st.session_state:
    st.session_state.selected_major = None
if 'selected_school' not in st.session_state:
    st.session_state.selected_school = None

# Initialize catalog loader
catalog_loader = get_catalog_loader()

# Main content in tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Upload & Plan", "🔍 Prerequisite Lookup", "📚 Catalog Explorer", "ℹ️ How It Works", "📊 About"])

with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📄 Step 1: Upload Your Academic Evaluation")

        # File uploader
        uploaded_file = st.file_uploader(
            "Upload your Academic Evaluation PDF from DegreeWorks",
            type=['pdf'],
            help="Download this from PAWS > Student > DegreeWorks > Print/Save as PDF"
        )

        if uploaded_file:
            st.success(f"✅ File uploaded: {uploaded_file.name}")

            # Parse the academic evaluation
            with st.spinner("📊 Analyzing your academic evaluation..."):
                try:
                    file_content = uploaded_file.read()
                    st.session_state.eval_data = parse_academic_eval(file_content)
                    eval_data = st.session_state.eval_data

                    # Show parsed info
                    with st.expander("📋 Your Academic Summary", expanded=True):
                        info = eval_data["student_info"]
                        col_info1, col_info2 = st.columns(2)

                        with col_info1:
                            st.write(f"**Name:** {info['student_name']}")
                            st.write(f"**Major:** {info['major']}")

                        with col_info2:
                            st.write(f"**Credits:** {info['credits_applied']}/{info['credits_required']}")
                            progress_pct = (info['credits_applied'] / info['credits_required']) * 100
                            st.progress(progress_pct / 100)
                            st.write(f"**Progress:** {progress_pct:.1f}%")

                    # Show completed courses
                    with st.expander(f"✅ Completed Courses ({len(eval_data['completed_courses'])})"):
                        for course in eval_data["completed_courses"]:
                            st.write(f"- **{course['course_code']}**: {course['course_name']} ({course['grade']})")

                    # Show in-progress courses
                    if eval_data["in_progress_courses"]:
                        with st.expander(f"📚 Currently Enrolled ({len(eval_data['in_progress_courses'])})"):
                            for course in eval_data["in_progress_courses"]:
                                st.write(f"- **{course['course_code']}**: {course['course_name']} ({course['credits']} credits)")

                    # Show required courses
                    with st.expander(f"📝 Courses Still Needed ({len(eval_data['required_courses'])})"):
                        for req in eval_data["required_courses"]:
                            if req.get("is_elective"):
                                st.write(f"- {req['credits']} credits of electives: {req['courses'][0]}")
                            elif req.get("is_choice"):
                                st.write(f"- {req['credits']} credits: {' OR '.join(req['courses'])}")
                            else:
                                st.write(f"- **{req['courses'][0]}** ({req['credits']} credits)")

                except Exception as e:
                    st.error(f"Error parsing file: {str(e)}")
                    st.session_state.eval_data = None

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
            selected_major = st.selectbox(
                "Select Your Major",
                options=available_majors,
                help="Choose your degree program to get tailored recommendations"
            )
            st.session_state.selected_major = selected_major
            st.session_state.selected_school = selected_school

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
            st.session_state.schedule_generated = True
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
            
            except Exception as e:
                st.error(f"❌ Error generating schedule: {str(e)}")
                import traceback
                st.error(f"Debug info: {traceback.format_exc()}")
                st.session_state.schedule_generated = False
                use_ai = False
            
            # Only show success and results if no error occurred
            if st.session_state.schedule_generated:
                st.success("✅ Schedule Generated!")

                # Display student info summary
                info = eval_data["student_info"]
                st.markdown(f"#### 🎓 Recommendations for {info['student_name']}")

                # Show AI recommendations or fallback
                if use_ai and st.session_state.ai_recommendations:
                    ai_recs = st.session_state.ai_recommendations

                    if ai_recs.get("recommended_courses"):
                        st.markdown("##### Recommended Courses")
                        for course in ai_recs["recommended_courses"][:max_courses]:
                            with st.container():
                                st.markdown(f"""
                                **{course.get('course_code', 'N/A')}** - {course.get('course_name', 'N/A')}
                                - Difficulty: {course.get('difficulty', 'N/A')}
                                - Reason: {course.get('reason', 'Required for major')}
                                """)
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
                st.markdown("#### 📥 Export")

                if st.session_state.ai_recommendations:
                    export_data = json.dumps(st.session_state.ai_recommendations, indent=2)
                    st.download_button(
                        "📄 Download Recommendations (JSON)",
                        data=export_data,
                        file_name="gsu_schedule_recommendations.json",
                        mime="application/json"
                    )

        elif submit_button and not st.session_state.eval_data:
            st.warning("⚠️ Please upload your academic evaluation first.")

        elif not submit_button and not st.session_state.schedule_generated:
            st.info("👆 Upload your academic evaluation and click 'Generate My Schedule' to get started.")

    # Add catalog-based recommendations section if major is selected
    if st.session_state.eval_data and st.session_state.selected_major:
        st.markdown("---")
        st.markdown("### 📚 Catalog-Based Recommendations")

        eval_data = st.session_state.eval_data
        major = st.session_state.selected_major

        # Get completed courses
        completed_courses = [c['course_code'] for c in eval_data['completed_courses']]

        # Show degree progress
        col_prog1, col_prog2, col_prog3 = st.columns(3)

        with col_prog1:
            progress_info = catalog_loader.get_degree_progress(major, completed_courses)
            st.metric("Core Courses", progress_info['core_progress'])

        with col_prog2:
            st.metric("Math Courses", progress_info['math_progress'])

        with col_prog3:
            st.metric("Completion", f"{progress_info['completion_percentage']}%")

        # Show next available courses based on catalog
        st.markdown("#### 🟢 Courses You Can Take Now")

        next_courses = catalog_loader.get_recommended_next_courses(major, completed_courses, limit=8)

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
            core_courses = catalog_loader.get_core_courses(major)
            completed_core = [c for c in core_courses if c['course_code'] in completed_courses]
            pending_core = [c for c in core_courses if c['course_code'] not in completed_courses]

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Completed:**")
                if completed_core:
                    for course in completed_core:
                        st.markdown(f"✅ {course['course_code']}: {course['course_name']}")
                else:
                    st.markdown("*None yet*")

            with col2:
                st.markdown("**Still Needed:**")
                if pending_core:
                    for course in pending_core:
                        st.markdown(f"⏳ {course['course_code']}: {course['course_name']}")
                else:
                    st.success("✅ All core courses completed!")

        with req_tab2:
            electives = catalog_loader.get_elective_courses(major)
            if electives:
                st.markdown("Choose electives based on your interests:")
                for elective in electives:
                    can_take = catalog_loader.check_prerequisites_met(
                        major, elective['course_code'], completed_courses
                    )['can_take']
                    status = "✅ Available" if can_take else "🔒 Prerequisites needed"
                    st.markdown(f"- **{elective['course_code']}**: {elective['course_name']} - {status}")
            else:
                st.info("No electives defined for this major.")

        with req_tab3:
            math_reqs = catalog_loader.get_math_requirements(major)
            if math_reqs:
                completed_math = [m for m in math_reqs if m['course_code'] in completed_courses]
                pending_math = [m for m in math_reqs if m['course_code'] not in completed_courses]

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Completed:**")
                    if completed_math:
                        for course in completed_math:
                            st.markdown(f"✅ {course['course_code']}: {course['course_name']}")
                    else:
                        st.markdown("*None yet*")

                with col2:
                    st.markdown("**Still Needed:**")
                    if pending_math:
                        for course in pending_math:
                            st.markdown(f"⏳ {course['course_code']}: {course['course_name']}")
                    else:
                        st.success("✅ All math requirements completed!")

with tab3:
    st.markdown("### 📚 Catalog Explorer")
    st.markdown("Browse and explore courses for each major program at GSU.")

    # Major selector
    explorer_major = st.selectbox(
        "Select a Major to Explore",
        options=catalog_loader.get_available_majors(),
        key="catalog_explorer_major"
    )

    if explorer_major:
        # Get catalog info
        catalog = catalog_loader.get_catalog(explorer_major)
        metadata = catalog.get("metadata", {})

        # Header
        st.markdown(f"## {metadata.get('major', explorer_major)}")
        st.markdown(f"**Degree Type:** {metadata.get('degree_type', 'N/A')} | "
                    f"**Total Credits Required:** {metadata.get('total_credits_required', 'N/A')}")

        st.markdown("---")

        # Tabs for different course types
        cat_tab1, cat_tab2, cat_tab3 = st.tabs(["Core Courses", "Electives", "All Courses"])

        with cat_tab1:
            core_courses = catalog_loader.get_core_courses(explorer_major)
            st.markdown(f"### Required Core Courses ({len(core_courses)} courses)")

            for course in core_courses:
                with st.expander(f"**{course['course_code']}**: {course['course_name']} ({course['credits']} credits)"):
                    st.markdown(course['description'])

                    prereqs = catalog_loader.get_prerequisites(explorer_major, course['course_code'])
                    if prereqs:
                        st.markdown(f"**Prerequisites:** {', '.join(prereqs)}")
                    else:
                        st.markdown("**Prerequisites:** None")

        with cat_tab2:
            electives = catalog_loader.get_elective_courses(explorer_major)
            st.markdown(f"### Elective Courses ({len(electives)} courses)")

            for course in electives:
                with st.expander(f"**{course['course_code']}**: {course['course_name']} ({course['credits']} credits)"):
                    st.markdown(course['description'])

                    prereqs = catalog_loader.get_prerequisites(explorer_major, course['course_code'])
                    if prereqs:
                        st.markdown(f"**Prerequisites:** {', '.join(prereqs)}")
                    else:
                        st.markdown("**Prerequisites:** None")

        with cat_tab3:
            all_courses = catalog_loader.get_all_courses_for_major(explorer_major)
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
    st.markdown("""
    ### 🔍 How This Works

    This AI-powered tool helps you plan your course schedule by:

    1. **📄 Analyzing Your Academic Evaluation**
       - Extracts completed courses and grades
       - Identifies remaining degree requirements
       - Checks which prerequisites you've satisfied
       - Finds courses you're eligible to take

    2. **🎯 Understanding Your Preferences**
       - Career goals and interests
       - Schedule constraints (work, preferred times)
       - Course load preferences

    3. **🤖 AI-Powered Recommendations**
       - Uses GPT-4 to analyze your specific situation
       - Matches available courses to your needs
       - Balances difficulty across your schedule
       - Optimizes your path to graduation

    4. **📊 Smart Planning**
       - Shows degree progress
       - Predicts graduation timeline
       - Suggests alternative courses
       - Respects prerequisite chains

    ### 📥 How to Get Your Academic Evaluation

    1. Log into **PAWS** (paws.gsu.edu)
    2. Go to **Student** tab
    3. Click **DegreeWorks**
    4. Click **Print** or save as PDF
    5. Upload the PDF here!

    ### 🔒 Privacy & Data

    - Your data is processed in your browser session only
    - We don't permanently store your personal information
    - The AI sees only what's needed for recommendations
    - Close the browser to clear all data
    """)

with tab5:
    st.markdown("""
    ### 📊 About This Project

    **GSU Course Planning AI** is a student-built tool designed to help Georgia State University
    students make better course planning decisions.

    #### 🎯 What It Does
    - Parses DegreeWorks academic evaluations
    - Identifies courses you can take (prerequisites met)
    - Uses AI to recommend optimal course combinations
    - Tracks your progress toward graduation

    #### ⚠️ Limitations
    - Not official GSU software
    - Recommendations should be verified with advisors
    - Course availability changes each semester
    - AI recommendations are suggestions, not guarantees

    #### 🚀 Version
    - **Current Version:** 0.2.0
    - **Last Updated:** January 2026
    - **Supported:** Computer Science majors (more coming!)

    #### 📧 Feedback
    Found a bug? Have a suggestion? Let us know!

    ---

    Built with ❤️ by a GSU student, for GSU students.
    """)

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>⚠️ Not affiliated with Georgia State University | "
    "Always verify course plans with your academic advisor</p>",
    unsafe_allow_html=True
)
