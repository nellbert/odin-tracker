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

*   User registration, login, logout.
*   Dashboard displaying course sections and lessons.
*   Mark lessons/projects as complete.
*   Points accumulation based on completed items.
*   Overall progress tracking.
*   Admin interface for managing course structure (Sections, Lessons) and user data. 