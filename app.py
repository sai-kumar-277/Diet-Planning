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
from nutrition_db import lookup_nutrition, lookup_nutrition_query
from flask import session
from datetime import datetime, date
from voice import get_voice_input, extract_food_quantities
from flask import jsonify, render_template_string
from werkzeug.security import check_password_hash, generate_password_hash
import re
from datetime import datetime, timedelta
from pprint import pprint
from collections import defaultdict
import llm_helper

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
model = YOLO('model/yolo_fruits_and_vegetables_v1.pt')

# ── Nutrition lookup (local database — no API key needed) ──────────────

def get_nutrition_info(food_item):
    """Return nutrition dict for a single food item, or None."""
    print(f"[DEBUG] Looking up nutrition for: '{food_item}'")
    result = lookup_nutrition(food_item)
    if result:
        print(f"[DEBUG] Found: {result}")
    else:
        print(f"[DEBUG] No match found for '{food_item}'")
    return result

def get_info(query):
    """Process a natural-language query and return {foods: [...]}."""
    print(f"[DEBUG] Processing query: '{query}'")
    result = lookup_nutrition_query(query)
    if not result['foods']:
        return {"error": "No matching foods found in database"}
    return result

# === 🧠 Local RAG Chatbot ===
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get("message", "")
    
    # Retrieve relevant nutrition info locally if message implies food lookup
    likely_food = any(word in message.lower() for word in [
        "calories", "nutrition", "protein", "carbs", "fat", "ate", "eaten", "have", "had", "food"
    ])
    
    nutrition_data = None
    if likely_food or any(char.isdigit() for char in message):
        nutrition_data = get_info(message)
        if "error" in nutrition_data:
            nutrition_data = None
            
    user_id = session.get('user_id')
    user_profile = None
    health_profile = None
    if user_id:
        user_profile = Profile.query.filter_by(user_id=user_id).first()
        health_profile = Health.query.filter_by(user_id=user_id).first()
            
    reply = llm_helper.generate_chatbot_reply(message, nutrition_data, user_profile, health_profile)
    return jsonify({"reply": reply})

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

    ist_offset = timedelta(hours=5, minutes=30)
    now_ist = datetime.utcnow() + ist_offset
    today_ist = now_ist.date()
    start_of_day_ist = datetime.combine(today_ist, datetime.min.time())
    start_of_day_utc = start_of_day_ist - ist_offset
    end_of_day_utc = start_of_day_utc + timedelta(days=1)

    entries = FoodEntry.query.filter(
        FoodEntry.timestamp >= start_of_day_utc,
        FoodEntry.timestamp < end_of_day_utc,
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
            ist_time = entry.timestamp + timedelta(hours=5, minutes=30) if entry.timestamp else datetime.utcnow()
            hour = ist_time.hour
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
    ist_offset = timedelta(hours=5, minutes=30)
    now_ist = datetime.utcnow() + ist_offset
    today_ist = now_ist.date()
    start_of_day_ist = datetime.combine(today_ist, datetime.min.time())
    start_of_day_utc = start_of_day_ist - ist_offset
    end_of_day_utc = start_of_day_utc + timedelta(days=1)

    items = FoodEntry.query.filter(
        FoodEntry.user_id == user_id,
        FoodEntry.timestamp >= start_of_day_utc,
        FoodEntry.timestamp < end_of_day_utc
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

@app.route('/update_diet_goals', methods=['POST'])
def update_diet_goals():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session['user_id']
    profile = Profile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = Profile(user_id=user_id)
        db.session.add(profile)
        
    goals = request.form.get('goals')
    profile.goals = goals
    db.session.commit()
    
    return jsonify({"success": True})

@app.route('/save_health', methods=['POST'])
def save_health():
    condition = request.form.get('condition')
    schedule = request.form.get('schedule')
    avoid_foods = request.form.get('avoid_foods', '')
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'status': 'error', 'message': 'User not logged in'})

    health = Health.query.filter_by(user_id=user_id).first()

    if health:
        health.condition = condition
        health.schedule = schedule
        health.avoid_foods = avoid_foods
    else:
        health = Health(user_id=user_id, condition=condition, schedule=schedule, avoid_foods=avoid_foods)
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

    @property
    def timestamp_ist(self):
        from datetime import timedelta
        if self.timestamp:
            return self.timestamp + timedelta(hours=5, minutes=30)
        return None

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
    avoid_foods = db.Column(db.Text, default='')           # comma-separated list of foods to avoid

    user = db.relationship('User', backref=db.backref('health', uselist=False, cascade="all, delete-orphan"))

# === 🍎 Suggested Foods & Diet Section ===
def get_dynamic_suggestions(profile, health):
    import random
    from nutrition_db import NUTRITION_DATA
    
    # Base lists to avoid
    meats = ["chicken", "mutton", "beef", "pork", "fish", "salmon", "tuna", "prawns", "shrimp", "bacon", "sausage", "turkey", "lamb", "nuggets"]
    dairy = ["milk", "cheese", "paneer", "curd", "buttermilk", "lassi", "ghee", "cream", "ice cream", "butter", "yogurt"]
    
    user_text = ""
    if profile and profile.goals:
        user_text += profile.goals.lower() + " "
    if health and health.condition:
        user_text += health.condition.lower() + " "
    if health and health.avoid_foods:
        user_text += health.avoid_foods.lower() + " "
        
    is_vegan = "vegan" in user_text
    is_veg = "vegetarian" in user_text or "veg" in user_text
    high_protein = "muscle" in user_text or "gain" in user_text or "protein" in user_text
    low_cal = "loss" in user_text or "lose" in user_text or "cut" in user_text
    
    avoid_list = []
    if is_vegan:
        avoid_list.extend(meats)
        avoid_list.extend(dairy)
        avoid_list.extend(["egg", "honey", "omelette"])
    elif is_veg:
        avoid_list.extend(meats)
        
    # Also split custom avoid foods
    if health and health.avoid_foods:
        custom_avoids = [x.strip().lower() for x in health.avoid_foods.split(',')]
        avoid_list.extend(custom_avoids)
        
    safe_foods = []
    for food, data in NUTRITION_DATA.items():
        # Check if food contains any avoid word
        if any(bad in food for bad in avoid_list):
            continue
            
        # Score based on goals
        score = 1
        if high_protein and data["protein"] > 10:
            score += 5
        if low_cal and data["calories"] < 150:
            score += 5
            
        safe_foods.append((food.title(), score))
        
    if not safe_foods:
        return ["Apple", "Banana", "Oats", "Salad"]
        
    # Sort by score descending and pick from top ones
    safe_foods.sort(key=lambda x: x[1], reverse=True)
    top_candidates = [f[0] for f in safe_foods[:10]]
    random.shuffle(top_candidates)
    return top_candidates[:4]

@app.route('/suggestions')
def suggestions():
    if 'user_id' not in session:
        flash('Please log in to view dietary suggestions.', 'error')
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    user = User.query.get(user_id)
    profile = Profile.query.filter_by(user_id=user_id).first()
    health = Health.query.filter_by(user_id=user_id).first()
    
    suggested_foods = get_dynamic_suggestions(profile, health)
    
    return render_template('suggestions.html', user=user, profile=profile, health=health, suggested_foods=suggested_foods)

@app.route('/can_i_eat_this', methods=['POST'])
def can_i_eat_this():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.get_json()
    food_item = data.get("food", "").strip()
    
    user_id = session['user_id']
    profile = Profile.query.filter_by(user_id=user_id).first()
    health = Health.query.filter_by(user_id=user_id).first()
    
    nutrition_data = get_nutrition_info(food_item)
    advice = llm_helper.generate_diet_advice(food_item, nutrition_data, profile, health)
    
    return jsonify({
        "advice": advice,
        "nutrition": nutrition_data
    })

@app.route('/api/analyze-image', methods=['POST'])
def api_analyze_image():
    if 'image' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    image = request.files['image']
    filename = secure_filename(image.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(filepath)

    results = model.predict(filepath, save=False, conf=0.4)
    names = results[0].names
    boxes = results[0].boxes.cls.tolist()

    counted_items = Counter([names[int(cls_id)] for cls_id in boxes])
    
    # Format as "2 Apple, 1 Banana"
    items_list = [f"{count} {item}" for item, count in counted_items.items()]
    predicted_text = ", ".join(items_list) if items_list else "Nothing detected"

    return jsonify({"prediction": predicted_text})


@app.route('/api/voice-input', methods=['GET'])
def api_voice_input():
    spoken_text = get_voice_input()
    if spoken_text:
        return jsonify({"text": spoken_text})
    else:
        return jsonify({"error": "Could not understand audio"}), 400

@app.route('/api/get_goals', methods=['GET'])
def api_get_goals():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"goals": ""})
    profile = Profile.query.filter_by(user_id=user_id).first()
    health = Health.query.filter_by(user_id=user_id).first()
    
    goals = []
    if profile and profile.goals:
        goals.append(profile.goals.strip())
    if health and health.condition:
        goals.append("Health: " + health.condition.strip())
    if health and health.avoid_foods:
        goals.append("Avoid: " + health.avoid_foods.strip())
        
    return jsonify({"goals": " | ".join(goals) if goals else "No diet goals set"})

# Create DB
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)

