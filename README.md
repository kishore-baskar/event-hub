# EventHub - Event Management and Chatbot Platform

## Problem Statement:
Overcrowding and poor crowd management are major challenges in event management, leading to discomfort, safety risks, and inefficient movement. Stall owners struggle without real-time insights into foot traffic, impacting their sales. Organizers lack proper feedback systems, missing opportunities for improvement. Attendees also face difficulties accessing event information. A solution for solving these problems effectively using Al and a clean and user friendly software.

## Solution:
Our Project "EventHub" will provide an Al-driven platform that transforms event experiences. It tackles overcrowding with Crowd Flow Optimization, by providing analytical description and stats with real-time insights for effecient monitoring to both users and vendors. Smart Stall Recommendations using semantic and interest-based algorithms using NLP models which also includes summarization of big chunks of reviews for an event using Al models. A Chatbot for seamless interaction of all the features in the platform, and Data-Driven Insights for organizers and vendors. Built with scalability in mind, it adapts to events of all sizes (specificly big size events), while its technical feasibility ensures practical implementation, making it a robust solution for enhancing event management.

## Features:
- Event Management: Create, view, and register for events with details stored in an SQLite database.
- User Profiles: Register users with interests for personalized event recommendations.
- Recommendations: Interest-based, mood-based, and trend-based event suggestions using TextBlob for sentiment analysis.
- Crowd Monitoring: Real-time stall crowd density visualization using Folium maps.
- Feedback System: Collect and analyze feedback, with AI-generated performance insights and stall suggestions.
- Chatbot (EventBuddy): Dual-mode chatbot (Chat and Quick Options) powered by Groq API, restricted to event-related responses.
- Admin Dashboard: Manage feedback with display and delete options.
- Responsive UI: Animated, mobile-friendly design with CSS and JavaScript.

## Prerequisites:
Before setting up EventHub, ensure you have the following installed:
- Python 3.8+: Core programming language.
- pip: Python package manager.
- SQLite: Lightweight database (included with Python).
- Git: For cloning the repository (optional).

## Installation Steps
1. Clone the Repository (if applicable):
```
git clone <repository-url>
cd EventHub
```

2. Create a Virtual Environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Required Libraries: Install all dependencies listed in the "Libraries Used" section:
```
pip install flask flask-cors groq pandas geopy folium textblob
```

4. Set Up the Groq API Key:
- Sign up at Groq and obtain an API key.
- Replace the placeholder in app.py:
```
GROQ_API_KEY = "your_actual_groq_api_key_here"
```

5. Initialize the Database and CSV:
- Run the app once to create emr.db and feedback.csv:
```
python app.py
```
- Stop the app (Ctrl+C) after initialization.

6. Add Sample Data (Optional):
- Open emr.db with an SQLite client (e.g., DB Browser for SQLite) and insert test data:
```
INSERT INTO users (name, email, interests) VALUES ('John Doe', 'john@example.com', 'Technology,Music');
INSERT INTO events (title, date, venue, description, category, created_by) VALUES ('Tech Fest', '2025-04-15', 'Downtown Convention Center', 'A tech showcase.', 'Technology', 1);
```

## Running the Application:

1. Activate the Virtual Environment (if not already active):
```
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Start the Flask Server:
```
python app.py
```

3. Access the App:
- Open a browser and go to http://127.0.0.1:5000/.
- Register a user to get a User ID, then log in to access features.

## Usage Instructions:
- Home Page: View the latest events.
- Register/Login: Create a profile or log in with your User ID.
- Events: Browse and register for events.
- Add Event: Create new events (requires login).
- Recommendations: Get personalized event suggestions.
- Feedback: Submit feedback for events or stalls.
- Performance Insights: Analyze event feedback (AI-generated).
- Stall Suggestions: Get AI suggestions for stall improvements.
- Crowd Monitor: View stall crowd density on a map.
- Admin Dashboard: Manage feedback (password: admin123).
- Chatbot:
  - Chat Mode: Ask event-related questions (e.g., "What's the venue of Tech Fest?").
  - Quick Options: Toggle the button to select predefined queries (e.g., "List all events").
  - Non-event queries return: "I can only provide information about events."

## Libraries and APIs Used:
- Flask: Web framework for routing and templating (pip install flask).
- Flask-CORS: Enable Cross-Origin Resource Sharing (pip install flask-cors).
- SQLite3: Built-in Python library for database management.
- Groq: AI API for chatbot responses and text generation (pip install groq).
- API Key: Required for chatbot functionality (set in GROQ_API_KEY).
- Pandas: Data manipulation for feedback storage and analysis (pip install pandas).
- Geopy: Calculate distances for crowd monitoring (pip install geopy).
- Folium: Generate interactive maps for crowd visualization (pip install folium).
- TextBlob: Sentiment analysis for mood-based recommendations (pip install textblob).
- Datetime/Math: Built-in Python libraries for date handling and calculations.

## Troubleshooting:
- Chatbot Not Working: Verify the Groq API key and internet connection. Check app.py logs for errors.
- No Events Displayed: Ensure emr.db has data in the events table.
- UI Issues: Confirm styles.css and scripts.js are in the static folder and loaded correctly.
- Database Errors: Delete emr.db and rerun app.py to reinitialize.

## One drive link for demo video:
-https://1drv.ms/v/c/e15e1adba3d259a7/EUbb1wTT3nxFoZNDnBLY9v0BfLgR-aY9v9PJX-IEnVo0Zw?e=40f1hs
