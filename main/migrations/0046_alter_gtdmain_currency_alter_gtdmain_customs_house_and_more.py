# Generated by Django 4.1 on 2022-08-25 10:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0045_reguser_done_registration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gtdmain',
            name='currency',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='main.currency', verbose_name='id валюты'),
        ),
        migrations.AlterField(
            model_name='gtdmain',
            name='customs_house',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='main.customshouse', verbose_name='id таможенного отделения'),
        ),
        migrations.AlterField(
            model_name='gtdmain',
            name='deal_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='main.dealtype', verbose_name='id характера сделки'),
        ),
        migrations.AlterField(
            model_name='gtdmain',
            name='exporter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='main.exporter', verbose_name='id Экспортера'),
        ),
        migrations.AlterField(
            model_name='gtdmain',
            name='gtd_file',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='main.uploadgtdfile', verbose_name='id xml-документа гтд'),
        ),
        migrations.AlterField(
            model_name='gtdmain',
            name='importer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='main.importer', verbose_name='id импортера'),
        ),
        migrations.AlterField(
            model_name='gtdmain',
            name='trading_country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='main.country', verbose_name='id торгующей страны'),
        ),
    ]
