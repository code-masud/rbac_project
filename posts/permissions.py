from rest_framework import permissions


class CanCreatePost(permissions.BasePermission):
    """Allow only regular users and above to create posts"""
    
    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user and request.user.is_authenticated and not request.user.is_guest
        return True


class CanModifyPost(permissions.BasePermission):
    """Check if user can modify a post"""
    
    def has_permission(self, request, view):
        # For DELETE requests, we need to check object permissions
        # This method is called before has_object_permission
        return True
    
    def has_object_permission(self, request, view, obj):
        # Safe methods (GET, HEAD, OPTIONS) are always allowed
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Super admin can do anything
        if request.user.is_super_admin:
            return True
        
        # Moderator can delete any post
        if request.method == 'DELETE' and request.user.is_moderator:
            return True
        
        # Regular users can only modify their own posts
        if request.user.is_regular_user and obj.author == request.user:
            return True
        
        # For PUT/PATCH (update operations), only the author can modify
        if request.method in ['PUT', 'PATCH'] and obj.author != request.user:
            return False
        
        return False