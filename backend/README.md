  # GCS RSVP Dashboard

  A simple yet powerful Flask web application to display and summarize RSVP data from JSON files stored in a Google Cloud Storage (GCS) bucket.

  The application reads all `.json` files from a specified bucket, handles multiple submissions from the same party by only using the latest one, and presents the information in a clean, sorted, and easy-to-read web interface.

  ## Features

  -   **GCS Integration**: Reads RSVP data directly from a Google Cloud Storage bucket.
  -   **De-duplication**: Automatically handles duplicate RSVPs by using only the entry with the latest `submission_timestamp_utc`.
  -   **Data Sorting**: Sorts all RSVPs to show the most recent submissions first.
  -   **Clear Dashboard**: Displays results in a clean HTML table with key information.
  -   **Live Summary**: Calculates and shows a summary of total guests and parties attending.
  -   **Containerized**: Includes a `Dockerfile` for easy building and deployment using Docker.

  ## Prerequisites

  Before you begin, ensure you have the following installed and configured:

  1.  **Python 3.7+**: [Download Python](https://www.python.org/downloads/)
  2.  **Google Cloud SDK**: The `gcloud` command-line tool. [Installation Guide](https://cloud.google.com/sdk/docs/install)
  3.  **Docker**: Required for running the application in a container. [Install Docker](https://docs.docker.com/get-docker/)
  4.  **A Google Cloud Project**: You need an active GCP project with a GCS bucket created to store your JSON files.

  ## Project Structure

  ```
  .
  ├── app.py              # Main Flask application logic
  ├── requirements.txt    # Python dependencies
  ├── Dockerfile          # Docker container configuration
  └── templates/
      └── index.html      # HTML template for the dashboard
  ```

  ## Setup & Installation

  Follow these steps to get the application running on your local machine.

  ### 1. Get the Project Files

  Clone the repository or download the files into a local directory.

  ### 2. Authenticate with Google Cloud

  You need to authenticate your local environment so the application has permission to access your GCS bucket. Run the following command in your terminal:

  ```bash
  gcloud auth application-default login
  ```

  This will open a browser window for you to log in to your Google account.

  ### 3. Install Dependencies

  Create a virtual environment (optional but recommended) and install the required Python packages.

  ```bash
  # Create and activate a virtual environment (Mac/Linux)
  python3 -m venv venv
  source venv/bin/activate

  # Install packages
  pip install -r requirements.txt
  ```

  ### 4. Configure Environment Variable

  The application needs to know which GCS bucket to read from. Set this using an environment variable.

  **Mac/Linux:**
  ```bash
  export GCS_BUCKET_NAME="your-gcs-bucket-name"
  ```

  **Windows (Command Prompt):**
  ```bash
  set GCS_BUCKET_NAME="your-gcs-bucket-name"
  ```

  **Windows (PowerShell):**
  ```bash
  $env:GCS_BUCKET_NAME="your-gcs-bucket-name"
  ```
  > **Note:** Replace `"your-gcs-bucket-name"` with the actual name of your bucket.

  ---

  ## Running the Application

  You can run the application directly with Python or as a Docker container.

  ### Option 1: Running Locally with Python

  After setting the environment variable, start the Flask development server:

  ```bash
  python app.py
  ```

  The application will be available at **`http://127.0.0.1:8080`**.

  ### Option 2: Running with Docker

  This is the recommended method for consistency and easy deployment.

  **1. Build the Docker Image:**

  From the root of the project directory, run the build command:
  ```bash
  docker build -t rsvp-app .
  ```

  **2. Run the Docker Container:**

  Start a container from the image you just built. Remember to pass the `GCS_BUCKET_NAME` environment variable to the container.

  ```bash
  docker run -d -p 8080:8080 \
    -e GCS_BUCKET_NAME="your-gcs-bucket-name" \
    --name rsvp-container \
    rsvp-app
  ```
  > **Note:** Replace `"your-gcs-bucket-name"` again.

  The application is now running inside the container and is accessible at **`http://localhost:8080`**.

  ---

  ## Deploying to Cloud Run

  This containerized application is perfect for deployment on serverless platforms like Google Cloud Run. You can build the image, push it to Google Artifact Registry, and deploy it with just a few `gcloud` commands. You would need to set the `GCS_BUCKET_NAME` environment variable in the Cloud Run service configuration.