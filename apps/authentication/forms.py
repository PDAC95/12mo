from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

User = get_user_model()

class LoginForm(forms.Form):
    """User login form"""
    email = forms.EmailField(
        label=_("Correo electrónico"),
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': _('correo@ejemplo.com'),
            'autofocus': True,
            'autocomplete': 'email',
        })
    )
    password = forms.CharField(
        label=_("Contraseña"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Tu contraseña'),
            'autocomplete': 'current-password',
        })
    )
    remember_me = forms.BooleanField(
        label=_("Recordarme"),
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
                    _("Email o contraseña incorrectos."),
                    code='invalid_login'
                )
            elif not self.user_cache.is_active:
                raise forms.ValidationError(
                    _("Esta cuenta está desactivada."),
                    code='inactive'
                )
        
        return self.cleaned_data
    
    def get_user(self):
        return self.user_cache


class RegisterForm(forms.ModelForm):
    """User registration form"""
    password1 = forms.CharField(
        label=_("Contraseña"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Mínimo 8 caracteres'),
            'autocomplete': 'new-password',
        }),
        help_text=_("Tu contraseña debe tener al menos 8 caracteres.")
    )
    password2 = forms.CharField(
        label=_("Confirmar contraseña"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Confirma tu contraseña'),
            'autocomplete': 'new-password',
        }),
        help_text=_("Ingresa la misma contraseña para verificación.")
    )
    
    class Meta:
        model = User
        fields = ('email', 'username')
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': _('correo@ejemplo.com'),
                'autocomplete': 'email',
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': _('nombreusuario'),
                'autocomplete': 'username',
            }),
        }
        help_texts = {
            'username': _('Requerido. Solo letras, números y @/./+/-/_ caracteres.'),
            'email': _('Ingresa un email válido. Lo usarás para iniciar sesión.'),
        }
        labels = {
            'email': _('Correo electrónico'),
            'username': _('Nombre de usuario'),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError(
                _("Ya existe una cuenta con este correo electrónico."),
                code='duplicate_email'
            )
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise ValidationError(
                _("Este nombre de usuario ya está en uso."),
                code='duplicate_username'
            )
        return username
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            if len(password1) < 8:
                raise ValidationError(
                    _("La contraseña debe tener al menos 8 caracteres."),
                    code='password_too_short'
                )
            # Basic password strength validation
            if password1.isdigit():
                raise ValidationError(
                    _("La contraseña no puede ser completamente numérica."),
                    code='password_entirely_numeric'
                )
        return password1
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                _("Las contraseñas no coinciden."),
                code='password_mismatch'
            )
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user