from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tenants", "0009_alter_tenant_website_style"),
    ]

    operations = [
        migrations.AddField(
            model_name="tenant",
            name="business_name_size",
            field=models.PositiveSmallIntegerField(default=24),
        ),
    ]
