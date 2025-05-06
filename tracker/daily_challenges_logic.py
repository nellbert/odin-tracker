# tracker/daily_challenges_logic.py

from django.utils import timezone
from django.contrib import messages
from .models import User, DailyChallenge, UserDailyChallenge, UserProfile, Completion, Lesson
import random

def assign_new_daily_challenge(user):
    """Assigns a new random daily challenge if the user doesn't have one for today or it's the first time."""
    today = timezone.now().date()
    user_challenge_instance, created = UserDailyChallenge.objects.get_or_create(
        user=user,
        defaults={'assigned_date': today}
    )

    # Assign new challenge ONLY if it was just created for the user OR if the current assignment is from a previous day
    if created or user_challenge_instance.assigned_date < today:
        active_challenges = DailyChallenge.objects.filter(is_active=True)
        if not active_challenges.exists():
            user_challenge_instance.challenge = None # No active challenge types available
            user_challenge_instance.current_progress = 0
            user_challenge_instance.initial_points_at_assignment = 0
            user_challenge_instance.completed_date = None
            user_challenge_instance.assigned_date = today # Update to today if it was an old one
            user_challenge_instance.save()
            return user_challenge_instance # Return the instance, even if no challenge assigned

        selected_challenge = random.choice(list(active_challenges))
        
        user_challenge_instance.challenge = selected_challenge
        user_challenge_instance.assigned_date = today
        user_challenge_instance.completed_date = None # Reset completion status
        user_challenge_instance.current_progress = 0 # Reset progress
        
        if selected_challenge.challenge_type == 'EARN_N_POINTS':
            try:
                profile = UserProfile.objects.get(user=user)
                user_challenge_instance.initial_points_at_assignment = profile.total_points
            except UserProfile.DoesNotExist:
                 user_challenge_instance.initial_points_at_assignment = 0 # Should not happen
        else:
            user_challenge_instance.initial_points_at_assignment = None
            
        user_challenge_instance.save()
    
    # Always return the instance for the current user (which might be from today, completed or not)
    return user_challenge_instance

def update_daily_challenge_progress(user, request=None, completed_lesson_info=None, points_earned_in_action=0):
    """Updates the user's active daily challenge progress and awards if completed (only once)."""
    today = timezone.now().date()
    # Retrieve the challenge instance assigned for today or create if missing (should be handled by assign_new)
    user_challenge_instance = UserDailyChallenge.objects.filter(user=user, assigned_date=today).first()

    # Only proceed if there is an instance assigned for today and it has a challenge and it's not already marked completed
    if not user_challenge_instance or not user_challenge_instance.challenge or user_challenge_instance.is_completed:
        return 

    challenge = user_challenge_instance.challenge
    updated = False

    if challenge.challenge_type == 'COMPLETE_N_LESSONS':
        if completed_lesson_info: # This means a lesson was just completed
            user_challenge_instance.current_progress += 1
            updated = True
    elif challenge.challenge_type == 'EARN_N_POINTS':
        try:
            profile = UserProfile.objects.get(user=user)
            points_progress = profile.total_points - (user_challenge_instance.initial_points_at_assignment or 0)
            # Only update progress if it actually increased (handles potential point loss scenarios better)
            if points_progress > user_challenge_instance.current_progress:
                 user_challenge_instance.current_progress = max(0, points_progress)
                 updated = True
            elif user_challenge_instance.current_progress == 0 and points_progress == 0 and points_earned_in_action > 0:
                 # Edge case: If initial points was 0, and current is 0, but points were earned, update.
                 user_challenge_instance.current_progress = max(0, points_progress)
                 updated = True
        except UserProfile.DoesNotExist:
            return 

    elif challenge.challenge_type == 'COMPLETE_PROJECT':
        if completed_lesson_info and completed_lesson_info.get('lesson_type') == 'Project':
            # For this simple version, any project completion counts. We don't track N projects yet.
            user_challenge_instance.current_progress = 1 # Mark as 1 (representing 1 project done)
            updated = True
    
    if updated:
        user_challenge_instance.save()

    # Check for completion - Award points ONLY if newly completed
    if user_challenge_instance.current_progress >= challenge.target_value and user_challenge_instance.completed_date is None:
        user_challenge_instance.completed_date = today
        user_challenge_instance.save() # Save completion date first
        
        # Award points for challenge completion (now happens only once)
        try:
            profile = UserProfile.objects.get(user=user)
            profile.total_points += challenge.points_reward
            profile.save()
            if request:
                messages.success(request, 
                    f"🏆 Daily Challenge Completed: {challenge.title}! (+{challenge.points_reward} bonus points)")
        except UserProfile.DoesNotExist:
            pass # Should not happen
        
        # Potentially trigger other things, like an achievement for completing X daily challenges
        # from tracker.achievements import check_and_award_achievements # Avoid circular import by calling directly if needed
        # check_and_award_achievements(user, request) # Re-check if completing challenge unlocks other achievements 