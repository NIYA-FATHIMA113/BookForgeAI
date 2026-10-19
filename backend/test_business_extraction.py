import os

from django.test import SimpleTestCase


class BusinessExtractionTest(SimpleTestCase):

    def test_business_extraction(self):

        if os.getenv("RUN_GEMINI_TESTS", "false").lower() != "true":
            self.skipTest(
                "Gemini integration tests are disabled."
            )

        from ai_assistant.services.ai_provider import extract_business_info

        message = """
        I run a football turf called Niya Turf.
        We have one 5-a-side pitch.
        It costs 800 rupees per hour.
        Customers need to pay a 200 rupee deposit.
        We are open every day from 9 AM to 10 PM.
        Customers can book multiple hours.
        Our address is Test Address, Kerala.
        Our contact number is 9876543210.
        Our email is niyaturf@example.com.
        The minimum booking length is 1 hour.
        """

        result = extract_business_info(message)

        self.assertIsNotNone(result)

        print()
        print("Business name:", result.business_name)
        print("Business type:", result.business_type)
        print("Services:", result.services)
        print("Opening:", result.opening_time)
        print("Closing:", result.closing_time)
        print("Working days:", result.working_days)