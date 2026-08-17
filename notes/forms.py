from django import forms


class UploadFileForm(forms.Form):

    file = forms.FileField(
        label="Upload PDF",
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control",
                "accept": ".pdf"
            }
        )
    )