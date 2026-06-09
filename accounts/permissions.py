from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """Allow access only to Super Admins"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_super_admin


class IsModeratorOrSuperAdmin(permissions.BasePermission):
    """Allow access to Moderators and Super Admins"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_super_admin or request.user.is_moderator


class IsRegularUserOrAbove(permissions.BasePermission):
    """Allow access to Regular Users, Moderators, and Super Admins"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_super_admin or request.user.is_moderator or request.user.is_regular_user


class IsOwnerOrSuperAdmin(permissions.BasePermission):
    """Allow access to owner of the object or Super Admin"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_super_admin:
            return True
        return obj.id == request.user.id