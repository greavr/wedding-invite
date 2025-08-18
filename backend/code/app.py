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
    # We don't care about the username for this simple auth
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
# Example -> export GCS_BUCKET_NAME="your-actual-bucket-name"
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
        # Process only .json files
        if not blob.name.lower().endswith('.json'):
            continue

        try:
            content = blob.download_as_text()
            data = json.loads(content)

            # Ensure the JSON has the required keys for processing
            if 'name' not in data or 'submission_timestamp_utc' not in data:
                print(f"Skipping {blob.name}: missing 'name' or 'submission_timestamp_utc'.")
                continue

            rsvp_name = data['name']
            # Parse the UTC timestamp string into a datetime object for comparison
            current_timestamp = datetime.fromisoformat(data['submission_timestamp_utc'].replace('Z', '+00:00'))

            # If we've already seen an RSVP from this person, check if the current one is newer.
            # Otherwise, add it to our dictionary.
            if rsvp_name not in latest_rsvps or current_timestamp > latest_rsvps[rsvp_name]['_timestamp_obj']:
                data['_timestamp_obj'] = current_timestamp  # Add datetime object for sorting
                latest_rsvps[rsvp_name] = data

        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from blob: {blob.name}")
        except Exception as e:
            print(f"An unexpected error occurred while processing {blob.name}: {e}")

    # Convert the dictionary of latest RSVPs back into a list
    final_rsvp_list = list(latest_rsvps.values())

    # Sort the final list by the timestamp in descending order (latest first)
    return sorted(final_rsvp_list, key=lambda x: x['_timestamp_obj'], reverse=True)


@app.route('/')
@requires_auth  # This decorator protects the page
def index():
    """
    Main route to display the RSVP dashboard.
    """
    error_message = None
    rsvps = []
    attending_count = 0
    total_guests = 0

    try:
        rsvps = get_rsvp_data()
        # Calculate summary counts for guests who are attending
        attending_rsvps = [r for r in rsvps if r.get('attending', '').lower() == 'yes']
        attending_count = len(attending_rsvps)
        total_guests = sum(r.get('guest_count', 0) for r in attending_rsvps)

    except Exception as e:
        error_message = f"An error occurred: {e}"
        print(error_message)

    return render_template(
        'index.html',
        rsvps=rsvps,
        error=error_message,
        bucket_name=GCS_BUCKET_NAME or "Not Configured",
        total_guests=total_guests,
        attending_count=attending_count
    )

if __name__ == '__main__':
    # The app will run on http://localhost:8080
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)