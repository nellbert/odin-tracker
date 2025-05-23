# Generated by Django 5.2 on 2024-09-06 18:49 # Adjust date/time if needed
# Updated based on user-provided structure

from django.db import migrations

# --- New Foundations Course Structure ---
# URLs are mapped from the previous version where possible.
# Points are estimated (default 10 for lessons, higher for projects) - ADJUST AS NEEDED.
# Lesson order is sequential as provided by the user.
NEW_FOUNDATIONS_COURSE = {
    1: {"title": "Introduction", "lessons": [
        (1, "How This Course Will Work", 10, "Lesson", "https://www.theodinproject.com/lessons/foundations-how-this-course-will-work"),
        (2, "Introduction to Web Development", 10, "Lesson", "https://www.theodinproject.com/lessons/foundations-introduction-to-web-development"),
        (3, "Motivation and Mindset", 5, "Lesson", "https://www.theodinproject.com/lessons/foundations-motivation-and-mindset"),
        (4, "Asking For Help", 5, "Lesson", "https://www.theodinproject.com/lessons/foundations-asking-for-help"),
        (5, "Join the Odin Community", 5, "Lesson", "https://www.theodinproject.com/lessons/foundations-join-the-odin-community"),
    ]},
    2: {"title": "Prerequisites", "lessons": [
        (1, "Computer Basics", 10, "Lesson", "https://www.theodinproject.com/lessons/foundations-computer-basics"),
        (2, "How Does the Web Work?", 15, "Lesson", "https://www.theodinproject.com/lessons/foundations-how-does-the-web-work"),
        (3, "Installation Overview", 5, "Lesson", "https://www.theodinproject.com/lessons/foundations-installation-overview"),
        (4, "Installations", 20, "Lesson", "https://www.theodinproject.com/lessons/foundations-installations"),
        (5, "Text Editors", 10, "Lesson", "https://www.theodinproject.com/lessons/foundations-text-editors"),
        (6, "Command Line Basics", 15, "Lesson", "https://www.theodinproject.com/lessons/foundations-command-line-basics"),
        (7, "Setting up Git", 15, "Lesson", "https://www.theodinproject.com/lessons/foundations-setting-up-git"),
    ]},
    3: {"title": "Git Basics", "lessons": [
        (1, "Introduction to Git", 10, "Lesson", "https://www.theodinproject.com/lessons/foundations-introduction-to-git"),
        (2, "Git Basics", 20, "Lesson", "https://www.theodinproject.com/lessons/foundations-git-basics"),
        # Note: "Commit Messages" moved to HTML Foundations section as per user list.
        # Note: "Practice: Git Basics" removed as it wasn't in user list.
    ]},
    4: {"title": "HTML Foundations", "lessons": [
        (1, "Introduction to HTML and CSS", 10, "Lesson", "https://www.theodinproject.com/lessons/foundations-introduction-to-html-and-css"),
        (2, "Elements and Tags", 15, "Lesson", "https://www.theodinproject.com/lessons/foundations-elements-and-tags"),
        (3, "HTML Boilerplate", 10, "Lesson", "https://www.theodinproject.com/lessons/foundations-html-boilerplate"),
        (4, "Working with Text", 10, "Lesson", "https://www.theodinproject.com/lessons/foundations-working-with-text"),
        (5, "Lists", 10, "Lesson", "https://www.theodinproject.com/lessons/foundations-lists"),
        (6, "Links and Images", 15, "Lesson", "https://www.theodinproject.com/lessons/foundations-links-and-images"),
        (7, "Commit Messages", 10, "Lesson", "https://www.theodinproject.com/lessons/foundations-commit-messages"), # Moved from Git Basics
        (8, "Project: Recipes", 50, "Project", "https://www.theodinproject.com/lessons/foundations-recipes"),
    ]},
    5: {"title": "CSS Foundations", "lessons": [
        (1, "Intro to CSS", 10, "Lesson", "https://www.theodinproject.com/lessons/foundations-introduction-to-css"),
        (2, "The Cascade", 15, "Lesson", "https://www.theodinproject.com/lessons/foundations-the-cascade"),
        (3, "Inspecting HTML and CSS", 10, "Lesson", "https://www.theodinproject.com/lessons/foundations-inspecting-html-and-css"),
        (4, "The Box Model", 20, "Lesson", "https://www.theodinproject.com/lessons/foundations-the-box-model"),
        (5, "Block and Inline", 10, "Lesson", "https://www.theodinproject.com/lessons/foundations-block-and-inline"),
        # Note: "Project: Landing Page" moved to Flexbox section as per user list.
    ]},
    6: {"title": "Flexbox", "lessons": [
        (1, "Introduction to Flexbox", 15, "Lesson", "https://www.theodinproject.com/lessons/foundations-introduction-to-flexbox"),
        (2, "Growing and Shrinking", 15, "Lesson", "https://www.theodinproject.com/lessons/foundations-growing-and-shrinking"),
        (3, "Axes", 15, "Lesson", "https://www.theodinproject.com/lessons/foundations-axes"),
        (4, "Alignment", 15, "Lesson", "https://www.theodinproject.com/lessons/foundations-alignment"),
        (5, "Project: Landing Page", 75, "Project", "https://www.theodinproject.com/lessons/foundations-landing-page"), # Moved from CSS Foundations
    ]},
    7: {"title": "JavaScript Basics", "lessons": [
        # Mapping user list to previous URLs where possible. Titles updated.
        (1, "Variables and Operators", 15, "Lesson", "https://www.theodinproject.com/lessons/foundations-fundamentals-part-1"), # Was Fundamentals Part 1
        (2, "Installing Node.js", 10, "Lesson", "https://www.theodinproject.com/lessons/foundations-installing-node-js"),
        (3, "Data Types and Conditionals", 15, "Lesson", "https://www.theodinproject.com/lessons/foundations-fundamentals-part-2"), # Was Fundamentals Part 2
        (4, "JavaScript Developer Tools", 10, "Lesson", "https://www.theodinproject.com/lessons/foundations-javascript-developer-tools"),
        (5, "Function Basics", 20, "Lesson", "https://www.theodinproject.com/lessons/foundations-fundamentals-part-3"), # Was Fundamentals Part 3
        (6, "Problem Solving", 10, "Lesson", "https://www.theodinproject.com/lessons/foundations-problem-solving"),
        (7, "Understanding Errors", 10, "Lesson", "https://www.theodinproject.com/lessons/foundations-understanding-errors"),
        (8, "Project: Rock Paper Scissors", 60, "Project", "https://www.theodinproject.com/lessons/foundations-rock-paper-scissors"),
        (9, "Clean Code", 10, "Lesson", "https://www.theodinproject.com/lessons/foundations-clean-code"),
        (10, "Arrays and Loops", 20, "Lesson", "https://www.theodinproject.com/lessons/foundations-fundamentals-part-4"), # Was Fundamentals Part 4
        (11, "DOM Manipulation and Events", 25, "Lesson", "https://www.theodinproject.com/lessons/foundations-dom-manipulation-and-events"),
        (12, "Revisiting Rock Paper Scissors", 20, "Lesson", "https://www.theodinproject.com/lessons/foundations-revisiting-rock-paper-scissors"),
        (13, "Project: Etch-a-Sketch", 70, "Project", "https://www.theodinproject.com/lessons/foundations-etch-a-sketch"),
        (14, "Object Basics", 20, "Lesson", "https://www.theodinproject.com/lessons/foundations-fundamentals-part-5"), # Was Fundamentals Part 5
        (15, "Project: Calculator", 80, "Project", "https://www.theodinproject.com/lessons/foundations-calculator"),
    ]},
    8: {"title": "Conclusion", "lessons": [
        (1, "Choose Your Path Forward", 5, "Lesson", "https://www.theodinproject.com/lessons/foundations-choose-your-path-forward"),
    ]},
}

def populate_data(apps, schema_editor):
    Section = apps.get_model('tracker', 'Section')
    Lesson = apps.get_model('tracker', 'Lesson')
    db_alias = schema_editor.connection.alias

    # --- DELETION OF OLD DATA --- 
    # Get titles from the *new* structure to avoid deleting unrelated sections/lessons if any exist
    new_section_titles = [data['title'] for data in NEW_FOUNDATIONS_COURSE.values()]
    print(f"\nAttempting to delete existing Lessons and Sections matching titles: {new_section_titles}...")
    # Delete lessons first due to foreign key constraints
    deleted_lessons, _ = Lesson.objects.using(db_alias).filter(section__title__in=new_section_titles).delete()
    deleted_sections, _ = Section.objects.using(db_alias).filter(title__in=new_section_titles).delete()
    print(f"Deleted {deleted_lessons} existing lessons and {deleted_sections} existing sections.")
    # --- END DELETION --- 

    print("\nPopulating Sections and Lessons with NEW structure...")
    for section_order, section_data in NEW_FOUNDATIONS_COURSE.items():
        section = Section.objects.using(db_alias).create(
            order=section_order,
            title=section_data['title']
        )
        print(f"  Created Section: {section.title}")

        for lesson_order, title, points, lesson_type, url in section_data['lessons']:
            Lesson.objects.using(db_alias).create(
                section=section,
                order=lesson_order,
                title=title,
                points_value=points,
                lesson_type=lesson_type,
                url=url
            )
    print("NEW Data population complete.")

def delete_data(apps, schema_editor):
    # This function is run if the migration is reversed.
    Section = apps.get_model('tracker', 'Section')
    Lesson = apps.get_model('tracker', 'Lesson')
    db_alias = schema_editor.connection.alias
    
    # Get titles from the structure defined in THIS migration file (NEW_FOUNDATIONS_COURSE)
    section_titles_to_delete = [data['title'] for data in NEW_FOUNDATIONS_COURSE.values()]
    print(f"\nAttempting reverse deletion for sections: {section_titles_to_delete}")
    
    # Delete lessons first
    deleted_lessons, _ = Lesson.objects.using(db_alias).filter(section__title__in=section_titles_to_delete).delete()
    # Then delete sections
    deleted_sections, _ = Section.objects.using(db_alias).filter(title__in=section_titles_to_delete).delete()
    print(f"Reverse deleted {deleted_lessons} lessons and {deleted_sections} sections based on NEW structure.")


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0001_initial'), # Still depends on the initial schema
    ]

    operations = [
        migrations.RunPython(populate_data, reverse_code=delete_data),
    ]
