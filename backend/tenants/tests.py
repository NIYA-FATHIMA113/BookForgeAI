from io import BytesIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings
from django.test import RequestFactory
from PIL import Image
from rest_framework.test import APIClient

from .media_urls import public_image_url
from .models import Tenant
from .serializers import MAX_BUSINESS_IMAGE_SIZE, TenantSerializer


class PublicImageUrlTests(SimpleTestCase):
    def setUp(self):
        self.request = RequestFactory().get("/api/tenants/public/example/")

    def test_external_image_url_is_preserved(self):
        url = "https://images.example.test/photo.jpg?size=large"
        self.assertEqual(public_image_url(self.request, external_url=url), url)

    def test_missing_or_invalid_image_returns_none(self):
        self.assertIsNone(public_image_url(self.request))
        self.assertIsNone(public_image_url(self.request, external_url="not a url"))


class CloudinaryStorageConfigurationTests(SimpleTestCase):
    @override_settings(STORAGES={
        "default": {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    })
    def test_cloudinary_backend_is_selected_for_media(self):
        self.assertEqual(
            settings.STORAGES["default"]["BACKEND"],
            "cloudinary_storage.storage.MediaCloudinaryStorage",
        )


class TenantMediaApiTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="media-owner", password="pass")
        self.other_owner = User.objects.create_user(username="other-owner", password="pass")
        self.tenant = Tenant.objects.create(
            owner=self.owner,
            business_name="Owner Cafe",
            slug="owner-cafe",
            business_type="restaurant",
        )
        self.client = APIClient()

    def test_tenant_cannot_read_another_owners_business(self):
        self.client.force_authenticate(user=self.other_owner)
        response = self.client.get(f"/api/tenants/{self.tenant.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_external_image_reference_persists_and_is_returned_publicly(self):
        url = "https://images.example.test/owner-cafe.jpg"
        serializer = TenantSerializer(
            self.tenant,
            data={"hero_image_external_url": url},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.hero_image_external_url, url)

        public_response = self.client.get("/api/tenants/public/owner-cafe/")
        self.assertEqual(public_response.status_code, 200)
        self.assertEqual(public_response.data["hero_image"], url)

    def test_upload_validation_rejects_non_image_and_over_limit_files(self):
        invalid = SimpleUploadedFile("not-image.png", b"not an image", content_type="image/png")
        serializer = TenantSerializer(self.tenant, data={"logo_image": invalid}, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn("logo_image", serializer.errors)

    def test_multipart_upload_persists_storage_reference_and_returns_absolute_url(self):
        image_bytes = BytesIO()
        Image.new("RGB", (1600, 900), color=(45, 80, 60)).save(image_bytes, format="JPEG")
        upload = SimpleUploadedFile(
            "website-photo.jpg", image_bytes.getvalue(), content_type="image/jpeg"
        )
        self.client.force_authenticate(user=self.owner)
        storage = Tenant._meta.get_field("hero_image").storage
        cdn_url = "https://cdn.example.test/persisted/website-photo.jpg"

        with patch.object(storage, "save", return_value="businesses/hero/website-photo.jpg"), \
                patch.object(storage, "url", return_value=cdn_url):
            response = self.client.patch(
                f"/api/tenants/{self.tenant.pk}/",
                {"hero_image": upload},
                format="multipart",
            )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["hero_image"], cdn_url)
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.hero_image.name, "businesses/hero/website-photo.jpg")

        oversized = SimpleUploadedFile(
            "oversized.png", b"x" * (MAX_BUSINESS_IMAGE_SIZE + 1), content_type="image/png"
        )
        serializer = TenantSerializer(self.tenant, data={"logo_image": oversized}, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn("logo_image", serializer.errors)

    def test_uploaded_image_name_is_persisted_in_existing_model_field(self):
        # Simulate the Cloudinary storage response without contacting an account.
        with patch.object(
            Tenant._meta.get_field("logo_image").storage,
            "save",
            return_value="businesses/logos/owner-logo.png",
        ):
            self.tenant.logo_image.save(
                "owner-logo.png",
                SimpleUploadedFile("owner-logo.png", b"test", content_type="image/png"),
                save=True,
            )
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.logo_image.name, "businesses/logos/owner-logo.png")
        cdn_url = "https://cdn.example.test/persisted/owner-logo.png"
        with patch.object(
            Tenant._meta.get_field("logo_image").storage,
            "url",
            return_value=cdn_url,
        ):
            public_response = self.client.get("/api/tenants/public/owner-cafe/")
        self.assertEqual(public_response.data["logo_image"], cdn_url)
