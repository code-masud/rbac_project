import django_filters
from django.db import models
from .models import Post


class PostFilter(django_filters.FilterSet):
    """Filter class for posts"""
    
    author_email = django_filters.CharFilter(field_name='author__email', lookup_expr='icontains')
    author_name = django_filters.CharFilter(method='filter_author_name')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Post
        fields = {
            'author': ['exact'],
            'title': ['icontains'],
            'is_active': ['exact'],
        }
    
    def filter_author_name(self, queryset, name, value):
        return queryset.filter(
            models.Q(author__first_name__icontains=value) |
            models.Q(author__last_name__icontains=value)
        )
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            models.Q(title__icontains=value) |
            models.Q(content__icontains=value) |
            models.Q(author__email__icontains=value)
        )