import streamlit as st
import json
import uuid
import random
import hashlib
from datetime import datetime, date

st.set_page_config(
    page_title="DRSS | Digital Registration and Selection System",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

VERSION = "2.1"

st.markdown(
    """
    <style>
    .block-container {max-width: 1280px; padding-top: 1.2rem;}
    .hero {
        padding: 2.2rem;
        border: 1px solid #d7e2ed;
        border-radius: 20px;
        background: linear-gradient(135deg,#f7f9fc,#edf5fb);
        margin-bottom: 1.5rem;
    }
    .hero h1 {margin: 0; color: #243447; font-size: 2.35rem;}
    .hero p {color: #52606d; font-size: 1.05rem; line-height: 1.6;}
    .card {
        padding: 1.15rem;
        border: 1px solid #d9e2ec;
        border-radius: 14px;
        background: white;
        min-height: 120px;
    }
    .card h3 {color: #243447;}
    .card p {color: #52606d;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Firebase connection
# ============================================================

def get_secret_json():
    try:
        value = st.secrets.get("FIREBASE_SERVICE_ACCOUNT_JSON", "")
        return str(value).strip()
    except Exception:
        return ""


def load_firebase_config():
    raw = get_secret_json()

    if not raw:
        return {}, ["FIREBASE_SERVICE_ACCOUNT_JSON is missing."]

    try:
        config = json.loads(raw)
    except Exception as exc:
        return {}, [
            "FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON.",
            f"{type(exc).__name__}: {exc}",
        ]

    if not isinstance(config, dict):
        return {}, ["The Firebase secret must contain a JSON object."]

    required = ["project_id", "private_key", "client_email"]
    missing = [
        field for field in required
        if not str(config.get(field, "")).strip()
    ]

    if missing:
        return config, [
            "Missing required Firebase fields: " + ", ".join(missing)
        ]

    key = str(config["private_key"])
    key = key.replace("\\r\\n", "\n")
    key = key.replace("\\n", "\n")
    key = key.replace("\r\n", "\n")
    key = key.replace("\r", "\n")
    config["private_key"] = key

    if "BEGIN PRIVATE KEY" not in key:
        return config, ["The private_key does not appear to be a PEM private key."]

    return config, []


@st.cache_resource(show_spinner=False)
def connect_firebase():
    config, errors = load_firebase_config()

    if errors:
        return None, config, errors

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        try:
            firebase_admin.get_app()
        except ValueError:
            credential = credentials.Certificate(config)
            firebase_admin.initialize_app(credential)

        return firestore.client(), config, []

    except Exception as exc:
        return None, config, [
            "Firebase Admin SDK initialization failed.",
            f"{type(exc).__name__}: {exc}",
        ]


db, firebase_config, firebase_errors = connect_firebase()


# ============================================================
# Database helpers
# ============================================================

def collection(name):
    if db is None:
        return None
    return db.collection(name)


def set_doc(name, doc_id, data, merge=True):
    ref = collection(name)
    if ref is None:
        return False
    ref.document(doc_id).set(data, merge=merge)
    return True


def add_doc(name, data):
    ref = collection(name)
    if ref is None:
        return None
    _, document = ref.add(data)
    return document.id


def list_docs(name, limit=1000):
    ref = collection(name)
    if ref is None:
        return []

    rows = []
    for document in ref.limit(limit).stream():
        item = document.to_dict()
        item["_id"] = document.id
        rows.append(item)
    return rows


def now():
    return datetime.utcnow().isoformat() + "Z"


def new_id(prefix):
    return prefix + "-" + uuid.uuid4().hex[:10].upper()


def audit(action, details=None):
    try:
        add_doc(
            "audit_logs",
            {
                "action": action,
                "details": details or {},
                "created_at": now(),
            },
        )
    except Exception:
        pass


# ============================================================
# Home
# ============================================================

def home():
    st.markdown(
        """
        <div class="hero">
            <h1>Digital Registration and Selection System</h1>
            <p>
            A simple, transparent and auditable platform for participant
            registration, eligibility review, random selection, results
            management and reporting.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if db:
        st.success("Firebase Firestore is connected and ready.")
    else:
        st.error(
            "Firebase Admin is not connected. Configure the "
            "FIREBASE_SERVICE_ACCOUNT_JSON Streamlit Secret."
        )

    st.subheader("System overview")

    cards = [
        ("Registration", "Register participants through a simple form."),
        ("Eligibility", "Review and approve participants before selection."),
        ("Selection", "Select eligible participants randomly without replacement."),
        ("Results", "Review selected participants and maintain records."),
    ]

    columns = st.columns(4)
    for column, item in zip(columns, cards):
        with column:
            st.markdown(
                f'<div class="card"><h3>{item[0]}</h3><p>{item[1]}</p></div>',
                unsafe_allow_html=True,
            )

    st.subheader("Standard workflow")
    st.write(
        "Event creation -> registration -> verification -> eligibility -> "
        "random selection -> results -> reporting -> audit."
    )


# ============================================================
# Module 1
# ============================================================

def module1():
    st.header("Module 1: System Home")
    st.write(
        "This module introduces the DRSS workflow and provides a starting "
        "point for administrators and ordinary users."
    )

    st.subheader("Core principles")

    principles = [
        "Simple user interface",
        "Clear eligibility rules",
        "Controlled administration",
        "Random selection without replacement",
        "Persistent Firestore records",
        "Audit records for important actions",
        "Transparent result reporting",
    ]

    for item in principles:
        st.write(item)


# ============================================================
# Module 2
# ============================================================

def module2():
    st.header("Module 2: Participant Registration")

    with st.form("registration_form"):
        name = st.text_input("Full name")
        phone = st.text_input("Phone number")
        email = st.text_input("Email address")
        identification = st.text_input("Participant identification number")
        event_id = st.text_input("Event ID")
        confirmed = st.checkbox(
            "I confirm that the information provided is correct."
        )
        submitted = st.form_submit_button("Register participant")

    if not submitted:
        return

    if not name or not phone or not event_id:
        st.error("Full name, phone number and Event ID are required.")
        return

    if not confirmed:
        st.error("Please confirm the information.")
        return

    participant_id = new_id("P")

    record = {
        "participant_id": participant_id,
        "full_name": name,
        "phone": phone,
        "email": email,
        "identification": identification,
        "event_id": event_id,
        "status": "registered",
        "eligible": False,
        "created_at": now(),
    }

    if db:
        set_doc("participants", participant_id, record, False)
        audit(
            "participant_registered",
            {"participant_id": participant_id},
        )
        st.success(
            f"Registration completed. Participant ID: {participant_id}"
        )
    else:
        st.warning("Firebase is required to save the registration.")


# ============================================================
# Module 3
# ============================================================

def module3():
    st.header("Module 3: Eligibility Management")

    if not db:
        st.warning("Firebase is required.")
        return

    participants = list_docs("participants")

    if not participants:
        st.info("No participants have been registered.")
        return

    for participant in participants:
        participant_id = participant.get(
            "participant_id",
            participant["_id"],
        )

        with st.expander(
            f"{participant_id} | {participant.get('full_name', '')}"
        ):
            st.write(
                f"Event ID: {participant.get('event_id', '')}"
            )

            eligible = st.checkbox(
                "Eligible for selection",
                value=bool(participant.get("eligible")),
                key="eligibility_" + participant_id,
            )

            if st.button(
                "Save eligibility",
                key="save_eligibility_" + participant_id,
            ):
                set_doc(
                    "participants",
                    participant["_id"],
                    {
                        "eligible": eligible,
                        "status": (
                            "eligible" if eligible else "ineligible"
                        ),
                        "reviewed_at": now(),
                    },
                )

                audit(
                    "eligibility_updated",
                    {
                        "participant_id": participant_id,
                        "eligible": eligible,
                    },
                )

                st.success("Eligibility status saved.")


# ============================================================
# Module 4
# ============================================================

def module4():
    st.header("Module 4: Event Management")

    with st.form("event_form"):
        name = st.text_input("Event name")
        description = st.text_area("Event description")
        start_date = st.date_input(
            "Registration start date",
            date.today(),
        )
        end_date = st.date_input(
            "Registration end date",
            date.today(),
        )
        winners = st.number_input(
            "Number of winners",
            min_value=1,
            max_value=10000,
            value=1,
        )

        submitted = st.form_submit_button("Create event")

    if submitted:
        if not name:
            st.error("Event name is required.")
        elif end_date < start_date:
            st.error("End date cannot be earlier than start date.")
        elif not db:
            st.warning("Firebase is required.")
        else:
            event_id = new_id("EV")

            record = {
                "event_id": event_id,
                "event_name": name,
                "description": description,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "winners_count": int(winners),
                "status": "open",
                "created_at": now(),
            }

            set_doc("events", event_id, record, False)
            audit(
                "event_created",
                {"event_id": event_id},
            )
            st.success(f"Event created: {event_id}")

    if db:
        events = list_docs("events")
        if events:
            st.dataframe(
                events,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No events have been created.")


# ============================================================
# Module 5
# ============================================================

def module5():
    st.header("Module 5: Payment and Verification")

    st.write(
        "Record a payment reference. Automated payment processing requires "
        "an approved payment provider."
    )

    with st.form("payment_form"):
        participant_id = st.text_input("Participant ID")
        reference = st.text_input("Payment reference")
        amount = st.number_input(
            "Amount",
            min_value=0.0,
            value=0.0,
        )
        submitted = st.form_submit_button("Record payment")

    if not submitted:
        return

    if not participant_id or not reference:
        st.error("Participant ID and payment reference are required.")
        return

    if not db:
        st.warning("Firebase is required.")
        return

    payment_id = new_id("PAY")

    set_doc(
        "payments",
        payment_id,
        {
            "payment_id": payment_id,
            "participant_id": participant_id,
            "reference": reference,
            "amount": float(amount),
            "status": "pending_verification",
            "created_at": now(),
        },
        False,
    )

    audit(
        "payment_recorded",
        {"payment_id": payment_id},
    )

    st.success(f"Payment record created: {payment_id}")


# ============================================================
# Module 6
# ============================================================

def module6():
    st.header("Module 6: Document Verification")

    if not db:
        st.warning("Firebase is required.")
        return

    with st.form("verification_form"):
        participant_id = st.text_input("Participant ID")
        document_type = st.selectbox(
            "Document type",
            [
                "Identification",
                "Proof of payment",
                "Eligibility document",
                "Other",
            ],
        )
        status = st.selectbox(
            "Verification result",
            ["pending", "verified", "rejected"],
        )
        notes = st.text_area("Verification notes")
        submitted = st.form_submit_button("Save verification")

    if not submitted:
        return

    if not participant_id:
        st.error("Participant ID is required.")
        return

    verification_id = new_id("VER")

    set_doc(
        "verifications",
        verification_id,
        {
            "verification_id": verification_id,
            "participant_id": participant_id,
            "document_type": document_type,
            "status": status,
            "notes": notes,
            "created_at": now(),
        },
        False,
    )

    audit(
        "document_verification_saved",
        {"verification_id": verification_id},
    )

    st.success("Verification record saved.")


# ============================================================
# Module 7
# ============================================================

def module7():
    st.header("Module 7: Random Selection")

    st.write(
        "This module selects eligible participants using simple random "
        "sampling without replacement."
    )

    st.info(
        "For a regulated public lottery, formally define the legal rules, "
        "security controls, independent oversight and randomness "
        "verification requirements before production use."
    )

    if not db:
        st.warning("Firebase is required.")
        return

    events = list_docs("events")

    if not events:
        st.info("Create an event first.")
        return

    labels = [
        f"{event.get('event_id')} | {event.get('event_name')}"
        for event in events
    ]

    selected_label = st.selectbox(
        "Select event",
        labels,
    )

    event = events[labels.index(selected_label)]

    participants = list_docs("participants")

    eligible = [
        participant
        for participant in participants
        if participant.get("event_id") == event.get("event_id")
        and bool(participant.get("eligible"))
    ]

    population = len(eligible)
    requested = int(event.get("winners_count", 1))
    winner_count = min(requested, population)

    columns = st.columns(3)
    columns[0].metric(
        "Eligible population",
        population,
    )
    columns[1].metric(
        "Requested winners",
        requested,
    )
    columns[2].metric(
        "Winners possible",
        winner_count,
    )

    if population == 0:
        st.warning(
            "There are no eligible participants for this event."
        )
        return

    confirmed = st.checkbox(
        "I have reviewed the eligible population and event rules."
    )

    if st.button(
        "Run random selection",
        disabled=not confirmed,
    ):
        selected = random.SystemRandom().sample(
            eligible,
            winner_count,
        )

        selection_id = new_id("SEL")
        selection_time = now()

        set_doc(
            "selections",
            selection_id,
            {
                "selection_id": selection_id,
                "event_id": event.get("event_id"),
                "selected_at": selection_time,
                "method": (
                    "simple_random_sample_without_replacement"
                ),
                "population_size": population,
                "winner_count": winner_count,
                "winner_ids": [
                    participant.get("participant_id")
                    for participant in selected
                ],
            },
            False,
        )

        for rank, participant in enumerate(
            selected,
            start=1,
        ):
            winner_id = new_id("WIN")

            set_doc(
                "winners",
                winner_id,
                {
                    "winner_id": winner_id,
                    "selection_id": selection_id,
                    "event_id": event.get("event_id"),
                    "participant_id": participant.get(
                        "participant_id"
                    ),
                    "full_name": participant.get(
                        "full_name"
                    ),
                    "rank": rank,
                    "selected_at": selection_time,
                },
                False,
            )

        audit(
            "random_selection_completed",
            {
                "selection_id": selection_id,
                "event_id": event.get("event_id"),
                "population_size": population,
                "winner_count": winner_count,
            },
        )

        st.success(
            f"Selection completed. Selection ID: {selection_id}"
        )

        st.subheader("Selected participants")

        for rank, participant in enumerate(
            selected,
            start=1,
        ):
            st.write(
                f"{rank}. "
                f"{participant.get('participant_id')} - "
                f"{participant.get('full_name')}"
            )


# ============================================================
# Module 8
# ============================================================

def module8():
    st.header("Module 8: Results")

    if not db:
        st.warning("Firebase is required.")
        return

    winners = list_docs("winners")

    if winners:
        st.dataframe(
            winners,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No results are available.")


# ============================================================
# Module 9
# ============================================================

def module9():
    st.header("Module 9: Notifications")

    if not db:
        st.warning("Firebase is required.")
        return

    with st.form("notification_form"):
        participant_id = st.text_input("Participant ID")
        channel = st.selectbox(
            "Channel",
            ["SMS", "Email"],
        )
        message = st.text_area("Message")
        submitted = st.form_submit_button(
            "Queue notification"
        )

    if not submitted:
        return

    if not participant_id or not message:
        st.error(
            "Participant ID and message are required."
        )
        return

    notification_id = new_id("NOT")

    set_doc(
        "notifications",
        notification_id,
        {
            "notification_id": notification_id,
            "participant_id": participant_id,
            "channel": channel,
            "message": message,
            "status": "queued",
            "created_at": now(),
        },
        False,
    )

    audit(
        "notification_created",
        {"notification_id": notification_id},
    )

    st.success(
        f"Notification queued: {notification_id}"
    )


# ============================================================
# Module 10
# ============================================================

def module10():
    st.header("Module 10: Reports and Statistics")

    if not db:
        st.warning("Firebase is required.")
        return

    participants = list_docs(
        "participants",
        2000,
    )
    events = list_docs(
        "events",
        1000,
    )
    winners = list_docs(
        "winners",
        2000,
    )
    payments = list_docs(
        "payments",
        2000,
    )

    columns = st.columns(4)

    columns[0].metric(
        "Participants",
        len(participants),
    )
    columns[1].metric(
        "Events",
        len(events),
    )
    columns[2].metric(
        "Winners",
        len(winners),
    )
    columns[3].metric(
        "Payment records",
        len(payments),
    )

    if participants:
        st.subheader("Participants")
        st.dataframe(
            participants,
            use_container_width=True,
            hide_index=True,
        )

    if winners:
        st.subheader("Winners")
        st.dataframe(
            winners,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# Module 11
# ============================================================

def module11():
    st.header("Module 11: Audit Trail")

    if not db:
        st.warning("Firebase is required.")
        return

    logs = list_docs(
        "audit_logs",
        2000,
    )

    if logs:
        st.dataframe(
            logs,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No audit records are available.")


# ============================================================
# Module 12
# ============================================================

def module12():
    st.header("Module 12: Administration and System Health")

    if db:
        st.success(
            "Firebase Admin SDK and Firestore are connected."
        )

        st.write(
            "Project ID:",
            firebase_config.get(
                "project_id",
                "",
            ),
        )

        email = firebase_config.get(
            "client_email",
            "",
        )

        if "@" in email:
            local, domain = email.split(
                "@",
                1,
            )
            masked = (
                local[:2]
                + "*" * max(1, len(local) - 2)
                + "@"
                + domain
            )
        else:
            masked = "Configured"

        st.write(
            "Service account:",
            masked,
        )

        fingerprint = hashlib.sha256(
            email.encode()
        ).hexdigest()[:12].upper()

        st.write(
            "Credential fingerprint:",
            fingerprint,
        )

    else:
        st.error(
            "Firebase Admin SDK is not connected."
        )

        for error in firebase_errors:
            st.code(error)

    st.subheader("Configuration diagnostics")

    diagnostics = [
        {
            "configuration": (
                "FIREBASE_SERVICE_ACCOUNT_JSON"
            ),
            "status": (
                "Detected"
                if get_secret_json()
                else "Missing"
            ),
        },
        {
            "configuration": "project_id",
            "status": (
                "Detected"
                if firebase_config.get("project_id")
                else "Missing"
            ),
        },
        {
            "configuration": "private_key",
            "status": (
                "Detected"
                if firebase_config.get("private_key")
                else "Missing"
            ),
        },
        {
            "configuration": "client_email",
            "status": (
                "Detected"
                if firebase_config.get("client_email")
                else "Missing"
            ),
        },
    ]

    st.dataframe(
        diagnostics,
        use_container_width=True,
        hide_index=True,
    )

    st.info(
        "The private key is never displayed. Keep the Firebase "
        "service-account JSON out of GitHub and do not put the "
        "private key directly into app.py."
    )

    st.subheader(
        "Required Streamlit Secret"
    )

    secret_lines = [
        'FIREBASE_SERVICE_ACCOUNT_JSON = \'\'\'',
        '{',
        '  "type": "service_account",',
        '  "project_id": "drs-system-bffd7",',
        '  "private_key_id": "YOUR_REAL_VALUE",',
        '  "private_key": "-----BEGIN PRIVATE KEY-----\\\\nYOUR_REAL_KEY\\\\n-----END PRIVATE KEY-----\\\\n",',
        '  "client_email": "YOUR_REAL_SERVICE_ACCOUNT_EMAIL",',
        '  "client_id": "YOUR_REAL_VALUE",',
        '  "auth_uri": "https://accounts.google.com/o/oauth2/auth",',
        '  "token_uri": "https://oauth2.googleapis.com/token"',
        '}',
        '\'\'\'',
    ]

    st.code(
        "\n".join(secret_lines),
        language="toml",
    )


# ============================================================
# Navigation
# ============================================================

PAGES = {
    "Home": home,
    "Module 1: System Home": module1,
    "Module 2: Registration": module2,
    "Module 3: Eligibility": module3,
    "Module 4: Event Management": module4,
    "Module 5: Payment": module5,
    "Module 6: Document Verification": module6,
    "Module 7: Random Selection": module7,
    "Module 8: Results": module8,
    "Module 9: Notifications": module9,
    "Module 10: Reports": module10,
    "Module 11: Audit Trail": module11,
    "Module 12: Administration": module12,
}


with st.sidebar:
    st.markdown("## DRSS")
    st.caption(
        "Digital Registration and Selection System"
    )

    page = st.radio(
        "Navigation",
        list(PAGES.keys()),
    )

    st.divider()

    st.caption("Application")
    st.write(f"Version {VERSION}")

    st.caption("Firebase project")
    st.write(
        firebase_config.get(
            "project_id",
            "Not configured",
        )
    )

    st.caption("Database status")
    st.write(
        "Connected"
        if db
        else "Not connected"
    )


PAGES[page]()
