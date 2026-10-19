import os

from django.test import SimpleTestCase, override_settings


class GeminiIntegrationTest(SimpleTestCase):

    @override_settings()
    def test_gemini_connection(self):
        if os.getenv("RUN_GEMINI_TESTS", "false").lower() != "true":
            self.skipTest(
                "Gemini integration tests are disabled."
            )

        from ai_assistant.services.ai_provider import generate_ai_response

        history = [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "I run a football turf "
                            "called Niya Turf."
                        )
                    }
                ],
            }
        ]

        response = generate_ai_response(history)

        self.assertTrue(response)