
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from faker import Faker
import random
import sys
from datetime import timedelta

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Generate sample data for testing RBAC functionality'
    
    def add_arguments(self, parser):
        # User generation arguments
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of regular users to create (default: 20)'
        )
        parser.add_argument(
            '--moderators',
            type=int,
            default=3,
            help='Number of moderators to create (default: 3)'
        )
        parser.add_argument(
            '--super-admins',
            type=int,
            default=2,
            help='Number of super admins to create (default: 2)'
        )
        
        # Content generation arguments
        parser.add_argument(
            '--posts',
            type=int,
            default=100,
            help='Number of posts to create (default: 100)'
        )
        parser.add_argument(
            '--comments',
            type=int,
            default=300,
            help='Number of comments to create (default: 300)'
        )
        
        # Utility arguments
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean all existing sample data before generating new data'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Batch size for bulk creation (default: 100)'
        )
        parser.add_argument(
            '--seed',
            type=int,
            default=None,
            help='Random seed for reproducible data generation'
        )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_ids = []
        self.created_counts = {
            'users': 0,
            'moderators': 0,
            'super_admins': 0,
            'posts': 0,
            'comments': 0
        }
    
    def handle(self, *args, **options):
        """Main command handler"""
        
        # Set random seed for reproducibility if provided
        if options['seed']:
            fake.seed_instance(options['seed'])
            random.seed(options['seed'])
            self.stdout.write(self.style.SUCCESS(f'Using random seed: {options["seed"]}'))
        
        # Clean existing data if requested
        if options['clean']:
            self.clean_existing_data()
        
        # Generate data
        try:
            with transaction.atomic():
                self.generate_users(options)
                self.generate_posts(options)
                self.generate_comments(options)
            
            # Print summary
            self.print_summary()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating sample data: {str(e)}')
            )
            sys.exit(1)
    
    def clean_existing_data(self):
        """Clean all existing non-superuser data"""
        self.stdout.write(self.style.WARNING('Cleaning existing sample data...'))
        
        # Delete all comments
        from comments.models import Comment
        comment_count = Comment.objects.count()
        Comment.objects.all().delete()
        self.stdout.write(f'  Deleted {comment_count} comments')
        
        # Delete all posts
        from posts.models import Post
        post_count = Post.objects.count()
        Post.objects.all().delete()
        self.stdout.write(f'  Deleted {post_count} posts')
        
        # Delete all non-superuser users
        user_count = User.objects.exclude(is_superuser=True).count()
        User.objects.exclude(is_superuser=True).delete()
        self.stdout.write(f'  Deleted {user_count} users')
        
        self.stdout.write(self.style.SUCCESS('Cleaning completed!\n'))
    
    def generate_users(self, options):
        """Generate users with different roles"""
        self.stdout.write(self.style.NOTICE('Generating users...'))
        
        # Create super admins
        for i in range(options['super_admins']):
            user = self.create_user(
                role='super_admin',
                is_staff=True,
                is_superuser=True
            )
            self.user_ids.append(user.id)
            self.created_counts['super_admins'] += 1
            self.print_progress('Super Admin', i + 1, options['super_admins'])
        
        # Create moderators
        for i in range(options['moderators']):
            user = self.create_user(role='moderator')
            self.user_ids.append(user.id)
            self.created_counts['moderators'] += 1
            self.print_progress('Moderator', i + 1, options['moderators'])
        
        # Create regular users
        for i in range(options['users']):
            user = self.create_user(role='regular_user')
            self.user_ids.append(user.id)
            self.created_counts['users'] += 1
            self.print_progress('Regular User', i + 1, options['users'])
        
        self.stdout.write(self.style.SUCCESS(
            f'\n  ✓ Created {self.created_counts["users"]} regular users, '
            f'{self.created_counts["moderators"]} moderators, and '
            f'{self.created_counts["super_admins"]} super admins'
        ))
    
    def create_user(self, role, is_staff=False, is_superuser=False):
        """Create a single user with fake data"""
        
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}@{fake.free_email_domain()}"
        
        # Ensure unique email
        while User.objects.filter(email=email).exists():
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@{fake.free_email_domain()}"
        
        user = User.objects.create_user(
            email=email,
            password='Test@123456',  # Common password for all test users
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_staff=is_staff,
            is_superuser=is_superuser,
            is_active=True
        )
        
        return user
    
    def generate_posts(self, options):
        """Generate posts with realistic content"""
        self.stdout.write(self.style.NOTICE('\nGenerating posts...'))
        
        if not self.user_ids:
            self.stdout.write(self.style.WARNING('  No users available for posts'))
            return
        
        from posts.models import Post
        
        posts_to_create = []
        batch_size = options['batch_size']
        
        for i in range(options['posts']):
            # Random author from existing users
            author_id = random.choice(self.user_ids)
            
            # Generate realistic post content
            paragraph_count = random.randint(2, 8)
            content = '\n\n'.join(fake.paragraphs(nb=paragraph_count))
            
            post = Post(
                title=fake.sentence(nb_words=random.randint(3, 12)),
                content=content,
                author_id=author_id,
                is_active=True,
                created_at=fake.date_time_between(
                    start_date='-30d',
                    end_date='now',
                    tzinfo=timezone.get_current_timezone()
                )
            )
            
            posts_to_create.append(post)
            
            # Bulk create in batches
            if len(posts_to_create) >= batch_size:
                Post.objects.bulk_create(posts_to_create)
                self.created_counts['posts'] += len(posts_to_create)
                self.print_progress('Post', self.created_counts['posts'], options['posts'])
                posts_to_create = []
            
            # Update progress
            if (i + 1) % 10 == 0:
                self.print_progress('Post', i + 1, options['posts'])
        
        # Create remaining posts
        if posts_to_create:
            Post.objects.bulk_create(posts_to_create)
            self.created_counts['posts'] += len(posts_to_create)
        
        self.stdout.write(self.style.SUCCESS(
            f'  ✓ Created {self.created_counts["posts"]} posts'
        ))
    
    def generate_comments(self, options):
        """Generate comments on posts"""
        self.stdout.write(self.style.NOTICE('\nGenerating comments...'))
        
        from posts.models import Post
        from comments.models import Comment
        
        posts = list(Post.objects.filter(is_active=True).values_list('id', 'author_id'))
        
        if not posts:
            self.stdout.write(self.style.WARNING('  No posts available for comments'))
            return
        
        comments_to_create = []
        batch_size = options['batch_size']
        
        for i in range(options['comments']):
            # Random post
            post_id, post_author_id = random.choice(posts)
            
            # Random author (could be post author or other users)
            # Weighted towards regular users
            author_id = random.choice([
                post_author_id,  # Post owner comments
                random.choice(self.user_ids),  # Random user
            ])
            
            # Generate comment content
            comment_length = random.randint(1, 5)
            content = ' '.join(fake.sentences(nb=comment_length))
            
            comment = Comment(
                content=content,
                post_id=post_id,
                author_id=author_id,
                is_active=True,
                created_at=fake.date_time_between(
                    start_date='-15d',
                    end_date='now',
                    tzinfo=timezone.get_current_timezone()
                )
            )
            
            comments_to_create.append(comment)
            
            # Bulk create in batches
            if len(comments_to_create) >= batch_size:
                Comment.objects.bulk_create(comments_to_create)
                self.created_counts['comments'] += len(comments_to_create)
                self.print_progress('Comment', self.created_counts['comments'], options['comments'])
                comments_to_create = []
            
            # Update progress
            if (i + 1) % 50 == 0:
                self.print_progress('Comment', i + 1, options['comments'])
        
        # Create remaining comments
        if comments_to_create:
            Comment.objects.bulk_create(comments_to_create)
            self.created_counts['comments'] += len(comments_to_create)
        
        self.stdout.write(self.style.SUCCESS(
            f'  ✓ Created {self.created_counts["comments"]} comments'
        ))
    
    def print_progress(self, item_type, current, total):
        """Print progress indicator"""
        if total > 0:
            percentage = (current / total) * 100
            if percentage % 10 == 0 or current == total:
                self.stdout.write(
                    f'  {item_type}: {current}/{total} ({percentage:.0f}%)',
                    ending='\r'
                )
    
    def print_summary(self):
        """Print detailed summary of generated data"""
        from posts.models import Post
        from comments.models import Comment
        
        total_users = User.objects.count()
        total_posts = Post.objects.count()
        total_comments = Comment.objects.count()
        
        # Role breakdown
        role_counts = {
            'super_admin': User.objects.filter(role='super_admin').count(),
            'moderator': User.objects.filter(role='moderator').count(),
            'regular_user': User.objects.filter(role='regular_user').count(),
            'guest': User.objects.filter(role='guest').count(),
        }
        
        # Post statistics
        posts_with_comments = Post.objects.filter(comments__isnull=False).distinct().count()
        avg_comments_per_post = total_comments / total_posts if total_posts > 0 else 0
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('SAMPLE DATA GENERATION COMPLETE'))
        self.stdout.write('=' * 60)
        
        self.stdout.write('\n📊 USER STATISTICS:')
        self.stdout.write(f'  • Total Users: {total_users}')
        self.stdout.write(f'  • Super Admins: {role_counts["super_admin"]}')
        self.stdout.write(f'  • Moderators: {role_counts["moderator"]}')
        self.stdout.write(f'  • Regular Users: {role_counts["regular_user"]}')
        self.stdout.write(f'  • Guests: {role_counts["guest"]}')
        
        self.stdout.write('\n📝 CONTENT STATISTICS:')
        self.stdout.write(f'  • Total Posts: {total_posts}')
        self.stdout.write(f'  • Total Comments: {total_comments}')
        self.stdout.write(f'  • Posts with Comments: {posts_with_comments}')
        self.stdout.write(f'  • Average Comments/Post: {avg_comments_per_post:.2f}')
        
        # Sample credentials
        self.stdout.write('\n🔑 SAMPLE LOGIN CREDENTIALS:')
        sample_users = User.objects.filter(
            role__in=['super_admin', 'moderator', 'regular_user']
        )[:5]
        
        for user in sample_users:
            self.stdout.write(f'  • {user.role.upper()}: {user.email} / Test@123456')
        
        self.stdout.write('\n📚 USEFUL COMMANDS:')
        self.stdout.write('  • python manage.py generate_sample_data --clean')
        self.stdout.write('  • python manage.py generate_sample_data --users=100 --posts=500 --comments=1000')
        self.stdout.write('  • python manage.py generate_sample_data --seed=42')
        
        self.stdout.write('\n🌐 API ENDPOINTS TO TEST:')
        self.stdout.write('  • GET  /api/posts/     - List all posts')
        self.stdout.write('  • POST /api/auth/login/ - Login with above credentials')
        self.stdout.write('  • GET  /api/docs/      - View API documentation')
        
        self.stdout.write('\n' + '=' * 60)


class GenerateSpecificDataCommand(BaseCommand):
    """
    Additional command for generating specific scenarios
    """
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--scenario',
            type=str,
            choices=['conflict', 'popular', 'inactive', 'stress'],
            required=True,
            help='Scenario type to generate'
        )
        parser.add_argument(
            '--size',
            type=int,
            default=10,
            help='Size of scenario data'
        )
    
    def handle(self, *args, **options):
        scenario = options['scenario']
        size = options['size']
        
        if scenario == 'conflict':
            self.generate_conflict_scenario(size)
        elif scenario == 'popular':
            self.generate_popular_posts_scenario(size)
        elif scenario == 'inactive':
            self.generate_inactive_content_scenario(size)
        elif scenario == 'stress':
            self.generate_stress_test_data(size)
    
    def generate_conflict_scenario(self, size):
        """Generate scenario with multiple comments and interactions"""
        self.stdout.write('Generating conflict scenario...')
        
        # Create a controversial post
        post_author = User.objects.filter(role='regular_user').first()
        if not post_author:
            self.stdout.write(self.style.ERROR('No regular users found. Run main command first.'))
            return
        
        from posts.models import Post
        from comments.models import Comment
        
        post = Post.objects.create(
            title=f"Controversial Post: {fake.catch_phrase()}",
            content=fake.paragraph(nb_sentences=10),
            author=post_author
        )
        
        # Add many comments from different users
        users = list(User.objects.exclude(id=post_author.id))[:size]
        
        for i, user in enumerate(users):
            Comment.objects.create(
                content=fake.paragraph(nb_sentences=random.randint(1, 3)),
                post=post,
                author=user
            )
            
        self.stdout.write(self.style.SUCCESS(
            f'✓ Created conflict scenario: Post "{post.title[:50]}" with {len(users)} comments'
        ))
    
    def generate_popular_posts_scenario(self, size):
        """Generate highly popular posts with many comments"""
        self.stdout.write('Generating popular posts scenario...')
        
        from posts.models import Post
        from comments.models import Comment
        
        users = list(User.objects.all())
        
        for i in range(min(size, 5)):  # Create up to 5 popular posts
            post = Post.objects.create(
                title=f"TRENDING: {fake.catch_phrase()}",
                content=fake.paragraph(nb_sentences=15),
                author=random.choice(users)
            )
            
            # Add 50-200 comments to each popular post
            comment_count = random.randint(50, 200)
            for j in range(comment_count):
                Comment.objects.create(
                    content=fake.sentence(),
                    post=post,
                    author=random.choice(users)
                )
                
            self.stdout.write(f'  • Post {i+1}: "{post.title[:40]}" with {comment_count} comments')
    
    def generate_inactive_content_scenario(self, size):
        """Generate content that is soft deleted"""
        self.stdout.write('Generating inactive content scenario...')
        
        from posts.models import Post
        from comments.models import Comment
        
        # Create and soft delete posts
        for i in range(size):
            post = Post.objects.create(
                title=f"Deleted Post {i+1}: {fake.sentence()}",
                content=fake.paragraph(),
                author=random.choice(User.objects.all())
            )
            post.is_active = False
            post.save()
            
            # Add some comments to deleted posts
            for j in range(random.randint(0, 5)):
                comment = Comment.objects.create(
                    content=fake.sentence(),
                    post=post,
                    author=random.choice(User.objects.all())
                )
                comment.is_active = False
                comment.save()
        
        self.stdout.write(self.style.SUCCESS(
            f'✓ Created {size} inactive posts with comments'
        ))
    
    def generate_stress_test_data(self, size):
        """Generate large dataset for performance testing"""
        self.stdout.write(f'Generating stress test data (size: {size})...')
        
        from posts.models import Post
        from comments.models import Comment
        
        # Create a single user for bulk operations
        bulk_user = User.objects.create_user(
            email='bulk_test@example.com',
            password='BulkTest123',
            first_name='Bulk',
            last_name='Tester'
        )
        
        # Bulk create posts
        posts = []
        for i in range(size):
            posts.append(Post(
                title=f'Stress Test Post {i+1}',
                content=fake.paragraph(nb_sentences=50),
                author=bulk_user
            ))
        
        Post.objects.bulk_create(posts)
        
        # Bulk create comments
        created_posts = list(Post.objects.filter(author=bulk_user))
        comments = []
        for post in created_posts[:size]:  # Limit comments to avoid overload
            for j in range(5):  # 5 comments per post
                comments.append(Comment(
                    content=fake.paragraph(),
                    post=post,
                    author=bulk_user
                ))
        
        Comment.objects.bulk_create(comments)
        
        self.stdout.write(self.style.SUCCESS(
            f'✓ Stress test data: {size} posts, {len(comments)} comments'
        ))