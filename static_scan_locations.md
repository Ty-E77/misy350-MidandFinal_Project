# Static Scan — Locations to Refactor

This file lists exact file locations (file path and line numbers) for the functions, globals, and helpers you asked to locate. Use these references when applying the refactor patches.

Note: line numbers are based on the current working copy of `app.py` in this workspace.

- `load_json_list` — [app.py](app.py#L50)
- `json_file_properties` — [app.py](app.py#L95)
- `json_file_users` — [app.py](app.py#L96)
- `json_file_inquiries` — [app.py](app.py#L97)
- `json_file_bookings` — [app.py](app.py#L98)
- `users` (global list load) — [app.py](app.py#L100)
- `properties` (global list load) — [app.py](app.py#L106)
- `inquiries` (global list load) — [app.py](app.py#L116)
- `bookings` (global list load) — [app.py](app.py#L125)

- `save_json_list` — [app.py](app.py#L132)
- `delete_record_with_rollback` — [app.py](app.py#L159)
- `update_record_with_rollback` — [app.py](app.py#L170)

- `queue_rerun` — [app.py](app.py#L238)
- `flush_rerun` — [app.py](app.py#L243)
- `navigate_to` — [app.py](app.py#L249)
- `update_state_and_rerun` — [app.py](app.py#L262)
- `make_key` — [app.py](app.py#L273)

- `show_chat_bot` — [app.py](app.py#L437)
  - Note: there are related chat helper functions earlier in the file: `process_chat_message`, `get_agent_chatbot_response`, `get_buyer_chatbot_response` near the same area.

- `show_login_page` — [app.py](app.py#L523)
- `show_main_app_agent` — [app.py](app.py#L656)
- `show_main_app_buyer` — [app.py](app.py#L1405)

- `render_listing_detail_sections` — [app.py](app.py#L212)
- `find_listing_by_id` — [app.py](app.py#L203)

Tips for refactor:
- Most UI, state, and data manipulation occurs in `app.py` (see listed ranges). Start by extracting `load_json_list`/`save_json_list` into `data.py` and centralize file paths there to allow both `app_core.py` and `dashboard.py` to import `data_manager`.
- After `data.py` is in place, implement `RealEstateService` and start redirecting read operations to `service_manager`.

If you'd like, I can now implement the `data.py` module that centralizes JSON I/O and validation helpers (atomic save, parse helpers, `is_valid_*` functions)."