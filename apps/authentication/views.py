# Web-based authentication views
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import FormView, RedirectView
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from .forms import LoginForm, RegisterForm

# API views (keep for mobile/API usage)
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import UserRegistrationSerializer, UserSerializer


class LoginView(FormView):
    """User login view for web interface"""
    template_name = 'public/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('dashboard:home')
    
    @method_decorator(sensitive_post_parameters('password'))
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        # Redirect authenticated users to dashboard
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        
        # Handle remember me functionality
        if not form.cleaned_data.get('remember_me'):
            self.request.session.set_expiry(0)  # Session expires on browser close
        
        messages.success(
            self.request, 
            'Welcome back, {}!'.format(user.username)
        )
        
        # Get next URL if provided
        next_url = self.request.GET.get('next', self.success_url)
        return redirect(next_url)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'Please correct the errors in the form.'
        )
        return super().form_invalid(form)


class RegisterView(FormView):
    """User registration view for web interface"""
    template_name = 'public/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('dashboard:home')
    
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        # Redirect authenticated users to dashboard
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        # Create and save the user
        user = form.save()
        
        # Automatically log in the user
        login(self.request, user)
        
        messages.success(
            self.request,
            'Account created successfully! Welcome to Wallai, {}!'.format(user.username)
        )
        
        # Future: Trigger personal space creation signal here
        # signals.user_registered.send(sender=self.__class__, user=user, request=self.request)
        
        return redirect(self.success_url)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'Please correct the errors in the form.'
        )
        return super().form_invalid(form)


class LogoutView(RedirectView):
    """User logout view"""
    url = reverse_lazy('public:home')
    
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            username = request.user.username
            logout(request)
            messages.info(
                request,
                'You have been logged out successfully. See you soon, {}!'.format(username)
            )
        return super().get(request, *args, **kwargs)


# API views for mobile/API usage (keep existing functionality)
@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    """Register a new user via API"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """Login user with email and password via API"""
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {'error': 'Please provide both email and password'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=email, password=password)
    
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
    
    return Response(
        {'error': 'Invalid credentials'},
        status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(['GET'])
def profile(request):
    """Get current user profile"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)
