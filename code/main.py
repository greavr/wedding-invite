import json
import gspread
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
PASSWORD = "password"
INVITES_FILE = "invites.json"
GOOGLE_SHEET_NAME = "Wedding RSVP" # The exact name of your Google Sheet

# --- Google Sheets Setup ---
try:
    gc = gspread.service_account(filename="credentials.json")
    worksheet = gc.open(GOOGLE_SHEET_NAME).sheet1
except FileNotFoundError:
    print("\n!!! ERROR: 'credentials.json' not found. Please follow Step 1 & 2. !!!\n")
    worksheet = None
except gspread.exceptions.SpreadsheetNotFound:
    print(f"\n!!! ERROR: Google Sheet '{GOOGLE_SHEET_NAME}' not found. Did you create it and share it? !!!\n")
    worksheet = None


def get_guests():
    """Reads the guest list from the JSON file."""
    try:
        with open(INVITES_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
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
        # Return to the same page but with an error message
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
        print(f"Received data: {data}")

        # Flatten the meal preferences list into a single string
        meal_prefs_str = ", ".join(data.get("mealPreferences", []))

        # Prepare the row for Google Sheets
        row_to_insert = [
            data.get("name"),
            data.get("attending"),
            data.get("chocolate"),
            data.get("wine"),
            meal_prefs_str,
            data.get("notes"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]

        worksheet.append_row(row_to_insert)
        
        return jsonify({"success": True, "message": "Thank you for your RSVP!"})

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=8080)