import os
import json
import gspread
from flask import Flask, render_template, request, jsonify
from datetime import datetime
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# --- Configuration from Environment Variables ---
# Use os.environ.get() to provide a default for local testing
PASSWORD = os.environ.get("PASSWORD", "INDY")
INVITES_FILE = "invites.json"
GOOGLE_SHEET_NAME = os.environ.get("GOOGLE_SHEET_NAME")

# --- Google Sheets Setup ---
worksheet = None
# Only attempt to connect if the required environment variables are set
if GOOGLE_SHEET_NAME:
    try:
        # Get credentials JSON string from environment variable
        creds_json_str = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if not creds_json_str:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable not set.")

        # Parse the JSON string into a dictionary
        creds_dict = json.loads(creds_json_str)

        # Define the required scopes
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Create credentials object and authorize gspread
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)
        
        worksheet = gc.open(GOOGLE_SHEET_NAME).sheet1
        print(f"Successfully connected to Google Sheet: '{GOOGLE_SHEET_NAME}'")

    except ValueError as e:
        print(f"\n!!! CONFIGURATION ERROR: {e} !!!\n")
    except json.JSONDecodeError:
        print("\n!!! ERROR: Could not parse GOOGLE_APPLICATION_CREDENTIALS_JSON. Ensure it's a valid, single-line JSON string. !!!\n")
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"\n!!! ERROR: Google Sheet '{GOOGLE_SHEET_NAME}' not found. Did you create it and share it with the service account email? !!!\n")
    except Exception as e:
        print(f"\n!!! An unexpected error occurred during Google Sheets setup: {e} !!!\n")
else:
    print("\n!!! WARNING: GOOGLE_SHEET_NAME environment variable not set. Google Sheets integration is disabled. !!!\n")


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
    if provided_password == PASSWORD:
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
    """Receives the RSVP data and writes it to Google Sheets."""
    if not worksheet:
        return jsonify({"success": False, "error": "Server is not configured to connect to Google Sheets."}), 500

    try:
        data = request.get_json()
        
        # Format the list of meal preference objects into a readable string
        meal_prefs_list = data.get("mealPreferences", [])
        meal_prefs_str = ", ".join([f"{item.get('name', 'Guest')}: {item.get('choice', 'N/A')}" for item in meal_prefs_list])
        
        # Format the list of chocolate preference objects into a readable string
        chocolate_prefs_list = data.get("chocolate", [])
        chocolate_prefs_str = ", ".join([f"{item.get('name', 'Guest')}: {item.get('choice', 'N/A')}" for item in chocolate_prefs_list])

        # Prepare the row for Google Sheets
        row_to_insert = [
            data.get("name"),
            data.get("attending"),
            chocolate_prefs_str,
            data.get("wine"),
            meal_prefs_str,
            data.get("notes"),
            datetime.now().strftime("%Y-m-%d %H:%M:%S")
        ]

        worksheet.append_row(row_to_insert)
        
        return jsonify({"success": True, "message": "Thank you for your RSVP!"})

    except Exception as e:
        print(f"An error occurred during submission: {e}")
        return jsonify({"success": False, "error": "An internal error occurred."}), 500

if __name__ == "__main__":
    # Cloud Run provides the PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    # For production, debug should be False. Host must be 0.0.0.0 to be reachable.
    app.run(debug=False, host='0.0.0.0', port=port)
