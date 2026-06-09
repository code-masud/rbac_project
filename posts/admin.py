from django.contrib import admin
from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Custom admin for Post model"""
    
    list_display = ('title', 'author', 'comment_count', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at', 'author')
    search_fields = ('title', 'content', 'author__email')
    readonly_fields = ('created_at', 'updated_at', 'comment_count')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Post Information', {
            'fields': ('title', 'content', 'author')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['soft_delete_selected', 'restore_selected']
    
    def soft_delete_selected(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} posts were soft deleted.')
    soft_delete_selected.short_description = "Soft delete selected posts"
    
    def restore_selected(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} posts were restored.')
    restore_selected.short_description = "Restore selected posts"