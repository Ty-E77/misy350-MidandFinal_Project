# -- Importing necessary packages --
# breadcrumb
import streamlit as st
import json
from pathlib import Path
from datetime import datetime, time as dt_time
import uuid
import time
import re

# -- Setting page configuration --
st.set_page_config(page_title = "Real Estate Finder", 
                   page_icon = "🏠",
                   layout = "centered",
                   initial_sidebar_state = "expanded")


def apply_base_styles():
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1.25rem;
                padding-bottom: 1.25rem;
                max-width: 980px;
            }
            h1, h2, h3 {
                letter-spacing: -0.01em;
            }
            div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stHorizontalBlock"]) {
                gap: 0.7rem;
            }
            div[data-testid="stCaptionContainer"] p {
                color: #6b7280;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


apply_base_styles()


# -- Loading all json files, defining a valdation check for all json files, and setting defaults  -- 
data_load_warnings = []


def load_json_list(file_path, label):
    if not file_path.exists():
        data_load_warnings.append(f"{label}: file not found. Starting with empty data.")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data
        else:
            data_load_warnings.append(f"{label}: invalid format (expected a list). Using empty data.")
            return []

    except (json.JSONDecodeError, OSError):
        data_load_warnings.append(f"{label}: unreadable or malformed JSON. Using empty data.")
        return []
    
def is_valid_user(user):
    required_keys = ["id", "email", "password", "role"]
    return isinstance(user, dict) and all(key in user for key in required_keys)

def is_valid_property(listing):
    required_keys = [
        "id", "agent_id", "title", "address", "city", "state",
        "price", "bedrooms", "bathrooms", "property_sqft", "property_type"
    ]
    return isinstance(listing, dict) and all(key in listing for key in required_keys)

def is_valid_inquiry(inquiry):
    required_keys = [
        "id", "listing_id", "property_title", "agent_id", "buyer_id",
        "buyer_name", "buyer_email", "buyer_phone", "subject", "message"
    ]
    return isinstance(inquiry, dict) and all(key in inquiry for key in required_keys)

def is_valid_booking(booking):
    required_keys = [
        "id", "listing_id", "property_title", "agent_id", "buyer_id",
        "buyer_name", "buyer_email", "buyer_phone", "appointment_type",
        "appointment_date", "appointment_time"
    ]
    return isinstance(booking, dict) and all(key in booking for key in required_keys)
    
json_file_properties = Path("properties.json")
json_file_users = Path("users.json")
json_file_inquiries = Path("inquiry.json")
json_file_bookings = Path("bookings.json")

users = load_json_list(json_file_users, "Users")
users = [user for user in users if is_valid_user(user)]
for user in users:
    user.setdefault("full_name", "")
    user.setdefault("role", "")

properties = load_json_list(json_file_properties, "Properties")
properties = [listing for listing in properties if is_valid_property(listing)]
for listing in properties:
    listing.setdefault("status", "Available")
    listing.setdefault("description", "")
    listing.setdefault("contact_name", "")
    listing.setdefault("contact_email", "")
    listing.setdefault("contact_phone", "")


inquiries = load_json_list(json_file_inquiries, "Inquiries")
inquiries = [inquiry for inquiry in inquiries if is_valid_inquiry(inquiry)]
for inquiry in inquiries:
    inquiry.setdefault("response", "")
    inquiry.setdefault("response_at", "")
    inquiry.setdefault("status", "New")
    inquiry.setdefault("subject", "")
    inquiry.setdefault("message", "")

bookings = load_json_list(json_file_bookings, "Bookings")
bookings = [booking for booking in bookings if is_valid_booking(booking)]
for booking in bookings:
    booking.setdefault("status", "Pending")
    booking.setdefault("message", "")

# --  Functions for repetitive tasks --
def save_json_list(file_path, data):
    for attempt in range(3):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            return True
        except (OSError, TypeError, ValueError) as exc:
            if attempt == 2:
                st.error(f"Could not save {file_path.name}: {exc}")
                st.warning("Please try again. Your current form inputs are still on screen.")
                return False
            time.sleep(0.2)

# -- Session state defaults -- 
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "user" not in st.session_state:
    st.session_state["user"] = None

if "page" not in st.session_state:
    st.session_state["page"] = "home"

# -- Agent Session States --
if "selected_agent_listing_id" not in st.session_state:
    st.session_state["selected_agent_listing_id"] = None

if "selected_other_listing_id" not in st.session_state:
    st.session_state["selected_other_listing_id"] = None

if "edit_agent_inquiry_id" not in st.session_state:
    st.session_state["edit_agent_inquiry_id"] = None

# -- Buyer Session States -- 
if "booking_listing_id" not in st.session_state:
    st.session_state["booking_listing_id"] = None

if "selected_listing_id" not in st.session_state:
    st.session_state["selected_listing_id"] = None

if "question_listing_id" not in st.session_state:
    st.session_state["question_listing_id"] = None

if "edit_booking_id" not in st.session_state:
    st.session_state["edit_booking_id"] = None

if "edit_inquiry_id" not in st.session_state:
    st.session_state["edit_inquiry_id"] = None

# -- Chatbot Session States
if "agent_chatbot" not in st.session_state:
    st.session_state["agent_chatbot"] = [
        {
            "role": "assistant",
            "content": "Hi! I’m your agent assistant. Ask me about listings, buyer requests, or adding a property."
        }
    ]

if "buyer_chatbot" not in st.session_state:
    st.session_state["buyer_chatbot"] = [
        {
            "role": "assistant",
            "content": "Hi! I’m your buyer assistant. Ask me about browsing listings, booking appointments, or sending inquiries."
        }
    ]

if "_queued_rerun" not in st.session_state:
    st.session_state["_queued_rerun"] = False

# -- More Functions for repetive tasks after learning on 4/6/2026 --
def queue_rerun():
    if not st.session_state.get("_queued_rerun"):
        st.session_state["_queued_rerun"] = True


def flush_rerun():
    if st.session_state.get("_queued_rerun"):
        st.session_state["_queued_rerun"] = False
        st.rerun()


def navigate_to(page, **extra_updates):
    state_changed = st.session_state.get("page") != page
    st.session_state["page"] = page

    for state_key, state_value in extra_updates.items():
        if st.session_state.get(state_key) != state_value:
            state_changed = True
        st.session_state[state_key] = state_value

    if state_changed:
        queue_rerun()


def update_state_and_rerun(**state_updates):
    state_changed = False
    for state_key, state_value in state_updates.items():
        if st.session_state.get(state_key) != state_value:
            state_changed = True
        st.session_state[state_key] = state_value

    if state_changed:
        queue_rerun()


def make_key(section, item_id, action):
    return f"{section}_{item_id}_{action}"


def normalize_email(value):
    return value.strip().lower()


def is_valid_email(email):
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return bool(re.match(pattern, email))


def normalize_phone(phone):
    return "".join(char for char in phone if char.isdigit())


def is_valid_phone(phone):
    return len(phone) == 10


def show_data_warnings():
    if data_load_warnings:
        with st.expander("Data file warnings"):
            for warning in data_load_warnings:
                st.warning(warning)


def parse_date_safe(value, default_value):
    if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return default_value
    return default_value


def parse_time_safe(value, default_value):
    if hasattr(value, "hour") and hasattr(value, "minute"):
        return value

    if isinstance(value, str):
        time_formats = ["%H:%M:%S", "%H:%M"]
        for time_format in time_formats:
            try:
                return datetime.strptime(value, time_format).time()
            except ValueError:
                continue

    return default_value


def reset_state_for_logout():
    return {
        "logged_in": False,
        "user": None,
        "page": "home",
        "selected_agent_listing_id": None,
        "selected_other_listing_id": None,
        "selected_listing_id": None,
        "booking_listing_id": None,
        "question_listing_id": None,
        "edit_agent_inquiry_id": None,
        "edit_booking_id": None,
        "edit_inquiry_id": None,
    }


def find_listing_by_id(listing_id):
    for property_item in properties:
        if property_item["id"] == listing_id:
            return property_item
    return None


def render_listing_detail_sections(selected_listing):
    with st.container(border=True):
        col_left, col_right = st.columns([3, 1])

        with col_left:
            st.markdown(f"### {selected_listing['title']}")
            st.markdown(
                f"**{selected_listing['address']}, {selected_listing['city']}, {selected_listing['state']}**"
            )

        with col_right:
            st.markdown(f"**Status:** {selected_listing['status']}")
            st.markdown(f"### ${selected_listing['price']:,}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        with st.container(border=True):
            st.markdown("**Bedrooms**")
            st.markdown(f"### {selected_listing['bedrooms']}")

    with col2:
        with st.container(border=True):
            st.markdown("**Bathrooms**")
            st.markdown(f"### {selected_listing['bathrooms']}")

    with col3:
        with st.container(border=True):
            st.markdown("**Square Feet**")
            st.markdown(f"### {selected_listing['property_sqft']}")

    with col4:
        with st.container(border=True):
            st.markdown("**Property Type**")
            st.markdown(f"### {selected_listing['property_type']}")

    with st.container(border=True):
        st.markdown("### Description")
        st.markdown(selected_listing["description"])

    with st.container(border=True):
        st.markdown("### Contact Information")
        st.markdown(f"**Name:** {selected_listing['contact_name']}")
        st.markdown(f"**Email:** {selected_listing['contact_email']}")
        st.markdown(f"**Phone:** {selected_listing['contact_phone']}")


def process_chat_message(role, chat_key, user_input):
    st.session_state[chat_key].append({"role": "user", "content": user_input})

    if role == "Agent":
        response = get_agent_chatbot_response(user_input)
    else:
        response = get_buyer_chatbot_response(user_input)

    st.session_state[chat_key].append({"role": "assistant", "content": response})

def get_agent_chatbot_response(user_input):
    user_input = user_input.strip().lower()

    if user_input == "how do i add a new listing?":
        return "Go to the sidebar and click 'Add Property Listings'. Fill out the listing overview, property details, location, and contact information, then click 'Add Listing'."

    elif user_input == "where do i manage my listings?":
        return "Go to 'View/Manage Property Listings' in the sidebar. In the 'My Property Listings' tab, click 'Manage Listing' on any property to update or delete it."

    elif user_input == "where do i view buyer requests?":
        return "Go to 'Buyer Bookings & Inquiries' from the sidebar. There you can confirm or decline bookings and respond to buyer questions."

    else:
        return "I’m not sure about that yet. Try one of the suggested questions above."

def get_buyer_chatbot_response(user_input):
    user_input = user_input.strip().lower()

    if user_input == "how do i browse listings?":
        return "Go to the sidebar and click 'Browse Listings'. You can filter by property type and status, then click 'View Listing Details' for more information."

    elif user_input == "how do i book an appointment?":
        return "Open a property from 'Browse Listings', click 'Book an Appointment', complete the form, and submit it. Your request will appear under 'My Bookings & Inquiries'."

    elif user_input == "how do i ask a question?":
        return "Open a property from 'Browse Listings', click 'Ask a Question(s)', choose a subject, type your question, and submit it. You can later view the response in 'My Bookings & Inquiries'."

    else:
        return "I’m not sure about that yet. Try one of the suggested questions above."

def show_chat_bot(role):
    if role == "Agent":
        chat_key = "agent_chatbot"
        title = "### 🤖 Agent Assistant"
        suggestions = [
            "How do I add a new listing?",
            "Where do I manage my listings?",
            "Where do I view buyer requests?"
        ]
        default_message = "Hi! I’m your agent assistant. Ask me about listings, buyer requests, or adding a property."
    else:
        chat_key = "buyer_chatbot"
        title = "### 🤖 Buyer Assistant"
        suggestions = [
            "How do I browse listings?",
            "How do I book an appointment?",
            "How do I ask a question?"
        ]
        default_message = "Hi! I’m your buyer assistant. Ask me about browsing listings, booking appointments, or sending inquiries."

    with st.container(border=True):
        st.markdown(title)
        st.caption("Choose a suggested question or type your own below.")

        for index, column in enumerate(st.columns(3), start=1):
            suggestion = suggestions[index - 1]
            if column.button(
                suggestion,
                key=f"{role.lower()}_chat_suggestion_btn_{index}",
                use_container_width=True,
            ):
                process_chat_message(role, chat_key, suggestion)
                queue_rerun()

        st.divider()

        with st.container(border=True, height=260):
            for message in st.session_state[chat_key]:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        st.divider()

        chat_input_key = f"{role.lower()}_chat_text_input"

        col_input, col_send = st.columns([4, 1])

        with col_input:
            user_input = st.text_input(
                "Ask a question...",
                key=chat_input_key,
                label_visibility="collapsed",
                placeholder="Ask a question..."
            )

        with col_send:
            send_clicked = st.button(
                "Send",
                key=f"{role.lower()}_chat_send_btn",
                type="primary",
                use_container_width=True
            )

        if send_clicked:
            user_input = user_input.strip()

            if user_input:
                process_chat_message(role, chat_key, user_input)
                st.session_state[chat_input_key] = ""
                queue_rerun()

        if st.button(
            "Clear Chat",
            key=f"{role.lower()}_chat_clear_bottom_btn",
            use_container_width=True
        ):
            st.session_state[chat_key] = [
                {
                    "role": "assistant",
                    "content": default_message
                }
            ]
            st.session_state[chat_input_key] = ""
            queue_rerun()

# -- Creating registration & login page -- 
def show_login_page():
    st.markdown("# Real Estate Finder")
    st.caption("Browse listings, book appointments, and connect with agents.")
    show_data_warnings()
    st.divider()

    tab1, tab2 = st.tabs(["Log In", "Register"])

    with tab1:
        with st.container(border=True):
            st.markdown("## Welcome Back")

            email_login = st.text_input(
                "Email",
                placeholder="Enter your email",
                key="login_email"
            )
            password_login = st.text_input(
                "Password",
                type="password",
                key="login_password"
            )

            btn_login = st.button(
                "Log In",
                key="auth_login_submit_btn",
                use_container_width=True,
                type="primary"
            )

            if btn_login:
                login_errors = []
                login_check = None
                email_login = normalize_email(email_login)

                if not email_login or not password_login:
                    login_errors.append("Please enter your email and password.")

                if email_login and not is_valid_email(email_login):
                    login_errors.append("Please enter a valid email address.")

                if not login_errors:
                    with st.spinner("Verifying credentials..."):
                        time.sleep(0.5)

                    for user in users:
                        if user["email"] == email_login and user["password"] == password_login:
                            login_check = user
                            break

                    if login_check:
                        update_state_and_rerun(logged_in=True, user=login_check, page="home")
                    else:
                        st.error("Invalid email or password.")
                else:
                    for login_error in login_errors:
                        st.warning(login_error)

    with tab2:
        with st.container(border=True):
            st.markdown("## Create Account")

            full_name = st.text_input(
                "Full Name",
                placeholder="Enter your full name",
                key="full_name_new"
            )
            email = st.text_input(
                "Email",
                placeholder="Enter your email",
                key="email_new"
            )
            password = st.text_input(
                "Password",
                type="password",
                key="password_new"
            )
            role = st.selectbox(
                "Role",
                ["Agent", "Buyer"],
                key="role_new"
            )

            btn_create = st.button(
            "Create Account",
            key="auth_register_submit_btn",
            use_container_width=True,
            type="primary"
            )

            if btn_create:
                with st.spinner("Creating account..."):
                    time.sleep(0.5)

                new_email = normalize_email(email)
                existing_user = None
                register_errors = []

                for user in users:
                    if user["email"].strip().lower() == new_email:
                        existing_user = user
                        break

                if existing_user is not None:
                    register_errors.append("An account with this email already exists.")

                if not full_name or not new_email or not password:
                    register_errors.append("Please fill in all required fields.")

                if not is_valid_email(new_email):
                    register_errors.append("Please enter a valid email address.")

                if register_errors:
                    for register_error in register_errors:
                        st.error(register_error)
                else:
                    users.append({
                        "id": str(uuid.uuid4()),
                        "email": new_email,
                        "full_name": full_name.strip(),
                        "password": password,
                        "role": role,
                        "registered_at": str(datetime.now())
                    })
                    
                    if save_json_list(json_file_users, users):
                        st.success("Account created successfully! You can now log in.")

    flush_rerun()

# -- Defining application for agent --                                 
def show_main_app_agent():
    # -- Dashboard Page --
    if st.session_state["page"] == "home":
        st.markdown(f"## Agent Dashboard - {st.session_state['user']['full_name']}")
        st.caption("Manage listings, review buyer bookings, and respond to inquiries.")
        show_data_warnings()
        st.divider()

        # -- Calculate stats -- 
        my_listings_count = 0
        available_listings_count = 0
        pending_bookings_count = 0
        new_inquiries_count = 0

        agent_listings = []
        agent_bookings = []
        agent_inquiries = []

        for listing in properties:
            if listing["agent_id"] == st.session_state["user"]["id"]:
                agent_listings.append(listing)
                my_listings_count += 1
                if listing["status"] == "Available":
                    available_listings_count += 1

        for booking in bookings:
            if booking["agent_id"] == st.session_state["user"]["id"]:
                agent_bookings.append(booking)
                if booking["status"] == "Pending":
                    pending_bookings_count += 1

        for inquiry in inquiries:
            if inquiry["agent_id"] == st.session_state["user"]["id"]:
                agent_inquiries.append(inquiry)
                if inquiry["status"] == "New":
                    new_inquiries_count += 1

        # -- Stat Section --
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            with st.container(border=True):
                st.markdown("**My Listings**")
                st.markdown(f"### {my_listings_count}")

        with col2:
            with st.container(border=True):
                st.markdown("**Available Listings**")
                st.markdown(f"### {available_listings_count}")

        with col3:
            with st.container(border=True):
                st.markdown("**Pending Bookings**")
                st.markdown(f"### {pending_bookings_count}")

        with col4:
            with st.container(border=True):
                st.markdown("**New Inquiries**")
                st.markdown(f"### {new_inquiries_count}")

        st.divider()

        # -- Quick actions -- 
        st.markdown("### Quick Actions")

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            if st.button("View My Listings", key="agent_home_view_listings_btn", type="primary", use_container_width=True):
                navigate_to("properties_listings")

        with col_b:
            if st.button("Add New Listing", key="agent_home_add_listing_btn", use_container_width=True):
                navigate_to("add_listings")

        with col_c:
            if st.button("View Buyer Requests", key="agent_home_buyer_requests_btn", use_container_width=True):
                navigate_to("buyer_inquiries")

        st.divider()
        show_chat_bot("Agent")
        st.divider()

        # -- Recent activity -- 
        st.markdown("### Recent Activity")

        latest_listing = agent_listings[-1] if agent_listings else None
        latest_booking = agent_bookings[-1] if agent_bookings else None
        latest_inquiry = agent_inquiries[-1] if agent_inquiries else None

        if latest_listing:
            with st.container(border=True):
                st.markdown("**Latest Listing**")
                st.markdown(f"**Title:** {latest_listing['title']}")
                st.markdown(f"**Status:** {latest_listing['status']}")
                st.markdown(f"**Price:** ${latest_listing['price']:,}")

        if latest_booking:
            with st.container(border=True):
                st.markdown("**Latest Booking Request**")
                st.markdown(f"**Property:** {latest_booking['property_title']}")
                st.markdown(f"**Buyer:** {latest_booking['buyer_name']}")
                st.markdown(f"**Status:** {latest_booking['status']}")

        if latest_inquiry:
            with st.container(border=True):
                st.markdown("**Latest Inquiry**")
                st.markdown(f"**Property:** {latest_inquiry['property_title']}")
                st.markdown(f"**Buyer:** {latest_inquiry['buyer_name']}")
                st.markdown(f"**Status:** {latest_inquiry['status']}")

        if not latest_listing and not latest_booking and not latest_inquiry:
            st.info("No recent activity yet. Start by adding your first listing.")

    # -- Properties Page --
    elif st.session_state["page"] == "properties_listings":
        st.markdown("# View Property Listings")
        st.divider()

        tablist, taball = st.tabs(["My Property Listings", "Other Property Listings"])

        with tablist:
            st.markdown("### My Listings")

            my_listings = []
            for listing in properties:
                if listing["agent_id"] == st.session_state["user"]["id"]:
                    my_listings.append(listing)

            with st.container(border=True):
                st.markdown("###### Filter Listings")

                selected_type_my = st.selectbox(
                    "Property Type",
                    ["All", "House", "Apartment", "Condo", "Townhouse"],
                    key="my_type_filter"
                )

                selected_status_my = st.selectbox(
                    "Status",
                    ["All", "Available", "Pending", "Sold"],
                    key="my_status_filter"
                )

            filtered_my_listings = []
            for listing in my_listings:
                type_match = selected_type_my == "All" or listing["property_type"] == selected_type_my
                status_match = selected_status_my == "All" or listing["status"] == selected_status_my

                if type_match and status_match:
                    filtered_my_listings.append(listing)

            st.markdown(f"#### My Total Listings: {len(filtered_my_listings)}")

            if not filtered_my_listings:
                st.info("You have no listings matching these filters.")
            else:
                for listing in filtered_my_listings:
                    with st.container(border=True):
                        col_title, col_space, col_price = st.columns([3, 1, 1])

                        with col_title:
                            st.markdown(f"### {listing['title']}")

                        with col_price:
                            st.markdown(f"### **${listing['price']:,}**")

                        st.markdown(
                            f"##### **Address:** {listing['address']}, {listing['city']}, {listing['state']}"
                        )
                        st.markdown(f"##### **Status:** {listing['status']}")

                        if st.button(
                            "Manage Listing",
                            key=make_key("agent_listing", listing["id"], "manage"),
                            type="primary",
                            use_container_width=True
                        ):
                            navigate_to("manage_listing", selected_agent_listing_id=listing["id"])

        with taball:
            st.markdown("### Other Agent Listings")

            with st.container(border=True):
                st.markdown("###### Filter Listings")

                selected_type = st.selectbox(
                    "Property Type",
                    ["All", "House", "Apartment", "Condo", "Townhouse"],
                    key="all_type_filter"
                )

                selected_status = st.selectbox(
                    "Status",
                    ["All", "Available", "Pending", "Sold"],
                    key="all_status_filter"
                )

            filtered_properties = []
            for listing in properties:
                # only show listings that are NOT this agent's
                if listing["agent_id"] == st.session_state["user"]["id"]:
                    continue

                type_match = selected_type == "All" or listing["property_type"] == selected_type
                status_match = selected_status == "All" or listing["status"] == selected_status

                if type_match and status_match:
                    filtered_properties.append(listing)

            st.markdown(f"#### Total Other Listings: {len(filtered_properties)}")

            if not filtered_properties:
                st.info("No listings match your filters.")
            else:
                for listing in filtered_properties:
                    with st.container(border=True):
                        col_title, col_space, col_price = st.columns([3, 1, 1])

                        with col_title:
                            st.markdown(f"### {listing['title']}")

                        with col_price:
                            st.markdown(f"### **${listing['price']:,}**")

                        st.markdown(
                            f"##### **Address:** {listing['address']}, {listing['city']}, {listing['state']}"
                        )
                        st.markdown(f"##### **Status:** {listing['status']}")

                        if st.button(
                            "View Listing Details",
                            key=make_key("other_listing", listing["id"], "view"),
                            type="primary",
                            use_container_width=True
                        ):
                            navigate_to("view_other_listing_details", selected_other_listing_id=listing["id"])

    # -- Manage Listings Page --
    elif st.session_state["page"] == "manage_listing":
        selected_listing = find_listing_by_id(st.session_state["selected_agent_listing_id"])

        if selected_listing is None:
            st.error("Listing not found.")
        else:
            st.markdown("## Manage Listing")
            st.divider()
            render_listing_detail_sections(selected_listing)

            # Action buttons
            col_btn1, col_btn2, col_btn3 = st.columns(3)

            with col_btn1:
                if st.button(
                    "Update Listing",
                    key=f"edit_listing_{selected_listing['id']}",
                    type="primary",
                    use_container_width=True
                ):
                    navigate_to("edit_listing")

            with col_btn2:
                if st.button(
                    "Delete Listing",
                    key=f"delete_listing_{selected_listing['id']}",
                    use_container_width=True
                ):
                    properties.remove(selected_listing)

                    if save_json_list(json_file_properties, properties):
                        st.success("Listing deleted successfully!")
                        time.sleep(0.5)
                        navigate_to("properties_listings", selected_agent_listing_id=None)

            with col_btn3:
                if st.button(
                    "← Back to My Listings",
                    key="back_to_my_listings",
                    use_container_width=True
                ):
                    navigate_to("properties_listings")

    # -- Edit Listing Page -- 
    elif st.session_state["page"] == "edit_listing":
        selected_listing = find_listing_by_id(st.session_state["selected_agent_listing_id"])

        if selected_listing is None:
            st.error("Listing not found.")
        else:
            st.markdown("## Update Listing")
            st.divider()

            title = st.text_input("Listing Title", value=selected_listing["title"])
            description = st.text_area("Description", value=selected_listing["description"])

            contact_name = st.text_input("Contact Name", value=selected_listing["contact_name"])
            contact_email = st.text_input("Contact Email", value=selected_listing["contact_email"])
            contact_phone = st.text_input("Contact Phone Number", value=selected_listing["contact_phone"])

            address = st.text_input("Street Address", value=selected_listing["address"])
            city = st.text_input("City", value=selected_listing["city"])
            state = st.text_input("State", value=selected_listing["state"])
            price = st.number_input("Price", min_value=1, value=int(selected_listing["price"]))
            bedrooms = st.number_input("Bedrooms", min_value=0, step=1, value=int(selected_listing["bedrooms"]))
            bathrooms = st.number_input("Bathrooms", min_value=0, step=1, value=int(selected_listing["bathrooms"]))
            property_sqft = st.number_input("Property Square Footage", min_value=1, step=1, value=int(selected_listing["property_sqft"]))

            property_type = st.selectbox(
                "Property Type",
                ["House", "Apartment", "Condo", "Townhouse"],
                index=["House", "Apartment", "Condo", "Townhouse"].index(selected_listing["property_type"])
            )

            status = st.selectbox(
                "Status",
                ["Available", "Pending", "Sold"],
                index=["Available", "Pending", "Sold"].index(selected_listing["status"])
            )

            col_save, col_cancel = st.columns(2)

            with col_save:
                if st.button(
                    "Save Changes",
                    key=f"save_listing_{selected_listing['id']}",
                    type="primary",
                    use_container_width=True
                ):
                    title = title.strip()
                    description = description.strip()
                    contact_name = contact_name.strip()
                    contact_email = normalize_email(contact_email)
                    contact_phone = normalize_phone(contact_phone)
                    address = address.strip()
                    city = city.strip()
                    state = state.strip()
                    edit_listing_errors = []

                    if not title or not address or not city or not state or not contact_name or not contact_email or not contact_phone:
                        edit_listing_errors.append("Please fill in all required fields.")

                    if not is_valid_phone(contact_phone):
                        edit_listing_errors.append("Enter a valid 10-digit phone number.")

                    if not is_valid_email(contact_email):
                        edit_listing_errors.append("Enter a valid email address.")

                    if edit_listing_errors:
                        for edit_listing_error in edit_listing_errors:
                            st.error(edit_listing_error)
                    else:
                        selected_listing["title"] = title
                        selected_listing["description"] = description
                        selected_listing["contact_name"] = contact_name
                        selected_listing["contact_email"] = contact_email
                        selected_listing["contact_phone"] = contact_phone
                        selected_listing["address"] = address
                        selected_listing["city"] = city
                        selected_listing["state"] = state
                        selected_listing["price"] = price
                        selected_listing["bedrooms"] = bedrooms
                        selected_listing["bathrooms"] = bathrooms
                        selected_listing["property_sqft"] = property_sqft
                        selected_listing["property_type"] = property_type
                        selected_listing["status"] = status

                        if save_json_list(json_file_properties, properties):
                            st.success("Listing updated successfully!")
                            time.sleep(0.5)
                            navigate_to("manage_listing")

            with col_cancel:
                if st.button(
                    "← Cancel",
                    key=f"cancel_edit_listing_{selected_listing['id']}",
                    use_container_width=True
                ):
                    navigate_to("manage_listing")
    
    # -- View Other Agents Listings
    elif st.session_state["page"] == "view_other_listing_details":
        selected_listing = find_listing_by_id(st.session_state["selected_other_listing_id"])

        if selected_listing is None:
            st.error("Listing not found.")
        else:
            st.markdown("## View Listing Details")
            st.divider()
            render_listing_detail_sections(selected_listing)

            if st.button(
                "← Back to Other Listings",
                key="back_to_other_agent_listings",
                use_container_width=True
            ):
                navigate_to("properties_listings", selected_other_listing_id=None)

    # -- Add Listings Page --
    elif st.session_state["page"] == "add_listings":
        st.markdown("# Add New Listing")
        st.caption("Create a new property listing for buyers to view, book, and inquire about.")
        st.divider()

        # -- Listing Overview --
        with st.container(border=True):
            st.markdown("### Listing Overview")
            title = st.text_input(
                "Listing Title",
                placeholder="Ex: Modern 4 Bedroom Family Home"
            )
            description = st.text_area(
                "Description",
                placeholder="Write a short description of the property"
            )

        # -- Property Details --
        with st.container(border=True):
            st.markdown("### Property Details")

            col1, col2 = st.columns(2)

            with col1:
                property_type = st.selectbox(
                    "Property Type",
                    ["House", "Apartment", "Condo", "Townhouse"]
                )
                price = st.number_input("Price", min_value=1)
                bedrooms = st.number_input("Bedrooms", min_value=0, step=1)

            with col2:
                status = st.selectbox(
                    "Status",
                    ["Available", "Pending", "Sold"]
                )
                bathrooms = st.number_input("Bathrooms", min_value=0, step=1)
                property_sqft = st.number_input("Property Square Footage", min_value=1, step=1)

        # -- Location --
        with st.container(border=True):
            st.markdown("### Property Location")

            address = st.text_input(
                "Street Address",
                placeholder="Enter street address"
            )

            col1, col2 = st.columns(2)
            with col1:
                city = st.text_input("City", placeholder="Enter city")
            with col2:
                state = st.text_input("State", placeholder="Enter state")

        # -- Contact Information --
        with st.container(border=True):
            st.markdown("### Contact Information")

            contact_name = st.text_input(
                "Contact Name",
                placeholder="John Doe"
            )

            col1, col2 = st.columns(2)
            with col1:
                contact_email = st.text_input(
                    "Contact Email",
                    placeholder="name@email.com"
                )
            with col2:
                contact_phone = st.text_input(
                    "Contact Phone Number",
                    placeholder="3025551234"
                )

        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            btn_add_listing = st.button(
                "Add Listing",
                key="agent_add_listing_submit_btn",
                type="primary",
                use_container_width=True
            )

        with col_btn2:
            btn_cancel_listing = st.button(
                "← Cancel",
                key="agent_cancel_listing_submit_btn",
                use_container_width=True
            )

        if btn_cancel_listing:
            navigate_to("properties_listings")

        if btn_add_listing:
            with st.spinner("Listing is being created..."):
                time.sleep(0.5)

                title = title.strip()
                description = description.strip()
                contact_name = contact_name.strip()
                contact_email = normalize_email(contact_email)
                address = address.strip()
                city = city.strip()
                state = state.strip()
                contact_phone = normalize_phone(contact_phone)
                add_listing_errors = []

            if not title or not address or not city or not state or not contact_name or not contact_email or not contact_phone:
                add_listing_errors.append("Please fill in all required fields.")

            if not is_valid_phone(contact_phone):
                add_listing_errors.append("Enter a valid 10-digit phone number.")

            if not is_valid_email(contact_email):
                add_listing_errors.append("Enter a valid email address.")

            duplicate_listing = None
            for listing in properties:
                if (
                    listing["agent_id"] == st.session_state["user"]["id"]
                    and listing["title"].strip().lower() == title.lower()
                    and listing["address"].strip().lower() == address.lower()
                ):
                    duplicate_listing = listing
                    break

            if duplicate_listing:
                add_listing_errors.append("A listing with this title and address already exists.")

            if add_listing_errors:
                for add_listing_error in add_listing_errors:
                    st.error(add_listing_error)
            else:
                new_listing = {
                    "id": str(uuid.uuid4()),
                    "agent_id": st.session_state["user"]["id"],
                    "title": title,
                    "description": description,
                    "address": address,
                    "city": city,
                    "state": state,
                    "price": price,
                    "bedrooms": bedrooms,
                    "bathrooms": bathrooms,
                    "property_sqft": property_sqft,
                    "property_type": property_type,
                    "status": status,
                    "contact_name": contact_name,
                    "contact_email": contact_email,
                    "contact_phone": contact_phone,
                    "listing_date": str(datetime.now())
                }

                properties.append(new_listing)

                if save_json_list(json_file_properties, properties):
                    st.success("Listing added successfully!")
                    st.balloons()
                    time.sleep(0.5)
                    navigate_to("properties_listings")

    # -- Buyer bookings/inquiries Page -- 
    elif st.session_state["page"] == "buyer_inquiries":
        st.markdown("# Buyer Bookings & Inquiries")
        st.divider()

        tab_bookings, tab_inquiries = st.tabs(["View Bookings", "View Inquiries"])

        # -- Booking Section
        with tab_bookings:
            agent_bookings = []
            for booking in bookings:
                if booking["agent_id"] == st.session_state["user"]["id"]:
                    agent_bookings.append(booking)

            st.markdown("### Booking Requests")
            st.markdown(f"**Total Bookings:** {len(agent_bookings)}")
            st.divider()

            if not agent_bookings:
                st.info("You do not have any booking requests.")
            else:
                for booking in agent_bookings:
                    with st.container(border=True):
                        col_left, col_right = st.columns([3, 1])

                        with col_left:
                            st.markdown(f"### {booking['property_title']}")
                            st.markdown(f"**Buyer:** {booking['buyer_name']}")
                            st.markdown(f"**Email:** {booking['buyer_email']}")
                            st.markdown(f"**Phone:** {booking['buyer_phone']}")
                            st.markdown(f"**Appointment Type:** {booking['appointment_type']}")
                            st.markdown(f"**Date:** {booking['appointment_date']}")
                            st.markdown(f"**Time:** {booking['appointment_time']}")

                        with col_right:
                            st.markdown(f"### {booking['status']}")

                        if booking["message"]:
                            st.markdown(f"**Notes:** {booking['message']}")
                        else:
                            st.markdown("**Notes:** No additional notes provided.")

                        st.divider()

                        col1, col2 = st.columns(2)

                        with col1:
                            if st.button(
                                "Confirm Appointment",
                                key=make_key("agent_booking", booking["id"], "confirm"),
                                type="primary",
                                use_container_width=True
                            ):
                                booking["status"] = "Confirmed"

                                if save_json_list(json_file_bookings, bookings):
                                    st.success("Appointment confirmed successfully!")
                                    queue_rerun()

                        with col2:
                            if st.button(
                                "Decline Appointment",
                                key=make_key("agent_booking", booking["id"], "decline"),
                                use_container_width=True
                            ):
                                booking["status"] = "Declined"

                                if save_json_list(json_file_bookings, bookings):
                                    st.success("Appointment declined.")
                                    queue_rerun()

        # -- Inquiries Tab --
        with tab_inquiries:
            agent_inquiries = []
            for inquiry in inquiries:
                if inquiry["agent_id"] == st.session_state["user"]["id"]:
                    agent_inquiries.append(inquiry)

            st.markdown("### Buyer Inquiries")
            st.markdown(f"**Total Inquiries:** {len(agent_inquiries)}")
            st.divider()

            if not agent_inquiries:
                st.info("You do not have any buyer inquiries.")
            else:
                for inquiry in agent_inquiries:
                    with st.container(border=True):
                        col_left, col_right = st.columns([3, 1])

                        with col_left:
                            st.markdown(f"### {inquiry['property_title']}")
                            st.markdown(f"**Buyer:** {inquiry['buyer_name']}")
                            st.markdown(f"**Email:** {inquiry['buyer_email']}")
                            st.markdown(f"**Phone:** {inquiry['buyer_phone']}")
                            st.markdown(f"**Subject:** {inquiry['subject']}")
                            st.markdown(f"**Question:** {inquiry['message']}")

                        with col_right:
                            st.markdown(f"### {inquiry['status']}")

                        if inquiry.get("response"):
                            st.markdown("**Current Response:**")
                            st.markdown(inquiry["response"])

                        st.divider()

                        if st.button(
                            "Respond to Inquiry",
                            key=make_key("agent_inquiry", inquiry["id"], "edit"),
                            use_container_width=True
                        ):
                            update_state_and_rerun(edit_agent_inquiry_id=inquiry["id"])

                        if st.session_state["edit_agent_inquiry_id"] == inquiry["id"]:
                            with st.container(border=True):
                                st.markdown("### Update Inquiry")

                                updated_status = st.selectbox(
                                    "Status",
                                    ["New", "In Progress", "Answered"],
                                    index=["New", "In Progress", "Answered"].index(inquiry["status"])
                                    if inquiry["status"] in ["New", "In Progress", "Answered"] else 0,
                                    key=make_key("agent_inquiry", inquiry["id"], "status")
                                )

                                updated_response = st.text_area(
                                    "Response to Buyer",
                                    value=inquiry.get("response", ""),
                                    placeholder="Type your answer here",
                                    key=make_key("agent_inquiry", inquiry["id"], "response")
                                )

                                col_save, col_cancel = st.columns(2)

                                with col_save:
                                    if st.button(
                                        "Save Response",
                                        key=make_key("agent_inquiry", inquiry["id"], "save"),
                                        type="primary",
                                        use_container_width=True
                                    ):
                                        if updated_status == "Answered" and not updated_response.strip():
                                            st.error("Please enter a response before marking as Answered.")
                                        else:
                                            inquiry["status"] = updated_status
                                            inquiry["response"] = updated_response.strip()
                                            inquiry["response_at"] = str(datetime.now()) if updated_response.strip() else ""

                                            if save_json_list(json_file_inquiries, inquiries):
                                                st.success("Inquiry updated successfully!")
                                                update_state_and_rerun(edit_agent_inquiry_id=None)

                                with col_cancel:
                                    if st.button(
                                        "← Cancel",
                                        key=make_key("agent_inquiry", inquiry["id"], "cancel"),
                                        use_container_width=True
                                    ):
                                        update_state_and_rerun(edit_agent_inquiry_id=None)
    
    # -- Sidebar for navigating pages and logging out for agent -- 
    with st.sidebar:
        st.markdown("# **Navigator**")

        if st.button("🏠 Dashboard", key="agent_nav_dashboard_btn", type="primary", use_container_width=True):
            navigate_to("home")

        if st.button("🔍 View/Manage Property Listings", key="agent_nav_properties_btn", type="primary", use_container_width=True):
            navigate_to("properties_listings")

        if st.button("➕ Add Property Listings", key="agent_nav_add_listing_btn", type="primary", use_container_width=True):
            navigate_to("add_listings")

        if st.button("📖 Buyer Bookings & Inquiries", key="agent_nav_buyer_requests_btn", type="primary", use_container_width=True):
            navigate_to("buyer_inquiries")
        
        st.write(f"Logged in as: {st.session_state['user']['email']}")
        st.write(f"Role: {st.session_state['user']['role']}")

        if st.button("🚪 Log Out", key="agent_nav_logout_btn", type="primary", use_container_width=True):
            st.success("Logout Succesful")
            time.sleep(0.5)
            update_state_and_rerun(**reset_state_for_logout())

    flush_rerun()


# -- Defining application for buyer -- 
def show_main_app_buyer():
    # -- Dashboard Page --
    if st.session_state["page"] == "home":
        st.markdown(f"## Buyer Dashboard - {st.session_state['user']['full_name']}")
        st.caption("Browse listings, book appointments, and manage your inquiries.")
        show_data_warnings()
        st.divider()

        # -- Calculate stats --
        available_listings = 0
        my_bookings = 0
        my_inquiries = 0
        pending_bookings = 0

        for listing in properties:
            if listing["status"] in ["Available", "Pending"]:
                available_listings += 1

        for booking in bookings:
            if booking["buyer_id"] == st.session_state["user"]["id"]:
                my_bookings += 1
                if booking["status"] == "Pending":
                    pending_bookings += 1

        for inquiry in inquiries:
            if inquiry["buyer_id"] == st.session_state["user"]["id"]:
                my_inquiries += 1

        # -- Stat Section -- 
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            with st.container(border=True):
                st.markdown("**Available Listings**")
                st.markdown(f"### {available_listings}")

        with col2:
            with st.container(border=True):
                st.markdown("**My Bookings**")
                st.markdown(f"### {my_bookings}")

        with col3:
            with st.container(border=True):
                st.markdown("**Pending Bookings**")
                st.markdown(f"### {pending_bookings}")

        with col4:
            with st.container(border=True):
                st.markdown("**My Inquiries**")
                st.markdown(f"### {my_inquiries}")

        st.divider()

        #-- Quick actions --
        st.markdown("### Quick Actions")

        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("Browse Listings", key="buyer_home_browse_btn", type="primary", use_container_width=True):
                navigate_to("browse_listings")

        with col_b:
            if st.button("View My Bookings & Inquiries", key="buyer_home_requests_btn", use_container_width=True):
                navigate_to("my_inquiries")

        st.divider()
        show_chat_bot("Buyer")
        st.divider()

        # -- Recent activity --
        st.markdown("### Recent Activity")

        latest_booking = None
        latest_inquiry = None

        buyer_bookings = [b for b in bookings if b["buyer_id"] == st.session_state["user"]["id"]]
        buyer_inquiries = [i for i in inquiries if i["buyer_id"] == st.session_state["user"]["id"]]

        if buyer_bookings:
            latest_booking = buyer_bookings[-1]

        if buyer_inquiries:
            latest_inquiry = buyer_inquiries[-1]

        if latest_booking:
            with st.container(border=True):
                st.markdown("**Latest Booking**")
                st.markdown(f"Property: {latest_booking['property_title']}")
                st.markdown(f"Status: {latest_booking['status']}")
                st.markdown(f"Date: {latest_booking['appointment_date']}")

        if latest_inquiry:
            with st.container(border=True):
                st.markdown("**Latest Inquiry**")
                st.markdown(f"Property: {latest_inquiry['property_title']}")
                st.markdown(f"Status: {latest_inquiry['status']}")
                st.markdown(f"Subject: {latest_inquiry['subject']}")

        if not latest_booking and not latest_inquiry:
            st.info("No recent activity yet. Start by browsing available listings.")
    
    # -- Browse Listings Page --
    elif st.session_state["page"] == "browse_listings":
        st.markdown("# View Property Listings")
        st.divider()

        with st.container(border=True):
            st.markdown("###### Filter Listings")

            selected_type = st.selectbox(
                "Property Type",
                ["All", "House", "Apartment", "Condo", "Townhouse"],
                key="buyer_type_filter"
            )

            selected_status = st.selectbox(
                "Status",
                ["All", "Available", "Pending"],
                key="buyer_status_filter"
            )

        # Build filtered list first
        filtered_properties = []
        for listing in properties:
            if listing["status"] == "Sold":
                continue

            type_match = selected_type == "All" or listing["property_type"] == selected_type
            status_match = selected_status == "All" or listing["status"] == selected_status

            if type_match and status_match:
                filtered_properties.append(listing)

        st.markdown(f"#### Total Available Listings: {len(filtered_properties)}")

        # Render once, after filtering is complete
        if not filtered_properties:
            st.info("No listings match your filters.")
        else:
            for listing in filtered_properties:
                with st.container(border=True):
                    cola, colspace, colp = st.columns([3,1,1])
                    with cola:
                        st.markdown(f"### {listing['title']}")
                    with colp:
                        st.markdown(f"### **${listing['price']:,}**")
                    
                    st.markdown(f"##### **Address:** {listing['address']}, {listing['city']}, {listing['state']}")
                    
                    st.markdown(f"##### **Status:** {listing['status']}")

                    if st.button(
                        "View Listing Details",
                        key=make_key("buyer_listing", listing["id"], "view"),
                        type="primary",
                        use_container_width=True
                    ):
                        navigate_to("view_listing_details", selected_listing_id=listing["id"])

    # -- Shows listing Details when a user clicks the listing -- 
    elif st.session_state["page"] == "view_listing_details":
        selected_listing = find_listing_by_id(st.session_state["selected_listing_id"])

        if selected_listing is None:
            st.error("Listing not found.")
        else:
            st.markdown("## View Listing Details")
            st.divider()
            render_listing_detail_sections(selected_listing)

            # -- Buttons --
            col_btn1, col_btn2, col_btn3 = st.columns(3)

            with col_btn1:
                if st.button(
                    "Book an Appointment",
                    key=f"details_book_{selected_listing['id']}",
                    type="primary",
                    use_container_width=True
                ):
                    update_state_and_rerun(booking_listing_id=selected_listing["id"])

            with col_btn2:
                if st.button(
                    "Ask a Question(s)",
                    key=f"details_question_{selected_listing['id']}",
                    use_container_width=True
                ):
                    update_state_and_rerun(question_listing_id=selected_listing["id"])

            with col_btn3:
                if st.button("← Back to Listings", key="buyer_details_back_btn", use_container_width=True):
                    navigate_to("browse_listings", booking_listing_id=None)

            # -- Booking Section -- 
            if st.session_state["booking_listing_id"] == selected_listing["id"]:
                with st.container(border=True):
                    st.markdown("### Appointment Form")

                    appointment_name = st.text_input(
                        "Full Name",
                        value=st.session_state["user"]["full_name"],
                        key=f"appointment_name_{selected_listing['id']}"
                    )

                    appointment_email = st.text_input(
                        "Email",
                        value=st.session_state["user"]["email"],
                        key=f"appointment_email_{selected_listing['id']}"
                    )

                    appointment_phone = st.text_input(
                        "Phone Number",
                        key=f"appointment_phone_{selected_listing['id']}"
                    )

                    appointment_type = st.selectbox(
                        "Appointment Type",
                        [
                            "Select Type",
                            "Property Walkthrough",
                            "Initial Consultation",
                            "Offer Discussion"
                        ],
                        key=f"appointment_type_{selected_listing['id']}"
                    )

                    appointment_date = st.date_input(
                        "Preferred Appointment Date",
                        key=f"appointment_date_{selected_listing['id']}"
                    )

                    appointment_time = st.time_input("Preferred Appointment Time", key = f"appointment_time_{selected_listing['id']}"
                    )

                    # -- Show in 12-hour format for the buyer -- 
                    st.write("Selected Time:", appointment_time.strftime("%I:%M %p"))
                    st.caption("Appointments must be between 8:00 AM and 5:00 PM.")

                    appointment_message = st.text_area(
                        "Notes (Optional)",
                        placeholder="Add any details or preferences here",
                        key=f"appointment_message_{selected_listing['id']}"
                    )

                    col_submit, col_cancel = st.columns(2)

                    with col_submit:
                        btn_submit_appointment = st.button(
                            "Submit Appointment",
                            key=f"submit_appointment_{selected_listing['id']}",
                            type="primary",
                            use_container_width=True
                        )

                    with col_cancel:
                        btn_cancel_appointment = st.button(
                            "← Cancel",
                            key=f"cancel_appointment_{selected_listing['id']}",
                            use_container_width=True
                        )

                    if btn_cancel_appointment:
                        update_state_and_rerun(booking_listing_id=None)

                    if btn_submit_appointment:
                        appointment_name = appointment_name.strip()
                        appointment_email = normalize_email(appointment_email)
                        appointment_phone = normalize_phone(appointment_phone)
                        appointment_message = appointment_message.strip()
                        appointment_errors = []

                        if not appointment_name or not appointment_email or not appointment_phone:
                            appointment_errors.append("Please fill in all required fields.")

                        if not is_valid_phone(appointment_phone):
                            appointment_errors.append("Enter a valid 10-digit phone number.")

                        if not is_valid_email(appointment_email):
                            appointment_errors.append("Enter a valid email address.")

                        if appointment_type == "Select Type":
                            appointment_errors.append("Please select an appointment type.")

                        if appointment_time < dt_time(8, 0) or appointment_time > dt_time(17, 0):
                            appointment_errors.append("Appointments must be between 8:00 AM and 5:00 PM.")

                        if appointment_errors:
                            for appointment_error in appointment_errors:
                                st.error(appointment_error)
                        else:
                            with st.spinner("Submitting appointment..."):
                                time.sleep(0.5)

                                new_booking = {
                                    "id": str(uuid.uuid4()),
                                    "listing_id": selected_listing["id"],
                                    "property_title": selected_listing["title"],
                                    "agent_id": selected_listing["agent_id"],
                                    "buyer_id": st.session_state["user"]["id"],
                                    "buyer_name": appointment_name,
                                    "buyer_email": appointment_email,
                                    "buyer_phone": appointment_phone,
                                    "appointment_type": appointment_type,
                                    "appointment_date": str(appointment_date),
                                    "appointment_time": str(appointment_time),
                                    "message": appointment_message,
                                    "status": "Pending",
                                    "created_at": str(datetime.now())
                                }

                                bookings.append(new_booking)

                                saved = save_json_list(json_file_bookings, bookings)

                            if saved:
                                st.success("Appointment submitted successfully!")
                                update_state_and_rerun(booking_listing_id=None)

            # -- Question Section -- 
            if st.session_state["question_listing_id"] == selected_listing["id"]:
                with st.container(border=True):
                    st.markdown("### Question Form")

                    question_name = st.text_input(
                        "Full Name",
                        value=st.session_state["user"]["full_name"],
                        key=f"question_name_{selected_listing['id']}"
                    )

                    question_email = st.text_input(
                        "Email",
                        value=st.session_state["user"]["email"],
                        key=f"question_email_{selected_listing['id']}"
                    )

                    question_phone = st.text_input(
                        "Phone Number",
                        key=f"question_phone_{selected_listing['id']}"
                    )

                    question_subject = st.selectbox(
                        "Subject",
                        [
                            "Select Subject",
                            "Property Availability",
                            "Schedule a Tour",
                            "Pricing Information",
                            "Financing Questions",
                            "Property Details",
                            "Make an Offer",
                            "Other"
                        ],
                        key=f"question_subject_{selected_listing['id']}"
                    )

                    question_message = st.text_area(
                        "Question",
                        placeholder="Type your question here",
                        key=f"question_message_{selected_listing['id']}"
                    )

                    col_submit_q, col_cancel_q = st.columns(2)

                    with col_submit_q:
                        btn_submit_question = st.button(
                            "Submit Question",
                            key=f"submit_question_{selected_listing['id']}",
                            type="primary",
                            use_container_width=True
                        )

                    with col_cancel_q:
                        btn_cancel_question = st.button(
                            "← Cancel",
                            key=f"cancel_question_{selected_listing['id']}",
                            use_container_width=True
                        )

                    if btn_cancel_question:
                        update_state_and_rerun(question_listing_id=None)

                    if btn_submit_question:
                        question_name = question_name.strip()
                        question_email = normalize_email(question_email)
                        question_phone = normalize_phone(question_phone)
                        question_subject = question_subject.strip()
                        question_message = question_message.strip()
                        question_errors = []

                        if (
                            not question_name
                            or not question_email
                            or not question_phone
                            or question_subject == "Select Subject"
                            or not question_message
                        ):
                            question_errors.append("Please fill in all required fields.")

                        if not is_valid_phone(question_phone):
                            question_errors.append("Enter a valid 10-digit phone number.")

                        if not is_valid_email(question_email):
                            question_errors.append("Enter a valid email address.")

                        if question_errors:
                            for question_error in question_errors:
                                st.error(question_error)
                        else:
                            with st.spinner("Submitting question..."):
                                time.sleep(0.5)

                                new_inquiry = {
                                    "id": str(uuid.uuid4()),
                                    "listing_id": selected_listing["id"],
                                    "property_title": selected_listing["title"],
                                    "agent_id": selected_listing["agent_id"],
                                    "buyer_id": st.session_state["user"]["id"],
                                    "buyer_name": question_name,
                                    "buyer_email": question_email,
                                    "buyer_phone": question_phone,
                                    "subject": question_subject,
                                    "message": question_message,
                                    "status": "New",
                                    "created_at": str(datetime.now())
                                }

                                inquiries.append(new_inquiry)

                                saved = save_json_list(json_file_inquiries, inquiries)

                            if saved:
                                st.success("Question submitted successfully!")
                                update_state_and_rerun(question_listing_id=None)
    
    # -- Booking & Inquiries Page --
    elif st.session_state["page"] == "my_inquiries":
        st.markdown("# My Bookings & Inquiries")
        st.divider()

        tab_bookings, tab_inquiries = st.tabs(["My Bookings", "My Inquiries"])

        # -- Booking Tab --
        with tab_bookings:
            my_bookings = []
            for booking in bookings:
                if booking["buyer_id"] == st.session_state["user"]["id"]:
                    my_bookings.append(booking)

            st.markdown(f"### My Bookings")
            st.markdown(f"**Total Bookings:** {len(my_bookings)}")
            st.divider()

            if not my_bookings:
                st.info("You have not made any bookings yet.")
            else:
                for booking in my_bookings:
                    with st.container(border=True):
                        col_left, col_right = st.columns([3, 1])

                        with col_left:
                            st.markdown(f"### {booking['property_title']}")
                            st.markdown(f"**Appointment Type:** {booking['appointment_type']}")
                            st.markdown(f"**Date:** {booking['appointment_date']}")
                            st.markdown(f"**Time:** {booking['appointment_time']}")

                        with col_right:
                            st.markdown(f"### {booking['status']}")

                        if booking["message"]:
                            st.markdown(f"**Notes:** {booking['message']}")
                        else:
                            st.markdown("**Notes:** No additional notes provided.")

                        st.divider()

                        col1, col2 = st.columns(2)

                        with col1:
                            if st.button(
                                "Update Booking",
                                key=make_key("buyer_booking", booking["id"], "edit"),
                                use_container_width=True
                            ):
                                update_state_and_rerun(edit_booking_id=booking["id"])

                        with col2:
                            if st.button(
                                "Delete Booking",
                                key=make_key("buyer_booking", booking["id"], "delete"),
                                use_container_width=True
                            ):
                                bookings.remove(booking)

                                if save_json_list(json_file_bookings, bookings):
                                    st.success("Booking deleted successfully!")
                                    queue_rerun()

                        if st.session_state["edit_booking_id"] == booking["id"]:
                            with st.container(border=True):
                                st.markdown("### Update Booking")

                                updated_type = st.selectbox(
                                    "Appointment Type",
                                    [
                                        "Property Walkthrough",
                                        "Initial Consultation",
                                        "Offer Discussion"
                                    ],
                                    index=[
                                        "Property Walkthrough",
                                        "Initial Consultation",
                                        "Offer Discussion"
                                    ].index(booking["appointment_type"]) if booking["appointment_type"] in [
                                        "Property Walkthrough",
                                        "Initial Consultation",
                                        "Offer Discussion"
                                    ] else 0,
                                    key=make_key("buyer_booking", booking["id"], "updated_type")
                                )

                                updated_date = st.date_input(
                                    "Preferred Appointment Date",
                                    value=parse_date_safe(booking.get("appointment_date"), datetime.now().date()),
                                    key=make_key("buyer_booking", booking["id"], "updated_date")
                                )

                                updated_time = st.time_input(
                                    "Preferred Appointment Time",
                                    value=parse_time_safe(booking.get("appointment_time"), dt_time(9, 0)),
                                    key=make_key("buyer_booking", booking["id"], "updated_time")
                                )

                                st.markdown(
                                    f"**Selected Time:** {updated_time.strftime('%I:%M %p')}"
                                )
                                st.caption("Appointments must be between 8:00 AM and 5:00 PM.")

                                updated_message = st.text_area(
                                    "Notes",
                                    value=booking["message"],
                                    key=make_key("buyer_booking", booking["id"], "updated_message")
                                )

                                col_save, col_cancel = st.columns(2)

                                with col_save:
                                    if st.button(
                                        "Save Changes",
                                        key=make_key("buyer_booking", booking["id"], "save"),
                                        type="primary",
                                        use_container_width=True
                                    ):
                                        if updated_time < dt_time(8, 0) or updated_time > dt_time(17, 0):
                                            st.error("Appointments must be between 8:00 AM and 5:00 PM.")
                                        else:
                                            booking["appointment_type"] = updated_type
                                            booking["appointment_date"] = str(updated_date)
                                            booking["appointment_time"] = str(updated_time)
                                            booking["message"] = updated_message.strip()

                                            if save_json_list(json_file_bookings, bookings):
                                                st.success("Booking updated successfully!")
                                                update_state_and_rerun(edit_booking_id=None)

                                with col_cancel:
                                    if st.button(
                                        "← Cancel",
                                        key=make_key("buyer_booking", booking["id"], "cancel"),
                                        use_container_width=True
                                    ):
                                        update_state_and_rerun(edit_booking_id=None)
        # -- Inquiries Tab --
        with tab_inquiries:
            my_inquiries = []
            for inquiry in inquiries:
                if inquiry["buyer_id"] == st.session_state["user"]["id"]:
                    my_inquiries.append(inquiry)

            st.markdown("### My Inquiries")
            st.markdown(f"**Total Inquiries:** {len(my_inquiries)}")
            st.divider()

            if not my_inquiries:
                st.info("You have not submitted any inquiries yet.")
            else:
                for inquiry in my_inquiries:
                    with st.container(border=True):
                        col_left, col_right = st.columns([3, 1])

                        with col_left:
                            st.markdown(f"### {inquiry['property_title']}")
                            st.markdown(f"**Subject:** {inquiry['subject']}")
                            st.markdown(f"**Question:** {inquiry['message']}")

                        with col_right:
                            st.markdown(f"### {inquiry['status']}")

                        st.markdown(f"**Submitted:** {inquiry['created_at']}")

                        # --- Agent response section ---
                        if inquiry.get("response") and inquiry["response"].strip():
                            st.markdown("### Agent Response")
                            st.markdown(inquiry["response"])

                            if inquiry.get("response_at") and str(inquiry["response_at"]).strip():
                                st.markdown(f"**Responded:** {inquiry['response_at']}")
                        else:
                            st.markdown("### Agent Response")
                            st.markdown("*No response yet.*")

                        st.divider()

                        col1, col2 = st.columns(2)

                        with col1:
                            if st.button(
                                "Update Inquiry",
                                key=make_key("buyer_inquiry", inquiry["id"], "edit"),
                                use_container_width=True
                            ):
                                update_state_and_rerun(edit_inquiry_id=inquiry["id"])

                        with col2:
                            if st.button(
                                "Delete Inquiry",
                                key=make_key("buyer_inquiry", inquiry["id"], "delete"),
                                use_container_width=True
                            ):
                                inquiries.remove(inquiry)

                                if save_json_list(json_file_inquiries, inquiries):
                                    st.success("Inquiry deleted successfully!")
                                    queue_rerun()

                        if st.session_state["edit_inquiry_id"] == inquiry["id"]:
                            with st.container(border=True):
                                st.markdown("### Update Inquiry")

                                updated_subject = st.selectbox(
                                    "Subject",
                                    [
                                        "Property Availability",
                                        "Schedule a Tour",
                                        "Pricing Information",
                                        "Financing Questions",
                                        "Property Details",
                                        "Make an Offer",
                                        "Other"
                                    ],
                                    index=[
                                        "Property Availability",
                                        "Schedule a Tour",
                                        "Pricing Information",
                                        "Financing Questions",
                                        "Property Details",
                                        "Make an Offer",
                                        "Other"
                                    ].index(inquiry["subject"]) if inquiry["subject"] in [
                                        "Property Availability",
                                        "Schedule a Tour",
                                        "Pricing Information",
                                        "Financing Questions",
                                        "Property Details",
                                        "Make an Offer",
                                        "Other"
                                    ] else 0,
                                    key=make_key("buyer_inquiry", inquiry["id"], "subject")
                                )

                                updated_question = st.text_area(
                                    "Question",
                                    value=inquiry["message"],
                                    key=make_key("buyer_inquiry", inquiry["id"], "question")
                                )

                                col_save, col_cancel = st.columns(2)

                                with col_save:
                                    if st.button(
                                        "Save Changes",
                                        key=make_key("buyer_inquiry", inquiry["id"], "save"),
                                        type="primary",
                                        use_container_width=True
                                    ):
                                        if not updated_question.strip():
                                            st.error("Question cannot be empty.")
                                        else:
                                            inquiry["subject"] = updated_subject
                                            inquiry["message"] = updated_question.strip()

                                            if save_json_list(json_file_inquiries, inquiries):
                                                st.success("Inquiry updated successfully!")
                                                update_state_and_rerun(edit_inquiry_id=None)

                                with col_cancel:
                                    if st.button(
                                        "← Cancel",
                                        key=make_key("buyer_inquiry", inquiry["id"], "cancel"),
                                        use_container_width=True
                                    ):
                                        update_state_and_rerun(edit_inquiry_id=None)
                            
    # -- Sidebar for navigating pages and logging out for buyer -- 
    with st.sidebar:
        st.markdown("# **Navigator**")

        if st.button("🏠 Dashboard", key="buyer_nav_dashboard_btn", type="primary", use_container_width=True):
            navigate_to("home")

        if st.button("🔍 Browse Listings", key="buyer_nav_browse_btn", type="primary", use_container_width=True):
            navigate_to("browse_listings")

        if st.button("📅 My Bookings & Inquiries", key="buyer_nav_requests_btn", type="primary", use_container_width=True):
            navigate_to("my_inquiries")
                
        st.write(f"Logged in as: {st.session_state['user']['email']}")
        st.write(f"Role: {st.session_state['user']['role']}")

        if st.button("🚪 Log Out", key="buyer_nav_logout_btn", type="primary", use_container_width=True):
            st.success("Logout Succesful")
            time.sleep(0.5)
            update_state_and_rerun(**reset_state_for_logout())

    flush_rerun()

# -- Runs the main page best on user role and if not logged in displays login/registration page -- 
if (
    st.session_state["logged_in"]
    and st.session_state["user"] is not None
    and isinstance(st.session_state["user"], dict)
):
    if st.session_state["user"]["role"] == "Agent":
        show_main_app_agent()
    elif st.session_state["user"]["role"] == "Buyer":
        show_main_app_buyer()
else:
    show_login_page()