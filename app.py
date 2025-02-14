from flask import Flask, request, jsonify
from flask_cors import CORS  # ✅ Import CORS
import json
import openai
import os
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime

# Load API key from .env file.
load_dotenv()
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app)  # ✅ Enable CORS globally

# Apply rate limiting to prevent abuse (10 requests per minute per IP).
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["10 per minute"]
)

# Ensure the "cocktail_recipes" directory exists
OUTPUT_DIR = "cocktail_recipes"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_cocktail(ingredients, drink_preference, flavor_preference):
    """
    Uses OpenAI API to generate a structured JSON cocktail recipe.
    Saves the output as a JSON file instead of printing it to the terminal.
    """
    prompt = f"""
    You are a professional mixologist. Based on the provided inputs, create a unique cocktail recipe.
    
    **Inputs:**
    - Ingredients available: {', '.join(ingredients)}
    - Preferred drink style: {drink_preference}
    - Desired flavor profile: {flavor_preference}
    
    **Response Format (valid JSON only, no extra text):**
    
    {{
      "name": "Cocktail Name",
      "ingredients": [
        "Quantity + Ingredient (e.g., '2 oz Vodka')",
        "Quantity + Ingredient (or substitution, if needed)"
      ],
      "preparation": "Step-by-step preparation instructions.",
      "glassware": "Recommended glass type.",
      "garnish": "Suggested garnish.",
      "backstory": "A fun and creative story about the cocktail."
    }}

    **Important:**
    - Use **imperial units** (oz, tsp, cups) instead of milliliters.
    - Return only JSON—do not include any additional text or commentary.
    - If you are using grenadine, don't use specific volumes, say only "a lining of"
    - If you are using bitters, don't use specific volumes, say only "a dash of"
    - If you are using simple syru[], don't use specific volumes, say only "a splash of"
    - If you are using lemon/lime juice, don't use specific volumes, say only "a squeeze of"
    - If you are using soda water, tonic or cola don't use specific volumes, say only "top with"
    """

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an expert mixologist responding with structured JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )

        # Extract the raw response
        raw_response = response.choices[0].message.content.strip()

        # Ensure valid JSON format
        structured_response = json.loads(raw_response)

        # Validate that all required fields exist
        required_fields = ["name", "ingredients", "preparation", "glassware", "garnish", "backstory"]
        for field in required_fields:
            if field not in structured_response:
                raise ValueError(f"Missing field in AI response: {field}")

        # Create a filename based on cocktail name & timestamp
        sanitized_name = structured_response["name"].replace(" ", "_").lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{sanitized_name}_{timestamp}.json"

        # Save the cocktail as a JSON file
        file_path = os.path.join(OUTPUT_DIR, filename)
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(structured_response, file, indent=4)

        return {"message": f"Cocktail saved successfully!", "file": filename}

    except openai.RateLimitError:
        return {"error": "Rate limit exceeded. Please wait and try again."}

    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON. The AI might have returned an invalid response."}

    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}

@app.route('/generate-cocktail', methods=['POST'])
@limiter.limit("10 per minute")  # Apply rate limiting
def generate_cocktail_endpoint():
    """
    API endpoint for generating a structured cocktail recipe.
    """
    try:
        data = request.json
        ingredients = data.get("ingredients", [])
        drink_preference = data.get("drink_preference", "any")
        flavor_preference = data.get("flavor_preference", "balanced")

        if not ingredients:
            return jsonify({"error": "Please provide at least one ingredient."}), 400

        response = generate_cocktail(ingredients, drink_preference, flavor_preference)

        return jsonify(response)  # ✅ Always returns structured JSON

    except Exception as e:
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
