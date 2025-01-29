import streamlit as st  # type: ignore
import re

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="PK Hospitals Virtual Assistant", layout="centered")

# -------------------- SESSION STATE --------------------
# For appointments
if "appointments" not in st.session_state:
    st.session_state["appointments"] = []

if "appointment_counter" not in st.session_state:
    st.session_state["appointment_counter"] = 1

# For library books
if "books" not in st.session_state:
    st.session_state["books"] = []
    # Each book is a dict with fields:
    #   id, title, author, year, borrower (None if available)
if "book_id_counter" not in st.session_state:
    st.session_state["book_id_counter"] = 1

# Conversation storage
if "conversation" not in st.session_state:
    st.session_state["conversation"] = [
        ("assistant", "Hello! I'm the PK Hospitals Virtual Assistant. How can I help you today?")
    ]

# -------------------- INTENT PARSING --------------------
def parse_user_input(user_input: str) -> str:
    """
    Determine whether the user wants to manage appointments or library books,
    or something else. Return a short string representing the intent.
    
    We'll match specific phrases to differentiate between appointment vs. book tasks.
    """
    text = user_input.lower()

    # Appointment logic
    if ("book an appointment" in text or "schedule an appointment" in text
        or "book appointment" in text or "schedule appointment" in text):
        return "book_appointment"
    elif "cancel" in text and "appointment" in text:
        return "cancel_appointment"
    elif "reschedule" in text and "appointment" in text:
        return "reschedule_appointment"
    elif ("show appointments" in text or "list appointments" in text 
          or "check appointments" in text):
        return "show_appointments"
    elif ("search appointment" in text or "search appointments" in text):
        return "search_appointments"

    # Book logic
    if ("add a book" in text or "add book" in text):
        return "add_book"
    elif ("remove a book" in text or "remove book" in text):
        return "remove_book"
    elif ("list books" in text or "show books" in text):
        return "list_books"
    elif ("search book" in text or "search books" in text):
        return "search_books"
    elif ("update book" in text):
        return "update_book"
    elif ("borrow" in text and "book" in text):
        return "borrow_book"
    elif ("return" in text and "book" in text):
        return "return_book"

    # If not matched, see if "appointment" or "book" is in text as a fallback
    if "appointment" in text:
        # Could be "book" or "show" or "search" in a simpler sense
        if "cancel" in text:
            return "cancel_appointment"
        if "reschedule" in text:
            return "reschedule_appointment"
        if "search" in text:
            return "search_appointments"
        if "show" in text or "list" in text:
            return "show_appointments"
        return "book_appointment"

    if "book" in text:
        # Could be library book context
        if "add" in text:
            return "add_book"
        if "remove" in text:
            return "remove_book"
        if "list" in text or "show" in text:
            return "list_books"
        if "search" in text:
            return "search_books"

    # Otherwise, unknown
    return "unknown"


# ========================================================================
#                           APPOINTMENT FUNCTIONS
# ========================================================================

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


def book_appointment(user_input: str, user_name: str = "John Doe") -> str:
    """ Create a new appointment. """
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
    """ Cancel an appointment by ID or naive date/time matching. """
    id_match = re.search(r"\d+", user_input)
    if id_match:
        apt_id = int(id_match.group(0))
        for apt in st.session_state["appointments"]:
            if apt['id'] == apt_id:
                st.session_state["appointments"].remove(apt)
                return (f"Appointment ID {apt_id} with Dr. {apt['doctor']} has been canceled.")
        return "No appointment found with that ID."
    else:
        # Try matching date/time
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


def reschedule_appointment(user_input: str) -> str:
    """ Reschedule an existing appointment by ID to a new date/time. """
    id_match = re.search(r"\d+", user_input)
    if not id_match:
        return "Please specify the appointment ID to reschedule."

    apt_id = int(id_match.group(0))
    _, date_info, time_info = extract_details_for_booking(user_input)

    for apt in st.session_state["appointments"]:
        if apt['id'] == apt_id:
            if date_info != "not specified":
                apt['date'] = date_info
            if time_info != "not specified":
                apt['time'] = time_info
            return (f"Appointment ID {apt_id} has been rescheduled to "
                    f"{apt['date']} at {apt['time']}.")
    return "No appointment found with that ID to reschedule."


def show_appointments(user_name: str = "John Doe") -> str:
    """ List all appointments for the user. """
    user_appointments = [apt for apt in st.session_state["appointments"] if apt['user'] == user_name]
    if not user_appointments:
        return "You have no upcoming appointments."

    lines = ["Here are your upcoming appointments:"]
    for apt in user_appointments:
        lines.append(
            f"  ID: {apt['id']} | Doctor: {apt['doctor']} "
            f"| Date: {apt['date']} | Time: {apt['time']}"
        )
    return "\n".join(lines)


def search_appointments(user_input: str, user_name: str = "John Doe") -> str:
    """ Search for appointments by ID, doctor name, or date. """
    id_match = re.search(r"\d+", user_input)
    doctor_match = re.search(r"dr\.?\s+(\w+)", user_input, re.IGNORECASE)
    date_match = re.search(
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
        r"tomorrow|today|\d{4}-\d{2}-\d{2})",
        user_input, re.IGNORECASE
    )

    user_appointments = [apt for apt in st.session_state["appointments"] if apt['user'] == user_name]

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
        return ("Please specify an ID, doctor name, or date. E.g., 'Search appointment 2'.")

    lines = ["Search results:"]
    for apt in results:
        lines.append(
            f"  ID: {apt['id']} | Doctor: {apt['doctor']} "
            f"| Date: {apt['date']} | Time: {apt['time']}"
        )
    return "\n".join(lines)


# ========================================================================
#                           LIBRARY BOOK FUNCTIONS
# ========================================================================

def add_book(user_input: str) -> str:
    """
    Adds a new book to the library. 
    We'll look for the pattern: "Add a book <title> by <author> in <year>"
    If <year> is missing, we store None or "Unknown".
    """
    # Regex capturing groups: title, author, year
    # e.g. "Add a book Harry Potter by J K Rowling in 1997"
    # We'll be flexible: year is optional
    pattern = r"book\s+(.+?)\s+by\s+(.+?)(?:\s+in\s+(\d{4}))?$"
    match = re.search(pattern, user_input, re.IGNORECASE)
    if not match:
        return (
            "Please specify the book title, author, and optionally year. "
            "E.g., 'Add a book Harry Potter by J K Rowling in 1997'."
        )

    title = match.group(1).strip('"\' ')
    author = match.group(2).strip('"\' ')
    year = match.group(3) if match.group(3) else "Unknown"

    new_book = {
        "id": st.session_state["book_id_counter"],
        "title": title,
        "author": author,
        "year": year,
        "borrower": None  # None means the book is currently available
    }
    st.session_state["books"].append(new_book)
    st.session_state["book_id_counter"] += 1

    return f"Book added: '{title}' by {author} ({year}). [ID {new_book['id']}]"


def remove_book(user_input: str) -> str:
    """
    Removes a book by ID or by partial title.
    E.g., "Remove book 1" or "Remove book Harry Potter"
    """
    # 1) Try ID
    id_match = re.search(r"\b(\d+)\b", user_input)
    if id_match:
        book_id = int(id_match.group(0))
        for bk in st.session_state["books"]:
            if bk["id"] == book_id:
                st.session_state["books"].remove(bk)
                return f"Removed book ID {book_id} ('{bk['title']}')."
        return f"No book found with ID {book_id}."

    # 2) Try partial title
    match_title = re.search(r"remove\s+book\s+(.+)", user_input, re.IGNORECASE)
    if match_title:
        possible_title = match_title.group(1).strip('"\' ')
        for bk in st.session_state["books"]:
            if possible_title.lower() in bk["title"].lower():
                st.session_state["books"].remove(bk)
                return (f"Removed book '{bk['title']}' by {bk['author']} "
                        f"(ID {bk['id']}).")
        return f"No book found with title containing '{possible_title}'."

    return "Please specify the book to remove (ID or partial title)."


def list_books() -> str:
    """ Lists all books in the library. """
    if not st.session_state["books"]:
        return "No books currently in the library."

    lines = ["Here are the books in the library:"]
    for bk in st.session_state["books"]:
        status = "(Borrowed)" if bk["borrower"] else "(Available)"
        lines.append(
            f"  ID: {bk['id']} | '{bk['title']}' by {bk['author']} ({bk['year']}) {status}"
        )
    return "\n".join(lines)


def search_books(user_input: str) -> str:
    """
    Search books by ID, title, author, or year.
    e.g., "Search book 2", "Search book Harry Potter", "Search book 1997"
    """
    id_match = re.search(r"\b(\d+)\b", user_input)
    if id_match:
        book_id = int(id_match.group(0))
        results = [bk for bk in st.session_state["books"] if bk["id"] == book_id]
        if not results:
            return f"No book found with ID {book_id}."
    else:
        # Look for everything after "search book"
        match_search = re.search(r"search\s+book\s+(.+)", user_input, re.IGNORECASE)
        if not match_search:
            return (
                "Please specify a book ID, title, author, or year. "
                "E.g., 'Search book 2' or 'Search book Harry Potter'."
            )
        query = match_search.group(1).strip('"\' ')

        # Partial match in title, author, or year
        results = []
        for bk in st.session_state["books"]:
            if (query.lower() in bk["title"].lower() or
                query.lower() in bk["author"].lower() or
                (bk["year"] != "Unknown" and query == bk["year"])):
                results.append(bk)

        if not results:
            return f"No books match '{query}'."

    lines = ["Book search results:"]
    for bk in results:
        status = "(Borrowed)" if bk["borrower"] else "(Available)"
        lines.append(
            f"  ID: {bk['id']} | '{bk['title']}' by {bk['author']} ({bk['year']}) {status}"
        )
    return "\n".join(lines)


def update_book(user_input: str) -> str:
    """
    Update a book's title, author, or year by ID.
    e.g.: "Update book 2 title The Secret Garden"
    or:   "Update book 1 author Jane Austen"
    or:   "Update book 3 year 1990"
    We'll parse out "book <id> <field> <new_value>" using a naive approach.
    """
    # Check for ID
    id_match = re.search(r"book\s+(\d+)\s+(\w+)\s+(.+)$", user_input, re.IGNORECASE)
    if not id_match:
        return (
            "Please specify an ID and what you'd like to update. E.g.:\n"
            "'Update book 2 title The Secret Garden'\n"
            "'Update book 1 author Jane Austen'\n"
            "'Update book 3 year 1990'"
        )

    book_id_str, field, new_value = id_match.group(1), id_match.group(2), id_match.group(3)
    book_id = int(book_id_str)

    # Find the book
    for bk in st.session_state["books"]:
        if bk["id"] == book_id:
            field_lower = field.lower()
            if field_lower in ["title", "author", "year"]:
                bk[field_lower] = new_value.strip('"\' ')
                return f"Book {book_id} updated. New {field_lower}: {bk[field_lower]}"
            return f"Unknown field '{field}'. Use title, author, or year."
    return f"No book found with ID {book_id}."


def borrow_book(user_input: str) -> str:
    """
    Borrow a book by ID if available.
    e.g. "Borrow book 2 by Sarim" or "Borrow book 2"
    We'll parse a possible borrower name after "by".
    """
    # Check for ID
    match_id = re.search(r"borrow\s+book\s+(\d+)(?:\s+by\s+(.+))?", user_input, re.IGNORECASE)
    if not match_id:
        return (
            "Please specify the book ID (and optional borrower name). E.g.:\n"
            "'Borrow book 2 by Ali'"
        )

    book_id_str = match_id.group(1)
    borrower = match_id.group(2) if match_id.group(2) else "Unknown User"
    book_id = int(book_id_str)

    # Find the book
    for bk in st.session_state["books"]:
        if bk["id"] == book_id:
            if bk["borrower"]:
                return (f"Sorry, '{bk['title']}' is already borrowed by "
                        f"{bk['borrower']}.")
            bk["borrower"] = borrower
            return f"You have borrowed '{bk['title']}' (ID {book_id})."

    return f"No book found with ID {book_id}."


def return_book(user_input: str) -> str:
    """
    Return a borrowed book by ID.
    e.g. "Return book 2"
    """
    match_id = re.search(r"return\s+book\s+(\d+)", user_input, re.IGNORECASE)
    if not match_id:
        return "Please specify the book ID to return. E.g., 'Return book 2'."

    book_id = int(match_id.group(1))
    for bk in st.session_state["books"]:
        if bk["id"] == book_id:
            if not bk["borrower"]:
                return f"Book ID {book_id} ('{bk['title']}') is not borrowed."
            bk["borrower"] = None
            return f"Returned '{bk['title']}' (ID {book_id})."
    return f"No book found with ID {book_id}."


# ========================================================================
#                          MAIN HANDLER
# ========================================================================
def handle_user_input(user_text: str) -> str:
    """ Route user input to the correct function. """
    intent = parse_user_input(user_text)

    # Appointment branch
    if intent == "book_appointment":
        return book_appointment(user_text)
    elif intent == "cancel_appointment":
        return cancel_appointment(user_text)
    elif intent == "reschedule_appointment":
        return reschedule_appointment(user_text)
    elif intent == "show_appointments":
        return show_appointments()
    elif intent == "search_appointments":
        return search_appointments(user_text)

    # Book branch
    elif intent == "add_book":
        return add_book(user_text)
    elif intent == "remove_book":
        return remove_book(user_text)
    elif intent == "list_books":
        return list_books()
    elif intent == "search_books":
        return search_books(user_text)
    elif intent == "update_book":
        return update_book(user_text)
    elif intent == "borrow_book":
        return borrow_book(user_text)
    elif intent == "return_book":
        return return_book(user_text)

    # Unknown
    else:
        return (
            "I'm sorry, I didn't understand. Here are some ideas:\n\n"
            "**Appointments**:\n"
            "- 'Book an appointment with Dr. Khan on Monday at 2pm.'\n"
            "- 'Cancel appointment 1.'\n"
            "- 'Reschedule appointment 2 to Friday at 4pm.'\n"
            "- 'Show appointments.'\n"
            "- 'Search appointment Dr. Khan.'\n\n"
            "**Library Books**:\n"
            "- 'Add a book Harry Potter by J K Rowling in 1997.'\n"
            "- 'Remove book 1.'\n"
            "- 'List books.'\n"
            "- 'Search book Harry Potter.'\n"
            "- 'Update book 1 author Jane Austen'\n"
            "- 'Borrow book 2 by Hina'\n"
            "- 'Return book 2'"
        )


# ========================================================================
#                          STREAMLIT UI
# ========================================================================
st.title("PK Hospitals Virtual Assistant")

# Display conversation so far
for speaker, text in st.session_state["conversation"]:
    if speaker == "assistant":
        st.markdown(f"**Assistant:** {text}")
    else:
        st.markdown(f"**You:** {text}")

# Text input for user
user_input = st.text_input("Ask me something about appointments or books:", "")

# Create columns for multiple buttons
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
        help_message = (
            "**Appointments**:\n"
            "- 'Book an appointment with Dr. Khan on Monday at 2pm.'\n"
            "- 'Cancel appointment 1.'\n"
            "- 'Reschedule appointment 2 to Friday at 4pm.'\n"
            "- 'Show appointments.'\n"
            "- 'Search appointment Dr. Khan.'\n\n"
            "**Library Books**:\n"
            "- 'Add a book Harry Potter by J K Rowling in 1997.'\n"
            "- 'Remove book 1.'\n"
            "- 'List books.'\n"
            "- 'Search book Harry Potter.'\n"
            "- 'Update book 1 author Jane Austen'\n"
            "- 'Borrow book 2 by Hina'\n"
            "- 'Return book 2'"
        )
        st.session_state["conversation"].append(("assistant", help_message))

with col3:
    if st.button("Goodbye"):
        goodbye_text = "Goodbye! Thanks for using PK Hospitals Virtual Assistant."
        st.session_state["conversation"].append(("assistant", goodbye_text))
        # Optionally stop the script:
        # st.stop()

# Show updated conversation
st.write("---")
for speaker, text in st.session_state["conversation"]:
    if speaker == "assistant":
        st.markdown(f"**Assistant:** {text}")
    else:
        st.markdown(f"**You:** {text}")
