from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='邮箱')
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, label='角色', initial='operator')
    phone = forms.CharField(max_length=20, required=False, label='手机号')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'role', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone', '')
        user.role = self.cleaned_data['role']
        
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'phone', 'avatar')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }