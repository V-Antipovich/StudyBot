# Generated by Django 4.1 on 2022-08-14 20:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_alter_measurequalifier_english_symbol_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='measurequalifier',
            name='english_symbol',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Международное условное обозначение'),
        ),
        migrations.AlterField(
            model_name='measurequalifier',
            name='russian_symbol',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Русское условное обозначение'),
        ),
    ]
