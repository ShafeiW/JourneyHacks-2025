import openai
import os
from dotenv import load_dotenv

# Load API key
load_dotenv()
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def recommend_cocktail_by_mood(mood):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional mixologist and cocktail expert."},
                {"role": "user", "content": f"I am feeling {mood}. Can you recommend a cocktail that matches my mood? Please include the cocktail name, ingredients, and preparation steps."}
            ],
            max_tokens=200
        )

        cocktail_suggestion = response.choices[0].message.content
        return cocktail_suggestion

    except Exception as e:
        return f"❌ Error fetching cocktail recommendation: {str(e)}"

if __name__ == "__main__":
    mood = input("Enter your mood: ")
    cocktail = recommend_cocktail_by_mood(mood)
    print("\n🍹 Recommended Cocktail:\n", cocktail)
