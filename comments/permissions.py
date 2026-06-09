from rest_framework import permissions


class CanCreateComment(permissions.BasePermission):
    """Allow only authenticated users (not guests) to create comments"""
    
    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user and request.user.is_authenticated and not request.user.is_guest
        return True


class CanModifyComment(permissions.BasePermission):
    """
    Custom permission for comment modification:
    - Post owners can delete comments on their posts
    - Comment authors can delete their own comments
    - Moderators can delete any comment
    - Super Admins can delete any comment
    """
    
    def has_permission(self, request, view):
        # For DELETE requests, we need to check object permissions
        return True
    
    def has_object_permission(self, request, view, obj):
        # Safe methods are always allowed
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only DELETE operation is allowed for modifications
        if request.method != 'DELETE':
            return False
        
        # Super admin can delete any comment
        if request.user.is_super_admin:
            return True
        
        # Moderator can delete any comment
        if request.user.is_moderator:
            return True
        
        # Comment author can delete their own comment
        if obj.author == request.user:
            return True
        
        # Post owner can delete comments on their posts
        if obj.post.author == request.user:
            return True
        
        return False