from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import openai
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
CORS(app, resources={r"/recommend-cocktail-by-mood": {"origins": "*"}})
# Apply rate limiting (10 requests per minute per IP)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["10 per minute"]
)

# Ensure "cocktail_recipes" directory exists
OUTPUT_DIR = "cocktail_recipes"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_json(text):
    """
    Extract JSON from OpenAI response using regex.
    """
    match = re.search(r'\{.*\}', text, re.DOTALL)  # Looks for JSON pattern in response
    if match:
        return match.group(0)  # Returns matched JSON block
    return None  # Returns None if no JSON is found

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
      "ingredients": [
        "Quantity + Ingredient (e.g., '2 oz Vodka')",
        "Quantity + Ingredient (or substitution, if needed)"
      ],
      "preparation": "Step-by-step preparation instructions.",
      "glassware": "Recommended glass type.",
      "garnish": "Suggested garnish.",
      "backstory": "A fun and creative story about the cocktail."
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

        # Extract response text
        raw_response = response.choices[0].message.content.strip()

        # Extract JSON using regex
        json_text = extract_json(raw_response)

        if not json_text:
            return {"error": "AI did not return a valid JSON response."}

        # Parse JSON
        structured_response = json.loads(json_text)

        # Validate all required fields exist
        required_fields = ["name", "ingredients", "preparation", "glassware", "garnish", "backstory"]
        for field in required_fields:
            if field not in structured_response:
                return {"error": f"Missing field in AI response: {field}"}

        # Create filename
        sanitized_name = structured_response["name"].replace(" ", "_").lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{sanitized_name}_{timestamp}.json"

        # Save the cocktail as a JSON file
        file_path = os.path.join(OUTPUT_DIR, filename)
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(structured_response, file, indent=4)

        return {"message": "Cocktail saved successfully!", "file": filename, "cocktail": structured_response}

    except openai.RateLimitError:
        return {"error": "Rate limit exceeded. Please wait and try again."}

    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON. The AI might have returned an invalid response."}

    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}

@app.route('/recommend-cocktail-by-mood', methods=['GET'])
@limiter.limit("10 per minute")
def recommend_cocktail_by_mood_endpoint():
    """
    API endpoint to get a cocktail recommendation based on mood.
    """
    try:
        mood = request.args.get("mood", default="happy", type=str)
        response = recommend_cocktail_by_mood(mood)
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
