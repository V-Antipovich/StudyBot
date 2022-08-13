from django import forms
from .models import UploadGtd


class GtdFileForm(forms.Form):
    file = forms.FileField()


class UploadGtdForm(forms.ModelForm):
    class Meta:
        model = UploadGtd
        fields = "__all__"
