from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import UserProfile

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name')


class EmailChangeForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}), label="New Email Address")

    class Meta:
        model = User
        fields = ['email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email


# class NotificationSettingsForm(forms.ModelForm):
#     receive_email_notifications = forms.BooleanField(
#         required=False, 
#         label="Receive email notifications",
#         widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
#     )
# 
#     class Meta:
#         model = UserProfile
#         fields = ['receive_email_notifications'] 