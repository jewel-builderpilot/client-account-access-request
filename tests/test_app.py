"""Smoke tests — run without real Supabase/Gmail connections."""
import json
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def app():
    import os
    os.environ.setdefault("FLASK_ENV", "testing")
    os.environ.setdefault("SECRET_KEY", "test-secret")
    os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
    os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-key")
    os.environ.setdefault("GMAIL_CLIENT_ID", "test-client-id")
    os.environ.setdefault("GMAIL_CLIENT_SECRET", "test-secret")
    os.environ.setdefault("GMAIL_REFRESH_TOKEN", "test-refresh-token")
    os.environ.setdefault("GMAIL_SENDER_EMAIL", "test@gmail.com")
    os.environ.setdefault("WTF_CSRF_ENABLED", "False")

    from app import create_app
    application = create_app("development")
    application.config["TESTING"] = True
    application.config["WTF_CSRF_ENABLED"] = False
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def test_form_page_loads(client):
    resp = client.get("/form")
    assert resp.status_code == 200
    assert b"Business Information" in resp.data


def test_form_redirect_from_root(client):
    resp = client.get("/")
    assert resp.status_code in (301, 302)


def test_success_page_loads(client):
    resp = client.get("/form/success")
    assert resp.status_code == 200
    assert b"all set" in resp.data.lower()


def test_admin_login_page_loads(client):
    resp = client.get("/admin/login")
    assert resp.status_code == 200
    assert b"Admin Login" in resp.data


def test_admin_dashboard_requires_auth(client):
    resp = client.get("/admin/")
    assert resp.status_code in (302, 401)


def test_form_submit_validation_error(client):
    """Submitting an empty form returns 422 with error JSON."""
    with patch("app.routes.client.create_client_record") as mock_create, \
         patch("app.routes.client.process_access_requests"):
        resp = client.post("/form/submit", data={})
        assert resp.status_code == 422
        body = json.loads(resp.data)
        assert "errors" in body
        assert "company_name" in body["errors"]


def test_form_submit_success(client):
    """A complete form submission redirects to /form/success."""
    valid_data = {
        "company_name": "Acme Roofing",
        "owner_name": "Jane Smith",
        "phone": "555-1234",
        "best_email": "jane@acme.com",
        "website": "https://acme.com",
        "city_state": "Austin, TX",
        "services_offered": "Roofing",
        "top_revenue_service": "Roof replacement",
        "more_leads_service": "Roof replacement",
        "avg_project_size": "$10,000",
        "service_area": "Austin Metro",
        "ideal_customer": "Homeowners",
        "lead_receive_method": "phone_calls",
        "qualified_lead": "Homeowner with roof damage",
        "primary_goal": "Get 20 leads/month",
        "success_90_days": "Consistent pipeline",
        "leads_per_month": "20",
        "grow_or_steady": "grow_scale",
        "monthly_ad_budget": "1k_2500",
        "ran_ads_before": "no_first_time",
        "ads_live_when": "asap",
        "approve_ad_copy": "yes_review_everything",
    }

    mock_client_row = {"id": "test-uuid-123", "company_name": "Acme Roofing"}

    with patch("app.routes.client.create_client_record", return_value=mock_client_row), \
         patch("app.routes.client.log_event"), \
         patch("app.routes.client.process_access_requests"):
        resp = client.post("/form/submit", data=valid_data)
        assert resp.status_code in (302, 200)


def test_access_requests_process(app):
    """Access request service creates DB rows and attempts email for eligible platforms."""
    mock_client_id = "test-uuid"
    form_data = {
        "best_email": "jane@acme.com",
        "owner_name": "Jane Smith",
        "company_name": "Acme",
        "platform_google_ads": "has_account",
        "platform_gtm": "not_sure",
        "platform_ga4": "doesnt_have",
        "platform_gbp": "needs_created",
        "platform_gsc": "doesnt_have",
        "platform_meta": "has_account",
        "platform_facebook_page": "doesnt_have",
    }

    mock_row = {"id": "req-uuid"}

    with app.app_context():
        with patch("app.services.access_requests.create_access_request", return_value=mock_row), \
             patch("app.services.access_requests.update_access_request"), \
             patch("app.services.access_requests.log_event"), \
             patch("app.services.access_requests.get_setting", return_value=""), \
             patch("app.services.access_requests.send_email", return_value=True) as mock_send:
            from app.services.access_requests import process_access_requests
            process_access_requests(mock_client_id, form_data)
            # Should send 2 emails: one Google consolidated, one Meta
            assert mock_send.call_count == 2
