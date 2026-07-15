# Generated for the Django 3.2 -> 4.2 / django-polymorphic 2.1 -> 3.1 upgrade.
# django-polymorphic 3.x stores the polymorphic_ctype related_name as an
# unresolved '%(app_label)s.%(class)s' template.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('backend', '0016_connectionrdp_defaults'),
    ]

    operations = [
        migrations.AlterField(
            model_name='connection',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype'),
        ),
    ]
