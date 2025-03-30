import sqlite3
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime, timedelta
import pandas as pd
from geopy.distance import geodesic
import folium
from flask_cors import CORS
from groq import Groq
import math
from textblob import TextBlob
from threading import Lock
from collections import defaultdict
import csv

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a secure key
CORS(app)

# Constants
CATEGORIES = ["Technology", "Music", "Sports", "Art", "Business", "Games", "Movies", "Food", "Products"]
MOOD_MAPPING = {"positive": ["Sports", "Music", "Games"], "negative": ["Art"], "neutral": CATEGORIES}
FEEDBACK_FILE = "feedback.csv"
STALLS = ["Food Stall", "Tech Stall", "Merchandise Stall", "Game Stall"]
GROQ_API_KEY = "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"
co = Groq(api_key=GROQ_API_KEY)

# CSV file paths for crowd monitoring
USER_ID_INTERESTS_FILE = "user_id_interests.csv"
STALL_PEOPLE_COUNT_FILE = "stall_people_count.csv"
STALLS_FILE = "stalls.csv"
USER_LOCATIONS_FILE = "user_locations.csv"
STALL_CATEGORIES_FILE = "stall_categories.csv"

# Thread lock for file operations
file_lock = Lock()

# Database connection
def get_db_connection():
    conn = sqlite3.connect('emr.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database with all tables
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        interests TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        date TEXT,
        venue TEXT,
        description TEXT,
        category TEXT NOT NULL,
        created_by INTEGER,
        FOREIGN KEY (created_by) REFERENCES users(id)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        event_id INTEGER,
        registration_date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (event_id) REFERENCES events(id)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS stalls (
        user_id INTEGER PRIMARY KEY,
        stall_name TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_locations (
        user_id INTEGER PRIMARY KEY,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        timestamp TEXT NOT NULL
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS stall_categories (
        stall_name TEXT PRIMARY KEY,
        category TEXT
    )''')
    conn.commit()
    conn.close()

# Initialize CSV files
def initialize_csv():
    if not os.path.exists(FEEDBACK_FILE):
        pd.DataFrame(columns=["name", "feedback", "event", "rating", "response"]).to_csv(FEEDBACK_FILE, index=False)
    with file_lock:
        if not os.path.exists(USER_ID_INTERESTS_FILE):
            with open(USER_ID_INTERESTS_FILE, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["id", "interests"])
        if not os.path.exists(STALL_PEOPLE_COUNT_FILE):
            with open(STALL_PEOPLE_COUNT_FILE, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["stall_name", "people_count"])
        if not os.path.exists(STALLS_FILE):
            with open(STALLS_FILE, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["user_id", "stall_name", "latitude", "longitude"])
        if not os.path.exists(USER_LOCATIONS_FILE):
            with open(USER_LOCATIONS_FILE, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["user_id", "latitude", "longitude", "timestamp"])
        if not os.path.exists(STALL_CATEGORIES_FILE):
            with open(STALL_CATEGORIES_FILE, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["stall_name", "category"])

# Database utility functions (unchanged)
def get_all_events():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events ORDER BY id DESC")
    events = cursor.fetchall()
    conn.close()
    return events

def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_user(name, email, interests):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name, email, interests) VALUES (?, ?, ?)",
                   (name, email, ",".join(interests)))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id

def add_event(title, date, venue, description, category, created_by):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO events (title, date, venue, description, category, created_by) VALUES (?, ?, ?, ?, ?, ?)",
                   (title, date, venue, description, category, created_by))
    conn.commit()
    event_id = cursor.lastrowid
    conn.close()
    return event_id

def register_for_event(user_id, event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registrations WHERE user_id = ? AND event_id = ?", (user_id, event_id))
    if cursor.fetchone():
        conn.close()
        return False
    cursor.execute("INSERT INTO registrations (user_id, event_id, registration_date) VALUES (?, ?, CURRENT_TIMESTAMP)", (user_id, event_id))
    conn.commit()
    conn.close()
    return True

def get_user_registrations(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT e.* FROM events e JOIN registrations r ON e.id = r.event_id WHERE r.user_id = ?", (user_id,))
    registrations = cursor.fetchall()
    conn.close()
    return registrations

def get_interest_based_events(user_id):
    user = get_user(user_id)
    if not user or not user['interests']:
        return []
    interests = user['interests'].split(',')
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM events WHERE category IN ({})".format(','.join('?' * len(interests)))
    cursor.execute(query, interests)
    recommended = cursor.fetchall()
    conn.close()
    return recommended

def get_mood_based_events(mood_input):
    if not mood_input:
        return []
    blob = TextBlob(mood_input)
    sentiment = blob.sentiment.polarity
    mood = "positive" if sentiment > 0.3 else "negative" if sentiment < -0.3 else "neutral"
    mood_categories = MOOD_MAPPING[mood]
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM events WHERE category IN ({})".format(','.join('?' * len(mood_categories)))
    cursor.execute(query, mood_categories)
    mood_events = cursor.fetchall()
    conn.close()
    return mood_events

def calculate_trend_scores(user_id, decay_rate=0.02):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.category, r.registration_date, r.id 
        FROM registrations r 
        JOIN events e ON r.event_id = e.id 
        WHERE r.user_id = ?
    """, (user_id,))
    bookings = cursor.fetchall()
    conn.close()
    
    if not bookings:
        return {}
    
    category_scores = {}
    current_date = datetime.now()
    
    booking_ids = [booking['id'] for booking in bookings if 'id' in booking and booking['id'] is not None]
    if not booking_ids:
        return {}
    
    min_id = min(booking_ids)
    max_id = max(booking_ids)
    id_range = max_id - min_id if max_id > min_id else 1
    
    for booking in bookings:
        try:
            category = booking['category']
            reg_date_str = booking["registration_date"]
            if reg_date_str:
                reg_date = datetime.strptime(reg_date_str, "%Y-%m-%d %H:%M:%S")
            else:
                days_ago = int((max_id - booking['id']) * 90 / id_range)
                reg_date = current_date - timedelta(days=days_ago)
            
            days_ago = max((current_date - reg_date).days, 0)
            weight = math.exp(-decay_rate * days_ago)
            category_scores[category] = category_scores.get(category, 0) + weight
        except Exception:
            continue
    
    return category_scores

def get_trend_based_events(user_id):
    scores = calculate_trend_scores(user_id)
    if not scores:
        return []
    top_category = max(scores, key=scores.get)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT * 
        FROM events 
        WHERE category = ? AND date > ? 
        ORDER BY date ASC 
        LIMIT 3
    """, (top_category, current_date_str))
    recommendations = cursor.fetchall()
    conn.close()
    return recommendations

def generate_event_description(title, date, venue, category):
    prompt = f"Generate a concise event description (2-3 sentences) for an event with the following details:\n" \
             f"Title: {title}\n" \
             f"Date: {date}\n" \
             f"Venue: {venue if venue else 'TBD'}\n" \
             f"Category: {category}\n" \
             f"Highlight the event's purpose and appeal."
    try:
        response = co.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating description: {str(e)}"

# New crowd monitoring backend functions
def update_stall_people_count():
    stalls = []
    users = []
    
    with file_lock:
        if os.path.exists(STALLS_FILE):
            with open(STALLS_FILE, mode='r') as file:
                reader = csv.reader(file)
                next(reader)
                stalls = [{'stall_id': row[0], 'stall_name': row[1], 'latitude': float(row[2]), 'longitude': float(row[3])} 
                          for row in reader if row and len(row) >= 4]
        
        if os.path.exists(USER_LOCATIONS_FILE):
            with open(USER_LOCATIONS_FILE, mode='r') as file:
                reader = csv.reader(file)
                next(reader)
                users = [{'user_id': row[0], 'latitude': float(row[1]), 'longitude': float(row[2])} 
                         for row in reader if row and len(row) >= 3]
    
    if not stalls:
        return {"default": {"crowd_count": 0, "crowd_level": "Very Low", "latitude": 12.8225, "longitude": 80.2250}}
    
    stall_crowd = {}
    for stall in stalls:
        count = sum(1 for user in users if geodesic((stall["latitude"], stall["longitude"]), 
                                                    (user["latitude"], user["longitude"])).meters <= 50)
        level = "Very Low" if count <= 1 else "Low" if count <= 3 else "Medium" if count <= 5 else "High" if count <= 7 else "Very High"
        stall_crowd[stall["stall_name"]] = {
            "crowd_count": count,
            "crowd_level": level,
            "latitude": stall["latitude"],
            "longitude": stall["longitude"]
        }
    
    with file_lock:
        with open(STALL_PEOPLE_COUNT_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["stall_name", "people_count"])
            for stall_name, details in stall_crowd.items():
                writer.writerow([stall_name, details["crowd_count"]])
    
    return stall_crowd

def get_user_interests_from_csv(user_id):
    if not os.path.exists(USER_ID_INTERESTS_FILE):
        return set()
    
    with file_lock:
        with open(USER_ID_INTERESTS_FILE, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                if row[0] == str(user_id):
                    interests = row[1].split(",") if row[1] else []
                    return set(interest.strip().lower() for interest in interests)
    return set()

def get_stall_categories():
    categories = {}
    if os.path.exists(STALL_CATEGORIES_FILE):
        with file_lock:
            with open(STALL_CATEGORIES_FILE, mode='r') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                for row in reader:
                    categories[row[0].lower()] = row[1].lower() if row[1] else ""
    return categories

def suggest_best_stall(user_id):
    stall_counts = {}
    if os.path.exists(STALL_PEOPLE_COUNT_FILE):
        with file_lock:
            with open(STALL_PEOPLE_COUNT_FILE, mode='r') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 2:
                        stall_counts[row[0]] = int(row[1] if row[1] else 0)
    
    if not stall_counts:
        return {"stall": None, "reason": "No stall data available"}
    
    user_interests = get_user_interests_from_csv(user_id)
    if not user_interests:
        return {"stall": None, "reason": "No user interests available"}

    stall_categories = get_stall_categories()
    
    best_stall = None
    best_reason = "No suitable stall found"
    min_crowd = float('inf')
    best_interest_match = None
    
    for stall_name, crowd_count in stall_counts.items():
        interest_score = 0
        if stall_name.lower() in stall_categories:
            stall_cat = stall_categories[stall_name.lower()]
            if stall_cat in user_interests:
                interest_score = 2
            elif any(cat in stall_cat for cat in user_interests):
                interest_score = 1
        
        if crowd_count < min_crowd or (crowd_count == min_crowd and interest_score > (best_interest_match or 0)):
            min_crowd = crowd_count
            best_stall = stall_name
            best_interest_match = interest_score
            if interest_score > 0:
                best_reason = f"Recommended due to low crowd ({crowd_count} people) and matching {stall_cat} interest"
            else:
                best_reason = f"Recommended due to low crowd ({crowd_count} people)"
    
    return {"stall": best_stall, "reason": best_reason}

# Routes
@app.route('/')
def index():
    events = get_all_events()[:3]
    return render_template('index.html', events=events)

@app.route('/login', methods=['POST'])
def login():
    user_id = request.form.get('user_id')
    user = get_user(user_id)
    if user:
        session['user_id'] = int(user_id)
        return jsonify({"success": True, "message": f"Logged in as {user['name']}!"})
    return jsonify({"success": False, "message": "Invalid User ID. Please register first."})

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        interests = request.form.getlist('interests')
        if not name or not email or not interests:
            return render_template('register.html', categories=CATEGORIES, error="All fields are required.")
        user_id = add_user(name, email, interests)
        session['user_id'] = user_id
        with file_lock:
            with open(USER_ID_INTERESTS_FILE, mode='a', newline='') as file:
                csv.writer(file).writerow([user_id, ",".join(interests)])
        return jsonify({"success": True, "user_id": user_id, "message": f"Registration successful! Your User ID is {user_id}."})
    return render_template('register.html', categories=CATEGORIES)

@app.route('/events')
def events():
    events = get_all_events()
    return render_template('events.html', events=events, user_id=session.get('user_id'))

@app.route('/my_events')
def my_events():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    registrations = get_user_registrations(user_id)
    return render_template('my_events.html', events=registrations, user_id=user_id)

@app.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    interest_events = get_interest_based_events(user_id)
    mood_events = []
    trend_events = get_trend_based_events(user_id)
    if request.method == 'POST':
        mood_input = request.form.get('mood')
        if mood_input:
            mood_events = get_mood_based_events(mood_input)
    return render_template('recommendations.html', interest_events=interest_events, mood_events=mood_events, trend_events=trend_events, user_id=user_id)

@app.route('/add_event', methods=['GET', 'POST'])
def add_event_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    if request.method == 'POST':
        title = request.form.get('title')
        date = request.form.get('date')
        venue = request.form.get('venue')
        description = request.form.get('description')
        category = request.form.get('category')
        if not all([title, date, description, category]):
            return render_template('add_event.html', categories=CATEGORIES, error="All fields are required.")
        add_event(title, date, venue, description, category, user_id)
        return redirect(url_for('index'))
    return render_template('add_event.html', categories=CATEGORIES)

@app.route('/generate_description', methods=['POST'])
def generate_description():
    title = request.form.get('title')
    date = request.form.get('date')
    venue = request.form.get('venue')
    category = request.form.get('category')
    if not all([title, date, category]):
        return jsonify({"error": "Title, date, and category are required."}), 400
    description = generate_event_description(title, date, venue, category)
    return jsonify({"description": description})

@app.route('/register_event/<int:event_id>', methods=['POST'])
def register_event(event_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Please log in first."})
    if register_for_event(user_id, event_id):
        return jsonify({"success": True, "message": "Registered successfully!"})
    return jsonify({"success": False, "message": "You’re already registered for this event."})

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form.get('name')
        feedback_text = request.form.get('feedback')
        event = request.form.get('event')
        rating = request.form.get('rating')
        if not all([name, feedback_text, event, rating]):
            return render_template('feedback.html', events=get_all_events(), error="All fields are required.")
        df = pd.read_csv(FEEDBACK_FILE) if os.path.exists(FEEDBACK_FILE) else pd.DataFrame(columns=["name", "feedback", "event", "rating", "response"])
        df = pd.concat([df, pd.DataFrame([{"name": name, "feedback": feedback_text, "event": event, "rating": rating, "response": ""}])], ignore_index=True)
        df.to_csv(FEEDBACK_FILE, index=False)
        return redirect(url_for('index'))
    events = [e["title"] for e in get_all_events()] + STALLS
    return render_template('feedback.html', events=events)

@app.route('/performance_insights', methods=['GET', 'POST'])
def performance_insights():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    df = pd.read_csv(FEEDBACK_FILE) if os.path.exists(FEEDBACK_FILE) else pd.DataFrame(columns=["name", "feedback", "event", "rating", "response"])
    events = sorted(df["event"].dropna().unique()) if not df.empty else []
    prediction = ""
    if request.method == 'POST':
        event_selected = request.form.get('event')
        if event_selected:
            stall_feedback = df[df["event"] == event_selected]
            feedback_text = " ".join(stall_feedback["feedback"].dropna().tolist())
            if not feedback_text:
                prediction = f"No feedback available for {event_selected}."
            else:
                try:
                    response = co.chat.completions.create(
                        model="llama3-8b-8192",
                        messages=[
                            {"role": "system", "content": "You are an analyst summarizing event performance based on feedback. Write your response as clear, concise paragraphs without bullet points or asterisks. Use natural language and proper spacing between paragraphs."},
                            {"role": "user", "content": f"Analyze feedback for {event_selected} and summarize event performance:\n\n{feedback_text}"}
                        ],
                        max_tokens=300,
                        temperature=0.7
                    )
                    prediction = response.choices[0].message.content.strip()
                except Exception as e:
                    prediction = f"Error fetching prediction: {str(e)}"
        else:
            prediction = "Please select an event."
    return render_template('performance_insights.html', events=events, prediction=prediction)

@app.route('/stall_suggestions', methods=['GET', 'POST'])
def stall_suggestions():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    df = pd.read_csv(FEEDBACK_FILE) if os.path.exists(FEEDBACK_FILE) else pd.DataFrame(columns=["name", "feedback", "event", "rating", "response"])
    events = sorted(df["event"].dropna().unique()) if not df.empty else []
    suggestions = ""
    if request.method == 'POST':
        event_selected = request.form.get('event')
        if event_selected:
            stall_feedback = df[df["event"] == event_selected]
            feedback_text = " ".join(stall_feedback["feedback"].dropna().tolist())
            if not feedback_text:
                suggestions = f"No feedback available for {event_selected}."
            else:
                try:
                    response = co.chat.completions.create(
                        model="llama3-8b-8192",
                        messages=[
                            {"role": "system", "content": "You are an expert suggesting stall improvements based on feedback. Write your response as clear, concise paragraphs without bullet points or asterisks. Use natural language and proper spacing between paragraphs."},
                            {"role": "user", "content": f"Suggest stall improvements for {event_selected} based on this feedback:\n\n{feedback_text}"}
                        ],
                        max_tokens=300,
                        temperature=0.7
                    )
                    suggestions = response.choices[0].message.content.strip()
                except Exception as e:
                    suggestions = f"Error fetching suggestions: {str(e)}"
        else:
            suggestions = "Please select an event."
    return render_template('stall_suggestions.html', events=events, suggestions=suggestions)

@app.route('/crowd_monitor', methods=['GET', 'POST'])
def crowd_monitor():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    crowd_data = update_stall_people_count()
    suggestion = suggest_best_stall(user_id)
    if request.method == 'POST':
        data = request.json or request.form
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        is_stall_owner = data.get('is_stall_owner', False)
        stall_name = data.get('stall_name', "")
        
        if not all([latitude, longitude]):
            return jsonify({"error": "Missing coordinates"}), 400
        
        with file_lock:
            if is_stall_owner:
                if not stall_name:
                    return jsonify({"error": "Stall name required"}), 400
                stall_exists = any(row[0] == str(user_id) for row in csv.reader(open(STALLS_FILE, "r")) if row) if os.path.exists(STALLS_FILE) else False
                if not stall_exists:
                    with open(STALLS_FILE, mode='a', newline='') as file:
                        csv.writer(file).writerow([user_id, stall_name, latitude, longitude])
                    update_stall_people_count()
            else:
                all_rows = []
                user_exists = False
                if os.path.exists(USER_LOCATIONS_FILE):
                    with open(USER_LOCATIONS_FILE, "r") as file:
                        reader = csv.reader(file)
                        header = next(reader)
                        all_rows.append(header)
                        for row in reader:
                            if row and row[0] == str(user_id):
                                all_rows.append([user_id, latitude, longitude, datetime.utcnow().isoformat()])
                                user_exists = True
                            else:
                                all_rows.append(row)
                else:
                    all_rows.append(["user_id", "latitude", "longitude", "timestamp"])
                if not user_exists:
                    all_rows.append([user_id, latitude, longitude, datetime.utcnow().isoformat()])
                with open(USER_LOCATIONS_FILE, mode='w', newline='') as file:
                    csv.writer(file).writerows(all_rows)
        update_stall_people_count()
        crowd_data = update_stall_people_count()
    
    m = folium.Map(location=[37.7749, -122.4194], zoom_start=13)
    for stall_name, details in crowd_data.items():
        if "latitude" in details and "longitude" in details:
            crowd_count = details["crowd_count"]
            color = "green" if crowd_count < 10 else "orange" if crowd_count < 20 else "red"
            folium.Marker(
                [details["latitude"], details["longitude"]],
                popup=f"{stall_name}<br>Crowd Count: {crowd_count}",
                icon=folium.Icon(color=color, icon="info-sign")
            ).add_to(m)
    map_html = m._repr_html_()
    return render_template('crowd_monitor.html', map_html=map_html, crowd_data=crowd_data, suggestion=suggestion, user_id=user_id)

@app.route('/save-location', methods=['POST'])
def save_location():
    data = request.json
    user_id = data.get("user_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    is_stall_owner = data.get("is_stall_owner", False)
    stall_name = data.get("stall_name", "")
    
    if not all([user_id, latitude, longitude]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        latitude = float(latitude)
        longitude = float(longitude)
        if latitude == 1.0 and longitude == 1.0:
            return jsonify({"error": "Invalid default coordinates (1.0, 1.0) detected"}), 400
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return jsonify({"error": "Invalid coordinates"}), 400
    except ValueError:
        return jsonify({"error": "Coordinates must be numeric"}), 400
    
    with file_lock:
        if is_stall_owner:
            if not stall_name:
                return jsonify({"error": "Stall name required"}), 400
            stall_exists = any(row[0] == str(user_id) for row in csv.reader(open(STALLS_FILE, "r")) if row) if os.path.exists(STALLS_FILE) else False
            if not stall_exists:
                with open(STALLS_FILE, mode='a', newline='') as file:
                    csv.writer(file).writerow([user_id, stall_name, latitude, longitude])
                update_stall_people_count()
                return jsonify({"message": "Stall registered", "latitude": latitude, "longitude": longitude}), 200
            return jsonify({"message": "Stall already registered"}), 200
        else:
            all_rows = []
            user_exists = False
            if os.path.exists(USER_LOCATIONS_FILE):
                with open(USER_LOCATIONS_FILE, "r") as file:
                    reader = csv.reader(file)
                    header = next(reader)
                    all_rows.append(header)
                    for row in reader:
                        if row and row[0] == str(user_id):
                            all_rows.append([user_id, latitude, longitude, datetime.utcnow().isoformat()])
                            user_exists = True
                        else:
                            all_rows.append(row)
            else:
                all_rows.append(["user_id", "latitude", "longitude", "timestamp"])
            if not user_exists:
                all_rows.append([user_id, latitude, longitude, datetime.utcnow().isoformat()])
            with open(USER_LOCATIONS_FILE, mode='w', newline='') as file:
                csv.writer(file).writerows(all_rows)
    
    update_stall_people_count()
    return jsonify({"message": "Location updated", "latitude": latitude, "longitude": longitude}), 200

@app.route('/crowd_density', methods=['GET'])
def crowd_density():
    try:
        stall_crowd = update_stall_people_count()
        return jsonify(stall_crowd), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/remove_stall', methods=['POST'])
def remove_stall():
    data = request.json
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    stall_exists = False
    updated_rows = []

    with file_lock:
        if os.path.exists(STALLS_FILE):
            with open(STALLS_FILE, "r") as file:
                reader = csv.reader(file)
                header = next(reader)
                updated_rows.append(header)
                for row in reader:
                    if row and row[0] == str(user_id):
                        stall_exists = True
                    else:
                        updated_rows.append(row)
            if stall_exists:
                with open(STALLS_FILE, "w", newline='') as file:
                    writer = csv.writer(file)
                    writer.writerows(updated_rows)
                update_stall_people_count()
                return jsonify({"message": "Stall location removed successfully"}), 200
            return jsonify({"error": "No stall found for the given user ID"}), 404
        return jsonify({"error": "Stall database not found"}), 500

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    df = pd.read_csv(FEEDBACK_FILE) if os.path.exists(FEEDBACK_FILE) else pd.DataFrame(columns=["name", "feedback", "event", "rating", "response"])
    events = sorted(df["event"].dropna().unique()) if not df.empty else []
    
    if request.method == 'POST':
        password = request.form.get('password')
        if password != "admin123":
            return render_template('admin_dashboard.html', error="Incorrect password!", feedback=None, events=events, selected_event=None)
        
        selected_event = request.form.get('event')
        stall_feedback = df[df["event"] == selected_event] if selected_event else pd.DataFrame()

        if 'reply' in request.form:
            feedback_id = int(request.form.get('feedback_id'))
            response = request.form.get('response')
            if feedback_id < len(df):
                df.at[feedback_id, "response"] = response
                df.to_csv(FEEDBACK_FILE, index=False)
            stall_feedback = df[df["event"] == selected_event]
        elif 'delete' in request.form:
            feedback_id = int(request.form.get('delete'))
            if feedback_id < len(df):
                df = df.drop(index=feedback_id).reset_index(drop=True)
                df.to_csv(FEEDBACK_FILE, index=False)
            stall_feedback = df[df["event"] == selected_event]
        
        return render_template('admin_dashboard.html', error=None, feedback=stall_feedback.to_dict('records'), events=events, selected_event=selected_event)
    
    return render_template('admin_dashboard.html', error=None, feedback=None, events=events, selected_event=None)

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    
    messages = session.get('chat_messages', [])
    quick_options = [
        "List all events",
        "Show upcoming events",
        "What’s the next event?",
        "Tell me about events in [category] (e.g., Technology)"
    ]

    if request.method == 'POST':
        chat_mode = request.form.get('chat_mode', 'chat')
        user_input = request.form.get('user_input')
        
        if user_input:
            messages.append({"role": "user", "content": user_input})
            system_prompt = """
            You are EventBuddy, a helpful assistant for EventHub. I can only provide information about events from the database. Respond in clear, concise paragraphs without bullet points or asterisks. Use natural language and proper spacing between paragraphs. If the user asks about something unrelated to events, say: 'I can only provide information about events.' If you need to fetch event data, use [FETCH_EVENT_DATA: query] in your response, and I’ll replace it with actual data. For quick options, process the exact option text provided.
            """
            history = [{"role": "system", "content": system_prompt}]
            for msg in messages:
                history.append({"role": msg["role"], "content": msg["content"]})
            history.append({"role": "user", "content": user_input})

            try:
                response = co.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=history,
                    max_tokens=300,
                    temperature=0.7
                )
                bot_response = response.choices[0].message.content.strip()
                if "[FETCH_EVENT_DATA:" in bot_response:
                    start_idx = bot_response.index("[FETCH_EVENT_DATA:") + 18
                    end_idx = bot_response.index("]", start_idx)
                    query = bot_response[start_idx:end_idx].strip()
                    event_data = fetch_event_data(query if chat_mode == 'chat' else user_input, user_id)
                    bot_response = bot_response[:start_idx-18] + event_data + bot_response[end_idx+1:]
                messages.append({"role": "bot", "content": bot_response})
            except Exception as e:
                messages.append({"role": "bot", "content": f"Error: {str(e)}"})
            
            session['chat_messages'] = messages

    return render_template('chatbot.html', messages=messages, quick_options=quick_options, chat_mode='chat')

def fetch_event_data(query, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    current_date = datetime.now().strftime("%Y-%m-%d")

    if query.lower() == "list all events":
        cursor.execute("SELECT title, date, venue, category FROM events ORDER BY date ASC")
        events = cursor.fetchall()
        if events:
            response = "Here’s a list of all events currently in the database. "
            for event in events:
                response += f"The event '{event['title']}' is scheduled on {event['date']} at {event['venue']} in the {event[' tuvoategory']} category. "
            return response.strip()
        return "There are no events in the database right now."

    elif query.lower() == "show upcoming events":
        cursor.execute("SELECT title, date, venue, category FROM events WHERE date >= ? ORDER BY date ASC", (current_date,))
        events = cursor.fetchall()
        if events:
            response = "Here are the upcoming events. "
            for event in events:
                response += f"The event '{event['title']}' is happening on {event['date']} at {event['venue']} in the {event['category']} category. "
            return response.strip()
        return "There are no upcoming events at the moment."

    elif query.lower() == "what’s the next event?":
        cursor.execute("SELECT title, date, venue, category FROM events WHERE date >= ? ORDER BY date ASC LIMIT 1", (current_date,))
        event = cursor.fetchone()
        if event:
            return f"The next event is '{event['title']}'. It’s scheduled on {event['date']} at {event['venue']} in the {event['category']} category."
        return "There’s no next event scheduled right now."

    elif "tell me about events in" in query.lower():
        category = query.split("in")[-1].strip()
        cursor.execute("SELECT title, date, venue FROM events WHERE category = ? ORDER BY date ASC", (category,))
        events = cursor.fetchall()
        if events:
            response = f"Here’s what I found for {category} events. "
            for event in events:
                response += f"The event '{event['title']}' is on {event['date']} at {event['venue']}. "
            return response.strip()
        return f"There are no events in the {category} category at the moment."

    conn.close()
    return "I can only provide information about events. Please ask something event-related!"

if __name__ == "__main__":
    init_db()
    initialize_csv()
    app.run(debug=True)