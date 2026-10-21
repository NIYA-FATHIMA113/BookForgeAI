from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("ai_assistant", "0007_businessconfiguration_website_style")]

    operations = [
        migrations.AddField(
            model_name="businessconfiguration",
            name="contact_details_reviewed",
            field=models.BooleanField(default=False),
        ),
    ]
