import hashlib
from datetime import datetime
import re
from copy import deepcopy


class RealEstateService:
    def __init__(self, data_manager, users, properties, inquiries, bookings):
        self.data_manager = data_manager
        self.users = users
        self.properties = properties
        self.inquiries = inquiries
        self.bookings = bookings

    # --- Password helpers ---
    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def verify_password(self, stored_password: str, entered_password: str) -> bool:
        entered_hash = self.hash_password(entered_password)
        return stored_password == entered_password or stored_password == entered_hash

    # --- Basic validators ---
    def normalize_email(self, value):
        return value.strip().lower()

    def is_valid_email(self, email):
        pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        return bool(re.match(pattern, email))

    def normalize_phone(self, phone):
        return "".join(char for char in phone if char.isdigit())

    def is_valid_phone(self, phone):
        return len(phone) == 10

    def get_option_index(self, options, value):
        return options.index(value) if value in options else 0

    def make_key(self, section, item_id, action):
        return f"{section}_{item_id}_{action}"

    # --- Record timestamp helper ---
    def get_record_timestamp(self, record, *field_names):
        for field_name in field_names:
            if field_name in record:
                parsed_value = self.data_manager.parse_datetime_safe(record.get(field_name, ""))
                if parsed_value != datetime.min:
                    return parsed_value
        return datetime.min

    # --- Reset session defaults for logout ---
    def reset_state_for_logout(self):
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

    # --- Finders & read helpers ---
    def find_listing_by_id(self, listing_id):
        for property_item in self.properties:
            if property_item["id"] == listing_id:
                return property_item
        return None

    # Generic filter for properties
    def list_properties(self, property_type=None, status=None, exclude_agent_id=None):
        results = []
        for p in self.properties:
            if exclude_agent_id and p.get("agent_id") == exclude_agent_id:
                continue
            if property_type and property_type != "All" and p.get("property_type") != property_type:
                continue
            if status and status != "All" and p.get("status") != status:
                continue
            results.append(p)
        return results

    def get_agent_dashboard_stats(self, agent_id):
        my_listings = [l for l in self.properties if l.get("agent_id") == agent_id]
        my_listings_count = len(my_listings)
        available_listings_count = sum(1 for l in my_listings if l.get("status") == "Available")
        pending_bookings_count = sum(1 for b in self.bookings if b.get("agent_id") == agent_id and b.get("status") == "Pending")
        new_inquiries_count = sum(1 for i in self.inquiries if i.get("agent_id") == agent_id and i.get("status") == "New")

        return {
            "my_listings_count": my_listings_count,
            "available_listings_count": available_listings_count,
            "pending_bookings_count": pending_bookings_count,
            "new_inquiries_count": new_inquiries_count,
            "latest_listing": (max(my_listings, key=lambda l: self.get_record_timestamp(l, "listing_date", "created_at"), default=None) if my_listings else None),
            "latest_booking": (max([b for b in self.bookings if b.get("agent_id") == agent_id], key=lambda b: self.get_record_timestamp(b, "created_at", "appointment_date"), default=None) if self.bookings else None),
            "latest_inquiry": (max([i for i in self.inquiries if i.get("agent_id") == agent_id], key=lambda i: self.get_record_timestamp(i, "created_at"), default=None) if self.inquiries else None),
        }

    def get_buyer_dashboard_stats(self, buyer_id):
        available_listings = sum(1 for l in self.properties if l.get("status") in ["Available", "Pending"])
        my_bookings = sum(1 for b in self.bookings if b.get("buyer_id") == buyer_id)
        pending_bookings = sum(1 for b in self.bookings if b.get("buyer_id") == buyer_id and b.get("status") == "Pending")
        my_inquiries = sum(1 for i in self.inquiries if i.get("buyer_id") == buyer_id)

        return {
            "available_listings": available_listings,
            "my_bookings": my_bookings,
            "pending_bookings": pending_bookings,
            "my_inquiries": my_inquiries,
        }

    # --- Registration & Authentication ---
    def register_user(self, full_name, email, password, role):
        errors = []
        email_n = self.normalize_email(email)

        for u in self.users:
            if u.get("email", "").strip().lower() == email_n:
                errors.append("An account with this email already exists.")
                return {"success": False, "errors": errors}

        if not full_name or not email_n or not password:
            errors.append("Please fill in all required fields.")

        if not self.is_valid_email(email_n):
            errors.append("Enter a valid email address.")

        if errors:
            return {"success": False, "errors": errors}

        new_user = {
            "id": str(hashlib.sha1((email_n + str(datetime.now())).encode()).hexdigest()),
            "email": email_n,
            "full_name": full_name.strip(),
            "password": self.hash_password(password),
            "role": role,
            "registered_at": str(datetime.now()),
        }

        self.users.append(new_user)
        saved = self.data_manager.save_json_list(self.data_manager.json_file_users, self.users)
        if not saved:
            self.users.pop()
            return {"success": False, "errors": ["Could not persist new user."]}

        return {"success": True, "user": new_user}

    def authenticate(self, email, password):
        email_n = self.normalize_email(email)
        for u in self.users:
            if u.get("email") == email_n and self.verify_password(u.get("password"), password):
                return u
        return None

    # --- Transactional mutation helpers (rollback via in-memory revert) ---
    def delete_record_with_rollback(self, collection, record, file_path):
        try:
            idx = collection.index(record)
        except ValueError:
            return False

        backup = deepcopy(record)
        collection.pop(idx)

        if self.data_manager.save_json_list(file_path, collection):
            return True

        collection.insert(idx, backup)
        return False

    def update_record_with_rollback(self, record, updates, collection, file_path):
        previous_values = deepcopy(record)
        record.update(updates)

        if self.data_manager.save_json_list(file_path, collection):
            return True

        # revert
        record.clear()
        record.update(previous_values)
        return False

    # --- Example mutation APIs ---
    def create_listing(self, listing_data):
        errors = []
        # minimal required fields
        required = ["agent_id", "title", "address", "city", "state", "price"]
        if any(not listing_data.get(k) for k in required):
            errors.append("Please fill in all required fields.")

        if errors:
            return {"success": False, "errors": errors}

        listing = deepcopy(listing_data)
        listing.setdefault("id", str(hashlib.sha1((listing.get("title", "") + str(datetime.now())).encode()).hexdigest()))
        listing.setdefault("status", "Available")
        self.properties.append(listing)

        if not self.data_manager.save_json_list(self.data_manager.json_file_properties, self.properties):
            self.properties.pop()
            return {"success": False, "errors": ["Could not persist listing."]}

        return {"success": True, "listing": listing}

    def update_listing(self, listing_id, updates):
        listing = self.find_listing_by_id(listing_id)
        if not listing:
            return {"success": False, "errors": ["Listing not found."]}

        if self.update_record_with_rollback(listing, updates, self.properties, self.data_manager.json_file_properties):
            return {"success": True, "listing": listing}
        return {"success": False, "errors": ["Could not save listing updates."]}

    def delete_listing(self, listing_id):
        listing = self.find_listing_by_id(listing_id)
        if not listing:
            return {"success": False, "errors": ["Listing not found."]}

        if self.delete_record_with_rollback(self.properties, listing, self.data_manager.json_file_properties):
            return {"success": True}
        return {"success": False, "errors": ["Could not delete listing."]}

    def create_booking(self, booking_data):
        errors = []
        req = ["listing_id", "agent_id", "buyer_id", "buyer_name", "buyer_email", "appointment_date", "appointment_time"]
        if any(not booking_data.get(k) for k in req):
            errors.append("Please fill in all required fields.")

        if not self.is_valid_email(self.normalize_email(booking_data.get("buyer_email", ""))):
            errors.append("Enter a valid email address.")

        if errors:
            return {"success": False, "errors": errors}

        b = deepcopy(booking_data)
        b.setdefault("id", str(hashlib.sha1((b.get("listing_id", "") + str(datetime.now())).encode()).hexdigest()))
        b.setdefault("status", "Pending")
        self.bookings.append(b)

        if not self.data_manager.save_json_list(self.data_manager.json_file_bookings, self.bookings):
            self.bookings.pop()
            return {"success": False, "errors": ["Could not persist booking."]}

        return {"success": True, "booking": b}

    def update_booking_status(self, booking_id, status):
        for b in self.bookings:
            if b.get("id") == booking_id:
                if self.update_record_with_rollback(b, {"status": status}, self.bookings, self.data_manager.json_file_bookings):
                    return {"success": True, "booking": b}
                return {"success": False, "errors": ["Could not update booking status."]}
        return {"success": False, "errors": ["Booking not found."]}

    def create_inquiry(self, inquiry_data):
        errors = []
        req = ["listing_id", "property_title", "agent_id", "buyer_id", "buyer_name", "buyer_email", "subject", "message"]
        if any(not inquiry_data.get(k) for k in req):
            errors.append("Please fill in all required fields.")

        if not self.is_valid_email(self.normalize_email(inquiry_data.get("buyer_email", ""))):
            errors.append("Enter a valid email address.")

        if errors:
            return {"success": False, "errors": errors}

        i = deepcopy(inquiry_data)
        i.setdefault("id", str(hashlib.sha1((i.get("listing_id", "") + str(datetime.now())).encode()).hexdigest()))
        i.setdefault("status", "New")
        self.inquiries.append(i)

        if not self.data_manager.save_json_list(self.data_manager.json_file_inquiries, self.inquiries):
            self.inquiries.pop()
            return {"success": False, "errors": ["Could not persist inquiry."]}

        return {"success": True, "inquiry": i}

    def update_inquiry(self, inquiry_id, updates):
        for idx, inquiry in enumerate(self.inquiries):
            if inquiry.get("id") == inquiry_id:
                if self.update_record_with_rollback(inquiry, updates, self.inquiries, self.data_manager.json_file_inquiries):
                    return {"success": True, "inquiry": inquiry}
                return {"success": False, "errors": ["Could not update inquiry."]}
        return {"success": False, "errors": ["Inquiry not found."]}
