import streamlit as st
import json
import uuid
import random
from datetime import datetime, date
from typing import Any, Dict, Optional

st.set_page_config(page_title="DRSS | Digital Registration and Selection System", layout="wide")

APP_NAME = "Digital Registration and Selection System"
DEFAULT_PROJECT = "drs-system-bffd7"

def text(v):
    return "" if v is None else str(v).strip()

def read_config():
    cfg = {}
    try:
        section = st.secrets.get("firebase_admin", {})
        for k in ["type","project_id","private_key_id","private_key","client_email","client_id",
                  "auth_uri","token_uri","auth_provider_x509_cert_url","client_x509_cert_url"]:
            if k in section:
                cfg[k] = text(section[k])
    except Exception:
        pass
    raw = ""
    try:
        raw = text(st.secrets.get("FIREBASE_SERVICE_ACCOUNT_JSON", ""))
    except Exception:
        pass
    if raw and not cfg:
        try:
            cfg = {k:text(v) for k,v in json.loads(raw).items()}
        except Exception:
            pass
    return cfg

def normalize_key(v):
    return text(v).replace("\\r\\n","\n").replace("\\n","\n").replace("\r\n","\n").replace("\r","\n")

def validate(cfg):
    missing = [k for k in ["project_id","private_key","client_email"] if not text(cfg.get(k))]
    if missing:
        return False, missing
    if not normalize_key(cfg["private_key"]).startswith("-----BEGIN PRIVATE KEY-----"):
        return False, ["private_key format"]
    return True, []

@st.cache_resource(show_spinner=False)
def connect_firebase():
    cfg = read_config()
    ok, errors = validate(cfg)
    if not ok:
        return None, cfg, errors
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        cfg["private_key"] = normalize_key(cfg["private_key"])
        try:
            firebase_admin.get_app()
        except ValueError:
            data = {
                "type": cfg.get("type","service_account"),
                "project_id": cfg["project_id"],
                "private_key_id": cfg.get("private_key_id",""),
                "private_key": cfg["private_key"],
                "client_email": cfg["client_email"],
                "client_id": cfg.get("client_id",""),
                "auth_uri": cfg.get("auth_uri","https://accounts.google.com/o/oauth2/auth"),
                "token_uri": cfg.get("token_uri","https://oauth2.googleapis.com/token"),
                "auth_provider_x509_cert_url": cfg.get("auth_provider_x509_cert_url","https://www.googleapis.com/oauth2/v1/certs"),
                "client_x509_cert_url": cfg.get("client_x509_cert_url","")
            }
            firebase_admin.initialize_app(credentials.Certificate(data))
        return firestore.client(), cfg, []
    except Exception as e:
        return None, cfg, [f"{type(e).__name__}: {e}"]

db, firebase_cfg, firebase_errors = connect_firebase()

def col(name):
    return None if db is None else db.collection(name)

def set_doc(name, doc_id, data, merge=True):
    c = col(name)
    if c is None: return False
    c.document(doc_id).set(data, merge=merge)
    return True

def add_doc(name, data):
    c = col(name)
    if c is None: return None
    _, ref = c.add(data)
    return ref.id

def get_docs(name, limit=500):
    c = col(name)
    if c is None: return []
    out=[]
    for d in c.limit(limit).stream():
        x=d.to_dict(); x["_id"]=d.id; out.append(x)
    return out

def audit(action, details=None):
    try:
        add_doc("audit_logs", {"action":action,"details":details or {},"created_at":datetime.utcnow().isoformat()})
    except Exception:
        pass

st.markdown("""
<style>
.block-container{max-width:1250px;padding-top:1.5rem}
.hero{padding:2rem;border:1px solid #d9e2ec;border-radius:18px;background:#f7f9fc;margin-bottom:1.5rem}
.hero h1{margin:0;color:#243447;font-size:2.2rem}
.hero p{color:#52606d;font-size:1.05rem}
.card{padding:1rem;border:1px solid #d9e2ec;border-radius:12px;background:#fff;min-height:120px}
</style>
""", unsafe_allow_html=True)

def home():
    st.markdown('<div class="hero"><h1>Digital Registration and Selection System</h1><p>A simple, transparent and auditable platform for registration, eligibility, random selection and results.</p></div>', unsafe_allow_html=True)
    if db: st.success("Firebase Firestore connection is active.")
    else: st.error("Firebase Admin connection is not active. Configure Streamlit Secrets.")
    cols=st.columns(4)
    for c,title,desc in zip(cols,["Registration","Eligibility","Selection","Results"],
                            ["Register participants.","Review eligibility.","Select winners randomly.","View published results."]):
        with c:
            st.markdown(f'<div class="card"><h4>{title}</h4><p>{desc}</p></div>',unsafe_allow_html=True)

def module1():
    st.header("Module 1: System Home")
    st.write("DRSS provides a complete workflow from event creation and registration through eligibility review, random selection, results and audit reporting.")
    st.write("Design principles: simple use, transparent rules, controlled access, auditable actions and reproducible procedures.")

def module2():
    st.header("Module 2: Participant Registration")
    with st.form("registration"):
        name=st.text_input("Full name")
        phone=st.text_input("Phone number")
        email=st.text_input("Email address")
        pidno=st.text_input("Participant identification number")
        event=st.text_input("Event ID")
        agree=st.checkbox("I confirm that the information provided is correct.")
        submit=st.form_submit_button("Register participant")
    if submit:
        if not name or not phone or not event: st.error("Full name, phone number and event ID are required."); return
        if not agree: st.error("Please confirm the information."); return
        pid="P-"+uuid.uuid4().hex[:10].upper()
        data={"participant_id":pid,"full_name":name,"phone":phone,"email":email,"national_id":pidno,
              "event_id":event,"status":"registered","eligible":False,"created_at":datetime.utcnow().isoformat()}
        if db:
            set_doc("participants",pid,data,False); audit("participant_registered",{"participant_id":pid})
            st.success(f"Registration completed. Participant ID: {pid}")
        else: st.warning("Firebase is required to permanently save the registration.")

def module3():
    st.header("Module 3: Eligibility")
    if not db: st.warning("Firebase is required."); return
    rows=get_docs("participants")
    if not rows: st.info("No participants found."); return
    for p in rows:
        with st.expander(f'{p.get("participant_id","")} - {p.get("full_name","")}'):
            eligible=st.checkbox("Eligible for selection",bool(p.get("eligible")),key="e"+p["_id"])
            if st.button("Save eligibility",key="s"+p["_id"]):
                set_doc("participants",p["_id"],{"eligible":eligible,"status":"eligible" if eligible else "ineligible","reviewed_at":datetime.utcnow().isoformat()})
                audit("eligibility_updated",{"participant_id":p["_id"],"eligible":eligible})
                st.success("Saved.")

def module4():
    st.header("Module 4: Event Management")
    with st.form("event"):
        name=st.text_input("Event name")
        desc=st.text_area("Description")
        start=st.date_input("Registration start",date.today())
        end=st.date_input("Registration end",date.today())
        winners=st.number_input("Number of winners",1,100,1)
        submit=st.form_submit_button("Create event")
    if submit:
        if not name: st.error("Event name is required."); return
        eid="EV-"+uuid.uuid4().hex[:8].upper()
        data={"event_id":eid,"event_name":name,"description":desc,"start_date":str(start),"end_date":str(end),
              "winners_count":int(winners),"status":"open","created_at":datetime.utcnow().isoformat()}
        if db: set_doc("events",eid,data,False); audit("event_created",{"event_id":eid}); st.success(f"Event created: {eid}")
        else: st.warning("Firebase is required.")
    if db: st.dataframe(get_docs("events"),use_container_width=True)

def module5():
    st.header("Module 5: Payment and Verification")
    st.write("Record payment references. Connect an approved payment provider separately for automated processing.")
    with st.form("payment"):
        pid=st.text_input("Participant ID")
        ref=st.text_input("Payment reference")
        amount=st.number_input("Amount",0.0,1000000.0,0.0)
        submit=st.form_submit_button("Record payment")
    if submit:
        if not pid or not ref: st.error("Participant ID and payment reference are required."); return
        pay="PAY-"+uuid.uuid4().hex[:10].upper()
        if db: set_doc("payments",pay,{"payment_id":pay,"participant_id":pid,"reference":ref,"amount":float(amount),"status":"pending_verification","created_at":datetime.utcnow().isoformat()},False); audit("payment_recorded",{"payment_id":pay}); st.success(f"Payment recorded: {pay}")
        else: st.warning("Firebase is required.")

def module6():
    st.header("Module 6: Document Verification")
    st.write("Record document verification status. File storage can be integrated separately.")
    if not db: st.warning("Firebase is required."); return
    with st.form("verification"):
        pid=st.text_input("Participant ID")
        dtype=st.selectbox("Document type",["Identification","Proof of payment","Eligibility document","Other"])
        status=st.selectbox("Verification result",["pending","verified","rejected"])
        notes=st.text_area("Notes")
        submit=st.form_submit_button("Save verification")
    if submit:
        if not pid: st.error("Participant ID is required."); return
        vid="VER-"+uuid.uuid4().hex[:10].upper()
        set_doc("verifications",vid,{"verification_id":vid,"participant_id":pid,"document_type":dtype,"status":status,"notes":notes,"created_at":datetime.utcnow().isoformat()},False)
        audit("document_verification_saved",{"verification_id":vid}); st.success("Verification saved.")

def module7():
    st.header("Module 7: Random Selection")
    st.write("Simple random sample without replacement from eligible participants. Production public lotteries should have formally approved rules, oversight and independent verification.")
    if not db: st.warning("Firebase is required."); return
    events=get_docs("events")
    if not events: st.info("Create an event first."); return
    labels=[f'{e.get("event_id")} - {e.get("event_name")}' for e in events]
    selected=st.selectbox("Select event",labels); event=events[labels.index(selected)]
    people=[p for p in get_docs("participants") if p.get("event_id")==event.get("event_id") and p.get("eligible")]
    st.write(f"Eligible participants: {len(people)}")
    n=min(int(event.get("winners_count",1)),len(people))
    if st.button("Run random selection",disabled=n<1):
        winners=random.SystemRandom().sample(people,n)
        sid="SEL-"+uuid.uuid4().hex[:10].upper()
        stamp=datetime.utcnow().isoformat()
        set_doc("selections",sid,{"selection_id":sid,"event_id":event.get("event_id"),"selected_at":stamp,
                                  "method":"simple_random_sample_without_replacement","population_size":len(people),
                                  "winner_count":n,"winner_ids":[p.get("participant_id") for p in winners]},False)
        for rank,p in enumerate(winners,1):
            wid="WIN-"+uuid.uuid4().hex[:10].upper()
            set_doc("winners",wid,{"winner_id":wid,"selection_id":sid,"event_id":event.get("event_id"),
                                   "participant_id":p.get("participant_id"),"full_name":p.get("full_name"),
                                   "rank":rank,"selected_at":stamp},False)
        audit("random_selection_completed",{"selection_id":sid,"event_id":event.get("event_id"),"population_size":len(people),"winner_count":n})
        st.success(f"Selection completed: {sid}")
        for rank,p in enumerate(winners,1): st.write(f"{rank}. {p.get('participant_id')} - {p.get('full_name')}")

def module8():
    st.header("Module 8: Results")
    if not db: st.warning("Firebase is required."); return
    rows=get_docs("winners")
    st.dataframe(rows,use_container_width=True) if rows else st.info("No results available.")

def module9():
    st.header("Module 9: Notifications")
    st.write("Create notification records. SMS and email delivery require an external provider.")
    if not db: st.warning("Firebase is required."); return
    with st.form("notification"):
        pid=st.text_input("Participant ID")
        channel=st.selectbox("Channel",["SMS","Email"])
        message=st.text_area("Message")
        submit=st.form_submit_button("Queue notification")
    if submit:
        if not pid or not message: st.error("Participant ID and message are required."); return
        nid="NOT-"+uuid.uuid4().hex[:10].upper()
        set_doc("notifications",nid,{"notification_id":nid,"participant_id":pid,"channel":channel,"message":message,"status":"queued","created_at":datetime.utcnow().isoformat()},False)
        audit("notification_created",{"notification_id":nid}); st.success("Notification queued.")

def module10():
    st.header("Module 10: Reports")
    if not db: st.warning("Firebase is required."); return
    p,e,w,pay=get_docs("participants"),get_docs("events"),get_docs("winners"),get_docs("payments")
    a,b,c,d=st.columns(4)
    a.metric("Participants",len(p)); b.metric("Events",len(e)); c.metric("Winners",len(w)); d.metric("Payments",len(pay))
    st.dataframe(p,use_container_width=True)

def module11():
    st.header("Module 11: Audit Trail")
    if not db: st.warning("Firebase is required."); return
    rows=get_docs("audit_logs")
    st.dataframe(rows,use_container_width=True) if rows else st.info("No audit records yet.")

def module12():
    st.header("Module 12: Administration and System Health")
    if db:
        st.success("Firebase Admin SDK connected successfully.")
        st.write("Project ID:",firebase_cfg.get("project_id",""))
        st.write("Service account:",firebase_cfg.get("client_email",""))
    else:
        st.error("Firebase Admin SDK is not connected.")
        for e in firebase_errors: st.code(e)
    st.subheader("Secret field status")
    fields=["project_id","private_key_id","private_key","client_email","client_id"]
    st.dataframe([{"field":f,"configured":bool(firebase_cfg.get(f))} for f in fields],use_container_width=True)
    st.info("Private keys are never displayed. Keep the service-account JSON and private key out of GitHub and app.py.")

pages={"Home":home,"Module 1: System Home":module1,"Module 2: Registration":module2,
       "Module 3: Eligibility":module3,"Module 4: Event Management":module4,
       "Module 5: Payment":module5,"Module 6: Document Verification":module6,
       "Module 7: Random Selection":module7,"Module 8: Results":module8,
       "Module 9: Notifications":module9,"Module 10: Reports":module10,
       "Module 11: Audit Trail":module11,"Module 12: Administration":module12}

with st.sidebar:
    st.markdown("## DRSS")
    page=st.radio("Navigation",list(pages))
    st.divider()
    st.write("Firebase project")
    st.write(firebase_cfg.get("project_id",DEFAULT_PROJECT))
    st.write("Database status")
    st.write("Connected" if db else "Not connected")

pages[page]()
