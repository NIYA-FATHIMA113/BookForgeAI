from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("tenants", "0006_tenant_name_typography_social_profiles")]

    operations = [
        migrations.AddField(
            model_name="tenant",
            name="website_template",
            field=models.CharField(
                choices=[
                    ("auto", "Match business type"),
                    ("restaurant_classic", "Classic bistro"),
                    ("restaurant_modern", "Modern menu"),
                    ("restaurant_bistro", "Neighborhood bistro"),
                    ("restaurant_market", "Market table"),
                    ("salon_editorial", "Editorial studio"),
                    ("salon_minimal", "Minimal studio"),
                    ("salon_botanical", "Botanical beauty"),
                    ("salon_glam", "Glam lounge"),
                    ("clinic_calm", "Calm care"),
                    ("clinic_modern", "Modern practice"),
                    ("clinic_family", "Family clinic"),
                    ("clinic_holistic", "Holistic wellness"),
                    ("sports_arena", "Arena"),
                    ("sports_club", "Sports club"),
                    ("sports_field", "Open field"),
                    ("sports_night", "Night game"),
                ],
                default="auto",
                max_length=30,
            ),
        ),
    ]
