# 🚀 QUICKSTART GUIDE

## Get Running in 5 Minutes!

### Step 1: Get Your API Key
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy it (you'll need it in Step 3)

### Step 2: Setup the Project

**On Windows:**
```bash
# Double-click setup.bat
# OR run in Command Prompt:
setup.bat
```

**On Mac/Linux:**
```bash
# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh
```

### Step 3: Add Your API Key

1. Open the `.env` file in a text editor
2. Replace `your_claude_api_key_here` with your actual API key:
   ```
   ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
   ```
3. Save the file

### Step 4: Run the App

**Activate virtual environment first:**

Windows:
```bash
venv\Scripts\activate
```

Mac/Linux:
```bash
source venv/bin/activate
```

**Then run:**
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 🎯 Quick Test

1. Click on "📋 Upload & Plan" tab
2. Fill out the student preferences form:
   - Select your major
   - Add some career goals
   - Choose your preferred class times
3. Click "🚀 Generate My Schedule"
4. See the mock schedule (AI integration coming next!)

## ⚠️ Troubleshooting

**"ANTHROPIC_API_KEY not found"**
- Make sure you created the `.env` file
- Make sure you added your API key without quotes
- Make sure the file is named exactly `.env` (not `.env.txt`)

**"Module not found" errors**
- Make sure virtual environment is activated
- Run: `pip install -r requirements.txt`

**Port already in use**
- Streamlit is already running
- Close other Streamlit instances
- Or use: `streamlit run app.py --server.port 8502`

## 📝 What's Working Now

✅ **Working:**
- Beautiful Streamlit UI with GSU branding
- File upload interface
- Student preference forms
- Mock schedule display
- All tabs and sections

🔨 **In Progress (Next Steps):**
- Actual transcript parsing
- Claude API integration
- Rate My Professor data
- Real course recommendations

## 🎓 Next Steps

Once you have the app running, check out the full README.md for:
- How to contribute
- Development roadmap
- API integration guide
- Deployment instructions

## 💡 Pro Tips

1. **Keep the terminal open** - Streamlit needs it running
2. **Auto-reload** - Streamlit watches for file changes and reloads automatically
3. **Use the sidebar** - Streamlit adds useful debugging info there
4. **Check the logs** - Look at the terminal for error messages

## 🆘 Need Help?

- Check the main README.md for detailed documentation
- Look at the Notion project plan
- Ask in the GSU CS Discord

---

Built with ❤️ for GSU students. Happy coding! 🎉
