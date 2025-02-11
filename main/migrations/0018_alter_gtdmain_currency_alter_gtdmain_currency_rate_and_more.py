# Generated by Django 4.1 on 2022-08-16 09:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0017_rename_brand_good_goodsmark_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gtdmain',
            name='currency',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='main.currency', verbose_name='id валюты'),
        ),
        migrations.AlterField(
            model_name='gtdmain',
            name='currency_rate',
            field=models.FloatField(blank=True, null=True, verbose_name='Курс валюты'),
        ),
        migrations.AlterField(
            model_name='gtdmain',
            name='customs_house',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='main.customshouse', verbose_name='id таможенного отделения'),
        ),
        migrations.AlterField(
            model_name='gtdmain',
            name='date',
            field=models.DateField(blank=True, null=True, verbose_name='Дата'),
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
            name='importer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='main.importer', verbose_name='id импортера'),
        ),
        migrations.AlterField(
            model_name='gtdmain',
            name='order_num',
            field=models.CharField(blank=True, max_length=7, null=True, verbose_name='Порядковый номер'),
        ),
        migrations.AlterField(
            model_name='gtdmain',
            name='total_cost',
            field=models.FloatField(blank=True, null=True, verbose_name='Общая стоимость'),
        ),
        migrations.AlterField(
            model_name='gtdmain',
            name='total_goods_number',
            field=models.IntegerField(blank=True, null=True, verbose_name='Всего товаров'),
        ),
        migrations.AlterField(
            model_name='gtdmain',
            name='total_invoice_amount',
            field=models.FloatField(blank=True, null=True, verbose_name='Общая стоимость по счету'),
        ),
        migrations.AlterField(
            model_name='gtdmain',
            name='trading_country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='main.country', verbose_name='id торгующей страны'),
        ),
    ]
