from pathlib import Path
import json
import time
from datetime import datetime


class RealEstateData:
    def __init__(self):
        self.json_file_properties = Path("properties.json")
        self.json_file_users = Path("users.json")
        self.json_file_inquiries = Path("inquiry.json")
        self.json_file_bookings = Path("bookings.json")

        self.warnings = []

    def load_json_list(self, file_path: Path, label: str):
        if not file_path.exists():
            self.warnings.append(f"{label}: file not found. Starting with empty data.")
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                return data
            else:
                self.warnings.append(f"{label}: invalid format (expected a list). Using empty data.")
                return []

        except (json.JSONDecodeError, OSError):
            self.warnings.append(f"{label}: unreadable or malformed JSON. Using empty data.")
            return []

    def save_json_list(self, file_path: Path, data_list) -> bool:
        for attempt in range(3):
            try:
                temp_file_path = file_path.with_suffix(file_path.suffix + ".tmp")

                with open(temp_file_path, "w", encoding="utf-8") as f:
                    json.dump(data_list, f, indent=4)

                temp_file_path.replace(file_path)
                return True
            except (OSError, TypeError, ValueError) as exc:
                if attempt == 2:
                    self.warnings.append(f"Could not save {file_path.name}: {exc}")
                    return False
                time.sleep(0.2)

    # Basic validation helpers (mirrors previous app checks)
    def is_valid_user(self, user):
        required_keys = ["id", "email", "password", "role"]
        return isinstance(user, dict) and all(key in user for key in required_keys)

    def is_valid_property(self, listing):
        required_keys = [
            "id", "agent_id", "title", "address", "city", "state",
            "price", "bedrooms", "bathrooms", "property_sqft", "property_type"
        ]
        return isinstance(listing, dict) and all(key in listing for key in required_keys)

    def is_valid_inquiry(self, inquiry):
        required_keys = [
            "id", "listing_id", "property_title", "agent_id", "buyer_id",
            "buyer_name", "buyer_email", "buyer_phone", "subject", "message"
        ]
        return isinstance(inquiry, dict) and all(key in inquiry for key in required_keys)

    def is_valid_booking(self, booking):
        required_keys = [
            "id", "listing_id", "property_title", "agent_id", "buyer_id",
            "buyer_name", "buyer_email", "buyer_phone", "appointment_type",
            "appointment_date", "appointment_time"
        ]
        return isinstance(booking, dict) and all(key in booking for key in required_keys)

    # Parsing helpers
    def parse_date_safe(self, value, default_value):
        if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
            return value
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return default_value
        return default_value

    def parse_time_safe(self, value, default_value):
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

    def parse_datetime_safe(self, value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return datetime.min
        return datetime.min


# module-level singleton
data_manager = RealEstateData()
