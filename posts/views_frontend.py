from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Post
from .forms import PostForm
from comments.models import Comment
import requests


class PostListView(ListView):
    """Post List View with search and pagination"""
    model = Post
    template_name = 'posts/post_list.html'
    context_object_name = 'posts'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = Post.objects.filter(is_active=True)
        search_query = self.request.GET.get('search', '')
        
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(author__first_name__icontains=search_query) |
                Q(author__last_name__icontains=search_query) |
                Q(author__email__icontains=search_query)
            )
        
        return queryset.select_related('author').prefetch_related('comments')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class PostDetailView(DetailView):
    """Post Detail View with comments"""
    model = Post
    template_name = 'posts/post_detail.html'
    context_object_name = 'post'
    
    def get_queryset(self):
        return Post.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.filter(is_active=True).select_related('author')
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """Create Post View (Regular users and above)"""
    model = Post
    form_class = PostForm
    template_name = 'posts/post_form.html'
    success_url = reverse_lazy('post-list')
    login_url = 'login'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_guest:
            messages.error(request, 'Guests cannot create posts.')
            return redirect('post-list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Post created successfully!')
        
        # Also create via API
        try:
            access_token = self.request.session.get('access_token')
            if access_token:
                headers = {'Authorization': f'Bearer {access_token}'}
                requests.post(
                    'http://localhost:8000/api/posts/',
                    json={
                        'title': form.cleaned_data['title'],
                        'content': form.cleaned_data['content']
                    },
                    headers=headers
                )
        except:
            pass
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update Post View (Only post owner or super admin)"""
    model = Post
    form_class = PostForm
    template_name = 'posts/post_form.html'
    login_url = 'login'
    
    def test_func(self):
        post = self.get_object()
        return self.request.user.is_super_admin or post.author == self.request.user
    
    def get_success_url(self):
        return reverse_lazy('post-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Post updated successfully!')
        
        # Also update via API
        try:
            access_token = self.request.session.get('access_token')
            if access_token:
                headers = {'Authorization': f'Bearer {access_token}'}
                requests.put(
                    f'http://localhost:8000/api/posts/{self.object.pk}/',
                    json={
                        'title': form.cleaned_data['title'],
                        'content': form.cleaned_data['content']
                    },
                    headers=headers
                )
        except:
            pass
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete Post View (Post owner, moderator, or super admin)"""
    model = Post
    template_name = 'posts/post_confirm_delete.html'
    success_url = reverse_lazy('post-list')
    login_url = 'login'
    
    def test_func(self):
        post = self.get_object()
        return (self.request.user.is_super_admin or 
                self.request.user.is_moderator or 
                post.author == self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Post deleted successfully!')
        
        # Also delete via API
        try:
            access_token = self.request.session.get('access_token')
            if access_token:
                headers = {'Authorization': f'Bearer {access_token}'}
                requests.delete(
                    f'http://localhost:8000/api/posts/{self.get_object().pk}/',
                    headers=headers
                )
        except:
            pass
        
        return super().delete(request, *args, **kwargs)