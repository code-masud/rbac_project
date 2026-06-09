from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Comment
from .serializers import CommentSerializer, CommentCreateSerializer
from .permissions import CanCreateComment, CanModifyComment


@extend_schema_view(
    get=extend_schema(summary="List comments", description="Get paginated list of comments with filtering"),
    post=extend_schema(summary="Create comment", description="Create a new comment on a post")
)
class CommentListCreateView(generics.ListCreateAPIView):
    """List and create comments"""
    
    queryset = Comment.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, CanCreateComment]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['post', 'author']
    search_fields = ['content', 'author__email']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommentCreateSerializer
        return CommentSerializer
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


@extend_schema_view(
    get=extend_schema(summary="Get comment details", description="Retrieve a specific comment by ID"),
    delete=extend_schema(summary="Delete comment", description="Delete a comment (Author, Post Owner, Moderator, or Super Admin)")
)
class CommentDetailView(generics.RetrieveDestroyAPIView):
    """Retrieve or delete a comment"""
    
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, CanModifyComment]
    
    def perform_destroy(self, instance):
        # Soft delete the comment
        instance.is_active = False
        instance.save()