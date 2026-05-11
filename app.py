# =========================
# IMPORTS
# =========================

import json
import hashlib
import os
from pathlib import Path
from datetime import datetime, time as dt_time
import uuid
import time
import html

import streamlit as st

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# =========================
# REAL ESTATE DATA CLASS
# =========================

class RealEstateData:
    def __init__(self):
        self.json_file_properties = Path("properties.json")
        self.json_file_users = Path("users.json")
        self.json_file_inquiries = Path("inquiry.json")
        self.json_file_bookings = Path("bookings.json")

        self.data_load_warnings = []

        self.users = self.load_json_list(self.json_file_users, "users")
        self.users = self.validate_records(self.users, self.is_valid_user, "users")
        self.apply_user_defaults()

        self.properties = self.load_json_list(self.json_file_properties, "properties")
        self.properties = self.validate_records(self.properties, self.is_valid_property, "properties")
        self.apply_property_defaults()

        self.inquiries = self.load_json_list(self.json_file_inquiries, "inquiries")
        self.inquiries = self.validate_records(self.inquiries, self.is_valid_inquiry, "inquiries")
        self.apply_inquiry_defaults()

        self.bookings = self.load_json_list(self.json_file_bookings, "bookings")
        self.bookings = self.validate_records(self.bookings, self.is_valid_booking, "bookings")
        self.apply_booking_defaults()

    def load_json_list(self, file_path, label="data"):
        if not file_path.exists():
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                return data

            self.data_load_warnings.append(f"{label} file did not contain a list, so it was ignored.")
            return []

        except json.JSONDecodeError:
            self.data_load_warnings.append(f"{label} file could not be decoded, so it was ignored.")
            return []
        except OSError:
            self.data_load_warnings.append(f"{label} file could not be opened, so it was ignored.")
            return []

    def save_json_list(self, file_path, data):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def validate_records(self, records, validator, label):
        valid_records = []
        invalid_count = 0

        for record in records:
            if validator(record):
                valid_records.append(record)
            else:
                invalid_count += 1

        if invalid_count:
            self.data_load_warnings.append(f"{invalid_count} invalid {label} record(s) were skipped.")

        return valid_records

    def has_required_keys(self, record, required_keys):
        return isinstance(record, dict) and all(key in record for key in required_keys)

    def is_valid_user(self, user):
        required_keys = ["id", "email", "password", "role"]
        return self.has_required_keys(user, required_keys)

    def is_valid_property(self, listing):
        required_keys = [
            "id", "agent_id", "title", "address", "city", "state",
            "price", "bedrooms", "bathrooms", "property_sqft", "property_type"
        ]
        return self.has_required_keys(listing, required_keys)

    def is_valid_inquiry(self, inquiry):
        required_keys = [
            "id", "listing_id", "property_title", "agent_id", "buyer_id",
            "buyer_name", "buyer_email", "buyer_phone", "subject", "message"
        ]
        return self.has_required_keys(inquiry, required_keys)

    def is_valid_booking(self, booking):
        required_keys = [
            "id", "listing_id", "property_title", "agent_id", "buyer_id",
            "buyer_name", "buyer_email", "buyer_phone", "appointment_type",
            "appointment_date", "appointment_time"
        ]
        return self.has_required_keys(booking, required_keys)

    def apply_user_defaults(self):
        for user in self.users:
            user.setdefault("full_name", "")
            user.setdefault("role", "")
            user.setdefault("saved_listing_ids", [])

    def apply_property_defaults(self):
        for listing in self.properties:
            listing.setdefault("status", "Available")
            listing.setdefault("description", "")
            listing.setdefault("contact_name", "")
            listing.setdefault("contact_email", "")
            listing.setdefault("contact_phone", "")
            listing.setdefault("image_url", "")

    def apply_inquiry_defaults(self):
        for inquiry in self.inquiries:
            inquiry.setdefault("response", "")
            inquiry.setdefault("response_at", "")
            inquiry.setdefault("status", "New")
            inquiry.setdefault("subject", "")
            inquiry.setdefault("message", "")
            inquiry.setdefault("created_at", "")

    def apply_booking_defaults(self):
        for booking in self.bookings:
            booking.setdefault("status", "Pending")
            booking.setdefault("message", "")
            booking.setdefault("created_at", "")

    def save_users(self):
        self.save_json_list(self.json_file_users, self.users)

    def save_properties(self):
        self.save_json_list(self.json_file_properties, self.properties)

    def save_inquiries(self):
        self.save_json_list(self.json_file_inquiries, self.inquiries)

    def save_bookings(self):
        self.save_json_list(self.json_file_bookings, self.bookings)

    def add_record(self, collection, file_path, record):
        collection.append(record)
        try:
            self.save_json_list(file_path, collection)
        except Exception:
            collection.remove(record)
            raise
        return record

    def update_record(self, collection, file_path, record_id, updates):
        record = self.find_record_by_id(collection, record_id)
        if record is None:
            return None

        old_record = record.copy()
        record.update(updates)

        try:
            self.save_json_list(file_path, collection)
        except Exception:
            record.clear()
            record.update(old_record)
            raise

        return record

    def delete_record(self, collection, file_path, record_id):
        record = self.find_record_by_id(collection, record_id)
        if record is None:
            return None

        index = collection.index(record)
        removed_record = collection.pop(index)

        try:
            self.save_json_list(file_path, collection)
        except Exception:
            collection.insert(index, removed_record)
            raise

        return removed_record

    def find_record_by_id(self, collection, record_id):
        for record in collection:
            if record.get("id") == record_id:
                return record
        return None

    def add_user(self, user):
        return self.add_record(self.users, self.json_file_users, user)

    def update_user(self, user_id, updates):
        return self.update_record(self.users, self.json_file_users, user_id, updates)

    def add_property(self, listing):
        return self.add_record(self.properties, self.json_file_properties, listing)

    def add_inquiry(self, inquiry):
        return self.add_record(self.inquiries, self.json_file_inquiries, inquiry)

    def add_booking(self, booking):
        return self.add_record(self.bookings, self.json_file_bookings, booking)

    def update_property(self, listing_id, updates):
        return self.update_record(self.properties, self.json_file_properties, listing_id, updates)

    def update_booking(self, booking_id, updates):
        return self.update_record(self.bookings, self.json_file_bookings, booking_id, updates)

    def update_inquiry(self, inquiry_id, updates):
        return self.update_record(self.inquiries, self.json_file_inquiries, inquiry_id, updates)

    def delete_property(self, listing_id):
        return self.delete_record(self.properties, self.json_file_properties, listing_id)

    def delete_booking(self, booking_id):
        return self.delete_record(self.bookings, self.json_file_bookings, booking_id)

    def delete_inquiry(self, inquiry_id):
        return self.delete_record(self.inquiries, self.json_file_inquiries, inquiry_id)


# =========================
# REAL ESTATE SERVICE CLASS
# =========================

class RealEstateService:
    APPOINTMENT_START = dt_time(8, 0)
    APPOINTMENT_END = dt_time(17, 0)

    def __init__(self, data, openai_api_key=None, openai_model="gpt-4o-mini"):
        self.data = data
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model
        self.openai_client = None
        self.configure_openai(openai_api_key, openai_model)

    def configure_openai(self, api_key=None, model=None):
        self.openai_api_key = (api_key or self.openai_api_key or "").strip()
        self.openai_model = (model or self.openai_model or "gpt-4o-mini").strip()
        self.last_openai_error = ""

        if OpenAI is None:
            self.openai_client = None
            self.last_openai_error = "OpenAI Python package is not installed. Add openai>=1.99.0 to requirements.txt."
            return False

        if not self.openai_api_key:
            self.openai_client = None
            self.last_openai_error = "OPENAI_API_KEY was not found in Streamlit secrets or environment variables."
            return False

        try:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            return True
        except Exception as error:
            self.openai_client = None
            self.last_openai_error = f"{type(error).__name__}: {error}"
            return False

    def openai_is_ready(self):
        return self.openai_client is not None

    def hash_password(self, password):
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def verify_password(self, submitted_password, stored_password):
        if stored_password == submitted_password:
            return True
        return stored_password == self.hash_password(submitted_password)

    def normalize_email(self, email):
        return email.strip().lower()

    def normalize_phone(self, phone):
        return phone.strip()

    def is_valid_email(self, email):
        return "@" in email and "." in email

    def is_valid_phone(self, phone):
        return phone.isdigit() and len(phone) == 10

    def safe_parse_date(self, date_value):
        if hasattr(date_value, "strftime"):
            return date_value
        try:
            return datetime.strptime(str(date_value), "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return datetime.now().date()

    def safe_parse_time(self, time_value):
        if hasattr(time_value, "strftime"):
            return time_value
        for fmt in ["%H:%M:%S", "%H:%M"]:
            try:
                return datetime.strptime(str(time_value), fmt).time()
            except (TypeError, ValueError):
                continue
        return dt_time(9, 0)

    def is_valid_appointment_time(self, appointment_time):
        return self.APPOINTMENT_START <= appointment_time <= self.APPOINTMENT_END

    def find_user_by_email(self, email):
        normalized_email = self.normalize_email(email)
        for user in self.data.users:
            if self.normalize_email(user.get("email", "")) == normalized_email:
                return user
        return None

    def authenticate_user(self, email, password):
        user = self.find_user_by_email(email)
        if user and self.verify_password(password, user.get("password", "")):
            return user
        return None

    def find_listing_by_id(self, listing_id):
        return self.data.find_record_by_id(self.data.properties, listing_id)

    def find_booking_by_id(self, booking_id):
        return self.data.find_record_by_id(self.data.bookings, booking_id)

    def find_inquiry_by_id(self, inquiry_id):
        return self.data.find_record_by_id(self.data.inquiries, inquiry_id)

    def filter_listings(self, listings, selected_type="All", selected_status="All", exclude_agent_id=None, buyer_visible_only=False, search_text=""):
        filtered = []
        search_text = str(search_text or "").strip().lower()

        for listing in listings:
            if exclude_agent_id and listing.get("agent_id") == exclude_agent_id:
                continue
            if buyer_visible_only and listing.get("status") == "Sold":
                continue

            type_match = selected_type == "All" or listing.get("property_type") == selected_type
            status_match = selected_status == "All" or listing.get("status") == selected_status

            if search_text:
                searchable_text = " ".join([
                    str(listing.get("title", "")),
                    str(listing.get("address", "")),
                    str(listing.get("city", "")),
                    str(listing.get("state", "")),
                    str(listing.get("property_type", "")),
                    str(listing.get("status", "")),
                ]).lower()
                search_match = search_text in searchable_text
            else:
                search_match = True

            if type_match and status_match and search_match:
                filtered.append(listing)
        return filtered

    def sort_listings(self, listings, sort_option="Newest First"):
        sortable = list(listings)

        def safe_number(value):
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0

        def safe_date_text(value):
            return str(value or "")

        if sort_option == "Price: Low to High":
            return sorted(sortable, key=lambda listing: safe_number(listing.get("price")))
        if sort_option == "Price: High to Low":
            return sorted(sortable, key=lambda listing: safe_number(listing.get("price")), reverse=True)
        if sort_option == "Bedrooms: High to Low":
            return sorted(sortable, key=lambda listing: safe_number(listing.get("bedrooms")), reverse=True)
        if sort_option == "Square Feet: High to Low":
            return sorted(sortable, key=lambda listing: safe_number(listing.get("property_sqft")), reverse=True)
        if sort_option == "Status":
            return sorted(sortable, key=lambda listing: str(listing.get("status", "")))
        return sorted(sortable, key=lambda listing: safe_date_text(listing.get("listing_date")), reverse=True)

    def get_agent_listings(self, agent_id):
        return [listing for listing in self.data.properties if listing.get("agent_id") == agent_id]

    def get_agent_bookings(self, agent_id):
        return [booking for booking in self.data.bookings if booking.get("agent_id") == agent_id]

    def get_agent_inquiries(self, agent_id):
        return [inquiry for inquiry in self.data.inquiries if inquiry.get("agent_id") == agent_id]

    def get_buyer_bookings(self, buyer_id):
        return [booking for booking in self.data.bookings if booking.get("buyer_id") == buyer_id]

    def get_buyer_inquiries(self, buyer_id):
        return [inquiry for inquiry in self.data.inquiries if inquiry.get("buyer_id") == buyer_id]

    def calculate_agent_dashboard_stats(self, agent_id):
        agent_listings = self.get_agent_listings(agent_id)
        agent_bookings = self.get_agent_bookings(agent_id)
        agent_inquiries = self.get_agent_inquiries(agent_id)

        return {
            "my_listings_count": len(agent_listings),
            "available_listings_count": len([l for l in agent_listings if l.get("status") == "Available"]),
            "pending_bookings_count": len([b for b in agent_bookings if b.get("status") == "Pending"]),
            "new_inquiries_count": len([i for i in agent_inquiries if i.get("status") == "New"]),
            "agent_listings": agent_listings,
            "agent_bookings": agent_bookings,
            "agent_inquiries": agent_inquiries,
        }

    def calculate_buyer_dashboard_stats(self, buyer_id):
        buyer_bookings = self.get_buyer_bookings(buyer_id)
        buyer_inquiries = self.get_buyer_inquiries(buyer_id)
        available_listings = [l for l in self.data.properties if l.get("status") in ["Available", "Pending"]]

        return {
            "available_listings": len(available_listings),
            "my_bookings": len(buyer_bookings),
            "pending_bookings": len([b for b in buyer_bookings if b.get("status") == "Pending"]),
            "my_inquiries": len(buyer_inquiries),
            "saved_listings": len(self.get_saved_listings(buyer_id)),
            "buyer_bookings": buyer_bookings,
            "buyer_inquiries": buyer_inquiries,
        }

    def has_duplicate_listing(self, agent_id, title, address, exclude_listing_id=None):
        for listing in self.data.properties:
            if exclude_listing_id and listing.get("id") == exclude_listing_id:
                continue
            if (
                listing.get("agent_id") == agent_id
                and listing.get("title", "").strip().lower() == title.strip().lower()
                and listing.get("address", "").strip().lower() == address.strip().lower()
            ):
                return True
        return False

    def create_user(self, full_name, email, password, role):
        new_email = self.normalize_email(email)
        if self.find_user_by_email(new_email):
            return False, "An account with this email already exists.", None
        if not full_name.strip() or not new_email or not password:
            return False, "Please fill in all required fields.", None
        if not self.is_valid_email(new_email):
            return False, "Enter a valid email address.", None

        user = {
            "id": str(uuid.uuid4()),
            "email": new_email,
            "full_name": full_name.strip(),
            "password": password,
            "role": role,
            "saved_listing_ids": [],
            "registered_at": str(datetime.now())
        }
        self.data.add_user(user)
        return True, "Account created successfully! You can now log in.", user

    def create_listing(self, agent_id, title, description, address, city, state, price, bedrooms, bathrooms, property_sqft, property_type, status, contact_name, contact_email, contact_phone, image_url=""):
        title = title.strip()
        description = description.strip()
        address = address.strip()
        city = city.strip()
        state = state.strip()
        contact_name = contact_name.strip()
        contact_email = self.normalize_email(contact_email)
        contact_phone = self.normalize_phone(contact_phone)
        image_url = str(image_url or "").strip()

        if not title or not address or not city or not state or not contact_name or not contact_email or not contact_phone:
            return False, "Please fill in all required fields.", None
        if not self.is_valid_phone(contact_phone):
            return False, "Enter a valid 10-digit phone number.", None
        if not self.is_valid_email(contact_email):
            return False, "Enter a valid email address.", None
        if self.has_duplicate_listing(agent_id, title, address):
            return False, "A listing with this title and address already exists.", None

        new_listing = {
            "id": str(uuid.uuid4()),
            "agent_id": agent_id,
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
            "image_url": image_url,
            "listing_date": str(datetime.now())
        }
        self.data.add_property(new_listing)
        return True, "Listing added successfully!", new_listing

    def update_listing(self, listing_id, updates):
        required_text_fields = ["title", "address", "city", "state", "contact_name", "contact_email", "contact_phone"]
        for key in required_text_fields:
            updates[key] = str(updates.get(key, "")).strip()

        updates["description"] = str(updates.get("description", "")).strip()
        updates["image_url"] = str(updates.get("image_url", "")).strip()
        updates["contact_email"] = self.normalize_email(updates["contact_email"])
        updates["contact_phone"] = self.normalize_phone(updates["contact_phone"])

        if any(not updates[key] for key in required_text_fields):
            return False, "Please fill in all required fields.", None
        if not self.is_valid_phone(updates["contact_phone"]):
            return False, "Enter a valid 10-digit phone number.", None
        if not self.is_valid_email(updates["contact_email"]):
            return False, "Enter a valid email address.", None

        selected_listing = self.find_listing_by_id(listing_id)
        if selected_listing is None:
            return False, "Listing not found.", None

        if self.has_duplicate_listing(selected_listing.get("agent_id"), updates["title"], updates["address"], exclude_listing_id=listing_id):
            return False, "A listing with this title and address already exists.", None

        updated_listing = self.data.update_property(listing_id, updates)
        return True, "Listing updated successfully!", updated_listing

    def delete_listing(self, listing_id):
        deleted_listing = self.data.delete_property(listing_id)
        if deleted_listing is None:
            return False, "Listing not found."
        return True, "Listing deleted successfully!"

    def get_saved_listing_ids(self, buyer):
        saved_ids = buyer.get("saved_listing_ids", []) if isinstance(buyer, dict) else []
        return saved_ids if isinstance(saved_ids, list) else []

    def is_listing_saved(self, buyer, listing_id):
        return listing_id in self.get_saved_listing_ids(buyer)

    def get_saved_listings(self, buyer_id):
        buyer = self.data.find_record_by_id(self.data.users, buyer_id)
        saved_ids = self.get_saved_listing_ids(buyer or {})
        return [listing for listing in self.data.properties if listing.get("id") in saved_ids]

    def toggle_saved_listing(self, buyer, listing_id):
        if not isinstance(buyer, dict) or not buyer.get("id"):
            return False, "Please log in again before saving listings.", False

        if self.find_listing_by_id(listing_id) is None:
            return False, "Listing not found.", False

        saved_ids = list(self.get_saved_listing_ids(buyer))
        if listing_id in saved_ids:
            saved_ids.remove(listing_id)
            saved = False
            message = "Listing removed from saved listings."
        else:
            saved_ids.append(listing_id)
            saved = True
            message = "Listing saved successfully."

        updated_user = self.data.update_user(buyer["id"], {"saved_listing_ids": saved_ids})
        if updated_user is None:
            return False, "User not found.", False

        buyer["saved_listing_ids"] = saved_ids
        return True, message, saved

    def create_booking(self, listing, buyer, appointment_name, appointment_email, appointment_phone, appointment_type, appointment_date, appointment_time, appointment_message):
        appointment_name = appointment_name.strip()
        appointment_email = self.normalize_email(appointment_email)
        appointment_phone = self.normalize_phone(appointment_phone)
        appointment_message = appointment_message.strip()

        if not appointment_name or not appointment_email or not appointment_phone:
            return False, "Please fill in all required fields.", None
        if not self.is_valid_phone(appointment_phone):
            return False, "Enter a valid 10-digit phone number.", None
        if not self.is_valid_email(appointment_email):
            return False, "Enter a valid email address.", None
        if appointment_type == "Select Type":
            return False, "Please select an appointment type.", None
        if not self.is_valid_appointment_time(appointment_time):
            return False, "Appointments must be between 8:00 AM and 5:00 PM.", None

        new_booking = {
            "id": str(uuid.uuid4()),
            "listing_id": listing["id"],
            "property_title": listing["title"],
            "agent_id": listing["agent_id"],
            "buyer_id": buyer["id"],
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
        self.data.add_booking(new_booking)
        return True, "Appointment submitted successfully!", new_booking

    def update_booking(self, booking_id, appointment_type, appointment_date, appointment_time, message):
        if not self.is_valid_appointment_time(appointment_time):
            return False, "Appointments must be between 8:00 AM and 5:00 PM.", None

        updates = {
            "appointment_type": appointment_type,
            "appointment_date": str(appointment_date),
            "appointment_time": str(appointment_time),
            "message": message.strip()
        }
        updated_booking = self.data.update_booking(booking_id, updates)
        if updated_booking is None:
            return False, "Booking not found.", None
        return True, "Booking updated successfully!", updated_booking

    def update_booking_status(self, booking_id, status):
        updated_booking = self.data.update_booking(booking_id, {"status": status})
        if updated_booking is None:
            return False, "Booking not found.", None
        return True, f"Appointment {status.lower()} successfully!", updated_booking

    def delete_booking(self, booking_id):
        deleted_booking = self.data.delete_booking(booking_id)
        if deleted_booking is None:
            return False, "Booking not found."
        return True, "Booking deleted successfully!"

    def create_inquiry(self, listing, buyer, question_name, question_email, question_phone, question_subject, question_message):
        question_name = question_name.strip()
        question_email = self.normalize_email(question_email)
        question_phone = self.normalize_phone(question_phone)
        question_subject = question_subject.strip()
        question_message = question_message.strip()

        if not question_name or not question_email or not question_phone or question_subject == "Select Subject" or not question_message:
            return False, "Please fill in all required fields.", None
        if not self.is_valid_phone(question_phone):
            return False, "Enter a valid 10-digit phone number.", None
        if not self.is_valid_email(question_email):
            return False, "Enter a valid email address.", None

        new_inquiry = {
            "id": str(uuid.uuid4()),
            "listing_id": listing["id"],
            "property_title": listing["title"],
            "agent_id": listing["agent_id"],
            "buyer_id": buyer["id"],
            "buyer_name": question_name,
            "buyer_email": question_email,
            "buyer_phone": question_phone,
            "subject": question_subject,
            "message": question_message,
            "status": "New",
            "created_at": str(datetime.now())
        }
        self.data.add_inquiry(new_inquiry)
        return True, "Question submitted successfully!", new_inquiry

    def update_buyer_inquiry(self, inquiry_id, subject, message):
        if not message.strip():
            return False, "Question cannot be empty.", None

        updates = {"subject": subject, "message": message.strip()}
        updated_inquiry = self.data.update_inquiry(inquiry_id, updates)
        if updated_inquiry is None:
            return False, "Inquiry not found.", None
        return True, "Inquiry updated successfully!", updated_inquiry

    def update_agent_inquiry_response(self, inquiry_id, status, response):
        response = response.strip()
        if status == "Answered" and not response:
            return False, "Please enter a response before marking as Answered.", None

        updates = {
            "status": status,
            "response": response,
            "response_at": str(datetime.now()) if response else ""
        }
        updated_inquiry = self.data.update_inquiry(inquiry_id, updates)
        if updated_inquiry is None:
            return False, "Inquiry not found.", None
        return True, "Inquiry updated successfully!", updated_inquiry

    def delete_inquiry(self, inquiry_id):
        deleted_inquiry = self.data.delete_inquiry(inquiry_id)
        if deleted_inquiry is None:
            return False, "Inquiry not found."
        return True, "Inquiry deleted successfully!"

    def get_agent_chatbot_response(self, user_input):
        user_input = user_input.strip().lower()
        if user_input == "how do i add a new listing?":
            return "Go to the sidebar and click 'Add Property Listings'. Fill out the listing overview, property details, location, and contact information, then click 'Add Listing'."
        if user_input == "where do i manage my listings?":
            return "Go to 'View/Manage Property Listings' in the sidebar. In the 'My Property Listings' tab, click 'Manage Listing' on any property to update or delete it."
        if user_input == "where do i view buyer requests?":
            return "Go to 'Buyer Bookings & Inquiries' from the sidebar. There you can confirm or decline bookings and respond to buyer questions."
        return "I’m not sure about that yet. Try one of the suggested questions above."

    def get_buyer_chatbot_response(self, user_input):
        user_input = user_input.strip().lower()
        if user_input == "how do i browse listings?":
            return "Go to the sidebar and click 'Browse Listings'. You can filter by property type and status, then click 'View Listing Details' for more information."
        if user_input == "how do i book an appointment?":
            return "Open a property from 'Browse Listings', click 'Book an Appointment', complete the form, and submit it. Your request will appear under 'My Bookings & Inquiries'."
        if user_input == "how do i ask a question?":
            return "Open a property from 'Browse Listings', click 'Ask a Question(s)', choose a subject, type your question, and submit it. You can later view the response in 'My Bookings & Inquiries'."
        return "I’m not sure about that yet. Try one of the suggested questions above."

    def safe_money(self, value):
        try:
            return f"${int(value):,}"
        except (TypeError, ValueError):
            return "$0"

    def summarize_listing_for_chat(self, listing):
        return (
            f"- {listing.get('title', 'Untitled')} | "
            f"{listing.get('property_type', 'Property')} | "
            f"{listing.get('city', '')}, {listing.get('state', '')} | "
            f"{self.safe_money(listing.get('price', 0))} | "
            f"{listing.get('bedrooms', 0)} bed / {listing.get('bathrooms', 0)} bath | "
            f"{listing.get('property_sqft', 0)} sqft | "
            f"Status: {listing.get('status', '')}"
        )

    def build_chat_context(self, role, current_user=None):
        current_user = current_user or {}
        user_id = current_user.get("id")
        role = role or current_user.get("role", "")

        if role == "Agent":
            stats = self.calculate_agent_dashboard_stats(user_id)
            listing_lines = [self.summarize_listing_for_chat(l) for l in stats["agent_listings"][:10]]
            booking_lines = [
                f"- {b.get('property_title', '')} | Buyer: {b.get('buyer_name', '')} | "
                f"Date: {b.get('appointment_date', '')} at {b.get('appointment_time', '')} | Status: {b.get('status', '')}"
                for b in stats["agent_bookings"][:10]
            ]
            inquiry_lines = [
                f"- {i.get('property_title', '')} | Buyer: {i.get('buyer_name', '')} | "
                f"Subject: {i.get('subject', '')} | Status: {i.get('status', '')}"
                for i in stats["agent_inquiries"][:10]
            ]
            return "\n".join([
                "Current role: Agent",
                f"Current user: {current_user.get('full_name', '')}",
                f"Dashboard counts: {stats['my_listings_count']} listings, {stats['available_listings_count']} available, {stats['pending_bookings_count']} pending bookings, {stats['new_inquiries_count']} new inquiries.",
                "Agent listings:",
                "\n".join(listing_lines) if listing_lines else "- None",
                "Recent booking requests:",
                "\n".join(booking_lines) if booking_lines else "- None",
                "Recent inquiries:",
                "\n".join(inquiry_lines) if inquiry_lines else "- None",
            ])

        buyer_bookings = self.get_buyer_bookings(user_id)
        buyer_inquiries = self.get_buyer_inquiries(user_id)
        saved_listings = self.get_saved_listings(user_id)
        visible_listings = [l for l in self.data.properties if l.get("status") != "Sold"][:12]
        listing_lines = [self.summarize_listing_for_chat(l) for l in visible_listings]
        saved_lines = [self.summarize_listing_for_chat(l) for l in saved_listings[:10]]
        booking_lines = [
            f"- {b.get('property_title', '')} | {b.get('appointment_type', '')} | "
            f"{b.get('appointment_date', '')} at {b.get('appointment_time', '')} | Status: {b.get('status', '')}"
            for b in buyer_bookings[:10]
        ]
        inquiry_lines = [
            f"- {i.get('property_title', '')} | Subject: {i.get('subject', '')} | Status: {i.get('status', '')}"
            for i in buyer_inquiries[:10]
        ]
        return "\n".join([
            "Current role: Buyer",
            f"Current user: {current_user.get('full_name', '')}",
            f"Available/Pending listings shown to buyers: {len([l for l in self.data.properties if l.get('status') in ['Available', 'Pending']])}",
            f"Current buyer bookings: {len(buyer_bookings)}",
            f"Current buyer inquiries: {len(buyer_inquiries)}",
            "Visible listings:",
            "\n".join(listing_lines) if listing_lines else "- None",
            "Buyer bookings:",
            "\n".join(booking_lines) if booking_lines else "- None",
            "Buyer inquiries:",
            "\n".join(inquiry_lines) if inquiry_lines else "- None",
        ])

    def format_chat_history_for_model(self, messages, limit=8):
        recent_messages = messages[-limit:] if messages else []
        lines = []
        for message in recent_messages:
            role = message.get("role", "user")
            content = str(message.get("content", "")).strip()
            if content:
                lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def get_openai_chatbot_response(self, role, user_input, messages=None, current_user=None):
        fallback_answer = (
            self.get_agent_chatbot_response(user_input)
            if role == "Agent"
            else self.get_buyer_chatbot_response(user_input)
        )

        if not self.openai_is_ready():
            if self.last_openai_error:
                return f"OpenAI is not ready: {self.last_openai_error}\n\nFallback answer: {fallback_answer}"
            return fallback_answer

        app_context = self.build_chat_context(role, current_user)
        chat_history = self.format_chat_history_for_model(messages)

        instructions = """
You are the in-app AI assistant for a Streamlit app named Real Estate Finder.
Help the logged-in user understand and use the app.
Use the provided app context when answering questions about listings, bookings, inquiries, dashboards, and next steps.
Keep answers concise, practical, and specific to the user's role.
Do not claim you completed an action in the app. You can guide the user to click buttons or fill forms, but you cannot directly create, update, or delete records from chat.
Do not expose raw JSON, passwords, internal IDs, API keys, or hidden implementation details.
If the user asks for something outside the app, answer briefly and redirect back to real estate app tasks when helpful.
""".strip()

        prompt = f"""
APP CONTEXT:
{app_context}

RECENT CHAT:
{chat_history if chat_history else '- No previous chat messages.'}

USER QUESTION:
{user_input}
""".strip()

        try:
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": instructions},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=500,
            )
            answer = response.choices[0].message.content
            answer = str(answer).strip() if answer else ""
            return answer or "I could not generate a response. Please try again."
        except Exception as error:
            self.last_openai_error = f"{type(error).__name__}: {error}"
            return f"OpenAI error: {self.last_openai_error}\n\nFallback answer: {fallback_answer}"


# =========================
# REAL ESTATE UI CLASS
# =========================

class RealEstateUI:
    PROPERTY_TYPES = ["House", "Apartment", "Condo", "Townhouse"]
    LISTING_STATUSES = ["Available", "Pending", "Sold"]
    BUYER_STATUSES = ["Available", "Pending"]
    APPOINTMENT_TYPES = ["Property Walkthrough", "Initial Consultation", "Offer Discussion"]
    QUESTION_SUBJECTS = [
        "Property Availability", "Schedule a Tour", "Pricing Information",
        "Financing Questions", "Property Details", "Make an Offer", "Other"
    ]

    STOCK_PROPERTY_IMAGES = [
        "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=1400&q=80",
        "https://images.unsplash.com/photo-1570129477492-45c003edd2be?auto=format&fit=crop&w=1400&q=80",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1400&q=80",
        "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1400&q=80",
        "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1400&q=80",
        "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1400&q=80",
        "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1400&q=80",
        "https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1400&q=80",
    ]

    STOCK_IMAGES_BY_TYPE = {
        "House": [
            "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1570129477492-45c003edd2be?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1400&q=80",
        ],
        "Apartment": [
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1400&q=80",
        ],
        "Condo": [
            "https://images.unsplash.com/photo-1493809842364-78817add7ffb?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1400&q=80",
        ],
        "Townhouse": [
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1605146769289-440113cc3d00?auto=format&fit=crop&w=1400&q=80",
        ],
    }

    def __init__(self, service):
        self.service = service
        self.data = service.data

    def configure_page(self):
        st.set_page_config(
            page_title="Real Estate Finder",
            page_icon="🏠",
            layout="wide",
            initial_sidebar_state="expanded"
        )

    def apply_base_styles(self):
        st.markdown(
            """
            <style>
            :root {
                --re-bg: var(--secondary-background-color);
                --re-surface: rgba(255, 255, 255, 0.04);
                --re-surface-2: rgba(255, 255, 255, 0.06);
                --re-border: rgba(255, 255, 255, 0.12);
                --re-text: var(--text-color);
                --re-muted: rgba(250, 250, 250, 0.72);
                --re-shadow: 0 8px 24px rgba(0, 0, 0, 0.22);
                --re-danger-bg: rgba(239, 68, 68, 0.10);
                --re-danger-border: rgba(239, 68, 68, 0.28);
                --re-warning-bg: rgba(245, 158, 11, 0.12);
                --re-warning-border: rgba(245, 158, 11, 0.28);
                --re-success-bg: rgba(34, 197, 94, 0.12);
                --re-success-border: rgba(34, 197, 94, 0.28);
            }

            .block-container {
                padding-top: 2rem;
                padding-bottom: 3rem;
                max-width: 1500px;
                padding-left: 2.5rem;
                padding-right: 2.5rem;
            }

            @media (max-width: 900px) {
                .block-container {
                    padding-left: 1rem;
                    padding-right: 1rem;
                }
            }

            .page-header {
                background: linear-gradient(
                    135deg,
                    rgba(255,255,255,0.04) 0%,
                    rgba(255,255,255,0.02) 100%
                );
                border: 1px solid var(--re-border);
                border-radius: 24px;
                padding: 1.35rem 1.5rem;
                margin-bottom: 1.25rem;
                box-shadow: var(--re-shadow);
            }

            .page-title {
                font-size: 2rem;
                line-height: 1.2;
                font-weight: 850;
                color: var(--re-text);
                margin: 0 0 0.25rem 0;
            }

            .page-caption {
                color: var(--re-muted);
                font-size: 1rem;
                margin: 0;
            }

            .section-title {
                font-size: 1.25rem;
                font-weight: 800;
                color: var(--re-text);
                margin: 1.2rem 0 0.6rem 0;
            }

            .section-card {
                background: var(--re-surface);
                border: 1px solid var(--re-border);
                border-radius: 20px;
                padding: 1rem 1.1rem;
                margin: 0.75rem 0 1rem 0;
                box-shadow: var(--re-shadow);
                color: var(--re-text);
            }

            .metric-card {
                background: var(--re-surface);
                border: 1px solid var(--re-border);
                border-radius: 20px;
                padding: 1rem;
                min-height: 118px;
                box-shadow: var(--re-shadow);
                color: var(--re-text);
            }

            .metric-icon {
                font-size: 1.35rem;
                margin-bottom: 0.25rem;
            }

            .metric-label {
                color: var(--re-muted);
                font-size: 0.88rem;
                font-weight: 700;
                margin-bottom: 0.35rem;
            }

            .metric-value {
                color: var(--re-text);
                font-size: 2rem;
                font-weight: 900;
                line-height: 1;
            }

            .listing-card {
                background: var(--re-surface);
                border: 1px solid var(--re-border);
                border-radius: 24px;
                padding: 1rem;
                margin: 1rem 0 0.4rem 0;
                box-shadow: var(--re-shadow);
                color: var(--re-text);
                height: 100%;
            }

            .listing-card-top {
                display: flex;
                justify-content: space-between;
                gap: 1rem;
                align-items: flex-start;
            }

            .listing-title {
                font-size: 1.35rem;
                font-weight: 850;
                color: var(--re-text);
                margin: 0 0 0.35rem 0;
            }

            .listing-price {
                font-size: 1.25rem;
                font-weight: 900;
                color: var(--re-text);
                text-align: right;
                margin: 0 0 0.35rem 0;
            }

            .listing-address,
            .muted-text {
                color: var(--re-muted);
                margin: 0;
            }

            .listing-facts {
                border-top: 1px solid var(--re-border);
                margin-top: 0.9rem;
                padding-top: 0.85rem;
                color: var(--re-text);
                font-weight: 650;
            }

            .status-badge {
                display: inline-block;
                padding: 0.28rem 0.7rem;
                border-radius: 999px;
                font-size: 0.78rem;
                font-weight: 850;
                letter-spacing: 0.01em;
                border: 1px solid transparent;
                white-space: nowrap;
            }

            .status-available, .status-confirmed, .status-answered {
                background: rgba(34, 197, 94, 0.14);
                color: #86efac;
                border-color: rgba(34, 197, 94, 0.32);
            }

            .status-pending, .status-new, .status-in-progress {
                background: rgba(245, 158, 11, 0.14);
                color: #fcd34d;
                border-color: rgba(245, 158, 11, 0.30);
            }

            .status-sold, .status-declined {
                background: rgba(239, 68, 68, 0.14);
                color: #fca5a5;
                border-color: rgba(239, 68, 68, 0.30);
            }

            .status-default {
                background: rgba(99, 102, 241, 0.14);
                color: #c7d2fe;
                border-color: rgba(99, 102, 241, 0.28);
            }

            .empty-state-card {
                background: var(--re-surface);
                border: 1px dashed var(--re-border);
                border-radius: 22px;
                padding: 1.4rem;
                text-align: center;
                margin: 1rem 0;
                color: var(--re-text);
            }

            .empty-state-icon {
                font-size: 2rem;
                margin-bottom: 0.35rem;
            }

            .empty-state-title {
                font-size: 1.15rem;
                font-weight: 850;
                color: var(--re-text);
                margin-bottom: 0.25rem;
            }

            .empty-state-message {
                color: var(--re-muted);
                margin: 0;
            }

            .danger-text {
                color: #fca5a5;
                font-weight: 800;
            }

            .confirm-box {
                background: var(--re-warning-bg);
                border: 1px solid var(--re-warning-border);
                border-radius: 18px;
                padding: 1rem;
                margin: 0.75rem 0;
                color: var(--re-text);
            }

            .confirm-title {
                font-weight: 850;
                color: #fcd34d;
                margin-bottom: 0.25rem;
            }

            .confirm-message {
                color: var(--re-text);
                margin: 0;
            }

            .sidebar-user-card {
                background: var(--re-surface);
                border: 1px solid var(--re-border);
                border-radius: 18px;
                padding: 0.9rem 1rem;
                margin: 0.75rem 0 1rem 0;
                box-shadow: var(--re-shadow);
                color: var(--re-text);
            }

            .sidebar-user-name {
                color: var(--re-text);
                font-weight: 800;
                font-size: 1rem;
                margin-bottom: 0.15rem;
            }

            .sidebar-user-email {
                color: var(--re-muted);
                font-size: 0.9rem;
                margin-bottom: 0.5rem;
                word-break: break-word;
            }

            .success-summary-card {
                background: var(--re-success-bg);
                border: 1px solid var(--re-success-border);
                border-radius: 18px;
                padding: 1rem;
                margin: 0.75rem 0;
                color: var(--re-text);
            }

            .success-summary-title {
                color: #86efac;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .success-summary-line {
                color: var(--re-text);
                margin: 0.12rem 0;
            }



            .listing-image {
                width: 100%;
                min-height: 180px;
                border-radius: 18px;
                border: 1px solid var(--re-border);
                background: linear-gradient(135deg, rgba(99,102,241,0.18), rgba(14,165,233,0.12));
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: hidden;
                margin-bottom: 1rem;
                color: var(--re-muted);
                font-weight: 800;
                text-align: center;
            }

            .listing-detail-image {
                min-height: 360px;
                margin-bottom: 1.25rem;
            }

            .listing-image img {
                width: 100%;
                height: 220px;
                object-fit: cover;
                display: block;
            }

            .listing-detail-image img {
                height: 420px;
            }

            @media (max-width: 900px) {
                .listing-detail-image,
                .listing-detail-image img {
                    min-height: 220px;
                    height: 260px;
                }
            }

            .filter-chip-row {
                display: flex;
                flex-wrap: wrap;
                gap: 0.4rem;
                margin: 0.75rem 0 0.25rem 0;
            }

            .filter-chip {
                display: inline-block;
                padding: 0.35rem 0.65rem;
                border-radius: 999px;
                border: 1px solid var(--re-border);
                background: var(--re-surface);
                color: var(--re-text);
                font-size: 0.82rem;
                font-weight: 700;
            }

            .next-step-card {
                background: var(--re-surface);
                border: 1px solid var(--re-border);
                border-radius: 20px;
                padding: 1rem;
                margin: 0.5rem 0;
                box-shadow: var(--re-shadow);
                color: var(--re-text);
            }

            .next-step-title {
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .next-step-message {
                color: var(--re-muted);
                margin: 0;
            }

            .answered-badge {
                display: inline-block;
                margin-top: 0.35rem;
                padding: 0.25rem 0.6rem;
                border-radius: 999px;
                background: rgba(34, 197, 94, 0.14);
                color: #86efac;
                border: 1px solid rgba(34, 197, 94, 0.32);
                font-size: 0.78rem;
                font-weight: 850;
            }

            /* Streamlit bordered containers */
            div[data-testid="stVerticalBlockBorderWrapper"] {
                background: transparent !important;
                border-color: var(--re-border) !important;
                border-radius: 18px !important;
            }

            /* Expanders */
            div[data-testid="stExpander"] {
                border: 1px solid var(--re-border) !important;
                border-radius: 18px !important;
                background: var(--re-surface) !important;
                color: var(--re-text) !important;
            }

            /* Tabs */
            button[data-baseweb="tab"] {
                color: var(--re-text) !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

    def setup_session_state(self):
        defaults = {
            "logged_in": False,
            "user": None,
            "page": "home",
            "selected_agent_listing_id": None,
            "selected_other_listing_id": None,
            "edit_agent_inquiry_id": None,
            "booking_listing_id": None,
            "selected_listing_id": None,
            "question_listing_id": None,
            "edit_booking_id": None,
            "edit_inquiry_id": None,
            "agent_chat_input_version": 0,
            "buyer_chat_input_version": 0,
            "confirm_delete_listing_id": None,
            "confirm_delete_booking_id": None,
            "confirm_delete_inquiry_id": None,
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

        if "agent_chatbot" not in st.session_state:
            st.session_state["agent_chatbot"] = [{"role": "assistant", "content": "Hi! I’m your agent assistant. Ask me about listings, buyer requests, or adding a property."}]
        if "buyer_chatbot" not in st.session_state:
            st.session_state["buyer_chatbot"] = [{"role": "assistant", "content": "Hi! I’m your buyer assistant. Ask me about browsing listings, booking appointments, or sending inquiries."}]

    def rerun(self):
        st.rerun()

    def go_to_page(self, page):
        st.session_state["page"] = page
        self.rerun()

    def current_user(self):
        return st.session_state.get("user")

    def configure_openai_from_secrets(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

        try:
            api_key = api_key or st.secrets.get("OPENAI_API_KEY")
            model = st.secrets.get("OPENAI_MODEL", model)
        except (FileNotFoundError, KeyError, AttributeError):
            pass

        self.service.configure_openai(api_key=api_key, model=model)

    def escape(self, value):
        return html.escape(str(value))

    def format_price(self, price):
        try:
            return f"${int(price):,}"
        except (TypeError, ValueError):
            return "$0"

    def listing_sort_options(self):
        return [
            "Newest First",
            "Price: Low to High",
            "Price: High to Low",
            "Bedrooms: High to Low",
            "Square Feet: High to Low",
            "Status",
        ]

    def get_stock_image_url(self, listing):
        property_type = str(listing.get("property_type", "")).strip()
        listing_id = str(listing.get("id") or listing.get("title") or property_type or "default")
        image_pool = self.STOCK_IMAGES_BY_TYPE.get(property_type, self.STOCK_PROPERTY_IMAGES)
        if not image_pool:
            image_pool = self.STOCK_PROPERTY_IMAGES
        index = sum(ord(char) for char in listing_id) % len(image_pool)
        return image_pool[index]

    def get_listing_image_url(self, listing):
        image_url = str(listing.get("image_url", "") or "").strip()
        return image_url if image_url else self.get_stock_image_url(listing)

    def render_listing_image_html(self, listing, detail=False):
        image_url = self.get_listing_image_url(listing)
        detail_class = " listing-detail-image" if detail else ""
        return f'<div class="listing-image{detail_class}"><img src="{self.escape(image_url)}" alt="Property image"></div>'

    def render_listing_grid(self, listings, button_label, button_key_prefix, next_page, selected_key, show_favorite=False, columns=2):
        if not listings:
            return
        column_items = st.columns(columns)
        for index, listing in enumerate(listings):
            with column_items[index % columns]:
                self.render_listing_card(
                    listing,
                    button_label,
                    f"{button_key_prefix}_{listing['id']}",
                    next_page,
                    selected_key,
                    show_favorite=show_favorite
                )

    def render_active_filter_summary(self, selected_type, selected_status, search_text, sort_option):
        chips = []
        if selected_type != "All":
            chips.append(f"Type: {selected_type}")
        if selected_status != "All":
            chips.append(f"Status: {selected_status}")
        if str(search_text or "").strip():
            chips.append(f"Search: {search_text.strip()}")
        if sort_option:
            chips.append(f"Sort: {sort_option}")
        if not chips:
            chips.append("Showing all matching listings")

        chip_html = "".join(f'<span class="filter-chip">{self.escape(chip)}</span>' for chip in chips)
        st.markdown(f'<div class="filter-chip-row">{chip_html}</div>', unsafe_allow_html=True)

    def render_next_step_card(self, title, message, icon="✨"):
        st.markdown(
            f'''
            <div class="next-step-card">
                <div class="next-step-title">{self.escape(icon)} {self.escape(title)}</div>
                <p class="next-step-message">{self.escape(message)}</p>
            </div>
            ''',
            unsafe_allow_html=True
        )

    def render_agent_next_steps(self, stats):
        self.render_section_title("Recommended Next Steps")
        if stats["pending_bookings_count"]:
            self.render_next_step_card("Review pending appointments", f"You have {stats['pending_bookings_count']} pending booking request(s) waiting for a response.", "📅")
        if stats["new_inquiries_count"]:
            self.render_next_step_card("Answer new buyer questions", f"You have {stats['new_inquiries_count']} new inquiry/inquiries that may need a response.", "💬")
        if not stats["my_listings_count"]:
            self.render_next_step_card("Add your first listing", "Create a property listing so buyers can browse, book, and ask questions.", "🏠")
        if stats["my_listings_count"] and not stats["pending_bookings_count"] and not stats["new_inquiries_count"]:
            self.render_next_step_card("Keep listings fresh", "Review your active listings and update pricing, status, or photos when needed.", "✅")

    def render_buyer_next_steps(self, stats):
        self.render_section_title("Recommended Next Steps")
        if not stats["saved_listings"]:
            self.render_next_step_card("Save listings you like", "Use the Save Listing button while browsing so you can compare your favorite properties later.", "⭐")
        if not stats["my_bookings"]:
            self.render_next_step_card("Book a property tour", "Open a listing and request an appointment when you find a property you want to see.", "📅")
        if stats["pending_bookings"]:
            self.render_next_step_card("Track pending appointments", f"You have {stats['pending_bookings']} pending appointment request(s). Check back for agent updates.", "⏳")
        if stats["my_inquiries"]:
            self.render_next_step_card("Check inquiry responses", "Review your inquiries to see whether agents have answered your questions.", "💬")

    def render_save_listing_button(self, listing):
        user = self.current_user() or {}
        if user.get("role") != "Buyer":
            return
        is_saved = self.service.is_listing_saved(user, listing.get("id"))
        label = "★ Saved Listing" if is_saved else "☆ Save Listing"
        if st.button(label, key=f"save_listing_{listing['id']}", use_container_width=True):
            success, message, saved = self.service.toggle_saved_listing(user, listing["id"])
            if success:
                st.success(message)
                st.session_state["user"] = user
                self.rerun()
            else:
                st.error(message)

    def render_listing_filter_controls(self, type_key, status_key, search_key, sort_key, status_options):
        with st.container(border=True):
            st.markdown("###### Search, Filter, and Sort Listings")
            search_text = st.text_input(
                "Search Listings",
                placeholder="Search by title, city, address, state, type, or status...",
                key=search_key
            )
            col_type, col_status = st.columns(2)
            with col_type:
                selected_type = st.selectbox("Property Type", ["All"] + self.PROPERTY_TYPES, key=type_key)
            with col_status:
                selected_status = st.selectbox("Status", ["All"] + status_options, key=status_key)
            sort_option = st.selectbox("Sort By", self.listing_sort_options(), key=sort_key)
        return selected_type, selected_status, search_text, sort_option

    def render_sidebar_user_card(self):
        user = self.current_user() or {}
        st.markdown(
            f"""
            <div class="sidebar-user-card">
                <div class="sidebar-user-name">{self.escape(user.get('full_name', 'User'))}</div>
                <div class="sidebar-user-email">{self.escape(user.get('email', ''))}</div>
                {self.get_status_badge_html(user.get('role', ''))}
            </div>
            """,
            unsafe_allow_html=True
        )

    def render_success_summary(self, title, lines):
        line_html = "".join(f'<div class="success-summary-line">{self.escape(line)}</div>' for line in lines)
        st.markdown(
            f"""
            <div class="success-summary-card">
                <div class="success-summary-title">{self.escape(title)}</div>
                {line_html}
            </div>
            """,
            unsafe_allow_html=True
        )

    def render_top_back_button(self, label, target_page, key, reset_callback=None):
        if st.button(label, key=key, use_container_width=False):
            if reset_callback:
                reset_callback()
            self.go_to_page(target_page)

    def run(self):
        self.configure_page()
        self.apply_base_styles()
        self.setup_session_state()
        self.configure_openai_from_secrets()

        for warning in self.data.data_load_warnings:
            st.warning(warning)

        if st.session_state["logged_in"] and isinstance(st.session_state["user"], dict):
            if st.session_state["user"].get("role") == "Agent":
                self.show_main_app_agent()
            elif st.session_state["user"].get("role") == "Buyer":
                self.show_main_app_buyer()
            else:
                self.show_login_page()
        else:
            self.show_login_page()

    def render_page_header(self, title, caption=None):
        caption_html = f'<p class="page-caption">{self.escape(caption)}</p>' if caption else ""
        st.markdown(
            f"""
            <div class="page-header">
                <div class="page-title">{self.escape(title)}</div>
                {caption_html}
            </div>
            """,
            unsafe_allow_html=True
        )

    def render_section_title(self, title):
        st.markdown(f'<div class="section-title">{self.escape(title)}</div>', unsafe_allow_html=True)

    def status_class(self, status):
        normalized = str(status).strip().lower().replace(" ", "-")
        allowed = {"available", "pending", "sold", "confirmed", "declined", "new", "in-progress", "answered"}
        return f"status-{normalized}" if normalized in allowed else "status-default"

    def render_status_badge(self, status):
        st.markdown(
            f'<span class="status-badge {self.status_class(status)}">{self.escape(status)}</span>',
            unsafe_allow_html=True
        )

    def get_status_badge_html(self, status):
        return f'<span class="status-badge {self.status_class(status)}">{self.escape(status)}</span>'

    def render_metric_card(self, label, value, icon=""):
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-icon">{self.escape(icon)}</div>
                <div class="metric-label">{self.escape(label)}</div>
                <div class="metric-value">{self.escape(value)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    def render_empty_state(self, title, message, icon="ℹ️"):
        st.markdown(
            f"""
            <div class="empty-state-card">
                <div class="empty-state-icon">{self.escape(icon)}</div>
                <div class="empty-state-title">{self.escape(title)}</div>
                <p class="empty-state-message">{self.escape(message)}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    def render_delete_confirmation(self, state_key, record_id, message, confirm_key, cancel_key, delete_callback, after_delete_callback=None):
        if st.session_state.get(state_key) != record_id:
            return

        st.markdown(
            f"""
            <div class="confirm-box">
                <div class="confirm-title">Confirm Delete</div>
                <p class="confirm-message">{self.escape(message)}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Yes, Delete", key=confirm_key, use_container_width=True):
                success, response_message = delete_callback()
                if success:
                    st.success(response_message)
                    st.session_state[state_key] = None
                    if after_delete_callback:
                        after_delete_callback()
                    self.rerun()
                else:
                    st.error(response_message)
        with col_no:
            if st.button("Cancel", key=cancel_key, use_container_width=True):
                st.session_state[state_key] = None
                self.rerun()

    def render_stat_card(self, title, value):
        self.render_metric_card(title, value)

    def render_listing_card(self, listing, button_label, button_key, next_page, selected_key, show_favorite=False):
        st.markdown(
            f"""
            <div class="listing-card">
                {self.render_listing_image_html(listing)}
                <div class="listing-card-top">
                    <div>
                        <div class="listing-title">{self.escape(listing.get('title', 'Untitled Listing'))}</div>
                        <p class="listing-address">{self.escape(listing.get('address', ''))}, {self.escape(listing.get('city', ''))}, {self.escape(listing.get('state', ''))}</p>
                    </div>
                    <div>
                        <div class="listing-price">{self.format_price(listing.get('price', 0))}</div>
                        {self.get_status_badge_html(listing.get('status', ''))}
                    </div>
                </div>
                <div class="listing-facts">
                    🛏️ {self.escape(listing.get('bedrooms', 0))} Beds &nbsp; 
                    🛁 {self.escape(listing.get('bathrooms', 0))} Baths &nbsp; 
                    📐 {self.escape(listing.get('property_sqft', 0))} sqft &nbsp; 
                    🏠 {self.escape(listing.get('property_type', ''))}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        col_view, col_save = st.columns([2, 1]) if show_favorite else (None, None)
        if show_favorite:
            with col_view:
                if st.button(button_label, key=button_key, type="primary", use_container_width=True):
                    st.session_state[selected_key] = listing["id"]
                    st.session_state["page"] = next_page
                    self.rerun()
            with col_save:
                self.render_save_listing_button(listing)
        else:
            if st.button(button_label, key=button_key, type="primary", use_container_width=True):
                st.session_state[selected_key] = listing["id"]
                st.session_state["page"] = next_page
                self.rerun()

    def render_listing_detail_sections(self, selected_listing, description_writer="markdown"):
        st.markdown(self.render_listing_image_html(selected_listing, detail=True), unsafe_allow_html=True)
        with st.container(border=True):
            col_left, col_right = st.columns([3, 1])
            with col_left:
                st.markdown(f"### {selected_listing['title']}")
                st.markdown(f"**{selected_listing['address']}, {selected_listing['city']}, {selected_listing['state']}**")
            with col_right:
                self.render_status_badge(selected_listing["status"])
                st.markdown(f"### {self.format_price(selected_listing['price'])}")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            self.render_metric_card("Bedrooms", selected_listing["bedrooms"], "🛏️")
        with col2:
            self.render_metric_card("Bathrooms", selected_listing["bathrooms"], "🛁")
        with col3:
            self.render_metric_card("Square Feet", selected_listing["property_sqft"], "📐")
        with col4:
            self.render_metric_card("Property Type", selected_listing["property_type"], "🏠")

        with st.container(border=True):
            st.markdown("### Description")
            if description_writer == "write":
                st.write(selected_listing["description"])
            else:
                st.markdown(selected_listing["description"])

        with st.container(border=True):
            st.markdown("### Contact Information")
            st.markdown(f"**Name:** {selected_listing['contact_name']}")
            st.markdown(f"**Email:** {selected_listing['contact_email']}")
            st.markdown(f"**Phone:** {selected_listing['contact_phone']}")

    def generate_chatbot_response(self, role, user_input, chat_key):
        return self.service.get_openai_chatbot_response(
            role=role,
            user_input=user_input,
            messages=st.session_state.get(chat_key, []),
            current_user=self.current_user()
        )

    def show_chat_bot(self, role):
        if role == "Agent":
            chat_key = "agent_chatbot"
            input_version_key = "agent_chat_input_version"
            title = "### 🤖 Agent Assistant"
            suggestions = [
                "What should I do next?",
                "Summarize my pending requests",
                "Which listings are available?",
                "Where do I view buyer requests?"
            ]
            default_message = "Hi! I’m your agent assistant. Ask me about listings, buyer requests, or adding a property."
        else:
            chat_key = "buyer_chatbot"
            input_version_key = "buyer_chat_input_version"
            title = "### 🤖 Buyer Assistant"
            suggestions = [
                "What should I do next?",
                "Which listings should I save?",
                "How do I book an appointment?",
                "Do I have any answered inquiries?"
            ]
            default_message = "Hi! I’m your buyer assistant. Ask me about browsing listings, booking appointments, or sending inquiries."

        with st.container(border=True):
            st.markdown(title)
            if self.service.openai_is_ready():
                st.caption(f"OpenAI connected with model: {self.service.openai_model}. Choose a suggested question or type your own below.")
            else:
                st.caption("OpenAI is not configured yet, so the assistant is using the built-in fallback responses.")

            with st.expander("OpenAI connection debug", expanded=False):
                st.caption(f"OpenAI SDK installed: {OpenAI is not None}")
                st.caption(f"OpenAI key found: {bool(self.service.openai_api_key)}")
                st.caption(f"OpenAI client ready: {self.service.openai_client is not None}")
                if self.service.last_openai_error:
                    st.caption(f"Last OpenAI error: {self.service.last_openai_error}")

            suggestion_columns = st.columns(len(suggestions))

            for index, column in enumerate(suggestion_columns, start=1):
                if column.button(suggestions[index - 1], key=f"{role.lower()}_chat_suggestion_btn_{index}", use_container_width=True):
                    user_input = suggestions[index - 1]
                    st.session_state[chat_key].append({"role": "user", "content": user_input})
                    with st.spinner("AI assistant is typing..."):
                        response = self.generate_chatbot_response(role, user_input, chat_key)
                    st.session_state[chat_key].append({"role": "assistant", "content": response})
                    self.rerun()

            st.divider()
            with st.container(border=True, height=260):
                for message in st.session_state[chat_key]:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

            st.divider()
            chat_input_key = f"{role.lower()}_chat_text_input_{st.session_state[input_version_key]}"
            col_input, col_send = st.columns([4, 1])
            with col_input:
                user_input = st.text_input("Ask a question...", key=chat_input_key, label_visibility="collapsed", placeholder="Ask a question...")
            with col_send:
                send_clicked = st.button("Send", key=f"{role.lower()}_chat_send_btn", type="primary", use_container_width=True)

            if send_clicked:
                user_input = user_input.strip()
                if user_input:
                    st.session_state[chat_key].append({"role": "user", "content": user_input})
                    with st.spinner("AI assistant is typing..."):
                        response = self.generate_chatbot_response(role, user_input, chat_key)
                    st.session_state[chat_key].append({"role": "assistant", "content": response})
                    st.session_state[input_version_key] += 1
                    self.rerun()

            if st.button("Clear Chat", key=f"{role.lower()}_chat_clear_bottom_btn", use_container_width=True):
                st.session_state[chat_key] = [{"role": "assistant", "content": default_message}]
                st.session_state[input_version_key] += 1
                self.rerun()

    def show_login_page(self):
        self.render_page_header("Real Estate Finder", "Browse listings, book appointments, and connect with agents.")
        tab1, tab2 = st.tabs(["Log In", "Register"])

        with tab1:
            with st.container(border=True):
                st.markdown("## Welcome Back")
                email_login = st.text_input("Email", placeholder="Enter your email", key="login_email")
                password_login = st.text_input("Password", type="password", key="login_password")
                btn_login = st.button("Log In", key="auth_login_submit_btn", use_container_width=True, type="primary")

                if btn_login:
                    if not email_login or not password_login:
                        st.warning("Please enter your email and password.")
                        st.stop()
                    with st.spinner("Verifying credentials..."):
                        time.sleep(0.5)
                    login_check = self.service.authenticate_user(email_login, password_login)
                    if login_check:
                        st.session_state["logged_in"] = True
                        st.session_state["user"] = login_check
                        st.session_state["page"] = "home"
                        self.rerun()
                    else:
                        st.error("Invalid email or password.")

        with tab2:
            with st.container(border=True):
                st.markdown("## Create Account")
                full_name = st.text_input("Full Name", placeholder="Enter your full name", key="full_name_new")
                email = st.text_input("Email", placeholder="Enter your email", key="email_new")
                password = st.text_input("Password", type="password", key="password_new")
                role = st.selectbox("Role", ["Agent", "Buyer"], key="role_new")
                btn_create = st.button("Create Account", key="auth_register_submit_btn", use_container_width=True, type="primary")

                if btn_create:
                    with st.spinner("Creating account..."):
                        time.sleep(0.5)
                    success, message, user = self.service.create_user(full_name, email, password, role)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                        st.stop()

    def show_main_app_agent(self):
        page = st.session_state["page"]
        if page == "home":
            self.show_agent_dashboard()
        elif page == "properties_listings":
            self.show_agent_properties_page()
        elif page == "manage_listing":
            self.show_agent_manage_listing_page()
        elif page == "edit_listing":
            self.show_agent_edit_listing_page()
        elif page == "view_other_listing_details":
            self.show_agent_other_listing_details_page()
        elif page == "add_listings":
            self.show_agent_add_listing_page()
        elif page == "buyer_inquiries":
            self.show_agent_buyer_requests_page()
        self.render_agent_sidebar()

    def show_agent_dashboard(self):
        user = self.current_user()
        stats = self.service.calculate_agent_dashboard_stats(user["id"])
        self.render_page_header(f"Agent Dashboard - {user['full_name']}", "Manage listings, review buyer bookings, and respond to inquiries.")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            self.render_metric_card("My Listings", stats["my_listings_count"], "🏘️")
        with col2:
            self.render_metric_card("Available Listings", stats["available_listings_count"], "✅")
        with col3:
            self.render_metric_card("Pending Bookings", stats["pending_bookings_count"], "📅")
        with col4:
            self.render_metric_card("New Inquiries", stats["new_inquiries_count"], "💬")

        self.render_section_title("Quick Actions")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("View My Listings", key="agent_home_view_listings_btn", type="primary", use_container_width=True):
                self.go_to_page("properties_listings")
        with col_b:
            if st.button("Add New Listing", key="agent_home_add_listing_btn", use_container_width=True):
                self.go_to_page("add_listings")
        with col_c:
            if st.button("View Buyer Requests", key="agent_home_buyer_requests_btn", use_container_width=True):
                self.go_to_page("buyer_inquiries")

        self.render_agent_next_steps(stats)
        self.render_section_title("Assistant")
        self.show_chat_bot("Agent")
        self.render_agent_recent_activity(stats)

    def render_agent_recent_activity(self, stats):
        self.render_section_title("Recent Activity")
        latest_listing = stats["agent_listings"][-1] if stats["agent_listings"] else None
        latest_booking = stats["agent_bookings"][-1] if stats["agent_bookings"] else None
        latest_inquiry = stats["agent_inquiries"][-1] if stats["agent_inquiries"] else None

        if latest_listing:
            with st.container(border=True):
                st.markdown("**Latest Listing**")
                st.markdown(f"**Title:** {latest_listing['title']}")
                self.render_status_badge(latest_listing["status"])
                st.markdown(f"**Price:** {self.format_price(latest_listing['price'])}")
        if latest_booking:
            with st.container(border=True):
                st.markdown("**Latest Booking Request**")
                st.markdown(f"**Property:** {latest_booking['property_title']}")
                st.markdown(f"**Buyer:** {latest_booking['buyer_name']}")
                self.render_status_badge(latest_booking["status"])
        if latest_inquiry:
            with st.container(border=True):
                st.markdown("**Latest Inquiry**")
                st.markdown(f"**Property:** {latest_inquiry['property_title']}")
                st.markdown(f"**Buyer:** {latest_inquiry['buyer_name']}")
                self.render_status_badge(latest_inquiry["status"])
        if not latest_listing and not latest_booking and not latest_inquiry:
            self.render_empty_state("No recent activity yet", "Start by adding your first listing.", "🏠")

    def show_agent_properties_page(self):
        user = self.current_user()
        my_listings_all = self.service.get_agent_listings(user["id"])
        other_listings_all = [listing for listing in self.data.properties if listing.get("agent_id") != user["id"]]

        self.render_page_header("View Property Listings", "Manage your listings and review properties posted by other agents.")
        tablist, taball = st.tabs([
            f"My Property Listings ({len(my_listings_all)})",
            f"Other Property Listings ({len(other_listings_all)})"
        ])

        with tablist:
            self.render_section_title("My Listings")
            selected_type_my, selected_status_my, search_my, sort_my = self.render_listing_filter_controls(
                "my_type_filter", "my_status_filter", "my_listing_search", "my_listing_sort", self.LISTING_STATUSES
            )
            self.render_active_filter_summary(selected_type_my, selected_status_my, search_my, sort_my)
            filtered_my_listings = self.service.filter_listings(my_listings_all, selected_type_my, selected_status_my, search_text=search_my)
            filtered_my_listings = self.service.sort_listings(filtered_my_listings, sort_my)
            st.markdown(f"#### My Total Listings: {len(filtered_my_listings)}")
            if not filtered_my_listings:
                self.render_empty_state("No matching listings", "Try adjusting your search, filters, or sort option.", "🔍")
            else:
                self.render_listing_grid(filtered_my_listings, "Manage Listing", "manage_listing_btn", "manage_listing", "selected_agent_listing_id")

        with taball:
            self.render_section_title("Other Agent Listings")
            selected_type, selected_status, search_other, sort_other = self.render_listing_filter_controls(
                "all_type_filter", "all_status_filter", "other_listing_search", "other_listing_sort", self.LISTING_STATUSES
            )
            self.render_active_filter_summary(selected_type, selected_status, search_other, sort_other)
            filtered_properties = self.service.filter_listings(
                self.data.properties,
                selected_type,
                selected_status,
                exclude_agent_id=user["id"],
                search_text=search_other
            )
            filtered_properties = self.service.sort_listings(filtered_properties, sort_other)
            st.markdown(f"#### Total Other Listings: {len(filtered_properties)}")
            if not filtered_properties:
                self.render_empty_state("No matching listings", "Try adjusting your search, filters, or sort option.", "🔍")
            else:
                self.render_listing_grid(filtered_properties, "View Listing Details", "view_other_listing_btn", "view_other_listing_details", "selected_other_listing_id")

    def show_agent_manage_listing_page(self):
        selected_listing = self.service.find_listing_by_id(st.session_state["selected_agent_listing_id"])
        if selected_listing is None:
            st.error("Listing not found.")
            return

        self.render_top_back_button("← Back to My Listings", "properties_listings", "top_back_manage_listing")
        self.render_page_header("Manage Listing", "Update, review, or delete this property listing.")
        self.render_listing_detail_sections(selected_listing)
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("Update Listing", key=f"edit_listing_{selected_listing['id']}", type="primary", use_container_width=True):
                self.go_to_page("edit_listing")
        with col_btn2:
            if st.button("Delete Listing", key=f"delete_listing_{selected_listing['id']}", use_container_width=True):
                st.session_state["confirm_delete_listing_id"] = selected_listing["id"]
                self.rerun()
        with col_btn3:
            if st.button("Back to My Listings", key="back_to_my_listings", use_container_width=True):
                self.go_to_page("properties_listings")

        self.render_delete_confirmation(
            "confirm_delete_listing_id",
            selected_listing["id"],
            "Are you sure you want to delete this listing? This cannot be undone.",
            f"confirm_delete_listing_{selected_listing['id']}",
            f"cancel_delete_listing_{selected_listing['id']}",
            lambda: self.service.delete_listing(selected_listing["id"]),
            after_delete_callback=lambda: self.after_listing_deleted()
        )

    def after_listing_deleted(self):
        st.session_state["selected_agent_listing_id"] = None
        st.session_state["page"] = "properties_listings"

    def show_agent_edit_listing_page(self):
        selected_listing = self.service.find_listing_by_id(st.session_state["selected_agent_listing_id"])
        if selected_listing is None:
            st.error("Listing not found.")
            return

        self.render_top_back_button("← Back to Listing", "manage_listing", f"top_back_edit_listing_{selected_listing['id']}")
        self.render_page_header("Update Listing", "Edit property details, pricing, status, and contact information.")

        with st.expander("Listing Overview", expanded=True):
            title = st.text_input("Listing Title", value=selected_listing["title"])
            st.caption("Use a clear title buyers can quickly understand.")
            description = st.text_area("Description", value=selected_listing["description"])
            st.caption("Mention the most important features, location benefits, and property highlights.")
            image_url = st.text_input("Property Image URL", value=selected_listing.get("image_url", ""), placeholder="https://example.com/property-photo.jpg")
            st.caption("Optional: paste your own image URL. If left blank, the app automatically uses a stock property photo.")

        with st.expander("Contact Information", expanded=True):
            contact_name = st.text_input("Contact Name", value=selected_listing["contact_name"])
            contact_email = st.text_input("Contact Email", value=selected_listing["contact_email"])
            st.caption("Use an email address buyers can contact.")
            contact_phone = st.text_input("Contact Phone Number", value=selected_listing["contact_phone"])
            st.caption("Enter 10 digits, no dashes.")

        with st.expander("Location", expanded=True):
            address = st.text_input("Street Address", value=selected_listing["address"])
            col_city, col_state = st.columns(2)
            with col_city:
                city = st.text_input("City", value=selected_listing["city"])
            with col_state:
                state = st.text_input("State", value=selected_listing["state"])

        with st.expander("Property Details", expanded=True):
            col_a, col_b = st.columns(2)
            with col_a:
                price = st.number_input("Price", min_value=1, value=int(selected_listing["price"]))
                st.caption("Enter whole dollar amount only.")
                bedrooms = st.number_input("Bedrooms", min_value=0, step=1, value=int(selected_listing["bedrooms"]))
                property_type = st.selectbox("Property Type", self.PROPERTY_TYPES, index=self.PROPERTY_TYPES.index(selected_listing["property_type"]))
            with col_b:
                bathrooms = st.number_input("Bathrooms", min_value=0, step=1, value=int(selected_listing["bathrooms"]))
                property_sqft = st.number_input("Property Square Footage", min_value=1, step=1, value=int(selected_listing["property_sqft"]))
                status = st.selectbox("Status", self.LISTING_STATUSES, index=self.LISTING_STATUSES.index(selected_listing["status"]))

        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.button("Save Changes", key=f"save_listing_{selected_listing['id']}", type="primary", use_container_width=True):
                updates = {
                    "title": title,
                    "description": description,
                    "image_url": image_url,
                    "contact_name": contact_name,
                    "contact_email": contact_email,
                    "contact_phone": contact_phone,
                    "address": address,
                    "city": city,
                    "state": state,
                    "price": price,
                    "bedrooms": bedrooms,
                    "bathrooms": bathrooms,
                    "property_sqft": property_sqft,
                    "property_type": property_type,
                    "status": status,
                }
                success, message, updated_listing = self.service.update_listing(selected_listing["id"], updates)
                if success:
                    self.render_success_summary(
                        message,
                        [
                            f"Title: {updated_listing['title']}",
                            f"Price: {self.format_price(updated_listing['price'])}",
                            f"Status: {updated_listing['status']}",
                        ]
                    )
                    time.sleep(0.5)
                    self.go_to_page("manage_listing")
                else:
                    st.error(message)
                    st.stop()
        with col_cancel:
            if st.button("Cancel", key=f"cancel_edit_listing_{selected_listing['id']}", use_container_width=True):
                self.go_to_page("manage_listing")

    def show_agent_other_listing_details_page(self):
        selected_listing = self.service.find_listing_by_id(st.session_state["selected_other_listing_id"])
        if selected_listing is None:
            st.error("Listing not found.")
            return

        self.render_top_back_button("← Back to Other Listings", "properties_listings", "top_back_other_listing", reset_callback=lambda: st.session_state.update({"selected_other_listing_id": None}))
        self.render_page_header("View Listing Details", "Review another agent’s property listing.")
        self.render_listing_detail_sections(selected_listing)
        if st.button("Back to Other Listings", key="back_to_other_agent_listings", use_container_width=True):
            st.session_state["selected_other_listing_id"] = None
            self.go_to_page("properties_listings")

    def show_agent_add_listing_page(self):
        user = self.current_user()
        self.render_page_header("Add New Listing", "Create a new property listing for buyers to view, book, and inquire about.")

        with st.expander("Listing Overview", expanded=True):
            title = st.text_input("Listing Title", placeholder="Ex: Modern 4 Bedroom Family Home")
            st.caption("Use a clear title buyers can quickly understand.")
            description = st.text_area("Description", placeholder="Write a short description of the property")
            st.caption("Mention the most important features, location benefits, and property highlights.")
            image_url = st.text_input("Property Image URL", placeholder="https://example.com/property-photo.jpg")
            st.caption("Optional: paste your own image URL. If left blank, the app automatically uses a stock property photo.")

        with st.expander("Property Details", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                property_type = st.selectbox("Property Type", self.PROPERTY_TYPES)
                price = st.number_input("Price", min_value=1)
                st.caption("Enter whole dollar amount only.")
                bedrooms = st.number_input("Bedrooms", min_value=0, step=1)
            with col2:
                status = st.selectbox("Status", self.LISTING_STATUSES)
                bathrooms = st.number_input("Bathrooms", min_value=0, step=1)
                property_sqft = st.number_input("Property Square Footage", min_value=1, step=1)

        with st.expander("Property Location", expanded=True):
            address = st.text_input("Street Address", placeholder="Enter street address")
            col1, col2 = st.columns(2)
            with col1:
                city = st.text_input("City", placeholder="Enter city")
            with col2:
                state = st.text_input("State", placeholder="Enter state")

        with st.expander("Contact Information", expanded=True):
            contact_name = st.text_input("Contact Name", placeholder="John Doe")
            col1, col2 = st.columns(2)
            with col1:
                contact_email = st.text_input("Contact Email", placeholder="name@email.com")
                st.caption("Use an email address buyers can contact.")
            with col2:
                contact_phone = st.text_input("Contact Phone Number", placeholder="3025551234")
                st.caption("Enter 10 digits, no dashes.")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            btn_add_listing = st.button("Add Listing", key="agent_add_listing_submit_btn", type="primary", use_container_width=True)
        with col_btn2:
            btn_cancel_listing = st.button("Cancel", key="agent_cancel_listing_submit_btn", use_container_width=True)

        if btn_cancel_listing:
            self.go_to_page("properties_listings")

        if btn_add_listing:
            with st.spinner("Listing is being created..."):
                time.sleep(0.5)
            success, message, listing = self.service.create_listing(
                user["id"], title, description, address, city, state, price,
                bedrooms, bathrooms, property_sqft, property_type, status,
                contact_name, contact_email, contact_phone, image_url
            )
            if success:
                self.render_success_summary(
                    message,
                    [
                        f"Title: {listing['title']}",
                        f"Price: {self.format_price(listing['price'])}",
                        f"Status: {listing['status']}",
                    ]
                )
                st.balloons()
                time.sleep(0.5)
                self.go_to_page("properties_listings")
            else:
                st.error(message)
                st.stop()

    def show_agent_buyer_requests_page(self):
        user = self.current_user()
        agent_bookings = self.service.get_agent_bookings(user["id"])
        agent_inquiries = self.service.get_agent_inquiries(user["id"])
        self.render_page_header("Buyer Bookings & Inquiries", "Confirm appointments and respond to buyer questions.")
        tab_bookings, tab_inquiries = st.tabs([
            f"View Bookings ({len(agent_bookings)})",
            f"View Inquiries ({len(agent_inquiries)})"
        ])

        with tab_bookings:
            self.render_section_title("Booking Requests")
            st.markdown(f"**Total Bookings:** {len(agent_bookings)}")
            if not agent_bookings:
                self.render_empty_state("No booking requests", "You do not have any booking requests.", "📅")
            else:
                for booking in agent_bookings:
                    self.render_agent_booking_request_card(booking)

        with tab_inquiries:
            self.render_section_title("Buyer Inquiries")
            st.markdown(f"**Total Inquiries:** {len(agent_inquiries)}")
            if not agent_inquiries:
                self.render_empty_state("No buyer inquiries", "You do not have any buyer inquiries.", "💬")
            else:
                for inquiry in agent_inquiries:
                    self.render_agent_inquiry_card(inquiry)

    def render_agent_booking_request_card(self, booking):
        with st.container(border=True):
            col_left, col_right = st.columns([3, 1])
            with col_left:
                st.markdown(f"### {booking['property_title']}")
                st.markdown("**Buyer Info**")
                st.markdown(f"**Buyer:** {booking['buyer_name']}")
                st.markdown(f"**Email:** {booking['buyer_email']}")
                st.markdown(f"**Phone:** {booking['buyer_phone']}")
                st.markdown("**Appointment Details**")
                st.markdown(f"**Appointment Type:** {booking['appointment_type']}")
                st.markdown(f"**Date:** {booking['appointment_date']}")
                st.markdown(f"**Time:** {booking['appointment_time']}")
            with col_right:
                self.render_status_badge(booking["status"])
            st.markdown(f"**Notes:** {booking['message'] if booking['message'] else 'No additional notes provided.'}")
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Confirm Appointment", key=f"confirm_booking_{booking['id']}", type="primary", use_container_width=True):
                    success, message, _ = self.service.update_booking_status(booking["id"], "Confirmed")
                    st.success("Appointment confirmed successfully!" if success else message)
                    self.rerun()
            with col2:
                if st.button("Decline Appointment", key=f"decline_booking_{booking['id']}", use_container_width=True):
                    success, message, _ = self.service.update_booking_status(booking["id"], "Declined")
                    st.success("Appointment declined." if success else message)
                    self.rerun()

    def render_agent_inquiry_card(self, inquiry):
        with st.container(border=True):
            col_left, col_right = st.columns([3, 1])
            with col_left:
                st.markdown(f"### {inquiry['property_title']}")
                st.markdown("**Buyer Info**")
                st.markdown(f"**Buyer:** {inquiry['buyer_name']}")
                st.markdown(f"**Email:** {inquiry['buyer_email']}")
                st.markdown(f"**Phone:** {inquiry['buyer_phone']}")
                st.markdown("**Inquiry Details**")
                st.markdown(f"**Subject:** {inquiry['subject']}")
                st.markdown(f"**Question:** {inquiry['message']}")
            with col_right:
                self.render_status_badge(inquiry["status"])
            if inquiry.get("response"):
                st.markdown("**Current Response:**")
                st.markdown(inquiry["response"])
            st.divider()
            if st.button("Respond to Inquiry", key=f"edit_agent_inquiry_{inquiry['id']}", use_container_width=True):
                st.session_state["edit_agent_inquiry_id"] = inquiry["id"]
                self.rerun()
            if st.session_state["edit_agent_inquiry_id"] == inquiry["id"]:
                self.render_agent_inquiry_update_form(inquiry)

    def render_agent_inquiry_update_form(self, inquiry):
        with st.container(border=True):
            st.markdown("### Update Inquiry")
            statuses = ["New", "In Progress", "Answered"]
            updated_status = st.selectbox(
                "Status", statuses,
                index=statuses.index(inquiry["status"]) if inquiry["status"] in statuses else 0,
                key=f"agent_inquiry_status_{inquiry['id']}"
            )
            updated_response = st.text_area(
                "Response to Buyer", value=inquiry.get("response", ""),
                placeholder="Type your answer here", key=f"agent_inquiry_response_{inquiry['id']}"
            )
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("Save Response", key=f"save_agent_inquiry_{inquiry['id']}", type="primary", use_container_width=True):
                    success, message, _ = self.service.update_agent_inquiry_response(inquiry["id"], updated_status, updated_response)
                    if success:
                        st.success(message)
                        st.session_state["edit_agent_inquiry_id"] = None
                        self.rerun()
                    else:
                        st.error(message)
                        st.stop()
            with col_cancel:
                if st.button("Cancel", key=f"cancel_agent_inquiry_{inquiry['id']}", use_container_width=True):
                    st.session_state["edit_agent_inquiry_id"] = None
                    self.rerun()

    def render_agent_sidebar(self):
        with st.sidebar:
            st.markdown("# **Navigator**")
            if st.button("🏠 Dashboard", key="agent_nav_dashboard_btn", type="primary", use_container_width=True):
                self.go_to_page("home")
            if st.button("🔍 View/Manage Property Listings", key="agent_nav_properties_btn", type="primary", use_container_width=True):
                self.go_to_page("properties_listings")
            if st.button("➕ Add Property Listings", key="agent_nav_add_listing_btn", type="primary", use_container_width=True):
                self.go_to_page("add_listings")
            if st.button("📖 Buyer Bookings & Inquiries", key="agent_nav_buyer_requests_btn", type="primary", use_container_width=True):
                self.go_to_page("buyer_inquiries")
            self.render_sidebar_user_card()
            if st.button("🚪 Log Out", key="agent_nav_logout_btn", type="primary", use_container_width=True):
                st.session_state["logged_in"] = False
                st.session_state["user"] = None
                st.session_state["page"] = "home"
                st.session_state["selected_agent_listing_id"] = None
                st.session_state["selected_other_listing_id"] = None
                st.success("Logout Succesful")
                time.sleep(0.5)
                self.rerun()

    def show_main_app_buyer(self):
        page = st.session_state["page"]
        if page == "home":
            self.show_buyer_dashboard()
        elif page == "browse_listings":
            self.show_buyer_browse_listings_page()
        elif page == "view_listing_details":
            self.show_buyer_listing_details_page()
        elif page == "my_inquiries":
            self.show_buyer_bookings_inquiries_page()
        elif page == "saved_listings":
            self.show_buyer_saved_listings_page()
        self.render_buyer_sidebar()

    def show_buyer_dashboard(self):
        user = self.current_user()
        stats = self.service.calculate_buyer_dashboard_stats(user["id"])
        self.render_page_header(f"Buyer Dashboard - {user['full_name']}", "Browse listings, book appointments, and manage your inquiries.")

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            self.render_metric_card("Available Listings", stats["available_listings"], "🏠")
        with col2:
            self.render_metric_card("Saved Listings", stats["saved_listings"], "⭐")
        with col3:
            self.render_metric_card("My Bookings", stats["my_bookings"], "📅")
        with col4:
            self.render_metric_card("Pending Bookings", stats["pending_bookings"], "⏳")
        with col5:
            self.render_metric_card("My Inquiries", stats["my_inquiries"], "💬")

        self.render_section_title("Quick Actions")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("Browse Listings", key="buyer_home_browse_btn", type="primary", use_container_width=True):
                self.go_to_page("browse_listings")
        with col_b:
            if st.button("View My Bookings & Inquiries", key="buyer_home_requests_btn", use_container_width=True):
                self.go_to_page("my_inquiries")
        with col_c:
            if st.button("View Saved Listings", key="buyer_home_saved_btn", use_container_width=True):
                self.go_to_page("saved_listings")

        self.render_buyer_next_steps(stats)
        self.render_section_title("Assistant")
        self.show_chat_bot("Buyer")
        self.render_buyer_recent_activity(stats)

    def render_buyer_recent_activity(self, stats):
        self.render_section_title("Recent Activity")
        latest_booking = stats["buyer_bookings"][-1] if stats["buyer_bookings"] else None
        latest_inquiry = stats["buyer_inquiries"][-1] if stats["buyer_inquiries"] else None
        if latest_booking:
            with st.container(border=True):
                st.markdown("**Latest Booking**")
                st.markdown(f"Property: {latest_booking['property_title']}")
                self.render_status_badge(latest_booking["status"])
                st.markdown(f"Date: {latest_booking['appointment_date']}")
        if latest_inquiry:
            with st.container(border=True):
                st.markdown("**Latest Inquiry**")
                st.markdown(f"Property: {latest_inquiry['property_title']}")
                self.render_status_badge(latest_inquiry["status"])
                st.markdown(f"Subject: {latest_inquiry['subject']}")
        if not latest_booking and not latest_inquiry:
            self.render_empty_state("No recent activity yet", "Start by browsing available listings.", "🔍")

    def show_buyer_browse_listings_page(self):
        self.render_page_header("View Property Listings", "Browse available properties and open details to book or ask questions.")
        selected_type, selected_status, search_text, sort_option = self.render_listing_filter_controls(
            "buyer_type_filter", "buyer_status_filter", "buyer_listing_search", "buyer_listing_sort", self.BUYER_STATUSES
        )

        self.render_active_filter_summary(selected_type, selected_status, search_text, sort_option)
        filtered_properties = self.service.filter_listings(
            self.data.properties,
            selected_type,
            selected_status,
            buyer_visible_only=True,
            search_text=search_text
        )
        filtered_properties = self.service.sort_listings(filtered_properties, sort_option)
        st.markdown(f"#### Total Available Listings: {len(filtered_properties)}")
        if not filtered_properties:
            self.render_empty_state("No matching listings", "Try adjusting your search, filters, or sort option.", "🔍")
        else:
            self.render_listing_grid(filtered_properties, "View Listing Details", "view_listing_btn", "view_listing_details", "selected_listing_id", show_favorite=True)

    def show_buyer_listing_details_page(self):
        selected_listing = self.service.find_listing_by_id(st.session_state["selected_listing_id"])
        if selected_listing is None:
            st.error("Listing not found.")
            return

        self.render_top_back_button("← Back to Listings", "browse_listings", "top_back_buyer_listing", reset_callback=lambda: st.session_state.update({"booking_listing_id": None, "question_listing_id": None}))
        self.render_page_header("View Listing Details", "Review property information, book an appointment, or ask the agent a question.")
        self.render_listing_detail_sections(selected_listing, description_writer="write")

        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
        with col_btn1:
            if st.button("Book an Appointment", key=f"details_book_{selected_listing['id']}", type="primary", use_container_width=True):
                st.session_state["booking_listing_id"] = selected_listing["id"]
                self.rerun()
        with col_btn2:
            if st.button("Ask a Question(s)", key=f"details_question_{selected_listing['id']}", use_container_width=True):
                st.session_state["question_listing_id"] = selected_listing["id"]
                self.rerun()
        with col_btn3:
            self.render_save_listing_button(selected_listing)
        with col_btn4:
            if st.button("Back to Listings", key="buyer_details_back_btn", use_container_width=True):
                st.session_state["page"] = "browse_listings"
                st.session_state["booking_listing_id"] = None
                self.rerun()

        if st.session_state["booking_listing_id"] == selected_listing["id"]:
            self.render_booking_form(selected_listing)
        if st.session_state["question_listing_id"] == selected_listing["id"]:
            self.render_question_form(selected_listing)

    def render_booking_form(self, selected_listing):
        user = self.current_user()
        with st.container(border=True):
            st.markdown("### Appointment Form")
            appointment_name = st.text_input("Full Name", value=user["full_name"], key=f"appointment_name_{selected_listing['id']}")
            appointment_email = st.text_input("Email", value=user["email"], key=f"appointment_email_{selected_listing['id']}")
            appointment_phone = st.text_input("Phone Number", key=f"appointment_phone_{selected_listing['id']}")
            st.caption("Enter 10 digits, no dashes.")
            appointment_type = st.selectbox("Appointment Type", ["Select Type"] + self.APPOINTMENT_TYPES, key=f"appointment_type_{selected_listing['id']}")
            appointment_date = st.date_input("Preferred Appointment Date", key=f"appointment_date_{selected_listing['id']}")
            appointment_time = st.time_input("Preferred Appointment Time", key=f"appointment_time_{selected_listing['id']}")
            st.write("Selected Time:", appointment_time.strftime("%I:%M %p"))
            st.caption("Appointments must be between 8:00 AM and 5:00 PM.")
            appointment_message = st.text_area("Notes (Optional)", placeholder="Add any details or preferences here", key=f"appointment_message_{selected_listing['id']}")
            col_submit, col_cancel = st.columns(2)
            with col_submit:
                btn_submit_appointment = st.button("Submit Appointment", key=f"submit_appointment_{selected_listing['id']}", type="primary", use_container_width=True)
            with col_cancel:
                btn_cancel_appointment = st.button("Cancel", key=f"cancel_appointment_{selected_listing['id']}", use_container_width=True)

            if btn_cancel_appointment:
                st.session_state["booking_listing_id"] = None
                self.rerun()
            if btn_submit_appointment:
                with st.spinner("Submitting appointment..."):
                    time.sleep(0.5)
                success, message, booking = self.service.create_booking(
                    selected_listing, user, appointment_name, appointment_email,
                    appointment_phone, appointment_type, appointment_date,
                    appointment_time, appointment_message
                )
                if success:
                    self.render_success_summary(message, [f"Property: {selected_listing['title']}", f"Date: {appointment_date}", f"Time: {appointment_time.strftime('%I:%M %p')}"])
                    st.session_state["booking_listing_id"] = None
                    self.rerun()
                else:
                    st.error(message)
                    st.stop()

    def render_question_form(self, selected_listing):
        user = self.current_user()
        with st.container(border=True):
            st.markdown("### Question Form")
            question_name = st.text_input("Full Name", value=user["full_name"], key=f"question_name_{selected_listing['id']}")
            question_email = st.text_input("Email", value=user["email"], key=f"question_email_{selected_listing['id']}")
            question_phone = st.text_input("Phone Number", key=f"question_phone_{selected_listing['id']}")
            st.caption("Enter 10 digits, no dashes.")
            question_subject = st.selectbox("Subject", ["Select Subject"] + self.QUESTION_SUBJECTS, key=f"question_subject_{selected_listing['id']}")
            question_message = st.text_area("Question", placeholder="Type your question here", key=f"question_message_{selected_listing['id']}")
            col_submit_q, col_cancel_q = st.columns(2)
            with col_submit_q:
                btn_submit_question = st.button("Submit Question", key=f"submit_question_{selected_listing['id']}", type="primary", use_container_width=True)
            with col_cancel_q:
                btn_cancel_question = st.button("Cancel", key=f"cancel_question_{selected_listing['id']}", use_container_width=True)

            if btn_cancel_question:
                st.session_state["question_listing_id"] = None
                self.rerun()
            if btn_submit_question:
                with st.spinner("Submitting question..."):
                    time.sleep(0.5)
                success, message, inquiry = self.service.create_inquiry(
                    selected_listing, user, question_name, question_email,
                    question_phone, question_subject, question_message
                )
                if success:
                    self.render_success_summary(message, [f"Property: {selected_listing['title']}", f"Subject: {question_subject}"])
                    st.session_state["question_listing_id"] = None
                    self.rerun()
                else:
                    st.error(message)
                    st.stop()

    def show_buyer_saved_listings_page(self):
        user = self.current_user()
        saved_listings = self.service.get_saved_listings(user["id"])
        self.render_top_back_button("← Back to Browse Listings", "browse_listings", "top_back_saved_listings")
        self.render_page_header("Saved Listings", "Review properties you saved while browsing.")
        st.markdown(f"#### Saved Listings: {len(saved_listings)}")
        if not saved_listings:
            self.render_empty_state("No saved listings yet", "Browse listings and use the Save Listing button to build your shortlist.", "⭐")
            return

        self.render_listing_grid(
            saved_listings,
            "View Listing Details",
            "view_saved_listing_btn",
            "view_listing_details",
            "selected_listing_id",
            show_favorite=True
        )

    def show_buyer_bookings_inquiries_page(self):
        user = self.current_user()
        my_bookings = self.service.get_buyer_bookings(user["id"])
        my_inquiries = self.service.get_buyer_inquiries(user["id"])
        self.render_page_header("My Bookings & Inquiries", "Track appointment requests and questions you sent to agents.")
        tab_bookings, tab_inquiries = st.tabs([
            f"My Bookings ({len(my_bookings)})",
            f"My Inquiries ({len(my_inquiries)})"
        ])

        with tab_bookings:
            self.render_section_title("My Bookings")
            st.markdown(f"**Total Bookings:** {len(my_bookings)}")
            if not my_bookings:
                self.render_empty_state("No bookings yet", "You have not made any bookings yet.", "📅")
            else:
                for booking in my_bookings:
                    self.render_buyer_booking_card(booking)

        with tab_inquiries:
            self.render_section_title("My Inquiries")
            st.markdown(f"**Total Inquiries:** {len(my_inquiries)}")
            if not my_inquiries:
                self.render_empty_state("No inquiries yet", "You have not submitted any inquiries yet.", "💬")
            else:
                for inquiry in my_inquiries:
                    self.render_buyer_inquiry_card(inquiry)

    def render_buyer_booking_card(self, booking):
        with st.container(border=True):
            col_left, col_right = st.columns([3, 1])
            with col_left:
                st.markdown(f"### {booking['property_title']}")
                st.markdown(f"**Appointment Type:** {booking['appointment_type']}")
                st.markdown(f"**Date:** {booking['appointment_date']}")
                st.markdown(f"**Time:** {booking['appointment_time']}")
            with col_right:
                self.render_status_badge(booking["status"])
            st.markdown(f"**Notes:** {booking['message'] if booking['message'] else 'No additional notes provided.'}")
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Update Booking", key=f"edit_booking_{booking['id']}", use_container_width=True):
                    st.session_state["edit_booking_id"] = booking["id"]
                    self.rerun()
            with col2:
                if st.button("Delete Booking", key=f"delete_booking_{booking['id']}", use_container_width=True):
                    st.session_state["confirm_delete_booking_id"] = booking["id"]
                    self.rerun()

            self.render_delete_confirmation(
                "confirm_delete_booking_id",
                booking["id"],
                "Are you sure you want to delete this booking? This cannot be undone.",
                f"confirm_delete_booking_{booking['id']}",
                f"cancel_delete_booking_{booking['id']}",
                lambda: self.service.delete_booking(booking["id"])
            )

            if st.session_state["edit_booking_id"] == booking["id"]:
                self.render_buyer_booking_update_form(booking)

    def render_buyer_booking_update_form(self, booking):
        with st.container(border=True):
            st.markdown("### Update Booking")
            updated_type = st.selectbox(
                "Appointment Type", self.APPOINTMENT_TYPES,
                index=self.APPOINTMENT_TYPES.index(booking["appointment_type"]) if booking["appointment_type"] in self.APPOINTMENT_TYPES else 0,
                key=f"updated_type_{booking['id']}"
            )
            updated_date = st.date_input("Preferred Appointment Date", value=self.service.safe_parse_date(booking["appointment_date"]), key=f"updated_date_{booking['id']}")
            updated_time = st.time_input("Preferred Appointment Time", value=self.service.safe_parse_time(booking["appointment_time"]), key=f"updated_time_{booking['id']}")
            st.markdown(f"**Selected Time:** {updated_time.strftime('%I:%M %p')}")
            st.caption("Appointments must be between 8:00 AM and 5:00 PM.")
            updated_message = st.text_area("Notes", value=booking["message"], key=f"updated_message_{booking['id']}")
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("Save Changes", key=f"save_booking_{booking['id']}", type="primary", use_container_width=True):
                    success, message, _ = self.service.update_booking(booking["id"], updated_type, updated_date, updated_time, updated_message)
                    if success:
                        st.success(message)
                        st.session_state["edit_booking_id"] = None
                        self.rerun()
                    else:
                        st.error(message)
                        st.stop()
            with col_cancel:
                if st.button("Cancel", key=f"cancel_edit_booking_{booking['id']}", use_container_width=True):
                    st.session_state["edit_booking_id"] = None
                    self.rerun()

    def render_buyer_inquiry_card(self, inquiry):
        with st.container(border=True):
            col_left, col_right = st.columns([3, 1])
            with col_left:
                st.markdown(f"### {inquiry['property_title']}")
                st.markdown(f"**Subject:** {inquiry['subject']}")
                st.markdown(f"**Question:** {inquiry['message']}")
            with col_right:
                self.render_status_badge(inquiry["status"])
            st.markdown(f"**Submitted:** {inquiry.get('created_at', '')}")
            st.markdown("### Agent Response")
            if inquiry.get("response") and inquiry["response"].strip():
                st.markdown('<span class="answered-badge">Answered by agent</span>', unsafe_allow_html=True)
                st.markdown(inquiry["response"])
                if inquiry.get("response_at") and str(inquiry["response_at"]).strip():
                    st.markdown(f"**Responded:** {inquiry['response_at']}")
            else:
                st.markdown("*No response yet.*")
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Update Inquiry", key=f"edit_inquiry_{inquiry['id']}", use_container_width=True):
                    st.session_state["edit_inquiry_id"] = inquiry["id"]
                    self.rerun()
            with col2:
                if st.button("Delete Inquiry", key=f"delete_inquiry_{inquiry['id']}", use_container_width=True):
                    st.session_state["confirm_delete_inquiry_id"] = inquiry["id"]
                    self.rerun()

            self.render_delete_confirmation(
                "confirm_delete_inquiry_id",
                inquiry["id"],
                "Are you sure you want to delete this inquiry? This cannot be undone.",
                f"confirm_delete_inquiry_{inquiry['id']}",
                f"cancel_delete_inquiry_{inquiry['id']}",
                lambda: self.service.delete_inquiry(inquiry["id"])
            )

            if st.session_state["edit_inquiry_id"] == inquiry["id"]:
                self.render_buyer_inquiry_update_form(inquiry)

    def render_buyer_inquiry_update_form(self, inquiry):
        with st.container(border=True):
            st.markdown("### Update Inquiry")
            updated_subject = st.selectbox(
                "Subject", self.QUESTION_SUBJECTS,
                index=self.QUESTION_SUBJECTS.index(inquiry["subject"]) if inquiry["subject"] in self.QUESTION_SUBJECTS else 0,
                key=f"updated_subject_{inquiry['id']}"
            )
            updated_question = st.text_area("Question", value=inquiry["message"], key=f"updated_question_{inquiry['id']}")
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("Save Changes", key=f"save_inquiry_{inquiry['id']}", type="primary", use_container_width=True):
                    success, message, _ = self.service.update_buyer_inquiry(inquiry["id"], updated_subject, updated_question)
                    if success:
                        st.success(message)
                        st.session_state["edit_inquiry_id"] = None
                        self.rerun()
                    else:
                        st.error(message)
                        st.stop()
            with col_cancel:
                if st.button("Cancel", key=f"cancel_edit_inquiry_{inquiry['id']}", use_container_width=True):
                    st.session_state["edit_inquiry_id"] = None
                    self.rerun()

    def render_buyer_sidebar(self):
        with st.sidebar:
            st.markdown("# **Navigator**")
            if st.button("🏠 Dashboard", key="buyer_nav_dashboard_btn", type="primary", use_container_width=True):
                self.go_to_page("home")
            if st.button("🔍 Browse Listings", key="buyer_nav_browse_btn", type="primary", use_container_width=True):
                self.go_to_page("browse_listings")
            if st.button("📅 My Bookings & Inquiries", key="buyer_nav_requests_btn", type="primary", use_container_width=True):
                self.go_to_page("my_inquiries")
            if st.button("⭐ Saved Listings", key="buyer_nav_saved_listings_btn", type="primary", use_container_width=True):
                self.go_to_page("saved_listings")
            self.render_sidebar_user_card()
            if st.button("🚪 Log Out", key="buyer_nav_logout_btn", type="primary", use_container_width=True):
                st.session_state["logged_in"] = False
                st.session_state["user"] = None
                st.session_state["page"] = "home"
                st.session_state["booking_listing_id"] = None
                st.session_state["selected_listing_id"] = None
                st.success("Logout Succesful")
                time.sleep(0.5)
                self.rerun()




# =========================
# ENHANCED PRODUCT UI EXTENSIONS
# =========================

class EnhancedRealEstateService(RealEstateService):
    """Adds UI-supporting business logic without changing JSON storage."""

    def advanced_filter_listings(
        self,
        listings,
        selected_type="All",
        selected_status="All",
        exclude_agent_id=None,
        buyer_visible_only=False,
        search_text="",
        city="All",
        min_price=None,
        max_price=None,
        min_bedrooms=0,
        min_bathrooms=0,
        min_sqft=0,
    ):
        filtered = self.filter_listings(
            listings,
            selected_type=selected_type,
            selected_status=selected_status,
            exclude_agent_id=exclude_agent_id,
            buyer_visible_only=buyer_visible_only,
            search_text=search_text,
        )

        def safe_number(value):
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0

        results = []
        for listing in filtered:
            price = safe_number(listing.get("price"))
            bedrooms = safe_number(listing.get("bedrooms"))
            bathrooms = safe_number(listing.get("bathrooms"))
            sqft = safe_number(listing.get("property_sqft"))
            listing_city = str(listing.get("city", "")).strip()

            if city != "All" and listing_city != city:
                continue
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and max_price > 0 and price > max_price:
                continue
            if bedrooms < min_bedrooms:
                continue
            if bathrooms < min_bathrooms:
                continue
            if sqft < min_sqft:
                continue
            results.append(listing)
        return results

    def get_listing_cities(self, listings=None):
        source = listings if listings is not None else self.data.properties
        cities = sorted({str(listing.get("city", "")).strip() for listing in source if str(listing.get("city", "")).strip()})
        return ["All"] + cities

    def get_notifications(self, user):
        notifications = []
        if not isinstance(user, dict):
            return notifications

        user_id = user.get("id")
        role = user.get("role")

        if role == "Agent":
            pending_bookings = [b for b in self.get_agent_bookings(user_id) if b.get("status") == "Pending"]
            new_inquiries = [i for i in self.get_agent_inquiries(user_id) if i.get("status") == "New"]
            if pending_bookings:
                notifications.append({
                    "icon": "📅",
                    "title": f"{len(pending_bookings)} pending appointment request(s)",
                    "message": "Review and confirm or decline buyer appointment requests.",
                    "target_page": "buyer_inquiries",
                    "priority": "High",
                })
            if new_inquiries:
                notifications.append({
                    "icon": "💬",
                    "title": f"{len(new_inquiries)} new buyer question(s)",
                    "message": "Respond to buyer inquiries to keep leads moving.",
                    "target_page": "buyer_inquiries",
                    "priority": "High",
                })
            if not self.get_agent_listings(user_id):
                notifications.append({
                    "icon": "🏠",
                    "title": "No listings yet",
                    "message": "Add your first property listing so buyers can discover it.",
                    "target_page": "add_listings",
                    "priority": "Medium",
                })

        if role == "Buyer":
            buyer_bookings = self.get_buyer_bookings(user_id)
            buyer_inquiries = self.get_buyer_inquiries(user_id)
            answered_inquiries = [i for i in buyer_inquiries if str(i.get("response", "")).strip()]
            confirmed_bookings = [b for b in buyer_bookings if b.get("status") == "Confirmed"]
            pending_bookings = [b for b in buyer_bookings if b.get("status") == "Pending"]
            saved_listings = self.get_saved_listings(user_id)
            if answered_inquiries:
                notifications.append({
                    "icon": "✅",
                    "title": f"{len(answered_inquiries)} answered inquiry/inquiries",
                    "message": "An agent responded to one or more of your questions.",
                    "target_page": "my_inquiries",
                    "priority": "High",
                })
            if confirmed_bookings:
                notifications.append({
                    "icon": "📅",
                    "title": f"{len(confirmed_bookings)} confirmed appointment(s)",
                    "message": "Check your appointment details before your tour.",
                    "target_page": "my_inquiries",
                    "priority": "High",
                })
            if pending_bookings:
                notifications.append({
                    "icon": "⏳",
                    "title": f"{len(pending_bookings)} pending appointment request(s)",
                    "message": "Your request is waiting for the agent to confirm or decline.",
                    "target_page": "my_inquiries",
                    "priority": "Medium",
                })
            if not saved_listings:
                notifications.append({
                    "icon": "⭐",
                    "title": "No saved listings yet",
                    "message": "Save properties you like so you can compare them later.",
                    "target_page": "browse_listings",
                    "priority": "Medium",
                })

        if not notifications:
            notifications.append({
                "icon": "✨",
                "title": "You’re all caught up",
                "message": "No urgent app notifications right now.",
                "target_page": "home",
                "priority": "Low",
            })
        return notifications

    def group_bookings_by_date(self, bookings):
        grouped = {}
        for booking in bookings:
            date_key = str(booking.get("appointment_date", "No date"))
            grouped.setdefault(date_key, []).append(booking)
        return dict(sorted(grouped.items(), key=lambda item: item[0]))

    def update_user_profile(self, user_id, full_name, email):
        full_name = str(full_name or "").strip()
        email = self.normalize_email(str(email or ""))
        if not full_name or not email:
            return False, "Please enter your full name and email.", None
        if not self.is_valid_email(email):
            return False, "Enter a valid email address.", None

        existing_user = self.find_user_by_email(email)
        if existing_user and existing_user.get("id") != user_id:
            return False, "Another account already uses this email.", None

        updated_user = self.data.update_user(user_id, {"full_name": full_name, "email": email})
        if updated_user is None:
            return False, "User not found.", None
        return True, "Profile updated successfully.", updated_user

    def update_user_password(self, user_id, current_password, new_password, confirm_password):
        user = self.data.find_record_by_id(self.data.users, user_id)
        if user is None:
            return False, "User not found."
        if not current_password or not new_password or not confirm_password:
            return False, "Please fill in all password fields."
        if not self.verify_password(current_password, user.get("password", "")):
            return False, "Current password is incorrect."
        if new_password != confirm_password:
            return False, "New passwords do not match."
        if len(new_password) < 6:
            return False, "New password must be at least 6 characters."
        # Keep compatibility with existing plain-text passwords by storing the new value exactly as entered.
        self.data.update_user(user_id, {"password": new_password})
        return True, "Password updated successfully."


class EnhancedRealEstateUI(RealEstateUI):
    """Adds product-style UI features while reusing the original app flow."""

    def apply_base_styles(self):
        super().apply_base_styles()
        st.markdown(
            """
            <style>
            .feature-card, .notification-card, .calendar-card, .comparison-card, .profile-card, .assistant-panel, .filter-panel {
                background: var(--re-surface);
                border: 1px solid var(--re-border);
                border-radius: 22px;
                padding: 1rem 1.1rem;
                margin: 0.75rem 0;
                box-shadow: var(--re-shadow);
            }
            .notification-top, .calendar-top {
                display: flex;
                justify-content: space-between;
                gap: 1rem;
                align-items: flex-start;
            }
            .notification-icon, .calendar-icon {
                font-size: 1.35rem;
                margin-right: 0.35rem;
            }
            .notification-title, .calendar-title, .comparison-title, .assistant-title {
                font-weight: 850;
                color: var(--re-text);
                font-size: 1.05rem;
                margin-bottom: 0.2rem;
            }
            .notification-message, .calendar-message, .assistant-message {
                color: var(--re-muted);
                margin: 0.1rem 0 0 0;
            }
            .priority-high {
                background: rgba(239, 68, 68, 0.14);
                color: #fca5a5;
                border-color: rgba(239, 68, 68, 0.3);
            }
            .priority-medium {
                background: rgba(245, 158, 11, 0.14);
                color: #fcd34d;
                border-color: rgba(245, 158, 11, 0.3);
            }
            .priority-low {
                background: rgba(34, 197, 94, 0.14);
                color: #86efac;
                border-color: rgba(34, 197, 94, 0.3);
            }
            .comparison-table-wrap {
                overflow-x: auto;
                border-radius: 16px;
                border: 1px solid var(--re-border);
            }
            .comparison-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 0.92rem;
            }
            .comparison-table th, .comparison-table td {
                border-bottom: 1px solid var(--re-border);
                padding: 0.75rem;
                text-align: left;
                color: var(--re-text);
                vertical-align: top;
            }
            .comparison-table th {
                color: var(--re-muted);
                font-weight: 850;
                background: rgba(255,255,255,0.03);
            }
            .filter-panel {
                position: sticky;
                top: 1rem;
            }
            .assistant-hero {
                background: linear-gradient(135deg, rgba(99,102,241,0.16), rgba(14,165,233,0.09));
                border: 1px solid var(--re-border);
                border-radius: 24px;
                padding: 1.1rem;
                margin-bottom: 1rem;
            }
            .small-muted {
                color: var(--re-muted);
                font-size: 0.9rem;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    def setup_session_state(self):
        super().setup_session_state()
        extra_defaults = {
            "compare_listing_ids": [],
            "profile_edit_mode": False,
        }
        for key, value in extra_defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def numeric_listing_value(self, listing, key):
        try:
            return float(listing.get(key, 0) or 0)
        except (TypeError, ValueError):
            return 0

    def render_notification_card(self, notification, key_prefix):
        priority = str(notification.get("priority", "Low")).lower()
        priority_class = f"priority-{priority}" if priority in ["high", "medium", "low"] else "status-default"
        st.markdown(
            f"""
            <div class="notification-card">
                <div class="notification-top">
                    <div>
                        <div class="notification-title"><span class="notification-icon">{self.escape(notification.get('icon', '🔔'))}</span>{self.escape(notification.get('title', 'Notification'))}</div>
                        <p class="notification-message">{self.escape(notification.get('message', ''))}</p>
                    </div>
                    <span class="status-badge {priority_class}">{self.escape(notification.get('priority', 'Low'))}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        target_page = notification.get("target_page", "home")
        if target_page:
            if st.button("Open", key=f"{key_prefix}_{target_page}_{notification.get('title', '')}", use_container_width=True):
                self.go_to_page(target_page)

    def render_notification_center(self, limit=None):
        notifications = self.service.get_notifications(self.current_user())
        if limit:
            notifications = notifications[:limit]
        for index, notification in enumerate(notifications):
            self.render_notification_card(notification, f"notification_{index}")

    def show_notifications_page(self):
        self.render_page_header("Notification Center", "Review important activity, next steps, and updates from your real estate workflow.")
        self.render_notification_center()

    def render_advanced_filter_panel(self, base_listings, prefix, status_options, include_status=True):
        st.markdown('<div class="filter-panel">', unsafe_allow_html=True)
        st.markdown("### Filters")
        search_text = st.text_input(
            "Search",
            placeholder="Title, address, city, state...",
            key=f"{prefix}_search",
        )
        selected_type = st.selectbox("Property Type", ["All"] + self.PROPERTY_TYPES, key=f"{prefix}_type")
        if include_status:
            selected_status = st.selectbox("Status", ["All"] + status_options, key=f"{prefix}_status")
        else:
            selected_status = "All"
        city = st.selectbox("City", self.service.get_listing_cities(base_listings), key=f"{prefix}_city")
        st.markdown("**Price Range**")
        col_min, col_max = st.columns(2)
        with col_min:
            min_price = st.number_input("Min", min_value=0, value=0, step=25000, key=f"{prefix}_min_price")
        with col_max:
            max_price = st.number_input("Max", min_value=0, value=0, step=25000, key=f"{prefix}_max_price")
        min_bedrooms = st.slider("Minimum Bedrooms", 0, 8, 0, key=f"{prefix}_min_bedrooms")
        min_bathrooms = st.slider("Minimum Bathrooms", 0, 8, 0, key=f"{prefix}_min_bathrooms")
        min_sqft = st.number_input("Minimum Sqft", min_value=0, value=0, step=250, key=f"{prefix}_min_sqft")
        sort_option = st.selectbox("Sort By", self.listing_sort_options(), key=f"{prefix}_sort")
        st.markdown('</div>', unsafe_allow_html=True)
        return {
            "selected_type": selected_type,
            "selected_status": selected_status,
            "search_text": search_text,
            "sort_option": sort_option,
            "city": city,
            "min_price": min_price,
            "max_price": max_price,
            "min_bedrooms": min_bedrooms,
            "min_bathrooms": min_bathrooms,
            "min_sqft": min_sqft,
        }

    def filter_and_sort_listings(self, listings, filters, exclude_agent_id=None, buyer_visible_only=False):
        filtered = self.service.advanced_filter_listings(
            listings,
            selected_type=filters["selected_type"],
            selected_status=filters["selected_status"],
            exclude_agent_id=exclude_agent_id,
            buyer_visible_only=buyer_visible_only,
            search_text=filters["search_text"],
            city=filters["city"],
            min_price=filters["min_price"],
            max_price=filters["max_price"],
            min_bedrooms=filters["min_bedrooms"],
            min_bathrooms=filters["min_bathrooms"],
            min_sqft=filters["min_sqft"],
        )
        return self.service.sort_listings(filtered, filters["sort_option"])

    def render_advanced_filter_summary(self, filters):
        self.render_active_filter_summary(
            filters["selected_type"],
            filters["selected_status"],
            filters["search_text"],
            filters["sort_option"],
        )
        extra_chips = []
        if filters["city"] != "All":
            extra_chips.append(f"City: {filters['city']}")
        if filters["min_price"]:
            extra_chips.append(f"Min Price: {self.format_price(filters['min_price'])}")
        if filters["max_price"]:
            extra_chips.append(f"Max Price: {self.format_price(filters['max_price'])}")
        if filters["min_bedrooms"]:
            extra_chips.append(f"Beds: {filters['min_bedrooms']}+")
        if filters["min_bathrooms"]:
            extra_chips.append(f"Baths: {filters['min_bathrooms']}+")
        if filters["min_sqft"]:
            extra_chips.append(f"Sqft: {filters['min_sqft']}+")
        if extra_chips:
            chip_html = "".join(f'<span class="filter-chip">{self.escape(chip)}</span>' for chip in extra_chips)
            st.markdown(f'<div class="filter-chip-row">{chip_html}</div>', unsafe_allow_html=True)

    def show_agent_properties_page(self):
        user = self.current_user()
        my_listings_all = self.service.get_agent_listings(user["id"])
        other_listings_all = [listing for listing in self.data.properties if listing.get("agent_id") != user["id"]]

        self.render_page_header("View Property Listings", "Use the filter panel to search, sort, and manage listings faster.")
        tablist, taball = st.tabs([
            f"My Property Listings ({len(my_listings_all)})",
            f"Other Property Listings ({len(other_listings_all)})",
        ])

        with tablist:
            filter_col, results_col = st.columns([1, 3])
            with filter_col:
                filters = self.render_advanced_filter_panel(my_listings_all, "agent_my_advanced", self.LISTING_STATUSES)
            with results_col:
                self.render_section_title("My Listings")
                filtered_my = self.filter_and_sort_listings(my_listings_all, filters)
                self.render_advanced_filter_summary(filters)
                st.markdown(f"#### Results: {len(filtered_my)}")
                if not filtered_my:
                    self.render_empty_state("No matching listings", "Try widening your price range or removing a filter.", "🔍")
                else:
                    self.render_listing_grid(filtered_my, "Manage Listing", "manage_listing_btn", "manage_listing", "selected_agent_listing_id", columns=2)

        with taball:
            filter_col, results_col = st.columns([1, 3])
            with filter_col:
                filters = self.render_advanced_filter_panel(other_listings_all, "agent_other_advanced", self.LISTING_STATUSES)
            with results_col:
                self.render_section_title("Other Agent Listings")
                filtered_other = self.filter_and_sort_listings(self.data.properties, filters, exclude_agent_id=user["id"])
                self.render_advanced_filter_summary(filters)
                st.markdown(f"#### Results: {len(filtered_other)}")
                if not filtered_other:
                    self.render_empty_state("No matching listings", "Try adjusting the filters or search box.", "🔍")
                else:
                    self.render_listing_grid(filtered_other, "View Listing Details", "view_other_listing_btn", "view_other_listing_details", "selected_other_listing_id", columns=2)

    def show_buyer_browse_listings_page(self):
        self.render_page_header("View Property Listings", "Use advanced filters to narrow down properties by price, city, bedrooms, bathrooms, and square footage.")
        visible_base = [listing for listing in self.data.properties if listing.get("status") != "Sold"]
        filter_col, results_col = st.columns([1, 3])
        with filter_col:
            filters = self.render_advanced_filter_panel(visible_base, "buyer_advanced", self.BUYER_STATUSES)
        with results_col:
            filtered_properties = self.filter_and_sort_listings(self.data.properties, filters, buyer_visible_only=True)
            self.render_advanced_filter_summary(filters)
            st.markdown(f"#### Total Available Listings: {len(filtered_properties)}")
            if not filtered_properties:
                self.render_empty_state("No matching listings", "Try adjusting your price range, city, or bedroom filters.", "🔍")
            else:
                self.render_listing_grid(filtered_properties, "View Listing Details", "view_listing_btn", "view_listing_details", "selected_listing_id", show_favorite=True, columns=2)

    def render_comparison_table(self, listings):
        if len(listings) < 2:
            self.render_empty_state("Choose at least two listings", "Select 2 or 3 saved listings above to compare them side by side.", "⚖️")
            return

        fields = [
            ("Price", lambda l: self.format_price(l.get("price", 0))),
            ("Bedrooms", lambda l: l.get("bedrooms", 0)),
            ("Bathrooms", lambda l: l.get("bathrooms", 0)),
            ("Square Feet", lambda l: l.get("property_sqft", 0)),
            ("Type", lambda l: l.get("property_type", "")),
            ("Status", lambda l: l.get("status", "")),
            ("City", lambda l: l.get("city", "")),
            ("Address", lambda l: f"{l.get('address', '')}, {l.get('state', '')}"),
        ]
        header_cells = "".join(f"<th>{self.escape(listing.get('title', 'Listing'))}</th>" for listing in listings)
        rows = []
        for label, getter in fields:
            value_cells = "".join(f"<td>{self.escape(getter(listing))}</td>" for listing in listings)
            rows.append(f"<tr><th>{self.escape(label)}</th>{value_cells}</tr>")
        st.markdown(
            f"""
            <div class="comparison-card">
                <div class="comparison-title">Property Comparison</div>
                <div class="comparison-table-wrap">
                    <table class="comparison-table">
                        <tr><th>Feature</th>{header_cells}</tr>
                        {''.join(rows)}
                    </table>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def show_buyer_saved_listings_page(self):
        user = self.current_user()
        saved_listings = self.service.get_saved_listings(user["id"])
        self.render_top_back_button("← Back to Browse Listings", "browse_listings", "top_back_saved_listings")
        self.render_page_header("Saved Listings", "Review, compare, and revisit properties you saved while browsing.")
        st.markdown(f"#### Saved Listings: {len(saved_listings)}")
        if not saved_listings:
            self.render_empty_state("No saved listings yet", "Browse listings and use the Save Listing button to build your shortlist.", "⭐")
            return

        self.render_section_title("Compare Saved Properties")
        listing_options = {f"{listing.get('title', 'Listing')} — {self.format_price(listing.get('price', 0))}": listing.get("id") for listing in saved_listings}
        selected_labels = st.multiselect(
            "Select 2 or 3 saved listings to compare",
            list(listing_options.keys()),
            default=list(listing_options.keys())[:2] if len(listing_options) >= 2 else list(listing_options.keys()),
            max_selections=3,
            key="saved_listing_compare_select",
        )
        selected_ids = [listing_options[label] for label in selected_labels]
        selected_listings = [listing for listing in saved_listings if listing.get("id") in selected_ids]
        self.render_comparison_table(selected_listings)

        self.render_section_title("Saved Listing Cards")
        self.render_listing_grid(saved_listings, "View Listing Details", "view_saved_listing_btn", "view_listing_details", "selected_listing_id", show_favorite=True, columns=2)

    def render_calendar_booking_view(self, bookings, role):
        grouped = self.service.group_bookings_by_date(bookings)
        if not bookings:
            self.render_empty_state("No appointments", "There are no appointments to show on the calendar yet.", "📅")
            return
        for date_key, date_bookings in grouped.items():
            st.markdown(f"### 📅 {self.escape(date_key)}")
            for booking in sorted(date_bookings, key=lambda b: str(b.get("appointment_time", ""))):
                with st.container(border=True):
                    col_left, col_right = st.columns([3, 1])
                    with col_left:
                        st.markdown(f"**{booking.get('appointment_time', '')} — {booking.get('property_title', '')}**")
                        if role == "Agent":
                            st.markdown(f"Buyer: {booking.get('buyer_name', '')} • {booking.get('buyer_email', '')}")
                        else:
                            st.markdown(f"Type: {booking.get('appointment_type', '')}")
                        if booking.get("message"):
                            st.caption(f"Notes: {booking.get('message')}")
                    with col_right:
                        self.render_status_badge(booking.get("status", ""))

    def show_agent_buyer_requests_page(self):
        user = self.current_user()
        agent_bookings = self.service.get_agent_bookings(user["id"])
        agent_inquiries = self.service.get_agent_inquiries(user["id"])
        self.render_page_header("Buyer Bookings & Inquiries", "Confirm appointments, view your calendar, and respond to buyer questions.")
        tab_bookings, tab_calendar, tab_inquiries = st.tabs([
            f"View Bookings ({len(agent_bookings)})",
            "Calendar View",
            f"View Inquiries ({len(agent_inquiries)})",
        ])

        with tab_bookings:
            self.render_section_title("Booking Requests")
            if not agent_bookings:
                self.render_empty_state("No booking requests", "You do not have any booking requests.", "📅")
            else:
                for booking in agent_bookings:
                    self.render_agent_booking_request_card(booking)

        with tab_calendar:
            self.render_section_title("Appointment Calendar")
            self.render_calendar_booking_view(agent_bookings, "Agent")

        with tab_inquiries:
            self.render_section_title("Buyer Inquiries")
            if not agent_inquiries:
                self.render_empty_state("No buyer inquiries", "You do not have any buyer inquiries.", "💬")
            else:
                for inquiry in agent_inquiries:
                    self.render_agent_inquiry_card(inquiry)

    def show_buyer_bookings_inquiries_page(self):
        user = self.current_user()
        my_bookings = self.service.get_buyer_bookings(user["id"])
        my_inquiries = self.service.get_buyer_inquiries(user["id"])
        self.render_page_header("My Bookings & Inquiries", "Track appointment requests and questions you sent to agents.")
        tab_bookings, tab_calendar, tab_inquiries = st.tabs([
            f"My Bookings ({len(my_bookings)})",
            "Calendar View",
            f"My Inquiries ({len(my_inquiries)})",
        ])

        with tab_bookings:
            self.render_section_title("My Bookings")
            if not my_bookings:
                self.render_empty_state("No bookings yet", "You have not made any bookings yet.", "📅")
            else:
                for booking in my_bookings:
                    self.render_buyer_booking_card(booking)

        with tab_calendar:
            self.render_section_title("Appointment Calendar")
            self.render_calendar_booking_view(my_bookings, "Buyer")

        with tab_inquiries:
            self.render_section_title("My Inquiries")
            if not my_inquiries:
                self.render_empty_state("No inquiries yet", "You have not submitted any inquiries yet.", "💬")
            else:
                for inquiry in my_inquiries:
                    self.render_buyer_inquiry_card(inquiry)

    def show_profile_settings_page(self):
        user = self.current_user()
        self.render_page_header("Profile & Settings", "Update your basic account information and password.")
        with st.container(border=True):
            st.markdown("### Account Information")
            full_name = st.text_input("Full Name", value=user.get("full_name", ""), key="profile_full_name")
            email = st.text_input("Email", value=user.get("email", ""), key="profile_email")
            st.caption(f"Role: {user.get('role', '')}")
            if st.button("Save Profile", key="save_profile_settings_btn", type="primary", use_container_width=True):
                success, message, updated_user = self.service.update_user_profile(user["id"], full_name, email)
                if success:
                    st.session_state["user"] = updated_user
                    st.success(message)
                    self.rerun()
                else:
                    st.error(message)

        with st.container(border=True):
            st.markdown("### Password")
            current_password = st.text_input("Current Password", type="password", key="profile_current_password")
            new_password = st.text_input("New Password", type="password", key="profile_new_password")
            confirm_password = st.text_input("Confirm New Password", type="password", key="profile_confirm_password")
            if st.button("Update Password", key="update_profile_password_btn", use_container_width=True):
                success, message = self.service.update_user_password(user["id"], current_password, new_password, confirm_password)
                if success:
                    st.success(message)
                else:
                    st.error(message)

    def show_ai_assistant_page(self):
        user = self.current_user()
        role = user.get("role", "Buyer")
        self.render_page_header("AI Assistant", "Ask about listings, appointments, inquiries, filters, next steps, or how to use the app.")
        left, right = st.columns([1, 2])
        with left:
            st.markdown(
                """
                <div class="assistant-hero">
                    <div class="assistant-title">What I can help with</div>
                    <p class="assistant-message">Use the assistant to understand your dashboard, summarize activity, compare saved listings, or decide what to do next.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            self.render_notification_center(limit=3)
        with right:
            self.show_chat_bot(role)

    def show_agent_dashboard(self):
        super().show_agent_dashboard()
        self.render_section_title("Notification Center")
        self.render_notification_center(limit=3)

    def show_buyer_dashboard(self):
        super().show_buyer_dashboard()
        self.render_section_title("Notification Center")
        self.render_notification_center(limit=3)

    def show_main_app_agent(self):
        page = st.session_state["page"]
        if page == "notifications":
            self.show_notifications_page()
        elif page == "profile_settings":
            self.show_profile_settings_page()
        elif page == "assistant":
            self.show_ai_assistant_page()
        else:
            # Render normal inherited pages without inherited sidebar, then add enhanced sidebar once.
            if page == "home":
                self.show_agent_dashboard()
            elif page == "properties_listings":
                self.show_agent_properties_page()
            elif page == "manage_listing":
                self.show_agent_manage_listing_page()
            elif page == "edit_listing":
                self.show_agent_edit_listing_page()
            elif page == "view_other_listing_details":
                self.show_agent_other_listing_details_page()
            elif page == "add_listings":
                self.show_agent_add_listing_page()
            elif page == "buyer_inquiries":
                self.show_agent_buyer_requests_page()
        self.render_agent_sidebar()

    def show_main_app_buyer(self):
        page = st.session_state["page"]
        if page == "notifications":
            self.show_notifications_page()
        elif page == "profile_settings":
            self.show_profile_settings_page()
        elif page == "assistant":
            self.show_ai_assistant_page()
        else:
            if page == "home":
                self.show_buyer_dashboard()
            elif page == "browse_listings":
                self.show_buyer_browse_listings_page()
            elif page == "view_listing_details":
                self.show_buyer_listing_details_page()
            elif page == "my_inquiries":
                self.show_buyer_bookings_inquiries_page()
            elif page == "saved_listings":
                self.show_buyer_saved_listings_page()
        self.render_buyer_sidebar()

    def render_agent_sidebar(self):
        with st.sidebar:
            st.markdown("# **Navigator**")
            if st.button("🏠 Dashboard", key="agent_nav_dashboard_btn", type="primary", use_container_width=True):
                self.go_to_page("home")
            if st.button("🔍 View/Manage Property Listings", key="agent_nav_properties_btn", type="primary", use_container_width=True):
                self.go_to_page("properties_listings")
            if st.button("➕ Add Property Listings", key="agent_nav_add_listing_btn", type="primary", use_container_width=True):
                self.go_to_page("add_listings")
            if st.button("📖 Buyer Bookings & Inquiries", key="agent_nav_buyer_requests_btn", type="primary", use_container_width=True):
                self.go_to_page("buyer_inquiries")
            if st.button("🔔 Notifications", key="agent_nav_notifications_btn", type="primary", use_container_width=True):
                self.go_to_page("notifications")
            if st.button("🤖 AI Assistant", key="agent_nav_assistant_btn", type="primary", use_container_width=True):
                self.go_to_page("assistant")
            if st.button("⚙️ Profile & Settings", key="agent_nav_profile_btn", type="primary", use_container_width=True):
                self.go_to_page("profile_settings")
            self.render_sidebar_user_card()
            if st.button("🚪 Log Out", key="agent_nav_logout_btn", type="primary", use_container_width=True):
                st.session_state["logged_in"] = False
                st.session_state["user"] = None
                st.session_state["page"] = "home"
                st.session_state["selected_agent_listing_id"] = None
                st.session_state["selected_other_listing_id"] = None
                st.success("Logout Succesful")
                time.sleep(0.5)
                self.rerun()

    def render_buyer_sidebar(self):
        with st.sidebar:
            st.markdown("# **Navigator**")
            if st.button("🏠 Dashboard", key="buyer_nav_dashboard_btn", type="primary", use_container_width=True):
                self.go_to_page("home")
            if st.button("🔍 Browse Listings", key="buyer_nav_browse_btn", type="primary", use_container_width=True):
                self.go_to_page("browse_listings")
            if st.button("📅 My Bookings & Inquiries", key="buyer_nav_requests_btn", type="primary", use_container_width=True):
                self.go_to_page("my_inquiries")
            if st.button("⭐ Saved Listings", key="buyer_nav_saved_listings_btn", type="primary", use_container_width=True):
                self.go_to_page("saved_listings")
            if st.button("🔔 Notifications", key="buyer_nav_notifications_btn", type="primary", use_container_width=True):
                self.go_to_page("notifications")
            if st.button("🤖 AI Assistant", key="buyer_nav_assistant_btn", type="primary", use_container_width=True):
                self.go_to_page("assistant")
            if st.button("⚙️ Profile & Settings", key="buyer_nav_profile_btn", type="primary", use_container_width=True):
                self.go_to_page("profile_settings")
            self.render_sidebar_user_card()
            if st.button("🚪 Log Out", key="buyer_nav_logout_btn", type="primary", use_container_width=True):
                st.session_state["logged_in"] = False
                st.session_state["user"] = None
                st.session_state["page"] = "home"
                st.session_state["booking_listing_id"] = None
                st.session_state["selected_listing_id"] = None
                st.success("Logout Succesful")
                time.sleep(0.5)
                self.rerun()

# =========================
# APP ENTRY POINT
# =========================

data = RealEstateData()
service = EnhancedRealEstateService(data)
ui = EnhancedRealEstateUI(service)
ui.run()
