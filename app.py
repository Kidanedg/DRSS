"""
DRSS — Digital Registration and Selection System
Single-file Streamlit application
Modules 1–12 in one app.py

Backend:
- Firebase Firestore for persistent data
- Firebase Authentication via Firebase Web API for admin email/password
- No Firebase Storage required in this version
- Designed for GitHub -> Streamlit Community Cloud

IMPORTANT:
1. Put Firebase web configuration in Streamlit Secrets.
2. Create an admin user in Firebase Authentication.
3. Add that admin email to [admin] in Streamlit Secrets.
4. Configure Firestore Security Rules appropriately for your deployment.
"""

import random
import secrets
from datetime import datetime, timezone
from io import BytesIO

import pandas as pd
import requests
import streamlit as st

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except Exception:
    firebase_admin = None
    credentials = None
    firestore = None


# ============================================================
# APP CONFIG
# ============================================================

st.set_page_config(
    page_title="DRSS — Digital Registration & Selection System",
    page_icon="🎟️",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "Digital Registration and Selection System"
APP_SHORT = "DRSS"


# ============================================================
# UI
# ============================================================

st.markdown(
    """
    <style>
    .drss-title {font-size:2.25rem;font-weight:800;margin-bottom:.1rem;}
    .drss-subtitle {opacity:.75;margin-bottom:1rem;}
    .ticket-box {
        padding:24px;border:2px solid rgba(49,51,63,.20);
        border-radius:16px;text-align:center;margin:12px 0;
    }
    .ticket-number {font-size:2rem;font-weight:800;letter-spacing:1px;}
    .status-box {padding:16px;border-radius:12px;margin:8px 0;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CONFIG / FIREBASE
# ============================================================

def secret_value(section, key, default=None):
    try:
        return st.secrets[section][key]
    except Exception:
        try:
            return st.secrets[key]
        except Exception:
            return default


def firebase_web_config():
    return {
        "apiKey": secret_value("firebase", "apiKey"),
        "authDomain": secret_value("firebase", "authDomain"),
        "projectId": secret_value("firebase", "projectId"),
        "storageBucket": secret_value("firebase", "storageBucket"),
        "messagingSenderId": secret_value("firebase", "messagingSenderId"),
        "appId": secret_value("firebase", "appId"),
    }


def get_db():
    if firebase_admin is None:
        st.error("firebase-admin is not installed. Check requirements.txt.")
        st.stop()

    if not firebase_admin._apps:
        project_id = secret_value("firebase", "projectId")
        private_key = secret_value("firebase_admin", "private_key")
        client_email = secret_value("firebase_admin", "client_email")
        private_key_id = secret_value("firebase_admin", "private_key_id")
        client_id = secret_value("firebase_admin", "client_id")

        if not project_id or not private_key or not client_email:
            st.error(
                "Firebase Admin credentials are missing. "
                "Add [firebase_admin] credentials to Streamlit Secrets."
            )
            st.stop()

        private_key = private_key.replace("\\n", "\n")

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
            "client_x509_cert_url": (
                "https://www.googleapis.com/robot/v1/metadata/"
                f"x509/{client_email.replace('@', '%40')}"
            ),
        }

        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred)

    return firestore.client()


# ============================================================
# COMMON HELPERS
# ============================================================

def now_iso():
    return datetime.now(timezone.utc).isoformat()


def normalize_phone(phone):
    phone = "".join(c for c in str(phone).strip() if c.isdigit() or c == "+")
    if phone.startswith("09") and len(phone) == 10:
        return "+251" + phone[1:]
    if phone.startswith("9") and len(phone) == 9:
        return "+251" + phone
    if phone.startswith("2519") and len(phone) == 12:
        return "+" + phone
    return phone


def valid_phone(phone):
    p = normalize_phone(phone)
    return p.startswith("+") and p[1:].isdigit() and 10 <= len(p[1:]) <= 15


def clean(value, limit=500):
    return str(value or "").strip()[:limit]


def ticket_number(event_id):
    db = get_db()
    while True:
        code = f"DRSS-{datetime.now().year}-{secrets.randbelow(999999)+1:06d}"
        if not list(db.collection("participants")
                    .where("ticket_number", "==", code)
                    .limit(1).stream()):
            return code


def event_list(open_only=False):
    db = get_db()
    docs = db.collection("events").stream()
    rows = []
    for d in docs:
        x = d.to_dict()
        x["id"] = d.id
        if open_only and x.get("status") != "OPEN":
            continue
        rows.append(x)
    rows.sort(key=lambda x: (str(x.get("event_date", "")), x["id"]))
    return rows


def get_event(event_id):
    db = get_db()
    snap = db.collection("events").document(event_id).get()
    if not snap.exists:
        return None
    x = snap.to_dict()
    x["id"] = snap.id
    return x


def participant_docs(event_id=None):
    db = get_db()
    ref = db.collection("participants")
    if event_id:
        ref = ref.where("event_id", "==", event_id)
    return list(ref.stream())


def participant_count(event_id):
    return len(participant_docs(event_id))


def participant_by_ticket(ticket):
    db = get_db()
    docs = list(
        db.collection("participants")
        .where("ticket_number", "==", clean(ticket))
        .limit(1).stream()
    )
    if not docs:
        return None
    x = docs[0].to_dict()
    x["id"] = docs[0].id
    return x


def participant_by_phone(phone):
    db = get_db()
    p = normalize_phone(phone)
    docs = list(
        db.collection("participants")
        .where("phone", "==", p)
        .limit(20).stream()
    )
    if not docs:
        return None
    docs.sort(
        key=lambda d: d.to_dict().get("created_at", ""),
        reverse=True
    )
    x = docs[0].to_dict()
    x["id"] = docs[0].id
    return x


def log_action(action, actor, details=None):
    db = get_db()
    db.collection("audit_logs").add({
        "action": action,
        "actor": actor or "PUBLIC",
        "details": details or {},
        "created_at": now_iso(),
    })


def is_admin_email(email):
    allowed = secret_value("admin", "emails", "")
    if isinstance(allowed, str):
        allowed = [x.strip().lower() for x in allowed.split(",") if x.strip()]
    return str(email or "").lower() in allowed


def status_badge(value):
    value = str(value or "UNKNOWN")
    if value in ("APPROVED", "SELECTED", "OPEN", "PUBLISHED"):
        st.success(value)
    elif value in ("PENDING", "REGISTERED"):
        st.warning(value)
    elif value in ("REJECTED", "CLOSED", "NOT_SELECTED"):
        st.info(value)
    else:
        st.write(value)


# ============================================================
# MODULE 1 — PUBLIC HOME
# ============================================================

def module_1():
    st.markdown(
        f'<div class="drss-title">🎟️ {APP_NAME}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="drss-subtitle">'
        "Simple registration • transparent status • controlled selection"
        "</div>",
        unsafe_allow_html=True,
    )

    events = event_list(open_only=True)

    if not events:
        st.info("There is currently no open registration event.")
        return

    event = events[0]
    n = participant_count(event["id"])

    a, b, c, d = st.columns(4)
    a.metric("Event", str(event.get("name", ""))[:25])
    b.metric("Registered", n)
    c.metric("Capacity", event.get("max_participants", 0))
    d.metric(
        "Fee",
        f"{event.get('registration_fee', 0):,.2f} "
        f"{event.get('currency', 'ETB')}",
    )

    st.divider()
    st.subheader(event.get("name", "DRSS Event"))
    st.write(event.get("description", ""))
    st.markdown(f"**Date:** {event.get('event_date', '')}")
    st.markdown(f"**Location:** {event.get('location', '')}")

    st.subheader("How DRSS works")
    st.markdown(
        """
        1. **Register** — enter your information once.
        2. **Receive a ticket** — save your unique DRSS ticket.
        3. **Payment verification** — where applicable, the organizer verifies it.
        4. **Check status** — use your ticket or phone number.
        5. **Selection** — eligible participants are selected according to event rules.
        6. **Results** — published winners can be verified publicly.
        """
    )


# ============================================================
# MODULE 2 — REGISTRATION
# ============================================================

def module_2():
    st.title("📝 Module 2 — Participant Registration")
    events = event_list(open_only=True)

    if not events:
        st.warning("No open event is available.")
        return

    labels = {
        f"{e.get('name','')} — {e.get('event_date','')}": e["id"]
        for e in events
    }
    label = st.selectbox("Select event *", list(labels))
    eid = labels[label]
    event = get_event(eid)

    current = participant_count(eid)
    st.info(
        f"{current:,} / {event.get('max_participants', 0):,} places used."
    )

    if current >= int(event.get("max_participants", 0)):
        st.error("Registration capacity has been reached.")
        return

    with st.form("drss_registration"):
        st.subheader("Personal information")
        full_name = st.text_input("Full name *")
        c1, c2 = st.columns(2)
        with c1:
            phone = st.text_input("Phone number *")
            email = st.text_input("Email")
            sex = st.selectbox(
                "Sex",
                ["Prefer not to say", "Male", "Female", "Other"]
            )
        with c2:
            age = st.number_input("Age", 0, 120, 0)
            region = st.text_input("Region")
            zone = st.text_input("Zone")

        c3, c4 = st.columns(2)
        with c3:
            woreda = st.text_input("Woreda")
            kebele = st.text_input("Kebele")
        with c4:
            address = st.text_input("Address")
            id_number = st.text_input("ID / National ID (optional)")

        st.subheader("Payment information")
        payment_reference = st.text_input("Payment / transaction reference")
        payment_method = st.selectbox(
            "Payment method",
            ["Not applicable", "Bank", "Mobile Money", "Cash", "Other"]
        )
        amount = st.number_input(
            "Amount paid",
            min_value=0.0,
            value=float(event.get("registration_fee", 0)),
            step=10.0,
        )

        notes = st.text_area("Additional note")
        consent = st.checkbox(
            "I confirm that the information entered is correct."
        )

        submit = st.form_submit_button(
            "🎟️ Submit Registration",
            type="primary",
            use_container_width=True,
        )

    if not submit:
        return

    errors = []
    if len(clean(full_name)) < 2:
        errors.append("Enter your full name.")
    if not valid_phone(phone):
        errors.append("Enter a valid phone number.")
    if not consent:
        errors.append("Confirm the information is correct.")
    if float(event.get("registration_fee", 0)) > amount:
        errors.append("The payment amount is below the required fee.")

    normalized = normalize_phone(phone)

    db = get_db()
    duplicate = list(
        db.collection("participants")
        .where("event_id", "==", eid)
        .where("phone", "==", normalized)
        .limit(1).stream()
    )

    if duplicate:
        errors.append(
            "This phone number is already registered for this event."
        )

    if errors:
        for e in errors:
            st.error(e)
        return

    ticket = ticket_number(eid)
    payment_required = float(event.get("registration_fee", 0)) > 0

    data = {
        "ticket_number": ticket,
        "event_id": eid,
        "full_name": clean(full_name),
        "phone": normalized,
        "email": clean(email),
        "sex": clean(sex),
        "age": int(age) if age else None,
        "region": clean(region),
        "zone": clean(zone),
        "woreda": clean(woreda),
        "kebele": clean(kebele),
        "address": clean(address),
        "id_number": clean(id_number),
        "payment_reference": clean(payment_reference),
        "payment_method": clean(payment_method),
        "payment_amount": float(amount),
        "payment_status": "PENDING" if payment_required else "NOT_REQUIRED",
        "registration_status": "REGISTERED",
        "selection_status": "NOT_SELECTED",
        "notes": clean(notes),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }

    db.collection("participants").add(data)
    log_action(
        "PARTICIPANT_REGISTERED",
        "PUBLIC",
        {"ticket_number": ticket, "event_id": eid},
    )

    st.success("Registration completed successfully.")
    st.markdown(
        f"""
        <div class="ticket-box">
        <div>Your DRSS Ticket Number</div>
        <div class="ticket-number">{ticket}</div>
        <div>Save this number.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    confirmation = (
        "DRSS REGISTRATION CONFIRMATION\n\n"
        f"Name: {data['full_name']}\n"
        f"Ticket: {ticket}\n"
        f"Event: {event.get('name','')}\n"
        f"Date: {event.get('event_date','')}\n"
        f"Registration status: REGISTERED\n"
        f"Payment status: {data['payment_status']}\n"
    )

    st.download_button(
        "⬇️ Download confirmation",
        confirmation,
        file_name=f"{ticket}.txt",
        mime="text/plain",
        use_container_width=True,
    )


# ============================================================
# MODULE 3 — STATUS / RESULTS
# ============================================================

def module_3():
    st.title("🔎 Module 3 — Check Status")

    method = st.radio(
        "Search using",
        ["Ticket Number", "Phone Number"],
        horizontal=True,
    )

    if method == "Ticket Number":
        ticket = st.text_input("DRSS Ticket Number")
        phone = ""
    else:
        phone = st.text_input("Registered phone number")
        ticket = ""

    if st.button("🔎 Check", type="primary", use_container_width=True):
        p = (
            participant_by_ticket(ticket)
            if ticket.strip()
            else participant_by_phone(phone)
        )

        if not p:
            st.error("No registration was found.")
            return

        event = get_event(p.get("event_id"))
        st.success("Registration found.")

        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Name:** {p.get('full_name','')}")
            st.write(f"**Ticket:** `{p.get('ticket_number','')}`")
            st.write(f"**Event:** {event.get('name','') if event else ''}")
        with c2:
            st.write(f"**Registration:** {p.get('registration_status','')}")
            st.write(f"**Payment:** {p.get('payment_status','')}")
            st.write(f"**Selection:** {p.get('selection_status','')}")

        if p.get("selection_status") == "SELECTED":
            st.success("🎉 Congratulations! Your ticket was selected.")
        elif p.get("payment_status") == "PENDING":
            st.warning("Payment verification is still pending.")
        else:
            st.info(
                "Your registration is recorded. Selection status may change "
                "when the organizer completes the selection."
            )


# ============================================================
# MODULE 4 — ADMIN LOGIN
# ============================================================

def module_4_login():
    st.title("🔐 Module 4 — Administrator Login")
    st.write(
        "This application expects the administrator to authenticate "
        "through the configured Firebase/Streamlit authentication layer."
    )

    st.info(
        "For a simple Streamlit deployment, this version uses an admin "
        "password stored as a Streamlit secret. You can later replace "
        "this with a full OAuth/Firebase Identity flow."
    )

    with st.form("admin_login"):
        email = st.text_input("Administrator email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign in", type="primary")

    if submit:
        expected_email = secret_value("admin", "email", "")
        expected_password = secret_value("admin", "password", "")

        if (
            email.lower().strip() == str(expected_email).lower().strip()
            and password == expected_password
            and is_admin_email(email)
        ):
            st.session_state["admin_authenticated"] = True
            st.session_state["admin_email"] = email.strip()
            st.success("Administrator signed in.")
            st.rerun()
        else:
            st.error("Invalid administrator credentials.")


def admin_required():
    return bool(st.session_state.get("admin_authenticated"))


# ============================================================
# MODULE 5 — EVENT MANAGEMENT
# ============================================================

def module_5():
    if not admin_required():
        st.warning("Administrator login required.")
        module_4_login()
        return

    st.title("🗓️ Module 5 — Event Management")
    db = get_db()

    st.subheader("Create new event")
    with st.form("new_event"):
        name = st.text_input("Event name *")
        description = st.text_area("Description")
        location = st.text_input("Location")
        event_date = st.date_input("Event date", value=datetime.now().date())
        fee = st.number_input("Registration fee", min_value=0.0, step=10.0)
        currency = st.text_input("Currency", value="ETB")
        capacity = st.number_input("Maximum participants", 1, 1000000, 1000)
        create = st.form_submit_button("Create event", type="primary")

    if create:
        if not clean(name):
            st.error("Event name is required.")
        else:
            db.collection("events").add({
                "name": clean(name),
                "description": clean(description, 2000),
                "location": clean(location),
                "event_date": str(event_date),
                "registration_fee": float(fee),
                "currency": clean(currency, 10),
                "max_participants": int(capacity),
                "status": "OPEN",
                "created_at": now_iso(),
                "created_by": st.session_state.get("admin_email"),
            })
            log_action(
                "EVENT_CREATED",
                st.session_state.get("admin_email"),
                {"name": name},
            )
            st.success("Event created.")
            st.rerun()

    st.divider()
    st.subheader("Existing events")

    for event in event_list():
        with st.expander(
            f"{event.get('name','')} — {event.get('status','')}"
        ):
            st.write(
                f"Date: {event.get('event_date','')} | "
                f"Capacity: {event.get('max_participants',0)} | "
                f"Fee: {event.get('registration_fee',0)} "
                f"{event.get('currency','ETB')}"
            )

            if event.get("status") == "OPEN":
                if st.button(
                    f"Close {event['id']}",
                    key=f"close_{event['id']}"
                ):
                    db.collection("events").document(event["id"]).update({
                        "status": "CLOSED",
                        "updated_at": now_iso(),
                    })
                    log_action(
                        "EVENT_CLOSED",
                        st.session_state.get("admin_email"),
                        {"event_id": event["id"]},
                    )
                    st.rerun()
            else:
                if st.button(
                    f"Open {event['id']}",
                    key=f"open_{event['id']}"
                ):
                    db.collection("events").document(event["id"]).update({
                        "status": "OPEN",
                        "updated_at": now_iso(),
                    })
                    log_action(
                        "EVENT_OPENED",
                        st.session_state.get("admin_email"),
                        {"event_id": event["id"]},
                    )
                    st.rerun()


# ============================================================
# MODULE 6 — PARTICIPANT MANAGEMENT
# ============================================================

def module_6():
    if not admin_required():
        st.warning("Administrator login required.")
        module_4_login()
        return

    st.title("👥 Module 6 — Participant Management")

    events = event_list()
    if not events:
        st.info("No events.")
        return

    labels = {
        f"{e.get('name','')} — {e.get('event_date','')}": e["id"]
        for e in events
    }
    label = st.selectbox("Event", list(labels))
    eid = labels[label]

    docs = participant_docs(eid)
    rows = []
    for d in docs:
        x = d.to_dict()
        x["id"] = d.id
        rows.append(x)

    if not rows:
        st.info("No participants.")
        return

    df = pd.DataFrame(rows)

    search = st.text_input("Search name / ticket / phone")
    if search:
        s = search.lower()
        mask = (
            df["full_name"].fillna("").str.lower().str.contains(s)
            | df["ticket_number"].fillna("").str.lower().str.contains(s)
            | df["phone"].fillna("").str.lower().str.contains(s)
        )
        df = df[mask]

    st.dataframe(
        df[
            [
                "ticket_number",
                "full_name",
                "phone",
                "payment_status",
                "registration_status",
                "selection_status",
                "created_at",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "⬇️ Export participants CSV",
        df.to_csv(index=False).encode("utf-8"),
        "drss_participants.csv",
        "text/csv",
        use_container_width=True,
    )


# ============================================================
# MODULE 7 — PAYMENT VERIFICATION
# ============================================================

def module_7():
    if not admin_required():
        st.warning("Administrator login required.")
        module_4_login()
        return

    st.title("💳 Module 7 — Payment Verification")
    db = get_db()

    pending = []
    for d in db.collection("participants").stream():
        x = d.to_dict()
        if x.get("payment_status") == "PENDING":
            x["id"] = d.id
            pending.append(x)

    st.metric("Pending payments", len(pending))

    if not pending:
        st.success("No pending payments.")
        return

    for p in pending:
        with st.expander(
            f"{p.get('ticket_number')} — {p.get('full_name')}"
        ):
            st.write(f"Phone: {p.get('phone')}")
            st.write(f"Reference: {p.get('payment_reference')}")
            st.write(f"Amount: {p.get('payment_amount')}")
            st.write(f"Method: {p.get('payment_method')}")

            c1, c2 = st.columns(2)

            if c1.button(
                "✅ Approve",
                key=f"approve_{p['id']}",
                use_container_width=True,
            ):
                db.collection("participants").document(p["id"]).update({
                    "payment_status": "APPROVED",
                    "payment_verified_by":
                        st.session_state.get("admin_email"),
                    "payment_verified_at": now_iso(),
                    "updated_at": now_iso(),
                })
                log_action(
                    "PAYMENT_APPROVED",
                    st.session_state.get("admin_email"),
                    {"ticket": p.get("ticket_number")},
                )
                st.rerun()

            if c2.button(
                "❌ Reject",
                key=f"reject_{p['id']}",
                use_container_width=True,
            ):
                db.collection("participants").document(p["id"]).update({
                    "payment_status": "REJECTED",
                    "payment_verified_by":
                        st.session_state.get("admin_email"),
                    "payment_verified_at": now_iso(),
                    "updated_at": now_iso(),
                })
                log_action(
                    "PAYMENT_REJECTED",
                    st.session_state.get("admin_email"),
                    {"ticket": p.get("ticket_number")},
                )
                st.rerun()


# ============================================================
# MODULE 8 — DIGITAL SELECTION
# ============================================================

def module_8():
    if not admin_required():
        st.warning("Administrator login required.")
        module_4_login()
        return

    st.title("🎲 Module 8 — Digital Selection")

    events = event_list()
    if not events:
        st.info("No events.")
        return

    labels = {
        f"{e.get('name','')} — {e.get('event_date','')}": e["id"]
        for e in events
    }
    label = st.selectbox("Event", list(labels))
    eid = labels[label]
    event = get_event(eid)

    db = get_db()

    participants = []
    for d in db.collection("participants").where(
        "event_id", "==", eid
    ).stream():
        x = d.to_dict()
        x["id"] = d.id
        eligible = (
            x.get("registration_status") == "REGISTERED"
            and x.get("payment_status") in ("APPROVED", "NOT_REQUIRED")
        )
        if eligible:
            participants.append(x)

    st.metric("Eligible participants", len(participants))

    if not participants:
        st.warning("There are no eligible participants.")
        return

    winners_requested = st.number_input(
        "Number of winners",
        min_value=1,
        max_value=len(participants),
        value=min(1, len(participants)),
    )

    existing = list(
        db.collection("selections")
        .where("event_id", "==", eid)
        .limit(1).stream()
    )

    if existing:
        st.warning(
            "A selection record already exists for this event. "
            "Do not run another selection unless the organizer intentionally "
            "creates a new official selection."
        )

    confirm = st.checkbox(
        "I confirm that the eligible list is correct and I want to run the official selection."
    )

    if st.button(
        "🎲 RUN OFFICIAL RANDOM SELECTION",
        type="primary",
        use_container_width=True,
        disabled=bool(existing),
    ):
        if not confirm:
            st.error("Please confirm before running the selection.")
            return

        # System randomness from Python's cryptographic RNG.
        # The complete eligible list is stored with the selection record.
        eligible_ids = [p["id"] for p in participants]
        selected = secrets.SystemRandom().sample(
            eligible_ids,
            int(winners_requested),
        )

        selection_id = f"SEL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        selected_tickets = []

        for rank, pid in enumerate(selected, start=1):
            p = next(x for x in participants if x["id"] == pid)
            db.collection("participants").document(pid).update({
                "selection_status": "SELECTED",
                "selection_rank": rank,
                "selection_id": selection_id,
                "updated_at": now_iso(),
            })
            selected_tickets.append(p.get("ticket_number"))

        db.collection("selections").document(selection_id).set({
            "event_id": eid,
            "event_name": event.get("name"),
            "requested_winners": int(winners_requested),
            "eligible_count": len(participants),
            "eligible_participant_ids": eligible_ids,
            "selected_participant_ids": selected,
            "selected_tickets": selected_tickets,
            "selection_id": selection_id,
            "selected_at": now_iso(),
            "selected_by": st.session_state.get("admin_email"),
            "status": "COMPLETED",
        })

        log_action(
            "OFFICIAL_SELECTION_COMPLETED",
            st.session_state.get("admin_email"),
            {
                "event_id": eid,
                "selection_id": selection_id,
                "winner_count": len(selected),
            },
        )

        st.success(f"Selection completed: {selection_id}")
        for rank, pid in enumerate(selected, start=1):
            p = next(x for x in participants if x["id"] == pid)
            st.write(
                f"**Winner {rank}:** {p.get('full_name')} — "
                f"`{p.get('ticket_number')}`"
            )


# ============================================================
# MODULE 9 — PUBLIC WINNERS
# ============================================================

def module_9():
    st.title("🏆 Module 9 — Winners")

    db = get_db()
    events = event_list()

    if not events:
        st.info("No events.")
        return

    labels = {
        f"{e.get('name','')} — {e.get('event_date','')}": e["id"]
        for e in events
    }
    label = st.selectbox("Event", list(labels))
    eid = labels[label]

    docs = list(
        db.collection("participants")
        .where("event_id", "==", eid)
        .where("selection_status", "==", "SELECTED")
        .stream()
    )

    if not docs:
        st.info("No published winners for this event.")
        return

    winners = []
    for d in docs:
        x = d.to_dict()
        winners.append({
            "Rank": x.get("selection_rank", ""),
            "Name": x.get("full_name", ""),
            "Ticket": x.get("ticket_number", ""),
        })

    winners.sort(key=lambda x: int(x["Rank"]) if str(x["Rank"]).isdigit() else 999)

    st.success("Official selected winners")
    st.dataframe(
        pd.DataFrame(winners),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# MODULE 10 — REPORTS
# ============================================================

def module_10():
    if not admin_required():
        st.warning("Administrator login required.")
        module_4_login()
        return

    st.title("📊 Module 10 — Reports")

    db = get_db()
    docs = list(db.collection("participants").stream())

    if not docs:
        st.info("No participant data.")
        return

    rows = []
    for d in docs:
        x = d.to_dict()
        x["id"] = d.id
        rows.append(x)

    df = pd.DataFrame(rows)

    a, b, c, d = st.columns(4)
    a.metric("Total", len(df))
    b.metric(
        "Payment approved",
        int((df["payment_status"] == "APPROVED").sum()),
    )
    c.metric(
        "Payment pending",
        int((df["payment_status"] == "PENDING").sum()),
    )
    d.metric(
        "Selected",
        int((df["selection_status"] == "SELECTED").sum()),
    )

    st.subheader("Registration summary by event")
    summary = (
        df.groupby("event_id")
        .size()
        .reset_index(name="registrations")
    )
    st.dataframe(summary, use_container_width=True, hide_index=True)

    st.subheader("Full report")
    st.dataframe(df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download CSV report",
        csv,
        "drss_full_report.csv",
        "text/csv",
        use_container_width=True,
    )

    # Excel download if openpyxl is available.
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Participants")
            summary.to_excel(writer, index=False, sheet_name="Event Summary")
        st.download_button(
            "⬇️ Download Excel report",
            output.getvalue(),
            "drss_report.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    except Exception:
        st.caption("Excel export is unavailable; CSV export is available.")


# ============================================================
# MODULE 11 — SYSTEM SETTINGS
# ============================================================

def module_11():
    if not admin_required():
        st.warning("Administrator login required.")
        module_4_login()
        return

    st.title("⚙️ Module 11 — System Settings")

    st.subheader("Application information")
    st.write(f"Application: **{APP_NAME}**")
    st.write("Version: **1.0 — Modules 1–12 single-file architecture**")
    st.write("Backend: **Firebase Firestore**")

    st.subheader("Administrator")
    st.write(
        f"Current administrator: "
        f"**{st.session_state.get('admin_email', 'Unknown')}**"
    )

    st.subheader("Available events")
    for event in event_list():
        st.write(
            f"- {event.get('name')} | {event.get('status')} | "
            f"{event.get('event_date')}"
        )

    st.warning(
        "Production settings such as Firebase Security Rules, backups, "
        "administrator permissions, privacy policy, and retention periods "
        "must be configured before public deployment."
    )


# ============================================================
# MODULE 12 — AUDIT LOG
# ============================================================

def module_12():
    if not admin_required():
        st.warning("Administrator login required.")
        module_4_login()
        return

    st.title("📜 Module 12 — Audit Log")

    db = get_db()
    docs = list(
        db.collection("audit_logs")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(500)
        .stream()
    )

    if not docs:
        st.info("No audit records.")
        return

    rows = []
    for d in docs:
        x = d.to_dict()
        x["id"] = d.id
        rows.append(x)

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

def admin_dashboard():
    if not admin_required():
        module_4_login()
        return

    st.title("🛡️ DRSS Administrator Dashboard")
    st.caption(
        f"Signed in as {st.session_state.get('admin_email','')}"
    )

    if st.button("Logout"):
        st.session_state["admin_authenticated"] = False
        st.session_state["admin_email"] = ""
        st.rerun()

    tabs = st.tabs([
        "Events",
        "Participants",
        "Payments",
        "Selection",
        "Reports",
        "Settings",
        "Audit",
    ])

    with tabs[0]:
        module_5()
    with tabs[1]:
        module_6()
    with tabs[2]:
        module_7()
    with tabs[3]:
        module_8()
    with tabs[4]:
        module_10()
    with tabs[5]:
        module_11()
    with tabs[6]:
        module_12()


# ============================================================
# MAIN APP
# ============================================================

def main():
    st.sidebar.title("🎟️ DRSS")

    public_pages = [
        "🏠 Home",
        "📝 Register",
        "🔎 Check Status",
        "🏆 Winners",
        "🔐 Administrator",
    ]

    page = st.sidebar.radio("Main Menu", public_pages)

    st.sidebar.divider()
    st.sidebar.caption(
        "Modules 1–12 are implemented in this single app.py."
    )

    if page == "🏠 Home":
        module_1()
    elif page == "📝 Register":
        module_2()
    elif page == "🔎 Check Status":
        module_3()
    elif page == "🏆 Winners":
        module_9()
    elif page == "🔐 Administrator":
        admin_dashboard()


if __name__ == "__main__":
    main()
