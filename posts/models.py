from django.db import models
from django.conf import settings
from django.utils import timezone


class Post(models.Model):
    """Post model for content management"""
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'posts'
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return self.title[:50]
    
    @property
    def comment_count(self):
        return self.comments.filter(is_active=True).count()
    
    def soft_delete(self):
        self.is_active = False
        self.save()