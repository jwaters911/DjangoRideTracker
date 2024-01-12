from django import forms
from .models import Comment


class UploadFileForm(forms.Form):
    fit_file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'accept': '.fit'}),
        label='Select a .fit file'
    )

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        activity_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['text'].widget = forms.Textarea(attrs={'rows': 4, 'cols': 40})