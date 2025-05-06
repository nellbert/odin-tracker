from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Count, Q, Sum # Import Sum
from django.contrib import messages
from .models import Section, Lesson, Completion, UserProfile, UserStreak, UserAchievement, UserDailyChallenge # Add UserAchievement and UserDailyChallenge
from django.contrib.auth.models import User # Import User
from .forms import SignUpForm
from django.contrib.auth import login # Import login
from datetime import date, timedelta # Add date for streak logic if not already there from models
from .achievements import check_and_award_achievements # Import the new function
from .daily_challenges_logic import assign_new_daily_challenge, update_daily_challenge_progress # Import new functions
from django.urls import reverse_lazy
from django.utils import timezone

@login_required
def dashboard(request):
    user = request.user
    sections = Section.objects.prefetch_related('lessons').all()
    completed_lessons = Completion.objects.filter(user=user).values_list('lesson_id', flat=True)

    total_lessons_count = Lesson.objects.count()
    user_completed_count = len(completed_lessons)

    progress_percentage = 0
    if total_lessons_count > 0:
        progress_percentage = round((user_completed_count / total_lessons_count) * 100)

    profile, created = UserProfile.objects.get_or_create(user=user)
    # Fetch streak data, get_or_create ensures it exists
    user_streak, streak_created = UserStreak.objects.get_or_create(user=user)
    # If streak was just created, its last_activity_date might be None.
    # We might want to run update_streak() here if user has completions but streak was just made.
    # For now, assume update_streak() is primarily driven by new completions.
    # A more robust daily check (e.g. on login) might be needed for perfect accuracy if user completes offline and then syncs.

    # Check if streak should be reset (if last activity was before yesterday)
    # This is a simple check on dashboard load. A more robust solution uses a daily cron job.
    today = date.today()
    if user_streak.last_activity_date and user_streak.last_activity_date < (today - timedelta(days=1)):
        if user_streak.current_streak > 0: # Only reset if there was an active streak
            user_streak.current_streak = 0
            # Do not reset last_activity_date here, update_streak handles it on new activity.
            user_streak.save()
            messages.info(request, "Your streak was reset due to inactivity. Keep learning daily!")

    # Assign or get current daily challenge
    user_daily_challenge = assign_new_daily_challenge(user)

    # Check for achievements on dashboard load (for cumulative ones)
    check_and_award_achievements(user, request)

    context = {
        'sections': sections,
        'completed_lessons': set(completed_lessons),
        'total_points': profile.total_points,
        'progress_percentage': progress_percentage,
        'user_completed_count': user_completed_count,
        'total_lessons_count': total_lessons_count,
        'current_streak': user_streak.current_streak,
        'longest_streak': user_streak.longest_streak,
        'last_activity_date': user_streak.last_activity_date,
        'user_achievements': UserAchievement.objects.filter(user=user).select_related('achievement')[:5], # Get top 5 recent
        'user_daily_challenge': user_daily_challenge,
    }
    return render(request, 'tracker/dashboard.html', context)

@login_required
@require_POST # Ensure this view only accepts POST requests
def mark_complete(request, lesson_id):
    user = request.user
    lesson_obj = get_object_or_404(Lesson, id=lesson_id)
    profile = user.profile # Assumes profile exists via signal
    # Get or create the streak record for the user
    user_streak, streak_created = UserStreak.objects.get_or_create(user=user)

    points_awarded_for_lesson = 0 # Track points from this lesson completion

    # Use transaction.atomic to ensure database consistency
    try:
        with transaction.atomic():
            # Check if already completed
            completion, created = Completion.objects.get_or_create(
                user=user,
                lesson=lesson_obj
            )

            if created:
                # If newly created, update points
                profile.total_points += lesson_obj.points_value
                points_awarded_for_lesson = lesson_obj.points_value # Store points from this lesson
                profile.save()
                
                # Update streak
                user_streak.update_streak()

                # Check for achievements after a lesson is completed
                check_and_award_achievements(user, request, completed_lesson=lesson_obj)

                messages.success(request, f"'{lesson_obj.title}' marked as complete! +{lesson_obj.points_value} points. Streak: {user_streak.current_streak} day(s)!")
                
                # Update daily challenge progress
                lesson_info_for_challenge = {
                    'lesson_type': lesson_obj.lesson_type,
                    'points_earned': lesson_obj.points_value # This specific lesson's points
                }
                update_daily_challenge_progress(user, request, completed_lesson_info=lesson_info_for_challenge, points_earned_in_action=points_awarded_for_lesson)
            else:
                # If already existed
                messages.info(request, f"'{lesson_obj.title}' was already marked as complete.")
                # Even if already complete, we could update daily challenge if it's point-based and points were gained elsewhere.
                # For now, tied to lesson completion action.
                # update_daily_challenge_progress(user, request, points_earned_in_action=0) # If points are earned by other means and should count

    except Exception as e:
        # Handle potential errors during the transaction
        messages.error(request, f'An error occurred: {e}')

    return redirect('dashboard')

@login_required
@require_POST
def unmark_complete(request, lesson_id):
    user = request.user
    lesson = get_object_or_404(Lesson, id=lesson_id)
    profile = user.profile

    try:
        with transaction.atomic():
            # Find the specific completion record
            completion = Completion.objects.filter(user=user, lesson=lesson).first()

            if completion:
                # Subtract points BEFORE deleting completion
                # Ensure points don't go below zero
                points_to_subtract = lesson.points_value
                profile.total_points = max(0, profile.total_points - points_to_subtract)
                profile.save()

                # Delete the completion record
                completion.delete()

                messages.success(request, 
                    f"'{lesson.title}' marked as incomplete. (-{points_to_subtract} points)")
                
                # Note: We are NOT automatically recalculating streaks here.
                # The user's last_activity_date remains, and the next completion
                # will correctly determine the streak continuation from that date.
                # We also don't need to re-check achievements here, as undoing 
                # completion shouldn't typically grant new achievements.

            else:
                # If no completion record exists, inform the user
                messages.info(request, f"'{lesson.title}' was already not marked as complete.")

    except Exception as e:
        messages.error(request, f'An error occurred while undoing completion: {e}')

    return redirect('dashboard')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save() # This triggers the post_save signal for UserProfile
            login(request, user) # Log the user in directly after signup
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard') # Redirect to dashboard after signup
        else:
            # Form is invalid, add error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def user_settings(request):
    """Displays the user settings page."""
    # Can add more settings later (e.g., change password, email)
    context = {}
    return render(request, 'tracker/settings.html', context)

@login_required
@require_POST # Ensure this can only be triggered by a POST request
def reset_progress(request):
    """Resets all progress for the logged-in user."""
    user = request.user

    try:
        with transaction.atomic():
            # 1. Delete Completions
            completions_deleted, _ = Completion.objects.filter(user=user).delete()

            # 2. Delete Earned Achievements
            achievements_deleted, _ = UserAchievement.objects.filter(user=user).delete()

            # 3. Reset UserStreak
            streak, streak_created = UserStreak.objects.get_or_create(user=user)
            streak.current_streak = 0
            streak.longest_streak = 0 # Reset longest streak too, or keep it?
            streak.last_activity_date = None
            streak.save()

            # 4. Reset UserProfile points
            profile, profile_created = UserProfile.objects.get_or_create(user=user)
            profile.total_points = 0
            profile.save()

            # 5. Reset or Clear UserDailyChallenge
            daily_challenge_instance = UserDailyChallenge.objects.filter(user=user).first()
            if daily_challenge_instance:
                daily_challenge_instance.challenge = None
                daily_challenge_instance.assigned_date = timezone.now().date() - timedelta(days=1) # Mark as old
                daily_challenge_instance.completed_date = None
                daily_challenge_instance.current_progress = 0
                daily_challenge_instance.initial_points_at_assignment = None
                daily_challenge_instance.save()
                # Alternatively, delete it: daily_challenge_instance.delete()
                # and let it be recreated on next dashboard load. Resetting fields is safer.

            messages.success(request, "Your progress has been successfully reset!")

    except Exception as e:
        messages.error(request, f"An error occurred while resetting progress: {e}")
        # Redirect back to settings page on error
        return redirect('user_settings')

    # Redirect to dashboard after successful reset
    return redirect('dashboard') 