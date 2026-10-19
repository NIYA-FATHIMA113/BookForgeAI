import django.db.models.deletion
from django.db import migrations, models


def copy_resource_tenants(apps, schema_editor):
    Resource = apps.get_model("services", "Resource")

    for resource in Resource.objects.select_related("service"):
        resource.tenant_id = resource.service.tenant_id
        resource.save(update_fields=["tenant"])


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0002_resource"),
    ]

    operations = [
        migrations.AddField(
            model_name="resource",
            name="tenant",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="resources",
                to="tenants.tenant",
            ),
        ),
        migrations.RunPython(copy_resource_tenants, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="resource",
            name="service",
        ),
        migrations.AlterField(
            model_name="resource",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="resources",
                to="tenants.tenant",
            ),
        ),
    ]
