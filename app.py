# -- Importing necessary packages --
# breadcrumb
import streamlit as st
import json
from pathlib import Path
from datetime import datetime, time as dt_time
import uuid
import time
import re
import hashlib

from data import data_manager
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


# -- Data loading and validation are delegated to the data layer (data_manager) --
# Load collections via data_manager and apply simple normalization/defaults
users = data_manager.load_json_list(data_manager.json_file_users, "Users")
users = [user for user in users if data_manager.is_valid_user(user)]
for user in users:
    user.setdefault("full_name", "")
    user.setdefault("role", "")

properties = data_manager.load_json_list(data_manager.json_file_properties, "Properties")
properties = [listing for listing in properties if data_manager.is_valid_property(listing)]
for listing in properties:
    listing.setdefault("status", "Available")
    listing.setdefault("description", "")
    listing.setdefault("contact_name", "")
    listing.setdefault("contact_email", "")
    listing.setdefault("contact_phone", "")

inquiries = data_manager.load_json_list(data_manager.json_file_inquiries, "Inquiries")
inquiries = [inquiry for inquiry in inquiries if data_manager.is_valid_inquiry(inquiry)]
for inquiry in inquiries:
    inquiry.setdefault("response", "")
    inquiry.setdefault("response_at", "")
    inquiry.setdefault("status", "New")
    inquiry.setdefault("subject", "")
    inquiry.setdefault("message", "")

bookings = data_manager.load_json_list(data_manager.json_file_bookings, "Bookings")
bookings = [booking for booking in bookings if data_manager.is_valid_booking(booking)]
for booking in bookings:
    booking.setdefault("status", "Pending")
    booking.setdefault("message", "")


# Instantiate service and UI managers (data + ui modules)
from service import RealEstateService
from ui import RealEstateUI

service_manager = RealEstateService(data_manager, users, properties, inquiries, bookings)
ui = RealEstateUI(service_manager, data_manager)

# --  Functions for repetitive tasks --
# Use data_manager.save_json_list(...) and service_manager.hash_password(...) directly.
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


# Use service_manager.delete_record_with_rollback(...) and
# service_manager.update_record_with_rollback(...) directly where needed.


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


# Use service_manager.make_key/normalize_email/is_valid_email/normalize_phone/is_valid_phone
# directly instead of local implementations.


def show_data_warnings():
    if data_manager.warnings:
        with st.expander("Data file warnings"):
            for warning in data_manager.warnings:
                st.warning(warning)


# Use data_manager.parse_date_safe(...) and data_manager.parse_time_safe(...)
# directly where needed.


# Use service_manager.reset_state_for_logout() when resetting session state.


# Use service_manager.find_listing_by_id(listing_id) instead of this local helper.


# Call ui.render_listing_detail_sections(selected_listing) directly in call sites.


# Call ui.process_chat_message / ui.get_agent_chatbot_response / ui.get_buyer_chatbot_response
# / ui.show_chat_bot directly where needed.

# -- Creating registration & login page -- 
# Call ui.show_login_page() directly.

# -- Defining application for agent --                                 
# Call ui.show_main_app_agent() directly.

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
        ui.show_chat_bot("Buyer")
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
                        key=service_manager.make_key("buyer_listing", listing["id"], "view"),
                        type="primary",
                        use_container_width=True
                    ):
                        navigate_to("view_listing_details", selected_listing_id=listing["id"])

    # -- Shows listing Details when a user clicks the listing -- 
    elif st.session_state["page"] == "view_listing_details":
        selected_listing = service_manager.find_listing_by_id(st.session_state["selected_listing_id"])

        if selected_listing is None:
            st.error("Listing not found.")
        else:
            st.markdown("## View Listing Details")
            st.divider()
            ui.render_listing_detail_sections(selected_listing)

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
                        appointment_email = service_manager.normalize_email(appointment_email)
                        appointment_phone = service_manager.normalize_phone(appointment_phone)
                        appointment_message = appointment_message.strip()
                        appointment_errors = []

                        if not appointment_name or not appointment_email or not appointment_phone:
                            appointment_errors.append("Please fill in all required fields.")

                        if not service_manager.is_valid_phone(appointment_phone):
                            appointment_errors.append("Enter a valid 10-digit phone number.")
                        
                        if not service_manager.is_valid_email(appointment_email):
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

                                saved = data_manager.save_json_list(data_manager.json_file_bookings, bookings)
                                if not saved:
                                    bookings.pop()

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
                        question_email = service_manager.normalize_email(question_email)
                        question_phone = service_manager.normalize_phone(question_phone)
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

                        if not service_manager.is_valid_phone(question_phone):
                            question_errors.append("Enter a valid 10-digit phone number.")

                        if not service_manager.is_valid_email(question_email):
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

                                saved = data_manager.save_json_list(data_manager.json_file_inquiries, inquiries)
                                if not saved:
                                    inquiries.pop()

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
                                    key=service_manager.make_key("buyer_booking", booking["id"], "edit"),
                                    use_container_width=True
                                ):
                                    update_state_and_rerun(edit_booking_id=booking["id"])

                        with col2:
                            if st.button(
                                "Delete Booking",
                                key=service_manager.make_key("buyer_booking", booking["id"], "delete"),
                                use_container_width=True
                            ):
                                if service_manager.delete_record_with_rollback(bookings, booking, data_manager.json_file_bookings):
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
                                    key=service_manager.make_key("buyer_booking", booking["id"], "updated_type")
                                )

                                updated_date = st.date_input(
                                    "Preferred Appointment Date",
                                    value=data_manager.parse_date_safe(booking.get("appointment_date"), datetime.now().date()),
                                    key=service_manager.make_key("buyer_booking", booking["id"], "updated_date")
                                )

                                updated_time = st.time_input(
                                    "Preferred Appointment Time",
                                    value=data_manager.parse_time_safe(booking.get("appointment_time"), dt_time(9, 0)),
                                    key=service_manager.make_key("buyer_booking", booking["id"], "updated_time")
                                )

                                st.markdown(
                                    f"**Selected Time:** {updated_time.strftime('%I:%M %p')}"
                                )
                                st.caption("Appointments must be between 8:00 AM and 5:00 PM.")

                                updated_message = st.text_area(
                                    "Notes",
                                    value=booking["message"],
                                    key=service_manager.make_key("buyer_booking", booking["id"], "updated_message")
                                )

                                col_save, col_cancel = st.columns(2)

                                with col_save:
                                    if st.button(
                                        "Save Changes",
                                        key=service_manager.make_key("buyer_booking", booking["id"], "save"),
                                        type="primary",
                                        use_container_width=True
                                    ):
                                        if updated_time < dt_time(8, 0) or updated_time > dt_time(17, 0):
                                            st.error("Appointments must be between 8:00 AM and 5:00 PM.")
                                        else:
                                            updated_booking_values = {
                                                "appointment_type": updated_type,
                                                "appointment_date": str(updated_date),
                                                "appointment_time": str(updated_time),
                                                "message": updated_message.strip(),
                                            }

                                            if service_manager.update_record_with_rollback(booking, updated_booking_values, bookings, data_manager.json_file_bookings):
                                                st.success("Booking updated successfully!")
                                                update_state_and_rerun(edit_booking_id=None)

                                with col_cancel:
                                    if st.button(
                                        "← Cancel",
                                        key=service_manager.make_key("buyer_booking", booking["id"], "cancel"),
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
                                    key=service_manager.make_key("buyer_inquiry", inquiry["id"], "edit"),
                                    use_container_width=True
                                ):
                                    update_state_and_rerun(edit_inquiry_id=inquiry["id"])

                        with col2:
                            if st.button(
                                "Delete Inquiry",
                                key=service_manager.make_key("buyer_inquiry", inquiry["id"], "delete"),
                                use_container_width=True
                            ):
                                if service_manager.delete_record_with_rollback(inquiries, inquiry, data_manager.json_file_inquiries):
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
                                    key=service_manager.make_key("buyer_inquiry", inquiry["id"], "subject")
                                )

                                updated_question = st.text_area(
                                    "Question",
                                    value=inquiry["message"],
                                    key=service_manager.make_key("buyer_inquiry", inquiry["id"], "question")
                                )

                                col_save, col_cancel = st.columns(2)

                                with col_save:
                                    if st.button(
                                        "Save Changes",
                                        key=service_manager.make_key("buyer_inquiry", inquiry["id"], "save"),
                                        type="primary",
                                        use_container_width=True
                                    ):
                                        if not updated_question.strip():
                                            st.error("Question cannot be empty.")
                                        else:
                                            updated_inquiry_values = {
                                                "subject": updated_subject,
                                                "message": updated_question.strip(),
                                            }

                                            if service_manager.update_record_with_rollback(inquiry, updated_inquiry_values, inquiries, data_manager.json_file_inquiries):
                                                st.success("Inquiry updated successfully!")
                                                update_state_and_rerun(edit_inquiry_id=None)

                                with col_cancel:
                                    if st.button(
                                        "← Cancel",
                                        key=service_manager.make_key("buyer_inquiry", inquiry["id"], "cancel"),
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
            update_state_and_rerun(**service_manager.reset_state_for_logout())

    flush_rerun()

# -- Runs the main page best on user role and if not logged in displays login/registration page -- 
if (
    st.session_state["logged_in"]
    and st.session_state["user"] is not None
    and isinstance(st.session_state["user"], dict)
):
    if st.session_state["user"]["role"] == "Agent":
        ui.show_main_app_agent()
    elif st.session_state["user"]["role"] == "Buyer":
        show_main_app_buyer()
else:
    ui.show_login_page()