# Generated by Django 4.1 on 2022-10-09 08:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0065_alter_tnved_collection_rate_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tnved',
            name='code',
            field=models.CharField(max_length=18, unique=True, verbose_name='Номер группы'),
        ),
    ]
