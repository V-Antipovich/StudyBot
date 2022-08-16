from django.contrib import admin
from .models import RegUser, Role, CustomsHouse, Country, Currency, DealType, TnVed, Procedure, GtdMain, UserRole, Exporter, Importer, GtdGroup, GtdGood, Good, TradeMark, GoodsMark, Manufacturer, GtdDocument, Document, UploadGtd
# Register your models here.


admin.site.register(RegUser)
admin.site.register(Role)
admin.site.register(CustomsHouse)
admin.site.register(Country)
admin.site.register(Currency)
admin.site.register(DealType)
admin.site.register(TnVed)
admin.site.register(Procedure)
admin.site.register(GtdMain)
admin.site.register(UserRole)
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
