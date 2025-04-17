import speech_recognition as sr
import re
import spacy
from textblob import Word

# Load English NLP model
nlp = spacy.load("en_core_web_sm")

# Word-to-number mappings (including common mishearings)
word_to_num = {
    "one": 1, "won": 1,
    "two": 2, "to": 2, "too": 2, "tu": 2,
    "three": 3, "tree": 3, "free": 3,
    "four": 4, "for": 4, "fore": 4,
    "five": 5, "fife": 5,
    "six": 6, "sex": 6,
    "seven": 7, "saven": 7,
    "eight": 8, "ate": 8, "aid": 8,
    "nine": 9, "mine": 9, "nighn": 9,
    "ten": 10, "then": 10, "den": 10
}

# Corrections for common food name mishearings
food_corrections = {
    "chocolate ice": "chocolate ice cream",
    "vanilla ice": "vanilla ice cream",
    "carat": "carrot", "cart": "carrot", "carrots": "carrot",
    "tomatoe": "tomato", "tomatoes": "tomato",
    "potatos": "potato",
    "mashroom": "mushroom", "mushrom": "mushroom",
    "bananna": "banana", "appel": "apple",
    "pineaple": "pineapple", "pine apple": "pineapple",
    "grapees": "grapes", "grape": "grapes",
    "onion": "onions", "bred": "bread", "toast": "bread",
    "chiken": "chicken", "eggs": "egg", "omlet": "omelette",
    "cabbag": "cabbage", "brokoli": "broccoli", "brocoly": "broccoli",
    "lettice": "lettuce", "chese": "cheese", "chesse": "cheese",
    "ricee": "rice", "chapati": "roti", "chapathi": "roti",
    "dal": "lentils", "dahl": "lentils",
    "biriyani": "biryani", "biriani": "biryani",
    "icecream": "ice cream",

    # ✅ Newly added corrections below:
    "friedrich": "fried rice", "friedrichs": "fried rice",
    "penza": "pizza", "pisa": "pizza", "peetza": "pizza",
    "burgher": "burger", "burgur": "burger", "buger": "burger",
    "pancakes": "pancake", "pan cake": "pancake", "pan cakes": "pancake",
    "chickn": "chicken", "chikn": "chicken",
    "chicken biriyani": "chicken biryani", "chiken biryani": "chicken biryani",
    "fried": "fried rice", "friedrice": "fried rice",
    "fried ricee": "fried rice", "rice": "fried rice",  # optional, can remove if needed
}


def correct_food_spelling(food):
    food = food.lower().strip()
    if food in food_corrections:
        return food_corrections[food]
    corrected = str(Word(food).correct())
    return food_corrections.get(corrected, corrected)

def get_voice_input():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        print("🎤 Say your food items (e.g. '2 eggs and 1 toast')...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("🔴 Listening now...")
        audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)
        print("✅ Audio captured...")

    try:
        text = recognizer.recognize_google(audio)
        print("📝 You said:", text)
        return text
    except sr.UnknownValueError:
        print("😕 Sorry, I couldn't understand.")
    except sr.RequestError as e:
        print(f"⚠️ Response from Google was empty or invalid: {e}")

    return None

def extract_food_quantities(text):
    text = text.lower()
    tokens = text.split()

    result = {}
    i = 0

    while i < len(tokens):
        token = tokens[i]
        quantity = 0

        # Identify quantity
        if token.isdigit():
            quantity = int(token)
        elif token in word_to_num:
            quantity = word_to_num[token]

        if quantity > 0:
            i += 1
            food_tokens = []

            # Gather food item tokens until next quantity or end
            while i < len(tokens):
                next_token = tokens[i]
                if next_token in word_to_num or next_token.isdigit():
                    break
                if next_token not in ("and", "with", "of", "for"):
                    food_tokens.append(next_token)
                i += 1

            food_name = " ".join(food_tokens).strip()
            corrected_name = correct_food_spelling(food_name)

            if corrected_name in result:
                result[corrected_name] += quantity
            else:
                result[corrected_name] = quantity
        else:
            i += 1

    return result

# --- Main Execution ---
if __name__ == "__main__":
    spoken_text = get_voice_input()
    if spoken_text:
        food_data = extract_food_quantities(spoken_text)
        print("🍱 Food Items Detected:", food_data)