# Generated by Django 4.1 on 2022-09-11 18:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0058_alter_good_marking'),
    ]

    operations = [
        migrations.AlterField(
            model_name='good',
            name='marking',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Артикул'),
        ),
    ]
