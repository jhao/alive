from datetime import UTC, datetime

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///guardianme.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nickname = db.Column(db.String(80), nullable=False)
    age = db.Column(db.Integer)
    notify_threshold_days = db.Column(db.Integer, default=2)
    reminder_time = db.Column(db.String(20), default="09:00")
    last_checkin_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))


class EmergencyContact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(32))
    channel_priority = db.Column(db.String(120), default="email,sms,whatsapp")


class VitalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    heart_rate = db.Column(db.Integer, nullable=False)
    blood_oxygen = db.Column(db.Integer)
    source = db.Column(db.String(80), default="manual")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))


class NotificationJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    type = db.Column(db.String(32), nullable=False)  # missed_checkin | critical_vital
    channels = db.Column(db.String(120), nullable=False)
    payload = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(32), default="queued")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))


@app.route("/health", methods=["GET"])
def health() -> tuple:
    return jsonify({"ok": True}), 200


@app.route("/api/register", methods=["POST"])
def register() -> tuple:
    data = request.get_json(force=True)
    email = data.get("email", "").strip().lower()
    nickname = data.get("nickname", "").strip()
    age = data.get("age")

    if not email or not nickname:
        return jsonify({"error": "email 和 nickname 必填"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "用户已存在"}), 409

    user = User(email=email, nickname=nickname, age=age)
    db.session.add(user)
    db.session.commit()
    return jsonify({"id": user.id, "email": user.email, "nickname": user.nickname}), 201


@app.route("/api/checkin", methods=["POST"])
def checkin() -> tuple:
    data = request.get_json(force=True)
    email = data.get("email", "").strip().lower()

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "用户不存在"}), 404

    user.last_checkin_at = datetime.now(UTC)
    db.session.commit()
    return jsonify({"message": "签到成功", "last_checkin_at": user.last_checkin_at.isoformat()}), 200


@app.route("/api/contacts", methods=["POST"])
def add_contact() -> tuple:
    data = request.get_json(force=True)
    email = data.get("email", "").strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "用户不存在"}), 404

    contact = EmergencyContact(
        user_id=user.id,
        name=data.get("name", "未命名联系人"),
        email=data.get("contact_email"),
        phone=data.get("phone"),
        channel_priority=data.get("channel_priority", "email,sms,whatsapp"),
    )
    db.session.add(contact)
    db.session.commit()
    return jsonify({"message": "联系人已添加", "contact_id": contact.id}), 201


@app.route("/api/contacts/<email>", methods=["GET"])
def list_contacts(email: str) -> tuple:
    user = User.query.filter_by(email=email.strip().lower()).first()
    if not user:
        return jsonify({"error": "用户不存在"}), 404

    contacts = EmergencyContact.query.filter_by(user_id=user.id).all()
    return (
        jsonify(
            [
                {
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "phone": c.phone,
                    "channel_priority": c.channel_priority,
                }
                for c in contacts
            ]
        ),
        200,
    )


@app.route("/api/vitals", methods=["POST"])
def submit_vitals() -> tuple:
    data = request.get_json(force=True)
    email = data.get("email", "").strip().lower()
    heart_rate = int(data.get("heart_rate", 0))
    blood_oxygen = data.get("blood_oxygen")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "用户不存在"}), 404

    record = VitalRecord(user_id=user.id, heart_rate=heart_rate, blood_oxygen=blood_oxygen)
    db.session.add(record)

    alert = None
    if heart_rate == 0:
        alert = "critical_vital:no_pulse"
    elif heart_rate < 40:
        alert = "critical_vital:low_heart_rate"

    if alert:
        job = NotificationJob(
            user_id=user.id,
            type="critical_vital",
            channels="email,sms,whatsapp",
            payload=f"{user.nickname} 心率异常: {heart_rate} bpm ({alert})",
        )
        db.session.add(job)

    db.session.commit()

    return (
        jsonify(
            {
                "message": "生命体征已记录",
                "heart_rate": heart_rate,
                "alert": alert,
            }
        ),
        201,
    )


@app.route("/api/dashboard/<email>", methods=["GET"])
def dashboard(email: str) -> tuple:
    user = User.query.filter_by(email=email.strip().lower()).first()
    if not user:
        return jsonify({"error": "用户不存在"}), 404

    latest_vital = (
        VitalRecord.query.filter_by(user_id=user.id).order_by(VitalRecord.created_at.desc()).first()
    )
    jobs = NotificationJob.query.filter_by(user_id=user.id).order_by(NotificationJob.created_at.desc()).limit(5)

    return (
        jsonify(
            {
                "user": {
                    "email": user.email,
                    "nickname": user.nickname,
                    "last_checkin_at": user.last_checkin_at.isoformat() if user.last_checkin_at else None,
                },
                "latest_vital": {
                    "heart_rate": latest_vital.heart_rate,
                    "blood_oxygen": latest_vital.blood_oxygen,
                    "created_at": latest_vital.created_at.isoformat(),
                }
                if latest_vital
                else None,
                "recent_notifications": [
                    {
                        "id": j.id,
                        "type": j.type,
                        "channels": j.channels,
                        "payload": j.payload,
                        "status": j.status,
                        "created_at": j.created_at.isoformat(),
                    }
                    for j in jobs
                ],
            }
        ),
        200,
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
