from functools import wraps

from flask import redirect
from flask_login import current_user


def annonymous(f):
    @wraps(f)
    def decorate(*args, **kwrags):
        if current_user.is_authenticated:
            return redirect('/')
        return f(*args, **kwrags)

    return decorate