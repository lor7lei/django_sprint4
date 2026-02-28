from django import forms
from django.contrib.auth import get_user_model
from .models import Post, Comment

User = get_user_model()

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'text', 'category', 'location', 'pub_date', 'is_published']
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Напишите комментарий...'
            }),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }