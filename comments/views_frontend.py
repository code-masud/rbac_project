from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views import View
from django.views.generic import DeleteView
from django.urls import reverse_lazy
from .models import Comment
from posts.models import Post
from .forms import CommentForm
import requests


class CommentCreateView(LoginRequiredMixin, View):
    """Create Comment View (Authenticated users only)"""
    login_url = 'login'
    
    def post(self, request):
        if request.user.is_guest:
            messages.error(request, 'Guests cannot post comments.')
            return redirect('post-list')
        
        form = CommentForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.save()
            
            messages.success(request, 'Comment posted successfully!')
            
            # Also create via API
            try:
                access_token = request.session.get('access_token')
                if access_token:
                    headers = {'Authorization': f'Bearer {access_token}'}
                    requests.post(
                        'http://localhost:8000/api/comments/',
                        json={
                            'content': form.cleaned_data['content'],
                            'post': form.cleaned_data['post'].id
                        },
                        headers=headers
                    )
            except:
                pass
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
        
        return redirect('post-detail', pk=request.POST.get('post'))


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete Comment View (Comment owner, post owner, moderator, or super admin)"""
    model = Comment
    template_name = 'comments/comment_confirm_delete.html'
    login_url = 'login'
    
    def test_func(self):
        comment = self.get_object()
        return (self.request.user.is_super_admin or 
                self.request.user.is_moderator or 
                comment.author == self.request.user or
                comment.post.author == self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('post-detail', kwargs={'pk': self.get_object().post.pk})
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Comment deleted successfully!')
        
        # Also delete via API
        try:
            access_token = self.request.session.get('access_token')
            if access_token:
                headers = {'Authorization': f'Bearer {access_token}'}
                requests.delete(
                    f'http://localhost:8000/api/comments/{self.get_object().pk}/',
                    headers=headers
                )
        except:
            pass
        
        return super().delete(request, *args, **kwargs)