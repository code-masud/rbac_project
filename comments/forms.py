from django import forms
from .models import Comment


class CommentForm(forms.ModelForm):
    """Comment Form"""
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Write your comment here...'
        })
    )
    post = forms.IntegerField(widget=forms.HiddenInput())
    
    class Meta:
        model = Comment
        fields = ('content', 'post')
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content or len(content.strip()) == 0:
            raise forms.ValidationError('Comment cannot be empty.')
        if len(content) > 1000:
            raise forms.ValidationError('Comment must be less than 1000 characters.')
        return content