from datetime import time
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from ai_assistant.services.ai_provider import extract_time_range
from ai_assistant.schemas import BookingRequest, BusinessInfo
from ai_assistant.services.ai_provider import (
	extract_booking_request,
	generate_ai_response,
	normalize_messages,
	parse_json_response,
	assert_fallback_business_info,
)
from ai_assistant.models import AIConversation, BusinessConfiguration
from ai_assistant.services.business_setup import create_business_from_configuration
from ai_assistant.views import get_onboarding_question
from services.models import Service, Resource
from availability.models import BusinessHours
from tenants.models import Tenant
from datetime import date, timedelta


class AIProviderTests(TestCase):

	def test_normalize_messages_accepts_gemini_parts(self):
		messages = normalize_messages([
			{
				"role": "user",
				"parts": [{"text": "hello"}],
			},
			{
				"role": "model",
				"parts": [{"text": "hi"}],
			},
		])

		self.assertEqual(messages[-2:], [
			{"role": "user", "content": "hello"},
			{"role": "assistant", "content": "hi"},
		])

	def test_provider_fallback_continues_after_gemini_failure(self):
		with patch(
			"ai_assistant.services.ai_provider.gemini_generate",
			side_effect=RuntimeError("quota"),
		), patch(
			"ai_assistant.services.ai_provider.groq_generate",
			return_value="Groq response",
		) as groq:
			result = generate_ai_response([
				{"role": "user", "content": "hello"},
			])

		self.assertEqual(result, "Groq response")
		groq.assert_called_once()

	def test_empty_history_is_rejected(self):
		with self.assertRaisesRegex(
			RuntimeError,
			"No valid user message",
		):
			generate_ai_response([
				{"role": "user", "parts": [{"text": "  "}]},
			])

	def test_extraction_contracts_are_typed(self):
		business = BusinessInfo.model_validate(
			parse_json_response('{"business_name": "BookForge"}')
		)
		booking = extract_booking_request("")

		self.assertEqual(business.business_name, "BookForge")
		self.assertIsInstance(booking, BookingRequest)

	def test_onboarding_asks_one_next_required_field(self):
		configuration = BusinessInfo()
		configuration.business_name = "Niya Turf"

		question = get_onboarding_question(
			configuration,
			["business_type", "services", "working_days"],
		)

		self.assertEqual(
			question,
			"Great! I'll help you set up Niya Turf. "
			"What type of business do you run?",
		)

	def test_services_answer_advances_authenticated_onboarding(self):
		user = User.objects.create_user(
			username="onboarding-owner",
			password="test-password",
		)
		client = APIClient()
		client.force_authenticate(user=user)
		business_info = BusinessInfo(
			business_name="Hightown Turf",
			business_type="sports_turf",
		)
		services_info = BusinessInfo(
			services=[
				{"name": "Service One"},
				{"name": "Service Two"},
			],
		)

		with patch(
			"ai_assistant.views.extract_business_info",
			side_effect=[business_info, services_info],
		):
			first = client.post(
				"/api/ai/chat/",
				{"message": "I run a business called Hightown Turf."},
				format="json",
			)
			conversation_id = first.data["conversation_id"]
			second = client.post(
				"/api/ai/chat/",
				{
					"conversation_id": conversation_id,
					"message": "Service One and Service Two.",
				},
				format="json",
			)

		self.assertEqual(first.status_code, 200)
		self.assertEqual(second.status_code, 200)
		self.assertEqual(
			second.data["business_configuration"]["services"],
			[
				{"name": "Service One", "price": None, "duration_minutes": None},
				{"name": "Service Two", "price": None, "duration_minutes": None},
			],
		)
		self.assertNotIn(
			"services",
			second.data["business_configuration"]["missing_fields"],
		)

	def test_create_business_from_configuration_supports_sports_turf(self):
		user = User.objects.create_user(
			username="sports-owner",
			password="test-password",
		)
		conversation = AIConversation.objects.create(
			owner=user,
			title="Sports Turf Setup",
		)
		configuration = BusinessConfiguration.objects.create(
			conversation=conversation,
			business_name="Hightown Turf",
			business_type="sports_turf",
			services=[
				{"name": "5-a-side football"},
				{"name": "7-a-side football"},
				{"name": "birthday matches"},
				{"name": "tournament bookings"},
			],
			opening_time=time(6, 0),
			closing_time=time(23, 0),
			working_days=[
				"Monday",
				"Tuesday",
				"Wednesday",
				"Thursday",
				"Friday",
				"Saturday",
			],
			number_of_resources=2,
		)

		tenant = create_business_from_configuration(
			configuration,
			user,
			configuration.services,
		)

		self.assertEqual(tenant.business_name, "Hightown Turf")
		self.assertEqual(tenant.business_type, "sports_turf")
		self.assertEqual(Service.objects.filter(tenant=tenant).count(), 4)
		self.assertEqual(Resource.objects.filter(tenant=tenant).count(), 2)
		self.assertEqual(
			list(Resource.objects.filter(tenant=tenant).values_list("name", flat=True)),
			["Resource 1", "Resource 2"],
		)

		create_business_from_configuration(
			configuration,
			user,
			configuration.services,
		)
		self.assertEqual(Resource.objects.filter(tenant=tenant).count(), 2)
		self.assertEqual(BusinessHours.objects.filter(tenant=tenant).count(), 6)

	def test_extract_time_range(self):
		self.assertEqual(
			extract_time_range("6:00 AM to 11:00 PM"),
			("06:00", "23:00"),
		)

		self.assertEqual(
			extract_time_range("6 AM - 11 PM"),
			("06:00", "23:00"),
		)

		self.assertEqual(
			extract_time_range("06:00 - 23:00"),
			("06:00", "23:00"),
		)

	def test_assert_fallback_business_info_preserves_name_and_services(self):
		business = assert_fallback_business_info(
			"I run a football turf called Hightown Turf."
		)
		self.assertEqual(business.business_name, "Hightown Turf")
		self.assertEqual(business.business_type, "sports_turf")

		services = assert_fallback_business_info(
			"We offer 5-a-side football, 7-a-side football, birthday matches, and tournament bookings."
		)
		names = [s.name for s in services.services]
		self.assertEqual(names, [
			"5-a-side football",
			"7-a-side football",
			"birthday matches",
			"tournament bookings",
		])

		time_info = assert_fallback_business_info("6 AM to 11 PM")
		self.assertEqual(time_info.opening_time, "06:00")
		self.assertEqual(time_info.closing_time, "23:00")

	def test_complete_turf_description_is_recovered_deterministically(self):
		info = assert_fallback_business_info(
			"I run Hightown Turf. We offer 5-a-side and 7-a-side football. "
			"We are open from 6 AM to 11 PM, Monday to Saturday, "
			"and have two pitches."
		)
		self.assertEqual(info.business_type, "sports_turf")
		self.assertEqual(info.opening_time, "06:00")
		self.assertEqual(info.closing_time, "23:00")
		self.assertEqual(info.working_days, [
			"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
		])
		self.assertEqual(info.number_of_resources, 2)
		self.assertEqual([service.name for service in info.services], [
			"5-a-side football", "7-a-side football",
		])

	def test_shared_football_pitches_are_counted(self):
		info = assert_fallback_business_info(
			"We have two shared football pitches available for bookings."
		)
		self.assertEqual(info.number_of_resources, 2)


class BusinessJourneyTests(TestCase):
	def setUp(self):
		self.owner = User.objects.create_user(username="journey-owner", password="pass")
		self.client = APIClient()
		self.client.force_authenticate(self.owner)
		self.conversation = AIConversation.objects.create(owner=self.owner)
		self.configuration = BusinessConfiguration.objects.create(
			conversation=self.conversation,
			business_name="Hightown Turf",
			business_type="sports_turf",
			services=[{"name": "5-a-side football", "duration_minutes": 60, "price": 20}],
			opening_time=time(6, 0), closing_time=time(23, 0),
			working_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
			number_of_resources=2,
		)

	def test_chat_stores_shared_pitch_answer_instead_of_asking_again(self):
		self.configuration.number_of_resources = None
		self.configuration.save()
		with patch("ai_assistant.views.extract_business_info", return_value=BusinessInfo()):
			response = self.client.post("/api/ai/chat/", {
				"conversation_id": self.conversation.id,
				"message": "We have two shared football pitches available for bookings.",
			}, format="json")

		self.assertEqual(response.status_code, 200, response.data)
		self.configuration.refresh_from_db()
		self.assertEqual(self.configuration.number_of_resources, 2)
		self.assertNotIn("How many bookable resources", response.data["message"])

	def test_confirmation_saves_edited_service_price_and_duration(self):
		response = self.client.post("/api/ai/confirm/", {
			"conversation_id": self.conversation.id,
			"website_style": "elegant",
			"services": [{
				"name": "Hair Coloring",
				"duration_minutes": 90,
				"price": 1250,
			}],
		}, format="json")

		self.assertEqual(response.status_code, 201, response.data)
		tenant = Tenant.objects.get(pk=response.data["tenant_id"])
		service = Service.objects.get(tenant=tenant)
		self.assertEqual(service.name, "Hair Coloring")
		self.assertEqual(service.duration, 90)
		self.assertEqual(service.price, 1250)

	def test_confirmation_is_idempotent_and_public_booking_reaches_owner(self):
		payload = {"conversation_id": self.conversation.id, "website_style": "elegant"}
		first = self.client.post("/api/ai/confirm/", payload, format="json")
		second = self.client.post("/api/ai/confirm/", payload, format="json")
		self.assertEqual(first.status_code, 201)
		self.assertEqual(second.status_code, 201)
		self.assertEqual(first.data["slug"], "hightown-turf")
		self.assertEqual(first.data["public_url"], "/book/hightown-turf")
		self.assertEqual(first.data["website_style"], "elegant")
		tenant = Tenant.objects.get(pk=first.data["tenant_id"])
		self.assertEqual(Service.objects.filter(tenant=tenant).count(), 1)
		self.assertEqual(Resource.objects.filter(tenant=tenant).count(), 2)
		self.assertEqual(BusinessHours.objects.filter(tenant=tenant).count(), 7)

		public = APIClient()
		business = public.get(f"/api/tenants/public/{tenant.slug}/")
		services = public.get(f"/api/book/{tenant.slug}/services/")
		self.assertEqual(business.data["business_name"], "Hightown Turf")
		self.assertEqual(business.data["website_style"], "elegant")
		public_services = services.data.get("results", services.data)
		self.assertEqual([item["name"] for item in public_services], ["5-a-side football"])

		booking_date = date.today() + timedelta(days=1)
		# Find the next configured day to keep the test independent of weekday.
		while booking_date.weekday() not in range(7):
			booking_date += timedelta(days=1)
		available = public.get(
			f"/api/book/{tenant.slug}/available-slots/",
			{"date": booking_date.isoformat(), "service": public_services[0]["id"]},
		)
		self.assertEqual(available.status_code, 200)
		self.assertTrue(available.data["available_slots"])
		created = public.post(f"/api/book/{tenant.slug}/", {
			"customer_name": "A Customer", "customer_phone": "1234567890",
			"booking_date": booking_date.isoformat(),
			"booking_time": available.data["available_slots"][0],
			"service": public_services[0]["id"],
		}, format="json")
		self.assertEqual(created.status_code, 201, created.data)
		owner_bookings = self.client.get("/api/bookings/")
		self.assertEqual(owner_bookings.data["count"], 1)
		self.assertEqual(owner_bookings.data["results"][0]["customer_name"], "A Customer")
		self.assertEqual(owner_bookings.data["results"][0]["tenant"]["business_name"], "Hightown Turf")
		other = User.objects.create_user(username="other-owner", password="pass")
		other_client = APIClient()
		other_client.force_authenticate(other)
		self.assertEqual(other_client.get("/api/bookings/").data["count"], 0)
