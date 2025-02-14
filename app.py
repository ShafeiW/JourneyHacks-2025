import openai
from openai import OpenAIError  # ✅ Import correct error handling
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime

# Load API key from .env file
load_dotenv()
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app, resources={r"/generate-cocktail": {"origins": "*"}})

# Apply rate limiting to prevent abuse
limiter = Limiter(get_remote_address, app=app, default_limits=["10 per minute"])

# Ensure output directory exists
OUTPUT_DIR = "cocktail_recipes"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_cocktail(ingredients, drink_preference, flavor_preference):
    """
    Uses OpenAI API to generate a structured JSON cocktail recipe.
    Saves the output as a JSON file.
    """
    prompt = f"""
    You are a professional mixologist. Based on the provided inputs, create a unique cocktail recipe.
    
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

        try:
            structured_response = json.loads(raw_response)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON from OpenAI"}), 500

        # Validate required fields
        required_fields = ["name", "ingredients", "preparation", "glassware", "garnish", "backstory"]
        for field in required_fields:
            if field not in structured_response:
                return jsonify({"error": f"Missing field in AI response: {field}"}), 500

        # Save cocktail to JSON file
        sanitized_name = structured_response["name"].replace(" ", "_").lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{sanitized_name}_{timestamp}.json"
        file_path = os.path.join(OUTPUT_DIR, filename)

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(structured_response, file, indent=4)

        return jsonify({"message": "Cocktail saved!", "file": filename, "recipe": structured_response})

    except OpenAIError as e:  # ✅ Correct OpenAI error handling
        return jsonify({"error": f"OpenAI API Error: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route('/generate-cocktail', methods=['POST'])
@limiter.limit("10 per minute")
def generate_cocktail_endpoint():
    try:
        data = request.json
        ingredients = data.get("ingredients", [])
        drink_preference = data.get("drink_preference", "any")
        flavor_preference = data.get("flavor_preference", "balanced")

        if not ingredients:
            return jsonify({"error": "Please provide at least one ingredient."}), 400

        response = generate_cocktail(ingredients, drink_preference, flavor_preference)

        return response

    except Exception as e:
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
