# Generated by Django 4.1 on 2022-08-15 08:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_alter_gtdgood_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='number',
            field=models.CharField(max_length=255, null=True, verbose_name='Номер документа'),
        ),
    ]
