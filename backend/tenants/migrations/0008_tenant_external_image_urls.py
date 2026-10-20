from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("tenants", "0007_tenant_website_template")]

    operations = [
        migrations.AddField(
            model_name="tenant",
            name="logo_image_external_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="tenant",
            name="hero_image_external_url",
            field=models.URLField(blank=True),
        ),
    ]
