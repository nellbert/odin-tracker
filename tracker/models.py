from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date, timedelta
from django.utils import timezone # For date/time operations
import random # For selecting random challenges
from django.db import transaction # Import transaction

# Import necessary for broadcasting
import asyncio
from asgiref.sync import async_to_sync

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    total_points = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.user.username} Profile ({self.total_points} points)'

# Signal to create or update UserProfile whenever a User instance is saved
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    instance.profile.save()

# Signal to broadcast stats update whenever a UserProfile is saved
@receiver(post_save, sender=UserProfile)
def broadcast_profile_update(sender, instance, **kwargs):
    # Import the function here, just before use
    from .consumers import broadcast_stats_update
    # Define the function to run on commit
    def do_broadcast():
        async_to_sync(broadcast_stats_update)()
    # Schedule the broadcast to run after the current transaction commits
    transaction.on_commit(do_broadcast)

class Section(models.Model):
    title = models.CharField(max_length=200)
    order = models.IntegerField(unique=True) # Ensure unique ordering

    class Meta:
        ordering = ['order'] # Default ordering

    def __str__(self):
        return self.title

class Lesson(models.Model):
    LESSON_TYPE_CHOICES = (
        ('Lesson', 'Lesson'),
        ('Project', 'Project'),
    )

    title = models.CharField(max_length=200)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='lessons')
    points_value = models.IntegerField(default=10)
    lesson_type = models.CharField(max_length=10, choices=LESSON_TYPE_CHOICES, default='Lesson')
    url = models.URLField(blank=True, null=True)
    order = models.IntegerField() # Order within the section

    class Meta:
        ordering = ['section__order', 'order'] # Order by section, then lesson order
        unique_together = ('section', 'order') # Ensure unique order within a section

    def __str__(self):
        return f'{self.section.title} - {self.title}'

class Completion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='completions')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='completions')
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'lesson') # Prevent duplicate completions
        ordering = ['-completed_at']

    def __str__(self):
        return f'{self.user.username} completed {self.lesson.title}'

class UserStreak(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='streak')
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - Current Streak: {self.current_streak}, Longest: {self.longest_streak}"

    def update_streak(self):
        """Updates the streak based on the current date and last_activity_date."""
        today = date.today()

        if self.last_activity_date == today:
            # Multiple activities on the same day don't break/increment streak further for that day
            return 

        if self.last_activity_date == (today - timedelta(days=1)):
            self.current_streak += 1
        else:
            # Streak broken or first activity
            self.current_streak = 1 
        
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        
        self.last_activity_date = today
        self.save()

# Signal to create UserStreak when UserProfile is created (which is when User is created)
@receiver(post_save, sender=UserProfile)
def create_user_streak(sender, instance, created, **kwargs):
    if created:
        UserStreak.objects.get_or_create(user=instance.user)

class Achievement(models.Model):
    title = models.CharField(max_length=150, unique=True)
    description = models.TextField()
    icon_class = models.CharField(max_length=100, blank=True, help_text="e.g., 'fas fa-trophy', Font Awesome class")
    points_reward = models.IntegerField(default=0, help_text="Extra points awarded when this achievement is unlocked.")
    # Criteria for unlocking - this can be simple for now, or more complex later
    # For example, a slug to identify the achievement in code for awarding logic
    achievement_slug = models.SlugField(unique=True, help_text="A unique slug for programmatic checking, e.g., 'completed_html_section'.")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']

class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='user_awards')
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement') # User can only earn an achievement once
        ordering = ['-awarded_at']

    def __str__(self):
        return f"{self.user.username} earned {self.achievement.title}"

# Note: The logic for awarding achievements will be implemented separately, likely in views or signals.

class DailyChallenge(models.Model):
    CHALLENGE_TYPES = (
        ('COMPLETE_N_LESSONS', 'Complete N Lessons'),
        ('EARN_N_POINTS', 'Earn N Points'),
        ('COMPLETE_PROJECT', 'Complete any Project'),
        # Add more types later, e.g., 'COMPLETE_LESSON_FROM_SECTION_X'
    )

    title = models.CharField(max_length=200)
    description_template = models.TextField(help_text="Template for challenge description, e.g., 'Complete {target_value} lessons today.'")
    challenge_type = models.CharField(max_length=50, choices=CHALLENGE_TYPES)
    # Target value for the challenge, e.g., if N_LESSONS, target_value could be 2 (meaning complete 2 lessons)
    target_value = models.IntegerField(default=1)
    points_reward = models.IntegerField(default=20, help_text="Bonus points for completing the daily challenge.")
    is_active = models.BooleanField(default=True, help_text="Whether this challenge type can be assigned.")
    # Cooldown in days (e.g., if a user gets this challenge, they can't get it again for X days)
    # For simplicity, we'll start without a cooldown specific to challenge type, but can be added.

    def __str__(self):
        return self.title

    def get_description(self):
        """Returns a formatted description using the target_value."""
        return self.description_template.format(target_value=self.target_value)

class UserDailyChallenge(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='daily_challenge_instance')
    challenge = models.ForeignKey(DailyChallenge, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_date = models.DateField(auto_now_add=True)
    completed_date = models.DateField(null=True, blank=True)
    current_progress = models.IntegerField(default=0)
    # Store the initial points of the user when the challenge was assigned for 'EARN_N_POINTS' type
    initial_points_at_assignment = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self):
        if self.challenge:
            return f"{self.user.username} - {self.challenge.title} ({self.assigned_date}) - Progress: {self.current_progress}/{self.challenge.target_value}"
        return f"{self.user.username} - No active challenge ({self.assigned_date})"

    @property
    def is_completed(self):
        return self.completed_date is not None

    @property
    def is_active_today(self):
        return self.assigned_date == timezone.now().date() and not self.is_completed

# Note: Logic for assigning and updating challenges will be in a separate module/functions. 