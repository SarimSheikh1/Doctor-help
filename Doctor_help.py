import streamlit as st  # type: ignore  # Helps avoid mypy "import not found" stub errors
import re

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="PK Hospitals Virtual Assistant", layout="centered")

# -------------------- SESSION STATE --------------------
if "appointments" not in st.session_state:
    st.session_state["appointments"] = []

if "appointment_counter" not in st.session_state:
    st.session_state["appointment_counter"] = 1

# We'll store conversation messages in a list of (speaker, text) tuples.
if "conversation" not in st.session_state:
    st.session_state["conversation"] = [
        ("assistant", "Hello! I'm the PK Hospitals Virtual Assistant. How can I help you today?")
    ]

# -------------------- HELPER FUNCTIONS --------------------
def parse_user_input(user_input: str) -> str:
    """
    Detect user intent by simple keyword checks.
    We add 'list_doctors' as a new function if user says 'list doctors' or 'show doctors'.
    """
    user_input_lower = user_input.lower()

    if "book" in user_input_lower or "schedule" in user_input_lower:
        return "book"
    elif "cancel" in user_input_lower:
        return "cancel"
    elif "reschedule" in user_input_lower:
        return "reschedule"
    elif ("show" in user_input_lower or "list" in user_input_lower or "check" in user_input_lower):
        # If user specifically mentions "doctors" as well, we’ll interpret as "list_doctors"
        if "doctor" in user_input_lower:
            return "list_doctors"
        return "show"
    elif "search" in user_input_lower:
        return "search"
    else:
        return "unknown"


def extract_details_for_booking(user_input: str):
    """
    Extract doctor, date, and time from user input with naive regex.
    E.g., "Book an appointment with Dr. Khan Monday at 2 pm"
    """
    # Doctor name: look for "Dr. Name"
    doctor_match = re.search(r"dr\.?\s+(\w+)", user_input, re.IGNORECASE)
    doctor_name = doctor_match.group(1) if doctor_match else "Unknown"

    # Date: Monday, tomorrow, YYYY-MM-DD, etc.
    date_match = re.search(
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
        r"tomorrow|today|\d{4}-\d{2}-\d{2})",
        user_input, re.IGNORECASE
    )
    date_info = date_match.group(0) if date_match else "not specified"

    # Time: 2 pm, 2:30 pm, etc.
    time_match = re.search(r"(\d{1,2}\s?(am|pm|\:\d{2}))", user_input, re.IGNORECASE)
    time_info = time_match.group(0) if time_match else "not specified"

    return doctor_name.capitalize(), date_info, time_info


# -------------------- NEW FUNCTION: List Doctors --------------------
def list_doctors() -> str:
    """
    Example function to list available doctors in PK Hospitals.
    Customize this with real data if desired.
    """
    doctors_data = [
        {"name": "Khan", "specialty": "Cardiology"},
        {"name": "Ali", "specialty": "Dentistry"},
        {"name": "Farooq", "specialty": "Neurology"},
    ]
    lines = ["Here are some doctors at PK Hospitals:"]
    for doc in doctors_data:
        lines.append(f"  Dr. {doc['name']} - {doc['specialty']}")
    return "\n".join(lines)


# -------------------- BOOK --------------------
def book_appointment(user_input: str, user_name: str = "John Doe") -> str:
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

# -------------------- CANCEL --------------------
def cancel_appointment(user_input: str) -> str:
    id_match = re.search(r"\d+", user_input)
    if id_match:
        apt_id = int(id_match.group(0))
        for apt in st.session_state["appointments"]:
            if apt['id'] == apt_id:
                st.session_state["appointments"].remove(apt)
                return (f"Appointment ID {apt_id} with Dr. {apt['doctor']} has been canceled.")
        return "No appointment found with that ID."
    else:
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


# -------------------- RESCHEDULE --------------------
def reschedule_appointment(user_input: str) -> str:
    id_match = re.search(r"\d+", user_input)
    if not id_match:
        return "Please specify the appointment ID to reschedule."

    apt_id = int(id_match.group(0))
    # Extract new date/time (doctor can remain same)
    _, date_info, time_info = extract_details_for_booking(user_input)

    for apt in st.session_state["appointments"]:
        if apt['id'] == apt_id:
            if date_info and date_info != "not specified":
                apt['date'] = date_info
            if time_info and time_info != "not specified":
                apt['time'] = time_info
            return (f"Appointment ID {apt_id} has been rescheduled to "
                    f"{apt['date']} at {apt['time']}.")
    return "No appointment found with that ID to reschedule."


# -------------------- SHOW APPOINTMENTS --------------------
def show_appointments(user_name: str = "John Doe") -> str:
    user_appointments = [
        apt for apt in st.session_state["appointments"]
        if apt['user'] == user_name
    ]
    if not user_appointments:
        return "You have no upcoming appointments."

    lines = ["Here are your upcoming appointments:"]
    for apt in user_appointments:
        lines.append(
            f"  ID: {apt['id']} | Doctor: {apt['doctor']} "
            f"| Date: {apt['date']} | Time: {apt['time']}"
        )
    return "\n".join(lines)


# -------------------- SEARCH APPOINTMENTS --------------------
def search_appointments(user_input: str, user_name: str = "John Doe") -> str:
    # Check numeric ID
    id_match = re.search(r"\d+", user_input)
    # Check doctor name
    doctor_match = re.search(r"dr\.?\s+(\w+)", user_input, re.IGNORECASE)
    # Check date
    date_match = re.search(
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
        r"tomorrow|today|\d{4}-\d{2}-\d{2})",
        user_input, re.IGNORECASE
    )

    user_appointments = [
        apt for apt in st.session_state["appointments"] if apt['user'] == user_name
    ]

    if id_match:
        apt_id = int(id_match.group(0))
        results = [apt for apt in user_appointments if apt['id'] == apt_id]
        if not results:
            return f"No appointment found with ID {apt_id}."
    elif doctor_match:
        doctor_name = doctor_match.group(1).capitalize()
        results = [apt for apt in user_appointments if apt['doctor'] == doctor_name]
        if not results:
            return f"No appointments found with Dr. {doctor_name}."
    elif date_match:
        date_text = date_match.group(0).lower()
        results = [apt for apt in user_appointments if apt['date'].lower() == date_text]
        if not results:
            return f"No appointments found on {date_text}."
    else:
        return ("Please specify what you want to search by: appointment ID, "
                "doctor name, or date (e.g., 'Search appointment 2').")

    # Format results
    lines = ["Search results:"]
    for apt in results:
        lines.append(
            f"  ID: {apt['id']} | Doctor: {apt['doctor']} "
            f"| Date: {apt['date']} | Time: {apt['time']}"
        )
    return "\n".join(lines)


# -------------------- HANDLE USER INPUT --------------------
def handle_user_input(user_text: str) -> str:
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
    elif intent == "list_doctors":
        return list_doctors()
    else:
        return (
            "I'm sorry, I didn't understand. "
            "Try commands like 'book', 'cancel', 'show', 'reschedule', "
            "'search', or 'list doctors'."
        )

# -------------------- UI LAYOUT --------------------
st.title("PK Hospitals - Virtual Assistant")

# Display conversation so far
for speaker, text in st.session_state["conversation"]:
    if speaker == "assistant":
        st.markdown(f"**Assistant:** {text}")
    else:
        st.markdown(f"**You:** {text}")

# Text input for user
user_input = st.text_input("Ask me something about your doctor's appointments:", "")

# Button row
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Send"):
        if user_input.strip():
            # Record user message
            st.session_state["conversation"].append(("user", user_input))

            # Assistant response
            assistant_reply = handle_user_input(user_input)
            st.session_state["conversation"].append(("assistant", assistant_reply))

with col2:
    if st.button("More Help"):
        # Provide usage instructions
        help_message = (
            "**Here are some things you can do:**\n"
            "- **Book an appointment**: 'Book an appointment with Dr. Khan Monday at 2pm.'\n"
            "- **Show appointments**: 'Show my appointments.'\n"
            "- **Cancel**: 'Cancel appointment 1.'\n"
            "- **Reschedule**: 'Reschedule appointment 2 to Friday at 4pm.'\n"
            "- **Search**: 'Search appointment 2' or 'Search appointment Dr. Khan.'\n"
            "- **List doctors**: 'List doctors.'\n"
            "\nFeel free to try these commands!"
        )
        st.session_state["conversation"].append(("assistant", help_message))

with col3:
    if st.button("Goodbye"):
        goodbye_text = "Goodbye! Thanks for using PK Hospitals Virtual Assistant."
        st.session_state["conversation"].append(("assistant", goodbye_text))
        # Optionally, you can stop Streamlit to end the app:
        # st.stop()


# Show updated conversation
st.write("---")
for speaker, text in st.session_state["conversation"]:
    if speaker == "assistant":
        st.markdown(f"**Assistant:** {text}")
    else:
        st.markdown(f"**You:** {text}")
