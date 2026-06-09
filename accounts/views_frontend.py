from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, ListView, View, FormView
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from .models import User
from .forms import UserRegistrationForm, UserUpdateForm, ChangePasswordForm
from rest_framework_simplejwt.tokens import RefreshToken
import requests


class LoginView(View):
    """Frontend Login View"""
    template_name = 'accounts/login.html'
    
    @method_decorator(never_cache)
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('post-list')
        return render(request, self.template_name)
    
    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, 'Please provide both email and password.')
            return render(request, self.template_name)
        
        # Authenticate with Django
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                
                # Store JWT tokens in session for API calls
                try:
                    # Call API to get JWT token
                    response = requests.post(
                        'http://localhost:8000/api/auth/login/',
                        json={'email': email, 'password': password}
                    )
                    if response.status_code == 200:
                        tokens = response.json()
                        request.session['access_token'] = tokens.get('access')
                        request.session['refresh_token'] = tokens.get('refresh')
                except:
                    pass  # Continue even if API fails
                
                messages.success(request, f'Welcome back, {user.first_name}!')
                
                # Redirect to next parameter or home
                next_url = request.GET.get('next', 'post-list')
                return redirect(next_url)
            else:
                messages.error(request, 'Your account is disabled.')
        else:
            messages.error(request, 'Invalid email or password.')
        
        return render(request, self.template_name)


class RegisterView(CreateView):
    """Frontend Registration View"""
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Registration successful! Please login.')
        
        # Also register via API
        try:
            requests.post(
                'http://localhost:8000/api/auth/register/',
                json={
                    'email': form.cleaned_data['email'],
                    'password': form.cleaned_data['password1'],
                    'first_name': form.cleaned_data['first_name'],
                    'last_name': form.cleaned_data['last_name']
                }
            )
        except:
            pass  # Continue even if API fails
        
        return response
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class ProfileView(LoginRequiredMixin, View):
    """User Profile View"""
    template_name = 'accounts/profile.html'
    login_url = 'login'
    
    def get(self, request):
        context = {
            'user': request.user,
            'post_count': request.user.posts.count(),
            'comment_count': request.user.comments.count(),
            'recent_posts': request.user.posts.all()[:5],
            'recent_comments': request.user.comments.all()[:5],
        }
        return render(request, self.template_name, context)


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Edit Profile View"""
    model = User
    form_class = UserUpdateForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('profile')
    login_url = 'login'
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return super().form_invalid(form)


class ChangePasswordView(LoginRequiredMixin, FormView):
    """Change Password View"""
    template_name = 'accounts/change_password.html'
    form_class = ChangePasswordForm
    success_url = reverse_lazy('profile')
    login_url = 'login'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Password changed successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return super().form_invalid(form)


class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """User List View (Admin only)"""
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    login_url = 'login'
    
    def test_func(self):
        return self.request.user.is_super_admin
    
    def get_queryset(self):
        queryset = super().get_queryset()
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_counts'] = {
            'super_admin': User.objects.filter(role='super_admin').count(),
            'moderator': User.objects.filter(role='moderator').count(),
            'regular_user': User.objects.filter(role='regular_user').count(),
            'guest': User.objects.filter(role='guest').count(),
        }
        return context