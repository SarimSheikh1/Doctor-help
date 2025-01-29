from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
import datetime

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///doctor_assistant.db'
db = SQLAlchemy(app)

# Initialize the chatbot
chatbot = ChatBot('DoctorAssistant')
trainer = ChatterBotCorpusTrainer(chatbot)
trainer.train("chatterbot.corpus.english")  # Train with basic English corpus

# Database models
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(10), nullable=False)

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    medication = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Rejected

# Create database tables
with app.app_context():
    db.create_all()

# Twilio configuration for SMS (replace with your credentials)
from twilio.rest import Client
TWILIO_ACCOUNT_SID = 'your_account_sid'
TWILIO_AUTH_TOKEN = 'your_auth_token'
TWILIO_PHONE_NUMBER = 'your_twilio_phone_number'
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint to handle patient queries.
    """
    user_input = request.json.get('message')
    response = str(chatbot.get_response(user_input))
    return jsonify({'response': response})

@app.route('/schedule', methods=['POST'])
def schedule_appointment():
    """
    Endpoint to schedule an appointment.
    """
    patient_name = request.json.get('patient_name')
    patient_phone = request.json.get('patient_phone')
    date = request.json.get('date')
    time = request.json.get('time')

    if not patient_name or not patient_phone or not date or not time:
        return jsonify({'error': 'Missing patient name, phone, date, or time'}), 400

    # Save patient to database
    patient = Patient(name=patient_name, phone=patient_phone)
    db.session.add(patient)
    db.session.commit()

    # Save appointment to database
    appointment = Appointment(patient_id=patient.id, date=date, time=time)
    db.session.add(appointment)
    db.session.commit()

    # Send SMS confirmation
    try:
        message = twilio_client.messages.create(
            body=f"Hi {patient_name}, your appointment is scheduled for {date} at {time}.",
            from_=TWILIO_PHONE_NUMBER,
            to=patient_phone
        )
    except Exception as e:
        print(f"Failed to send SMS: {e}")

    return jsonify({'message': f'Appointment scheduled for {patient_name} at {date} {time}'})

@app.route('/prescription/request', methods=['POST'])
def request_prescription():
    """
    Endpoint to request a prescription refill.
    """
    patient_id = request.json.get('patient_id')
    medication = request.json.get('medication')

    if not patient_id or not medication:
        return jsonify({'error': 'Missing patient ID or medication'}), 400

    # Save prescription request to database
    prescription = Prescription(patient_id=patient_id, medication=medication)
    db.session.add(prescription)
    db.session.commit()

    return jsonify({'message': 'Prescription refill requested. The doctor will review it soon.'})

@app.route('/prescription/status/<int:patient_id>', methods=['GET'])
def prescription_status(patient_id):
    """
    Endpoint to check the status of a prescription refill.
    """
    prescriptions = Prescription.query.filter_by(patient_id=patient_id).all()
    if not prescriptions:
        return jsonify({'error': 'No prescriptions found for this patient'}), 404

    status_list = [{'id': p.id, 'medication': p.medication, 'status': p.status} for p in prescriptions]
    return jsonify(status_list)

@app.route('/appointments', methods=['GET'])
def get_appointments():
    """
    Endpoint to retrieve all scheduled appointments.
    """
    appointments = Appointment.query.all()
    appointment_list = [{'id': a.id, 'patient_id': a.patient_id, 'date': a.date, 'time': a.time} for a in appointments]
    return jsonify(appointment_list)

if __name__ == '__main__':
    app.run(debug=True)