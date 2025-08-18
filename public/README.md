# Wedding Reservation Site
Wedding Reservation site for Rick & Josephine

## Run Code Locally
```
pip3 install virtualenv
python3 -m virtualenv venv
source venv/bin/activate
pip3 install -r code/requirements.txt
python3 code/main.py
```
Then you can browse the code [localhost:8080](http://localhost:8080).<br /><br />

### Documentation ###
You can also view the documentation locally on [localhost:8080/docs](http://localhost:8080)


**Deactivate the environment** 
Run the following command
```
deactivate
```

## Create GCS Bucket
```bash
PROJECT_ID=$(gcloud config get-value project)
gcloud storage buckets create gs://$PROJECT_ID-wedding-rsvp \
  --project=$PROJECT_ID \
  --location=us-west1 \
  --uniform-bucket-level-access
```

## Create the service account for the cloud run instance
```bash
PROJECT_ID=$(gcloud config get-value project)
gcloud iam service-accounts create invite-sa --display-name="Wedding Invite SA"
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:invite-sa@$PROJECT_ID$.iam.gserviceaccount.com" \
    --role="roles/editor
```
### Setup Repo
```bash
gcloud artifacts repositories create wedding-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="Repository for wedding RSVP container images"
```
### How to deploy
```bash
gcloud builds submit
```