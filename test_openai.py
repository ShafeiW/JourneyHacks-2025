import openai
import os
from dotenv import load_dotenv

# Load API key
load_dotenv()
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def test_openai_api():
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Change model here
            messages=[{"role": "system", "content": "You are a helpful assistant."},
                      {"role": "user", "content": "Can you confirm that my OpenAI API key is working?"}],
            max_tokens=50
        )

        print("✅ OpenAI API Key is working!")
        print("Response:", response.choices[0].message.content)
    except Exception as e:
        print("❌ OpenAI API Key test failed.")
        print("Error:", str(e))

if __name__ == "__main__":
    test_openai_api()
