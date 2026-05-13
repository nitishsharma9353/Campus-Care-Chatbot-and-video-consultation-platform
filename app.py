
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, uuid, hashlib, json, logging
from datetime import datetime
from groq import Groq
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant
from twilio.rest import Client as TwilioClient

# Suppress Flask/Werkzeug startup logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__, static_folder="static")
CORS(app)

# ── JSON Data Persistence ────────────────────────────────────────────────────
DATA_FILE = "data.json"

def load_data():
    """Load USERS, SESSIONS, APPOINTMENTS, CHAT_HIST, NOTIFICATIONS from JSON file."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"USERS": {}, "SESSIONS": {}, "APPOINTMENTS": {}, "CHAT_HIST": {}, "NOTIFICATIONS": {}}

def save_data():
    """Save user data to JSON file (excluding appointments and sessions for privacy)."""
    data = {
        "USERS": USERS,
        "CHAT_HIST": CHAT_HIST,
        "NOTIFICATIONS": NOTIFICATIONS
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)

# ── Credentials ───────────────────────────────────────────────────────────────
GROQ_API_KEY          = os.environ.get("GROQ_API_KEY", "your api key")
TWILIO_ACCOUNT_SID    = os.environ.get("TWILIO_ACCOUNT_SID", "your account sid")
TWILIO_AUTH_TOKEN     = os.environ.get("TWILIO_AUTH_TOKEN", "your auth token")
TWILIO_API_KEY_SID    = os.environ.get("TWILIO_API_KEY_SID", "your api key sid")
TWILIO_API_KEY_SECRET = os.environ.get("TWILIO_API_KEY_SECRET", "your api key secret")

groq_client   = Groq(api_key=GROQ_API_KEY)
twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


# Hospitals
HOSPITALS = {
    "HOSP01": {
        "id": "HOSP01",
        "name": "City General Hospital",
        "address": "Block C, Gate 3, Shivaji Nagar, Pune",
        "phone": "020-12345678",
        "timings": "Mon–Sat 9AM–8PM",
        "specialties": ["General Medicine", "Psychiatry", "Dermatology"],
        "logo": "🏥",
    },
    "HOSP02": {
        "id": "HOSP02",
        "name": "Sunrise Medical Centre",
        "address": "Plot 12, Kothrud, Pune",
        "phone": "020-98765432",
        "timings": "Mon–Sun 8AM–10PM",
        "specialties": ["General Medicine", "Gynecology", "ENT"],
        "logo": "🏨",
    },
    "HOSP03": {
        "id": "HOSP03",
        "name": "Pune Wellness Hospital",
        "address": "Baner Road, Pune",
        "phone": "020-11223344",
        "timings": "Mon–Sat 9AM–9PM",
        "specialties": ["General Medicine", "Neurology", "Cardiology"],
        "logo": "🏦",
    },
    "HOSP04": {
        "id": "HOSP04",
        "name": "CV raman hospital",
        "address": "80 feet road indiranagar",
        "phone": "93748339",     
        "timings": "Mon–Sat 9AM–9PM",
        "specialties": ["General Medicine"],
        "logo": "🏦",
    },
}

# College → Hospital tie-up  (one college can have multiple hospitals)
COLLEGE_HOSPITAL_MAP = {
    "MIT Pune":    ["HOSP01", "HOSP02"],
    "VIT Pune":    ["HOSP01", "HOSP03"],
    "COEP Pune":   ["HOSP02"],
    "PICT Pune":   ["HOSP01"],
    "SPPU Pune":   ["HOSP01", "HOSP02", "HOSP03"],
    "CMR University":["HOSP04"],
}

# In-memory stores
USERS        = {}   # uid  → user dict
SESSIONS     = {}   # tok  → uid
APPOINTMENTS = {}   # aid  → apt dict
CHAT_HIST    = {}   # key  → messages
NOTIFICATIONS = {}  # doctor_uid 

# Load existing data from JSON file
data = load_data()
USERS = data.get("USERS", {})
SESSIONS = data.get("SESSIONS", {})
APPOINTMENTS = data.get("APPOINTMENTS", {})
CHAT_HIST = data.get("CHAT_HIST", {})
NOTIFICATIONS = data.get("NOTIFICATIONS", {})

def _h(pw): return hashlib.sha256(pw.encode()).hexdigest()

def seed():
    # Check if we already have users (loaded from JSON), if so, don't seed
    if USERS:
        return
    students = [
        ("STU001", "Asha Kumar",    "pass123", "MIT Pune",  "3rd Year CSE", "HB-12"),
        ("STU002", "Rohan Verma",   "pass123", "MIT Pune",  "2nd Year ECE", "HB-07"),
        ("STU003", "Preethi Iyer",  "pass123", "VIT Pune",  "1st Year ME",  "HB-03"),
        ("STU004", "Arjun Nair",    "pass123", "COEP Pune", "4th Year Civil","HB-22"),
    ]
    for uid, name, pw, college, year, hostel in students:
        USERS[uid] = {"name":name,"pw":_h(pw),"role":"student",
                      "college":college,"year":year,"hostel":hostel,
                      "created_at":datetime.now().isoformat()}

    doctors = [
        ("DOC001","Dr. Priya Sharma", "doc123","General Medicine",   "HOSP01"),
        ("DOC002","Dr. Rahul Menon",  "doc123","Psychiatry",         "HOSP01"),
        ("DOC003","Dr. Anita Desai",  "doc123","Dermatology",        "HOSP02"),
        ("DOC004","Dr. Kiran Patel",  "doc123","General Medicine",   "HOSP02"),
        ("DOC005","Dr. Sneha Nair",   "doc123","cardiologist",         "HOSP02"),
        ("DOC006","Dr. Arun Kumar",   "doc123","General Medicine",   "HOSP03"),
        ("DOC007","Dr. Varun Kumar",   "doc123","General Medicine",  "HOSP04"),
    ]
    for uid, name, pw, spec, hosp_id in doctors:
        USERS[uid] = {"name":name,"pw":_h(pw),"role":"doctor",
                      "specialty":spec,"hospital_id":hosp_id,
                      "hospital_name":HOSPITALS[hosp_id]["name"],
                      "available":True}
        NOTIFICATIONS.setdefault(uid, [])

seed()

# ── AI prompt ─────────────────────────────────────────────────────────────────
MEDBOT = """You are MedBot, a friendly and empathetic AI health assistant for college hostel students.

CONVERSATION STYLE:
- Be warm, conversational, and supportive — like a caring friend who knows health
- Use natural language, not clinical/robotic responses
- Ask follow-up questions to understand their situation better
- Acknowledge their feelings and concerns
- Keep responses brief (2-4 sentences) but engaging

HOW TO RESPOND:
- Greet them warmly and acknowledge their symptoms
- Ask clarifying questions (when did it start? how severe? any other symptoms?)
- Show empathy — "I'm sorry you're feeling this way"
- Provide helpful health information and gentle guidance
- Suggest simple self-care steps when appropriate

IMPORTANT:
- Do NOT suggest booking appointments or specific doctors/hospitals
- Do NOT give definitive diagnoses
- For emergencies (severe pain, breathing issues, unconsciousness): say "Please call 112 immediately"
- Encourage seeing a real doctor if symptoms persist or worsen

EXAMPLE TONE:
"Hi there! I'm sorry to hear you're not feeling well. Fever and cold symptoms can be tough — when did these start, and do you have any other symptoms like a sore throat or body aches?"
"""

# Save data after seeding
save_data()

# ── Helpers ───────────────────────────────────────────────────────────────────
def auth(req):
    tok = req.headers.get("Authorization","").replace("Bearer ","")
    uid = SESSIONS.get(tok)
    return uid, USERS.get(uid)

# ══════════════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return send_from_directory("static","index.html")

@app.route("/api/signup", methods=["POST"])
def signup():
    d = request.json
    user_id = d.get("user_id","").strip().upper()
    name, college, year, hostel, pw = (
        d.get("name","").strip(), d.get("college","").strip(),
        d.get("year","").strip(),  d.get("hostel","").strip(),
        d.get("password","")
    )
    if not all([user_id, name, college, year, pw]):
        return jsonify({"error":"All fields required"}), 400
    if user_id in USERS:
        return jsonify({"error":"Student ID already exists"}), 400
    if college not in COLLEGE_HOSPITAL_MAP:
        return jsonify({"error":"College not in our system. Contact your college admin."}), 400
    if len(pw) < 6:
        return jsonify({"error":"Password must be at least 6 characters"}), 400
    USERS[user_id] = {"name":name,"pw":_h(pw),"role":"student",
                  "college":college,"year":year,"hostel":hostel or "—",
                  "created_at":datetime.now().isoformat()}
    tok = uuid.uuid4().hex
    SESSIONS[tok] = user_id
    save_data()  # Persist to JSON file
    hospitals = [HOSPITALS[hid] for hid in COLLEGE_HOSPITAL_MAP.get(college,[]) if hid in HOSPITALS]
    return jsonify({"token":tok,"user_id":user_id,"name":name,"role":"student",
                    "college":college,"year":year,"hostel":hostel,"hospitals":hospitals})

@app.route("/api/login", methods=["POST"])
def login():
    d   = request.json
    uid = d.get("user_id","").upper().strip()
    pw  = d.get("password","")
    # Reload data to get latest users
    data = load_data()
    USERS.update(data.get("USERS", {}))
    u   = USERS.get(uid)
    if not u or u["pw"] != _h(pw):
        return jsonify({"error":"Invalid ID or password"}), 401
    tok = uuid.uuid4().hex
    SESSIONS[tok] = uid
    save_data()
    safe = {k:v for k,v in u.items() if k!="pw"}
    # Attach hospitals for students
    if u["role"] == "student":
        hids = COLLEGE_HOSPITAL_MAP.get(u["college"],[])
        safe["hospitals"] = [HOSPITALS[hid] for hid in hids if hid in HOSPITALS]
    return jsonify({"token":tok,"user_id":uid,**safe})

# ══════════════════════════════════════════════════════════════
#  HOSPITALS — student sees hospitals linked to their college
# ══════════════════════════════════════════════════════════════

@app.route("/api/hospitals", methods=["GET"])
def get_hospitals():
    uid, user = auth(request)
    if not user:
        return jsonify({"error":"Unauthorised"}), 401
    if user["role"] == "student":
        hids = COLLEGE_HOSPITAL_MAP.get(user.get("college",""), [])
        return jsonify([HOSPITALS[h] for h in hids if h in HOSPITALS])
    elif user["role"] == "doctor":
        hid = user.get("hospital_id","")
        return jsonify([HOSPITALS[hid]] if hid in HOSPITALS else [])
    return jsonify(list(HOSPITALS.values()))

@app.route("/api/hospitals/<hid>/doctors", methods=["GET"])
def hospital_doctors(hid):
    """Doctors available at a given hospital."""
    docs = [
        {"id":uid, "name":u["name"], "specialty":u["specialty"],
         "available":u.get("available",True)}
        for uid,u in USERS.items()
        if u["role"]=="doctor" and u.get("hospital_id")==hid
    ]
    return jsonify(docs)

# ══════════════════════════════════════════════════════════════
#  APPOINTMENTS
# ══════════════════════════════════════════════════════════════

@app.route("/api/appointments", methods=["POST"])
def book():
    uid, user = auth(request)
    if not user or user["role"] != "student":
        return jsonify({"error":"Students only"}), 403
    d = request.json
    college  = user["college"]
    hosp_id  = d.get("hospital_id","")
    # Validate the hospital is actually tied to this college
    if hosp_id not in COLLEGE_HOSPITAL_MAP.get(college,[]):
        return jsonify({"error":"This hospital is not tied to your college"}), 400
    hosp = HOSPITALS.get(hosp_id)
    if not hosp:
        return jsonify({"error":"Hospital not found"}), 404

    doc_id = d.get("doctor_id")   # optional: student may pick a specific doctor

    apt_id    = "APT" + uuid.uuid4().hex[:6].upper()
    room_name = f"cc-{apt_id.lower()}"

    apt = {
        "id":              apt_id,
        "room_name":       room_name,
        "student_id":      uid,
        "student_name":    user["name"],
        "student_college": college,
        "student_year":    user.get("year",""),
        "student_hostel":  user.get("hostel",""),
        "hospital_id":     hosp_id,
        "hospital_name":   hosp["name"],
        "hospital_address":hosp["address"],
        "doctor_id":       doc_id,
        "doctor_name":     USERS[doc_id]["name"] if doc_id and doc_id in USERS else None,
        "reason":          d.get("reason",""),
        "symptoms":        d.get("symptoms",""),
        "priority":        d.get("priority","normal"),
        "preferred_time":  d.get("preferred_time","Flexible"),
        "status":          "waiting",   # waiting → confirmed → in_progress → completed
        "created_at":      datetime.now().isoformat(),
        "confirmed_at":    None,
    }
    APPOINTMENTS[apt_id] = apt

    # ── Notify relevant doctors
    if doc_id and doc_id in NOTIFICATIONS:
        NOTIFICATIONS[doc_id].append(apt_id)
    else:
        for duid, du in USERS.items():
            if du["role"]=="doctor" and du.get("hospital_id")==hosp_id:
                NOTIFICATIONS.setdefault(duid,[]).append(apt_id)

    # Pre-create Twilio room
    try:
        twilio_client.video.rooms.create(unique_name=room_name,type="group",max_participants=2)
    except Exception:
        pass

    return jsonify(apt)

@app.route("/api/appointments", methods=["GET"])
def list_apts():
    uid, user = auth(request)
    if not user:
        return jsonify({"error":"Unauthorised"}), 401
    apts = list(APPOINTMENTS.values())
    if user["role"] == "student":
        apts = [a for a in apts if a["student_id"]==uid]
    elif user["role"] == "doctor":
        hid = user.get("hospital_id","")
        # Doctor sees appointments for their hospital
        apts = [a for a in apts if a["hospital_id"]==hid]
    return jsonify(sorted(apts, key=lambda x:x["created_at"], reverse=True))

@app.route("/api/appointments/<aid>/confirm", methods=["POST"])
def confirm(aid):
    """Doctor confirms the appointment — student gets notified."""
    uid, user = auth(request)
    if not user or user["role"] != "doctor":
        return jsonify({"error":"Doctors only"}), 403
    apt = APPOINTMENTS.get(aid)
    if not apt:
        return jsonify({"error":"Not found"}), 404
    apt["doctor_id"]   = uid
    apt["doctor_name"] = user["name"]
    apt["status"]      = "confirmed"
    apt["confirmed_at"]= datetime.now().isoformat()
    apt["doctor_note"] = request.json.get("note","")
    # Remove from all doctor notification queues
    for duid in NOTIFICATIONS:
        if aid in NOTIFICATIONS[duid]:
            NOTIFICATIONS[duid].remove(aid)
    return jsonify(apt)

@app.route("/api/appointments/<aid>/status", methods=["PATCH"])
def update_status(aid):
    uid, user = auth(request)
    apt = APPOINTMENTS.get(aid)
    if not apt: return jsonify({"error":"Not found"}), 404
    s = request.json.get("status")
    if s in ("in_progress","completed","cancelled"):
        apt["status"] = s
    return jsonify(apt)

# Doctor's unread notifications
@app.route("/api/notifications", methods=["GET"])
def notifications():
    uid, user = auth(request)
    if not user or user["role"] != "doctor":
        return jsonify([])
    apt_ids = NOTIFICATIONS.get(uid, [])
    return jsonify([APPOINTMENTS[a] for a in apt_ids if a in APPOINTMENTS])

# ══════════════════════════════════════════════════════════════
#  MEDBOT
# ══════════════════════════════════════════════════════════════

@app.route("/api/chat", methods=["POST"])
def chat():
    uid, user = auth(request)
    d   = request.json
    msg = d.get("message","").strip()
    key = f"chat-{uid or 'anon'}"
    if not msg: return jsonify({"error":"Empty"}), 400
    CHAT_HIST.setdefault(key,[])
    CHAT_HIST[key].append({"role":"user","content":msg})
    try:
        # Check if GROQ_API_KEY is properly set (not empty or placeholder)
        if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key":
            raise Exception("GROQ_API_KEY not configured")
            
        r = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role":"system","content":MEDBOT},*CHAT_HIST[key][-10:]],
            max_tokens=300, temperature=0.7
        )
        reply = r.choices[0].message.content
        CHAT_HIST[key].append({"role":"assistant","content":reply})
        suggest = any(w in reply.lower() for w in ["symptom","medicine","medical","health","condition","treatment","advice"])
        return jsonify({"message":reply,"suggest":suggest})
    except Exception as e:
        print(f"Groq API Error: {e}")  # Debug logging
        return jsonify({"error": f"AI service error: {str(e)}"}), 503

# ══════════════════════════════════════════════════════════════
#  TWILIO VIDEO TOKEN
# ══════════════════════════════════════════════════════════════

@app.route("/api/video/token", methods=["POST"])
def video_token():
    uid, user = auth(request)
    if not user: return jsonify({"error":"Unauthorised"}), 401
    room = request.json.get("room_name","")
    if not room: return jsonify({"error":"room_name required"}), 400
    identity = f"{user['name'].replace(' ','-')}-{uid}"
    try:
        tok = AccessToken(TWILIO_ACCOUNT_SID, TWILIO_API_KEY_SID,
                          TWILIO_API_KEY_SECRET, identity=identity, ttl=3600)
        tok.add_grant(VideoGrant(room=room))
        return jsonify({"token":tok.to_jwt(),"room_name":room,"identity":identity})
    except Exception as e:
        return jsonify({"error":str(e)}), 500

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    print("\n🏥  CampusCare v3  →  http://localhost:5000\n")
    app.run(debug=False, port=5000)
