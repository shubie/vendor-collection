from io import BytesIO

from app import UPLOAD_ROOT, VendorApplication, app, db


def build_payload():
    return {
        "trade_name": "Test Vendor",
        "trade_number": "TR-12345",
        "services_applying": "SecurePath Basic - Dubai",
        "owner_email_id": "owner@test.com",
        "first_name": "Jane",
        "last_name": "Doe",
        "email_address": "ops@company.com",
        "contact_number": "+971500000000",
        "emirates_id": "784-2024-123456-7",
        "street": "Building 1 Street",
        "country": "United Arab Emirates",
        "state_emirate": "Dubai",
        "city": "Dubai",
        "year_company_establishment_uae": "2012",
        "experience_gps_tracking_years": "8",
        "running_vehicles_installed_uae": "1500",
        "running_vehicles_installed_outside_uae": "400",
        "number_of_engineers": "45",
        "number_of_technicians": "70",
        "po_box": "12345",
        "makani_number": "MK001",
        "trade_license": (BytesIO(b"pdf"), "trade_license.pdf"),
        "trn_certificate": (BytesIO(b"pdf"), "trn_certificate.pdf"),
        "tdra_certificate": (BytesIO(b"pdf"), "tdra_certificate.pdf"),
        "sira_certificate": (BytesIO(b"pdf"), "sira_certificate.pdf"),
        "authorized_person_emirates_id_file": (BytesIO(b"pdf"), "authorized_id.pdf"),
        "company_profile": (BytesIO(b"docx"), "company_profile.docx"),
        "vendor_logo": (BytesIO(b"img"), "logo.jpg"),
    }


with app.app_context():
    db.drop_all()
    db.create_all()

client = app.test_client()

valid_response = client.post("/submit", data=build_payload(), content_type="multipart/form-data", follow_redirects=True)
assert valid_response.status_code == 200

invalid_trade_number = build_payload()
invalid_trade_number["trade_number"] = "TRADE-NUMBER-TOO-LONG-123"
invalid_trade_response = client.post("/submit", data=invalid_trade_number, content_type="multipart/form-data", follow_redirects=True)
assert invalid_trade_response.status_code == 200
assert b"Trade Number must be 1-20 characters" in invalid_trade_response.data

invalid_emirates_id = build_payload()
invalid_emirates_id["emirates_id"] = "123-1990-9612342-1"
invalid_emirates_id_response = client.post("/submit", data=invalid_emirates_id, content_type="multipart/form-data", follow_redirects=True)
assert invalid_emirates_id_response.status_code == 200
assert b"Emirates ID format is invalid" in invalid_emirates_id_response.data

invalid_authorised_email = build_payload()
invalid_authorised_email["email_address"] = "agent@gmail.com"
invalid_authorised_email_response = client.post("/submit", data=invalid_authorised_email, content_type="multipart/form-data", follow_redirects=True)
assert invalid_authorised_email_response.status_code == 200
assert b"Authorised Email must use company domain" in invalid_authorised_email_response.data

with app.app_context():
    applications = VendorApplication.query.all()
    assert len(applications) == 1
    saved = applications[0]
    assert (UPLOAD_ROOT / saved.trade_license).exists()

admin_response = client.get("/admin/applications")
assert admin_response.status_code == 200

csv_export_response = client.get("/admin/applications/export/csv")
assert csv_export_response.status_code == 200
assert b"Vendor ID" in csv_export_response.data

excel_export_response = client.get("/admin/applications/export/excel")
assert excel_export_response.status_code == 200
assert b"Vendor ID" in excel_export_response.data
print("SMOKE_OK")
