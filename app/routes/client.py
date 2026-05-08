import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timezone
from ..models import create_client_record, log_event, get_access_request_by_token, update_access_request
from ..services.access_requests import process_access_requests

client_bp = Blueprint("client", __name__)

REQUIRED_FIELDS = [
    "company_name", "owner_name", "phone", "best_email", "website",
    "city_state", "services_offered", "top_revenue_service",
    "more_leads_service", "avg_project_size", "service_area",
    "ideal_customer", "lead_receive_method", "qualified_lead",
    "primary_goal", "success_90_days", "leads_per_month",
    "grow_or_steady", "monthly_ad_budget", "ran_ads_before",
    "ads_live_when", "approve_ad_copy",
]


@client_bp.route("/")
def index():
    return redirect(url_for("client.form"))


@client_bp.route("/form")
def form():
    return render_template("client/form.html")


@client_bp.route("/form/submit", methods=["POST"])
def submit_form():
    data = request.form.to_dict(flat=False)
    # Flatten single-value lists; keep multi-value as lists
    flat = {}
    for key, val in data.items():
        flat[key] = val if len(val) > 1 else val[0]

    errors = _validate(flat)
    if errors:
        return jsonify({"ok": False, "errors": errors}), 422

    client_row = {
        "status": "pending",
        "company_name": flat.get("company_name", "").strip(),
        "owner_name": flat.get("owner_name", "").strip(),
        "phone": flat.get("phone", "").strip(),
        "best_email": flat.get("best_email", "").strip(),
        "lead_notif_email": flat.get("lead_notif_email", "").strip(),
        "website": flat.get("website", "").strip(),
        "city_state": flat.get("city_state", "").strip(),
        "years_in_business": flat.get("years_in_business", "").strip(),
        "licensed_bonded_insured": flat.get("licensed_bonded_insured", ""),
        "tagline": flat.get("tagline", "").strip(),
        "company_values": flat.get("company_values", "").strip(),
        "step_data": json.dumps(flat),
    }

    client = create_client_record(client_row)
    log_event(client["id"], "form_submitted", f"Form submitted by {client_row['owner_name']}")

    process_access_requests(client["id"], flat)

    return redirect(url_for("client.success"))


@client_bp.route("/form/success")
def success():
    return render_template("client/success.html")


@client_bp.route("/confirm-access/<token>")
def confirm_access(token):
    req = get_access_request_by_token(token)
    if not req:
        return render_template("client/confirm_access.html", status="invalid")
    if req["request_status"] == "access_granted":
        return render_template("client/confirm_access.html", status="already_confirmed",
                               platform=req["platform"])
    now = datetime.now(timezone.utc).isoformat()
    update_access_request(req["id"], {
        "request_status": "access_granted",
        "granted_at": now,
    })
    log_event(req["client_id"], "access_granted",
              f"Client confirmed access for {req['platform']}")
    return render_template("client/confirm_access.html", status="confirmed",
                           platform=req["platform"])


def _validate(data: dict) -> dict:
    errors = {}
    for field in REQUIRED_FIELDS:
        val = data.get(field)
        if not val or (isinstance(val, str) and not val.strip()):
            errors[field] = "This field is required."
    email = data.get("best_email", "")
    if email and "@" not in email:
        errors["best_email"] = "Enter a valid email address."
    return errors
