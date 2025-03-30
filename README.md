EventHub - Event Management and Chatbot Platform

Problem Statement:
Organizing and managing events can be a complex task for both organizers and attendees. Event organizers need a platform to create events, track registrations, monitor crowd density at stalls, and analyze feedback, while attendees require an easy way to discover events, register, and get real-time information. Existing solutions often lack an integrated, user-friendly interface with intelligent assistance, such as a chatbot that provides event-specific information and quick options for common queries. The challenge was to build a web application that addresses these needs with a seamless UI, database-driven event management, and a chatbot restricted to event-related responses.

Solution:
EventHub is a Flask-based web application designed to streamline event management and enhance user experience. It offers features like event creation, user registration, interest-based recommendations, crowd monitoring, feedback analysis, and an AI-powered chatbot named EventBuddy. The chatbot supports two modes: a free-text "Chat" option for event-related queries (e.g., "What’s the venue of Tech Fest?") and a "Quick Options" mode for predefined queries (e.g., "List all events"). EventBuddy fetches data from an SQLite database and ensures responses are event-focused, replying "I can only provide information about events" for off-topic queries. The application integrates a modern UI with animations, secure user sessions, and real-time data processing.

Features:
Event Management: Create, view, and register for events with details stored in an SQLite database.
User Profiles: Register users with interests for personalized event recommendations.
Recommendations: Interest-based, mood-based, and trend-based event suggestions using TextBlob for sentiment analysis.
Crowd Monitoring: Real-time stall crowd density visualization using Folium maps.
Feedback System: Collect and analyze feedback, with AI-generated performance insights and stall suggestions.
Chatbot (EventBuddy): Dual-mode chatbot (Chat and Quick Options) powered by Groq API, restricted to event-related responses.
Admin Dashboard: Manage feedback with display and delete options.
Responsive UI: Animated, mobile-friendly design with CSS and JavaScript.

Prerequisites:
Before setting up EventHub, ensure you have the following installed:
Python 3.8+: Core programming language.
pip: Python package manager.
SQLite: Lightweight database (included with Python).
Git: For cloning the repository (optional).

Installation Steps
1.Clone the Repository (if applicable):
git clone <repository-url>
cd EventHub

2.Create a Virtual Environment:

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3.Install Required Libraries: Install all dependencies listed in the "Libraries Used" section:

pip install flask flask-cors groq pandas geopy folium textblob

4.Set Up the Groq API Key:
Sign up at Groq and obtain an API key.
Replace the placeholder in app.py:

GROQ_API_KEY = "your_actual_groq_api_key_here"

5.Initialize the Database and CSV:

Run the app once to create emr.db and feedback.csv:

python app.py

Stop the app (Ctrl+C) after initialization.

6.Add Sample Data (Optional):

Open emr.db with an SQLite client (e.g., DB Browser for SQLite) and insert test data:

INSERT INTO users (name, email, interests) VALUES ('John Doe', 'john@example.com', 'Technology,Music');
INSERT INTO events (title, date, venue, description, category, created_by) VALUES ('Tech Fest', '2025-04-15', 'Downtown Convention Center', 'A tech showcase.', 'Technology', 1);

Running the Application:

1.Activate the Virtual Environment (if not already active):

source venv/bin/activate  # On Windows: venv\Scripts\activate

2.Start the Flask Server:
python app.py

3.Access the App:
Open a browser and go to http://127.0.0.1:5000/.
Register a user to get a User ID, then log in to access features.

Usage Instructions:
Home Page: View the latest events.
Register/Login: Create a profile or log in with your User ID.
Events: Browse and register for events.
Add Event: Create new events (requires login).
Recommendations: Get personalized event suggestions.
Feedback: Submit feedback for events or stalls.
Performance Insights: Analyze event feedback (AI-generated).
Stall Suggestions: Get AI suggestions for stall improvements.
Crowd Monitor: View stall crowd density on a map.
Admin Dashboard: Manage feedback (password: admin123).
Chatbot:
Chat Mode: Ask event-related questions (e.g., "What’s the venue of Tech Fest?").
Quick Options: Toggle the button to select predefined queries (e.g., "List all events").
Non-event queries return: "I can only provide information about events."

Libraries and APIs Used:
Flask: Web framework for routing and templating (pip install flask).
Flask-CORS: Enable Cross-Origin Resource Sharing (pip install flask-cors).
SQLite3: Built-in Python library for database management.
Groq: AI API for chatbot responses and text generation (pip install groq).
API Key: Required for chatbot functionality (set in GROQ_API_KEY).
Pandas: Data manipulation for feedback storage and analysis (pip install pandas).
Geopy: Calculate distances for crowd monitoring (pip install geopy).
Folium: Generate interactive maps for crowd visualization (pip install folium).
TextBlob: Sentiment analysis for mood-based recommendations (pip install textblob).
Datetime/Math: Built-in Python libraries for date handling and calculations.

Project Structure:
EventHub/
├── static/
│   ├── css/
│   │   └── styles.css    # CSS for UI styling
│   ├── js/
│   │   └── scripts.js    # JavaScript for interactivity
│   └── images/
│       └── logo.png      # Logo image (add your own)
├── templates/
│   ├── index.html        # Home page
│   ├── register.html     # User registration
│   ├── events.html       # Event listing
│   ├── my_events.html    # User’s registered events
│   ├── recommendations.html # Event recommendations
│   ├── add_event.html    # Add new event
│   ├── feedback.html     # Feedback form
│   ├── performance_insights.html # Feedback analysis
│   ├── stall_suggestions.html # Stall improvement suggestions
│   ├── crowd_monitor.html # Crowd density map
│   ├── admin_dashboard.html # Admin feedback management
│   └── chatbot.html      # Chatbot interface
├── app.py                # Main Flask application
├── emr.db                # SQLite database (auto-generated)
├── feedback.csv          # Feedback storage (auto-generated)
└── README.md             # This file

Troubleshooting:
Chatbot Not Working: Verify the Groq API key and internet connection. Check app.py logs for errors.
No Events Displayed: Ensure emr.db has data in the events table.
UI Issues: Confirm styles.css and scripts.js are in the static folder and loaded correctly.
Database Errors: Delete emr.db and rerun app.py to reinitialize.
