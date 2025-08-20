import os
import json
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, Response
from google.cloud import storage

# Initialize the Flask application
app = Flask(__name__)

# --- START: Password Protection ---
# Define the password for the site
SITE_PASSWORD = 'Indy'

def check_auth(username, password):
    """Checks if the provided password is correct."""
    return password and password.lower() == SITE_PASSWORD.lower()

def authenticate():
    """Sends a 401 response to prompt for login."""
    return Response(
        'Could not verify your access level.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    """A decorator to protect routes with basic authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated
# --- END: Password Protection ---

# IMPORTANT: Set your GCS bucket name from an environment variable
GCS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME','prodapp1-214321-wedding-rsvp')

def get_rsvp_data():
    """
    Fetches, de-duplicates, and sorts RSVP data from a GCS bucket.
    """
    if not GCS_BUCKET_NAME:
        raise ValueError("GCS_BUCKET_NAME environment variable not set.")

    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blobs = bucket.list_blobs()
    latest_rsvps = {}
    for blob in blobs:
        if not blob.name.lower().endswith('.json'):
            continue
        try:
            content = blob.download_as_text()
            data = json.loads(content)
            if 'name' not in data or 'submission_timestamp_utc' not in data:
                print(f"Skipping {blob.name}: missing 'name' or 'submission_timestamp_utc'.")
                continue
            rsvp_name = data['name']
            current_timestamp = datetime.fromisoformat(data['submission_timestamp_utc'].replace('Z', '+00:00'))
            if rsvp_name not in latest_rsvps or current_timestamp > latest_rsvps[rsvp_name]['_timestamp_obj']:
                data['_timestamp_obj'] = current_timestamp
                latest_rsvps[rsvp_name] = data
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from blob: {blob.name}")
        except Exception as e:
            print(f"An unexpected error occurred while processing {blob.name}: {e}")
    final_rsvp_list = list(latest_rsvps.values())
    return sorted(final_rsvp_list, key=lambda x: x['_timestamp_obj'], reverse=True)

# NEW: Helper function for meal normalization
def normalize_meal_choice(choice):
    """Normalizes meal choices to group similar items using simple fuzzy logic."""
    c = choice.lower().strip()
    if 'steak' in c or 'beef' in c:
        return 'Steak / Beef'
    if 'fish' in c or 'salmon' in c or 'cod' in c:
        return 'Fish'
    if 'chicken' in c:
        return 'Chicken'
    if 'veg' in c or 'pasta' in c or 'gnocchi' in c:
        return 'Vegetarian'
    # Capitalize any other choices for consistent display
    return choice.strip().capitalize()

@app.route('/')
@requires_auth
def index():
    """
    Main route to display the RSVP dashboard.
    """
    error_message = None
    rsvps = []
    attending_count = 0
    total_guests = 0
    # NEW: Dictionaries to hold the new counts
    meal_counts = {}
    chocolate_counts = {}

    try:
        rsvps = get_rsvp_data()
        attending_rsvps = [r for r in rsvps if r.get('attending', '').lower() == 'yes']
        
        attending_count = len(attending_rsvps)
        total_guests = sum(r.get('attending_count', 0) for r in attending_rsvps)

        # NEW: Logic to count meals and chocolates for attending guests
        for rsvp in attending_rsvps:
            # Count meal preferences with normalization
            for meal_pref in rsvp.get('mealPreferences', []):
                choice = meal_pref.get('choice')
                if choice:
                    normalized_meal = normalize_meal_choice(choice)
                    meal_counts[normalized_meal] = meal_counts.get(normalized_meal, 0) + 1
            
            # Count chocolate choices
            for choc_pref in rsvp.get('chocolate', []):
                choice = choc_pref.get('choice')
                if choice:
                    choc_choice = choice.strip().capitalize()
                    chocolate_counts[choc_choice] = chocolate_counts.get(choc_choice, 0) + 1

    except Exception as e:
        error_message = f"An error occurred: {e}"
        print(error_message)

    return render_template(
        'index.html',
        rsvps=rsvps,
        error=error_message,
        bucket_name=GCS_BUCKET_NAME or "Not Configured",
        total_guests=total_guests,
        attending_count=attending_count,
        # NEW: Pass new counts to the template
        meal_counts=meal_counts,
        chocolate_counts=chocolate_counts
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)