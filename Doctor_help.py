import streamlit as st
import re

st.set_page_config(page_title="PK Hospitals Virtual Assistant", layout="centered")

# -- Initialize Session State --
if "appointments" not in st.session_state:
    st.session_state["appointments"] = []

if "appointment_counter" not in st.session_state:
    st.session_state["appointment_counter"] = 1

if "conversation" not in st.session_state:
    # We'll store all chat messages here as tuples: (speaker, text)
    st.session_state["conversation"] = [("assistant", "Hello! I'm the PK Hospitals Virtual Assistant. How can I help you today?")]


def parse_user_input(user_input: str) -> str:
    """
    A simplistic parser to detect intent and extract relevant info.
    For a real-world scenario, replace this with a robust NLP approach.
    """
    user_input_lower = user_input.lower()

    # Check for booking, canceling, or checking appointment
    if "book" in user_input_lower or "schedule" in user_input_lower:
        return "book"
    elif "cancel" in user_input_lower:
        return "cancel"
    elif ("show" in user_input_lower 
          or "list" in user_input_lower 
          or "check" in user_input_lower):
        return "show"
    else:
        return "unknown"


def extract_details_for_booking(user_input: str):
    """
    Very basic regex-based extraction for doctor and date/time info.
    This can be replaced by more advanced NLP tools.
    """
    # Extract doctor's name - naive approach:
    doctor_match = re.search(r"dr\.?\s+(\w+)", user_input, re.IGNORECASE)
    doctor_name = doctor_match.group(1) if doctor_match else "Unknown"

    # Extract date (monday, tomorrow, YYYY-MM-DD, etc.)
    date_match = re.search(
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
        r"tomorrow|today|\d{4}-\d{2}-\d{2})",
        user_input, re.IGNORECASE
    )
    date_info = date_match.group(0) if date_match else "not specified"

    # Extract time (1 pm, 1:30 pm, etc.)
    time_match = re.search(r"(\d{1,2}\s?(am|pm|\:\d{2}))", user_input, re.IGNORECASE)
    time_info = time_match.group(0) if time_match else "not specified"

    return doctor_name.capitalize(), date_info, time_info


def book_appointment(user_input: str, user_name: str = "John Doe") -> str:
    """
    Books a new appointment and stores it in the session state.
    Returns a response message.
    """
    doctor, date_info, time_info = extract_details_for_booking(user_input)

    new_appointment = {
        'id': st.session_state["appointment_counter"],
        'doctor': doctor,
        'date': date_info,
        'time': time_info,
        'user': user_name
    }
    st.session_state["appointments"].append(new_appointment)
    st.session_state["appointment_counter"] += 1

    return (f"Appointment booked with Dr. {doctor} on {date_info} at {time_info}. "
            f"Your reference ID is {new_appointment['id']}.")


def cancel_appointment(user_input: str) -> str:
    """
    Cancel an appointment by ID or by matching date/time if needed.
    Returns a response message.
    """
    # Try to extract an ID
    id_match = re.search(r"\d+", user_input)
    if id_match:
        apt_id = int(id_match.group(0))
        for apt in st.session_state["appointments"]:
            if apt['id'] == apt_id:
                st.session_state["appointments"].remove(apt)
                return f"Your appointment ID {apt_id} with Dr. {apt['doctor']} has been canceled."
        return "No appointment found with that ID."
    else:
        # If no ID is provided, try to find by date/time (very naive).
        date_match = re.search(
            r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
            r"tomorrow|today|\d{4}-\d{2}-\d{2})",
            user_input, re.IGNORECASE
        )
        time_match = re.search(r"(\d{1,2}\s?(am|pm|\:\d{2}))", user_input, re.IGNORECASE)

        date_text = date_match.group(0).lower() if date_match else None
        time_text = time_match.group(0).lower() if time_match else None

        for apt in st.session_state["appointments"]:
            if ((date_text is None or apt['date'].lower() == date_text) and
               (time_text is None or apt['time'].lower() == time_text)):
                st.session_state["appointments"].remove(apt)
                return (f"Appointment with Dr. {apt['doctor']} on "
                        f"{apt['date']} at {apt['time']} has been canceled.")
        return "No matching appointment found to cancel."


def show_appointments(user_name="John Doe") -> str:
    """
    Lists all appointments for the user. Returns the formatted string.
    """
    user_appointments = [apt for apt in st.session_state["appointments"] if apt['user'] == user_name]
    if not user_appointments:
        return "You have no upcoming appointments."

    lines = ["Here are your upcoming appointments:"]
    for apt in user_appointments:
        lines.append(f"  ID: {apt['id']} | Doctor: {apt['doctor']} | Date: {apt['date']} | Time: {apt['time']}")
    return "\n".join(lines)


def handle_user_input(user_text: str) -> str:
    """
    Determine the intent and return the assistant's response message.
    """
    intent = parse_user_input(user_text)

    if intent == "book":
        response = book_appointment(user_text)
    elif intent == "cancel":
        response = cancel_appointment(user_text)
    elif intent == "show":
        response = show_appointments()
    else:
        response = ("I'm sorry, I didn't understand. "
                    "Please try 'book', 'cancel', or 'show' appointments.")
    return response


# --- Streamlit UI ---
st.title("PK Hospitals - Virtual Assistant")

# Display existing conversation
for speaker, text in st.session_state["conversation"]:
    if speaker == "assistant":
        st.markdown(f"**Assistant:** {text}")
    else:
        st.markdown(f"**You:** {text}")

# User input
user_input = st.text_input("Ask me something about your doctor's appointments:", "")

if st.button("Send") and user_input.strip():
    # Store user's message in conversation
    st.session_state["conversation"].append(("user", user_input))

    # Generate assistant response
    assistant_reply = handle_user_input(user_input)

    # Store assistant's reply
    st.session_state["conversation"].append(("assistant", assistant_reply))
    
    # Rerun to show the updated conversation
    st.experimental_rerun()
