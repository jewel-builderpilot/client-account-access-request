"""Supabase query helpers. All DB access goes through these functions."""
from flask import current_app
from supabase import create_client, Client


def get_db() -> Client:
    return create_client(
        current_app.config["SUPABASE_URL"],
        current_app.config["SUPABASE_SERVICE_KEY"],
    )


# ---------- clients ----------

def create_client_record(data: dict) -> dict:
    db = get_db()
    result = db.table("clients").insert(data).execute()
    return result.data[0]


def get_all_clients() -> list:
    db = get_db()
    result = (
        db.table("clients")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


def get_client(client_id: str) -> dict | None:
    db = get_db()
    result = db.table("clients").select("*").eq("id", client_id).single().execute()
    return result.data


def update_client_status(client_id: str, status: str) -> None:
    db = get_db()
    db.table("clients").update({"status": status}).eq("id", client_id).execute()


# ---------- access_requests ----------

def create_access_request(data: dict) -> dict:
    db = get_db()
    result = db.table("access_requests").insert(data).execute()
    return result.data[0]


def get_access_requests_for_client(client_id: str) -> list:
    db = get_db()
    result = (
        db.table("access_requests")
        .select("*")
        .eq("client_id", client_id)
        .execute()
    )
    return result.data


def update_access_request(request_id: str, data: dict) -> None:
    db = get_db()
    db.table("access_requests").update(data).eq("id", request_id).execute()


# ---------- onboarding_logs ----------

def log_event(client_id: str, event: str, detail: str = "") -> None:
    db = get_db()
    db.table("onboarding_logs").insert(
        {"client_id": client_id, "event": event, "detail": detail}
    ).execute()


def get_logs_for_client(client_id: str) -> list:
    db = get_db()
    result = (
        db.table("onboarding_logs")
        .select("*")
        .eq("client_id", client_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


# ---------- settings ----------

def get_setting(key: str) -> str:
    db = get_db()
    result = db.table("settings").select("value").eq("key", key).limit(1).execute()
    return result.data[0]["value"] if result.data else ""


def set_setting(key: str, value: str) -> None:
    db = get_db()
    db.table("settings").upsert({"key": key, "value": value}).execute()


# ---------- admin_users ----------

def get_all_admins() -> list:
    db = get_db()
    result = db.table("admin_users").select("id, email, created_at").order("created_at").execute()
    return result.data


def delete_admin_user(user_id: str) -> None:
    db = get_db()
    db.table("admin_users").delete().eq("id", user_id).execute()


def get_admin_by_email(email: str) -> dict | None:
    db = get_db()
    result = (
        db.table("admin_users")
        .select("*")
        .eq("email", email)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def create_admin_user(email: str, password_hash: str) -> dict:
    db = get_db()
    result = (
        db.table("admin_users")
        .insert({"email": email, "password_hash": password_hash})
        .execute()
    )
    return result.data[0]
