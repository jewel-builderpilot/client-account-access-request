"""
Processes account access requests after a client submits the intake form.

Logic:
- For each platform in Step 5 where client_status is 'has_account' or 'not_sure',
  an access_requests row is created and an email is triggered.
- Google platforms (Ads, GTM, GA4, GBP, GSC) → one consolidated email to the client.
- Meta platforms (Meta BM, Facebook Page) → one separate email to the client.
"""
from datetime import datetime, timezone
from flask import current_app
from ..models import create_access_request, update_access_request, log_event, get_setting
from .email import send_email

GOOGLE_PLATFORMS = ["google_ads", "gtm", "ga4", "gbp", "gsc"]
META_PLATFORMS = ["meta", "facebook_page"]

PLATFORM_LABELS = {
    "google_ads": "Google Ads",
    "gtm": "Google Tag Manager",
    "ga4": "Google Analytics (GA4)",
    "gbp": "Google Business Profile",
    "gsc": "Google Search Console",
    "meta": "Meta Business Manager",
    "facebook_page": "Facebook Page",
}

NEEDS_ACTION_STATUSES = {"has_account", "not_sure"}


def process_access_requests(client_id: str, form_data: dict) -> None:
    google_needed: list[dict] = []
    meta_needed: list[dict] = []

    all_platforms = GOOGLE_PLATFORMS + META_PLATFORMS
    for platform in all_platforms:
        raw_status = form_data.get(f"platform_{platform}", "not_sure")
        row = create_access_request({
            "client_id": client_id,
            "platform": platform,
            "client_status": raw_status,
            "request_status": "pending",
        })

        if raw_status in NEEDS_ACTION_STATUSES:
            entry = {"id": row["id"], "platform": platform, "label": PLATFORM_LABELS[platform]}
            if platform in GOOGLE_PLATFORMS:
                google_needed.append(entry)
            else:
                meta_needed.append(entry)

    client_email = form_data.get("best_email", "")
    owner_name = form_data.get("owner_name", "")
    company_name = form_data.get("company_name", "")
    ads_manager_id = get_setting("agency_ads_manager_id")
    meta_bm_id = get_setting("agency_meta_bm_id")
    from_name = get_setting("email_from_name")
    reply_to = get_setting("email_reply_to")
    google_subject = get_setting("google_email_subject") or f"Action Required: Grant Account Access — {company_name}"
    google_intro = get_setting("google_email_intro")
    meta_subject = get_setting("meta_email_subject") or f"Action Required: Grant Meta Account Access — {company_name}"
    meta_intro = get_setting("meta_email_intro")

    if google_needed and client_email:
        html = _render_google_email(owner_name, company_name, google_needed, ads_manager_id, google_intro)
        sent = send_email(client_email, google_subject, html, from_name=from_name, reply_to=reply_to)
        if sent:
            now = datetime.now(timezone.utc).isoformat()
            for entry in google_needed:
                update_access_request(entry["id"], {
                    "request_status": "email_sent",
                    "email_sent_at": now,
                })
            log_event(client_id, "access_email_sent", f"Google access email sent to {client_email}")

    if meta_needed and client_email:
        html = _render_meta_email(owner_name, company_name, meta_needed, meta_bm_id, meta_intro)
        sent = send_email(client_email, meta_subject, html, from_name=from_name, reply_to=reply_to)
        if sent:
            now = datetime.now(timezone.utc).isoformat()
            for entry in meta_needed:
                update_access_request(entry["id"], {
                    "request_status": "email_sent",
                    "email_sent_at": now,
                })
            log_event(client_id, "access_email_sent", f"Meta access email sent to {client_email}")


DEFAULT_GOOGLE_INTRO = (
    "As part of your onboarding, we need admin/manager access to the following Google platforms "
    "so we can start setting up and managing your campaigns:"
)

DEFAULT_META_INTRO = (
    "We need access to the following Meta platforms to manage your advertising:"
)


def _render_google_email(
    owner_name: str, company_name: str, platforms: list[dict], manager_id: str, intro: str = ""
) -> str:
    platform_list = "".join(
        f"<li><strong>{p['label']}</strong></li>" for p in platforms
    )
    step_blocks = _google_step_instructions(platforms, manager_id)
    body_intro = intro.strip() if intro.strip() else DEFAULT_GOOGLE_INTRO
    return f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; padding: 24px;">
  <h2 style="color: #1a73e8;">Action Required: Grant Google Account Access</h2>
  <p>Hi {owner_name},</p>
  <p>{body_intro}</p>
  <ul>{platform_list}</ul>
  <p>Please follow the steps below for each platform:</p>
  {step_blocks}
  <p>
    Once you've granted access, we'll receive a notification and get started right away.
    If you run into any issues, just reply to this email and we'll walk you through it.
  </p>
  <p>Thank you!</p>
</body>
</html>
"""


def _google_step_instructions(platforms: list[dict], manager_id: str) -> str:
    blocks = []
    for p in platforms:
        key = p["platform"]
        label = p["label"]

        if key == "google_ads":
            id_line = (
                f"enter our Manager ID: <strong>{manager_id}</strong>"
                if manager_id
                else "enter the Manager ID we provide you"
            )
            blocks.append(f"""
<h3 style="color:#1a73e8">{label}</h3>
<ol>
  <li>Sign in to your Google Ads account at <a href="https://ads.google.com">ads.google.com</a>.</li>
  <li>Click the <strong>Tools &amp; Settings</strong> icon (wrench) → <strong>Access and security</strong>.</li>
  <li>Click the <strong>+</strong> button, {id_line}, and select <strong>Admin</strong> access.</li>
  <li>Click <strong>Send invitation</strong>.</li>
</ol>
""")
        elif key == "gtm":
            blocks.append(f"""
<h3 style="color:#1a73e8">{label}</h3>
<ol>
  <li>Go to <a href="https://tagmanager.google.com">tagmanager.google.com</a>.</li>
  <li>Select your container → click the <strong>Admin</strong> tab.</li>
  <li>Under <strong>Container</strong>, click <strong>User Management</strong> → <strong>+</strong>.</li>
  <li>Enter our email <strong>{_agency_email()}</strong>, select <strong>Edit</strong> permission, and save.</li>
</ol>
""")
        elif key == "ga4":
            blocks.append(f"""
<h3 style="color:#1a73e8">{label}</h3>
<ol>
  <li>Go to <a href="https://analytics.google.com">analytics.google.com</a>.</li>
  <li>Click <strong>Admin</strong> (bottom-left gear icon).</li>
  <li>Under <strong>Account</strong>, click <strong>Account Access Management</strong> → <strong>+</strong>.</li>
  <li>Enter our email <strong>{_agency_email()}</strong>, select <strong>Editor</strong>, and click <strong>Add</strong>.</li>
</ol>
""")
        elif key == "gbp":
            blocks.append(f"""
<h3 style="color:#1a73e8">{label}</h3>
<ol>
  <li>Go to <a href="https://business.google.com">business.google.com</a>.</li>
  <li>Select your business → click <strong>Business Profile settings</strong> → <strong>Managers</strong>.</li>
  <li>Click <strong>Add</strong>, enter our email <strong>{_agency_email()}</strong>, select <strong>Manager</strong>, and confirm.</li>
</ol>
""")
        elif key == "gsc":
            blocks.append(f"""
<h3 style="color:#1a73e8">{label}</h3>
<ol>
  <li>Go to <a href="https://search.google.com/search-console">search.google.com/search-console</a>.</li>
  <li>Select your property → click <strong>Settings</strong> → <strong>Users and permissions</strong>.</li>
  <li>Click <strong>Add User</strong>, enter our email <strong>{_agency_email()}</strong>, select <strong>Full</strong>, and save.</li>
</ol>
""")
    return "\n".join(blocks)


def _render_meta_email(
    owner_name: str, company_name: str, platforms: list[dict], meta_bm_id: str, intro: str = ""
) -> str:
    platform_list = "".join(
        f"<li><strong>{p['label']}</strong></li>" for p in platforms
    )
    step_blocks = _meta_step_instructions(platforms, meta_bm_id)
    body_intro = intro.strip() if intro.strip() else DEFAULT_META_INTRO
    return f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; padding: 24px;">
  <h2 style="color: #1877f2;">Action Required: Grant Meta Account Access</h2>
  <p>Hi {owner_name},</p>
  <p>{body_intro}</p>
  <ul>{platform_list}</ul>
  {step_blocks}
  <p>
    If you need help with any of these steps, just reply to this email and we'll assist you directly.
  </p>
  <p>Thank you!</p>
</body>
</html>
"""


def _meta_step_instructions(platforms: list[dict], meta_bm_id: str) -> str:
    blocks = []
    for p in platforms:
        key = p["platform"]
        label = p["label"]

        if key == "meta":
            bm_line = (
                f"Enter our Business Manager ID: <strong>{meta_bm_id}</strong>"
                if meta_bm_id
                else "Enter the Business Manager ID we provide you"
            )
            blocks.append(f"""
<h3 style="color:#1877f2">{label}</h3>
<ol>
  <li>Go to <a href="https://business.facebook.com/settings">business.facebook.com/settings</a>.</li>
  <li>In the left menu, click <strong>Partners</strong>.</li>
  <li>Click <strong>Add</strong> → <strong>Give a partner access to your assets</strong>.</li>
  <li>{bm_line} and click <strong>Next</strong>.</li>
  <li>Grant access to your ad accounts, pixel, and pages as prompted, then click <strong>Save</strong>.</li>
</ol>
""")
        elif key == "facebook_page":
            blocks.append(f"""
<h3 style="color:#1877f2">{label}</h3>
<ol>
  <li>Go to your Facebook Page and click <strong>Settings</strong>.</li>
  <li>Click <strong>Page Roles</strong> (or <strong>New Pages Experience</strong> → <strong>Page Access</strong>).</li>
  <li>Under <strong>Assign a New Page Role</strong>, enter our email <strong>{_agency_email()}</strong>.</li>
  <li>Select <strong>Editor</strong> and click <strong>Add</strong>. Confirm with your password.</li>
</ol>
""")
    return "\n".join(blocks)


def _agency_email() -> str:
    return current_app.config.get("GMAIL_SENDER_EMAIL", "")
