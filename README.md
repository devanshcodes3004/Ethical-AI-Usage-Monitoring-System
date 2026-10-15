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

## CSV business data for chat

Open **Business Data (CSV)** in Streamlit's multipage navigation to upload approved customer or employee CSV files. The app stores rows in MongoDB's `business_csv_records` collection and retrieves only a small keyword-matched subset for relevant chat questions.

- Upload UTF-8 CSV files up to 5 MB and 10,000 rows.
- Choose whether each file contains Customer or Employee records. Fictional templates are available at `examples/customer_issues_sample.csv` and `examples/employee_reference_sample.csv`.
- Credential, secret, payment, government-ID, and personal-contact columns (such as password, API key, phone, email, and address) are excluded during import.
- Recognizable emails, phone numbers, payment-card-like values, and labeled secrets in free-text cells are redacted.
- Ask questions such as "Summarize the open customer issues" or "What problems are mentioned in the customer records?" The model receives only a few matching, filtered rows.
- Direct requests to retrieve passwords, credentials, API keys, tokens, OTPs, or similar secrets are blocked before CSV retrieval and before an LLM call.
- Re-uploading the same filename for the same data type replaces that file's imported rows. You can remove an imported source from the page.

**Limitations and safety:** Retrieval currently uses keyword overlap, not semantic/vector search, so phrasing and CSV column names affect what it finds. Secret detection is defense-in-depth, not a guarantee that arbitrary sensitive text can always be recognized. Treat CSVs as untrusted, review them before upload, and use test data first. This demo does not yet authenticate employees or enforce role-based/row-level permissions; anyone who can access the app may be able to query the approved imported business records. Do not upload real credentials, unnecessary personal data, or highly sensitive records.