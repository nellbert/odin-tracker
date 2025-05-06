# tracker/achievements.py

from django.contrib import messages
from django.db import transaction
from django.utils import timezone # For date checks
from .models import User, Achievement, UserAchievement, UserProfile, Completion, Section, Lesson, UserStreak, UserDailyChallenge # Import UserDailyChallenge

def _award_achievement_if_not_earned(user, request, achievement_slug):
    """Awards an achievement if not already earned, adds points, and shows a message."""
    try:
        achievement = Achievement.objects.get(achievement_slug=achievement_slug)
        
        # Check if user already has this achievement
        if UserAchievement.objects.filter(user=user, achievement=achievement).exists():
            return False # Already earned

        # Use a transaction to ensure atomicity of awarding and point update
        with transaction.atomic():
            # Award the achievement
            UserAchievement.objects.create(user=user, achievement=achievement)
            
            # Update points if there's a reward
            if achievement.points_reward > 0:
                # Use select_for_update to prevent race conditions if points are updated elsewhere
                profile = UserProfile.objects.select_for_update().get(user=user)
                profile.total_points += achievement.points_reward
                profile.save()
            
            # Show message if request object is available
            if request:
                messages.success(request, 
                    f"🎉 Achievement Unlocked: {achievement.title}! (+{achievement.points_reward} points)")
            print(f"Awarded '{achievement.title}' to {user.username}") # Server log
            return True # Newly awarded

    except Achievement.DoesNotExist:
        print(f"ERROR: Attempted to award non-existent achievement slug: {achievement_slug}")
    except UserProfile.DoesNotExist:
        print(f"ERROR: UserProfile not found for {user.username} when awarding {achievement_slug}.")
    except Exception as e: # Catch other potential errors during transaction
        print(f"ERROR: Awarding achievement {achievement_slug} to {user.username}: {e}")
    
    return False # Not newly awarded or error occurred

def check_and_award_achievements(user, request=None, 
                                 # Context specific triggers:
                                 completion_instance=None, # Changed from completed_lesson
                                 profile=None, 
                                 streak=None, 
                                 daily_challenge_completed=False, 
                                 view_context=None 
                                 ):
    """Checks all relevant conditions and awards achievements based on context."""
    if not user or not user.is_authenticated:
        return

    # Fetch profile/streak if not provided or potentially stale
    current_profile = profile or UserProfile.objects.filter(user=user).first()
    current_streak = streak or UserStreak.objects.filter(user=user).first()

    if not current_profile:
        print(f"WARNING: No profile found for user {user.username} during achievement check.")
        return

    # --- Checks Triggered by Lesson Completion --- 
    if completion_instance:
        completed_lesson = completion_instance.lesson
        user_completion_count = Completion.objects.filter(user=user).count()
        today_date = completion_instance.completed_at.date()
        
        # 1. First Completion
        if user_completion_count == 1:
            _award_achievement_if_not_earned(user, request, 'first_completion')

        # 1b. First Project Completion (if the first completion was a project)
        if user_completion_count == 1 and completed_lesson.lesson_type == 'Project':
             _award_achievement_if_not_earned(user, request, 'first_project')
        # Or, if it's not the *very* first completion, check if it's the first *project* completion
        elif completed_lesson.lesson_type == 'Project':
            project_completion_count = Completion.objects.filter(user=user, lesson__lesson_type='Project').count()
            if project_completion_count == 1:
                 _award_achievement_if_not_earned(user, request, 'first_project')

        # 2. Section Completion (HTML, CSS)
        section_just_completed = completed_lesson.section
        section_lesson_ids = set(section_just_completed.lessons.values_list('id', flat=True))
        user_completed_lesson_ids_in_section = set(Completion.objects.filter(user=user, lesson__section=section_just_completed).values_list('lesson_id', flat=True))
        
        if section_lesson_ids.issubset(user_completed_lesson_ids_in_section) and len(section_lesson_ids) > 0:
            section_slug_part = section_just_completed.title.lower().split(' ')[0] 
            # TODO: Add Section.slug field for reliable matching
            if section_slug_part == 'html': 
                 _award_achievement_if_not_earned(user, request, 'completed_html_section')
            elif section_slug_part == 'css': 
                 _award_achievement_if_not_earned(user, request, 'completed_css_section')
            # Add elif for other sections here

        # 3. Course Completion
        total_lessons_in_course = Lesson.objects.count()
        if total_lessons_in_course > 0 and user_completion_count >= total_lessons_in_course:
            _award_achievement_if_not_earned(user, request, 'completed_all')

        # 4. Weekend Warrior
        if completion_instance.completed_at.weekday() >= 5: # 5 = Saturday, 6 = Sunday
            _award_achievement_if_not_earned(user, request, 'weekend_completion')

        # 5. Learning Spree (3 in a day)
        completions_today = Completion.objects.filter(user=user, completed_at__date=today_date).count()
        if completions_today >= 3:
             _award_achievement_if_not_earned(user, request, 'learning_spree_3')

    # --- Checks based on latest Profile state --- 
    if current_profile:
        if current_profile.total_points >= 100:
            _award_achievement_if_not_earned(user, request, 'points_100')
        if current_profile.total_points >= 500:
            _award_achievement_if_not_earned(user, request, 'points_500')
        if current_profile.total_points >= 1000:
             _award_achievement_if_not_earned(user, request, 'points_1000')

    # --- Checks based on latest Streak state --- 
    if current_streak:
        if current_streak.current_streak >= 3:
            _award_achievement_if_not_earned(user, request, 'streak_3_day')
        if current_streak.current_streak >= 7:
            _award_achievement_if_not_earned(user, request, 'streak_7_day')
        if current_streak.current_streak >= 30:
            _award_achievement_if_not_earned(user, request, 'streak_30_day')

    # --- Checks Triggered by Daily Challenge Completion --- 
    if daily_challenge_completed:
        completed_challenges_count = UserDailyChallenge.objects.filter(user=user, completed_date__isnull=False).count()
        # Check counts *after* the current one might have been completed
        if completed_challenges_count >= 1: # Award on first completion
            _award_achievement_if_not_earned(user, request, 'first_daily_challenge')
        if completed_challenges_count >= 5:
            _award_achievement_if_not_earned(user, request, 'daily_challenge_5')

    # --- Checks Triggered by Viewing Specific Pages --- 
    if view_context == 'leaderboard':
        _award_achievement_if_not_earned(user, request, 'viewed_leaderboard')
    elif view_context == 'achievements':
        _award_achievement_if_not_earned(user, request, 'viewed_achievements')
    elif view_context == 'reset':
        _award_achievement_if_not_earned(user, request, 'reset_progress')

    # Note: The old achievement slugs like FIRST_LESSON, FIRST_PROJECT, PERFECT_SECTION etc.
    # are replaced by the new slugs (first_completion, etc.)
    # The logic for HTML/CSS completion assumes section titles or needs refinement (e.g., Section slug).

    # 1. First Lesson Completed
    if Completion.objects.filter(user=user).count() == 1:
        _award_achievement_if_not_earned(user, request, 'first_completion')

    # 2. First Project Completed
    if completion_instance and completion_instance.lesson_type == 'Project':
        if Completion.objects.filter(user=user, lesson__lesson_type='Project').count() == 1:
            _award_achievement_if_not_earned(user, request, 'first_project')

    # 3. Section Completion Achievements (example: HTML, CSS, JS)
    # This requires knowing section titles or having specific slugs for sections.
    # Assuming section titles are somewhat stable or we add slugs to Section model later.
    completed_lesson_ids = Completion.objects.filter(user=user).values_list('lesson_id', flat=True)
    
    # Check for HTML Section (assuming its title or a way to identify it)
    try:
        html_section = Section.objects.get(title__icontains="HTML Foundations") # Fragile, better to use slug if added
        html_lessons_total = html_section.lessons.count()
        html_lessons_completed = html_section.lessons.filter(id__in=completed_lesson_ids).count()
        if html_lessons_total > 0 and html_lessons_total == html_lessons_completed:
            _award_achievement_if_not_earned(user, request, 'completed_html_section')
    except Section.DoesNotExist:
        pass # Section not found, can't award

    # Similar checks for CSS Foundations, JS Basics would go here...
    try:
        css_section = Section.objects.get(title__icontains="CSS Foundations")
        css_lessons_total = css_section.lessons.count()
        css_lessons_completed = css_section.lessons.filter(id__in=completed_lesson_ids).count()
        if css_lessons_total > 0 and css_lessons_total == css_lessons_completed:
            _award_achievement_if_not_earned(user, request, 'completed_css_section')
    except Section.DoesNotExist:
        pass
    
    try:
        js_section = Section.objects.get(title__icontains="JavaScript Basics")
        js_lessons_total = js_section.lessons.count()
        js_lessons_completed = js_section.lessons.filter(id__in=completed_lesson_ids).count()
        if js_lessons_total > 0 and js_lessons_total == js_lessons_completed:
            _award_achievement_if_not_earned(user, request, 'completed_js_section')
    except Section.DoesNotExist:
        pass

    # 4. Perfect Section (any section fully completed)
    if completion_instance: # Check only if a lesson was just completed
        section_just_completed = completed_lesson.section
        lessons_in_section_total = section_just_completed.lessons.count()
        lessons_in_section_completed_by_user = section_just_completed.lessons.filter(id__in=completed_lesson_ids).count()
        if lessons_in_section_total > 0 and lessons_in_section_total == lessons_in_section_completed_by_user:
            # Check if this is the *first time* this specific section was perfected by the user for this achievement
            # This specific "perfect section" achievement is generic and can be awarded multiple times
            # if we don't link it to a specific section object.
            # For now, let's assume a general "Perfect Section" can be awarded once.
            # To make it per-section, the Achievement model would need a ForeignKey to Section.
            _award_achievement_if_not_earned(user, request, 'completed_perfect_section')

    # 5. Streak Achievements
    if current_streak:
        if current_streak.current_streak >= 10:
            _award_achievement_if_not_earned(user, request, 'streak_10_day')
        if current_streak.current_streak >= 30:
            _award_achievement_if_not_earned(user, request, 'streak_30_day')
    
    # 6. Point Milestones
    if current_profile:
        if current_profile.total_points >= 100:
            _award_achievement_if_not_earned(user, request, 'points_100')
        if current_profile.total_points >= 500:
            _award_achievement_if_not_earned(user, request, 'points_500')

    # 7. Course Completed
    total_lessons_in_course = Lesson.objects.count()
    user_total_completed_lessons = Completion.objects.filter(user=user).count()
    if total_lessons_in_course > 0 and user_total_completed_lessons >= total_lessons_in_course:
        _award_achievement_if_not_earned(user, request, 'completed_all') 