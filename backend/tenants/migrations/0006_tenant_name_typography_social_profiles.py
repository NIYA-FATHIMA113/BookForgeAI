from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("tenants", "0005_tenant_website_font")]

    operations = [
        migrations.AddField(
            model_name="tenant",
            name="business_name_font",
            field=models.CharField(
                choices=[
                    ("classic", "Classic serif"),
                    ("modern", "Modern sans serif"),
                    ("friendly", "Friendly rounded"),
                    ("editorial", "Editorial display"),
                    ("mono", "Minimal mono"),
                ],
                default="editorial",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="tenant",
            name="instagram_handle",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="tenant",
            name="whatsapp_number",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name="tenant",
            name="facebook_id",
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
