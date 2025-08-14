import os
import json
import re
from flask import Flask, render_template, request, jsonify
from datetime import datetime
from google.cloud import storage

app = Flask(__name__)

# --- Configuration from Environment Variables ---
PASSWORD = os.environ.get("PASSWORD", "indy")
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "prodapp1-214321-wedding-rsvp")
INVITES_FILE = "invites.json"

# --- Google Cloud Storage Setup ---
storage_client = None
if GCS_BUCKET_NAME:
    try:
        storage_client = storage.Client()
        print(f"Successfully initialized GCS client for bucket: '{GCS_BUCKET_NAME}'")
    except Exception as e:
        print(f"\n!!! An unexpected error occurred during GCS client setup: {e} !!!\n")
else:
    print("\n!!! WARNING: GCS_BUCKET_NAME environment variable not set. GCS integration is disabled. !!!\n")


def get_guests():
    """Reads the guest list from the JSON file."""
    try:
        with open(INVITES_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: '{INVITES_FILE}' not found. Guest list will be empty.")
        return []

@app.route("/")
def index():
    """Renders the main page."""
    return render_template("index.html", password_required=True)

@app.route("/verify", methods=["POST"])
def verify():
    """Verifies the password."""
    provided_password = request.form.get("password")
    if provided_password.lower() == PASSWORD:
        return render_template("index.html", password_required=False)
    else:
        return render_template("index.html", password_required=True, error="Incorrect password.")

@app.route("/api/guests")
def api_guests():
    """Provides the guest list to the frontend for autocomplete."""
    guests = get_guests()
    return jsonify(guests)

@app.route("/submit", methods=["POST"])
def submit():
    """Receives RSVP data and uploads it as a JSON file to Google Cloud Storage."""
    if not storage_client or not GCS_BUCKET_NAME:
        return jsonify({"success": False, "error": "Server is not configured for GCS."}), 500

    try:
        data = request.get_json()
        
        # Add a server-side timestamp to the submission data
        data['submission_timestamp_utc'] = datetime.utcnow().isoformat() + "Z"

        # Sanitize the guest's name for use in a filename
        guest_name = data.get("name", "unknown-guest")
        sanitized_name = re.sub(r'[^a-z0-9]+', '-', guest_name.lower()).strip('-')
        
        # Create a unique filename
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"rsvp_{sanitized_name}_{timestamp}.json"

        # Get the bucket and create a new blob (file)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)

        # Upload the data as a JSON string
        blob.upload_from_string(
            data=json.dumps(data, indent=4),
            content_type='application/json'
        )

        print(f"Successfully uploaded RSVP to gs://{GCS_BUCKET_NAME}/{filename}")
        return jsonify({"success": True, "message": "Thank you for your RSVP!"})

    except Exception as e:
        print(f"An error occurred during GCS submission: {e}")
        return jsonify({"success": False, "error": "An internal error occurred."}), 500

if __name__ == "__main__":
    # Cloud Run provides the PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    # For production, debug should be False. Host must be 0.0.0.0 to be reachable.
    app.run(debug=False, host='0.0.0.0', port=port)