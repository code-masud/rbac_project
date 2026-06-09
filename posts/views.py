from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Post
from .serializers import PostSerializer, PostCreateSerializer
from .permissions import CanCreatePost, CanModifyPost
from .filters import PostFilter


@extend_schema_view(
    get=extend_schema(summary="List all posts", description="Get paginated list of posts with filtering and ordering"),
    post=extend_schema(summary="Create a new post", description="Create a new post (Authenticated users only)")
)
class PostListCreateView(generics.ListCreateAPIView):
    """List and create posts"""
    
    queryset = Post.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, CanCreatePost]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PostFilter
    search_fields = ['title', 'content', 'author__email']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostCreateSerializer
        return PostSerializer
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {'error': f'Error fetching posts: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema_view(
    get=extend_schema(summary="Get post details", description="Retrieve a specific post by ID"),
    put=extend_schema(summary="Update post", description="Update a post (Owner only)"),
    patch=extend_schema(summary="Partial update post", description="Partially update a post (Owner only)"),
    delete=extend_schema(summary="Delete post", description="Delete a post (Owner, Moderator, or Super Admin)")
)
class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a post"""
    
    queryset = Post.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, CanModifyPost]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PostCreateSerializer
        return PostSerializer
    
    def get_object(self):
        """Override to handle soft deletion"""
        try:
            obj = super().get_object()
            # For DELETE operation, we want to allow deleting even if already soft deleted?
            # Actually, we should return 404 if already deleted
            if self.request.method == 'DELETE' and not obj.is_active:
                raise NotFound({"detail": "Post not found."})
            # For other methods, also return 404 if soft deleted
            if self.request.method not in permissions.SAFE_METHODS and not obj.is_active:
                raise NotFound({"detail": "Post not found."})
            return obj
        except Post.DoesNotExist:
            raise NotFound({"detail": "Post not found."})
    
    def perform_update(self, serializer):
        post = self.get_object()
        # Check permission for update
        if not (self.request.user.is_super_admin or post.author == self.request.user):
            raise PermissionDenied("You can only edit your own posts")
        
        # Check if trying to update a soft-deleted post
        if not post.is_active:
            raise PermissionDenied("Cannot update a deleted post")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        # Check permission for deletion
        if not (self.request.user.is_super_admin or 
                self.request.user.is_moderator or 
                instance.author == self.request.user):
            raise PermissionDenied("You don't have permission to delete this post")
        
        # Soft delete the post
        instance.is_active = False
        instance.save()
        
        # Also soft delete all comments on this post
        instance.comments.update(is_active=False)
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except NotFound as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )