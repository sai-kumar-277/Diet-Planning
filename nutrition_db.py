"""
Local Nutrition Database — replaces the Nutritionix API.
All values are per single standard serving.
"""

from difflib import get_close_matches

# ── Nutrition data: { food_name: {calories, protein, fat, carbs} } ──────────
# Values are approximate per 1 standard serving.
NUTRITION_DATA = {
    # ─── Indian foods ───────────────────────────────────────────────────
    "idli":              {"calories": 39,   "protein": 1.0,  "fat": 0.2,  "carbs": 8.0},
    "dosa":              {"calories": 133,  "protein": 3.5,  "fat": 3.0,  "carbs": 22.0},
    "masala dosa":       {"calories": 206,  "protein": 5.0,  "fat": 7.0,  "carbs": 30.0},
    "vada":              {"calories": 171,  "protein": 5.0,  "fat": 10.0, "carbs": 15.0},
    "medu vada":         {"calories": 171,  "protein": 5.0,  "fat": 10.0, "carbs": 15.0},
    "upma":              {"calories": 185,  "protein": 4.5,  "fat": 6.0,  "carbs": 28.0},
    "poha":              {"calories": 180,  "protein": 3.5,  "fat": 5.0,  "carbs": 30.0},
    "pongal":            {"calories": 200,  "protein": 5.0,  "fat": 7.0,  "carbs": 30.0},
    "sambar":            {"calories": 65,   "protein": 3.0,  "fat": 1.5,  "carbs": 10.0},
    "rasam":             {"calories": 30,   "protein": 1.0,  "fat": 0.5,  "carbs": 5.0},
    "curd rice":         {"calories": 207,  "protein": 5.0,  "fat": 5.0,  "carbs": 35.0},
    "lemon rice":        {"calories": 220,  "protein": 4.0,  "fat": 6.0,  "carbs": 38.0},
    "tamarind rice":     {"calories": 230,  "protein": 4.0,  "fat": 5.0,  "carbs": 40.0},
    "roti":              {"calories": 71,   "protein": 2.7,  "fat": 0.4,  "carbs": 15.0},
    "chapati":           {"calories": 71,   "protein": 2.7,  "fat": 0.4,  "carbs": 15.0},
    "naan":              {"calories": 262,  "protein": 8.7,  "fat": 5.0,  "carbs": 45.0},
    "paratha":           {"calories": 260,  "protein": 5.0,  "fat": 12.0, "carbs": 32.0},
    "aloo paratha":      {"calories": 300,  "protein": 6.0,  "fat": 14.0, "carbs": 38.0},
    "puri":              {"calories": 101,  "protein": 2.0,  "fat": 5.0,  "carbs": 12.0},
    "bhatura":           {"calories": 290,  "protein": 5.0,  "fat": 15.0, "carbs": 33.0},
    "chole":             {"calories": 210,  "protein": 10.0, "fat": 6.0,  "carbs": 30.0},
    "chole bhature":     {"calories": 500,  "protein": 15.0, "fat": 21.0, "carbs": 63.0},
    "rajma":             {"calories": 180,  "protein": 9.0,  "fat": 4.0,  "carbs": 27.0},
    "dal":               {"calories": 104,  "protein": 6.0,  "fat": 1.8,  "carbs": 16.0},
    "dal fry":           {"calories": 150,  "protein": 7.0,  "fat": 5.0,  "carbs": 18.0},
    "dal makhani":       {"calories": 236,  "protein": 9.0,  "fat": 10.0, "carbs": 28.0},
    "lentils":           {"calories": 104,  "protein": 6.0,  "fat": 1.8,  "carbs": 16.0},
    "paneer":            {"calories": 265,  "protein": 18.0, "fat": 20.0, "carbs": 2.0},
    "palak paneer":      {"calories": 220,  "protein": 14.0, "fat": 15.0, "carbs": 8.0},
    "paneer butter masala": {"calories": 350, "protein": 15.0, "fat": 25.0, "carbs": 12.0},
    "butter chicken":    {"calories": 240,  "protein": 18.0, "fat": 14.0, "carbs": 10.0},
    "chicken curry":     {"calories": 220,  "protein": 20.0, "fat": 12.0, "carbs": 8.0},
    "chicken tikka":     {"calories": 150,  "protein": 22.0, "fat": 5.0,  "carbs": 3.0},
    "tandoori chicken":  {"calories": 195,  "protein": 27.0, "fat": 8.0,  "carbs": 3.0},
    "fish curry":        {"calories": 180,  "protein": 20.0, "fat": 8.0,  "carbs": 6.0},
    "biryani":           {"calories": 290,  "protein": 12.0, "fat": 10.0, "carbs": 40.0},
    "chicken biryani":   {"calories": 350,  "protein": 18.0, "fat": 13.0, "carbs": 42.0},
    "veg biryani":       {"calories": 250,  "protein": 6.0,  "fat": 8.0,  "carbs": 40.0},
    "pulao":             {"calories": 210,  "protein": 5.0,  "fat": 6.0,  "carbs": 35.0},
    "fried rice":        {"calories": 238,  "protein": 5.5,  "fat": 8.0,  "carbs": 36.0},
    "khichdi":           {"calories": 180,  "protein": 6.0,  "fat": 4.0,  "carbs": 28.0},
    "aloo gobi":         {"calories": 130,  "protein": 3.0,  "fat": 5.0,  "carbs": 18.0},
    "bhindi":            {"calories": 80,   "protein": 2.0,  "fat": 4.0,  "carbs": 9.0},
    "baingan bharta":    {"calories": 120,  "protein": 3.0,  "fat": 6.0,  "carbs": 14.0},
    "raita":             {"calories": 60,   "protein": 3.0,  "fat": 2.0,  "carbs": 6.0},
    "chutney":           {"calories": 30,   "protein": 0.5,  "fat": 0.5,  "carbs": 6.0},
    "pickle":            {"calories": 20,   "protein": 0.3,  "fat": 1.0,  "carbs": 2.0},
    "papad":             {"calories": 45,   "protein": 2.5,  "fat": 0.5,  "carbs": 7.0},
    "samosa":            {"calories": 262,  "protein": 4.5,  "fat": 15.0, "carbs": 28.0},
    "pakora":            {"calories": 175,  "protein": 4.0,  "fat": 10.0, "carbs": 18.0},
    "jalebi":            {"calories": 150,  "protein": 1.0,  "fat": 6.0,  "carbs": 24.0},
    "gulab jamun":       {"calories": 175,  "protein": 2.0,  "fat": 8.0,  "carbs": 24.0},
    "rasgulla":          {"calories": 186,  "protein": 4.0,  "fat": 1.0,  "carbs": 40.0},
    "laddu":             {"calories": 180,  "protein": 3.0,  "fat": 8.0,  "carbs": 24.0},
    "halwa":             {"calories": 250,  "protein": 3.0,  "fat": 12.0, "carbs": 34.0},
    "kheer":             {"calories": 160,  "protein": 4.0,  "fat": 5.0,  "carbs": 25.0},
    "pav bhaji":         {"calories": 400,  "protein": 10.0, "fat": 18.0, "carbs": 50.0},
    "vada pav":          {"calories": 290,  "protein": 6.0,  "fat": 13.0, "carbs": 38.0},
    "pani puri":         {"calories": 35,   "protein": 0.5,  "fat": 1.0,  "carbs": 6.0},
    "bhel puri":         {"calories": 180,  "protein": 4.0,  "fat": 5.0,  "carbs": 30.0},
    "uttapam":           {"calories": 200,  "protein": 5.0,  "fat": 6.0,  "carbs": 30.0},
    "pesarattu":         {"calories": 110,  "protein": 6.0,  "fat": 2.0,  "carbs": 17.0},
    "puttu":             {"calories": 190,  "protein": 4.0,  "fat": 3.0,  "carbs": 38.0},
    "appam":             {"calories": 120,  "protein": 2.0,  "fat": 1.5,  "carbs": 25.0},

    # ─── Breakfast / Western ────────────────────────────────────────────
    "egg":               {"calories": 78,   "protein": 6.3,  "fat": 5.3,  "carbs": 0.6},
    "boiled egg":        {"calories": 78,   "protein": 6.3,  "fat": 5.3,  "carbs": 0.6},
    "fried egg":         {"calories": 90,   "protein": 6.3,  "fat": 7.0,  "carbs": 0.4},
    "omelette":          {"calories": 154,  "protein": 11.0, "fat": 12.0, "carbs": 0.7},
    "scrambled eggs":    {"calories": 147,  "protein": 10.0, "fat": 11.0, "carbs": 1.6},
    "toast":             {"calories": 75,   "protein": 2.6,  "fat": 1.0,  "carbs": 14.0},
    "bread":             {"calories": 75,   "protein": 2.6,  "fat": 1.0,  "carbs": 14.0},
    "white bread":       {"calories": 75,   "protein": 2.6,  "fat": 1.0,  "carbs": 14.0},
    "brown bread":       {"calories": 73,   "protein": 3.6,  "fat": 1.1,  "carbs": 12.0},
    "butter":            {"calories": 102,  "protein": 0.1,  "fat": 11.5, "carbs": 0.0},
    "jam":               {"calories": 56,   "protein": 0.1,  "fat": 0.0,  "carbs": 14.0},
    "cereal":            {"calories": 130,  "protein": 3.0,  "fat": 1.0,  "carbs": 28.0},
    "cornflakes":        {"calories": 100,  "protein": 2.0,  "fat": 0.2,  "carbs": 24.0},
    "oatmeal":           {"calories": 150,  "protein": 5.0,  "fat": 2.5,  "carbs": 27.0},
    "oats":              {"calories": 150,  "protein": 5.0,  "fat": 2.5,  "carbs": 27.0},
    "pancake":           {"calories": 175,  "protein": 5.0,  "fat": 6.0,  "carbs": 25.0},
    "waffle":            {"calories": 218,  "protein": 6.0,  "fat": 10.0, "carbs": 25.0},
    "muesli":            {"calories": 170,  "protein": 5.0,  "fat": 4.0,  "carbs": 30.0},
    "granola":           {"calories": 210,  "protein": 5.0,  "fat": 8.0,  "carbs": 30.0},
    "yogurt":            {"calories": 100,  "protein": 5.0,  "fat": 2.5,  "carbs": 15.0},
    "greek yogurt":      {"calories": 130,  "protein": 12.0, "fat": 5.0,  "carbs": 8.0},

    # ─── Fruits ─────────────────────────────────────────────────────────
    "apple":             {"calories": 95,   "protein": 0.5,  "fat": 0.3,  "carbs": 25.0},
    "banana":            {"calories": 105,  "protein": 1.3,  "fat": 0.4,  "carbs": 27.0},
    "orange":            {"calories": 62,   "protein": 1.2,  "fat": 0.2,  "carbs": 15.0},
    "mango":             {"calories": 99,   "protein": 1.4,  "fat": 0.6,  "carbs": 25.0},
    "grapes":            {"calories": 62,   "protein": 0.6,  "fat": 0.3,  "carbs": 16.0},
    "watermelon":        {"calories": 46,   "protein": 0.9,  "fat": 0.2,  "carbs": 11.5},
    "pineapple":         {"calories": 82,   "protein": 0.9,  "fat": 0.2,  "carbs": 21.6},
    "papaya":            {"calories": 55,   "protein": 0.9,  "fat": 0.1,  "carbs": 14.0},
    "pomegranate":       {"calories": 83,   "protein": 1.7,  "fat": 1.2,  "carbs": 19.0},
    "guava":             {"calories": 37,   "protein": 1.4,  "fat": 0.5,  "carbs": 8.0},
    "strawberry":        {"calories": 4,    "protein": 0.1,  "fat": 0.0,  "carbs": 0.9},
    "blueberry":         {"calories": 1,    "protein": 0.0,  "fat": 0.0,  "carbs": 0.2},
    "kiwi":              {"calories": 42,   "protein": 0.8,  "fat": 0.4,  "carbs": 10.0},
    "pear":              {"calories": 101,  "protein": 0.7,  "fat": 0.3,  "carbs": 27.0},
    "peach":             {"calories": 59,   "protein": 1.4,  "fat": 0.4,  "carbs": 14.0},
    "plum":              {"calories": 30,   "protein": 0.5,  "fat": 0.2,  "carbs": 7.5},
    "cherry":            {"calories": 5,    "protein": 0.1,  "fat": 0.0,  "carbs": 1.0},
    "lychee":            {"calories": 6,    "protein": 0.1,  "fat": 0.0,  "carbs": 1.5},
    "coconut":           {"calories": 159,  "protein": 1.5,  "fat": 15.0, "carbs": 7.0},
    "dates":             {"calories": 20,   "protein": 0.2,  "fat": 0.0,  "carbs": 5.3},
    "fig":               {"calories": 37,   "protein": 0.4,  "fat": 0.2,  "carbs": 10.0},

    # ─── Vegetables ─────────────────────────────────────────────────────
    "carrot":            {"calories": 25,   "protein": 0.6,  "fat": 0.1,  "carbs": 6.0},
    "tomato":            {"calories": 22,   "protein": 1.1,  "fat": 0.2,  "carbs": 4.8},
    "potato":            {"calories": 163,  "protein": 4.3,  "fat": 0.2,  "carbs": 37.0},
    "sweet potato":      {"calories": 103,  "protein": 2.3,  "fat": 0.1,  "carbs": 24.0},
    "onion":             {"calories": 44,   "protein": 1.2,  "fat": 0.1,  "carbs": 10.0},
    "cucumber":          {"calories": 16,   "protein": 0.7,  "fat": 0.1,  "carbs": 3.6},
    "spinach":           {"calories": 7,    "protein": 0.9,  "fat": 0.1,  "carbs": 1.1},
    "cabbage":           {"calories": 22,   "protein": 1.3,  "fat": 0.1,  "carbs": 5.2},
    "cauliflower":       {"calories": 25,   "protein": 1.9,  "fat": 0.3,  "carbs": 5.0},
    "broccoli":          {"calories": 31,   "protein": 2.6,  "fat": 0.3,  "carbs": 6.0},
    "beans":             {"calories": 31,   "protein": 1.8,  "fat": 0.1,  "carbs": 7.0},
    "mushroom":          {"calories": 22,   "protein": 3.1,  "fat": 0.3,  "carbs": 3.3},
    "corn":              {"calories": 96,   "protein": 3.4,  "fat": 1.5,  "carbs": 21.0},
    "peas":              {"calories": 62,   "protein": 4.1,  "fat": 0.4,  "carbs": 11.0},
    "lettuce":           {"calories": 5,    "protein": 0.5,  "fat": 0.1,  "carbs": 1.0},
    "beetroot":          {"calories": 44,   "protein": 1.7,  "fat": 0.2,  "carbs": 10.0},

    # ─── Rice, Grains, Staples ──────────────────────────────────────────
    "rice":              {"calories": 206,  "protein": 4.3,  "fat": 0.4,  "carbs": 45.0},
    "white rice":        {"calories": 206,  "protein": 4.3,  "fat": 0.4,  "carbs": 45.0},
    "brown rice":        {"calories": 216,  "protein": 5.0,  "fat": 1.8,  "carbs": 45.0},
    "pasta":             {"calories": 220,  "protein": 8.0,  "fat": 1.3,  "carbs": 43.0},
    "noodles":           {"calories": 220,  "protein": 7.0,  "fat": 3.0,  "carbs": 40.0},
    "maggi":             {"calories": 205,  "protein": 4.5,  "fat": 8.5,  "carbs": 28.0},

    # ─── Meat / Protein ────────────────────────────────────────────────
    "chicken":           {"calories": 165,  "protein": 31.0, "fat": 3.6,  "carbs": 0.0},
    "chicken breast":    {"calories": 165,  "protein": 31.0, "fat": 3.6,  "carbs": 0.0},
    "chicken thigh":     {"calories": 209,  "protein": 26.0, "fat": 10.9, "carbs": 0.0},
    "chicken wings":     {"calories": 203,  "protein": 30.5, "fat": 8.1,  "carbs": 0.0},
    "mutton":            {"calories": 250,  "protein": 25.0, "fat": 16.0, "carbs": 0.0},
    "lamb":              {"calories": 250,  "protein": 25.0, "fat": 16.0, "carbs": 0.0},
    "fish":              {"calories": 136,  "protein": 20.0, "fat": 5.5,  "carbs": 0.0},
    "salmon":            {"calories": 208,  "protein": 20.0, "fat": 13.0, "carbs": 0.0},
    "tuna":              {"calories": 132,  "protein": 28.0, "fat": 1.0,  "carbs": 0.0},
    "prawns":            {"calories": 85,   "protein": 20.0, "fat": 0.5,  "carbs": 0.0},
    "shrimp":            {"calories": 85,   "protein": 20.0, "fat": 0.5,  "carbs": 0.0},
    "beef":              {"calories": 250,  "protein": 26.0, "fat": 15.0, "carbs": 0.0},
    "pork":              {"calories": 242,  "protein": 27.0, "fat": 14.0, "carbs": 0.0},
    "bacon":             {"calories": 42,   "protein": 3.0,  "fat": 3.3,  "carbs": 0.1},
    "sausage":           {"calories": 170,  "protein": 7.0,  "fat": 15.0, "carbs": 2.0},
    "turkey":            {"calories": 135,  "protein": 30.0, "fat": 1.0,  "carbs": 0.0},
    "tofu":              {"calories": 76,   "protein": 8.0,  "fat": 4.8,  "carbs": 1.9},

    # ─── Dairy ──────────────────────────────────────────────────────────
    "milk":              {"calories": 103,  "protein": 8.0,  "fat": 2.4,  "carbs": 12.0},
    "cheese":            {"calories": 113,  "protein": 7.0,  "fat": 9.0,  "carbs": 0.4},
    "curd":              {"calories": 98,   "protein": 5.0,  "fat": 4.5,  "carbs": 10.0},
    "buttermilk":        {"calories": 40,   "protein": 2.0,  "fat": 1.0,  "carbs": 5.0},
    "lassi":             {"calories": 130,  "protein": 4.0,  "fat": 3.0,  "carbs": 22.0},
    "paneer tikka":      {"calories": 280,  "protein": 18.0, "fat": 20.0, "carbs": 5.0},
    "ghee":              {"calories": 112,  "protein": 0.0,  "fat": 12.7, "carbs": 0.0},
    "cream":             {"calories": 51,   "protein": 0.4,  "fat": 5.5,  "carbs": 0.4},
    "ice cream":         {"calories": 207,  "protein": 3.5,  "fat": 11.0, "carbs": 24.0},
    "chocolate ice cream":{"calories": 216, "protein": 3.8,  "fat": 11.0, "carbs": 28.0},
    "vanilla ice cream": {"calories": 207,  "protein": 3.5,  "fat": 11.0, "carbs": 24.0},

    # ─── Fast food / Snacks ─────────────────────────────────────────────
    "pizza":             {"calories": 266,  "protein": 11.0, "fat": 10.0, "carbs": 33.0},
    "burger":            {"calories": 354,  "protein": 20.0, "fat": 17.0, "carbs": 29.0},
    "french fries":      {"calories": 312,  "protein": 3.4,  "fat": 15.0, "carbs": 41.0},
    "sandwich":          {"calories": 250,  "protein": 10.0, "fat": 10.0, "carbs": 30.0},
    "hot dog":           {"calories": 290,  "protein": 10.0, "fat": 18.0, "carbs": 22.0},
    "fried chicken":     {"calories": 320,  "protein": 25.0, "fat": 18.0, "carbs": 15.0},
    "nuggets":           {"calories": 286,  "protein": 15.0, "fat": 18.0, "carbs": 16.0},
    "wrap":              {"calories": 300,  "protein": 12.0, "fat": 12.0, "carbs": 35.0},
    "taco":              {"calories": 210,  "protein": 9.0,  "fat": 10.0, "carbs": 21.0},
    "chips":             {"calories": 152,  "protein": 2.0,  "fat": 10.0, "carbs": 15.0},
    "popcorn":           {"calories": 93,   "protein": 3.0,  "fat": 1.0,  "carbs": 19.0},
    "biscuit":           {"calories": 50,   "protein": 0.7,  "fat": 2.0,  "carbs": 7.5},
    "cookie":            {"calories": 72,   "protein": 0.8,  "fat": 3.5,  "carbs": 9.5},
    "cake":              {"calories": 257,  "protein": 3.5,  "fat": 11.0, "carbs": 38.0},
    "brownie":           {"calories": 227,  "protein": 2.7,  "fat": 9.0,  "carbs": 36.0},
    "donut":             {"calories": 253,  "protein": 4.0,  "fat": 14.0, "carbs": 30.0},
    "muffin":            {"calories": 340,  "protein": 5.0,  "fat": 13.0, "carbs": 51.0},
    "chocolate":         {"calories": 155,  "protein": 1.4,  "fat": 8.7,  "carbs": 17.0},

    # ─── Drinks ─────────────────────────────────────────────────────────
    "tea":               {"calories": 2,    "protein": 0.0,  "fat": 0.0,  "carbs": 0.5},
    "coffee":            {"calories": 2,    "protein": 0.3,  "fat": 0.0,  "carbs": 0.0},
    "green tea":         {"calories": 0,    "protein": 0.0,  "fat": 0.0,  "carbs": 0.0},
    "chai":              {"calories": 72,   "protein": 2.5,  "fat": 2.5,  "carbs": 10.0},
    "masala chai":       {"calories": 72,   "protein": 2.5,  "fat": 2.5,  "carbs": 10.0},
    "orange juice":      {"calories": 112,  "protein": 1.7,  "fat": 0.5,  "carbs": 26.0},
    "apple juice":       {"calories": 114,  "protein": 0.3,  "fat": 0.3,  "carbs": 28.0},
    "smoothie":          {"calories": 200,  "protein": 5.0,  "fat": 3.0,  "carbs": 40.0},
    "milkshake":         {"calories": 270,  "protein": 7.0,  "fat": 8.0,  "carbs": 42.0},
    "coconut water":     {"calories": 46,   "protein": 1.7,  "fat": 0.5,  "carbs": 9.0},
    "lemonade":          {"calories": 99,   "protein": 0.2,  "fat": 0.1,  "carbs": 26.0},
    "soda":              {"calories": 140,  "protein": 0.0,  "fat": 0.0,  "carbs": 39.0},
    "cola":              {"calories": 140,  "protein": 0.0,  "fat": 0.0,  "carbs": 39.0},
    "beer":              {"calories": 154,  "protein": 1.6,  "fat": 0.0,  "carbs": 13.0},
    "wine":              {"calories": 125,  "protein": 0.1,  "fat": 0.0,  "carbs": 4.0},

    # ─── Nuts / Seeds ───────────────────────────────────────────────────
    "almonds":           {"calories": 164,  "protein": 6.0,  "fat": 14.0, "carbs": 6.0},
    "cashews":           {"calories": 157,  "protein": 5.2,  "fat": 12.4, "carbs": 8.6},
    "peanuts":           {"calories": 161,  "protein": 7.3,  "fat": 14.0, "carbs": 4.6},
    "walnuts":           {"calories": 185,  "protein": 4.3,  "fat": 18.5, "carbs": 3.9},
    "pistachios":        {"calories": 156,  "protein": 5.7,  "fat": 12.4, "carbs": 7.7},
    "sunflower seeds":   {"calories": 165,  "protein": 5.5,  "fat": 14.0, "carbs": 6.5},
    "pumpkin seeds":     {"calories": 151,  "protein": 7.0,  "fat": 13.0, "carbs": 5.0},
    "chia seeds":        {"calories": 138,  "protein": 4.7,  "fat": 8.7,  "carbs": 12.0},
    "flax seeds":        {"calories": 150,  "protein": 5.1,  "fat": 11.8, "carbs": 8.1},
    "peanut butter":     {"calories": 188,  "protein": 8.0,  "fat": 16.0, "carbs": 6.0},

    # ─── Miscellaneous ──────────────────────────────────────────────────
    "honey":             {"calories": 64,   "protein": 0.1,  "fat": 0.0,  "carbs": 17.0},
    "sugar":             {"calories": 16,   "protein": 0.0,  "fat": 0.0,  "carbs": 4.2},
    "salad":             {"calories": 20,   "protein": 1.5,  "fat": 0.2,  "carbs": 3.5},
    "soup":              {"calories": 80,   "protein": 4.0,  "fat": 2.0,  "carbs": 10.0},
    "protein shake":     {"calories": 150,  "protein": 25.0, "fat": 2.0,  "carbs": 8.0},
    "energy bar":        {"calories": 200,  "protein": 10.0, "fat": 7.0,  "carbs": 25.0},
}


def lookup_nutrition(food_item):
    """
    Look up a food item in the local database.
    Uses exact match first, then fuzzy matching.
    Returns a dict that mirrors the Nutritionix API response format,
    or None if no match is found.
    """
    food_item = food_item.lower().strip()

    # 1) Exact match
    if food_item in NUTRITION_DATA:
        data = NUTRITION_DATA[food_item]
        return _format_result(food_item, data)

    # 2) Check if the query is a substring of any key, or vice-versa
    for key in NUTRITION_DATA:
        if food_item in key or key in food_item:
            data = NUTRITION_DATA[key]
            return _format_result(key, data)

    # 3) Fuzzy match (close spelling)
    matches = get_close_matches(food_item, NUTRITION_DATA.keys(), n=1, cutoff=0.6)
    if matches:
        best = matches[0]
        data = NUTRITION_DATA[best]
        return _format_result(best, data)

    return None


def lookup_nutrition_query(query):
    """
    Process a natural-language query like '2 eggs and 1 toast'.
    Returns a dict in the same structure as Nutritionix's /v2/natural/nutrients
    i.e. {"foods": [...]}.
    """
    import re as _re

    # Tokenise on 'and', commas, or just spaces with a leading number
    parts = _re.split(r'\band\b|,', query.lower())
    foods = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Try to extract a leading quantity  e.g. "2 eggs"
        m = _re.match(r'^(\d+)\s+(.+)$', part)
        if m:
            qty = int(m.group(1))
            name = m.group(2).strip()
        else:
            qty = 1
            name = part

        result = lookup_nutrition(name)
        if result:
            # Multiply nutrition by quantity
            result['nf_calories']           *= qty
            result['nf_protein']            *= qty
            result['nf_total_fat']          *= qty
            result['nf_total_carbohydrate'] *= qty
            result['serving_qty']            = qty
            foods.append(result)

    return {"foods": foods}


def _format_result(food_name, data):
    """Return a dict that looks like a single Nutritionix food object."""
    return {
        "food_name":              food_name,
        "serving_qty":            1,
        "serving_unit":           "serving",
        "nf_calories":            data["calories"],
        "nf_protein":             data["protein"],
        "nf_total_fat":           data["fat"],
        "nf_total_carbohydrate":  data["carbs"],
    }
