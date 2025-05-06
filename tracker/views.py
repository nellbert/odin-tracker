from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Count, Q, Sum # Import Sum
from django.contrib import messages
from .models import Section, Lesson, Completion, UserProfile, UserStreak, UserAchievement, UserDailyChallenge, Achievement # Add UserAchievement and UserDailyChallenge
from django.contrib.auth.models import User # Import User
from .forms import SignUpForm, EmailChangeForm # Updated imports
from django.contrib.auth import login, update_session_auth_hash # Import login and update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from datetime import date, timedelta # Add date for streak logic if not already there from models
from .achievements import check_and_award_achievements # Import the new function
from .daily_challenges_logic import assign_new_daily_challenge, update_daily_challenge_progress # Import new functions
from django.urls import reverse_lazy, reverse # Import reverse
from django.utils import timezone
from django.http import JsonResponse # Import JsonResponse
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView

# Helper function to get dashboard context data for a user
def _get_user_dashboard_context(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    user_streak, _ = UserStreak.objects.get_or_create(user=user)
    user_daily_challenge = assign_new_daily_challenge(user) # Get current challenge status
    
    total_lessons_count = Lesson.objects.count()
    user_completed_count = Completion.objects.filter(user=user).count()
    progress_percentage = 0
    if total_lessons_count > 0:
        progress_percentage = round((user_completed_count / total_lessons_count) * 100)

    # Format last activity date if it exists
    last_activity_str = user_streak.last_activity_date.strftime("%b %d") if user_streak.last_activity_date else "No activity yet"

    # Prepare daily challenge context
    daily_challenge_context = None
    if user_daily_challenge and user_daily_challenge.challenge:
        daily_challenge_context = {
            'is_completed': user_daily_challenge.is_completed,
            'description': user_daily_challenge.challenge.get_description(),
            'current_progress': user_daily_challenge.current_progress,
            'target_value': user_daily_challenge.challenge.target_value,
            'points_reward': user_daily_challenge.challenge.points_reward
        }
        
    return {
        'total_points': profile.total_points,
        'progress_percentage': progress_percentage,
        'user_completed_count': user_completed_count,
        'total_lessons_count': total_lessons_count, # Keep this if needed
        'current_streak': user_streak.current_streak,
        'longest_streak': user_streak.longest_streak,
        'last_activity_date_str': last_activity_str,
        'daily_challenge': daily_challenge_context # Include challenge details
        # We could add recent achievements here too, but it might complicate the JSON
    }

@login_required
def dashboard(request):
    user = request.user
    sections = Section.objects.prefetch_related('lessons').all()
    completed_lessons = Completion.objects.filter(user=user).values_list('lesson_id', flat=True)
    # Get context using the helper
    user_context = _get_user_dashboard_context(user)
    # Get recent achievements separately for the main template
    recent_achievements = UserAchievement.objects.filter(user=user).select_related('achievement')[:5]
    
    # Check for view-based achievements (handled in leaderboard/achievements views now)
    # check_and_award_achievements(user, request) # Not needed here anymore

    context = {
        'sections': sections,
        'completed_lessons': set(completed_lessons),
        **user_context, # Unpack the user-specific context
        'user_achievements': recent_achievements, # Pass recent achievements
        # Pass the full daily challenge object if needed by specific template logic
        'user_daily_challenge': assign_new_daily_challenge(user), 
    }
    return render(request, 'tracker/dashboard.html', context)

@login_required
@require_POST
def mark_complete(request, lesson_id):
    user = request.user
    lesson_obj = get_object_or_404(Lesson, id=lesson_id)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    response_message = ""

    try:
        with transaction.atomic():
            # Use select_for_update on profile and streak if potential race conditions exist
            profile = UserProfile.objects.select_for_update().get(user=user)
            user_streak, streak_created = UserStreak.objects.select_for_update().get_or_create(user=user)
            
            completion, created = Completion.objects.get_or_create(user=user, lesson=lesson_obj)

            if created:
                points_before = profile.total_points # Get points before update
                profile.total_points += lesson_obj.points_value
                points_awarded_for_lesson = lesson_obj.points_value
                profile.save()
                user_streak.update_streak() # Saves streak internally
                
                # Check achievements silently for AJAX, pass request for non-AJAX messages
                check_and_award_achievements(user, None if is_ajax else request, 
                                           completion_instance=completion, 
                                           profile=profile, 
                                           streak=user_streak)
                
                lesson_info_for_challenge = {'lesson_type': lesson_obj.lesson_type, 'points_earned': lesson_obj.points_value}
                challenge_was_completed = update_daily_challenge_progress(user, None if is_ajax else request, 
                                                                          completed_lesson_info=lesson_info_for_challenge, 
                                                                          points_earned_in_action=points_awarded_for_lesson)
                if challenge_was_completed:
                    # Check daily challenge achievements silently for AJAX
                    check_and_award_achievements(user, None if is_ajax else request, daily_challenge_completed=True)

                response_message = f"'{lesson_obj.title}' marked as complete! (+{points_awarded_for_lesson} points)"
                if not is_ajax:
                    messages.success(request, f"{response_message} Streak: {user_streak.current_streak} day(s)!")
                
            else: # Already completed
                response_message = f"'{lesson_obj.title}' was already marked as complete."
                if not is_ajax:
                    messages.info(request, response_message)
        
        # If successful, return updated context for AJAX
        if is_ajax:
            updated_context = _get_user_dashboard_context(user)
            return JsonResponse({'status': 'ok', 'message': response_message, 'context': updated_context})
            
    except Exception as e:
        print(f"Error in mark_complete for user {user.id}, lesson {lesson_id}: {e}") 
        response_message = f'An error occurred: {e}'
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': response_message}, status=500)
        else:
            messages.error(request, response_message)

    return redirect('dashboard')

@login_required
@require_POST
def unmark_complete(request, lesson_id):
    user = request.user
    lesson = get_object_or_404(Lesson, id=lesson_id)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    response_message = ""

    try:
        with transaction.atomic():
            profile = UserProfile.objects.select_for_update().get(user=user)
            completion = Completion.objects.filter(user=user, lesson=lesson).first()
            
            if completion:
                points_to_subtract = lesson.points_value
                profile.total_points = max(0, profile.total_points - points_to_subtract)
                profile.save()
                completion.delete()
                # Note: Not recalculating streak/achievements on unmark for simplicity now
                response_message = f"'{lesson.title}' marked as incomplete. (-{points_to_subtract} points)"
                if not is_ajax:
                    messages.success(request, response_message)
            else:
                response_message = f"'{lesson.title}' was already not marked as complete."
                if not is_ajax:
                    messages.info(request, response_message)
        
        if is_ajax:
            updated_context = _get_user_dashboard_context(user)
            return JsonResponse({'status': 'ok', 'message': response_message, 'context': updated_context})

    except Exception as e:
        print(f"Error in unmark_complete for user {user.id}, lesson {lesson_id}: {e}") 
        response_message = f'An error occurred: {e}'
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': response_message}, status=500)
        else:
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
    user = request.user

    email_form = EmailChangeForm(instance=user)
    password_form = PasswordChangeForm(user=user)

    if request.method == 'POST':
        if 'change_email' in request.POST:
            email_form = EmailChangeForm(request.POST, instance=user)
            if email_form.is_valid():
                email_form.save()
                messages.success(request, 'Your email address has been updated.')
                return redirect('user_settings')
        # Notification form logic removed

    context = {
        'email_form': email_form,
        'password_form': password_form,
    }
    return render(request, 'tracker/settings.html', context)

class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'tracker/settings_password_change.html' # Or integrate into settings.html
    success_url = reverse_lazy('password_change_done') # Redirect to a success page

    def form_valid(self, form):
        response = super().form_valid(form)
        update_session_auth_hash(self.request, form.user) # Important to keep user logged in
        messages.success(self.request, 'Your password was successfully updated!')
        return response

class CustomPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'tracker/settings_password_change_done.html' # A simple confirmation page

@login_required
@require_POST
def delete_account(request):
    user = request.user
    if request.POST.get('confirm_delete') == 'true': # Ensure confirmation
        try:
            # Keep user object to log out before deleting
            # Or handle logout after redirect if preferred
            user_to_delete = User.objects.get(pk=user.pk)
            user_to_delete.is_active = False # Deactivate instead of full delete initially for safety/recovery
            user_to_delete.save()
            # Perform full logout
            from django.contrib.auth import logout
            logout(request)
            messages.success(request, "Your account has been deactivated and you have been logged out. We're sad to see you go.")
            return redirect('login') # Or a 'goodbye' page
        except User.DoesNotExist:
            messages.error(request, "User not found.") # Should not happen if logged in
            return redirect('user_settings')
        except Exception as e:
            messages.error(request, f"An error occurred while deactivating your account: {e}")
            return redirect('user_settings')
    else:
        messages.error(request, "Account deletion not confirmed.")
        return redirect('user_settings')

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

@login_required
def leaderboard(request):
    user = request.user
    check_and_award_achievements(user, request, view_context='leaderboard')
    # Get all users with their profiles, streaks, completions, achievements, and daily challenge status
    users = User.objects.filter(is_active=True).select_related('profile', 'streak').prefetch_related('completions', 'achievements', 'daily_challenge_instance')

    leaderboard_data = []
    for u in users:
        profile = getattr(u, 'profile', None)
        streak = getattr(u, 'streak', None)
        completions_count = u.completions.count()
        achievements_count = u.achievements.count()
        daily_challenge = getattr(u, 'daily_challenge_instance', None)
        daily_challenge_completed = daily_challenge.is_completed if daily_challenge else False
        leaderboard_data.append({
            'username': u.username,
            'total_points': profile.total_points if profile else 0,
            'current_streak': streak.current_streak if streak else 0,
            'longest_streak': streak.longest_streak if streak else 0,
            'lessons_completed': completions_count,
            'achievements_earned': achievements_count,
            'daily_challenge_completed': daily_challenge_completed,
        })

    # Sort by total_points descending, then lessons_completed, then achievements_earned
    leaderboard_data.sort(key=lambda x: (-x['total_points'], -x['lessons_completed'], -x['achievements_earned']))

    context = {
        'leaderboard': leaderboard_data,
    }
    return render(request, 'tracker/leaderboard.html', context)

@login_required
def achievements_page(request):
    user = request.user
    check_and_award_achievements(user, request, view_context='achievements')
    all_system_achievements = Achievement.objects.all().order_by('title')
    user_unlocked_achievements = UserAchievement.objects.filter(user=user).select_related('achievement')
    
    user_unlocked_ids = {ua.achievement_id for ua in user_unlocked_achievements}
    user_unlocked_map = {ua.achievement_id: ua.awarded_at for ua in user_unlocked_achievements}

    all_achievements_data = []
    unlocked_achievements_data = []
    locked_achievements_data = []

    for ach in all_system_achievements:
        is_unlocked = ach.id in user_unlocked_ids
        awarded_at = user_unlocked_map.get(ach.id) if is_unlocked else None
        data_obj = {'instance': ach, 'is_unlocked': is_unlocked, 'awarded_at': awarded_at}
        
        all_achievements_data.append(data_obj)
        if is_unlocked:
            unlocked_achievements_data.append(data_obj)
        else:
            locked_achievements_data.append(data_obj)
            
    total_achievements_count = all_system_achievements.count()
    unlocked_count = len(unlocked_achievements_data)

    context = {
        'all_achievements_data': all_achievements_data,
        'unlocked_achievements_data': unlocked_achievements_data,
        'locked_achievements_data': locked_achievements_data,
        'total_achievements_count': total_achievements_count,
        'unlocked_achievements_count': unlocked_count,
        'locked_achievements_count': total_achievements_count - unlocked_count,
    }
    return render(request, 'tracker/achievements_list.html', context)

# View for the landing page or redirecting to dashboard
def root_landing_page_view(request):
    print("DEBUG: root_landing_page_view called. User authenticated:", request.user.is_authenticated)
    if request.user.is_authenticated:
        return redirect('dashboard') # Named URL for the dashboard
    return render(request, 'landing_page.html') 