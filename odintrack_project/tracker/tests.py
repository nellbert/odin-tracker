import datetime  # Standard library

from django.contrib.auth.models import User
from django.db import models
from django.test import Client, TestCase
from django.urls import reverse # Import reverse, even if not used with placeholders yet
from django.utils import timezone

from unittest.mock import MagicMock, patch # Standard library mock

# #############################################################################
# SECTION: Placeholder Models
# -----------------------------------------------------------------------------
# These are placeholder Django models. In a real project, these would be
# defined in tracker/models.py. They are included here to allow tests
# to run and demonstrate interactions with the database, even if the
# actual models.py is not yet available or fully defined.
# Ensure these definitions are compatible with the tests below.
# #############################################################################

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    total_points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Section(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title

class Lesson(models.Model):
    LESSON_TYPE_CHOICES = [
        ('Lesson', 'Lesson'),
        ('Project', 'Project'),
    ]
    title = models.CharField(max_length=100)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='lessons')
    lesson_type = models.CharField(max_length=10, choices=LESSON_TYPE_CHOICES)
    points = models.IntegerField()
    # order = models.PositiveIntegerField(default=0) # Example of a potential field

    def __str__(self):
        return self.title

class Achievement(models.Model):
    achievement_slug = models.SlugField(unique=True, max_length=100)
    title = models.CharField(max_length=100)
    description = models.TextField()
    points_reward = models.IntegerField()

    def __str__(self):
        return self.title

class DailyChallenge(models.Model):
    CHALLENGE_TYPE_CHOICES = [
        ('COMPLETE_N_LESSONS', 'Complete N Lessons'),
        ('EARN_N_POINTS', 'Earn N Points'),
        ('COMPLETE_PROJECT', 'Complete a Project'),
    ]
    title = models.CharField(max_length=100)
    description = models.TextField()
    challenge_type = models.CharField(max_length=50, choices=CHALLENGE_TYPE_CHOICES)
    target_value = models.IntegerField()
    points_reward = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class UserStreak(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='streak_data')
    current_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s streak"

class Completion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='completions')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='completions')
    completion_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'lesson')

    def __str__(self):
        return f"{self.user.username} completed {self.lesson.title}"

class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements_earned')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='earned_by')
    awarded_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'achievement')

    def __str__(self):
        return f"{self.user.username} earned {self.achievement.title}"

class UserDailyChallenge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_challenges')
    challenge = models.ForeignKey(DailyChallenge, on_delete=models.CASCADE, related_name='user_progress', null=True, blank=True) # Allow null challenge
    assigned_date = models.DateField(default=datetime.date.today)
    completed_date = models.DateField(null=True, blank=True)
    current_progress = models.IntegerField(default=0)
    initial_points_at_assignment = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s progress on {self.challenge.title if self.challenge else 'No Challenge'}"


# #############################################################################
# SECTION: Placeholder Data & Logic
# -----------------------------------------------------------------------------
# Placeholder data (like ACHIEVEMENT_SLUGS) and logic functions
# (award_achievement, etc.). These simulate the behavior of functions that
# would typically reside in other app files (e.g., tracker/achievements.py,
# tracker/daily_challenges_logic.py).
# #############################################################################

# Default ACHIEVEMENT_SLUGS. This would typically be in tracker.achievements
BASE_ACHIEVEMENT_SLUGS = {
    'first-lesson-completed': {'title': 'First Lesson!', 'description': 'You completed your first lesson.', 'points_reward': 10},
    'html-beginner': {'title': 'HTML Beginner', 'description': 'Completed all HTML lessons.', 'points_reward': 50},
    'css-beginner': {'title': 'CSS Beginner', 'description': 'Completed all CSS lessons.', 'points_reward': 50},
    'js-beginner': {'title': 'JavaScript Beginner', 'description': 'Completed all JavaScript lessons.', 'points_reward': 75},
    'first-project-completed': {'title': 'Project Starter', 'description': 'You completed your first project.', 'points_reward': 100},
    'points-milestone-100': {'title': 'Centurion', 'description': 'Earned 100 points.', 'points_reward': 20},
    'points-milestone-500': {'title': 'Five Hundred Club', 'description': 'Earned 500 points.', 'points_reward': 50},
    'streak-3-days': {'title': 'On a Roll!', 'description': 'Maintained a 3-day streak.', 'points_reward': 30},
    'streak-7-days': {'title': 'Committed Learner', 'description': 'Maintained a 7-day streak.', 'points_reward': 70},
}

# Attempt to import actual achievement logic and slugs
try:
    from tracker.achievements import award_achievement, check_and_award_achievements, ACHIEVEMENT_SLUGS as ACTUAL_ACHIEVEMENT_SLUGS
except ImportError:
    # print("Warning: Actual achievement logic from tracker.achievements not found. Using placeholders.")
    ACTUAL_ACHIEVEMENT_SLUGS = BASE_ACHIEVEMENT_SLUGS.copy() # Use a copy for modifications

    def award_achievement(user, achievement_slug_details_param, request=None, profile=None):
        if not user or not achievement_slug_details_param:
            return None, False
        
        slug_to_check = achievement_slug_details_param
        if isinstance(achievement_slug_details_param, dict):
             slug_to_check = achievement_slug_details_param.get('slug', list(achievement_slug_details_param.keys())[0] if isinstance(achievement_slug_details_param,dict) else None)


        try:
            achievement_obj = Achievement.objects.get(achievement_slug=slug_to_check)
        except Achievement.DoesNotExist:
            return None, False

        if profile is None:
            profile, _ = UserProfile.objects.get_or_create(user=user)

        ua, created = UserAchievement.objects.get_or_create(user=user, achievement=achievement_obj)
        if created:
            profile.total_points += achievement_obj.points_reward
            profile.save()
            if request and hasattr(request, 'messages') and hasattr(request.messages, 'success'):
                 request.messages.success(request, f"Achievement Unlocked: {achievement_obj.title}!")
            return ua, True
        return ua, False

    def check_and_award_achievements(user, completion_instance=None, request=None):
        # Highly simplified placeholder.
        if completion_instance and Completion.objects.filter(user=user).count() == 1:
            award_achievement(user, ACTUAL_ACHIEVEMENT_SLUGS['first-lesson-completed'], request=request)
        if completion_instance and completion_instance.lesson.lesson_type == 'Project':
            if not UserAchievement.objects.filter(user=user, achievement__achievement_slug='first-project-completed').exists():
                 if Completion.objects.filter(user=user, lesson__lesson_type='Project').count() == 1:
                    award_achievement(user, ACTUAL_ACHIEVEMENT_SLUGS['first-project-completed'], request=request)
        pass

# Attempt to import actual daily challenge logic
try:
    from tracker.daily_challenges_logic import assign_new_daily_challenge, update_daily_challenge_progress
except ImportError:
    # print("Warning: Actual daily challenge logic from tracker.daily_challenges_logic not found. Using placeholders.")
    def assign_new_daily_challenge(user):
        active_challenges = DailyChallenge.objects.filter(is_active=True)
        today = timezone.now().date()
        
        if not active_challenges.exists():
            udc, _ = UserDailyChallenge.objects.update_or_create(
                user=user, assigned_date=today,
                defaults={'challenge': None, 'current_progress': 0, 'completed_date': None, 'initial_points_at_assignment': None}
            )
            return udc

        udc, created = UserDailyChallenge.objects.get_or_create(
            user=user, assigned_date=today,
            defaults={'challenge': active_challenges.first(), 'current_progress': 0}
        )

        if not created and udc.challenge and udc.challenge.is_active and udc.completed_date is None:
            return udc
        
        chosen_challenge = active_challenges.order_by('?').first()
        initial_points = None
        if chosen_challenge and chosen_challenge.challenge_type == 'EARN_N_POINTS': # Check if chosen_challenge is not None
            profile, _ = UserProfile.objects.get_or_create(user=user)
            initial_points = profile.total_points

        udc.challenge = chosen_challenge
        udc.current_progress = 0
        udc.completed_date = None
        udc.initial_points_at_assignment = initial_points
        udc.assigned_date = today
        udc.save()
        return udc

    def update_daily_challenge_progress(user, completed_lesson_info=None, points_earned_in_action=None, request=None):
        today = timezone.now().date()
        try:
            udc = UserDailyChallenge.objects.get(user=user, assigned_date=today)
        except UserDailyChallenge.DoesNotExist: return

        if udc.completed_date or not udc.challenge or not udc.challenge.is_active: return

        challenge = udc.challenge
        profile, _ = UserProfile.objects.get_or_create(user=user)
        updated = False

        if challenge.challenge_type == 'COMPLETE_N_LESSONS' and completed_lesson_info:
            udc.current_progress += 1
            updated = True
        elif challenge.challenge_type == 'EARN_N_POINTS':
            current_earned = profile.total_points - (udc.initial_points_at_assignment or 0)
            udc.current_progress = current_earned
            updated = True
        elif challenge.challenge_type == 'COMPLETE_PROJECT' and completed_lesson_info:
            if completed_lesson_info.get('lesson_type') == 'Project':
                udc.current_progress += 1
                updated = True
        
        if updated and udc.current_progress >= challenge.target_value:
            udc.completed_date = today
            profile.total_points += challenge.points_reward
            profile.save()
            if request and hasattr(request, 'messages') and hasattr(request.messages, 'success'):
                request.messages.success(request, f"Daily Challenge Completed: {challenge.title}!")
        udc.save()

# Helper class for mocking requests
class MockRequest:
    def __init__(self):
        self.user = None
        self.session = {}
        self.messages = MagicMock()


# #############################################################################
# SECTION: Base Test Case
# #############################################################################

class TrackerBaseTestCase(TestCase):
    @classmethod
    def create_user(cls, username, password, email="test@example.com", first_name="Test", last_name="User"):
        user = User.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        return user, profile

    @classmethod
    def setUpTestData(cls):
        cls.user1, cls.user1_profile = cls.create_user("user1", "password123", email="user1@example.com")
        cls.user2, cls.user2_profile = cls.create_user("user2", "password456", email="user2@example.com")

        cls.setup_sections_lessons()
        cls.setup_achievements() # Uses ACTUAL_ACHIEVEMENT_SLUGS (which is a copy of BASE_ACHIEVEMENT_SLUGS by default)
        cls.setup_daily_challenges()

    @classmethod
    def setup_sections_lessons(cls):
        cls.section_html = Section.objects.create(title="HTML Foundations")
        cls.lesson_html_1 = Lesson.objects.create(section=cls.section_html, title="Introduction to HTML", lesson_type="Lesson", points=10)
        cls.lesson_html_2 = Lesson.objects.create(section=cls.section_html, title="HTML Tags", lesson_type="Lesson", points=15)
        cls.project_html_1 = Lesson.objects.create(section=cls.section_html, title="First HTML Page", lesson_type="Project", points=50)

        cls.section_css = Section.objects.create(title="CSS Foundations")
        cls.lesson_css_1 = Lesson.objects.create(section=cls.section_css, title="Introduction to CSS", lesson_type="Lesson", points=10)
        cls.lesson_css_2 = Lesson.objects.create(section=cls.section_css, title="CSS Selectors", lesson_type="Lesson", points=15)
        cls.project_css_1 = Lesson.objects.create(section=cls.section_css, title="Styling a Page", lesson_type="Project", points=60)

        cls.section_js = Section.objects.create(title="JavaScript Basics")
        cls.lesson_js_1 = Lesson.objects.create(section=cls.section_js, title="Introduction to JavaScript", lesson_type="Lesson", points=20)
        cls.lesson_js_2 = Lesson.objects.create(section=cls.section_js, title="Variables and Data Types", lesson_type="Lesson", points=25)
        cls.project_js_1 = Lesson.objects.create(section=cls.section_js, title="Simple JS Calculator", lesson_type="Project", points=100)

        cls.all_lessons = Lesson.objects.all()
        cls.all_projects = Lesson.objects.filter(lesson_type='Project')

    @classmethod
    def setup_achievements(cls):
        cls.achievements_map = {}
        # ACTUAL_ACHIEVEMENT_SLUGS is used here for consistency if it was successfully imported.
        # If not, it's a copy of BASE_ACHIEVEMENT_SLUGS.
        for slug, details in ACTUAL_ACHIEVEMENT_SLUGS.items():
            if not Achievement.objects.filter(achievement_slug=slug).exists():
                achievement = Achievement.objects.create(
                    achievement_slug=slug,
                    title=details['title'],
                    description=details['description'],
                    points_reward=details['points_reward']
                )
                cls.achievements_map[slug] = achievement
            else:
                cls.achievements_map[slug] = Achievement.objects.get(achievement_slug=slug)


    @classmethod
    def setup_daily_challenges(cls):
        cls.challenge_lessons = DailyChallenge.objects.create(
            title="Complete 2 Lessons", description="Complete any two lessons today.",
            challenge_type="COMPLETE_N_LESSONS", target_value=2, points_reward=20, is_active=True
        )
        cls.challenge_points = DailyChallenge.objects.create(
            title="Earn 50 Points", description="Earn 50 points by completing lessons or projects.",
            challenge_type="EARN_N_POINTS", target_value=50, points_reward=30, is_active=True
        )
        cls.challenge_project = DailyChallenge.objects.create(
            title="Complete a Project", description="Complete any project.",
            challenge_type="COMPLETE_PROJECT", target_value=1, points_reward=75, is_active=True
        )
        cls.inactive_challenge = DailyChallenge.objects.create(
            title="Old Inactive Challenge", description="This challenge is no longer active.",
            challenge_type="COMPLETE_N_LESSONS", target_value=5, points_reward=10, is_active=False
        )

# #############################################################################
# SECTION: Test Classes
# #############################################################################

class SanityCheckTests(TrackerBaseTestCase):
    def test_user_creation_and_profile(self):
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(UserProfile.objects.count(), 2)
        self.assertEqual(self.user1.username, "user1")
        self.assertIsNotNone(self.user1.profile)
        self.assertEqual(self.user1_profile.user, self.user1)
        self.assertEqual(self.user2.email, "user2@example.com")

    def test_sections_and_lessons_setup(self):
        self.assertEqual(Section.objects.count(), 3)
        self.assertEqual(Lesson.objects.count(), 9)
        self.assertEqual(self.section_html.lessons.count(), 3)
        self.assertEqual(self.project_html_1.lesson_type, 'Project')
        self.assertEqual(self.lesson_js_2.points, 25)
        self.assertEqual(self.all_lessons.count(), 9)
        self.assertEqual(self.all_projects.count(), 3)

    def test_achievements_setup(self):
        self.assertEqual(Achievement.objects.count(), len(ACTUAL_ACHIEVEMENT_SLUGS))
        first_lesson_achievement = self.achievements_map.get('first-lesson-completed')
        self.assertIsNotNone(first_lesson_achievement)
        self.assertEqual(first_lesson_achievement.title, 'First Lesson!')
        self.assertEqual(first_lesson_achievement.points_reward, 10)

    def test_daily_challenges_setup(self):
        self.assertEqual(DailyChallenge.objects.count(), 4)
        active_challenges = DailyChallenge.objects.filter(is_active=True)
        self.assertEqual(active_challenges.count(), 3)
        self.assertEqual(self.challenge_lessons.target_value, 2)
        self.assertEqual(self.challenge_points.challenge_type, "EARN_N_POINTS")
        self.assertFalse(self.inactive_challenge.is_active)


class TestUserAccountManagement(TrackerBaseTestCase):
    def setUp(self):
        self.client = Client()
        # Placeholder URLs - replace with reverse() once urls.py is available.
        self.signup_url = '/accounts/signup/'
        self.login_url = '/accounts/login/'
        self.logout_url = '/accounts/logout/'
        self.password_change_url = '/accounts/password/change/' # Matches Django's default name 'password_change'
        self.password_change_done_url = '/accounts/password/change/done/' # Matches Django's default name 'password_change_done'
        self.email_change_url = '/accounts/email/change/' # Custom URL, assuming
        self.delete_account_url = '/accounts/delete/' # Custom URL, assuming
        self.user_settings_url = '/accounts/settings/' # Custom URL, assuming

    def test_signup_success(self):
        initial_user_count = User.objects.count()
        initial_profile_count = UserProfile.objects.count()
        form_data = {
            'username': 'newuser', 'email': 'newuser@example.com',
            'password': 'newpassword123', 'password2': 'newpassword123',
            'first_name': 'New', 'last_name': 'User',
        }
        response = self.client.post(self.signup_url, form_data)
        self.assertEqual(response.status_code, 302, f"Expected redirect, got {response.status_code}. Content: {response.content.decode()}")
        # self.assertRedirects(response, self.login_url) # TODO: Update with actual redirect target

        self.assertEqual(User.objects.count(), initial_user_count + 1)
        self.assertEqual(UserProfile.objects.count(), initial_profile_count + 1)
        created_user = User.objects.get(username='newuser')
        self.assertEqual(created_user.email, 'newuser@example.com')
        self.assertEqual(created_user.first_name, 'New')
        self.assertEqual(created_user.last_name, 'User')
        self.assertTrue(created_user.check_password('newpassword123'))
        self.assertTrue(UserProfile.objects.filter(user=created_user).exists())
        self.assertEqual(UserProfile.objects.get(user=created_user).total_points, 0)

    def test_signup_duplicate_username(self):
        initial_user_count = User.objects.count()
        form_data = {'username': self.user1.username, 'email': 'another@example.com', 'password': 'password123', 'password2': 'password123'}
        response = self.client.post(self.signup_url, form_data)
        self.assertEqual(User.objects.count(), initial_user_count)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "username already exists", msg_prefix="Response should contain username exists error")

    def test_signup_duplicate_email(self):
        initial_user_count = User.objects.count()
        form_data = {'username': 'unique_user', 'email': self.user1.email, 'password': 'password123', 'password2': 'password123'}
        response = self.client.post(self.signup_url, form_data)
        self.assertEqual(User.objects.count(), initial_user_count)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "email already exists", msg_prefix="Response should contain email exists error")

    def test_signup_invalid_email_format(self):
        initial_user_count = User.objects.count()
        form_data = {'username': 'newuser_invalid_email', 'email': 'not-an-email', 'password': 'password123', 'password2': 'password123'}
        response = self.client.post(self.signup_url, form_data)
        self.assertEqual(User.objects.count(), initial_user_count)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a valid email address", msg_prefix="Response should contain invalid email error")

    def test_signup_password_mismatch(self):
        initial_user_count = User.objects.count()
        form_data = {'username': 'newuser_pw_mismatch', 'email': 'mismatch@example.com', 'password': 'password123', 'password2': 'password456'}
        response = self.client.post(self.signup_url, form_data)
        self.assertEqual(User.objects.count(), initial_user_count)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "passwords didn&#39;t match", msg_prefix="Response should contain password mismatch error") # Django's default error escaping

    def test_login_success(self):
        client = Client() # Use a fresh client for login tests
        login_data = {'username': self.user1.username, 'password': 'password123'}
        response = client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, 302) # Expect redirect
        # self.assertRedirects(response, '/dashboard/') # TODO: Update with actual redirect target
        self.assertIn('_auth_user_id', client.session)
        self.assertEqual(client.session['_auth_user_id'], str(self.user1.id))

    def test_login_failure_wrong_password(self):
        client = Client()
        login_data = {'username': self.user1.username, 'password': 'wrongpassword'}
        response = client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', client.session)
        self.assertContains(response, "Please enter a correct username and password.")

    def test_login_failure_nonexistent_user(self):
        client = Client()
        login_data = {'username': 'nonexistentuser', 'password': 'anypassword'}
        response = client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', client.session)
        self.assertContains(response, "Please enter a correct username and password.")

    def test_logout_success(self):
        self.client.login(username=self.user1.username, password='password123')
        self.assertIn('_auth_user_id', self.client.session)
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302) # Expect redirect
        # self.assertRedirects(response, self.login_url) # TODO: Update with actual redirect target
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_password_change_requires_login(self):
        response = self.client.get(self.password_change_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.login_url in response.url)

    def test_password_change_success(self):
        self.client.login(username=self.user1.username, password='password123')
        form_data = {'old_password': 'password123', 'new_password1': 'newsecurepassword', 'new_password2': 'newsecurepassword'}
        response = self.client.post(self.password_change_url, form_data)
        self.assertEqual(response.status_code, 302, f"Expected redirect to {self.password_change_done_url}, got {response.status_code}")
        self.assertRedirects(response, self.password_change_done_url)
        self.user1.refresh_from_db()
        self.assertFalse(self.user1.check_password('password123'))
        self.assertTrue(self.user1.check_password('newsecurepassword'))
        
        new_client = Client()
        self.assertTrue(new_client.login(username=self.user1.username, password='newsecurepassword'))

    def test_password_change_wrong_old_password(self):
        self.client.login(username=self.user1.username, password='password123')
        form_data = {'old_password': 'wrongoldpassword', 'new_password1': 'newpassword', 'new_password2': 'newpassword'}
        response = self.client.post(self.password_change_url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your old password was entered incorrectly.")
        self.user1.refresh_from_db()
        self.assertTrue(self.user1.check_password('password123'))

    def test_email_change_requires_login(self):
        response_get = self.client.get(self.email_change_url)
        self.assertEqual(response_get.status_code, 302)
        self.assertTrue(self.login_url in response_get.url)
        response_post = self.client.post(self.email_change_url, {'email': 'new@example.com'})
        self.assertEqual(response_post.status_code, 302)
        self.assertTrue(self.login_url in response_post.url)

    def test_email_change_success(self):
        self.client.login(username=self.user1.username, password='password123')
        new_email = 'updated_user1@example.com'
        response = self.client.post(self.email_change_url, {'email': new_email})
        self.assertEqual(response.status_code, 302, f"Expected redirect, got {response.status_code}. Content: {response.content.decode()}")
        # self.assertRedirects(response, self.user_settings_url) # TODO: Update with actual redirect target
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.email, new_email)

    def test_email_change_duplicate_email(self):
        self.client.login(username=self.user1.username, password='password123')
        response = self.client.post(self.email_change_url, {'email': self.user2.email})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "email address is already in use")
        self.user1.refresh_from_db()
        self.assertNotEqual(self.user1.email, self.user2.email)

    def test_email_change_invalid_format(self):
        self.client.login(username=self.user1.username, password='password123')
        original_email = self.user1.email
        response = self.client.post(self.email_change_url, {'email': 'invalid-email-format'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a valid email address")
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.email, original_email)

    def test_delete_account_requires_login(self):
        response_get = self.client.get(self.delete_account_url)
        self.assertEqual(response_get.status_code, 302)
        self.assertTrue(self.login_url in response_get.url)
        response_post = self.client.post(self.delete_account_url)
        self.assertEqual(response_post.status_code, 302)
        self.assertTrue(self.login_url in response_post.url)

    def test_delete_account_success(self):
        user_to_delete, profile_to_delete = self.create_user("todelete", "password123", email="delete@example.com")
        user_id_to_delete, profile_id_to_delete = user_to_delete.id, profile_to_delete.id
        self.client.login(username="todelete", password="password123")
        
        Completion.objects.create(user=user_to_delete, lesson=self.lesson_html_1)
        UserStreak.objects.create(user=user_to_delete, current_streak=1)
        UserAchievement.objects.create(user=user_to_delete, achievement=self.achievements_map['first-lesson-completed'])
        UserDailyChallenge.objects.create(user=user_to_delete, challenge=self.challenge_lessons)

        response = self.client.post(self.delete_account_url)
        self.assertEqual(response.status_code, 302)
        # self.assertRedirects(response, reverse('home_url_name')) # TODO: Update with actual redirect target

        self.assertFalse(User.objects.filter(id=user_id_to_delete).exists())
        self.assertFalse(UserProfile.objects.filter(id=profile_id_to_delete).exists())
        self.assertFalse(Completion.objects.filter(user_id=user_id_to_delete).exists())
        self.assertFalse(UserStreak.objects.filter(user_id=user_id_to_delete).exists())
        self.assertFalse(UserAchievement.objects.filter(user_id=user_id_to_delete).exists())
        self.assertFalse(UserDailyChallenge.objects.filter(user_id=user_id_to_delete).exists())
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_user_settings_view_authenticated(self):
        self.client.login(username=self.user1.username, password='password123')
        response = self.client.get(self.user_settings_url)
        self.assertEqual(response.status_code, 200)
        # self.assertContains(response, "User Settings") # Example content check

    def test_user_settings_view_unauthenticated(self):
        response = self.client.get(self.user_settings_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.login_url in response.url)


class TestTrackingFunctionality(TrackerBaseTestCase):
    def setUp(self):
        self.client = Client()
        self.user1.refresh_from_db()
        self.user1_profile.refresh_from_db()
        self.lesson1 = self.lesson_html_1
        self.lesson2 = self.lesson_html_2
        self.project1 = self.project_html_1
        # Placeholder URLs
        self.mark_complete_url_template = '/complete/{lesson_id}/'
        self.unmark_complete_url_template = '/uncomplete/{lesson_id}/'
        self.reset_progress_url = '/settings/reset/'
        self.login_url = '/accounts/login/'

    def test_mark_lesson_complete_success(self):
        self.client.login(username=self.user1.username, password='password123')
        initial_points = self.user1_profile.total_points
        response = self.client.post(self.mark_complete_url_template.format(lesson_id=self.lesson1.id))
        self.assertEqual(response.status_code, 302) # Expect redirect
        self.assertTrue(Completion.objects.filter(user=self.user1, lesson=self.lesson1).exists())
        self.user1_profile.refresh_from_db()
        self.assertEqual(self.user1_profile.total_points, initial_points + self.lesson1.points)

    def test_mark_lesson_complete_already_completed(self):
        self.client.login(username=self.user1.username, password='password123')
        Completion.objects.create(user=self.user1, lesson=self.lesson1)
        self.user1_profile.total_points += self.lesson1.points
        self.user1_profile.save()
        initial_points = self.user1_profile.total_points
        initial_completion_count = Completion.objects.filter(user=self.user1, lesson=self.lesson1).count()

        response = self.client.post(self.mark_complete_url_template.format(lesson_id=self.lesson1.id))
        self.assertEqual(response.status_code, 302) # Expect redirect (even if no change)
        self.user1_profile.refresh_from_db()
        self.assertEqual(Completion.objects.filter(user=self.user1, lesson=self.lesson1).count(), initial_completion_count)
        self.assertEqual(self.user1_profile.total_points, initial_points)

    def test_mark_lesson_complete_non_existent_lesson(self):
        self.client.login(username=self.user1.username, password='password123')
        response = self.client.post(self.mark_complete_url_template.format(lesson_id=999))
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Completion.objects.filter(user=self.user1, lesson_id=999).exists())

    def test_mark_lesson_complete_unauthenticated(self):
        response = self.client.post(self.mark_complete_url_template.format(lesson_id=self.lesson1.id))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.login_url in response.url)
        self.assertFalse(Completion.objects.filter(lesson=self.lesson1).exists())

    def test_unmark_lesson_complete_success(self):
        self.client.login(username=self.user1.username, password='password123')
        Completion.objects.create(user=self.user1, lesson=self.lesson1)
        self.user1_profile.total_points += self.lesson1.points
        self.user1_profile.save()
        self.user1_profile.refresh_from_db()
        initial_points = self.user1_profile.total_points

        response = self.client.post(self.unmark_complete_url_template.format(lesson_id=self.lesson1.id))
        self.assertEqual(response.status_code, 302) # Expect redirect
        self.assertFalse(Completion.objects.filter(user=self.user1, lesson=self.lesson1).exists())
        self.user1_profile.refresh_from_db()
        self.assertEqual(self.user1_profile.total_points, initial_points - self.lesson1.points)

    def test_unmark_lesson_not_yet_completed(self):
        self.client.login(username=self.user1.username, password='password123')
        initial_points = self.user1_profile.total_points
        response = self.client.post(self.unmark_complete_url_template.format(lesson_id=self.lesson2.id))
        self.assertEqual(response.status_code, 302) # Or 404, depending on view logic
        self.assertFalse(Completion.objects.filter(user=self.user1, lesson=self.lesson2).exists())
        self.user1_profile.refresh_from_db()
        self.assertEqual(self.user1_profile.total_points, initial_points)

    def test_unmark_lesson_complete_unauthenticated(self):
        Completion.objects.create(user=self.user1, lesson=self.lesson1) # Setup
        response = self.client.post(self.unmark_complete_url_template.format(lesson_id=self.lesson1.id))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.login_url in response.url)
        self.assertTrue(Completion.objects.filter(user=self.user1, lesson=self.lesson1).exists())

    def test_reset_progress_success(self):
        self.client.login(username=self.user1.username, password='password123')
        Completion.objects.create(user=self.user1, lesson=self.lesson1)
        self.user1_profile.total_points = self.lesson1.points
        self.user1_profile.save()
        UserAchievement.objects.create(user=self.user1, achievement=self.achievements_map['first-lesson-completed'])
        UserStreak.objects.create(user=self.user1, current_streak=5)

        response = self.client.post(self.reset_progress_url)
        self.assertEqual(response.status_code, 302) # Expect redirect
        self.user1_profile.refresh_from_db()
        self.assertFalse(Completion.objects.filter(user=self.user1).exists())
        self.assertEqual(self.user1_profile.total_points, 0)
        self.assertFalse(UserAchievement.objects.filter(user=self.user1).exists())
        self.assertFalse(UserStreak.objects.filter(user=self.user1).exists())

    def test_reset_progress_unauthenticated(self):
        Completion.objects.create(user=self.user1, lesson=self.lesson1) # Setup
        response = self.client.post(self.reset_progress_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.login_url in response.url)
        self.assertTrue(Completion.objects.filter(user=self.user1).exists())


class TestAchievementsLogic(TrackerBaseTestCase):
    def setUp(self):
        self.client = Client()
        self.user1.refresh_from_db()
        self.user1_profile.refresh_from_db()
        self.user2.refresh_from_db()
        self.user2_profile.refresh_from_db()

        # Dynamically ensure specific achievements for testing exist
        # These slugs should ideally match keys in ACTUAL_ACHIEVEMENT_SLUGS
        extra_achievement_slugs = {
            'TEN_DAY_STREAK': {'title': 'Ten Day Streak', 'description': '10 day streak!', 'points_reward': 50},
            'THIRTY_DAY_STREAK': {'title': 'Thirty Day Streak', 'description': '30 day streak!', 'points_reward': 100},
            'COURSE_COMPLETED': {'title': 'Course Completed!', 'description': 'You finished all lessons!', 'points_reward': 200},
            'PERFECT_SECTION': {'title': 'Perfect Section!', 'description': 'You finished a whole section!', 'points_reward': 75},
        }
        for slug, details in extra_achievement_slugs.items():
            if slug not in ACTUAL_ACHIEVEMENT_SLUGS: # Add to global dict if not present from "import"
                ACTUAL_ACHIEVEMENT_SLUGS[slug] = details
            if not Achievement.objects.filter(achievement_slug=slug).exists():
                self.achievements_map[slug] = Achievement.objects.create(achievement_slug=slug, **details)
            else: # Ensure it's in self.achievements_map if it existed from base setUpTestData
                if slug not in self.achievements_map:
                     self.achievements_map[slug] = Achievement.objects.get(achievement_slug=slug)


        self.first_lesson_achievement_obj = self.achievements_map['first-lesson-completed']
        self.first_project_achievement_obj = self.achievements_map['first-project-completed']
        self.points_100_achievement_obj = self.achievements_map['points-milestone-100']
        self.points_500_achievement_obj = self.achievements_map['points-milestone-500']
        self.html_section_achievement_obj = self.achievements_map.get('html-beginner')
        self.streak_3_days_obj = self.achievements_map['streak-3-days']
        self.ten_day_streak_obj = self.achievements_map['TEN_DAY_STREAK']
        self.thirty_day_streak_obj = self.achievements_map['THIRTY_DAY_STREAK']
        self.course_completed_obj = self.achievements_map['COURSE_COMPLETED']
        self.perfect_section_obj = self.achievements_map['PERFECT_SECTION']
        
        self.lesson1 = self.lesson_html_1
        self.project1 = self.project_html_1
        self.html_section = self.section_html
        self.all_lessons_list = list(Lesson.objects.all()) # Ensure this captures all lessons

    def _get_achievement_details(self, slug_key):
        details = ACTUAL_ACHIEVEMENT_SLUGS.get(slug_key)
        if details and 'slug' not in details: details['slug'] = slug_key
        return details

    def _complete_lesson(self, user, lesson, profile):
        completion, created = Completion.objects.get_or_create(user=user, lesson=lesson)
        if created:
            profile.total_points += lesson.points
            profile.save()
        return completion

    def test_award_new_achievement(self):
        achievement_details = self._get_achievement_details('first-lesson-completed')
        initial_points = self.user1_profile.total_points
        self.assertFalse(UserAchievement.objects.filter(user=self.user1, achievement=self.first_lesson_achievement_obj).exists())
        
        awarded_obj, created = award_achievement(self.user1, achievement_details, profile=self.user1_profile)
        
        self.assertTrue(created)
        self.assertIsNotNone(awarded_obj)
        self.assertEqual(awarded_obj.achievement, self.first_lesson_achievement_obj)
        self.assertTrue(UserAchievement.objects.filter(user=self.user1, achievement=self.first_lesson_achievement_obj).exists())
        self.user1_profile.refresh_from_db()
        self.assertEqual(self.user1_profile.total_points, initial_points + self.first_lesson_achievement_obj.points_reward)

    def test_award_already_awarded_achievement(self):
        achievement_details = self._get_achievement_details('first-lesson-completed')
        award_achievement(self.user1, achievement_details, profile=self.user1_profile) # First award
        self.user1_profile.refresh_from_db()
        points_after_first = self.user1_profile.total_points
        count_after_first = UserAchievement.objects.filter(user=self.user1, achievement=self.first_lesson_achievement_obj).count()

        awarded_obj, created = award_achievement(self.user1, achievement_details, profile=self.user1_profile) # Second attempt
        
        self.assertFalse(created)
        self.user1_profile.refresh_from_db()
        self.assertEqual(UserAchievement.objects.count(), count_after_first)
        self.assertEqual(self.user1_profile.total_points, points_after_first)

    def test_award_non_existent_achievement_slug(self):
        initial_points = self.user1_profile.total_points
        non_existent_details = {'slug': 'NON_EXISTENT_SLUG', 'title': 'Fake', 'description': 'Fake', 'points_reward': 100}
        awarded_obj, created = award_achievement(self.user1, non_existent_details, profile=self.user1_profile)
        self.assertFalse(created)
        self.assertIsNone(awarded_obj)
        self.user1_profile.refresh_from_db()
        self.assertEqual(self.user1_profile.total_points, initial_points)

    @patch('django.contrib.messages')
    def test_award_achievement_with_request_generates_message(self, mock_messages_framework):
        achievement_details = self._get_achievement_details('first-lesson-completed')
        UserAchievement.objects.filter(user=self.user1, achievement=self.first_lesson_achievement_obj).delete() # Ensure not awarded
        self.user1_profile.total_points -= self.first_lesson_achievement_obj.points_reward # Adjust points
        self.user1_profile.save()

        mock_request = MockRequest()
        mock_request.user = self.user1
        
        award_achievement(self.user1, achievement_details, request=mock_request, profile=self.user1_profile)
        
        mock_request.messages.success.assert_called_once()
        args, _ = mock_request.messages.success.call_args
        self.assertEqual(args[0], mock_request)
        self.assertIn(f"Achievement Unlocked: {self.first_lesson_achievement_obj.title}", args[1])

    def test_check_first_lesson_achievement(self):
        completion_instance = self._complete_lesson(self.user2, self.lesson1, self.user2_profile)
        check_and_award_achievements(self.user2, completion_instance=completion_instance)
        self.assertTrue(UserAchievement.objects.filter(user=self.user2, achievement=self.first_lesson_achievement_obj).exists())
        self.user2_profile.refresh_from_db()
        self.assertEqual(self.user2_profile.total_points, self.lesson1.points + self.first_lesson_achievement_obj.points_reward)

    def test_check_first_project_achievement(self):
        completion_instance = self._complete_lesson(self.user2, self.project1, self.user2_profile)
        check_and_award_achievements(self.user2, completion_instance=completion_instance)
        self.assertTrue(UserAchievement.objects.filter(user=self.user2, achievement=self.first_project_achievement_obj).exists())

    def test_check_section_completion_achievements(self):
        if not self.html_section_achievement_obj: self.skipTest("HTML beginner achievement not configured for this test run.")
        last_completion = None
        for lesson in Lesson.objects.filter(section=self.html_section):
            last_completion = self._complete_lesson(self.user2, lesson, self.user2_profile)
        if last_completion: check_and_award_achievements(self.user2, completion_instance=last_completion)
        else: check_and_award_achievements(self.user2) # General check if no lessons
        self.assertTrue(UserAchievement.objects.filter(user=self.user2, achievement=self.html_section_achievement_obj).exists())

    def test_check_perfect_section_achievement(self):
        last_completion = None
        for lesson in Lesson.objects.filter(section=self.html_section):
            last_completion = self._complete_lesson(self.user2, lesson, self.user2_profile)
        if last_completion: check_and_award_achievements(self.user2, completion_instance=last_completion)
        else: check_and_award_achievements(self.user2)
        self.assertTrue(UserAchievement.objects.filter(user=self.user2, achievement=self.perfect_section_obj).exists())

    def test_check_streak_achievements_ten_day(self):
        UserStreak.objects.update_or_create(user=self.user2, defaults={'current_streak': 10, 'last_activity_date': datetime.date.today()})
        check_and_award_achievements(self.user2)
        self.assertTrue(UserAchievement.objects.filter(user=self.user2, achievement=self.ten_day_streak_obj).exists())

    def test_check_streak_achievements_thirty_day(self):
        UserStreak.objects.update_or_create(user=self.user2, defaults={'current_streak': 30, 'last_activity_date': datetime.date.today()})
        check_and_award_achievements(self.user2)
        self.assertTrue(UserAchievement.objects.filter(user=self.user2, achievement=self.thirty_day_streak_obj).exists())

    def test_check_point_milestone_100_points(self):
        self.user2_profile.total_points = 100
        self.user2_profile.save()
        check_and_award_achievements(self.user2)
        self.assertTrue(UserAchievement.objects.filter(user=self.user2, achievement=self.points_100_achievement_obj).exists())
        self.user2_profile.refresh_from_db()
        self.assertEqual(self.user2_profile.total_points, 100 + self.points_100_achievement_obj.points_reward)

    def test_check_point_milestone_500_points(self):
        self.user2_profile.total_points = 500
        self.user2_profile.save()
        check_and_award_achievements(self.user2)
        self.assertTrue(UserAchievement.objects.filter(user=self.user2, achievement=self.points_500_achievement_obj).exists())

    def test_check_course_completed_achievement(self):
        last_completion = None
        for lesson in self.all_lessons_list: # self.all_lessons_list from setUp
            last_completion = self._complete_lesson(self.user2, lesson, self.user2_profile)
        if last_completion: check_and_award_achievements(self.user2, completion_instance=last_completion)
        else: check_and_award_achievements(self.user2)
        self.assertTrue(UserAchievement.objects.filter(user=self.user2, achievement=self.course_completed_obj).exists())

    def test_check_achievements_idempotency(self):
        completion1 = self._complete_lesson(self.user2, self.lesson1, self.user2_profile)
        check_and_award_achievements(self.user2, completion_instance=completion1) # First time
        self.user2_profile.refresh_from_db()
        points_after_first = self.user2_profile.total_points
        count_after_first = UserAchievement.objects.filter(user=self.user2, achievement=self.first_lesson_achievement_obj).count()
        
        check_and_award_achievements(self.user2, completion_instance=completion1) # Second time
        self.user2_profile.refresh_from_db()
        self.assertEqual(UserAchievement.objects.count(), count_after_first)
        self.assertEqual(self.user2_profile.total_points, points_after_first)


class TestDailyChallengesLogic(TrackerBaseTestCase):
    def setUp(self):
        self.client = Client()
        self.user1.refresh_from_db()
        self.user1_profile.refresh_from_db()
        self.user2.refresh_from_db()
        self.user2_profile.refresh_from_db()
        self.active_challenge_lessons = self.challenge_lessons
        self.active_challenge_points = self.challenge_points
        self.active_challenge_project = self.challenge_project
        self.all_active_challenges = DailyChallenge.objects.filter(is_active=True)
        self.lesson1 = self.lesson_html_1
        self.lesson2 = self.lesson_html_2
        self.project1 = self.project_html_1
        self.mock_request = MockRequest()

    def _assign_specific_challenge(self, user, challenge_obj, profile=None):
        today = timezone.now().date()
        initial_points = None
        if challenge_obj.challenge_type == 'EARN_N_POINTS':
            if profile is None: profile, _ = UserProfile.objects.get_or_create(user=user)
            initial_points = profile.total_points
        udc, _ = UserDailyChallenge.objects.update_or_create(
            user=user, assigned_date=today,
            defaults={'challenge': challenge_obj, 'current_progress': 0, 'completed_date': None, 'initial_points_at_assignment': initial_points}
        )
        return udc

    def test_assign_new_challenge_to_new_user(self):
        udc = assign_new_daily_challenge(self.user2)
        self.assertIsNotNone(udc)
        self.assertIn(udc.challenge, self.all_active_challenges)
        self.assertEqual(udc.assigned_date, timezone.now().date())

    def test_assign_new_challenge_reassigns_if_old(self):
        UserDailyChallenge.objects.create(user=self.user1, challenge=self.active_challenge_lessons, assigned_date=timezone.now().date() - timezone.timedelta(days=1))
        udc = assign_new_daily_challenge(self.user1)
        self.assertEqual(udc.assigned_date, timezone.now().date())
        self.assertEqual(udc.current_progress, 0)

    def test_assign_challenge_earn_n_points_sets_initial_points(self):
        original_statuses = {c.id: c.is_active for c in DailyChallenge.objects.all()}
        DailyChallenge.objects.exclude(id=self.active_challenge_points.id).update(is_active=False)
        self.active_challenge_points.is_active = True; self.active_challenge_points.save()
        
        self.user1_profile.total_points = 50; self.user1_profile.save()
        udc = assign_new_daily_challenge(self.user1)
        self.assertEqual(udc.challenge, self.active_challenge_points)
        self.assertEqual(udc.initial_points_at_assignment, 50)

        for cid, status in original_statuses.items(): DailyChallenge.objects.filter(id=cid).update(is_active=status) # Restore

    def test_assign_challenge_no_active_challenges(self):
        original_statuses = {c.id: c.is_active for c in DailyChallenge.objects.all()}
        DailyChallenge.objects.all().update(is_active=False)
        udc = assign_new_daily_challenge(self.user1)
        self.assertIsNotNone(udc)
        self.assertIsNone(udc.challenge)
        for cid, status in original_statuses.items(): DailyChallenge.objects.filter(id=cid).update(is_active=status) # Restore

    def test_assign_challenge_idempotent_for_today(self):
        udc1 = assign_new_daily_challenge(self.user1)
        udc2 = assign_new_daily_challenge(self.user1)
        self.assertEqual(udc1.id, udc2.id)
        self.assertEqual(udc1.challenge, udc2.challenge)

    def test_update_progress_complete_lessons(self):
        udc = self._assign_specific_challenge(self.user2, self.active_challenge_lessons)
        Completion.objects.create(user=self.user2, lesson=self.lesson1)
        update_daily_challenge_progress(self.user2, completed_lesson_info={'lesson_id': self.lesson1.id, 'lesson_type': self.lesson1.lesson_type})
        udc.refresh_from_db(); self.assertEqual(udc.current_progress, 1)
        Completion.objects.create(user=self.user2, lesson=self.lesson2)
        update_daily_challenge_progress(self.user2, completed_lesson_info={'lesson_id': self.lesson2.id, 'lesson_type': self.lesson2.lesson_type})
        udc.refresh_from_db(); self.assertEqual(udc.current_progress, 2); self.assertIsNotNone(udc.completed_date)

    def test_update_progress_earn_points(self):
        self.user2_profile.total_points = 10; self.user2_profile.save()
        udc = self._assign_specific_challenge(self.user2, self.active_challenge_points, profile=self.user2_profile)
        self.assertEqual(udc.initial_points_at_assignment, 10)
        self.user2_profile.total_points += 30; self.user2_profile.save() # Earn 30 points
        update_daily_challenge_progress(self.user2, points_earned_in_action=30)
        udc.refresh_from_db(); self.assertEqual(udc.current_progress, 30) # 40 total - 10 initial = 30 progress
        self.user2_profile.total_points += 30; self.user2_profile.save() # Earn another 30 points
        update_daily_challenge_progress(self.user2, points_earned_in_action=30)
        udc.refresh_from_db(); self.assertEqual(udc.current_progress, 60); self.assertIsNotNone(udc.completed_date) # 70 total - 10 initial = 60 progress

    def test_update_progress_complete_project(self):
        udc = self._assign_specific_challenge(self.user2, self.active_challenge_project)
        Completion.objects.create(user=self.user2, lesson=self.project1)
        update_daily_challenge_progress(self.user2, completed_lesson_info={'lesson_id': self.project1.id, 'lesson_type': self.project1.lesson_type})
        udc.refresh_from_db(); self.assertEqual(udc.current_progress, 1); self.assertIsNotNone(udc.completed_date)

    def test_challenge_completion_awards_points_and_sets_date(self):
        challenge = DailyChallenge.objects.create(title="Test Comp 1 L", challenge_type="COMPLETE_N_LESSONS", target_value=1, points_reward=15, is_active=True)
        udc = self._assign_specific_challenge(self.user2, challenge, self.user2_profile)
        initial_points = self.user2_profile.total_points
        Completion.objects.create(user=self.user2, lesson=self.lesson1)
        update_daily_challenge_progress(self.user2, completed_lesson_info={'lesson_id': self.lesson1.id, 'lesson_type': self.lesson1.lesson_type})
        udc.refresh_from_db(); self.user2_profile.refresh_from_db()
        self.assertEqual(udc.completed_date, timezone.now().date())
        self.assertEqual(self.user2_profile.total_points, initial_points + challenge.points_reward)

    def test_challenge_completion_points_awarded_only_once(self):
        udc = self._assign_specific_challenge(self.user2, self.active_challenge_lessons, self.user2_profile) # Target 2 lessons
        initial_points = self.user2_profile.total_points
        # Complete 2 lessons to trigger completion
        Completion.objects.create(user=self.user2, lesson=self.lesson1); update_daily_challenge_progress(self.user2, completed_lesson_info={'lesson_id': self.lesson1.id})
        Completion.objects.create(user=self.user2, lesson=self.lesson2); update_daily_challenge_progress(self.user2, completed_lesson_info={'lesson_id': self.lesson2.id})
        self.user2_profile.refresh_from_db(); points_after_completion = self.user2_profile.total_points
        self.assertEqual(points_after_completion, initial_points + self.active_challenge_lessons.points_reward)
        # Complete a 3rd lesson
        lesson3 = Lesson.objects.create(section=self.section_js, title="JS Lesson 3", lesson_type="Lesson", points=30)
        Completion.objects.create(user=self.user2, lesson=lesson3); update_daily_challenge_progress(self.user2, completed_lesson_info={'lesson_id': lesson3.id})
        self.user2_profile.refresh_from_db()
        self.assertEqual(self.user2_profile.total_points, points_after_completion) # Points should not change further from this challenge

    @patch('django.contrib.messages')
    def test_challenge_completion_with_request_generates_message(self, mock_messages_framework):
        challenge = DailyChallenge.objects.create(title="Msg Challenge", challenge_type="COMPLETE_N_LESSONS", target_value=1, points_reward=5, is_active=True)
        self._assign_specific_challenge(self.user2, challenge, self.user2_profile)
        self.mock_request.user = self.user2
        Completion.objects.create(user=self.user2, lesson=self.lesson1)
        update_daily_challenge_progress(self.user2, completed_lesson_info={'lesson_id': self.lesson1.id}, request=self.mock_request)
        self.mock_request.messages.success.assert_called_once()
        args, _ = self.mock_request.messages.success.call_args
        self.assertIn(f"Daily Challenge Completed: {challenge.title}", args[1])


class TestViews(TrackerBaseTestCase):
    def setUp(self):
        self.client = Client()
        self.user1.refresh_from_db(); self.user1_profile.refresh_from_db()
        self.user2.refresh_from_db(); self.user2_profile.refresh_from_db()
        self.dashboard_url = '/dashboard/' # TODO: Replace with reverse(...)
        self.leaderboard_url = '/leaderboard/' # TODO: Replace with reverse(...)
        self.achievements_page_url = '/achievements/' # TODO: Replace with reverse(...)
        self.login_url = '/accounts/login/' # TODO: Replace with reverse('login') or Django's settings.LOGIN_URL
        self.lesson1 = self.lesson_html_1
        self.first_lesson_achievement_obj = self.achievements_map['first-lesson-completed']
        self.points_100_achievement_obj = self.achievements_map['points-milestone-100']
        self.challenge_lessons_obj = self.challenge_lessons

    def test_dashboard_view_authenticated(self):
        self.client.login(username=self.user1.username, password='password123')
        Completion.objects.create(user=self.user1, lesson=self.lesson1)
        self.user1_profile.total_points += self.lesson1.points; self.user1_profile.save()
        assigned_challenge, _ = UserDailyChallenge.objects.update_or_create(
            user=self.user1, assigned_date=timezone.now().date(),
            defaults={'challenge': self.challenge_lessons_obj, 'current_progress': 0}
        )
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user1.username)
        self.assertContains(response, str(self.user1_profile.total_points))
        self.assertContains(response, self.lesson1.title)
        self.assertContains(response, assigned_challenge.challenge.title)

    def test_dashboard_view_unauthenticated(self):
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{self.login_url}?next={self.dashboard_url}")

    def test_leaderboard_view_loads(self):
        response = self.client.get(self.leaderboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Leaderboard")

    def test_leaderboard_displays_users_sorted_by_points(self):
        user3, user3_profile = self.create_user("user3", "pw3", email="u3@e.com")
        self.user1_profile.total_points = 100; self.user1_profile.save()
        self.user2_profile.total_points = 50; self.user2_profile.save()
        user3_profile.total_points = 150; user3_profile.save()
        response = self.client.get(self.leaderboard_url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertContains(response, user3.username)
        self.assertContains(response, self.user1.username)
        self.assertContains(response, self.user2.username)
        pos_user3 = content.find(user3.username)
        pos_user1 = content.find(self.user1.username)
        pos_user2 = content.find(self.user2.username)
        self.assertTrue(0 <= pos_user3 < pos_user1 < pos_user2, "Leaderboard order incorrect.")

    def test_achievements_page_view_authenticated(self):
        self.client.login(username=self.user1.username, password='password123')
        first_lesson_details = ACTUAL_ACHIEVEMENT_SLUGS['first-lesson-completed']
        award_achievement(self.user1, first_lesson_details, profile=self.user1_profile) # Award one
        locked_achievement = self.points_100_achievement_obj # Assume this one is not awarded yet
        
        response = self.client.get(self.achievements_page_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.first_lesson_achievement_obj.title)
        # The following assertions are highly dependent on specific HTML structure
        # For example, if unlocked achievements have a class 'unlocked' or specific text
        # self.assertContains(response, f'<div class="achievement unlocked">...{self.first_lesson_achievement_obj.title}...</div>')
        self.assertContains(response, locked_achievement.title)
        # self.assertContains(response, f'<div class="achievement locked">...{locked_achievement.title}...</div>')


    def test_achievements_page_view_unauthenticated(self):
        response = self.client.get(self.achievements_page_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{self.login_url}?next={self.achievements_page_url}")

    def test_lesson_detail_view_unauthenticated(self): # Example for other views
        lesson_detail_url_template = '/lessons/{lesson_id}/' # TODO: Replace with reverse(...)
        lesson_url = lesson_detail_url_template.format(lesson_id=self.lesson1.id)
        response = self.client.get(lesson_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{self.login_url}?next={lesson_url}")
