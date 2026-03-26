from datetime import datetime
from pathlib import Path
import csv
import io
import os
import re
import uuid

from flask import Flask, Response, abort, flash, redirect, render_template, request, send_from_directory, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
UPLOAD_ROOT = BASE_DIR / "uploads"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", uuid.uuid4().hex)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{INSTANCE_DIR / 'vendor_portal.db'}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024

db = SQLAlchemy(app)

TEXT_FIELDS = [
    "trade_name",
    "trade_number",
    "services_applying",
    "owner_email_id",
    "first_name",
    "last_name",
    "email_address",
    "contact_number",
    "emirates_id",
    "street",
    "country",
    "state_emirate",
    "city",
    "po_box",
    "makani_number",
]
NUMBER_FIELDS = [
    "year_company_establishment_uae",
    "experience_gps_tracking_years",
    "running_vehicles_installed_uae",
    "running_vehicles_installed_outside_uae",
    "number_of_engineers",
    "number_of_technicians",
]

FILE_FIELDS = {
    "vendor_logo": {"extensions": {"png", "jpg", "jpeg"}, "required": False},
    "trade_license": {"extensions": {"png", "jpg", "jpeg", "pdf"}, "required": True},
    "trn_certificate": {"extensions": {"png", "jpg", "jpeg", "pdf"}, "required": True},
    "tdra_certificate": {"extensions": {"png", "jpg", "jpeg", "pdf"}, "required": True},
    "sira_certificate": {"extensions": {"png", "jpg", "jpeg", "pdf"}, "required": True},
    "authorized_person_emirates_id_file": {"extensions": {"png", "jpg", "jpeg", "pdf"}, "required": True},
    "company_profile": {"extensions": {"pdf", "doc", "docx"}, "required": True},
}

UAE_EMIRATES = {
    "Abu Dhabi",
    "Dubai",
    "Sharjah",
    "Ajman",
    "Umm Al Quwain",
    "Ras Al Khaimah",
    "Fujairah",
}
TRADE_NUMBER_REGEX = re.compile(r"^[-A-Za-z0-9._/ ]{1,20}$")
EMIRATES_ID_REGEX = re.compile(r"^784-\d{4}-\d{6,7}-\d$")
SERVICE_OPTIONS = {
    "Securepath Premium",
    "SecurePath Basic - Dubai",
    "SecurePath Basic - Sharjah",
}
PUBLIC_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "icloud.com",
    "aol.com",
    "protonmail.com",
}
SQLITE_MIGRATION_COLUMNS = {
    "year_company_establishment_uae": "INTEGER NOT NULL DEFAULT 0",
    "experience_gps_tracking_years": "INTEGER NOT NULL DEFAULT 0",
    "running_vehicles_installed_uae": "INTEGER NOT NULL DEFAULT 0",
    "running_vehicles_installed_outside_uae": "INTEGER NOT NULL DEFAULT 0",
    "number_of_engineers": "INTEGER NOT NULL DEFAULT 0",
    "number_of_technicians": "INTEGER NOT NULL DEFAULT 0",
}
EXPORT_COLUMNS = [
    ("vendor_identification", "Vendor ID"),
    ("trade_name", "Trade Name"),
    ("trade_number", "Trade Number"),
    ("services_applying", "Service Package"),
    ("owner_email_id", "Owner Email ID"),
    ("first_name", "Authorised Contact First Name"),
    ("last_name", "Authorised Contact Last Name"),
    ("email_address", "Authorised Email"),
    ("contact_number", "Contact Number"),
    ("emirates_id", "Emirates ID"),
    ("year_company_establishment_uae", "Year of Company Establishment in UAE"),
    ("experience_gps_tracking_years", "Experience in GPS Tracking (Years)"),
    ("running_vehicles_installed_uae", "Vehicles with GPS Tracking in UAE"),
    ("running_vehicles_installed_outside_uae", "Vehicles with GPS Tracking outside UAE"),
    ("number_of_engineers", "Number of Engineers"),
    ("number_of_technicians", "Number of Technicians"),
    ("street", "Street"),
    ("country", "Country"),
    ("state_emirate", "State/Emirate"),
    ("city", "City"),
    ("po_box", "PO Box"),
    ("makani_number", "Makani Number"),
    ("created_at", "Submitted At"),
]


class VendorApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor_identification = db.Column(db.String(64), unique=True, nullable=False, index=True)
    trade_name = db.Column(db.String(255), nullable=False)
    trade_number = db.Column(db.String(255), nullable=False)
    platform_application = db.Column(db.String(255), nullable=False, default="")
    services_applying = db.Column(db.String(255), nullable=False)
    owner_email_id = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    email_address = db.Column(db.String(255), nullable=False)
    contact_number = db.Column(db.String(255), nullable=False)
    emirates_id = db.Column(db.String(255), nullable=False)
    street = db.Column(db.String(255), nullable=False)
    country = db.Column(db.String(255), nullable=False)
    state_emirate = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(255), nullable=False)
    year_company_establishment_uae = db.Column(db.Integer, nullable=False, default=0)
    experience_gps_tracking_years = db.Column(db.Integer, nullable=False, default=0)
    running_vehicles_installed_uae = db.Column(db.Integer, nullable=False, default=0)
    running_vehicles_installed_outside_uae = db.Column(db.Integer, nullable=False, default=0)
    number_of_engineers = db.Column(db.Integer, nullable=False, default=0)
    number_of_technicians = db.Column(db.Integer, nullable=False, default=0)
    po_box = db.Column(db.String(255), nullable=True)
    makani_number = db.Column(db.String(255), nullable=True)
    vendor_logo = db.Column(db.String(500), nullable=True)
    trade_license = db.Column(db.String(500), nullable=False)
    trn_certificate = db.Column(db.String(500), nullable=False)
    tdra_certificate = db.Column(db.String(500), nullable=False)
    sira_certificate = db.Column(db.String(500), nullable=False)
    authorized_person_emirates_id_file = db.Column(db.String(500), nullable=False)
    company_profile = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


def build_vendor_identification(trade_number: str, trade_name: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "-", trade_number.strip() or trade_name.strip()).strip("-").upper()
    base = base[:24] if base else "VENDOR"
    token = uuid.uuid4().hex[:6].upper()
    return f"{base}-{token}"


def ensure_unique_vendor_identification(trade_number: str, trade_name: str) -> str:
    while True:
        candidate = build_vendor_identification(trade_number, trade_name)
        exists = VendorApplication.query.filter_by(vendor_identification=candidate).first()
        if not exists:
            return candidate


def validate_file(field_name: str):
    file_storage = request.files.get(field_name)
    rules = FILE_FIELDS[field_name]
    if not file_storage or file_storage.filename == "":
        if rules["required"]:
            return None, f"{field_name.replace('_', ' ').title()} is required."
        return None, None
    filename = secure_filename(file_storage.filename)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in rules["extensions"]:
        return None, f"{field_name.replace('_', ' ').title()} has an invalid file type."
    file_storage.stream.seek(0, 2)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > 1024 * 1024:
        return None, f"{field_name.replace('_', ' ').title()} exceeds 1MB."
    return file_storage, None


def save_file(file_storage, target_dir: Path) -> str:
    safe_name = secure_filename(file_storage.filename)
    final_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
    target_dir.mkdir(parents=True, exist_ok=True)
    destination = target_dir / final_name
    file_storage.save(destination)
    return str(destination.relative_to(UPLOAD_ROOT))


def validate_payload(payload: dict) -> str | None:
    if payload["services_applying"] not in SERVICE_OPTIONS:
        return "Please select a valid service package."
    email_value = payload["email_address"].strip().lower()
    if not re.fullmatch(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", email_value):
        return "Authorised Email is invalid."
    email_domain = email_value.split("@")[-1]
    if email_domain in PUBLIC_EMAIL_DOMAINS:
        return "Authorised Email must use company domain and department mail ID."
    if not TRADE_NUMBER_REGEX.fullmatch(payload["trade_number"]):
        return "Trade Number must be 1-20 characters and can include letters, numbers, dash, dot, slash, underscore, and spaces."
    if len(payload["first_name"]) > 25:
        return "First Name must not exceed 25 characters."
    if len(payload["last_name"]) > 25:
        return "Last Name must not exceed 25 characters."
    if not EMIRATES_ID_REGEX.fullmatch(payload["emirates_id"]):
        return "Emirates ID format is invalid. Use 784-YYYY-XXXXXX-X or 784-YYYY-XXXXXXX-X."
    if payload["state_emirate"] not in UAE_EMIRATES:
        return "State/Emirate must be one of the 7 UAE emirates."
    current_year = datetime.utcnow().year
    if not (1900 <= payload["year_company_establishment_uae"] <= current_year):
        return f"Year of company establishment in UAE must be between 1900 and {current_year}."
    if not (0 <= payload["experience_gps_tracking_years"] <= 100):
        return "Experience in GPS tracking (Years) must be between 0 and 100."
    if payload["running_vehicles_installed_uae"] < 0:
        return "Number of currently running vehicles installed with gps tracking in uae must be 0 or greater."
    if payload["running_vehicles_installed_outside_uae"] < 0:
        return "Number of currently running vehicles installed with gps tracking outside UAE must be 0 or greater."
    if payload["number_of_engineers"] < 0:
        return "Number of Engineers in the company must be 0 or greater."
    if payload["number_of_technicians"] < 0:
        return "Number of Technicians in the company must be 0 or greater."
    return None


def parse_number_fields(payload: dict) -> str | None:
    for field in NUMBER_FIELDS:
        value = payload[field]
        if not re.fullmatch(r"\d+", value):
            return f"{field.replace('_', ' ').title()} must be a whole number."
        payload[field] = int(value)
    return None


def ensure_sqlite_schema_columns():
    if db.engine.dialect.name != "sqlite":
        return
    with db.engine.connect() as conn:
        table_rows = conn.execute(text("PRAGMA table_info(vendor_application)")).fetchall()
        if not table_rows:
            return
        existing_columns = {row[1] for row in table_rows}
        for column_name, definition in SQLITE_MIGRATION_COLUMNS.items():
            if column_name not in existing_columns:
                conn.execute(text(f"ALTER TABLE vendor_application ADD COLUMN {column_name} {definition}"))
        conn.commit()


def remember_form_data():
    session["form_data"] = request.form.to_dict()


def build_export_response(delimiter: str, filename: str, mimetype: str) -> Response:
    applications = VendorApplication.query.order_by(VendorApplication.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output, delimiter=delimiter)
    writer.writerow([label for _, label in EXPORT_COLUMNS])
    for item in applications:
        row = []
        for key, _ in EXPORT_COLUMNS:
            value = getattr(item, key)
            if key == "created_at" and value:
                row.append(value.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                row.append(value if value is not None else "")
        writer.writerow(row)
    content = output.getvalue()
    output.close()
    return Response(
        content,
        mimetype=mimetype,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.route("/", methods=["GET"])
def vendor_form():
    form_data = session.pop("form_data", {})
    return render_template("vendor_form.html", form_data=form_data)


@app.route("/submit", methods=["POST"])
def submit_application():
    payload = {}
    for field in TEXT_FIELDS + NUMBER_FIELDS:
        value = request.form.get(field, "").strip()
        if not value and field not in {"po_box", "makani_number"}:
            remember_form_data()
            flash(f"{field.replace('_', ' ').title()} is required.", "error")
            return redirect(url_for("vendor_form"))
        payload[field] = value

    number_error = parse_number_fields(payload)
    if number_error:
        remember_form_data()
        flash(number_error, "error")
        return redirect(url_for("vendor_form"))

    payload["platform_application"] = ""

    payload_error = validate_payload(payload)
    if payload_error:
        remember_form_data()
        flash(payload_error, "error")
        return redirect(url_for("vendor_form"))

    files = {}
    for field_name in FILE_FIELDS:
        file_storage, error = validate_file(field_name)
        if error:
            remember_form_data()
            flash(error, "error")
            return redirect(url_for("vendor_form"))
        files[field_name] = file_storage

    vendor_identification = ensure_unique_vendor_identification(payload["trade_number"], payload["trade_name"])
    vendor_folder = UPLOAD_ROOT / vendor_identification

    stored_paths = {}
    for field_name, file_storage in files.items():
        if file_storage:
            stored_paths[field_name] = save_file(file_storage, vendor_folder / field_name)
        else:
            stored_paths[field_name] = None

    application = VendorApplication(
        vendor_identification=vendor_identification,
        **payload,
        **stored_paths,
    )
    db.session.add(application)
    db.session.commit()
    session.pop("form_data", None)

    flash(f"Application submitted successfully. Vendor ID: {vendor_identification}", "success")
    return redirect(url_for("vendor_form"))


@app.route("/admin/applications", methods=["GET"])
def admin_list():
    applications = VendorApplication.query.order_by(VendorApplication.created_at.desc()).all()
    return render_template("admin_list.html", applications=applications)


@app.route("/admin/applications/<int:application_id>", methods=["GET"])
def admin_detail(application_id: int):
    application = VendorApplication.query.get_or_404(application_id)
    return render_template("admin_detail.html", application=application)


@app.route("/admin/applications/export/csv", methods=["GET"])
def export_applications_csv():
    return build_export_response(",", "vendor_applications.csv", "text/csv; charset=utf-8")


@app.route("/admin/applications/export/excel", methods=["GET"])
def export_applications_excel():
    return build_export_response("\t", "vendor_applications.xls", "application/vnd.ms-excel")


@app.route("/uploads/<path:filepath>", methods=["GET"])
def uploaded_file(filepath: str):
    full_path = UPLOAD_ROOT / filepath
    if not full_path.exists():
        abort(404)
    return send_from_directory(UPLOAD_ROOT, filepath)


with app.app_context():
    db.create_all()
    ensure_sqlite_schema_columns()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
