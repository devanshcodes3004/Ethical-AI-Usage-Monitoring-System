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
