from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("ai_assistant", "0006_businessconfiguration_number_of_resources")]

    operations = [
        migrations.AddField(
            model_name="businessconfiguration",
            name="website_style",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="businessconfiguration",
            name="website_style_suggested",
            field=models.BooleanField(default=False),
        ),
    ]
