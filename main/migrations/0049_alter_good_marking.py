# Generated by Django 4.1 on 2022-08-28 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0048_gtdgroup_description_gtdgroup_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='good',
            name='marking',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Артикул'),
        ),
    ]
