import openai
from openai import OpenAIError  # ✅ Import correct error handling
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import re
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime

# Load API key from .env file
load_dotenv()
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Apply rate limiting to prevent abuse
limiter = Limiter(get_remote_address, app=app, default_limits=["10 per minute"])

# Ensure output directory exists
OUTPUT_DIR = "cocktail_recipes"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_json(text):
    """Extracts JSON from OpenAI response using regex."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    return match.group(0) if match else None


def generate_cocktail(ingredients, drink_preference, flavor_preference):
    """
    Uses OpenAI API to generate a structured JSON cocktail recipe.
    Saves the output as a JSON file.
    """
    prompt = f"""
    You are a professional mixologist. Based on the provided inputs, create a unique cocktail recipe. DO NOT add any addition ingredients (except water or ice if needed). Only use the provided ingredients.
    For image, use "images/colour.png", where colour is the best fit colour of the cocktail based on the ingredients. you have 6 choices for colour: blue, brown, pink, red, clear, orange.

    **Inputs:**
    - Ingredients: {', '.join(ingredients)}
    - Drink Style: {drink_preference}
    - Flavor Profile: {flavor_preference}
    
    **Response Format (valid JSON only):**
    {{
      "name": "Cocktail Name",
      "ingredients": ["2 oz Vodka", "4 oz Orange Juice"],
      "preparation": "Step-by-step preparation.",
      "glassware": "Highball glass",
      "garnish": "Orange slice",
      "backstory": "Inspired by a summer sunset."
      "food_pairing": "Pairs well with grilled seafood."
      "image": "images/colour.png"
    }}
    """

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a mixologist returning structured JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )

        raw_response = response.choices[0].message.content.strip()
        structured_response = json.loads(raw_response)

        # Validate required fields
        required_fields = ["name", "ingredients", "preparation", "glassware", "garnish", "backstory", "food_pairing"]
        for field in required_fields:
            if field not in structured_response:
                return {"error": f"Missing field in AI response: {field}"}

        # Save cocktail to JSON file
        sanitized_name = structured_response["name"].replace(" ", "_").lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{sanitized_name}_{timestamp}.json"
        file_path = os.path.join(OUTPUT_DIR, filename)

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(structured_response, file, indent=4)

        return {"message": "Cocktail saved!", "file": filename, "recipe": structured_response}

    except OpenAIError as e:
        return {"error": f"OpenAI API Error: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON from OpenAI."}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@app.route('/generate-cocktail', methods=['POST'])
@limiter.limit("10 per minute")
def generate_cocktail_endpoint():
    """API endpoint to generate a cocktail based on ingredients."""
    try:
        data = request.json
        ingredients = data.get("ingredients", [])
        drink_preference = data.get("drink_preference", "any")
        flavor_preference = data.get("flavor_preference", "balanced")

        if not ingredients:
            return jsonify({"error": "Please provide at least one ingredient."}), 400

        response = generate_cocktail(ingredients, drink_preference, flavor_preference)
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500


def recommend_cocktail_by_mood(mood):
    """
    Uses OpenAI API to generate a structured JSON cocktail recipe based on mood.
    Saves the output as a JSON file.
    """
    prompt = f"""
    You are a professional mixologist. Recommend a cocktail that matches the mood: {mood}.
    
    Respond **only with valid JSON** in the following format:
    
    {{
      "name": "Cocktail Name",
      "ingredients": ["Quantity + Ingredient"],
      "preparation": "Step-by-step preparation instructions.",
      "glassware": "Recommended glass type.",
      "garnish": "Suggested garnish.",
      "backstory": "A fun and creative story about the cocktail."
        "food_pairing": "Suggested food pairing."
    }}
    """

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert mixologist responding with structured JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )

        raw_response = response.choices[0].message.content.strip()
        json_text = extract_json(raw_response)

        if not json_text:
            return {"error": "AI did not return a valid JSON response."}

        structured_response = json.loads(json_text)

        # Validate required fields
        required_fields = ["name", "ingredients", "preparation", "glassware", "garnish", "backstory", "food_pairing", "image"]
        for field in required_fields:
            if field not in structured_response:
                return {"error": f"Missing field in AI response: {field}"}

        # Save cocktail to JSON file
        sanitized_name = structured_response["name"].replace(" ", "_").lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{sanitized_name}_{timestamp}.json"
        file_path = os.path.join(OUTPUT_DIR, filename)

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(structured_response, file, indent=4)

        return {"message": "Cocktail saved!", "file": filename, "cocktail": structured_response}

    except OpenAIError as e:
        return {"error": f"OpenAI API Error: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON from OpenAI."}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@app.route('/recommend-cocktail-by-mood', methods=['GET'])
@limiter.limit("10 per minute")
def recommend_cocktail_by_mood_endpoint():
    """API endpoint to get a cocktail recommendation based on mood."""
    try:
        mood = request.args.get("mood", default="happy", type=str)
        response = recommend_cocktail_by_mood(mood)
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
