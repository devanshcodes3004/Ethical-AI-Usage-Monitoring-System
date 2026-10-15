"""Streamlit interface for importing safe employee/customer CSV data."""

import streamlit as st

from services.csv_data_service import CSVDataService


def render_business_data_page():
    st.title("📂 Business Data (CSV)")
    st.caption(
        "Upload customer issues or employee reference data. The chat can use "
        "a small relevant subset to answer business questions."
    )

    st.warning(
        "Use only approved data. Credential and personal-contact columns are "
        "dropped during import. This demo does not yet authenticate users or "
        "enforce employee-specific permissions."
    )

    service = CSVDataService()

    st.subheader("Upload a CSV")
    with st.form("business_csv_upload_form", clear_on_submit=True):
        record_type = st.selectbox(
            "Data type",
            ["Customer", "Employee"],
            help="Choose Customer for complaints/issues/tickets, or Employee for internal reference data.",
        )
        uploaded_file = st.file_uploader(
            "Choose CSV file",
            type=["csv"],
            help="UTF-8 CSV, maximum 5 MB and 10,000 data rows.",
        )
        submitted = st.form_submit_button("Import CSV", use_container_width=True)

    if submitted:
        if uploaded_file is None:
            st.error("Choose a CSV file first.")
        else:
            try:
                result = service.import_csv(
                    file_bytes=uploaded_file.getvalue(),
                    source_file=uploaded_file.name,
                    record_type=record_type,
                )
                st.success(
                    f"Imported {result['rows_imported']} {record_type.lower()} rows."
                )
                st.write("**Columns retained:** " + ", ".join(result["columns_kept"]))
                if result["columns_dropped"]:
                    st.info(
                        "Sensitive columns were excluded: "
                        + ", ".join(result["columns_dropped"])
                    )
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
            except Exception:
                st.error(
                    "Import failed. Check that MongoDB is running and inspect "
                    "the terminal for the underlying error."
                )

    st.divider()
    st.subheader("Imported CSV files")
    try:
        sources = service.list_sources()
    except Exception:
        st.error("Could not load imported files. Check MongoDB and the terminal.")
        return

    if not sources:
        st.info("No CSV data has been imported yet.")
        return

    rows = []
    for source in sources:
        identity = source.get("_id", {})
        rows.append({
            "Type": identity.get("record_type", ""),
            "File": identity.get("source_file", ""),
            "Rows": source.get("rows", 0),
            "Last imported (UTC)": source.get("latest_import", ""),
        })
    st.dataframe(rows, hide_index=True, use_container_width=True)

    with st.expander("Remove an imported CSV"):
        options = {
            f"{item['Type']} — {item['File']} ({item['Rows']} rows)": (
                item["Type"], item["File"]
            )
            for item in rows
        }
        selected = st.selectbox(
            "Select a CSV to remove",
            list(options.keys()),
            key="delete_csv_source",
        )
        if st.button("Delete selected CSV data", type="secondary"):
            record_type, source_file = options[selected]
            try:
                deleted = service.delete_source(record_type, source_file)
                st.success(f"Removed {deleted} rows.")
                st.rerun()
            except Exception:
                st.error("Could not delete this CSV data. Check the terminal.")
