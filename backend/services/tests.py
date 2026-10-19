from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from services.models import Resource
from tenants.models import Tenant


User = get_user_model()


class ResourceAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner", password="test-password")
        self.other_owner = User.objects.create_user("other-owner", password="test-password")
        self.tenant = Tenant.objects.create(
            owner=self.owner, business_name="Hightown Turf",
            business_type="sports_turf", slug="hightown-turf",
        )
        self.other_tenant = Tenant.objects.create(
            owner=self.other_owner, business_name="Other Turf",
            business_type="sports_turf", slug="other-turf",
        )

    def test_resource_belongs_to_tenant_and_owner_can_create_it(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            reverse("resource-list-create", kwargs={"tenant_id": self.tenant.id}),
            {"name": "Pitch 1"}, format="json",
        )

        self.assertEqual(response.status_code, 201)
        resource = Resource.objects.get()
        self.assertEqual(resource.tenant, self.tenant)
        self.assertEqual(response.data["tenant"], self.tenant.id)

    def test_owner_cannot_list_or_create_resources_for_another_tenant(self):
        Resource.objects.create(tenant=self.other_tenant, name="Pitch 1")
        self.client.force_authenticate(self.owner)
        url = reverse("resource-list-create", kwargs={"tenant_id": self.other_tenant.id})

        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {"name": "Pitch 2"}, format="json").status_code, 404)
