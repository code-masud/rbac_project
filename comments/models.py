from django.db import models
from django.conf import settings


class Comment(models.Model):
    """Comment model for posts"""
    
    content = models.TextField()
    post = models.ForeignKey(
        'posts.Post',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'comments'
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['author', '-created_at']),
        ]
    
    def __str__(self):
        return f"Comment by {self.author.email} on {self.post.title[:30]}"
    
    @property
    def is_post_owner(self, user):
        """Check if given user is the owner of the post this comment belongs to"""
        return self.post.author == user
    
    def soft_delete(self):
        self.is_active = False
        self.save()