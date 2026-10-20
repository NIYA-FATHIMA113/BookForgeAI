from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, storages
from django.core.management.base import BaseCommand, CommandError

from tenants.models import Tenant


class Command(BaseCommand):
    help = "Copy existing local business logos and hero photos to Cloudinary."

    def handle(self, *args, **options):
        if not settings.CLOUDINARY_STORAGE_ENABLED:
            raise CommandError(
                "Set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and "
                "CLOUDINARY_API_SECRET before running this command."
            )

        local_storage = FileSystemStorage(location=settings.MEDIA_ROOT)
        cloud_storage = storages["default"]
        migrated = 0
        skipped = 0
        missing = 0

        for tenant in Tenant.objects.all().iterator():
            for field_name in ("logo_image", "hero_image"):
                field_file = getattr(tenant, field_name)
                stored_name = field_file.name
                if not stored_name or stored_name.lower().startswith(("http://", "https://")):
                    skipped += 1
                    continue
                if not local_storage.exists(stored_name):
                    missing += 1
                    self.stdout.write(self.style.WARNING(
                        f"Missing local file for tenant {tenant.pk} ({field_name}): {stored_name}"
                    ))
                    continue

                with local_storage.open(stored_name, "rb") as local_file:
                    cloud_name = cloud_storage.save(
                        stored_name,
                        ContentFile(local_file.read(), name=stored_name.rsplit("/", 1)[-1]),
                    )
                setattr(tenant, field_name, cloud_name)
                tenant.save(update_fields=[field_name, "updated_at"])
                migrated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Migrated {migrated} image(s); skipped {skipped} empty/external reference(s); "
            f"{missing} local file(s) were unavailable."
        ))
