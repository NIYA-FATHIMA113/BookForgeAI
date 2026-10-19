from dotenv import load_dotenv

load_dotenv()

from ai_assistant.services.ai_provider import generate_ai_response


history = [
    {
        "role": "user",
        "parts": [
            {
                "text": "I run a football turf called Niya Turf."
            }
        ],
    }
]

response = generate_ai_response(history)

print(response)