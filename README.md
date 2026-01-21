# 🎓 GSU Course Planning AI

An AI-powered course planning assistant specifically for Georgia State University students that analyzes transcripts, recommends courses, and integrates Rate My Professor data.

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

1. **Upload Your Transcript**: Download your unofficial transcript from PAWS and upload it (PDF or TXT)
2. **Fill Out Preferences**: Tell the AI about your major, career goals, schedule constraints
3. **Generate Schedule**: Click the button and let the AI analyze and recommend courses
4. **Review Recommendations**: See your personalized course schedule with RMP ratings
5. **Export**: Download as PDF or add to your calendar

## 🏗️ Project Structure

```
gsu-course-planner/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment variables
├── .gitignore            # Git ignore file
├── README.md             # This file
├── utils/                # Helper functions (to be created)
│   ├── transcript_parser.py
│   ├── course_recommender.py
│   └── llm_integration.py
└── data/                 # Data files (to be created)
    ├── course_catalog.json
    └── degree_requirements.json
```

## 🛠️ Current Status

**Version:** 0.1.0 (MVP - Basic UI)

**What Works:**
- ✅ Basic Streamlit UI with all components
- ✅ File upload functionality
- ✅ Preference collection forms
- ✅ Mock schedule display

**In Progress:**
- 🔨 Transcript parsing (PDF/TXT)
- 🔨 Claude API integration
- 🔨 Rate My Professor scraping
- 🔨 Course catalog data collection
- 🔨 Degree requirements mapping

**Planned Features:**
- 📋 Support for multiple majors
- 🔍 Course seat availability tracking
- 📊 GPA impact predictions
- 📅 Summer/Winter session support
- 🌍 Study abroad integration

## 🤝 Contributing

This is a student project! If you're a GSU student and want to help:

1. Test the app and report bugs
2. Share your transcript format (anonymized) to improve parsing
3. Contribute course catalog data for your major
4. Suggest features or improvements

## ⚠️ Important Disclaimers

- **Not Official**: This is NOT official Georgia State University software
- **Verify Everything**: Always verify course plans with your academic advisor
- **Privacy**: We don't permanently store your transcript data
- **Accuracy**: Course recommendations are AI-generated and may have errors
- **No Guarantees**: We can't guarantee course availability or accuracy

## 📝 License

This project is for educational purposes. Not affiliated with Georgia State University.

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

Built with ❤️ by a GSU student, for GSU students.

**Current Development Phase:** Week 3-4 (MVP Development)
