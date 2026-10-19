
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY nahi mili. .env file check karo."
    )

client = genai.Client(api_key=api_key)

try:
    response = client.interactions.create(
        model="gemini-3.8-flash",
        input=(
            "You are the NLU for a voice assistant named BOB. "
            "Convert this command into a simple normalized command: "
            "'mere downloads dikhao'. "
            "Return only the command, without explanation."
        ),
    )

    print("Gemini API connected successfully!")
    print("Normalized command:", response.output_text)

except Exception as error:
    print("Gemini API test failed.")
    print("Error:", error)
