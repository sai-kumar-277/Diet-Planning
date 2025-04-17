from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename
from ultralytics import YOLO
from PIL import Image
import numpy as np
from collections import Counter
import cv2
import requests
from flask import session
from datetime import datetime, date
from voice import get_voice_input, extract_food_quantities
from flask import jsonify, render_template_string
from werkzeug.security import check_password_hash, generate_password_hash
import re
from datetime import datetime, timedelta
from pprint import pprint
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
model = YOLO('model/yolo_fruits_and_vegetables_v1.pt')

# Nutritionix API credentials
NUTRITIONIX_APP_ID = "298f3466"
NUTRITIONIX_API_KEY = "477bc905b0a6872c02332efac64d9770"

def get_nutrition_info(food_item):
    print(f"[DEBUG] Querying Nutritionix for: '{food_item}'")
    url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    headers = {
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_API_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "query": food_item,
        "timezone": "US/Eastern"
    }
    response = requests.post(url, json=body, headers=headers)
    print(f"[DEBUG] Response status code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"[DEBUG] Response JSON: {result}")
        if 'foods' in result and len(result['foods']) > 0:
            return result['foods'][0]  # Return first food item as dict
    return None

def get_info(query):
    url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    headers = {
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "query": query,
        "timezone": "US/Eastern"
    }

    response = requests.post(url, headers=headers, json=data)
    print("Nutritionix API Response Status:", response.status_code)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "API request failed"}

# === 🧠 Rule-based + Nutrition-aware chatbot ===
def chatbot_response(message):
    msg = message.lower()
    print("User Message:", msg)

    # 🌟 1. Handle goal-based requests like "give me 500 kcal"
    goal_match = re.search(r"(?:give me|need|suggest).(\d+)\s(kcal|calories|g protein|g carbs|g fat)", msg)
    if goal_match:
        amount = int(goal_match.group(1))
        nutrient = goal_match.group(2)

        suggestions = {
            "kcal": "Try a peanut butter sandwich 🥪 (around 500 kcal)",
            "calories": "How about a slice of pizza 🍕 or a smoothie 🥤?",
            "g protein": "Grilled chicken breast 🍗 or Greek yogurt 🥣 are great protein sources!",
            "g carbs": "Go for oatmeal 🥣 or bananas 🍌",
            "g fat": "Avocados 🥑, nuts 🥜, or cheese 🧀 work well!"
        }

        return suggestions.get(nutrient, "I’d suggest some healthy whole foods! 🥗")

    # 🌟 2. Check if the message seems to be about food
    likely_food = any(word in msg for word in [
        "calories", "nutrition", "protein", "carbs", "fat", "ate", "eaten", "have", "had", "food"
    ])
    if likely_food or any(char.isdigit() for char in msg):  # Also try if message has quantities
        nutrition_data = get_info(msg)
        if "error" in nutrition_data:
            return "Sorry, I couldn't get the nutrition info right now. 🥲"

        if "foods" in nutrition_data and nutrition_data["foods"]:
            reply = "Here's the nutrition breakdown:\n"
            for food in nutrition_data["foods"]:
                reply += (
                    f"\n🍽️ {food['food_name'].title()}:\n"
                    f"  - Calories: {food['nf_calories']} kcal\n"
                    f"  - Protein: {food['nf_protein']} g\n"
                    f"  - Fat: {food['nf_total_fat']} g\n"
                    f"  - Carbs: {food['nf_total_carbohydrate']} g\n"
                )
            return reply
        else:
            return "I couldn't find any nutrition info for that. Try something more specific like '2 boiled eggs' 🥚"

    # 🌟 3. Default rule-based responses
    if "hello" in msg or "hi" in msg:
        return "Hey there! 👋 How can I help you today?"
    elif "suggest" in msg:
        return "Try taking a short walk, listening to music, or learning something new today!"
    elif "who are you" in msg:
        return "I'm your friendly local chatbot. And I'm free 😎"
    elif "bye" in msg:
        return "Goodbye! Come back soon!"
    else:
        return "Hmm... I don't know that yet, but I'm learning! 😊"

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        age = request.form['age']
        
        # Removed health_issue from form

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please login.', 'error')
            return redirect(url_for('login'))

        new_user = User(name=name, email=email, password=password, age=age, health_issue=None)
        db.session.add(new_user)
        db.session.commit()
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to continue.', 'error')
        return redirect(url_for('login'))
    return render_template('dashboard.html', name=session['user_name'])

@app.route('/profile')
def profile():
    # For now, simply render a placeholder template
    return render_template('profile.html', name=session.get('user_name'))

@app.route('/voice-input')
def voice_input():
    saved_data = session.pop('saved_data', None)
    return render_template('voice_input.html', saved_data=saved_data)

@app.route('/image-input')
def image_input():
    return render_template('image_input.html')

@app.route('/manual-entry', methods=['GET', 'POST'])
def manual_entry():
    if request.method == 'POST':
        item = request.form.get('item')
        quantity = int(request.form.get('quantity'))
        user_id = session.get('user_id')

        if not user_id:
            flash("Please log in to submit entries.", "error")
            return redirect(url_for('login'))

        nutrition = get_nutrition_info(item.strip())

        if nutrition:
            entry = FoodEntry(
                user_id=user_id,
                item=item.strip(),
                quantity=quantity,
                calories=nutrition['nf_calories'] * quantity,
                protein=nutrition['nf_protein'] * quantity,
                carbs=nutrition['nf_total_carbohydrate'] * quantity,
                fat=nutrition['nf_total_fat'] * quantity,
                time_of_day="unspecified"
            )
            db.session.add(entry)
            db.session.commit()
            flash(f"Added {item} (x{quantity}) to your log.", "success")
        else:
            entry = FoodEntry(
                user_id=user_id,
                item=item.strip(),
                quantity=quantity,
                time_of_day="unspecified"
            )
            db.session.add(entry)
            db.session.commit()
            flash(f"Added {item} (x{quantity}), but nutrition data was unavailable.", "warning")

        return redirect(url_for('dashboard'))  # or wherever you want to send the user

    # This renders the form on GET
    return render_template('manual_entry.html')

@app.route('/analytics')
def analytics():
    user_id = session.get("user_id")
    if not user_id:
        return "User not logged in", 403

    today = datetime.today().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = start_of_day + timedelta(days=1)

    entries = FoodEntry.query.filter(
        FoodEntry.timestamp >= start_of_day,
        FoodEntry.timestamp < end_of_day,
        FoodEntry.user_id == user_id
    ).all()

    print("Entries Found:", len(entries))  # 👈
    pprint([(e.item, e.timestamp, e.time_of_day) for e in entries])  # 👈

    meals = {"morning": [], "afternoon": [], "evening": []}
    calories_per_meal = defaultdict(float)
    total_macros = {"protein": 0, "carbs": 0, "fat": 0}

    for entry in entries:
        time_slot = entry.time_of_day

        if not time_slot or time_slot == "unspecified":
            hour = entry.timestamp.hour
            if hour < 12:
                time_slot = "morning"
            elif hour < 17:
                time_slot = "afternoon"
            else:
                time_slot = "evening"

        if time_slot not in meals:
            meals[time_slot] = []

        meals[time_slot].append(entry)
        calories_per_meal[time_slot] += entry.calories or 0
        total_macros["protein"] += entry.protein or 0
        total_macros["carbs"] += entry.carbs or 0
        total_macros["fat"] += entry.fat or 0

    return render_template("analytics.html", meals=meals,calories_per_meal=calories_per_meal,
                           total_macros=total_macros)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/image-process', methods=['POST'])
def image_process():
    if 'image' not in request.files:
        return "No file uploaded"

    image = request.files['image']
    filename = secure_filename(image.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(filepath)

    results = model.predict(filepath, save=False, conf=0.4)
    names = results[0].names
    boxes = results[0].boxes.cls.tolist()

    # Count how many times each item appears
    counted_items = Counter([names[int(cls_id)] for cls_id in boxes])

    return render_template('image_input.html', predictions=counted_items)

@app.route('/edit-predictions', methods=['POST'])
def edit_predictions():
    items = request.form.getlist('items')
    quantities = request.form.getlist('quantities')
    new_item = request.form.get('new_item')
    new_quantity = request.form.get('new_quantity') or "1"

    if new_item:
        items.append(new_item)
        quantities.append(new_quantity)

    user_id = session.get('user_id')
    if not user_id:
        flash("You must be logged in to save data.", "error")
        return redirect(url_for('login'))

    saved_data = []

    for item, qty in zip(items, quantities):
        nutrition = get_nutrition_info(item.strip())
        if nutrition and isinstance(nutrition, dict):
            entry = FoodEntry(
                user_id=user_id,
                item=item.strip(),
                quantity=int(qty),
                calories=nutrition['nf_calories'] * int(qty),
                protein=nutrition['nf_protein'] * int(qty),
                carbs=nutrition['nf_total_carbohydrate'] * int(qty),
                fat=nutrition['nf_total_fat'] * int(qty),
                time_of_day="unspecified"
            )
            db.session.add(entry)
            saved_data.append((item, qty, nutrition['nf_calories'] * int(qty)))
        else:
            # Save basic info if Nutritionix fails
            entry = FoodEntry(user_id=user_id, item=item.strip(), quantity=int(qty))
            db.session.add(entry)
            saved_data.append((item, qty, "Nutrition data unavailable"))

    db.session.commit()

    return render_template('image_input.html', saved_data=saved_data,saved=True)

@app.route('/nutrition-summary')
def nutrition_summary():
    if 'user_id' not in session:
        flash('Please log in to view your nutrition summary.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    items = FoodEntry.query.filter(
    FoodEntry.user_id == user_id,
    db.func.date(FoodEntry.timestamp) == date.today()
    ).all()

    nutrition_data = []
    for item in items:
        result = get_nutrition_info(item.item)
        if result:
            nutrition_data.append({
                'name': item.item,
                'quantity': item.quantity,
                'calories': result['nf_calories'],
                'protein': result['nf_protein'],
                'carbs': result['nf_total_carbohydrate'],
                'fat': result['nf_total_fat'],
                'time_of_day': item.time_of_day
            })

    return render_template('nutrition_summary.html', nutrition_data=nutrition_data)

@app.route('/voice-process', methods=['GET'])
def voice_process():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to use voice input.", "error")
        return redirect(url_for('login'))

    spoken_text = get_voice_input()
    if not spoken_text:
        flash("Could not understand audio. Please try again.", "error")
        return redirect(url_for('voice_input'))

    food_data = extract_food_quantities(spoken_text)
    saved_data = []

    for item, quantity in food_data.items():
        nutrition = get_nutrition_info(item.strip())
        if nutrition:
            entry = FoodEntry(
                user_id=user_id,
                item=item.strip(),
                quantity=quantity,
                calories=nutrition['nf_calories'] * quantity,
                protein=nutrition['nf_protein'] * quantity,
                carbs=nutrition['nf_total_carbohydrate'] * quantity,
                fat=nutrition['nf_total_fat'] * quantity,
                time_of_day="unspecified"
            )
        else:
            entry = FoodEntry(user_id=user_id, item=item.strip(), quantity=quantity)

        db.session.add(entry)
        saved_data.append((item, quantity))

    db.session.commit()
    session['saved_data'] = saved_data
    flash("Voice entry added successfully!", "success")
    return redirect(url_for('voice_input'))

@app.route('/my-log')
def my_log():
    if 'user_id' not in session:
        flash('Please log in to view your food log.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    entries = FoodEntry.query.filter_by(user_id=user_id).order_by(FoodEntry.timestamp.desc()).all()
    return render_template('my_log.html', entries=entries)

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot/index.html')


@app.route('/load_section/<section>')
def load_section(section):
    if 'user_id' not in session:
        return "Unauthorized", 401

    user = User.query.get(session['user_id'])
    profile = Profile.query.filter_by(user_id=user.id).first()

    if section == 'profile':
        return render_template('sections/profile_section.html', user=user, profile=profile)
    elif section == 'health':
        return render_template('sections/health_section.html', user=user, profile=profile)
    elif section == 'settings':
        return render_template('sections/settings_section.html', user=user)
    elif section == 'diet':
        return render_template('sections/diet_section.html', user=user, profile=profile)
    elif section == 'connect':
        return render_template('sections/connect_section.html', user=user)
    else:
        return "Section not found", 404

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session['user_id']
    user = User.query.get(user_id)
    profile = Profile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = Profile(user_id=user_id)
        db.session.add(profile)

    # Update user + profile fields
    user.name = request.form.get('name')
    user.age = int(request.form.get('age', 0))
    profile.height = float(request.form.get('height', 0))
    profile.weight = float(request.form.get('weight', 0))
    profile.gender = request.form.get('gender')
    profile.goals = request.form.get('goals')

    db.session.commit()

    # Render updated profile details block
    updated_html = render_template_string("""
        <p><strong>Name:</strong> {{ user.name }}</p>
        <p><strong>Age:</strong> {{ user.age }}</p>
        <p><strong>Height:</strong> {{ profile.height }} cm</p>
        <p><strong>Weight:</strong> {{ profile.weight }} kg</p>
        <p><strong>Gender:</strong> {{ profile.gender }}</p>
        <p><strong>Goals:</strong> {{ profile.goals }}</p>
    """, user=user, profile=profile)

    return jsonify({"success": True, "updated_html": updated_html})

@app.route('/save_health', methods=['POST'])
def save_health():
    condition = request.form.get('condition')
    schedule = request.form.get('schedule')
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'status': 'error', 'message': 'User not logged in'})

    health = Health.query.filter_by(user_id=user_id).first()

    if health:
        health.condition = condition
        health.schedule = schedule
    else:
        health = Health(user_id=user_id, condition=condition, schedule=schedule)
        db.session.add(health)

    try:
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Health data saved successfully'})
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to save health data'})

@app.route('/change_password', methods=['POST'])
def change_password():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'User not logged in'})

    current_password = request.form.get('currentPassword')
    new_password = request.form.get('newPassword')

    user = User.query.get(user_id)
    if not user or not check_password_hash(user.password, current_password):
        return jsonify({'status': 'error', 'message': 'Current password is incorrect'})

    user.password = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Password updated successfully'})

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(200))
    age = db.Column(db.Integer)
    health_issue = db.Column(db.String(100))  # e.g. 'diabetes', 'bp', 'athlete'

    profile = db.relationship('Profile', backref='user', uselist=False, cascade="all, delete-orphan")

class FoodEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    item = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    calories = db.Column(db.Float)
    protein = db.Column(db.Float)
    carbs = db.Column(db.Float)
    fat = db.Column(db.Float)
    time_of_day = db.Column(db.String(50))  # ✅ new column
    timestamp = db.Column(db.DateTime, server_default=db.func.current_timestamp())

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    age = db.Column(db.Integer)
    height = db.Column(db.Float)  # in centimeters
    weight = db.Column(db.Float)  # in kilograms
    gender = db.Column(db.String(20))
    goals = db.Column(db.Text)

    def calculate_bmi(self):
        if self.height and self.weight and self.height > 0:
            height_in_m = self.height / 100
            return round(self.weight / (height_in_m ** 2), 2)
        return None

class Health(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    condition = db.Column(db.String(100), nullable=False)  # e.g., "diabetes", "heart"
    schedule = db.Column(db.String(200), nullable=False)   # e.g., "8AM, 2PM, 9PM"

    user = db.relationship('User', backref=db.backref('health', uselist=False, cascade="all, delete-orphan"))

# Create DB
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)

