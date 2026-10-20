from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("tenants", "0004_tenant_brand_images")]

    operations = [
        migrations.AddField(
            model_name="tenant",
            name="website_font",
            field=models.CharField(
                choices=[
                    ("classic", "Classic serif"),
                    ("modern", "Modern sans serif"),
                    ("friendly", "Friendly rounded"),
                    ("editorial", "Editorial display"),
                    ("mono", "Minimal mono"),
                ],
                default="classic",
                max_length=20,
            ),
        ),
    ]
