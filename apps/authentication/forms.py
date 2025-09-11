from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError

User = get_user_model()

class LoginForm(forms.Form):
    """User login form"""
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'you@email.com',
            'autofocus': True,
            'autocomplete': 'email',
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Your password',
            'autocomplete': 'current-password',
        })
    )
    remember_me = forms.BooleanField(
        label="Remember me",
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox',
        })
    )
    
    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
    
    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        
        if email and password:
            # Try to authenticate with email as username
            self.user_cache = authenticate(
                self.request, 
                username=email,  # Our custom User model uses email as USERNAME_FIELD
                password=password
            )
            
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Email or password incorrect.",
                    code='invalid_login'
                )
            elif not self.user_cache.is_active:
                raise forms.ValidationError(
                    "This account is deactivated.",
                    code='inactive'
                )
        
        return self.cleaned_data
    
    def get_user(self):
        return self.user_cache


class RegisterForm(forms.ModelForm):
    """User registration form"""
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Minimum 8 characters',
            'autocomplete': 'new-password',
        }),
        help_text="Your password must have at least 8 characters."
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password',
        }),
        help_text="Enter the same password for verification."
    )
    
    class Meta:
        model = User
        fields = ('email', 'username')
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'you@email.com',
                'autocomplete': 'email',
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'username',
                'autocomplete': 'username',
            }),
        }
        help_texts = {
            'username': 'Required. Letters, numbers and @/./+/-/_ characters only.',
            'email': 'Enter a valid email. You will use it to log in.',
        }
        labels = {
            'email': 'Email',
            'username': 'Username',
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError(
                "An account with this email already exists.",
                code='duplicate_email'
            )
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise ValidationError(
                "This username is already in use.",
                code='duplicate_username'
            )
        return username
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            if len(password1) < 8:
                raise ValidationError(
                    "Password must have at least 8 characters.",
                    code='password_too_short'
                )
            # Basic password strength validation
            if password1.isdigit():
                raise ValidationError(
                    "Password cannot be entirely numeric.",
                    code='password_entirely_numeric'
                )
        return password1
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                "Passwords do not match.",
                code='password_mismatch'
            )
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user