from django import forms
from django.core.validators import FileExtensionValidator
from .models import UploadGtd


class GtdFileForm(forms.Form):
    file = forms.FileField()


class UploadGtdfilesForm(forms.Form):
    comment = forms.CharField(max_length=255)
    document = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), validators=[FileExtensionValidator(allowed_extensions=['xml'])])
