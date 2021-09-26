"""
Utility functions used during user authentication.
"""

import random
import re
from urllib.parse import urlparse  # pylint: disable=import-error
from uuid import uuid4  # lint-amnesty, pylint: disable=unused-import

from django.conf import settings
from django.utils import http
from oauth2_provider.models import Application

from common.djangoapps.student.models import username_exists_or_retired
from openedx.core.djangoapps.user_api.accounts import USERNAME_MAX_LENGTH


def is_safe_login_or_logout_redirect(redirect_to, request_host, dot_client_id, require_https):
    """
    Determine if the given redirect URL/path is safe for redirection.

    Arguments:
        redirect_to (str):
            The URL in question.
        request_host (str):
            Originating hostname of the request.
            This is always considered an acceptable redirect target.
        dot_client_id (str|None):
            ID of Django OAuth Toolkit client.
            It is acceptable to redirect to any of the DOT client's redirct URIs.
            This argument is ignored if it is None.
        require_https (str):
            Whether HTTPs should be required in the redirect URL.

    Returns: bool
    """
    login_redirect_whitelist = set(getattr(settings, 'LOGIN_REDIRECT_WHITELIST', []))
    login_redirect_whitelist.add(request_host)

    # Allow OAuth2 clients to redirect back to their site after logout.
    if dot_client_id:
        application = Application.objects.get(client_id=dot_client_id)
        if redirect_to in application.redirect_uris:
            login_redirect_whitelist.add(urlparse(redirect_to).netloc)

    is_safe_url = http.is_safe_url(
        redirect_to, allowed_hosts=login_redirect_whitelist, require_https=require_https
    )
    return is_safe_url


def is_registration_api_v1(request):
    """
    Checks if registration api is v1
    :param request:
    :return: Bool
    """
    return 'v1' in request.get_full_path() and 'register' not in request.get_full_path()


def remove_special_characters_from_name(name):
    return "".join(re.findall("[\w-]+", name))

def generate_username_suggestions(name):
    """ Generate 3 available username suggestions """
    username_suggestions = []
    max_length = USERNAME_MAX_LENGTH
    names =  name.split(' ')

    first_name = remove_special_characters_from_name(names[0].lower())
    last_name = remove_special_characters_from_name(names[-1].lower())


    if first_name != last_name:

        # username combination of first and last name
        suggestion = f'{first_name}{last_name}'[:max_length]
        if not username_exists_or_retired(suggestion):
            username_suggestions.append(suggestion)

        # username is combination of first letter of first name and last name
        suggestion = f'{first_name[0]}-{last_name}'[:max_length]
        if not username_exists_or_retired(suggestion):
            username_suggestions.append(suggestion)


    short_username = first_name[:max_length - 6] if max_length is not None else first_name
    short_username = short_username.replace('_', '').replace('-', '')

    int_ranges = [
        {'min': 0, 'max': 9},
        {'min': 10, 'max': 99},
        {'min': 100, 'max': 999},
        {'min': 1000, 'max': 99999},
    ]
    for int_range in int_ranges:
        for _ in range(10):
            random_int = random.randint(int_range['min'], int_range['max'])
            suggestion = f'{short_username}_{random_int}'
            if not username_exists_or_retired(suggestion):
                username_suggestions.append(suggestion)
                break

        if len(username_suggestions) == 3:
            break

    return username_suggestions
