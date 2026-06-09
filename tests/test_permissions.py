from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from posts.models import Post
from comments.models import Comment

User = get_user_model()


class RBACPermissionTests(TestCase):
    """Test all permission rules"""
    
    def setUp(self):
        # Create test users
        self.super_admin = User.objects.create_superuser(
            email='super@admin.com',
            password='admin123',
            first_name='Super',
            last_name='Admin'
        )
        
        self.moderator = User.objects.create_user(
            email='moderator@test.com',
            password='mod123',
            first_name='Mod',
            last_name='User',
            role='moderator'
        )
        
        self.regular_user_1 = User.objects.create_user(
            email='user1@test.com',
            password='pass123',
            first_name='Regular',
            last_name='One'
        )
        
        self.regular_user_2 = User.objects.create_user(
            email='user2@test.com',
            password='pass123',
            first_name='Regular',
            last_name='Two'
        )
        
        # Create a post by user1
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post content',
            author=self.regular_user_1
        )
        
        # Create comments
        self.comment_by_user2 = Comment.objects.create(
            content='Comment from user2',
            post=self.post,
            author=self.regular_user_2
        )
        
        self.comment_by_user1 = Comment.objects.create(
            content='Comment from user1',
            post=self.post,
            author=self.regular_user_1
        )
        
        # Setup API clients
        self.client = APIClient()
    
    def test_guest_permissions(self):
        """Test Guest permissions - No authentication required"""
        # Guest can view posts
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Guest can view comments
        response = self.client.get('/api/comments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Guest cannot create posts
        response = self.client.post('/api/posts/', {
            'title': 'Guest Post',
            'content': 'Guest content'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Guest cannot create comments
        response = self.client.post('/api/comments/', {
            'content': 'Guest comment',
            'post': self.post.id
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Guest cannot update posts
        response = self.client.put(f'/api/posts/{self.post.id}/', {
            'title': 'Updated by Guest'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Guest cannot delete posts
        response = self.client.delete(f'/api/posts/{self.post.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_regular_user_permissions(self):
        """Test Regular User permissions"""
        self.client.force_authenticate(user=self.regular_user_1)
        
        # Can create post
        response = self.client.post('/api/posts/', {
            'title': 'New Post',
            'content': 'This is my new post'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_post = Post.objects.get(title='New Post')
        
        # Can update own post
        response = self.client.put(f'/api/posts/{new_post.id}/', {
            'title': 'Updated Post',
            'content': 'Updated content'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Can delete own post
        response = self.client.delete(f'/api/posts/{new_post.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Create another post for testing deletion permission
        another_post = Post.objects.create(
            title='Another User Post',
            content='Content by user2',
            author=self.regular_user_2
        )
        
        # Cannot delete other's post (should return 403)
        response = self.client.delete(f'/api/posts/{another_post.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Cannot update other's post (should return 403)
        response = self.client.put(f'/api/posts/{another_post.id}/', {
            'title': 'Hacked Title'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_post_owner_comment_deletion(self):
        """Test that post owner can delete comments on their post"""
        self.client.force_authenticate(user=self.regular_user_1)
        
        # Create a fresh comment for testing
        fresh_comment = Comment.objects.create(
            content='Fresh comment for deletion test',
            post=self.post,
            author=self.regular_user_2
        )
        
        # User1 (post owner) can delete User2's comment
        response = self.client.delete(f'/api/comments/{fresh_comment.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify comment is soft deleted
        fresh_comment.refresh_from_db()
        self.assertFalse(fresh_comment.is_active)
        
        # Create another comment for testing
        another_comment = Comment.objects.create(
            content='Another comment',
            post=self.post,
            author=self.regular_user_2
        )
        
        # User1 can delete their own comment
        response = self.client.delete(f'/api/comments/{self.comment_by_user1.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_comment_author_deletion(self):
        """Test that comment author can delete their own comments"""
        self.client.force_authenticate(user=self.regular_user_2)
        
        # Create a fresh comment by user2
        fresh_comment = Comment.objects.create(
            content='User2 comment for deletion',
            post=self.post,
            author=self.regular_user_2
        )
        
        # User2 can delete their own comment
        response = self.client.delete(f'/api/comments/{fresh_comment.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify comment is soft deleted
        fresh_comment.refresh_from_db()
        self.assertFalse(fresh_comment.is_active)
        
        # User2 cannot delete User1's comment (should return 403)
        response = self.client.delete(f'/api/comments/{self.comment_by_user1.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_moderator_permissions(self):
        """Test Moderator permissions"""
        self.client.force_authenticate(user=self.moderator)
        
        # Create a fresh post for testing
        fresh_post = Post.objects.create(
            title='Fresh Post for Moderator',
            content='This post will be deleted by moderator',
            author=self.regular_user_1
        )
        
        # Moderator can delete any post
        response = self.client.delete(f'/api/posts/{fresh_post.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify post is soft deleted
        fresh_post.refresh_from_db()
        self.assertFalse(fresh_post.is_active)
        
        # Create another post with a comment for testing
        another_post = Post.objects.create(
            title='Another Post for Comment Deletion',
            content='Content for testing comment deletion',
            author=self.regular_user_1
        )
        
        fresh_comment = Comment.objects.create(
            content='Comment to be deleted by moderator',
            post=another_post,
            author=self.regular_user_2
        )
        
        # Moderator can delete any comment
        response = self.client.delete(f'/api/comments/{fresh_comment.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify comment is soft deleted
        fresh_comment.refresh_from_db()
        self.assertFalse(fresh_comment.is_active)
        
        # Moderator cannot manage users (no user management endpoints exposed for moderator)
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_super_admin_permissions(self):
        """Test Super Admin permissions"""
        self.client.force_authenticate(user=self.super_admin)
        
        # Create a fresh post for testing
        fresh_post = Post.objects.create(
            title='Fresh Post for Super Admin',
            content='This post will be deleted by super admin',
            author=self.regular_user_1
        )
        
        # Super Admin can delete any post
        response = self.client.delete(f'/api/posts/{fresh_post.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify post is soft deleted
        fresh_post.refresh_from_db()
        self.assertFalse(fresh_post.is_active)
        
        # Create another post with a comment
        another_post = Post.objects.create(
            title='Another Post for Comment Deletion',
            content='Content for testing',
            author=self.regular_user_1
        )
        
        fresh_comment = Comment.objects.create(
            content='Comment to be deleted by super admin',
            post=another_post,
            author=self.regular_user_2
        )
        
        # Super Admin can delete any comment
        response = self.client.delete(f'/api/comments/{fresh_comment.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify comment is soft deleted
        fresh_comment.refresh_from_db()
        self.assertFalse(fresh_comment.is_active)
        
        # Super Admin can manage users
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Can update user roles
        response = self.client.put(f'/api/auth/users/{self.regular_user_2.id}/', {
            'role': 'moderator'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.regular_user_2.refresh_from_db()
        self.assertEqual(self.regular_user_2.role, 'moderator')
    
    def test_third_party_comment_deletion(self):
        """Test that User C cannot delete User B's comment on User A's post"""
        # Create a third user
        user_c = User.objects.create_user(
            email='userc@test.com',
            password='pass123',
            first_name='User',
            last_name='C'
        )
        
        # Create a new post by user A
        post_a = Post.objects.create(
            title='Post by User A',
            content='Content',
            author=self.regular_user_1
        )
        
        # Create comment by user B on post A
        comment_by_user_b = Comment.objects.create(
            content='Comment by User B',
            post=post_a,
            author=self.regular_user_2
        )
        
        # User C tries to delete User B's comment
        self.client.force_authenticate(user=user_c)
        response = self.client.delete(f'/api/comments/{comment_by_user_b.id}/')
        
        # Should be forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Comment should still exist and be active
        comment_by_user_b.refresh_from_db()
        self.assertTrue(comment_by_user_b.is_active)
    
    def test_soft_delete_functionality(self):
        """Test that posts and comments are soft deleted"""
        self.client.force_authenticate(user=self.super_admin)
        
        # Create a fresh post for testing
        fresh_post = Post.objects.create(
            title='Post for Soft Delete Test',
            content='This post will be soft deleted',
            author=self.regular_user_1
        )
        
        # Create comments on this post
        comment1 = Comment.objects.create(
            content='Comment 1 on soft delete post',
            post=fresh_post,
            author=self.regular_user_2
        )
        comment2 = Comment.objects.create(
            content='Comment 2 on soft delete post',
            post=fresh_post,
            author=self.regular_user_1
        )
        
        # Delete post
        response = self.client.delete(f'/api/posts/{fresh_post.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Post should still exist but be inactive
        fresh_post.refresh_from_db()
        self.assertFalse(fresh_post.is_active)
        
        # Comments should also be soft deleted
        comment1.refresh_from_db()
        comment2.refresh_from_db()
        self.assertFalse(comment1.is_active)
        self.assertFalse(comment2.is_active)
        
        # Deleted posts should not appear in list
        response = self.client.get('/api/posts/')
        self.assertNotContains(response, fresh_post.title)
        
        # Trying to get deleted post should return 404
        response = self.client.get(f'/api/posts/{fresh_post.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_filtering_and_pagination(self):
        """Test filtering, searching, and pagination"""
        self.client.force_authenticate(user=self.regular_user_1)
        
        # Create multiple posts with distinct titles
        for i in range(25):
            Post.objects.create(
                title=f'Unique Test Post {i} for Search',
                content=f'Content {i}',
                author=self.regular_user_1
            )
        
        # Test pagination (default page size is 20)
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 20)
        self.assertIsNotNone(response.data['next'])
        
        # Test search
        response = self.client.get('/api/posts/?search=Unique Test Post 1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) > 0)
        
        # Test ordering
        response = self.client.get('/api/posts/?ordering=title')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test filtering by author
        response = self.client.get(f'/api/posts/?author={self.regular_user_1.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)