import streamlit as st
import time
from datetime import datetime, time as dt_time


class RealEstateUI:
    def __init__(self, service_manager, data_manager):
        self.service = service_manager
        self.data = data_manager

    def render_listing_detail_sections(self, selected_listing):
        with st.container():
            st.markdown(f"### {selected_listing.get('title','')}")
            st.markdown(f"**{selected_listing.get('address','')}, {selected_listing.get('city','')}, {selected_listing.get('state','')}**")
            st.markdown(f"**Status:** {selected_listing.get('status','')}")
            st.markdown(f"### ${selected_listing.get('price',0):,}")

    def process_chat_message(self, role, chat_key, user_input):
        st.session_state.setdefault(chat_key, [])
        st.session_state[chat_key].append({"role": "user", "content": user_input})
        if role == "Agent":
            response = self.get_agent_chatbot_response(user_input)
        else:
            response = self.get_buyer_chatbot_response(user_input)
        st.session_state[chat_key].append({"role": "assistant", "content": response})

    def get_agent_chatbot_response(self, user_input):
        user_input = (user_input or "").strip().lower()
        if "add a new listing" in user_input:
            return "Use the sidebar 'Add New Listing' to create a listing."
        return "I’m not sure about that yet."

    def get_buyer_chatbot_response(self, user_input):
        user_input = (user_input or "").strip().lower()
        if "browse listings" in user_input:
            return "Use 'Browse Listings' to filter and view properties."
        return "I’m not sure about that yet."

    def show_chat_bot(self, role):
        chat_key = "agent_chatbot" if role == "Agent" else "buyer_chatbot"
        default_message = "Hi! I’m your assistant."
        st.session_state.setdefault(chat_key, [{"role": "assistant", "content": default_message}])
        with st.container():
            st.markdown(f"### {default_message}")

    def show_login_page(self):
        st.markdown("# Real Estate Finder")
        st.caption("Browse listings, book appointments, and connect with agents.")
        if getattr(self.data, "warnings", None):
            with st.expander("Data file warnings"):
                for w in self.data.warnings:
                    st.warning(w)
        st.divider()
        tab1, tab2 = st.tabs(["Log In", "Register"])
        with tab1:
            email_login = st.text_input("Email", key="login_email")
            password_login = st.text_input("Password", type="password", key="login_password")
            if st.button("Log In", key="auth_login_submit_btn"):
                user = self.service.authenticate((email_login or "").strip().lower(), password_login)
                if user:
                    st.session_state["logged_in"] = True
                    st.session_state["user"] = user
                    st.session_state["page"] = "home"
                    st.session_state["_queued_rerun"] = True
                else:
                    st.error("Invalid email or password.")
        with tab2:
            full_name = st.text_input("Full Name", key="full_name_new")
            email = st.text_input("Email", key="email_new")
            password = st.text_input("Password", type="password", key="password_new")
            role = st.selectbox("Role", ["Agent", "Buyer"], key="role_new")
            if st.button("Create Account", key="auth_register_submit_btn"):
                result = self.service.register_user(full_name, email, password, role)
                if not result.get("success"):
                    for err in result.get("errors", []):
                        st.error(err)
                else:
                    st.success("Account created successfully! You can now log in.")

    def show_main_app_agent(self):
        page = st.session_state.get("page", "home")
        user = st.session_state.get("user") or {}
        if page == "home":
            st.markdown(f"## Agent Dashboard - {user.get('full_name','')}")
            st.caption("Manage listings, review buyer bookings, and respond to inquiries.")
            if getattr(self.data, "warnings", None):
                with st.expander("Data file warnings"):
                    for w in self.data.warnings:
                        st.warning(w)
            st.divider()
            stats = self.service.get_agent_dashboard_stats(user.get("id")) if hasattr(self.service, 'get_agent_dashboard_stats') else {}
            st.markdown("### Quick Actions")
            cols = st.columns(3)
            with cols[0]:
                if st.button("View My Listings"):
                    st.session_state["page"] = "properties_listings"
                    st.session_state["_queued_rerun"] = True
            with cols[1]:
                if st.button("Add New Listing"):
                    st.session_state["page"] = "add_listings"
                    st.session_state["_queued_rerun"] = True
            with cols[2]:
                if st.button("View Buyer Requests"):
                    st.session_state["page"] = "buyer_inquiries"
                    st.session_state["_queued_rerun"] = True
            st.divider()
            self.show_chat_bot("Agent")

        elif page == "properties_listings":
            st.markdown("# View Property Listings")
            st.divider()
            st.info("Listings page - use app.py flow to populate and navigate listings.")

    # End of ui.py
