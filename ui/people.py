"""Streamlit UI for employee and customer record management."""

import streamlit as st

from services.people_service import PeopleService


def _record_form(service, record_type):
    is_employee = record_type == "Employee"
    label = "Employee ID" if is_employee else "Customer ID"
    extra_label = "Department" if is_employee else "Address"

    with st.form(f"{record_type.lower()}_record_form", clear_on_submit=True):
        left, right = st.columns(2)
        with left:
            record_id = st.text_input(label, max_chars=64)
            full_name = st.text_input("Full name")
            age = st.number_input("Age", min_value=0, max_value=120, value=18, step=1)
            phone = st.text_input("Phone number", placeholder="+91 98765 43210")
        with right:
            email = st.text_input("Email (optional)")
            extra_value = st.text_input(f"{extra_label} (optional)")
            password = st.text_input(
                "Password (optional)",
                type="password",
                help=(
                    "For demonstration only. If supplied, only a salted hash is saved. "
                    "This is not a production login system."
                ),
            )
            st.caption("Leave Password blank if this record does not need a credential.")

        submitted = st.form_submit_button(
            f"Save {record_type.lower()} record",
            use_container_width=True,
        )

    if submitted:
        try:
            service.add_record(
                record_type=record_type,
                record_id=record_id,
                full_name=full_name,
                age=int(age),
                phone=phone,
                email=email,
                department=extra_value if is_employee else "",
                address=extra_value if not is_employee else "",
                password=password,
            )
            st.success(f"{record_type} record saved.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error(
                "Could not save the record. Check that MongoDB is running, "
                "then review the terminal for the underlying error."
            )


def _record_list(service, record_type):
    label = "Employee ID" if record_type == "Employee" else "Customer ID"
    try:
        records = service.list_records(record_type)
    except Exception:
        st.error("Could not load records. Check MongoDB and the terminal output.")
        return

    st.subheader(f"Saved {record_type.lower()} records")
    if not records:
        st.info(f"No {record_type.lower()} records have been added yet.")
        return

    display_records = []
    for record in records:
        row = {
            label: record.get("record_id", ""),
            "Name": record.get("full_name", ""),
            "Age": record.get("age", ""),
            "Phone": record.get("phone", ""),
            "Email": record.get("email") or "",
        }
        if record_type == "Employee":
            row["Department"] = record.get("department") or ""
        else:
            row["Address"] = record.get("address") or ""
        row["Created at (UTC)"] = record.get("created_at", "")
        display_records.append(row)

    st.dataframe(display_records, hide_index=True, use_container_width=True)

    with st.expander(f"Delete a {record_type.lower()} record"):
        options = {
            f'{record.get("record_id", "")} — {record.get("full_name", "")}':
                record.get("record_id", "")
            for record in records
        }
        selected = st.selectbox(
            f"Select {record_type.lower()}",
            list(options.keys()),
            key=f"delete_{record_type.lower()}_selection",
        )
        if st.button(
            f"Delete selected {record_type.lower()}",
            key=f"delete_{record_type.lower()}_button",
            type="secondary",
        ):
            try:
                if service.delete_record(record_type, options[selected]):
                    st.success("Record deleted.")
                    st.rerun()
                else:
                    st.warning("That record was not found.")
            except Exception:
                st.error("Could not delete the record. Check the terminal output.")


def render_people_manager():
    st.title("👥 Employee & Customer Records")
    st.caption(
        "Add, view, and remove employee and customer records stored in MongoDB."
    )
    st.warning(
        "Demo data-entry page: this app does not yet enforce user roles or "
        "record-level access controls. Use fictional/test data until access "
        "controls and a privacy policy are implemented."
    )
    st.info(
        "Passwords are optional. When provided, they are stored as salted "
        "PBKDF2 hashes and are never shown in the records table. Do not reuse "
        "real account passwords here."
    )

    service = PeopleService()
    employee_tab, customer_tab = st.tabs(["👔 Employees", "🛍️ Customers"])

    with employee_tab:
        st.subheader("Add employee")
        _record_form(service, "Employee")
        st.divider()
        _record_list(service, "Employee")

    with customer_tab:
        st.subheader("Add customer")
        _record_form(service, "Customer")
        st.divider()
        _record_list(service, "Customer")
