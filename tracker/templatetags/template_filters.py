from django import template

register = template.Library()

@register.filter(name='attr')
def attr(field, attrs):
    """Template filter to add HTML attributes to a form field widget."""
    # attrs should be a string like "name:value,name2:value2"
    attributes = {}
    for pair in attrs.split(','):
        try:
            name, value = pair.split(':', 1)
            attributes[name.strip()] = value.strip()
        except ValueError:
            # Handle cases where the split might fail (e.g., empty string)
            pass
    return field.as_widget(attrs=attributes) 