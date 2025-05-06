# tracker/achievements.py

from django.contrib import messages
from .models import User, Achievement, UserAchievement, UserProfile, Completion, Section, Lesson, UserStreak

# Predefined achievement slugs (must match those created in the admin)
ACHIEVEMENT_SLUGS = {
    'FIRST_LESSON': 'first-lesson-completed',
    'HTML_FOUNDATION_COMPLETE': 'html-foundation-complete',
    'CSS_FOUNDATION_COMPLETE': 'css-foundation-complete',
    'JS_BASICS_COMPLETE': 'javascript-basics-complete',
    'FIRST_PROJECT': 'first-project-completed',
    'PERFECT_SECTION': 'perfect-section', # For completing all lessons in any section
    'TEN_DAY_STREAK': 'ten-day-streak',
    'THIRTY_DAY_STREAK': 'thirty-day-streak',
    'POINT_MILESTONE_100': '100-points-milestone',
    'POINT_MILESTONE_500': '500-points-milestone',
    'COURSE_COMPLETED': 'foundations-course-completed',
}

def award_achievement(user, achievement_slug, request=None):
    """Awards an achievement to a user if not already awarded and updates points."""
    try:
        achievement = Achievement.objects.get(achievement_slug=achievement_slug)
        user_achievement, created = UserAchievement.objects.get_or_create(
            user=user,
            achievement=achievement
        )
        if created:
            profile = UserProfile.objects.get(user=user)
            profile.total_points += achievement.points_reward
            profile.save()
            if request:
                messages.success(request, 
                    f"🎉 Achievement Unlocked: {achievement.title}! (+{achievement.points_reward} points)")
            # print(f"Awarded '{achievement.title}' to {user.username}") # For server logs
            return True # Indicates achievement was newly awarded
    except Achievement.DoesNotExist:
        # print(f"Attempted to award non-existent achievement: {achievement_slug}") # For server logs
        pass
    except UserProfile.DoesNotExist:
        # print(f"UserProfile not found for {user.username} when awarding achievement.")
        pass
    return False # Not newly awarded or error

def check_and_award_achievements(user, request=None, completed_lesson=None):
    """Checks all relevant conditions and awards achievements to the user."""
    if not user or not user.is_authenticated: # Ensure user is valid
        return

    # 1. First Lesson Completed
    if Completion.objects.filter(user=user).count() == 1:
        award_achievement(user, ACHIEVEMENT_SLUGS['FIRST_LESSON'], request)

    # 2. First Project Completed
    if completed_lesson and completed_lesson.lesson_type == 'Project':
        if Completion.objects.filter(user=user, lesson__lesson_type='Project').count() == 1:
            award_achievement(user, ACHIEVEMENT_SLUGS['FIRST_PROJECT'], request)

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
            award_achievement(user, ACHIEVEMENT_SLUGS['HTML_FOUNDATION_COMPLETE'], request)
    except Section.DoesNotExist:
        pass # Section not found, can't award

    # Similar checks for CSS Foundations, JS Basics would go here...
    try:
        css_section = Section.objects.get(title__icontains="CSS Foundations")
        css_lessons_total = css_section.lessons.count()
        css_lessons_completed = css_section.lessons.filter(id__in=completed_lesson_ids).count()
        if css_lessons_total > 0 and css_lessons_total == css_lessons_completed:
            award_achievement(user, ACHIEVEMENT_SLUGS['CSS_FOUNDATION_COMPLETE'], request)
    except Section.DoesNotExist:
        pass
    
    try:
        js_section = Section.objects.get(title__icontains="JavaScript Basics")
        js_lessons_total = js_section.lessons.count()
        js_lessons_completed = js_section.lessons.filter(id__in=completed_lesson_ids).count()
        if js_lessons_total > 0 and js_lessons_total == js_lessons_completed:
            award_achievement(user, ACHIEVEMENT_SLUGS['JS_BASICS_COMPLETE'], request)
    except Section.DoesNotExist:
        pass

    # 4. Perfect Section (any section fully completed)
    if completed_lesson: # Check only if a lesson was just completed
        section_just_completed = completed_lesson.section
        lessons_in_section_total = section_just_completed.lessons.count()
        lessons_in_section_completed_by_user = section_just_completed.lessons.filter(id__in=completed_lesson_ids).count()
        if lessons_in_section_total > 0 and lessons_in_section_total == lessons_in_section_completed_by_user:
            # Check if this is the *first time* this specific section was perfected by the user for this achievement
            # This specific "perfect section" achievement is generic and can be awarded multiple times
            # if we don't link it to a specific section object.
            # For now, let's assume a general "Perfect Section" can be awarded once.
            # To make it per-section, the Achievement model would need a ForeignKey to Section.
            award_achievement(user, ACHIEVEMENT_SLUGS['PERFECT_SECTION'], request)

    # 5. Streak Achievements
    user_streak = UserStreak.objects.filter(user=user).first()
    if user_streak:
        if user_streak.current_streak >= 10:
            award_achievement(user, ACHIEVEMENT_SLUGS['TEN_DAY_STREAK'], request)
        if user_streak.current_streak >= 30:
            award_achievement(user, ACHIEVEMENT_SLUGS['THIRTY_DAY_STREAK'], request)
    
    # 6. Point Milestones
    user_profile = UserProfile.objects.filter(user=user).first()
    if user_profile:
        if user_profile.total_points >= 100:
            award_achievement(user, ACHIEVEMENT_SLUGS['POINT_MILESTONE_100'], request)
        if user_profile.total_points >= 500:
            award_achievement(user, ACHIEVEMENT_SLUGS['POINT_MILESTONE_500'], request)

    # 7. Course Completed
    total_lessons_in_course = Lesson.objects.count()
    user_total_completed_lessons = Completion.objects.filter(user=user).count()
    if total_lessons_in_course > 0 and user_total_completed_lessons >= total_lessons_in_course:
        award_achievement(user, ACHIEVEMENT_SLUGS['COURSE_COMPLETED'], request) 