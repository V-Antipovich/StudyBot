# Generated by Django 4.1 on 2022-08-31 08:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0050_gtdmain_last_edited_uploadgtd_who_uploaded'),
    ]

    operations = [
        migrations.RenameField(
            model_name='gtdmain',
            old_name='last_edited',
            new_name='last_edited_user',
        ),
        migrations.AddField(
            model_name='gtdmain',
            name='last_edited_time',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Дата и время добавления/последнего редактирования'),
        ),
    ]
