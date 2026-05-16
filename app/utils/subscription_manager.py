import json
import os
from copy import deepcopy
from datetime import timedelta
from functools import wraps
from typing import Any

from flask import current_app, jsonify, redirect, request, url_for
from flask_login import current_user


PLAN_ORDER = {"free": 0, "pro": 1, "enterprise": 2}
STATUS_TO_PLAN = {
    "PRO": "pro",
    "ENTERPRISE": "enterprise",
    "VERIFIED": "free",
    "PENDING_PRO": "free",
    "UNVERIFIED": "free",
}
PLAN_TO_STATUS = {
    "free": "VERIFIED",
    "pro": "PRO",
    "enterprise": "ENTERPRISE",
}
# TODO: Enforce these subscription.json keys when matching infrastructure exists:
# ads, support queues/SLA routing, follower-growth analytics, API integrations,
# team seats/SSO, multi-device session registry, and comment-per-day counters.
_PLANS_CACHE: dict[str, Any] | None = None
_LOAD_ERROR: str | None = None


def _fallback_plans() -> dict[str, Any]:
    return {
        "free": {"features": {}, "status_value": "VERIFIED", "price": 0},
        "pro": {"features": {}, "status_value": "PRO", "price": 0},
        "enterprise": {"features": {}, "status_value": "ENTERPRISE", "price": 0},
    }


def _subscription_path() -> str:
    try:
        root_path = current_app.root_path
        base_dir = os.path.abspath(os.path.join(root_path, ".."))
    except RuntimeError:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(base_dir, "subscription.json")


def load_plans(force_reload: bool = False) -> dict[str, Any]:
    global _PLANS_CACHE, _LOAD_ERROR

    if _PLANS_CACHE is not None and not force_reload:
        return _PLANS_CACHE

    try:
        with open(_subscription_path(), "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        _LOAD_ERROR = str(exc)
        _PLANS_CACHE = _fallback_plans()
        return _PLANS_CACHE

    plans = {
        key: value
        for key, value in data.items()
        if isinstance(value, dict) and isinstance(value.get("features"), dict)
    }

    if "free" not in plans:
        plans = _fallback_plans()
        _LOAD_ERROR = "subscription.json does not define a usable free plan"
    else:
        for key, fallback in _fallback_plans().items():
            plans.setdefault(key, fallback)
        _LOAD_ERROR = None

    _PLANS_CACHE = plans
    return _PLANS_CACHE


def get_subscription_error() -> str | None:
    load_plans()
    return _LOAD_ERROR


def normalize_plan(plan: str | None) -> str:
    normalized = (plan or "free").strip().lower()
    return normalized if normalized in load_plans() else "free"


def plan_from_status(status: str | None) -> str:
    return normalize_plan(STATUS_TO_PLAN.get((status or "").upper(), "free"))


def status_for_plan(plan: str | None) -> str:
    normalized = normalize_plan(plan)
    configured = load_plans().get(normalized, {}).get("status_value")
    return (configured or PLAN_TO_STATUS.get(normalized) or "VERIFIED").upper()


def get_plan(user: Any = None) -> str:
    if user is None:
        try:
            user = current_user
        except RuntimeError:
            return "free"

    if not user or not getattr(user, "is_authenticated", False):
        return "free"

    explicit_plan = getattr(user, "_subscription_plan_override", None)
    if explicit_plan:
        return normalize_plan(explicit_plan)

    return plan_from_status(getattr(user, "status", None))


def get_plan_config(user: Any = None) -> dict[str, Any]:
    return deepcopy(load_plans().get(get_plan(user), load_plans()["free"]))


def get_feature(user: Any, section: str, key: str, default: Any = None) -> Any:
    plan = get_plan_config(user)
    features = plan.get("features", {})
    section_data = features.get(section, {})
    if not isinstance(section_data, dict):
        return default
    return section_data.get(key, default)


def has_feature(user: Any, section: str, key: str) -> bool:
    return bool(get_feature(user, section, key, False))


def get_limit(user: Any, section: str, key: str, default: Any = None) -> Any:
    value = get_feature(user, section, key, default)
    return default if value is None else value


def is_unlimited(value: Any) -> bool:
    return value == -1


def limit_response(message: str, status_code: int = 403):
    if request.accept_mimetypes.accept_json or request.is_json:
        return jsonify({"status": "error", "message": message}), status_code
    return message, status_code


def plan_rank(plan: str | None) -> int:
    return PLAN_ORDER.get(normalize_plan(plan), 0)


def user_has_plan(user: Any, required_plan: str) -> bool:
    return plan_rank(get_plan(user)) >= plan_rank(required_plan)


def plan_required(required_plan: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if not user_has_plan(current_user, required_plan):
                return limit_response(f"{required_plan.title()} plan required.", 403)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def feature_required(section: str, key: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if not has_feature(current_user, section, key):
                return limit_response("Your plan does not include this feature.", 403)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def session_lifetime_for(user: Any) -> timedelta:
    days = get_limit(user, "auth", "session_lifetime_days", 1)
    try:
        days = int(days)
    except (TypeError, ValueError):
        days = 1
    return timedelta(days=max(days, 1))
