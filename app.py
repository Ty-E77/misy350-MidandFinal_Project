# -- Importing necessary packages --
# breadcrumb
import streamlit as st
import json
from pathlib import Path
from datetime import datetime, time as dt_time
import uuid
import time

# -- Setting page configuration --
st.set_page_config(page_title = "Real Estate Finder", 
                   page_icon = "",
                   layout = "centered",
                   initial_sidebar_state = "collapsed")


# -- Loading all json files -- 
json_file_properties = Path("properties.json")
json_file_users = Path("users.json")
json_file_inquiries = Path("inquiry.json")
json_file_bookings = Path("bookings.json")

properties = []
users = []
inquiries = []
bookings = [] 

if json_file_properties.exists():
    with open(json_file_properties, "r") as f:
        properties = json.load(f)

if json_file_users.exists():
    with open(json_file_users, "r") as f:
        users = json.load(f)

if json_file_inquiries.exists():
    with open(json_file_inquiries, "r") as f:
        inquiries = json.load(f)

if json_file_bookings.exists():
    with open(json_file_bookings, "r") as f:
        bookings = json.load(f)

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

# -- Creating registration & login page -- 
def show_login_page():
    st.markdown("# Real Estate Finder")
    st.caption("Browse listings, book appointments, and connect with agents.")
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
                use_container_width=True,
                type="primary"
            )

            if btn_login:
                if not email_login or not password_login:
                    st.warning("Please enter your email and password.")
                    st.stop()

                with st.spinner("Verifying credentials..."):
                    time.sleep(1)

                login_check = None
                email_login = email_login.strip().lower()

                for user in users:
                    if user["email"] == email_login and user["password"] == password_login:
                        login_check = user
                        break

                if login_check:
                    st.session_state["logged_in"] = True
                    st.session_state["user"] = login_check
                    st.session_state["page"] = "home"
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

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
                use_container_width=True,
                type="primary"
            )

            if btn_create:
                with st.spinner("Creating account..."):
                    time.sleep(1)

                new_email = email.strip().lower()
                existing_user = None

                for user in users:
                    if user["email"].strip().lower() == new_email:
                        existing_user = user
                        break

                if existing_user is not None:
                    st.error("An account with this email already exists.")
                    st.stop()

                if not full_name or not new_email or not password:
                    st.error("Please fill in all required fields.")
                    st.stop()

                users.append({
                    "id": str(uuid.uuid4()),
                    "email": new_email,
                    "full_name": full_name.strip(),
                    "password": password,
                    "role": role,
                    "registered_at": str(datetime.now())
                })

                with json_file_users.open("w", encoding="utf-8") as f:
                    json.dump(users, f, indent=4)

                st.success("Account created successfully! You can now log in.")

# -- Defining application for agent --                                 
def show_main_app_agent():
    # -- Dashboard Page --
    if st.session_state["page"] == "home":
        st.markdown(f"## Agent Dashboard - {st.session_state['user']['full_name']}")
        st.caption("Manage listings, review buyer bookings, and respond to inquiries.")
        st.divider()

        # Calculate stats
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

        # Stat cards
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

        # Quick actions
        st.markdown("### Quick Actions")

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            if st.button("View My Listings", type="primary", use_container_width=True):
                st.session_state["page"] = "properties_listings"
                st.rerun()

        with col_b:
            if st.button("Add New Listing", use_container_width=True):
                st.session_state["page"] = "add_listings"
                st.rerun()

        with col_c:
            if st.button("View Buyer Requests", use_container_width=True):
                st.session_state["page"] = "buyer_inquiries"
                st.rerun()

        st.divider()

        # Recent activity
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
                            key=f"manage_listing_btn_{listing['id']}",
                            type="primary",
                            use_container_width=True
                        ):
                            st.session_state["selected_agent_listing_id"] = listing["id"]
                            st.session_state["page"] = "manage_listing"
                            st.rerun()

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
                            key=f"view_other_listing_btn_{listing['id']}",
                            type="primary",
                            use_container_width=True
                        ):
                            st.session_state["selected_other_listing_id"] = listing["id"]
                            st.session_state["page"] = "view_other_listing_details"
                            st.rerun()

    # -- Manage Listings Page --
    elif st.session_state["page"] == "manage_listing":
        selected_listing = None

        for property_item in properties:
            if property_item["id"] == st.session_state["selected_agent_listing_id"]:
                selected_listing = property_item
                break

        if selected_listing is None:
            st.error("Listing not found.")
        else:
            st.markdown("## Manage Listing")
            st.divider()

            # Summary Section
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

            # Facts Section
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

            # Description
            with st.container(border=True):
                st.markdown("### Description")
                st.markdown(selected_listing["description"])

            # Contact
            with st.container(border=True):
                st.markdown("### Contact Information")
                st.markdown(f"**Name:** {selected_listing['contact_name']}")
                st.markdown(f"**Email:** {selected_listing['contact_email']}")
                st.markdown(f"**Phone:** {selected_listing['contact_phone']}")

            # Action buttons
            col_btn1, col_btn2, col_btn3 = st.columns(3)

            with col_btn1:
                if st.button(
                    "Update Listing",
                    key=f"edit_listing_{selected_listing['id']}",
                    type="primary",
                    use_container_width=True
                ):
                    st.session_state["page"] = "edit_listing"
                    st.rerun()

            with col_btn2:
                if st.button(
                    "Delete Listing",
                    key=f"delete_listing_{selected_listing['id']}",
                    use_container_width=True
                ):
                    properties.remove(selected_listing)
                    with json_file_properties.open("w", encoding="utf-8") as f:
                        json.dump(properties, f, indent=4)

                    st.success("Listing deleted successfully!")
                    time.sleep(2)
                    st.session_state["selected_agent_listing_id"] = None
                    st.session_state["page"] = "properties_listings"
                    st.rerun()

            with col_btn3:
                if st.button(
                    "Back to My Listings",
                    key="back_to_my_listings",
                    use_container_width=True
                ):
                    st.session_state["page"] = "properties_listings"
                    st.rerun()

    # -- Edit Listing Page -- 
    elif st.session_state["page"] == "edit_listing":
        selected_listing = None

        for property_item in properties:
            if property_item["id"] == st.session_state["selected_agent_listing_id"]:
                selected_listing = property_item
                break

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
                    contact_email = contact_email.strip().lower()
                    contact_phone = contact_phone.strip()
                    address = address.strip()
                    city = city.strip()
                    state = state.strip()

                    if not title or not address or not city or not state or not contact_name or not contact_email or not contact_phone:
                        st.error("Please fill in all required fields.")
                        st.stop()

                    if not contact_phone.isdigit() or len(contact_phone) != 10:
                        st.error("Enter a valid 10-digit phone number.")
                        st.stop()

                    if "@" not in contact_email or "." not in contact_email:
                        st.error("Enter a valid email address.")
                        st.stop()

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

                    with json_file_properties.open("w", encoding="utf-8") as f:
                        json.dump(properties, f, indent=4)

                    st.success("Listing updated successfully!")
                    time.sleep(2)
                    st.session_state["page"] = "manage_listing"
                    st.rerun()

            with col_cancel:
                if st.button(
                    "Cancel",
                    key=f"cancel_edit_listing_{selected_listing['id']}",
                    use_container_width=True
                ):
                    st.session_state["page"] = "manage_listing"
                    st.rerun()
    
    # -- View Other Agents Listings
    elif st.session_state["page"] == "view_other_listing_details":
        selected_listing = None

        for property_item in properties:
            if property_item["id"] == st.session_state["selected_other_listing_id"]:
                selected_listing = property_item
                break

        if selected_listing is None:
            st.error("Listing not found.")
        else:
            st.markdown("## View Listing Details")
            st.divider()

            # Summary Section
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

            # Facts Section
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

            # Description
            with st.container(border=True):
                st.markdown("### Description")
                st.markdown(selected_listing["description"])

            # Contact Info
            with st.container(border=True):
                st.markdown("### Contact Information")
                st.markdown(f"**Name:** {selected_listing['contact_name']}")
                st.markdown(f"**Email:** {selected_listing['contact_email']}")
                st.markdown(f"**Phone:** {selected_listing['contact_phone']}")

            if st.button(
                "Back to Other Listings",
                key="back_to_other_agent_listings",
                use_container_width=True
            ):
                st.session_state["page"] = "properties_listings"
                st.session_state["selected_other_listing_id"] = None
                st.rerun()

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
                type="primary",
                use_container_width=True
            )

        with col_btn2:
            btn_cancel_listing = st.button(
                "Cancel",
                use_container_width=True
            )

        if btn_cancel_listing:
            st.session_state["page"] = "properties_listings"
            st.rerun()

        if btn_add_listing:
            with st.spinner("Listing is being created..."):
                time.sleep(2)

                title = title.strip()
                description = description.strip()
                contact_name = contact_name.strip()
                contact_email = contact_email.strip().lower()
                address = address.strip()
                city = city.strip()
                state = state.strip()
                contact_phone = contact_phone.strip()

            if not title or not address or not city or not state or not contact_name or not contact_email or not contact_phone:
                st.error("Please fill in all required fields.")
                st.stop()

            if not contact_phone.isdigit() or len(contact_phone) != 10:
                st.error("Enter a valid 10-digit phone number.")
                st.stop()

            if "@" not in contact_email or "." not in contact_email:
                st.error("Enter a valid email address.")
                st.stop()

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
                st.error("A listing with this title and address already exists.")
                st.stop()

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

            with json_file_properties.open("w", encoding="utf-8") as f:
                json.dump(properties, f, indent=4)

            st.success("Listing added successfully!")
            st.balloons()
            time.sleep(2)
            st.session_state["page"] = "properties_listings"
            st.rerun()

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
                                key=f"confirm_booking_{booking['id']}",
                                type="primary",
                                use_container_width=True
                            ):
                                booking["status"] = "Confirmed"
                                with json_file_bookings.open("w", encoding="utf-8") as f:
                                    json.dump(bookings, f, indent=4)
                                st.success("Appointment confirmed successfully!")
                                st.rerun()

                        with col2:
                            if st.button(
                                "Decline Appointment",
                                key=f"decline_booking_{booking['id']}",
                                use_container_width=True
                            ):
                                booking["status"] = "Declined"
                                with json_file_bookings.open("w", encoding="utf-8") as f:
                                    json.dump(bookings, f, indent=4)
                                st.success("Appointment declined.")
                                st.rerun()

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
                            key=f"edit_agent_inquiry_{inquiry['id']}",
                            use_container_width=True
                        ):
                            st.session_state["edit_agent_inquiry_id"] = inquiry["id"]
                            st.rerun()

                        if st.session_state["edit_agent_inquiry_id"] == inquiry["id"]:
                            with st.container(border=True):
                                st.markdown("### Update Inquiry")

                                updated_status = st.selectbox(
                                    "Status",
                                    ["New", "In Progress", "Answered"],
                                    index=["New", "In Progress", "Answered"].index(inquiry["status"])
                                    if inquiry["status"] in ["New", "In Progress", "Answered"] else 0,
                                    key=f"agent_inquiry_status_{inquiry['id']}"
                                )

                                updated_response = st.text_area(
                                    "Response to Buyer",
                                    value=inquiry.get("response", ""),
                                    placeholder="Type your answer here",
                                    key=f"agent_inquiry_response_{inquiry['id']}"
                                )

                                col_save, col_cancel = st.columns(2)

                                with col_save:
                                    if st.button(
                                        "Save Response",
                                        key=f"save_agent_inquiry_{inquiry['id']}",
                                        type="primary",
                                        use_container_width=True
                                    ):
                                        if updated_status == "Answered" and not updated_response.strip():
                                            st.error("Please enter a response before marking as Answered.")
                                            st.stop()

                                        inquiry["status"] = updated_status
                                        inquiry["response"] = updated_response.strip()
                                        inquiry["response_at"] = str(datetime.now()) if updated_response.strip() else ""

                                        with json_file_inquiries.open("w", encoding="utf-8") as f:
                                            json.dump(inquiries, f, indent=4)

                                        st.success("Inquiry updated successfully!")
                                        st.session_state["edit_agent_inquiry_id"] = None
                                        st.rerun()

                                with col_cancel:
                                    if st.button(
                                        "Cancel",
                                        key=f"cancel_agent_inquiry_{inquiry['id']}",
                                        use_container_width=True
                                    ):
                                        st.session_state["edit_agent_inquiry_id"] = None
                                        st.rerun()
    
    # -- Sidebar for navigating pages and logging out for agent -- 
    with st.sidebar:
        st.markdown("# **Navigator**")
        if st.button("Dashboard", key = "agent_dashboard_btn", type = "primary", use_container_width = True):
            st.session_state["page"] = "home"
            st.rerun()

        if st.button("View/Manage Property Listings", key = "properties_listings", type = "primary", use_container_width = True):
            st.session_state["page"] = "properties_listings"
            st.rerun()
        
        if st.button("Add Property Listings", key = "add_listings", type = "primary", use_container_width = True):
            st.session_state["page"] = "add_listings"
            st.rerun()
        
        if st.button("Buyer Bookings & Inquiries", key = "buyer_inquiries", type = "primary", use_container_width = True):
            st.session_state["page"] = "buyer_inquiries"
            st.rerun()
        
        st.write(f"Logged in as: {st.session_state['user']['email']}")
        st.write(f"Role: {st.session_state['user']['role']}")

        if st.button("Log Out", type="primary", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["user"] = None
            st.session_state["page"] = "home"
            st.session_state["selected_agent_listing_id"] = None
            st.session_state["selected_other_listing_id"] = None
            st.rerun()


# -- Defining application for buyer -- 
def show_main_app_buyer():
    # -- Dashboard Page --
    if st.session_state["page"] == "home":
        st.markdown(f"## Buyer Dashboard - {st.session_state['user']['full_name']}")
        st.caption("Browse listings, book appointments, and manage your inquiries.")
        st.divider()

        # Calculate stats
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

        # Stat cards
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

        # Quick actions
        st.markdown("### Quick Actions")

        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("Browse Listings", type="primary", use_container_width=True):
                st.session_state["page"] = "browse_listings"
                st.rerun()

        with col_b:
            if st.button("View My Bookings & Inquiries", use_container_width=True):
                st.session_state["page"] = "my_inquiries"
                st.rerun()

        st.divider()

        # Recent activity
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
                        key=f"view_listing_btn_{listing['id']}",
                        type="primary",
                        use_container_width=True
                    ):
                        st.session_state["selected_listing_id"] = listing["id"]
                        st.session_state["page"] = "view_listing_details"
                        st.rerun()

    # -- Shows listing Details when a user clicks the listing -- 
    elif st.session_state["page"] == "view_listing_details":
        selected_listing = None

        for property_item in properties:
            if property_item["id"] == st.session_state["selected_listing_id"]:
                selected_listing = property_item
                break

        if selected_listing is None:
            st.error("Listing not found.")
        else:
            st.markdown("## View Listing Details")
            st.divider()

            # -- Summary Section
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

            # -- Facts Section -- 
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

            # -- Description section --
            with st.container(border=True):
                st.markdown("### Description")
                st.write(selected_listing["description"])

            # -- Contact section --
            with st.container(border=True):
                st.markdown("### Contact Information")
                st.write(f"**Name:** {selected_listing['contact_name']}")
                st.write(f"**Email:** {selected_listing['contact_email']}")
                st.write(f"**Phone:** {selected_listing['contact_phone']}")

            # -- Buttons --
            col_btn1, col_btn2, col_btn3 = st.columns(3)

            with col_btn1:
                if st.button(
                    "Book an Appointment",
                    key=f"details_book_{selected_listing['id']}",
                    type="primary",
                    use_container_width=True
                ):
                    st.session_state["booking_listing_id"] = selected_listing["id"]
                    st.rerun()

            with col_btn2:
                if st.button(
                    "Ask a Question(s)",
                    key=f"details_question_{selected_listing['id']}",
                    use_container_width=True
                ):
                    st.session_state["question_listing_id"] = selected_listing["id"]
                    st.rerun()

            with col_btn3:
                if st.button("Back to Listings", use_container_width=True):
                    st.session_state["page"] = "browse_listings"
                    st.session_state["booking_listing_id"] = None
                    st.rerun()

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
                            "Cancel",
                            key=f"cancel_appointment_{selected_listing['id']}",
                            use_container_width=True
                        )

                    if btn_cancel_appointment:
                        st.session_state["booking_listing_id"] = None
                        st.rerun()

                    if btn_submit_appointment:
                        appointment_name = appointment_name.strip()
                        appointment_email = appointment_email.strip().lower()
                        appointment_phone = appointment_phone.strip()
                        appointment_message = appointment_message.strip()

                        if not appointment_name or not appointment_email or not appointment_phone:
                            st.error("Please fill in all required fields.")
                            st.stop()

                        if not appointment_phone.isdigit() or len(appointment_phone) != 10:
                            st.error("Enter a valid 10-digit phone number.")
                            st.stop()

                        if "@" not in appointment_email or "." not in appointment_email:
                            st.error("Enter a valid email address.")
                            st.stop()

                        if appointment_type == "Select Type":
                            st.error("Please select an appointment type.")
                            st.stop()

                        if appointment_time < dt_time(8, 0) or appointment_time > dt_time(17, 0):
                            st.error("Appointments must be between 8:00 AM and 5:00 PM.")
                            st.stop()

                        with st.spinner("Submitting appointment..."):
                            time.sleep(2)

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

                            with json_file_bookings.open("w", encoding="utf-8") as f:
                                json.dump(bookings, f, indent=4)

                        st.success("Appointment submitted successfully!")
                        time.sleep(4)
                        st.session_state["booking_listing_id"] = None
                        st.rerun()
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
                            "Cancel",
                            key=f"cancel_question_{selected_listing['id']}",
                            use_container_width=True
                        )

                    if btn_cancel_question:
                        st.session_state["question_listing_id"] = None
                        st.rerun()

                    if btn_submit_question:
                        question_name = question_name.strip()
                        question_email = question_email.strip().lower()
                        question_phone = question_phone.strip()
                        question_subject = question_subject.strip()
                        question_message = question_message.strip()

                        if (
                            not question_name
                            or not question_email
                            or not question_phone
                            or question_subject == "Select Subject"
                            or not question_message
                        ):
                            st.error("Please fill in all required fields.")
                            st.stop()                        

                        if not question_phone.isdigit() or len(question_phone) != 10:
                            st.error("Enter a valid 10-digit phone number.")
                            st.stop()

                        if "@" not in question_email or "." not in question_email:
                            st.error("Enter a valid email address.")
                            st.stop()

                        with st.spinner("Submitting question..."):
                            time.sleep(2)

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

                            with json_file_inquiries.open("w", encoding="utf-8") as f:
                                json.dump(inquiries, f, indent=4)

                        st.success("Question submitted successfully!")
                        time.sleep(2)
                        st.session_state["question_listing_id"] = None
                        st.rerun()
    
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
                                key=f"edit_booking_{booking['id']}",
                                use_container_width=True
                            ):
                                st.session_state["edit_booking_id"] = booking["id"]
                                st.rerun()

                        with col2:
                            if st.button(
                                "Delete Booking",
                                key=f"delete_booking_{booking['id']}",
                                use_container_width=True
                            ):
                                bookings.remove(booking)
                                with json_file_bookings.open("w", encoding="utf-8") as f:
                                    json.dump(bookings, f, indent=4)
                                st.success("Booking deleted successfully!")
                                st.rerun()

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
                                    key=f"updated_type_{booking['id']}"
                                )

                                updated_date = st.date_input(
                                    "Preferred Appointment Date",
                                    value=datetime.strptime(booking["appointment_date"], "%Y-%m-%d").date(),
                                    key=f"updated_date_{booking['id']}"
                                )

                                updated_time = st.time_input(
                                    "Preferred Appointment Time",
                                    value=datetime.strptime(booking["appointment_time"], "%H:%M:%S").time(),
                                    key=f"updated_time_{booking['id']}"
                                )

                                st.markdown(
                                    f"**Selected Time:** {updated_time.strftime('%I:%M %p')}"
                                )
                                st.caption("Appointments must be between 8:00 AM and 5:00 PM.")

                                updated_message = st.text_area(
                                    "Notes",
                                    value=booking["message"],
                                    key=f"updated_message_{booking['id']}"
                                )

                                col_save, col_cancel = st.columns(2)

                                with col_save:
                                    if st.button(
                                        "Save Changes",
                                        key=f"save_booking_{booking['id']}",
                                        type="primary",
                                        use_container_width=True
                                    ):
                                        if updated_time < dt_time(8, 0) or updated_time > dt_time(17, 0):
                                            st.error("Appointments must be between 8:00 AM and 5:00 PM.")
                                            st.stop()

                                        booking["appointment_type"] = updated_type
                                        booking["appointment_date"] = str(updated_date)
                                        booking["appointment_time"] = str(updated_time)
                                        booking["message"] = updated_message.strip()

                                        with json_file_bookings.open("w", encoding="utf-8") as f:
                                            json.dump(bookings, f, indent=4)

                                        st.success("Booking updated successfully!")
                                        st.session_state["edit_booking_id"] = None
                                        st.rerun()

                                with col_cancel:
                                    if st.button(
                                        "Cancel",
                                        key=f"cancel_edit_booking_{booking['id']}",
                                        use_container_width=True
                                    ):
                                        st.session_state["edit_booking_id"] = None
                                        st.rerun()
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
                                key=f"edit_inquiry_{inquiry['id']}",
                                use_container_width=True
                            ):
                                st.session_state["edit_inquiry_id"] = inquiry["id"]
                                st.rerun()

                        with col2:
                            if st.button(
                                "Delete Inquiry",
                                key=f"delete_inquiry_{inquiry['id']}",
                                use_container_width=True
                            ):
                                inquiries.remove(inquiry)
                                with json_file_inquiries.open("w", encoding="utf-8") as f:
                                    json.dump(inquiries, f, indent=4)
                                st.success("Inquiry deleted successfully!")
                                time.sleep(2)
                                st.rerun()

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
                                    key=f"updated_subject_{inquiry['id']}"
                                )

                                updated_question = st.text_area(
                                    "Question",
                                    value=inquiry["message"],
                                    key=f"updated_question_{inquiry['id']}"
                                )

                                col_save, col_cancel = st.columns(2)

                                with col_save:
                                    if st.button(
                                        "Save Changes",
                                        key=f"save_inquiry_{inquiry['id']}",
                                        type="primary",
                                        use_container_width=True
                                    ):
                                        if not updated_question.strip():
                                            st.error("Question cannot be empty.")
                                            st.stop()

                                        inquiry["subject"] = updated_subject
                                        inquiry["message"] = updated_question.strip()

                                        with json_file_inquiries.open("w", encoding="utf-8") as f:
                                            json.dump(inquiries, f, indent=4)

                                        st.success("Inquiry updated successfully!")
                                        time.sleep(2)
                                        st.session_state["edit_inquiry_id"] = None
                                        st.rerun()

                                with col_cancel:
                                    if st.button(
                                        "Cancel",
                                        key=f"cancel_edit_inquiry_{inquiry['id']}",
                                        use_container_width=True
                                    ):
                                        st.session_state["edit_inquiry_id"] = None
                                        st.rerun()
                            
    # -- Sidebar for navigating pages and logging out for buyer -- 
    with st.sidebar():
        if st.button("Dashboard", key = "buyer_dashboard_btn", type = "primary", use_container_width = True):
            st.session_state["page"] = "home"
            st.rerun()

        if st.button("Browse Listings", key = "browse_listings", type = "primary", use_container_width = True):
            st.session_state["page"] = "browse_listings"
            st.rerun()
                
        if st.button("My Bookings & Inquiries", key = "my_inquiries", type = "primary", use_container_width = True):
            st.session_state["page"] = "my_inquiries"
            st.rerun()
                
        st.write(f"Logged in as: {st.session_state['user']['email']}")
        st.write(f"Role: {st.session_state['user']['role']}")

        if st.button("Log Out", type="primary", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["user"] = None
            st.session_state["page"] = "home"
            st.session_state["booking_listing_id"] = None
            st.session_state["selected_listing_id"] = None
            st.rerun()

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