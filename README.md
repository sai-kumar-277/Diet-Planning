Link  : https://saikumar277-calorie-intake-calculator.hf.space/
---
title: Calorie Intake Calculator
emoji: 🥗
colorFrom: purple
colorTo: pink
sdk: docker
app_port: 7860
pinned: false
---

# 🥗 NutriTrack — AI-Powered Diet & Calorie Tracker

> A full-stack AI-powered diet and calorie tracking web application built with **Flask**, **YOLOv8**, a **local LLM (Qwen 2.5)**, and a glassmorphism dark UI.

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Tech Stack](#-tech-stack)
3. [Project Structure](#-project-structure)
4. [Architecture & How It Works](#-architecture--how-it-works)
5. [Database Models](#-database-models)
6. [Core Modules](#-core-modules)
7. [API Routes Reference](#-api-routes-reference)
8. [Feature Deep-Dives](#-feature-deep-dives)
9. [UI / Design System](#-ui--design-system)
10. [Setup & Running the App](#-setup--running-the-app)
11. [Key Design Decisions](#-key-design-decisions)

---

## 🌟 Project Overview

**NutriTrack** is a personal diet management application that lets users track their daily food intake through three input methods — **manual text entry**, **voice recognition**, and **image-based food detection** (using a YOLO model). The app calculates calories, protein, carbs, and fat from a local nutrition database and presents them in an analytics dashboard. An on-page **AI chatbot** (powered by a locally-loaded LLM) provides personalized dietary advice based on the user's health profile and goals.

### ✅ Core Capabilities

| Feature | Description |
|---|---|
| 🔐 User Auth | Register/Login with hashed passwords (Werkzeug) |
| 🖊️ Manual Entry | Type a food item + quantity; nutrition is looked up instantly |
| 🎤 Voice Input | Speak food items; speech-to-text parses quantities automatically |
| 📸 Image Detection | Upload a photo; YOLOv8 identifies fruits & vegetables in it |
| 📊 Analytics | Daily macro breakdown by meal time (morning / afternoon / evening) |
| 📁 Food Log | Full history of logged entries with timestamps |
| 🤖 AI Chatbot | RAG-style chatbot that knows your health profile and diet goals |
| 💡 Diet Suggestions | Personalized food recommendations based on health conditions & goals |
| 👤 Profile | BMI calculation, goal tracking, health conditions, food avoidances |

---

## 🛠️ Tech Stack

### Backend
| Layer | Technology | Purpose |
|---|---|---|
| Web Framework | **Flask** (Python) | Routing, sessions, templating |
| ORM | **Flask-SQLAlchemy** | Database models & queries |
| Database | **SQLite** (`instance/database.db`) | Persistent user/food data |
| Auth | **Werkzeug Security** | Password hashing & verification |
| Computer Vision | **YOLOv8** (`ultralytics`) | Real-time food item detection from images |
| Image Processing | **Pillow**, **OpenCV**, **NumPy** | Image loading & preprocessing |
| Speech Recognition | **SpeechRecognition** + **Google STT** | Microphone capture → text |
| NLP | **spaCy** + **TextBlob** | Food name correction from voice |
| Local LLM | **Transformers** — `Qwen/Qwen2.5-0.5B-Instruct` | Chatbot & diet advice (offline) |
| Fuzzy Matching | **difflib** | Nutrition lookup fallback |

### Frontend
| Layer | Technology | Purpose |
|---|---|---|
| Templating | **Jinja2** | HTML templating with dynamic data |
| Styling | **Vanilla CSS** (custom design system) | Glassmorphism dark UI |
| Typography | **Google Fonts — Outfit** | Modern sans-serif font |
| Icons | **Font Awesome 6** | UI icons throughout the app |
| JS/AJAX | **jQuery 3.6** | AJAX calls for chatbot & profile updates |
| Animations | Pure CSS keyframes | Floating blobs, fade-ins, slide-ins |

### AI / ML
| Model | Details |
|---|---|
| **YOLOv8 (custom)** | `model/yolo_fruits_and_vegetables_v1.pt` — ~52 MB fine-tuned for fruits & vegetables |
| **Qwen 2.5-0.5B Instruct** | Tiny 0.5B parameter LLM; runs on CPU or GPU; fully offline |

---

## 📁 Project Structure

```
calorie-intake-calculator/
│
├── app.py                  # Main Flask application (routes, models, logic)
├── llm_helper.py           # Local LLM loader and prompt builders
├── nutrition_db.py         # Local nutrition database + lookup functions
├── voice.py                # Speech recognition + food quantity extractor
├── migrate_db.py           # One-off SQLite migration script
├── .gitignore
│
├── model/
│   └── yolo_fruits_and_vegetables_v1.pt   # YOLOv8 weights (~52 MB)
│
├── static/
│   ├── style.css           # Full custom CSS design system
│   ├── script.js           # Frontend JS (chatbot widget, AJAX)
│   ├── background.avif
│   └── uploads/            # Uploaded images (gitignored)
│
└── templates/
    ├── base.html           # Master layout (nav, chatbot widget, toasts)
    ├── login.html / signup.html
    ├── dashboard.html
    ├── manual_entry.html
    ├── voice_input.html
    ├── image_input.html
    ├── analytics.html
    ├── my_log.html
    ├── nutrition_summary.html
    ├── profile.html
    ├── suggestions.html
    ├── chatbot/index.html
    └── sections/           # AJAX-loaded profile sub-sections
        ├── profile_section.html
        ├── health_section.html
        ├── diet_section.html
        ├── settings_section.html
        └── connect_section.html
```

---

## 🏗️ Architecture & How It Works

```
User Request
    ↓
Flask (app.py) — Routes & Session Management
    ↓
┌──────────────────────────────────────┐
│  nutrition_db.py  (Exact→Substring→Fuzzy lookup)  │
│  voice.py         (Google STT → spaCy NLP)        │
│  YOLOv8 Model     (Image inference @ conf=0.4)    │
│  llm_helper.py    (Qwen2.5 LLM — lazy loaded)     │
└──────────────────────────────────────┘
    ↓
SQLite DB ← FoodEntry / User / Profile / Health
    ↓
Jinja2 Templates → HTML Response to Browser
```

### Request Lifecycle
1. User submits food (voice / image / manual)
2. Flask route handler receives data
3. Nutrition lookup via `nutrition_db.py` (3-tier matching)
4. `FoodEntry` record saved to SQLite with IST-aware timestamp
5. Analytics/Log pages filter entries for today's IST date window
6. Chatbot performs RAG — retrieves nutrition facts, feeds with user profile to LLM

---

## 🗄️ Database Models

### `User`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `name` | String(150) | Full name |
| `email` | String(150) | Unique — used for login |
| `password` | String(200) | Werkzeug hashed |
| `age` | Integer | |
| `health_issue` | String(100) | Legacy optional health tag |

### `FoodEntry`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `user_id` | Integer | References User |
| `item` | String(100) | Food name |
| `quantity` | Integer | Number of servings |
| `calories` | Float | Total (qty × per-serving) |
| `protein` | Float | grams |
| `carbs` | Float | grams |
| `fat` | Float | grams |
| `time_of_day` | String(50) | morning/afternoon/evening |
| `timestamp` | DateTime | Server UTC default |

**Property**: `timestamp_ist` — converts UTC → IST (+5:30)

### `Profile`
| Column | Type | Notes |
|---|---|---|
| `height` | Float | cm |
| `weight` | Float | kg |
| `gender` | String(20) | |
| `goals` | Text | Free-text diet goals |

**Method**: `calculate_bmi()` → `weight / (height_m)²`

### `Health`
| Column | Type | Notes |
|---|---|---|
| `condition` | String(100) | e.g. diabetes, heart |
| `schedule` | String(200) | e.g. 8AM, 2PM, 9PM |
| `avoid_foods` | Text | Comma-separated list |

---

## 📦 Core Modules

### `nutrition_db.py` — Local Nutrition Database
- **~200+ foods** across Indian cuisine, Western, fruits, vegetables, grains, meats, dairy, fast food, drinks, nuts
- **3-tier lookup**: Exact → Substring → Fuzzy (`difflib`, cutoff=0.6)
- Parses natural-language queries: `"2 eggs and 1 toast"` → multiplied results
- Mirrors Nutritionix API format (drop-in replacement, no API key needed)

### `voice.py` — Voice Input Module
- Captures microphone audio with ambient noise calibration
- Uses **Google Speech Recognition** for transcription
- Custom `word_to_num` dict handles mishearings (`"ate"→8`, `"won"→1`)
- `food_corrections` dict corrects common mishearings (`"penza"→"pizza"`, `"biriyani"→"biryani"`)
- Falls back to **TextBlob** spell correction for unknown foods

### `llm_helper.py` — On-Device LLM
- Loads `Qwen/Qwen2.5-0.5B-Instruct` lazily (thread-safe, first-request-only)
- Auto-detects CUDA; falls back to CPU (`float32`)
- **`generate_diet_advice()`** — personalized food-specific dietary advice (max 3 sentences)
- **`generate_chatbot_reply()`** — RAG-style chat with nutrition context + user profile

---

## 🔌 API Routes Reference

### Authentication
| Route | Method | Description |
|---|---|---|
| `/` | GET | Redirects to login |
| `/signup` | GET/POST | Create account |
| `/login` | GET/POST | Authenticate user |
| `/logout` | GET | Clear session |

### Food Entry
| Route | Method | Description |
|---|---|---|
| `/manual-entry` | GET/POST | Manual food item + quantity |
| `/voice-input` | GET | Voice recording page |
| `/voice-process` | GET | Capture mic → save entries |
| `/image-process` | POST | Upload image → YOLO predictions |
| `/edit-predictions` | POST | Confirm YOLO results → save |

### Analytics & Log
| Route | Method | Description |
|---|---|---|
| `/dashboard` | GET | Home dashboard |
| `/analytics` | GET | Today's macros by meal slot |
| `/my-log` | GET | Full food history |
| `/nutrition-summary` | GET | Today's per-item breakdown |

### Profile & Health
| Route | Method | Description |
|---|---|---|
| `/profile` | GET | Profile page |
| `/load_section/<section>` | GET | AJAX: load sub-section HTML |
| `/update_profile` | POST | AJAX: update profile fields |
| `/save_health` | POST | AJAX: save health data |
| `/change_password` | POST | AJAX: update password |

### AI Features
| Route | Method | Description |
|---|---|---|
| `/chat` | POST | Chatbot → LLM reply (JSON) |
| `/suggestions` | GET | Personalized food suggestions |
| `/can_i_eat_this` | POST | LLM food advice (JSON) |
| `/api/analyze-image` | POST | YOLO prediction (JSON) |
| `/api/voice-input` | GET | STT transcription (JSON) |
| `/api/get_goals` | GET | User's diet goals (JSON) |

---

## 🔬 Feature Deep-Dives

### Image Food Detection
```
Upload Image → YOLOv8 (conf=0.4) → Count detected classes
→ Show editable prediction table → User confirms/edits
→ Nutrition lookup per item → FoodEntry saved to DB
```

### Voice Input Pipeline
```
Click Record → Google STT → Transcribed text
→ Tokenise → Find quantities (digit/word) → Group food tokens
→ Spell correct → Nutrition lookup → FoodEntry saved
```

### AI Chatbot (RAG)
```
User message → Keyword scan (food-related?)
→ If yes: lookup_nutrition_query() → retrieve facts
→ Load Profile + Health from DB
→ Build Qwen prompt with context + nutrition data
→ LLM generates reply → Return JSON
```

### Food Suggestions Algorithm
1. Parse profile goals + health condition + avoid_foods into text
2. Detect flags: `is_vegan`, `is_veg`, `high_protein`, `low_cal`
3. Build exclusion list (meat/dairy for veg/vegan + custom avoidances)
4. Score all 200+ foods: `+5` for high-protein if protein > 10g, `+5` for low-cal if calories < 150
5. Sort by score → top 10 candidates → shuffle → return 4 (varied per visit)

### IST Timezone Handling
```python
ist_offset = timedelta(hours=5, minutes=30)
today_ist = (datetime.utcnow() + ist_offset).date()
# Convert IST day boundaries back to UTC for DB filter
start_utc = datetime.combine(today_ist, time.min) - ist_offset
end_utc = start_utc + timedelta(days=1)
```

---

## 🎨 UI / Design System

### Color Palette
| Variable | Value | Usage |
|---|---|---|
| `--bg-base` | `#0f172a` | Deep navy background |
| `--accent-primary` | `#8b5cf6` | Purple — CTA, active nav |
| `--accent-secondary` | `#ec4899` | Pink — gradients, buttons |
| `--accent-success` | `#10b981` | Green — success, protein |
| `--accent-danger` | `#ef4444` | Red — errors, fat |
| `--accent-warning` | `#f59e0b` | Amber — warnings, carbs |

### Key UI Patterns
- **Glassmorphism**: `backdrop-filter: blur(16px)` + semi-transparent surfaces
- **Animated Blobs**: 3 blurred color blobs with 20s CSS float animation
- **Mesh Background**: 4-corner radial gradients at 15% opacity
- **Toast Notifications**: `slideInRight` animation, color-coded by type
- **Chatbot FAB**: Fixed bottom-right button with `scaleIn` popup panel
- **Feature Cards**: Hover → lift + icon rotates 5° and fills with gradient
- **Typography**: `Outfit` font (Google Fonts), `letter-spacing: -0.02em`

---

## 🚀 Setup & Running the App

### Prerequisites
- Python 3.9+
- pip
- Microphone (for voice input)

### Install Dependencies
```bash
pip install flask flask-sqlalchemy werkzeug ultralytics pillow opencv-python numpy \
            speechrecognition pyaudio spacy textblob transformers torch requests
python -m spacy download en_core_web_sm
python -m textblob.download_corpora
```

### Run
```bash
python app.py
```

- App starts at `http://127.0.0.1:5000`
- SQLite DB auto-created at `instance/database.db` on first run
- YOLO model loads at startup
- LLM lazy-loads on first chatbot request

### Database Migration (for existing installs)
```bash
python migrate_db.py
```

---

## 💡 Key Design Decisions

| Decision | Rationale |
|---|---|
| **Local nutrition DB** | No API key, no rate limits, offline support, includes Indian foods |
| **Qwen 2.5-0.5B LLM** | 0.5B params — runs on CPU, privacy-preserving, no cloud calls |
| **Lazy LLM loading** | Doesn't block app startup; loads only on first chat request |
| **SQLite** | Zero-config, file-based, perfect for local single-user deployment |
| **IST handling in Python** | SQLite stores UTC; IST math in Python avoids DB-level complexity |
| **Custom YOLOv8 model** | Fine-tuned for fruits & vegetables for higher food-specific accuracy |
| **3-tier nutrition lookup** | Handles typos, plurals, and partial names gracefully |
| **Glassmorphism dark UI** | Premium modern aesthetic that encourages engagement |
| **AJAX profile sections** | No full page reloads between profile tabs — smoother UX |
| **RAG chatbot pattern** | Grounds LLM in real nutrition data, reducing hallucinations |

---

*NutriTrack — Diet Planning Application*  
*Repository: [sai-kumar-277/Diet-Planning](https://github.com/sai-kumar-277/Diet-Planning)*
