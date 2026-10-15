# Ethical AI Usage Monitoring System

A Streamlit-based AI governance gateway that evaluates prompts before routing them to an LLM, with governance decisions and audit logging stored in MongoDB.

## Run locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure the required environment variables in a local `.env` file (for example, `GOOGLE_API_KEY`).
3. Start MongoDB. For a local database directory:
   ```bash
   mongod --dbpath ~/mongodb-data
   ```
4. Start the Streamlit app:
   ```bash
   streamlit run app.py
   ```

## Governance policies

Open **Policies** from Streamlit's multipage navigation to configure prompt rules. Each policy has a name, category, action (`BLOCK`, `WARN`, or `ALLOW`), description, enable/disable state, and match phrases (one phrase per line). Policies are stored in the MongoDB `governance_policies` collection and are evaluated before the existing model-based governance classifier. When multiple policies match, precedence is `BLOCK` > `WARN` > `ALLOW`. An `ALLOW` rule can suppress lower-risk warnings, but it does not override a high-risk block from the core classifier.

Two starter policies are inserted when the policy collection is empty. They can be edited by saving a policy with the same name or removed using the delete control.

**Important limitation:** Policy matching is case-insensitive substring matching. It is intended as a configurable, inspectable first layer, not a complete semantic safety classifier. Phrase choices can create false positives or miss paraphrases; test and tune policies before relying on them for production enforcement.

## Employee and customer records

Open **Employee & Customer Records** in Streamlit's multipage navigation to add, view, and delete employee and customer records.

- Employee fields: employee ID, name, age, phone, optional email, and optional department.
- Customer fields: customer ID, name, age, phone, optional email, and optional address.
- Records are stored separately in MongoDB collections: `employee_records` and `customer_records`.
- Record IDs must be unique within each record type.
- Password entry is optional. If provided, the app stores a salted PBKDF2 hash rather than the raw password, and the records view does not return or display the hash.

**Privacy and deployment warning:** This is a demonstration data-entry feature, not a complete identity or access-management system. The current app does not enforce roles or per-record access control. Use fictional/test records only until authentication, authorization, retention/deletion rules, and an appropriate privacy notice are implemented. Never reuse real account passwords in this form.
