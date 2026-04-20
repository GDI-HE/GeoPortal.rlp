from django import template

register = template.Library()


def bold(value, arg):
    """ Makes a word bold for rendering

    Inserts a span tag with appropriate class, such that the term will be bold after rendering.

    Args:
        value:
        arg: The word to be "bolded"
    Returns:
        The modified string
    """
    arg_lower = arg.lower()
    arg_upper = arg.upper()
    if arg in value or arg_lower in value or arg_upper in value:
        value = value.replace(arg, '<span class="searchmatch">' + arg + '</span>')
        value = value.replace(arg_lower, '<span class="searchmatch">' + arg_lower + '</span>')
        value = value.replace(arg_upper, '<span class="searchmatch">' + arg_upper + '</span>')
    return value


def contains(value, arg):
    """ Checks insensitive if a substring is found inside a string

    Args:
        value (str): The string
        arg (str): The substring
    Returns:
         bool: True if string contains substring, False otherwise
    """
    value = value.upper()
    arg = arg.upper()
    if arg in value:
        return True
    return False


def remove_translation_suffix(value, arg):
    """ Removes the '/de' component from page titles

    Args:
        value:
        arg:
    Returns:
         str: The title without a translation suffix
    """
    if arg in value:
        return value.replace("/" + arg, "")
    return value


def get_item(value, arg):
    """ Gets an item from a dictionary using a key
    
    Args:
        value (dict): The dictionary
        arg (str): The key to retrieve
    Returns:
        The value for the key, or empty string if not found
    """
    try:
        return value.get(arg, "")
    except (AttributeError, TypeError):
        return ""


register.filter("drop_translation", remove_translation_suffix)
register.filter("bold", bold)
register.filter("contains", contains)
register.filter("get_item", get_item)
