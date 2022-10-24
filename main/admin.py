from django.contrib import admin
from .models import RegUser, CustomsHouse, Country, Currency, DealType, TnVed, Procedure, GtdMain, Exporter, Importer, GtdGroup, GtdGood, Good, TradeMark, GoodsMark, Manufacturer, GtdDocument, Document, UploadGtd, DocumentType, UploadGtdFile, MeasureQualifier
# Register your models here.


class RegUserAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'email')


admin.site.register(RegUser, RegUserAdmin)
admin.site.register(CustomsHouse)
admin.site.register(Country)
admin.site.register(Currency)
admin.site.register(DealType)
admin.site.register(TnVed)
admin.site.register(Procedure)
admin.site.register(GtdMain)
admin.site.register(Exporter)
admin.site.register(Importer)
admin.site.register(GtdGroup)
admin.site.register(UploadGtd)
admin.site.register(Document)
admin.site.register(GtdDocument)
admin.site.register(Manufacturer)
admin.site.register(GoodsMark)
admin.site.register(TradeMark)
admin.site.register(Good)
admin.site.register(GtdGood)
admin.site.register(DocumentType)
admin.site.register(UploadGtdFile)
admin.site.register(MeasureQualifier)