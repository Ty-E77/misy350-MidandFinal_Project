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
st.title("Real Estate Finder")

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
            st.markdown("## New Account")
            email = st.text_input("Email", placeholder = "ex. 1234@gmail.com", key = "email_new")
            full_name = st.text_input("Full Name:", placeholder = "ex. John Doe", key = "full_name_new")
            password = st.text_input("Password", type = "password", key = "password_new")
            role = st.radio("Role", ["Agent", "Buyer"])
            btn_create = st.button("Create Account", use_container_width = True, disabled = False, type = "primary")

            if btn_create:
                if (email == "") or (full_name == "") or (password == ""):
                    st.warning("Missing required information")
                    st.stop()
                else:
                    with st.spinner("Account is being created..."):
                        time.sleep(5)

                        users.append ( {
                        "id": str(uuid.uuid4()),
                        "email": email,
                        "full_name": full_name,
                        "password": password,
                        "role": role,
                        "registered_at": str(datetime.now())

        })
                with json_file_users.open("w", encoding = "utf-8") as f:
                            json.dump(users, f)

                st.success("Account created successfully!")
    with tab2:
        with st.container(border = True):
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
                    for user in users:
                        if user["email"] == email_login and user["password"] == password_login:
                            login_check = user
                            break

                    if login_check:
                        st.session_state["logged_in"] = True
                        st.session_state["user"] = login_check
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

# -- Defining application for agent --                                 
def show_main_app_agent():
    st.markdown("Agent Home")

    with st.sidebar:
        if st.button("Home", key = "home_btn", type = "primary", use_container_width = True):
            st.session_state["page"] = "home"
            st.rerun()

        if st.button("My Listings", key = "properties_listings", type = "primary", use_container_width = True):
            st.session_state["page"] = "properties_listings"
            st.rerun()
        
        if st.button("Add Listings", key = "add_listings", type = "primary", use_container_width = True):
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
            st.rerun()

# -- Defining application for buyer -- 
def show_main_app_buyer():
    st.markdown("Buyer Home")

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
            st.rerun()
    



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