from django.contrib import admin
from .models import UserProfile, Section, Lesson, Completion, UserStreak, Achievement, UserAchievement, DailyChallenge, UserDailyChallenge
from django.utils import timezone
from datetime import timedelta

# Customize admin displays if desired, but basic registration is sufficient for now

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_points')

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')
    ordering = ('order',)

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'lesson_type', 'points_value', 'order')
    list_filter = ('section', 'lesson_type')
    ordering = ('section__order', 'order')

@admin.register(Completion)
class CompletionAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'completed_at')
    list_filter = ('user', 'lesson__section')
    ordering = ('-completed_at',)

@admin.register(UserStreak)
class UserStreakAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_streak', 'longest_streak', 'last_activity_date')
    readonly_fields = ('last_activity_date',)
    search_fields = ('user__username',)

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('title', 'achievement_slug', 'points_reward', 'icon_class')
    search_fields = ('title', 'achievement_slug')
    prepopulated_fields = {'achievement_slug': ('title',)}

@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'awarded_at')
    list_filter = ('achievement', 'user')
    search_fields = ('user__username', 'achievement__title')
    readonly_fields = ('awarded_at',)

@admin.register(DailyChallenge)
class DailyChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'challenge_type', 'target_value', 'points_reward', 'is_active')
    list_filter = ('challenge_type', 'is_active')
    search_fields = ('title', 'description_template')

@admin.register(UserDailyChallenge)
class UserDailyChallengeAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'assigned_date', 'completed_date', 'current_progress')
    list_filter = ('assigned_date', 'completed_date', 'challenge__challenge_type')
    search_fields = ('user__username', 'challenge__title')
    readonly_fields = ('assigned_date', 'completed_date', 'current_progress', 'initial_points_at_assignment')
    actions = ['reset_selected_challenges']

    def reset_selected_challenges(self, request, queryset):
        # Action to allow admin to reset a user's daily challenge (e.g., for testing or if it got stuck)
        # This effectively allows assigning a new one on next dashboard load if conditions met.
        updated_count = 0
        for udc in queryset:
            udc.challenge = None # Or set to a placeholder "no challenge" if you have one
            udc.completed_date = None
            udc.assigned_date = timezone.now().date() - timedelta(days=1) # Mark as old
            udc.current_progress = 0
            udc.initial_points_at_assignment = 0
            udc.save()
            updated_count +=1
        self.message_user(request, f"{updated_count} user daily challenges were reset, allowing new assignment.")
    reset_selected_challenges.short_description = "Reset selected user daily challenges" 