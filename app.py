# -- Importing necessary packages --
import streamlit as st
import json
from pathlib import Path
from datetime import datetime
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

# -- Creating registration & login page -- 
def show_login_page():
    tab1, tab2 = st.tabs(["Register", "Login"])

    with tab1:
        with st.container(border = True):
            st.header("Real Estate Finder")
            st.markdown("## New Account")
            email = st.text_input("Email", placeholder = "ex. 1234@gmail.com", key = "email_new")
            full_name = st.text_input("Full Name:", placeholder = "ex. John Doe", key = "full_name_new")
            password = st.text_input("Password", type = "password", key = "password_new")
            role = st.radio("Role", ["Agent", "Buyer"])
            btn_create = st.button("Create Account", use_container_width = True, disabled = False, type = "primary")

            if btn_create:
                with st.spinner("Creating account..."):
                    time.sleep(1)
                
                # -- Checking for duplicate email and making sure an account doesn't exist --
                new_email = email.strip().lower()
                existing_user = None
                for user in users:
                    if user["email"].strip().lower() == new_email:
                        existing_user = user
                        break

                if existing_user is not None:
                    st.error("An account with this email already exists.")
                    st.stop()
                elif not new_email or not password:
                    st.error("Email and password are required.")
                    st.stop()
                else:
                        users.append ( {
                        "id": str(uuid.uuid4()),
                        "email": new_email,
                        "full_name": full_name,
                        "password": password,
                        "role": role,
                        "registered_at": str(datetime.now())

        })
                with json_file_users.open("w", encoding = "utf-8") as f:
                            json.dump(users, f, indent = 6)

                st.success("Account created successfully!")
    with tab2:
        with st.container(border = True):
            st.header("Real Estate Finder")
            st.markdown("## Log In")
            email_login = st.text_input("Email", placeholder = "ex. 1234@gmail.com", key = "login_email")
            password_login = st.text_input("Password", type = "password", key = "login_password")

            btn_login = st.button("Log In", use_container_width = True, disabled = False, type = "primary")

            if btn_login:
                if (email_login == "") or (password_login == ""):
                    st.warning("Missing required information")
                    st.stop()
                else:
                    with st.spinner("Verifying credentials..."):
                        time.sleep(2)

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

# -- Defining application for agent --                                 
def show_main_app_agent():
    # -- Dashboard Page --
    if st.session_state["page"] == "home":
        st.markdown(f"## Agent Dashboard - {st.session_state['user']['full_name']}")

    # -- Properties Page --
    elif st.session_state["page"] == "properties_listings":
        st.markdown(f"## View Property Listings")
        

        tablist, taball = st.tabs(["My Property Listings", "All Property Listings"])

        with tablist:
            st.markdown("### My Listings")

            my_listings = []
            for listing in properties:
                if listing["agent_id"] == st.session_state["user"]["id"]:
                    my_listings.append(listing)

            col_listings, col_filters = st.columns([3, 1])

            with col_filters:
                st.markdown("#### Filter Listings")

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

            with col_listings:
                st.markdown(f"##### Total Listings: {len(filtered_my_listings)}")

                if not filtered_my_listings:
                    st.info("You have no listings matching these filters.")
                else:
                    for listing in filtered_my_listings:
                        with st.container(border=True):
                            st.markdown(f"### {listing['title']}")
                            st.write(f"**Address:** {listing['address']}, {listing['city']}, {listing['state']}")
                            st.write(f"**Price:** ${listing['price']:,}")
                            st.write(f"**Status:** {listing['status']}")

                            with st.expander("View More Details"):
                                st.write(f"**Bedrooms:** {listing['bedrooms']}")
                                st.write(f"**Bathrooms:** {listing['bathrooms']}")
                                st.write(f"**Square Footage:** {listing['property_sqft']}")
                                st.write(f"**Type:** {listing['property_type']}")
                                st.write(f"**Contact Name:** {listing['contact_name']}")
                                st.write(f"**Contact Email:** {listing['contact_email']}")
                                st.write(f"**Contact Phone:** {listing['contact_phone']}")

        with taball:
            st.markdown("### All Listings")
            
            col_listings, col_filters = st.columns([3, 1])

            with col_filters:
                st.markdown("#### Filter Listings")

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
                type_match = selected_type == "All" or listing["property_type"] == selected_type
                status_match = selected_status == "All" or listing["status"] == selected_status

                if type_match and status_match:
                    filtered_properties.append(listing)

            with col_listings:
                st.markdown(f"##### Total Listings: {len(filtered_properties)}")

                if not filtered_properties:
                    st.info("No listings match your filters.")
                else:
                    for listing in filtered_properties:
                        with st.container(border=True):
                            st.markdown(f"### {listing['title']}")
                            st.write(f"**Address:** {listing['address']}, {listing['city']}, {listing['state']}")
                            st.write(f"**Price:** ${listing['price']:,}")
                            st.write(f"**Status:** {listing['status']}")

                            with st.expander("View More Details"):
                                st.write(f"**Bedrooms:** {listing['bedrooms']}")
                                st.write(f"**Bathrooms:** {listing['bathrooms']}")
                                st.write(f"**Square Footage:** {listing['property_sqft']}")
                                st.write(f"**Type:** {listing['property_type']}")
                                st.write(f"**Contact Name:** {listing['contact_name']}")
                                st.write(f"**Contact Email:** {listing['contact_email']}")
                                st.write(f"**Contact Phone:** {listing['contact_phone']}")

    # -- Add Listings Page --
    elif st.session_state["page"] == "add_listings":
        st.markdown(f"## Add Listings")
        with st.container(border = True):
            st.markdown("#### Listing Details")
            title = st.text_input("Listing Title", placeholder = "ex... 5 Bedroom Perfect for a family")
            description = st.text_area("Description", placeholder = "brief description")
        
        with st.container(border = True):
            st.markdown("#### Contact Information")
                
            contact_name = st.text_input("Contact Name", placeholder = "John Doe")
            contact_email = st.text_input("Contact Email", placeholder = "123abc@gmail.com")
            contact_phone = st.text_input("Contact Phone Number")

        with st.container(border = True):
            st.markdown("#### Housing Information")
                
            address = st.text_input("Street Address", placeholder = "Enter street address here")
            city = st.text_input("City", placeholder = "Enter City")
            state = st.text_input("State", placeholder = "Enter State")
            price = st.number_input("Price", min_value=1)
            bedrooms = st.number_input("Bedrooms", min_value=0, step=1)
            bathrooms = st.number_input("Bathrooms", min_value=0, step=1)
            property_sqft = st.number_input("Property Square Footage", min_value=1, step=1)
            property_type = st.selectbox("Property Type", ["House", "Apartment", "Condo", "Townhouse"])
            status = st.selectbox("Status", ["Available", "Pending", "Sold"])

        btn_add_listing = st.button("Add Listing", type="primary", use_container_width=True)

        if btn_add_listing:
            with st.spinner("Listing is being created ..."):
                time.sleep(3)
            if not title or not address or not city or not state or price == 0 or not contact_name or not contact_email or not contact_phone:
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

                title = title.strip()
                description = description.strip()
                contact_name = contact_name.strip()
                contact_email = contact_email.strip().lower()
                address = address.strip()
                city = city.strip()
                state = state.strip()
                contact_phone = contact_phone.strip()

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
                json.dump(properties, f, indent = 4)

            
            st.success("Listing added successfully!")
            st.balloons()
            time.sleep(2)
            # st.session_state["page"] = "properties_listings"
            st.rerun()

    elif st.session_state["page"] == "buyer_inquiries":
        st.markdown(f"## Buyer Inquiries")
    


    # -- Sidebar for navigating pages and logging out for agent -- 
    with st.sidebar:
        st.markdown("# **Navigator**")
        if st.button("Dashboard", key = "agent_dashboard_btn", type = "primary", use_container_width = True):
            st.session_state["page"] = "home"
            st.rerun()

        if st.button("View Property Listings", key = "properties_listings", type = "primary", use_container_width = True):
            st.session_state["page"] = "properties_listings"
            st.rerun()
        
        if st.button("Add Property Listings", key = "add_listings", type = "primary", use_container_width = True):
            st.session_state["page"] = "add_listings"
            st.rerun()
        
        if st.button("Buyer Inquiries", key = "buyer_inquiries", type = "primary", use_container_width = True):
            st.session_state["page"] = "buyer_inquiries"
            st.rerun()
        
        st.write(f"Logged in as: {st.session_state['user']['email']}")
        st.write(f"Role: {st.session_state['user']['role']}")

        if st.button("Log Out", type="primary", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["user"] = None
            st.session_state["page"] = "home"
            st.rerun()


# -- Defining application for buyer -- 
def show_main_app_buyer():
    st.markdown("Buyer Dashboard")

    # -- Sidebar for navigating pages and logging out for buyer -- 
    with st.sidebar:
        if st.button("Home", key = "home_btn", type = "primary", use_container_width = True):
            st.session_state["page"] = "home"
            st.rerun()

        if st.button("Browse Listings", key = "browse_listings", type = "primary", use_container_width = True):
            st.session_state["page"] = "browse_listings"
            st.rerun()
        
        if st.button("My Inquiries", key = "my_inquiries", type = "primary", use_container_width = True):
            st.session_state["page"] = "my_inquiries"
            st.rerun()
        
        st.write(f"Logged in as: {st.session_state['user']['email']}")

        if st.button("Log Out", type="primary", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["user"] = None
            st.session_state["page"] = "home"
            st.rerun()

# -- runs the main page best on user role and if not logged in displays login/registration page -- 
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