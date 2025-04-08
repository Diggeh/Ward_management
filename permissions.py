from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from database import db
from models import Permission, RolePermission


def check_permission(permission_name):
    if not current_user.is_authenticated:
        return False

    if current_user.role_id == 1:
        return True

    permission = (
        db.session.query(Permission.id)
        .filter(Permission.permission_name == permission_name)
        .first()
    )

    if not permission:
        return False

    role_permission = (
        db.session.query(RolePermission)
        .filter(
            RolePermission.role_id == current_user.role_id,
            RolePermission.permission_id == permission.id,
        )
        .first()
    )

    return role_permission is not None


def permission_required(permission_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not check_permission(permission_name):
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for("main.dashboard"))
            return f(*args, **kwargs)

        return decorated_function

    return decorator
