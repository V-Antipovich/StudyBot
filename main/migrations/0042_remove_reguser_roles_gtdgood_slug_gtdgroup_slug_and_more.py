# Generated by Django 4.1 on 2022-08-23 08:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0041_alter_role_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reguser',
            name='roles',
        ),
        migrations.AddField(
            model_name='gtdgood',
            name='slug',
            field=models.SlugField(null=True),
        ),
        migrations.AddField(
            model_name='gtdgroup',
            name='slug',
            field=models.SlugField(null=True),
        ),
        migrations.AddField(
            model_name='gtdmain',
            name='slug',
            field=models.SlugField(null=True),
        ),
        migrations.DeleteModel(
            name='Role',
        ),
    ]
