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
        
        # Get the post ID from the form
        post_id = request.POST.get('post')
        
        # Validate post exists and is active
        try:
            post = Post.objects.get(id=post_id, is_active=True)
        except Post.DoesNotExist:
            messages.error(request, 'The post you are trying to comment on does not exist.')
            return redirect('post-list')
        
        # Create comment manually without form
        content = request.POST.get('content', '').strip()
        
        if not content:
            messages.error(request, 'Comment cannot be empty.')
            return redirect('post-detail', pk=post_id)
        
        if len(content) > 1000:
            messages.error(request, 'Comment must be less than 1000 characters.')
            return redirect('post-detail', pk=post_id)
        
        # Create the comment
        comment = Comment.objects.create(
            content=content,
            post=post,
            author=request.user
        )
        
        messages.success(request, 'Comment posted successfully!')
        
        # Also create via API
        try:
            access_token = request.session.get('access_token')
            if access_token:
                headers = {'Authorization': f'Bearer {access_token}'}
                requests.post(
                    'http://localhost:8000/api/comments/',
                    json={
                        'content': content,
                        'post': post_id
                    },
                    headers=headers
                )
        except Exception as e:
            # Log error but don't stop the process
            print(f"API error: {e}")
        
        return redirect('post-detail', pk=post_id)

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