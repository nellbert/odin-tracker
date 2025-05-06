# OdinTrack

A Django web application to track progress through The Odin Project (TOP) Foundations course in a gamified way.

## Setup

1.  **Clone the repository (if applicable)**

2.  **Install dependencies:**
    ```bash
    python3 -m pip install -r requirements.txt
    ```

3.  **Apply database migrations:**
    ```bash
    # Make sure you are in the directory containing manage.py
    python3 manage.py makemigrations tracker
    python3 manage.py migrate
    ```

4.  **Create a superuser (for admin access):**
    ```bash
    python3 manage.py createsuperuser
    ```
    Follow the prompts to create an admin username and password.

5.  **Run the development server:**
    ```bash
    python3 manage.py runserver
    ```

6.  **Access the application:**
    *   Open your web browser to `http://127.0.0.1:8000/`
    *   Access the admin interface at `http://127.0.0.1:8000/admin/` to populate Sections and Lessons.

## Features

*   User registration, login, and logout
*   Dashboard displaying course sections and lessons
*   Mark lessons and projects as complete
*   Points accumulation based on completed items
*   Overall progress tracking with progress bars and stats
*   Achievements system with unlockable badges and rewards
*   Streak tracking (current and longest streaks)
*   Daily challenges with bonus points for completion
*   Leaderboard with global user rankings (points, completions, achievements, streaks)
*   Recent achievements and live user stats (real-time updates)
*   User settings page with the ability to reset all progress
*   Admin interface for managing course structure (Sections, Lessons), achievements, and user data

## Core Concepts

- **Sections & Lessons:** The course is organized into sections, each containing lessons and projects. Lessons can be marked as complete to track progress.
- **Points:** Earn points for every lesson or project you complete. Points contribute to your overall ranking and unlock achievements.
- **Achievements:** Unlock badges for milestones like completing your first lesson, finishing a section, reaching point thresholds, or maintaining streaks.
- **Streaks:** Track your daily learning streaks. Maintain consecutive days of activity to build your streak and unlock special achievements.
- **Daily Challenges:** Each day, receive a new challenge (e.g., complete N lessons, earn N points, finish a project) for bonus points.
- **Leaderboard:** See how you rank against other users based on points, completions, achievements, and streaks. 