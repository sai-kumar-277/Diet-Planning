from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch
import os
import threading

# Lazy loading to avoid blocking app startup
_pipeline = None
_lock = threading.Lock()

def get_llm():
    global _pipeline
    with _lock:
        if _pipeline is None:
            print("[INFO] Loading Local LLM... This may take a moment if it's the first time (downloading weights).")
            model_id = "Qwen/Qwen2.5-0.5B-Instruct"
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            # if cpu only, device_map="auto" might fail, so we leave it default
            
            _pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=150,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1,
            )
            print("[INFO] Local LLM loaded successfully.")
    return _pipeline

def generate_diet_advice(food_item, nutrition_data, user_profile, health_profile):
    """
    Uses the local LLM to give personalized dietary advice based on the food and user profile.
    """
    llm = get_llm()
    
    # Build the prompt
    system_prompt = "You are a helpful and knowledgeable AI Dietitian."
    user_context = []
    
    if user_profile:
        user_context.append(f"The user is {user_profile.age} years old, {user_profile.height} cm tall, and weighs {user_profile.weight} kg.")
        if user_profile.goals:
            user_context.append(f"Their fitness goal is: {user_profile.goals}.")
            
    if health_profile and health_profile.condition:
        user_context.append(f"They have the following health condition: {health_profile.condition}.")
        if health_profile.avoid_foods:
            user_context.append(f"They need to avoid: {health_profile.avoid_foods}.")
            
    context_str = " ".join(user_context)
    
    nut_str = "Unknown"
    if nutrition_data:
        nut_str = f"Calories: {nutrition_data['nf_calories']} kcal, Protein: {nutrition_data['nf_protein']}g, Carbs: {nutrition_data['nf_total_carbohydrate']}g, Fat: {nutrition_data['nf_total_fat']}g"

    prompt = f"""<|im_start|>system
{system_prompt}
<|im_end|>
<|im_start|>user
Context about the user: {context_str}
Food item they want to eat: {food_item}
Nutrition data for this food: {nut_str}

Based on their health conditions, goals, and the nutrition data, can they eat this food? Give a brief, direct, and supportive answer (max 3 sentences).
<|im_end|>
<|im_start|>assistant
"""
    
    try:
        response = llm(prompt, return_full_text=False)[0]['generated_text']
        return response.strip()
    except Exception as e:
        print(f"[ERROR] LLM Generation failed: {e}")
        return "I am unable to provide specific advice right now due to an error, but generally monitor your portion sizes and consult your doctor."

def generate_chatbot_reply(user_message, relevant_nutrition, user_profile=None, health_profile=None):
    """
    RAG-style chatbot reply.
    """
    llm = get_llm()
    
    system_prompt = "You are an AI Dietitian chatbot. Answer the user's questions about food, calories, and diet. Keep it short and helpful."
    
    user_context = []
    if user_profile:
        user_context.append(f"The user is {user_profile.age} years old, {user_profile.height} cm tall, and weighs {user_profile.weight} kg.")
        if user_profile.goals:
            user_context.append(f"Their fitness goal and diet preferences: {user_profile.goals}.")
            
    if health_profile and health_profile.condition:
        user_context.append(f"They have the following health condition: {health_profile.condition}.")
        if health_profile.avoid_foods:
            user_context.append(f"They need to avoid: {health_profile.avoid_foods}.")
            
    context_str = " ".join(user_context)
    if context_str:
        system_prompt += f"\n\nTake the following user context into account when answering:\n{context_str}"

    nut_context = ""
    if relevant_nutrition and "foods" in relevant_nutrition and relevant_nutrition["foods"]:
        nut_context = "Here is some retrieved nutrition data that might help: "
        for f in relevant_nutrition["foods"]:
            nut_context += f"{f['food_name']} ({f['nf_calories']} kcal). "
            
    prompt = f"""<|im_start|>system
{system_prompt}
<|im_end|>
<|im_start|>user
{nut_context}
User message: {user_message}
<|im_end|>
<|im_start|>assistant
"""

    try:
        response = llm(prompt, return_full_text=False)[0]['generated_text']
        return response.strip()
    except Exception as e:
        print(f"[ERROR] LLM Generation failed: {e}")
        return "I'm having trouble thinking right now. Please try again later."
