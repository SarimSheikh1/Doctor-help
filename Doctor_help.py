import streamlit as st
import re

st.set_page_config(page_title="PK Hospitals Virtual Assistant", layout="centered")

# -- Initialize Session State --
if "appointments" not in st.session_state:
    st.session_state["appointments"] = []

if "appointment_counter" not in st.session_state:
    st.session_state["appointment_counter"] = 1

# We'll store conversation messages as tuples: (speaker, text)
if "conversation" not in st.session_state:
    st.session_state["conversation"] = [
        ("assistant", "Hello! I'm the PK Hospitals Virtual Assistant. How can I help you today?")
    ]


def parse_user_input(user_input: str) -> str:
    """
    Detect user intent (book, cancel, show, reschedule, search, etc.)
    Very naive approach using keyword search.
    """
    user_input_lower = user_input.lower()
    if "book" in user_input_lower or "schedule" in user_input_lower:
        return "book"
    elif "cancel" in user_input_lower:
        return "cancel"
    elif "reschedule" in user_input_lower:
        return "reschedule"
    elif ("show" in user_input_lower or 
          "list" in user_input_lower or 
          "check" in user_input_lower):
        return "show"
    elif "search" in user_input_lower:
        return "search"
    else:
        return "unknown"


def extract_details_for_booking(user_input: str):
    """
    Basic regex-based extraction for doctor, date, and time.
    e.g.: "Book appointment with Dr. Khan next Monday at 2pm"
    """
    # Find doctor name (naively assumes "Dr. <name>")
    doctor_match = re.search(r"dr\.?\s+(\w+)", user_input, re.IGNORECASE)
    doctor_name = doctor_match.group(1) if doctor_match else "Unknown"

    # Find date (e.g. Monday, tomorrow, 2025-01-01)
    date_match = re.search(
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
        r"tomorrow|today|\d{4}-\d{2}-\d{2})",
        user_input, re.IGNORECASE
    )
    date_info = date_match.group(0) if date_match else "not specified"

    # Find time (e.g. 2 pm, 2:30 pm)
    time_match = re.search(r"(\d{1,2}\s?(am|pm|\:\d{2}))", user_input, re.IGNORECASE)
    time_info = time_match.group(0) if time_match else "not specified"

    return doctor_name.capitalize(), date_info, time_info


def book_appointment(user_input: str, user_name: str = "John Doe") -> str:
    """
    Books a new appointment and stores it in session state.
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

    return (
        f"Appointment booked with Dr. {doctor} on {date_info} at {time_info}. "
        f"Your reference ID is {new_appointment['id']}."
    )


def cancel_appointment(user_input: str) -> str:
    """
    Cancel an appointment by ID or by date/time (very naive).
    """
    id_match = re.search(r"\d+", user_input)
    if id_match:
        # User gave an appointment ID
        apt_id = int(id_match.group(0))
        for apt in st.session_state["appointments"]:
            if apt['id'] == apt_id:
                st.session_state["appointments"].remove(apt)
                return (f"Your appointment ID {apt_id} with Dr. {apt['doctor']} "
                        "has been canceled.")
        return "No appointment found with that ID."
    else:
        # No ID provided, attempt to match by date/time
        date_match = re.search(
            r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
            r"tomorrow|today|\d{4}-\d{2}-\d{2})",
            user_input, re.IGNORECASE
        )
        time_match = re.search(r"(\d{1,2}\s?(am|pm|\:\d{2}))", user_input, re.IGNORECASE)

        date_text = date_match.group(0).lower() if date_match else None
        time_text = time_match.group(0).lower() if time_match else None

        for apt in st.session_state["appointments"]:
            # If either date or time is None, ignore that part
            if ((date_text is None or apt['date'].lower() == date_text) and 
                (time_text is None or apt['time'].lower() == time_text)):
                st.session_state["appointments"].remove(apt)
                return (f"Appointment with Dr. {apt['doctor']} on "
                        f"{apt['date']} at {apt['time']} has been canceled.")
        return "No matching appointment found to cancel."


def reschedule_appointment(user_input: str) -> str:
    """
    Reschedule an existing appointment to a new date/time by ID.
    Example: "Reschedule appointment 2 to next Friday at 4 pm"
    """
    # First, extract ID
    id_match = re.search(r"\d+", user_input)
    if not id_match:
        return "Please specify the appointment ID to reschedule (e.g., 'Reschedule appointment 2 ...')."

    apt_id = int(id_match.group(0))
    # Next, parse out any new date/time from the user input
    # (We reuse extract_details_for_booking, but only date/time matter now).
    _, date_info, time_info = extract_details_for_booking(user_input)

    # Find the appointment with that ID
    for apt in st.session_state["appointments"]:
        if apt['id'] == apt_id:
            # Update date/time if they're not "not specified"
            if date_info and date_info != "not specified":
                apt['date'] = date_info
            if time_info and time_info != "not specified":
                apt['time'] = time_info

            return (f"Appointment ID {apt_id} has been rescheduled to "
                    f"{apt['date']} at {apt['time']}.")
    return "No appointment found with that ID to reschedule."


def show_appointments(user_name: str = "John Doe") -> str:
    """
    Lists all appointments for the user. Returns a formatted string.
    """
    user_appointments = [apt for apt in st.session_state["appointments"] if apt['user'] == user_name]
    if not user_appointments:
        return "You have no upcoming appointments."

    lines = ["Here are your upcoming appointments:"]
    for apt in user_appointments:
        lines.append(
            f"  ID: {apt['id']} | Doctor: {apt['doctor']} | "
            f"Date: {apt['date']} | Time: {apt['time']}"
        )
    return "\n".join(lines)


def search_appointments(user_input: str, user_name: str = "John Doe") -> str:
    """
    Search for appointments by doctor name, date, or ID.
    Example: "Search appointment Dr. Khan" or "Search appointment 2"
    """
    # Check if there's a numeric ID
    id_match = re.search(r"\d+", user_input)
    doctor_match = re.search(r"dr\.?\s+(\w+)", user_input, re.IGNORECASE)
    date_match = re.search(
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
        r"tomorrow|today|\d{4}-\d{2}-\d{2})",
        user_input, re.IGNORECASE
    )

    # Filter user's appointments
    user_appointments = [apt for apt in st.session_state["appointments"] if apt['user'] == user_name]

    # If ID is present
    if id_match:
        apt_id = int(id_match.group(0))
        results = [apt for apt in user_appointments if apt['id'] == apt_id]
        if not results:
            return f"No appointment found with ID {apt_id}."
    # If doctor's name is present
    elif doctor_match:
        doctor_name = doctor_match.group(1).capitalize()
        results = [apt for apt in user_appointments if apt['doctor'] == doctor_name]
        if not results:
            return f"No appointments found with Dr. {doctor_name}."
    # If date is present
    elif date_match:
        date_text = date_match.group(0).lower()
        results = [apt for apt in user_appointments if apt['date'].lower() == date_text]
        if not results:
            return f"No appointments found on {date_text}."
    else:
        return "Please specify what you want to search by (e.g., appointment ID, doctor name, or date)."

    # Format results
    lines = ["Search results:"]
    for apt in results:
        lines.append(
            f"  ID: {apt['id']} | Doctor: {apt['doctor']} | "
            f"Date: {apt['date']} | Time: {apt['time']}"
        )
    return "\n".join(lines)


def handle_user_input(user_text: str) -> str:
    """
    Determine the intent and return the assistant's response message.
    """
    intent = parse_user_input(user_text)
    if intent == "book":
        return book_appointment(user_text)
    elif intent == "cancel":
        return cancel_appointment(user_text)
    elif intent == "show":
        return show_appointments()
    elif intent == "search":
        return search_appointments(user_text)
    elif intent == "reschedule":
        return reschedule_appointment(user_text)
    else:
        return (
            "I'm sorry, I didn't understand. "
            "Try commands like 'book', 'cancel', 'show', 'reschedule', or 'search'."
        )


# ------------- Streamlit UI -------------
st.title("PK Hospitals - Virtual Assistant")

# Display existing conversation
for speaker, text in st.session_state["conversation"]:
    if speaker == "assistant":
        st.markdown(f"**Assistant:** {text}")
    else:
        st.markdown(f"**You:** {text}")

# User input
user_input = st.text_input("Ask me something about your doctor's appointments:", "")

# "Send" button
if st.button("Send") and user_input.strip():
    # Save user message
    st.session_state["conversation"].append(("user", user_input))
    
    # Generate assistant response
    assistant_reply = handle_user_input(user_input)
    
    # Save assistant response
    st.session_state["conversation"].append(("assistant", assistant_reply))
    
    # Clear the text input by resetting the user_input variable
    # (Streamlit doesn't allow direct clearing of text_input easily,
    #  but we can simulate it by showing a new, empty text_input on reload.)
    # We won't use st.experimental_rerun. The user will see new messages immediately.
    
    # Instead, just show the updated conversation below
    # This is enough for many simple chat UIs.

# Re-display the conversation after sending
st.write("---")
for speaker, text in st.session_state["conversation"]:
    if speaker == "assistant":
        st.markdown(f"**Assistant:** {text}")
    else:
        st.markdown(f"**You:** {text}")
