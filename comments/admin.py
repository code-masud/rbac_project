from django.contrib import admin
from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Custom admin for Comment model"""
    
    list_display = ('id', 'author', 'post', 'content_preview', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at', 'author')
    search_fields = ('content', 'author__email', 'post__title')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Comment Preview'
    
    actions = ['soft_delete_selected', 'restore_selected']
    
    def soft_delete_selected(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} comments were soft deleted.')
    soft_delete_selected.short_description = "Soft delete selected comments"
    
    def restore_selected(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} comments were restored.')
    restore_selected.short_description = "Restore selected comments"