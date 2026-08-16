"""
DRSS - Digital Registration and Selection System
Complete single-file Streamlit application.

Modules 1-12:
1. Public Home
2. Participant Registration
3. Status Checking
4. Administrator Login
5. Event Management
6. Participant Management
7. Payment Verification
8. Digital Selection
9. Public Winners
10. Reports
11. System Settings
12. Audit Log

Deployment:
GitHub -> Streamlit Community Cloud -> Firebase Firestore

Important:
- Never put Firebase service-account private keys in GitHub.
- Put credentials in Streamlit Community Cloud Secrets.
- This application does not require Firebase Storage for the first version.
"""

import secrets
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    firebase_admin = None
    credentials = None
    firestore = None


APP_NAME = "Digital Registration and Selection System"
APP_SHORT_NAME = "DRSS"
APP_VERSION = "1.0"


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="DRSS - Digital Registration and Selection System",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PROFESSIONAL USER INTERFACE
# No emoji or decorative symbols are used.
# ============================================================

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1180px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    .drss-hero {
        padding: 3.2rem 3rem;
        border-radius: 22px;
        background: linear-gradient(135deg, #0B5CAD 0%, #164E86 55%, #243447 100%);
        color: white;
        margin-bottom: 1.6rem;
        box-shadow: 0 14px 35px rgba(11, 92, 173, 0.18);
    }

    .drss-hero h1 {
        font-size: 2.8rem;
        line-height: 1.12;
        margin: 0 0 0.75rem 0;
        font-weight: 800;
    }

    .drss-hero p {
        font-size: 1.1rem;
        line-height: 1.65;
        margin: 0;
        max-width: 880px;
    }

    .drss-card {
        background: #F7F9FC;
        border: 1px solid #E1E7EF;
        border-radius: 17px;
        padding: 1.35rem;
        min-height: 145px;
        box-shadow: 0 5px 18px rgba(36, 52, 71, 0.06);
    }

    .drss-card h3 {
        margin-top: 0;
        color: #243447;
    }

    .drss-card p {
        color: #526274;
        line-height: 1.55;
    }

    .drss-step {
        border-left: 4px solid #138A36;
        background: #F7F9FC;
        padding: 1rem 1.2rem;
        margin: 0.6rem 0;
        border-radius: 0 12px 12px 0;
    }

    .ticket-box {
        padding: 25px;
        border: 2px solid #0B5CAD;
        border-radius: 16px;
        text-align: center;
        margin: 15px 0;
        background: #F7F9FC;
    }

    .ticket-number {
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: 1px;
        color: #0B5CAD;
        margin: 10px 0;
    }

    .section-note {
        color: #526274;
        line-height: 1.6;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid #E1E7EF;
    }

    .footer-note {
        text-align: center;
        color: #667085;
        font-size: 0.85rem;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #E1E7EF;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# STREAMLIT SECRETS HELPERS
# ============================================================

def read_secret(section, key, default=None):
    """
    Read a value from Streamlit Secrets.

    Supports:
        [section]
        key = "value"

    It also supports a top-level key for convenience.
    """
    try:
        section_data = st.secrets.get(section)
        if section_data is not None:
            try:
                return section_data.get(key, default)
            except AttributeError:
                return section_data[key]
    except Exception:
        pass

    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def get_firebase_web_config():
    """
    Read the Firebase web configuration.

    This configuration is not sufficient for server-side Firestore access,
    but it is retained because it belongs to the Firebase project setup.
    """
    return {
        "apiKey": read_secret("firebase", "apiKey"),
        "authDomain": read_secret("firebase", "authDomain"),
        "projectId": read_secret("firebase", "projectId"),
        "storageBucket": read_secret("firebase", "storageBucket"),
        "messagingSenderId": read_secret("firebase", "messagingSenderId"),
        "appId": read_secret("firebase", "appId"),
    }


def get_database():
    """
    Initialize Firebase Admin SDK exactly once and return Firestore client.

    Accepted Streamlit Secrets format:

    [firebase_admin]
    project_id = "..."
    private_key_id = "..."
    private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
    client_email = "..."
    client_id = "..."

    Alternative:
    [firebase_admin]
    type = "service_account"
    project_id = "..."
    private_key_id = "..."
    private_key = "..."
    client_email = "..."
    client_id = "..."
    """

    if firebase_admin is None:
        st.error(
            "The Firebase Admin package is not installed. "
            "Check requirements.txt and redeploy the application."
        )
        st.stop()

    if firebase_admin._apps:
        return firestore.client()

    project_id = read_secret("firebase_admin", "project_id")
    private_key_id = read_secret("firebase_admin", "private_key_id")
    private_key = read_secret("firebase_admin", "private_key")
    client_email = read_secret("firebase_admin", "client_email")
    client_id = read_secret("firebase_admin", "client_id")

    missing = []

    if not project_id:
        missing.append("project_id")
    if not private_key:
        missing.append("private_key")
    if not client_email:
        missing.append("client_email")

    if missing:
        st.error("Firebase server configuration is incomplete.")

        st.markdown(
            """
            ### Required Streamlit Secret

            Add the following section to the Secrets area of the deployed
            Streamlit application.

            ```toml
            [firebase_admin]
            project_id = "YOUR_PROJECT_ID"
            private_key_id = "YOUR_PRIVATE_KEY_ID"
            private_key = "-----BEGIN PRIVATE KEY-----\\nYOUR_PRIVATE_KEY\\n-----END PRIVATE KEY-----\\n"
            client_email = "firebase-adminsdk-xxxxx@YOUR_PROJECT_ID.iam.gserviceaccount.com"
            client_id = "YOUR_CLIENT_ID"
            ```

            The values must come from the Firebase Admin SDK service-account
            JSON file for your project.

            Do not put the service-account JSON file or private key in GitHub.
            Do not put the private key directly into app.py.

            The missing required fields are:

            """
        )

        st.write(", ".join(missing))
        st.stop()

    private_key = str(private_key).replace("\\n", "\n").strip()

    if "BEGIN PRIVATE KEY" not in private_key:
        st.error(
            "The Firebase private key is not in the expected service-account "
            "format. Copy the complete private_key value from the Firebase "
            "service-account JSON file."
        )
        st.stop()

    service_account = {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": private_key_id or "",
        "private_key": private_key,
        "client_email": client_email,
        "client_id": client_id or "",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url":
            "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url":
            "https://www.googleapis.com/robot/v1/metadata/x509/"
            + str(client_email).replace("@", "%40"),
    }

    try:
        firebase_admin.initialize_app(
            credentials.Certificate(service_account)
        )
    except Exception as exc:
        st.error("Firebase initialization failed.")
        st.exception(exc)
        st.stop()

    try:
        return firestore.client()
    except Exception as exc:
        st.error("Firestore could not be opened.")
        st.exception(exc)
        st.stop()


# ============================================================
# GENERAL HELPERS
# ============================================================

def utc_now():
    return datetime.now(timezone.utc).isoformat()


def clean_text(value, max_length=500):
    return str(value or "").strip()[:max_length]


def normalize_phone(phone):
    value = "".join(
        c for c in str(phone or "").strip()
        if c.isdigit() or c == "+"
    )

    if value.startswith("09") and len(value) == 10:
        return "+251" + value[1:]

    if value.startswith("9") and len(value) == 9:
        return "+251" + value

    if value.startswith("2519") and len(value) == 12:
        return "+" + value

    return value


def valid_phone(phone):
    value = normalize_phone(phone)
    return (
        value.startswith("+")
        and value[1:].isdigit()
        and 10 <= len(value[1:]) <= 15
    )


def create_ticket():
    """
    Generate a unique human-readable DRSS ticket.

    Uniqueness is checked against Firestore before use.
    """
    db = get_database()

    for _ in range(100):
        number = secrets.randbelow(1_000_000)
        ticket = f"DRSS-{datetime.now().year}-{number:06d}"

        found = list(
            db.collection("participants")
            .where("ticket_number", "==", ticket)
            .limit(1)
            .stream()
        )

        if not found:
            return ticket

    raise RuntimeError("Could not create a unique ticket number.")


def get_events(open_only=False):
    db = get_database()

    result = []

    for document in db.collection("events").stream():
        data = document.to_dict()
        data["id"] = document.id

        if open_only and data.get("status") != "OPEN":
            continue

        result.append(data)

    result.sort(
        key=lambda item: (
            str(item.get("event_date", "")),
            str(item.get("name", "")),
        )
    )

    return result


def get_event(event_id):
    db = get_database()

    document = (
        db.collection("events")
        .document(event_id)
        .get()
    )

    if not document.exists:
        return None

    data = document.to_dict()
    data["id"] = document.id
    return data


def get_participants(event_id=None):
    db = get_database()

    reference = db.collection("participants")

    if event_id:
        reference = reference.where("event_id", "==", event_id)

    result = []

    for document in reference.stream():
        data = document.to_dict()
        data["id"] = document.id
        result.append(data)

    return result


def find_by_ticket(ticket):
    db = get_database()

    documents = list(
        db.collection("participants")
        .where("ticket_number", "==", clean_text(ticket, 100))
        .limit(1)
        .stream()
    )

    if not documents:
        return None

    data = documents[0].to_dict()
    data["id"] = documents[0].id
    return data


def find_by_phone(phone):
    db = get_database()

    normalized = normalize_phone(phone)

    documents = list(
        db.collection("participants")
        .where("phone", "==", normalized)
        .limit(50)
        .stream()
    )

    if not documents:
        return None

    documents.sort(
        key=lambda document:
        document.to_dict().get("created_at", ""),
        reverse=True,
    )

    data = documents[0].to_dict()
    data["id"] = documents[0].id
    return data


def write_audit(action, actor, details=None):
    db = get_database()

    db.collection("audit_logs").add(
        {
            "action": action,
            "actor": actor or "PUBLIC",
            "details": details or {},
            "created_at": utc_now(),
        }
    )


def admin_authenticated():
    return bool(
        st.session_state.get("admin_authenticated", False)
    )


def configured_admin_email():
    return clean_text(
        read_secret("admin", "email", ""),
        200,
    ).lower()


def configured_admin_password():
    return str(
        read_secret("admin", "password", "")
    )


def configured_admin_emails():
    value = read_secret("admin", "emails", "")

    if isinstance(value, str):
        return [
            item.strip().lower()
            for item in value.split(",")
            if item.strip()
        ]

    try:
        return [
            str(item).strip().lower()
            for item in value
            if str(item).strip()
        ]
    except Exception:
        return []


def is_authorized_admin(email):
    email = str(email or "").strip().lower()

    allowed = configured_admin_emails()

    primary = configured_admin_email()

    if primary and primary not in allowed:
        allowed.append(primary)

    return email in allowed


# ============================================================
# MODULE 1
# PUBLIC HOME
# ============================================================

def module_1_home():
    events = get_events(open_only=True)

    st.markdown(
        """
        <div class="drss-hero">
            <h1>Digital Registration and Selection System</h1>
            <p>
                A simple and transparent platform for participant registration,
                status checking, payment verification and controlled digital
                selection.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if events:
        event = events[0]

        participants = get_participants(event["id"])

        total = len(participants)
        capacity = int(event.get("max_participants", 0) or 0)
        remaining = max(capacity - total, 0)

        st.subheader(
            clean_text(
                event.get("name", "Current Registration Event"),
                200,
            )
        )

        description = clean_text(
            event.get("description", ""),
            2000,
        )

        if description:
            st.markdown(
                f'<div class="section-note">{description}</div>',
                unsafe_allow_html=True,
            )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Registered", f"{total:,}")
        c2.metric("Available places", f"{remaining:,}")
        c3.metric(
            "Registration fee",
            f"{float(event.get('registration_fee', 0)):,.2f} "
            f"{event.get('currency', 'ETB')}",
        )
        c4.metric(
            "Event date",
            str(event.get("event_date", "")),
        )

        st.divider()

    else:
        st.info("There is currently no open registration event.")

    st.subheader("How DRSS works")

    cards = st.columns(3)

    with cards[0]:
        st.markdown(
            """
            <div class="drss-card">
                <h3>Simple registration</h3>
                <p>
                    Complete one clear registration form and receive a unique
                    DRSS ticket number.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with cards[1]:
        st.markdown(
            """
            <div class="drss-card">
                <h3>Transparent status</h3>
                <p>
                    Check registration, payment and selection status using the
                    ticket number or registered phone number.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with cards[2]:
        st.markdown(
            """
            <div class="drss-card">
                <h3>Controlled selection</h3>
                <p>
                    Eligible participants can be selected digitally and the
                    official result is recorded in the system.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    steps = [
        ("01", "Register", "Enter your information."),
        ("02", "Receive your ticket",
         "Save the ticket number displayed after registration."),
        ("03", "Complete payment",
         "Use the payment method specified by the organizer."),
        ("04", "Check status",
         "Return to DRSS to check your registration and payment status."),
        ("05", "View results",
         "Use the public results page after an official selection."),
    ]

    for number, title, description in steps:
        st.markdown(
            f"""
            <div class="drss-step">
                <strong>{number} - {title}</strong><br>
                {description}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# MODULE 2
# PARTICIPANT REGISTRATION
# ============================================================

def module_2_registration():
    st.title("Module 2 - Participant Registration")

    events = get_events(open_only=True)

    if not events:
        st.warning("No open registration event is available.")
        return

    event_options = {
        f"{event.get('name', '')} - {event.get('event_date', '')}":
            event["id"]
        for event in events
    }

    selected_label = st.selectbox(
        "Select event",
        list(event_options.keys()),
    )

    event_id = event_options[selected_label]
    event = get_event(event_id)

    current_count = len(get_participants(event_id))
    maximum = int(event.get("max_participants", 0) or 0)

    st.info(
        f"{current_count:,} of {maximum:,} available places are currently used."
    )

    if current_count >= maximum:
        st.error("Registration capacity has been reached.")
        return

    with st.form("registration_form"):

        st.subheader("Personal information")

        full_name = st.text_input("Full name")

        c1, c2 = st.columns(2)

        with c1:
            phone = st.text_input("Phone number")
            email = st.text_input("Email address")
            sex = st.selectbox(
                "Sex",
                [
                    "Prefer not to say",
                    "Male",
                    "Female",
                    "Other",
                ],
            )
            age = st.number_input(
                "Age",
                min_value=0,
                max_value=120,
                value=0,
            )

        with c2:
            region = st.text_input("Region")
            zone = st.text_input("Zone")
            woreda = st.text_input("Woreda")
            kebele = st.text_input("Kebele")

        address = st.text_input("Address")
        id_number = st.text_input(
            "Identification number",
            help="Optional. Only provide it when required by the event.",
        )

        st.subheader("Payment information")

        registration_fee = float(
            event.get("registration_fee", 0) or 0
        )

        st.write(
            f"Required registration fee: "
            f"{registration_fee:,.2f} "
            f"{event.get('currency', 'ETB')}"
        )

        payment_reference = st.text_input(
            "Payment or transaction reference"
        )

        payment_method = st.selectbox(
            "Payment method",
            [
                "Not applicable",
                "Bank",
                "Mobile Money",
                "Cash",
                "Other",
            ],
        )

        amount_paid = st.number_input(
            "Amount paid",
            min_value=0.0,
            value=registration_fee,
            step=10.0,
        )

        notes = st.text_area("Additional information")

        consent = st.checkbox(
            "I confirm that the information I entered is correct."
        )

        submitted = st.form_submit_button(
            "Submit registration",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    errors = []

    if len(clean_text(full_name)) < 2:
        errors.append("Full name is required.")

    if not valid_phone(phone):
        errors.append("Please enter a valid phone number.")

    if not consent:
        errors.append(
            "Please confirm that the information entered is correct."
        )

    if registration_fee > float(amount_paid):
        errors.append(
            "The amount paid is lower than the required registration fee."
        )

    normalized_phone = normalize_phone(phone)

    existing = list(
        get_database()
        .collection("participants")
        .where("event_id", "==", event_id)
        .where("phone", "==", normalized_phone)
        .limit(1)
        .stream()
    )

    if existing:
        errors.append(
            "This phone number is already registered for this event."
        )

    if errors:
        for error in errors:
            st.error(error)
        return

    ticket = create_ticket()

    payment_status = (
        "PENDING"
        if registration_fee > 0
        else "NOT_REQUIRED"
    )

    participant = {
        "ticket_number": ticket,
        "event_id": event_id,
        "full_name": clean_text(full_name),
        "phone": normalized_phone,
        "email": clean_text(email, 200),
        "sex": clean_text(sex, 50),
        "age": int(age) if age else None,
        "region": clean_text(region, 100),
        "zone": clean_text(zone, 100),
        "woreda": clean_text(woreda, 100),
        "kebele": clean_text(kebele, 100),
        "address": clean_text(address, 300),
        "id_number": clean_text(id_number, 200),
        "payment_reference": clean_text(payment_reference, 200),
        "payment_method": clean_text(payment_method, 100),
        "payment_amount": float(amount_paid),
        "payment_status": payment_status,
        "registration_status": "REGISTERED",
        "selection_status": "NOT_SELECTED",
        "selection_rank": None,
        "selection_id": None,
        "notes": clean_text(notes, 1000),
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }

    get_database().collection("participants").add(participant)

    write_audit(
        "PARTICIPANT_REGISTERED",
        "PUBLIC",
        {
            "ticket_number": ticket,
            "event_id": event_id,
        },
    )

    st.success("Registration completed successfully.")

    st.markdown(
        f"""
        <div class="ticket-box">
            <div>Your DRSS ticket number</div>
            <div class="ticket-number">{ticket}</div>
            <div>Save this number for future status checking.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    confirmation = (
        "DRSS REGISTRATION CONFIRMATION\n"
        "\n"
        f"Name: {participant['full_name']}\n"
        f"Ticket: {participant['ticket_number']}\n"
        f"Event: {event.get('name', '')}\n"
        f"Event date: {event.get('event_date', '')}\n"
        f"Registration status: {participant['registration_status']}\n"
        f"Payment status: {participant['payment_status']}\n"
        f"Created: {participant['created_at']}\n"
    )

    st.download_button(
        "Download confirmation",
        confirmation,
        file_name=f"{ticket}.txt",
        mime="text/plain",
        use_container_width=True,
    )


# ============================================================
# MODULE 3
# STATUS CHECKING
# ============================================================

def module_3_status():
    st.title("Module 3 - Check Registration Status")

    method = st.radio(
        "Search using",
        [
            "Ticket number",
            "Phone number",
        ],
        horizontal=True,
    )

    if method == "Ticket number":
        ticket = st.text_input("DRSS ticket number")
        phone = ""
    else:
        phone = st.text_input("Registered phone number")
        ticket = ""

    if not st.button(
        "Check status",
        type="primary",
        use_container_width=True,
    ):
        return

    if method == "Ticket number":
        participant = find_by_ticket(ticket)
    else:
        participant = find_by_phone(phone)

    if not participant:
        st.error("No registration was found.")
        return

    event = get_event(participant.get("event_id"))

    st.success("Registration found.")

    c1, c2 = st.columns(2)

    with c1:
        st.write(
            f"Name: {participant.get('full_name', '')}"
        )
        st.write(
            f"Ticket: {participant.get('ticket_number', '')}"
        )
        st.write(
            f"Event: {event.get('name', '') if event else ''}"
        )

    with c2:
        st.write(
            f"Registration status: "
            f"{participant.get('registration_status', '')}"
        )
        st.write(
            f"Payment status: "
            f"{participant.get('payment_status', '')}"
        )
        st.write(
            f"Selection status: "
            f"{participant.get('selection_status', '')}"
        )

    if participant.get("selection_status") == "SELECTED":
        st.success(
            "Your ticket has been selected."
        )
    elif participant.get("payment_status") == "PENDING":
        st.warning(
            "Payment verification is still pending."
        )
    elif participant.get("payment_status") == "REJECTED":
        st.warning(
            "The submitted payment has not been approved."
        )
    else:
        st.info(
            "Your registration is recorded in the system."
        )


# ============================================================
# MODULE 4
# ADMINISTRATOR LOGIN
# ============================================================

def module_4_admin_login():
    st.title("Module 4 - Administrator Login")

    st.markdown(
        """
        Administrator access is separate from public participant access.
        The administrator password is stored in Streamlit Secrets and is
        never stored in the GitHub repository.
        """
    )

    with st.form("administrator_login"):
        email = st.text_input("Administrator email")
        password = st.text_input(
            "Administrator password",
            type="password",
        )

        submitted = st.form_submit_button(
            "Sign in",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    email = email.strip().lower()

    configured_email = configured_admin_email()
    configured_password = configured_admin_password()

    if not configured_email or not configured_password:
        st.error(
            "Administrator credentials have not been configured in "
            "Streamlit Secrets."
        )
        st.info(
            "Add the admin email, password and authorized email list under "
            "the [admin] section."
        )
        return

    if (
        email == configured_email
        and password == configured_password
        and is_authorized_admin(email)
    ):
        st.session_state["admin_authenticated"] = True
        st.session_state["admin_email"] = email
        st.success("Administrator login successful.")
        st.rerun()

    st.error("Invalid administrator credentials.")


# ============================================================
# MODULE 5
# EVENT MANAGEMENT
# ============================================================

def module_5_events():
    if not admin_authenticated():
        module_4_admin_login()
        return

    st.title("Module 5 - Event Management")

    db = get_database()
    admin_email = st.session_state.get("admin_email", "")

    st.subheader("Create a new event")

    with st.form("create_event"):
        name = st.text_input("Event name")
        description = st.text_area("Event description")
        location = st.text_input("Location")
        event_date = st.date_input(
            "Event date",
            value=datetime.now().date(),
        )
        registration_fee = st.number_input(
            "Registration fee",
            min_value=0.0,
            value=0.0,
            step=10.0,
        )
        currency = st.text_input(
            "Currency",
            value="ETB",
        )
        maximum = st.number_input(
            "Maximum participants",
            min_value=1,
            max_value=1_000_000,
            value=1000,
        )

        submitted = st.form_submit_button(
            "Create event",
            type="primary",
        )

    if submitted:
        if len(clean_text(name)) < 2:
            st.error("Event name is required.")
        else:
            event_data = {
                "name": clean_text(name, 200),
                "description": clean_text(description, 3000),
                "location": clean_text(location, 300),
                "event_date": str(event_date),
                "registration_fee": float(registration_fee),
                "currency": clean_text(currency, 10),
                "max_participants": int(maximum),
                "status": "OPEN",
                "created_at": utc_now(),
                "created_by": admin_email,
                "updated_at": utc_now(),
            }

            reference = db.collection("events").add(event_data)

            write_audit(
                "EVENT_CREATED",
                admin_email,
                {
                    "event_id": reference[1].id,
                    "name": event_data["name"],
                },
            )

            st.success("Event created successfully.")
            st.rerun()

    st.divider()
    st.subheader("Existing events")

    events = get_events()

    if not events:
        st.info("No events have been created.")
        return

    for event in events:
        with st.expander(
            f"{event.get('name', '')} - {event.get('status', '')}"
        ):
            st.write(
                f"Date: {event.get('event_date', '')}"
            )
            st.write(
                f"Location: {event.get('location', '')}"
            )
            st.write(
                f"Maximum participants: "
                f"{event.get('max_participants', 0)}"
            )
            st.write(
                f"Registration fee: "
                f"{event.get('registration_fee', 0)} "
                f"{event.get('currency', 'ETB')}"
            )

            if event.get("status") == "OPEN":
                if st.button(
                    "Close registration",
                    key=f"close_{event['id']}",
                ):
                    db.collection("events").document(
                        event["id"]
                    ).update(
                        {
                            "status": "CLOSED",
                            "updated_at": utc_now(),
                        }
                    )

                    write_audit(
                        "EVENT_CLOSED",
                        admin_email,
                        {"event_id": event["id"]},
                    )

                    st.rerun()

            else:
                if st.button(
                    "Open registration",
                    key=f"open_{event['id']}",
                ):
                    db.collection("events").document(
                        event["id"]
                    ).update(
                        {
                            "status": "OPEN",
                            "updated_at": utc_now(),
                        }
                    )

                    write_audit(
                        "EVENT_OPENED",
                        admin_email,
                        {"event_id": event["id"]},
                    )

                    st.rerun()


# ============================================================
# MODULE 6
# PARTICIPANT MANAGEMENT
# ============================================================

def module_6_participants():
    if not admin_authenticated():
        module_4_admin_login()
        return

    st.title("Module 6 - Participant Management")

    events = get_events()

    if not events:
        st.info("No events are available.")
        return

    options = {
        f"{event.get('name', '')} - {event.get('event_date', '')}":
            event["id"]
        for event in events
    }

    selected = st.selectbox(
        "Select event",
        list(options.keys()),
    )

    event_id = options[selected]

    rows = get_participants(event_id)

    if not rows:
        st.info("No participants have registered for this event.")
        return

    dataframe = pd.DataFrame(rows)

    search = st.text_input(
        "Search by name, ticket number or phone"
    )

    if search:
        search_value = search.lower()

        mask = (
            dataframe["full_name"]
            .fillna("")
            .str.lower()
            .str.contains(search_value)
            |
            dataframe["ticket_number"]
            .fillna("")
            .str.lower()
            .str.contains(search_value)
            |
            dataframe["phone"]
            .fillna("")
            .str.lower()
            .str.contains(search_value)
        )

        dataframe = dataframe[mask]

    preferred_columns = [
        "ticket_number",
        "full_name",
        "phone",
        "email",
        "payment_status",
        "registration_status",
        "selection_status",
        "created_at",
    ]

    visible_columns = [
        column
        for column in preferred_columns
        if column in dataframe.columns
    ]

    st.dataframe(
        dataframe[visible_columns],
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download participant CSV",
        dataframe.to_csv(index=False).encode("utf-8"),
        file_name="drss_participants.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ============================================================
# MODULE 7
# PAYMENT VERIFICATION
# ============================================================

def module_7_payments():
    if not admin_authenticated():
        module_4_admin_login()
        return

    st.title("Module 7 - Payment Verification")

    db = get_database()
    admin_email = st.session_state.get("admin_email", "")

    pending = []

    for document in db.collection("participants").stream():
        data = document.to_dict()

        if data.get("payment_status") == "PENDING":
            data["id"] = document.id
            pending.append(data)

    st.metric(
        "Pending payment records",
        len(pending),
    )

    if not pending:
        st.success("There are no pending payment records.")
        return

    for participant in pending:
        with st.expander(
            f"{participant.get('ticket_number', '')} - "
            f"{participant.get('full_name', '')}"
        ):
            st.write(
                f"Phone: {participant.get('phone', '')}"
            )
            st.write(
                f"Payment reference: "
                f"{participant.get('payment_reference', '')}"
            )
            st.write(
                f"Payment method: "
                f"{participant.get('payment_method', '')}"
            )
            st.write(
                f"Amount: "
                f"{participant.get('payment_amount', 0)}"
            )

            left, right = st.columns(2)

            if left.button(
                "Approve payment",
                key=f"approve_{participant['id']}",
                use_container_width=True,
            ):
                db.collection("participants").document(
                    participant["id"]
                ).update(
                    {
                        "payment_status": "APPROVED",
                        "payment_verified_by": admin_email,
                        "payment_verified_at": utc_now(),
                        "updated_at": utc_now(),
                    }
                )

                write_audit(
                    "PAYMENT_APPROVED",
                    admin_email,
                    {
                        "participant_id": participant["id"],
                        "ticket": participant.get("ticket_number"),
                    },
                )

                st.rerun()

            if right.button(
                "Reject payment",
                key=f"reject_{participant['id']}",
                use_container_width=True,
            ):
                db.collection("participants").document(
                    participant["id"]
                ).update(
                    {
                        "payment_status": "REJECTED",
                        "payment_verified_by": admin_email,
                        "payment_verified_at": utc_now(),
                        "updated_at": utc_now(),
                    }
                )

                write_audit(
                    "PAYMENT_REJECTED",
                    admin_email,
                    {
                        "participant_id": participant["id"],
                        "ticket": participant.get("ticket_number"),
                    },
                )

                st.rerun()


# ============================================================
# MODULE 8
# DIGITAL RANDOM SELECTION
# ============================================================

def module_8_selection():
    if not admin_authenticated():
        module_4_admin_login()
        return

    st.title("Module 8 - Digital Selection")

    db = get_database()
    admin_email = st.session_state.get("admin_email", "")

    events = get_events()

    if not events:
        st.info("No events are available.")
        return

    options = {
        f"{event.get('name', '')} - {event.get('event_date', '')}":
            event["id"]
        for event in events
    }

    selected = st.selectbox(
        "Select event",
        list(options.keys()),
    )

    event_id = options[selected]
    event = get_event(event_id)

    participants = get_participants(event_id)

    eligible = [
        participant
        for participant in participants
        if (
            participant.get("registration_status") == "REGISTERED"
            and participant.get("payment_status")
            in ("APPROVED", "NOT_REQUIRED")
        )
    ]

    st.metric(
        "Eligible participants",
        len(eligible),
    )

    if not eligible:
        st.warning(
            "There are no eligible participants for this selection."
        )
        return

    previous = list(
        db.collection("selections")
        .where("event_id", "==", event_id)
        .limit(1)
        .stream()
    )

    if previous:
        st.warning(
            "An official selection record already exists for this event."
        )

        previous_data = previous[0].to_dict()

        st.write(
            f"Selection ID: {previous_data.get('selection_id', '')}"
        )
        st.write(
            f"Selected at: {previous_data.get('selected_at', '')}"
        )
        st.write(
            f"Number selected: "
            f"{previous_data.get('requested_winners', '')}"
        )

        return

    number_of_winners = st.number_input(
        "Number of winners",
        min_value=1,
        max_value=len(eligible),
        value=1,
    )

    confirmation = st.checkbox(
        "I confirm that the eligible participant list has been reviewed "
        "and I want to run the official selection."
    )

    if not st.button(
        "Run official selection",
        type="primary",
        use_container_width=True,
    ):
        return

    if not confirmation:
        st.error(
            "Please confirm the selection before continuing."
        )
        return

    eligible_ids = [
        participant["id"]
        for participant in eligible
    ]

    random_generator = secrets.SystemRandom()

    selected_ids = random_generator.sample(
        eligible_ids,
        int(number_of_winners),
    )

    selection_id = (
        "SEL-"
        + datetime.now().strftime("%Y%m%d%H%M%S")
        + "-"
        + secrets.token_hex(3).upper()
    )

    selected_tickets = []

    for rank, participant_id in enumerate(
        selected_ids,
        start=1,
    ):
        participant = next(
            item
            for item in eligible
            if item["id"] == participant_id
        )

        selected_tickets.append(
            participant.get("ticket_number")
        )

        db.collection("participants").document(
            participant_id
        ).update(
            {
                "selection_status": "SELECTED",
                "selection_rank": rank,
                "selection_id": selection_id,
                "updated_at": utc_now(),
            }
        )

    db.collection("selections").document(
        selection_id
    ).set(
        {
            "selection_id": selection_id,
            "event_id": event_id,
            "event_name": event.get("name"),
            "requested_winners": int(number_of_winners),
            "eligible_count": len(eligible),
            "eligible_participant_ids": eligible_ids,
            "selected_participant_ids": selected_ids,
            "selected_tickets": selected_tickets,
            "selected_at": utc_now(),
            "selected_by": admin_email,
            "status": "COMPLETED",
        }
    )

    write_audit(
        "OFFICIAL_SELECTION_COMPLETED",
        admin_email,
        {
            "event_id": event_id,
            "selection_id": selection_id,
            "winner_count": int(number_of_winners),
        },
    )

    st.success(
        f"Official selection completed. Selection ID: {selection_id}"
    )

    for rank, participant_id in enumerate(
        selected_ids,
        start=1,
    ):
        participant = next(
            item
            for item in eligible
            if item["id"] == participant_id
        )

        st.write(
            f"Winner {rank}: "
            f"{participant.get('full_name', '')} - "
            f"{participant.get('ticket_number', '')}"
        )


# ============================================================
# MODULE 9
# PUBLIC WINNERS
# ============================================================

def module_9_winners():
    st.title("Module 9 - Official Winners")

    db = get_database()
    events = get_events()

    if not events:
        st.info("No events are available.")
        return

    options = {
        f"{event.get('name', '')} - {event.get('event_date', '')}":
            event["id"]
        for event in events
    }

    selected = st.selectbox(
        "Select event",
        list(options.keys()),
    )

    event_id = options[selected]

    documents = list(
        db.collection("participants")
        .where("event_id", "==", event_id)
        .where("selection_status", "==", "SELECTED")
        .stream()
    )

    if not documents:
        st.info(
            "No official winners have been published for this event."
        )
        return

    winners = []

    for document in documents:
        data = document.to_dict()

        winners.append(
            {
                "Rank": data.get("selection_rank", ""),
                "Name": data.get("full_name", ""),
                "Ticket": data.get("ticket_number", ""),
            }
        )

    winners.sort(
        key=lambda item:
        int(item["Rank"])
        if str(item["Rank"]).isdigit()
        else 999999
    )

    st.subheader("Official selected participants")

    st.dataframe(
        pd.DataFrame(winners),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# MODULE 10
# REPORTS
# ============================================================

def module_10_reports():
    if not admin_authenticated():
        module_4_admin_login()
        return

    st.title("Module 10 - Reports")

    participants = get_participants()

    if not participants:
        st.info("No participant records are available.")
        return

    dataframe = pd.DataFrame(participants)

    total = len(dataframe)

    approved = int(
        (
            dataframe["payment_status"] == "APPROVED"
        ).sum()
    )

    pending = int(
        (
            dataframe["payment_status"] == "PENDING"
        ).sum()
    )

    selected = int(
        (
            dataframe["selection_status"] == "SELECTED"
        ).sum()
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total registrations", total)
    c2.metric("Approved payments", approved)
    c3.metric("Pending payments", pending)
    c4.metric("Selected participants", selected)

    st.subheader("Registration summary by event")

    summary = (
        dataframe.groupby("event_id")
        .size()
        .reset_index(name="registrations")
    )

    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Full participant report")

    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download CSV report",
        dataframe.to_csv(index=False).encode("utf-8"),
        file_name="drss_full_report.csv",
        mime="text/csv",
        use_container_width=True,
    )

    try:
        excel_buffer = BytesIO()

        with pd.ExcelWriter(
            excel_buffer,
            engine="openpyxl",
        ) as writer:
            dataframe.to_excel(
                writer,
                index=False,
                sheet_name="Participants",
            )

            summary.to_excel(
                writer,
                index=False,
                sheet_name="Event Summary",
            )

        st.download_button(
            "Download Excel report",
            excel_buffer.getvalue(),
            file_name="drss_report.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
        )

    except Exception:
        st.info(
            "Excel export is unavailable. CSV export is available."
        )


# ============================================================
# MODULE 11
# SYSTEM SETTINGS
# ============================================================

def module_11_settings():
    if not admin_authenticated():
        module_4_admin_login()
        return

    st.title("Module 11 - System Settings")

    st.subheader("Application information")

    st.write(
        f"Application: {APP_NAME}"
    )

    st.write(
        f"Version: {APP_VERSION}"
    )

    st.write(
        "Database: Firebase Firestore"
    )

    st.write(
        "Deployment model: GitHub and Streamlit Community Cloud"
    )

    st.divider()

    st.subheader("Current administrator")

    st.write(
        st.session_state.get(
            "admin_email",
            "",
        )
    )

    st.divider()

    st.subheader("Events")

    events = get_events()

    if events:
        for event in events:
            st.write(
                f"{event.get('name', '')} | "
                f"{event.get('status', '')} | "
                f"{event.get('event_date', '')}"
            )
    else:
        st.info("No events are configured.")

    st.divider()

    st.warning(
        "Before public production use, configure Firestore Security Rules, "
        "administrator access, backups, privacy controls and appropriate "
        "data retention procedures."
    )


# ============================================================
# MODULE 12
# AUDIT LOG
# ============================================================

def module_12_audit():
    if not admin_authenticated():
        module_4_admin_login()
        return

    st.title("Module 12 - Audit Log")

    db = get_database()

    try:
        documents = list(
            db.collection("audit_logs")
            .order_by(
                "created_at",
                direction=firestore.Query.DESCENDING,
            )
            .limit(500)
            .stream()
        )
    except Exception:
        documents = list(
            db.collection("audit_logs")
            .limit(500)
            .stream()
        )

    if not documents:
        st.info("No audit records are available.")
        return

    rows = []

    for document in documents:
        data = document.to_dict()
        data["id"] = document.id
        rows.append(data)

    dataframe = pd.DataFrame(rows)

    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download audit log",
        dataframe.to_csv(index=False).encode("utf-8"),
        file_name="drss_audit_log.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ============================================================
# ADMINISTRATOR DASHBOARD
# ============================================================

def administrator_dashboard():
    if not admin_authenticated():
        module_4_admin_login()
        return

    st.title("DRSS Administrator Dashboard")

    st.caption(
        f"Signed in as {st.session_state.get('admin_email', '')}"
    )

    if st.button("Log out"):
        st.session_state["admin_authenticated"] = False
        st.session_state["admin_email"] = ""
        st.rerun()

    tabs = st.tabs(
        [
            "Event Management",
            "Participant Management",
            "Payment Verification",
            "Digital Selection",
            "Reports",
            "System Settings",
            "Audit Log",
        ]
    )

    with tabs[0]:
        module_5_events()

    with tabs[1]:
        module_6_participants()

    with tabs[2]:
        module_7_payments()

    with tabs[3]:
        module_8_selection()

    with tabs[4]:
        module_10_reports()

    with tabs[5]:
        module_11_settings()

    with tabs[6]:
        module_12_audit()


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():

    st.sidebar.title("DRSS")
    st.sidebar.caption(
        "Digital Registration and Selection System"
    )

    public_pages = [
        "Home",
        "Register",
        "Check Status",
        "Official Winners",
        "Administrator",
    ]

    page = st.sidebar.radio(
        "Main menu",
        public_pages,
    )

    st.sidebar.divider()

    st.sidebar.caption(
        "Modules 1 through 12 are contained in this single app.py file."
    )

    if page == "Home":
        module_1_home()

    elif page == "Register":
        module_2_registration()

    elif page == "Check Status":
        module_3_status()

    elif page == "Official Winners":
        module_9_winners()

    elif page == "Administrator":
        administrator_dashboard()

    st.markdown(
        """
        <div class="footer-note">
            DRSS - Digital Registration and Selection System
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
