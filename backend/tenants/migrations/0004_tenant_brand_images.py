from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("tenants", "0003_tenant_website_style")]

    operations = [
        migrations.AddField(
            model_name="tenant",
            name="logo_image",
            field=models.ImageField(blank=True, null=True, upload_to="businesses/logos/"),
        ),
        migrations.AddField(
            model_name="tenant",
            name="hero_image",
            field=models.ImageField(blank=True, null=True, upload_to="businesses/hero/"),
        ),
    ]
