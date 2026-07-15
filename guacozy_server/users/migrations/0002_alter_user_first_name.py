# Generated for the Django 2.2 -> 3.2 upgrade.
# Django 3.1+ widened AbstractUser.first_name from max_length=30 to 150.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='first_name',
            field=models.CharField(blank=True, max_length=150, verbose_name='first name'),
        ),
    ]
