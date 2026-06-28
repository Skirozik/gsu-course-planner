# 🎓 GSU & Georgia Tech Course Planning AI

An AI-powered course planning assistant for Georgia State University and Georgia Tech students that analyzes transcripts, recommends courses, and integrates Rate My Professor data.

## ✨ Features

- 📄 **Transcript Analysis**: Upload your transcript and automatically extract completed courses
- 🎯 **Smart Recommendations**: AI-powered course suggestions based on degree requirements
- ⭐ **Rate My Professor Integration**: See professor ratings alongside course recommendations
- 📊 **Progress Tracking**: Visual degree completion progress
- 📅 **Graduation Timeline**: Predict when you'll graduate based on your course load
- ⚖️ **Difficulty Balancing**: Distribute challenging courses across semesters
- 🎨 **Personalized**: Takes into account work schedule, learning style, and career goals

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- A Claude API key (get one at https://console.anthropic.com/)

### Installation

1. **Clone or download this repository**

2. **Navigate to the project directory**
   ```bash
   cd gsu-course-planner
   ```

3. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On Mac/Linux:
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up your API key**
   
   Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` and add your API key:
   ```
   ANTHROPIC_API_KEY=your_actual_api_key_here
   ```

6. **Run the app**
   ```bash
   streamlit run app.py
   ```

7. **Open your browser**
   
   The app should automatically open at `http://localhost:8501`

## 📖 How to Use

1. **Upload Your Academic Evaluation**: Export your DegreeWorks evaluation as a PDF (GSU: PAWS → DegreeWorks; Georgia Tech: OSCAR → DegreeWorks) and upload it
2. **Fill Out Preferences**: Tell the AI about your major, career goals, schedule constraints
3. **Generate Schedule**: Click the button and let the AI analyze and recommend courses
4. **Review Recommendations**: See your personalized course schedule with RMP ratings
5. **Export**: Download as PDF or add to your calendar

## 🏗️ Project Structure

```
gsu-course-planner/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment variables
├── README.md                   # This file
├── utils/                      # Application logic
│   ├── academic_eval_parser.py # Parse GSU DegreeWorks PDFs
│   ├── gatech_parser.py        # Parse Georgia Tech DegreeWorks PDFs
│   ├── catalog_loader.py       # Load/normalize course catalogs
│   ├── llm_integration.py      # Claude (Anthropic) recommendations
│   ├── rmp_integration.py      # Rate My Professors GraphQL client
│   ├── professor_ranking.py    # Rank sections by professor quality
│   ├── section_recommender.py  # Tie RMP rankings to course sections
│   ├── gsu_banner_api.py       # Live GSU section data (Banner API)
│   ├── gatech_banner_api.py    # Live Georgia Tech section data
│   ├── prerequisites.py        # Prerequisite graph / lookups
│   └── export_utils.py         # PDF / iCalendar / text exports
└── data/                       # Course catalogs, sections, prerequisites
    └── course_catalogs/        # One JSON catalog per major
```

## 🛠️ Current Status

**Version:** 0.2.0

**What Works:**
- ✅ DegreeWorks PDF parsing for Georgia State **and** Georgia Tech
- ✅ Claude (Anthropic) AI course recommendations
- ✅ Rate My Professors integration with section ranking
- ✅ Live section lookups via the schools' Banner APIs
- ✅ Prerequisite lookup and catalog explorer
- ✅ PDF / calendar (.ics) / text schedule exports

**Planned Features:**
- 🔍 Course seat-availability tracking
- 📊 GPA impact predictions
- 🌍 Additional majors and schools

## 🤝 Contributing

This is a student project! If you're a GSU or Georgia Tech student and want to help:

1. Test the app and report bugs
2. Share your transcript format (anonymized) to improve parsing
3. Contribute course catalog data for your major
4. Suggest features or improvements

## ⚠️ Important Disclaimers

- **Not Official**: This is NOT official Georgia State University or Georgia Tech software
- **Verify Everything**: Always verify course plans with your academic advisor
- **Privacy**: We don't permanently store your transcript data
- **Accuracy**: Course recommendations are AI-generated and may have errors
- **No Guarantees**: We can't guarantee course availability or accuracy

## 📝 License

This project is for educational purposes. Not affiliated with Georgia State University or Georgia Tech.

## 🆘 Troubleshooting

**App won't start?**
- Make sure you've activated your virtual environment
- Check that all dependencies are installed: `pip install -r requirements.txt`

**API errors?**
- Verify your `.env` file has the correct API key
- Check that you have API credits remaining

**Transcript won't upload?**
- Make sure it's a PDF or TXT file
- Check file size (keep under 10MB)

## 📧 Contact

Questions? Feedback? Found a bug?

- Open an issue on GitHub
- Or use the feedback form in the app

---

Built with ❤️ by a GSU student, for GSU and Georgia Tech students.

**Current Development Phase:** Week 3-4 (MVP Development)
