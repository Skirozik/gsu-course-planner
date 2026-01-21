# 📋 TODO - Development Checklist

## ✅ COMPLETED
- [x] Project structure set up
- [x] Basic Streamlit UI created
- [x] File upload functionality
- [x] Student preference forms
- [x] Mock schedule display
- [x] README and documentation
- [x] Utility files scaffolded

## 🔄 IN PROGRESS - Week 3-4 (Current)

### High Priority (Do These First!)
- [ ] **Get Claude API Working**
  - [ ] Get API key from console.anthropic.com
  - [ ] Add key to .env file
  - [ ] Test llm_integration.py
  - [ ] Connect to app.py (replace mock data)
  
- [ ] **Test the App Locally**
  - [ ] Run `streamlit run app.py`
  - [ ] Upload a sample transcript (any PDF for now)
  - [ ] Fill out preferences form
  - [ ] Generate schedule (will use mock data for now)
  - [ ] Check if everything renders correctly

### Medium Priority (Next Week)
- [ ] **Transcript Parsing**
  - [ ] Get a real GSU transcript (yours or anonymized)
  - [ ] Study the format
  - [ ] Implement PDF parsing in transcript_parser.py
  - [ ] Extract: courses, grades, credits, GPA
  - [ ] Test with multiple transcript formats
  
- [ ] **Course Data Collection**
  - [ ] Find GSU's online course catalog
  - [ ] Create data/course_catalog.json
  - [ ] Add at least 20-30 CS courses
  - [ ] Include: code, name, credits, description, prerequisites
  - [ ] Add more majors later (start with yours)

- [ ] **Degree Requirements**
  - [ ] Document your major's requirements
  - [ ] Create data/degree_requirements.json
  - [ ] List all required courses
  - [ ] Note elective requirements
  - [ ] Add credit hour totals

### Lower Priority (Week 5-6)
- [ ] **Rate My Professor Integration**
  - [ ] Research RMP scraping/API options
  - [ ] Test scraping a few professors
  - [ ] Add to course recommendations
  - [ ] Display ratings in UI

- [ ] **Polish & Features**
  - [ ] Add progress bar for degree completion
  - [ ] Calculate actual graduation timeline
  - [ ] Add alternative course suggestions
  - [ ] Implement PDF export for schedule
  - [ ] Add error handling everywhere

## 📅 BACKLOG - Week 7+

### Testing & Refinement
- [ ] Test with real students (5-10 people)
- [ ] Collect feedback
- [ ] Fix bugs
- [ ] Improve recommendations

### Deployment
- [ ] Push to GitHub
- [ ] Deploy to Streamlit Cloud
- [ ] Test deployed version
- [ ] Share with GSU students

### Advanced Features (Future)
- [ ] Course seat availability tracking
- [ ] GPA impact predictions
- [ ] Summer/Winter session support
- [ ] Multiple majors support
- [ ] Mobile optimization
- [ ] Google Calendar integration

## 🎯 THIS WEEK'S GOAL

**Get the AI working with real API calls!**

1. Get Claude API key
2. Add to .env file
3. Run the app
4. Test schedule generation
5. Verify AI responses make sense

## 📝 Notes

- Start small! Get ONE thing working at a time
- Test frequently - don't write too much code before testing
- Ask for help when stuck
- Document what you learn

## 🐛 Known Issues

- [ ] Transcript parsing not implemented (using mock data)
- [ ] No real course data yet (using mock data)
- [ ] No RMP integration yet
- [ ] PDF export not implemented
- [ ] Calendar export not implemented

## 💡 Ideas for Later

- Add a "Compare Schedules" feature
- Let users save multiple schedule options
- Show course difficulty distribution chart
- Add "friends taking this class" feature
- Integration with PAWS/OSCAR if possible

---

**Remember:** Progress > Perfection. Get something working, then make it better!
