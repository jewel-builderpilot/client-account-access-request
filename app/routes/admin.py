import json
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from ..auth import AdminUser
from ..models import (
    get_all_clients, get_client, update_client_status,
    get_access_requests_for_client, update_access_request,
    get_logs_for_client, log_event,
    get_setting, set_setting,
    get_all_admins, delete_admin_user, get_admin_by_email,
)

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = AdminUser.authenticate(email, password)
        if user:
            login_user(user)
            return redirect(url_for("admin.dashboard"))
        flash("Invalid email or password.", "danger")

    return render_template("admin/login.html")


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@login_required
def dashboard():
    clients = get_all_clients()
    # Attach access request completion % to each client
    for client in clients:
        reqs = get_access_requests_for_client(client["id"])
        if reqs:
            granted = sum(1 for r in reqs if r["request_status"] == "access_granted")
            client["access_pct"] = round(granted / len(reqs) * 100)
        else:
            client["access_pct"] = 0
    return render_template("admin/dashboard.html", clients=clients)


@admin_bp.route("/client/<client_id>")
@login_required
def client_detail(client_id):
    client = get_client(client_id)
    if not client:
        flash("Client not found.", "danger")
        return redirect(url_for("admin.dashboard"))

    access_reqs = get_access_requests_for_client(client_id)
    logs = get_logs_for_client(client_id)

    # Parse step_data JSON for display
    step_data = {}
    raw = client.get("step_data")
    if raw:
        try:
            step_data = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            pass

    return render_template(
        "admin/client_detail.html",
        client=client,
        access_reqs=access_reqs,
        logs=logs,
        step_data=step_data,
    )


@admin_bp.route("/access-request/<request_id>/update", methods=["POST"])
@login_required
def update_request(request_id):
    new_status = request.form.get("status")
    client_id = request.form.get("client_id")
    allowed = {"pending", "email_sent", "access_granted", "not_needed"}
    if new_status not in allowed:
        flash("Invalid status.", "danger")
        return redirect(url_for("admin.client_detail", client_id=client_id))

    data = {"request_status": new_status}
    if new_status == "access_granted":
        data["granted_at"] = datetime.now(timezone.utc).isoformat()

    update_access_request(request_id, data)
    log_event(client_id, "access_status_updated", f"Request {request_id} → {new_status}")
    flash("Access request updated.", "success")
    return redirect(url_for("admin.client_detail", client_id=client_id))


@admin_bp.route("/client/<client_id>/status", methods=["POST"])
@login_required
def update_status(client_id):
    new_status = request.form.get("status")
    allowed = {"pending", "active", "complete"}
    if new_status not in allowed:
        flash("Invalid status.", "danger")
    else:
        update_client_status(client_id, new_status)
        log_event(client_id, "status_updated", f"Client status → {new_status}")
        flash("Client status updated.", "success")
    return redirect(url_for("admin.client_detail", client_id=client_id))


SETTINGS_KEYS = [
    "agency_ads_manager_id", "agency_meta_bm_id",
    "email_from_name", "email_reply_to",
    "google_email_subject", "google_email_intro",
    "meta_email_subject", "meta_email_intro",
]


@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        for key in SETTINGS_KEYS:
            set_setting(key, request.form.get(key, "").strip())
        flash("Settings saved.", "success")
        return redirect(url_for("admin.settings"))

    return render_template("admin/settings.html",
        s={key: get_setting(key) for key in SETTINGS_KEYS},
        admins=get_all_admins(),
        current_user_id=current_user.id,
    )


@admin_bp.route("/settings/admin-users/add", methods=["POST"])
@login_required
def add_admin_user():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    if not email or not password:
        flash("Email and password are required.", "danger")
        return redirect(url_for("admin.settings"))
    if password != confirm:
        flash("Passwords do not match.", "danger")
        return redirect(url_for("admin.settings"))
    if len(password) < 8:
        flash("Password must be at least 8 characters.", "danger")
        return redirect(url_for("admin.settings"))
    if get_admin_by_email(email):
        flash(f"{email} is already an admin.", "danger")
        return redirect(url_for("admin.settings"))

    AdminUser.create(email, password)
    flash(f"Admin user {email} added.", "success")
    return redirect(url_for("admin.settings"))


@admin_bp.route("/settings/admin-users/<user_id>/delete", methods=["POST"])
@login_required
def remove_admin_user(user_id):
    if user_id == current_user.id:
        flash("You cannot remove your own account.", "danger")
        return redirect(url_for("admin.settings"))
    delete_admin_user(user_id)
    flash("Admin user removed.", "success")
    return redirect(url_for("admin.settings"))


@admin_bp.route("/client/<client_id>/kickoff")
@login_required
def kickoff_brief(client_id):
    client = get_client(client_id)
    if not client:
        flash("Client not found.", "danger")
        return redirect(url_for("admin.dashboard"))

    step_data = {}
    raw = client.get("step_data")
    if raw:
        try:
            step_data = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            pass

    access_reqs = get_access_requests_for_client(client_id)
    return render_template(
        "admin/kickoff_brief.html",
        client=client,
        step_data=step_data,
        access_reqs=access_reqs,
    )
