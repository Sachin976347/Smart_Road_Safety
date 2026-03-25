import random
import requests


from datetime import timedelta, datetime
import os
import uuid
import json
import re

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
from twilio.rest import Client

app = Flask(__name__)

# ==================== CONFIGURATION ====================
app.config["SECRET_KEY"] = "smart-road-safety-secret-key-2025"
app.config["JWT_SECRET_KEY"] = "jwt-smart-road-safety-2025"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024 # 16 MB max file size

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": ["http://localhost:*", "http://127.0.0.1:*"],
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    },
)

jwt = JWTManager(app)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs("data", exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

USERS_FILE = "data/users.json"
REPORTS_FILE = "data/reports.json"
IOT_DATA_FILE = "data/iot_data.json"

def load_data():
    def load_json(filepath):
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                try: return json.load(f)
                except: pass
        return {} if filepath == USERS_FILE else []
    users = load_json(USERS_FILE)
    reports = load_json(REPORTS_FILE)
    iot_data = load_json(IOT_DATA_FILE)
    users = users if isinstance(users, dict) else {}
    reports = reports if isinstance(reports, list) else []
    iot_data = iot_data if isinstance(iot_data, list) else []
    return users, reports, iot_data

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def save_reports(reports):
    with open(REPORTS_FILE, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2, ensure_ascii=False)

def save_iot_data(iot_data):
    with open(IOT_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(iot_data, f, indent=2, ensure_ascii=False)

users_db, reports_db, iot_db = load_data()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

otp_storage = {}  # In-memory OTP storage for demo purposes

# --- EMAIL OTP FUNCTION ---
def send_email_otp(email, otp):
    EMAIL_ADDRESS = "your_gmail_address@gmail.com"      # <-- set your address
    EMAIL_PASSWORD = "your_app_password"                # <-- set your app password
    msg = EmailMessage()
    msg.set_content(f"Your OTP code for Smart Road Safety registration is: {otp}")
    msg["Subject"] = "Smart Road Safety Registration OTP"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"📧 OTP sent to email {email}: {otp}")
    except Exception as e:
        print(f"❌ Email send failed: {str(e)}")



# Note: Example OTP sending code removed — OTP generation and sending is handled inside the /api/auth/send-otp route.

# ==================== AUTH ROUTES ====================
@app.route("/api/auth/register", methods=["POST"])
def register():
    try:
        data = request.get_json()

        email = data.get("email").lower().strip()
        password = data.get("password")
        name = data.get("name")
        phone = data.get("phone")

        if not email or not password or not name or not phone:
            return jsonify({"error": "All fields required"}), 400

        if email in users_db:
            return jsonify({"error": "User already exists"}), 409

        user = {
            "id": str(uuid.uuid4()),
            "name": name,
            "email": email,
            "password": generate_password_hash(password),
            "phone": phone,
            "verified": True   # ✅ IMPORTANT FIX
        }

        users_db[email] = user
        save_users(users_db)

        return jsonify({"message": "Signup successful"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        email = data.get("email").lower().strip()
        password = data.get("password")

        user = users_db.get(email)

        if not user:
            return jsonify({"error": "User not found"}), 404

        if not check_password_hash(user["password"], password):
            return jsonify({"error": "Wrong password"}), 401

        token = create_access_token(identity=email)

        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": user
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @app.route('/api/auth/send-otp', methods=['POST'])
# def send_otp():
#     try:
#         data = request.get_json()
#         phone = data.get('phone')
#         email = data.get('email', '').lower().strip()
#         name = data.get('name', '').strip()
#         password = data.get('password', '').strip()
#         if not phone or not email:
#             return jsonify({"error": "Phone and email required"}), 400
#         phone = phone.strip()
#         user = next((u for u in users_db.values() if u.get("phone") == phone), None)
#         if not user:
#             user_id = str(uuid.uuid4())
#             user_doc = {
#                 "id": user_id,
#                 "name": name,
#                 "email": email,
#                 "password": generate_password_hash(password),
#                 "phone": phone,
#                 "created_at": datetime.now().isoformat(),
#                 "verified": False,
#             }
#             users_db[email] = user_doc
#             save_users(users_db)
#         otp = random.randint(100000, 999999)
#         otp_storage[phone] = otp
#         send_email_otp(email, otp)
#         try:
#             send_sms_otp(phone, otp)
#         except Exception as e:
#             print(f"⚠️ SMS send failed: {str(e)}")
#         return jsonify({"message": "OTP sent successfully"}), 200
#     except Exception as e:
#         print(f"❌ Critical error during send-otp: {str(e)}")
#         return jsonify({"error": f"Internal server error: Failed to process OTP request ({str(e)})"}), 500
    
# def send_sms_otp(phone, otp):
#     account_sid = 'YOUR_TWILIO_SID'
#     auth_token = 'YOUR_TWILIO_AUTH_TOKEN'
#     # If Twilio credentials are not set, skip sending SMS (avoids runtime errors during development)
#     if account_sid.startswith("YOUR_TWILIO") or auth_token.startswith("YOUR_TWILIO"):
#         print("⚠️ Twilio credentials not configured; skipping SMS send")
#         return
#     try:
#         client = Client(account_sid, auth_token)
#         message = client.messages.create(
#             body=f"Your OTP for Smart Road Safety is {otp}",
#             from_='+YOUR_TWILIO_PHONE_NUMBER',  # replace with your Twilio number
#             to=phone
#         )
#         print(f"📩 SMS sent to {phone}: SID {getattr(message, 'sid', '')}")
#     except Exception as e:
#         print(f"❌ Twilio SMS error: {str(e)}")
#         raise

# def send_textlocal_otp(phone, otp):
#     apiKey = 'YOUR_TEXTLOCAL_API_KEY'
#     numbers = [phone]
#     sender = 'TXTLCL'
#     message = f'Your OTP for Smart Road Safety is {otp}'
#     url = 'https://api.textlocal.in/send/'
#     data = {
#         'apikey': apiKey,
#         'numbers': numbers,
#         'sender': sender,
#         'message': message
#     }
#     try:
#         response = requests.post(url, data=data)
#         print('SMS response:', response.text)
#     except Exception as e:
#         print(f"⚠️ Textlocal SMS error: {str(e)}")

# @app.route('/api/auth/verify-otp', methods=['POST'])
# def verify_otp():
#     data = request.get_json()
#     phone = data.get('phone')
#     otp = data.get('otp')
#     if not phone or not otp:
#         return jsonify({"error": "Phone and OTP are required"}), 400
#     phone = phone.strip()
#     if otp_storage.get(phone) and str(otp_storage[phone]) == str(otp):
#         user = next((u for u in users_db.values() if u.get("phone") == phone), None)
#         if not user:
#             return jsonify({"error": "User associated with this phone number not found."}), 404
#         user["verified"] = True
#         save_users(users_db)
#         del otp_storage[phone]
#         access_token = create_access_token(identity=user["email"])
#         return jsonify({
#             "message": "OTP verified successfully",
#             "token": access_token,
#             "user": {k: v for k, v in user.items() if k not in ["password"]},
#         }), 200
#     else:
#         return jsonify({"error": "Invalid OTP"}), 400

# @app.route("/api/auth/login", methods=["POST", "OPTIONS"])
# def login():
#     if request.method == "OPTIONS":
#         return "", 204
#     try:
#         data = request.get_json() or {}
#         if not data or not data.get("email") or not data.get("password"):
#             return jsonify({"error": "Email and password are required"}), 400
#         email = data["email"].lower().strip()
#         password = data["password"]
#         user = users_db.get(email)
#         if not user or not check_password_hash(user["password"], password) or not user.get("verified", False):
#             return jsonify({"error": "Invalid email or password, or user not verified"}), 401
#         access_token = create_access_token(identity=email)
#         print(f"✅ User logged in: {email}")
#         return jsonify({
#             "message": "Login successful",
#             "token": access_token,
#             "user": {k: v for k, v in user.items() if k not in ["password"]},
#         }), 200
#     except Exception as e:
#         print(f"❌ Login error: {str(e)}")
#         return jsonify({"error": f"Login failed: {str(e)}"}), 500

# @app.route("/api/auth/verify", methods=["GET"])
# @jwt_required()
# def verify_token():
#     try:
#         email = get_jwt_identity()
#         user = users_db.get(email)
#         if not user:
#             return jsonify({"valid": False}), 401
#         return jsonify({"valid": True, "user": {"id": user["id"], "name": user["name"], "email": user["email"]}}), 200
#     except Exception:
#         return jsonify({"valid": False}), 401

# ==================== REPORT ROUTES ====================
@app.route("/api/reports", methods=["POST", "OPTIONS"])
@jwt_required()
def create_report():
    if request.method == "OPTIONS":
        return "", 204
    try:
        email = get_jwt_identity()
        user = users_db.get(email)
        if not user:
            return jsonify({"error": "User not found"}), 404
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        location = (request.form.get("location") or "").strip()
        latitude = request.form.get("latitude", "0")
        longitude = request.form.get("longitude", "0")
        category = (request.form.get("category") or "").strip()
        severity = (request.form.get("severity") or "").strip()
        if not all([title, description, location, category, severity]):
            return jsonify({"error": "All fields are required"}), 400
        valid_categories = ["pothole", "accident", "broken-signal", "congestion", "weather", "construction"]
        if category not in valid_categories:
            return jsonify({"error": "Invalid category"}), 400
        valid_severities = ["critical", "high", "medium", "low"]
        if severity not in valid_severities:
            return jsonify({"error": "Invalid severity level"}), 400
        image_url = None
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename and allowed_file(file.filename):
                try:
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
                    image = Image.open(file)
                    if image.mode in ("RGBA", "P"): image = image.convert("RGB")
                    image.thumbnail((1200, 1200))
                    image.save(filepath, optimize=True, quality=85)
                    image_url = f"/uploads/{unique_filename}"
                    print(f"📸 Image saved: {unique_filename}")
                except Exception as img_error:
                    print(f"⚠️ Image processing error: {str(img_error)}")
                    image_url = None
        report_doc = {
            "id": str(uuid.uuid4()),
            "title": title,
            "description": description,
            "location": location,
            "latitude": float(latitude) if latitude else 0.0,
            "longitude": float(longitude) if longitude else 0.0,
            "category": category,
            "severity": severity,
            "image_url": image_url,
            "status": "pending",
            "user_id": user["id"],
            "user_name": user["name"],
            "user_email": email,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        reports_db.append(report_doc)
        save_reports(reports_db)
        print(f"✅ Report created: {title} by {user['name']}")
        return jsonify({"message": "Report submitted successfully", "report": report_doc}), 201
    except Exception as e:
        print(f"❌ Report creation error: {str(e)}")
        return jsonify({"error": f"Failed to create report: {str(e)}"}), 500

@app.route("/api/reports", methods=["GET"])
def get_reports():
    try:
        status = (request.args.get("status") or "").lower()
        category = (request.args.get("category") or "").lower()
        severity = (request.args.get("severity") or "").lower()
        filtered_reports = reports_db.copy()
        if status:
            filtered_reports = [r for r in filtered_reports if r.get("status", "").lower() == status]
        if category:
            filtered_reports = [r for r in filtered_reports if r.get("category", "").lower() == category]
        if severity:
            filtered_reports = [r for r in filtered_reports if r.get("severity", "").lower() == severity]
        filtered_reports = sorted(filtered_reports, key=lambda x: x.get("created_at", ""), reverse=True)
        return jsonify({"reports": filtered_reports, "count": len(filtered_reports)}), 200
    except Exception as e:
        print(f"❌ Error fetching reports: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/reports/<report_id>", methods=["DELETE", "OPTIONS"])
@jwt_required()
def delete_report(report_id):
    if request.method == "OPTIONS":
        return "", 204
    try:
        report_index = next((i for i, r in enumerate(reports_db) if r["id"] == report_id), -1)
        if report_index == -1:
            return jsonify({"error": "Report not found"}), 404
        report = reports_db[report_index]
        if report.get("image_url"):
            try:
                image_path = os.path.join(app.config["UPLOAD_FOLDER"], os.path.basename(report["image_url"]))
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                print(f"⚠️ Error deleting image: {str(e)}")
        reports_db.pop(report_index)
        save_reports(reports_db)
        print(f"✅ Report deleted: {report_id}")
        return jsonify({"message": "Report deleted successfully"}), 200
    except Exception as e:
        print(f"❌ Delete error: {str(e)}")
        return jsonify({"error": f"Failed to delete report: {str(e)}"}), 500

# ==================== IOT ROUTES ====================
@app.route("/api/iot/data", methods=["POST", "OPTIONS"])
def post_iot_data():
    if request.method == "OPTIONS":
        return "", 204
    try:
        data = request.get_json() or {}
        if not data:
            return jsonify({"error": "No IoT data provided"}), 400
        required_fields = ["device_id", "latitude", "longitude", "sensor_type", "value"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required IoT field: {field}"}), 400
        data["timestamp"] = datetime.now().isoformat()
        value = float(data.get("value", 0.0))
        sensor_type = data["sensor_type"]
        data["alert"] = False
        if sensor_type == "speed" and value > 100:
            data["alert"] = True
        elif sensor_type == "vibration" and value > 8.0:
            data["alert"] = True
        elif sensor_type == "traffic" and value >= 3:
            data["alert"] = True
        elif sensor_type == "weather" and value >= 3:
            data["alert"] = True
        iot_db.append(data)
        save_iot_data(iot_db)
        print(f"📡 IoT Data Received: Device {data.get('device_id')}, Type: {sensor_type} | Alert: {data['alert']}")
        return jsonify({"message": "IoT data recorded", "alert": data["alert"]}), 201
    except Exception as e:
        print(f"❌ IoT data error: {str(e)}")
        return jsonify({"error": f"Failed to process IoT data: {str(e)}"}), 500

@app.route("/api/iot/alerts", methods=["GET"])
def get_iot_alerts():
    try:
        alerts = [d for d in iot_db if d.get("alert") is True]
        alerts = sorted(alerts, key=lambda x: x.get("timestamp", ""), reverse=True)[:100]
        return jsonify({"alerts": alerts, "count": len(alerts)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== STATISTICS ====================
@app.route("/api/stats", methods=["GET"])
def get_statistics():
    try:
        total_reports = len(reports_db)
        pending = len([r for r in reports_db if r.get("status") == "pending"])
        resolved = len([r for r in reports_db if r.get("status") == "resolved"])
        in_progress = len([r for r in reports_db if r.get("status") == "in-progress"])
        rejected = len([r for r in reports_db if r.get("status") == "rejected"])
        categories = {}
        for report in reports_db:
            categories[report.get("category", "unknown")] = categories.get(report.get("category", "unknown"), 0) + 1
        severities = {}
        for report in reports_db:
            severities[report.get("severity", "unknown")] = severities.get(report.get("severity", "unknown"), 0) + 1
        iot_alerts = [d for d in iot_db if d.get("alert") is True]
        speed_alerts = len([d for d in iot_alerts if d.get("sensor_type") == "speed"])
        vibration_alerts = len([d for d in iot_alerts if d.get("sensor_type") == "vibration"])
        traffic_alerts = len([d for d in iot_alerts if d.get("sensor_type") == "traffic"])
        weather_alerts = len([d for d in iot_alerts if d.get("sensor_type") == "weather"])
        recent_speed_entry = next(
            (d for d in reversed(iot_db) if d.get('sensor_type') == 'speed'), None
        )
        current_speed = float(recent_speed_entry['value']) if recent_speed_entry and 'value' in recent_speed_entry else 0
        return jsonify({
            "total_reports": total_reports,
            "pending": pending,
            "resolved": resolved,
            "in_progress": in_progress,
            "rejected": rejected,
            "categories": categories,
            "severities": severities,
            "total_users": len(users_db),
            "iot_alerts": {
                "total": len(iot_alerts),
                "speed_alerts": speed_alerts,
                "vibration_alerts": vibration_alerts,
                "traffic_alerts": traffic_alerts,
                "weather_alerts": weather_alerts,
                "current_speed": current_speed,
            },
            "total_iot_data_points": len(iot_db)
        }), 200
    except Exception as e:
        print(f"❌ Stats error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ==================== FILE SERVING, HEALTH, ERROR HANDLERS ====================
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    try:
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
    except Exception:
        return jsonify({"error": "File not found"}), 404

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "Smart Road Safety API is running (JSON file persistence)",
        "version": "1.0.2",
        "timestamp": datetime.now().isoformat(),
        "stats": {
            "total_users": len(users_db),
            "total_reports": len(reports_db),
            "total_iot_data_points": len(iot_db),
        },
    }), 200

@app.route("/api/test", methods=["GET"])
def test_endpoint():
    return jsonify({"message": "Backend is working perfectly!", "cors": "enabled", "timestamp": datetime.now().isoformat()}), 200

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({"error": "File too large. Maximum size is 16MB"}), 413

# ==================== STARTUP ====================
if __name__ == "__main__":
    current_users = len(users_db)
    current_reports = len(reports_db)
    current_iot = len(iot_db)
    print("\n" + "=" * 60)
    print("🚀 SMART ROAD SAFETY BACKEND STARTING (v1.0.2 JSON)...")
    print("=" * 60)
    print("📡 API URL: http://localhost:5000")
    print("💾 Storage: JSON Files (in /data)")
    print(f"👥 Total Users: {current_users}")
    print(f"📋 Total Reports: {current_reports}")
    print(f"🌐 Total IoT Data Points: {current_iot}")
    print("=" * 60 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
