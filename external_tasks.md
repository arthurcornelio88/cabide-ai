# 📋 External Setup Tasks

This document tracks the manual configurations required in the Google Cloud Console and Google Drive to make the **Cabide AI** pipeline operational.

## 1. Google Cloud Console (IAM & APIs)

* [ ] **Create a Dedicated Project**: Create a new project (e.g., `cabide-ai-br`) or select your current one.
* [ ] **Enable Billing**: Ensure the project is linked to a **Paid Billing Account** (Required for Gemini 3 Pro / Nano Banana Pro).
* [ ] **Enable APIs**:
* [ ] Generative AI API
* [ ] Cloud Run API
* [ ] Artifact Registry API
* [ ] Cloud Storage API
* [ ] Google Drive API


* [ ] **Create Service Account (SA)**:
* [ ] Name: `cabide-ai-sa`
* [ ] **Roles to Grant**:
* `Storage Admin` (To read/write images in GCS)
* `Cloud Run Admin` (For the GitHub Action to deploy)
* `Artifact Registry Writer` (To push Docker images)
* `Service Account User` (Needed for deployment)
* [ ] **Generate SA Key**:
* [ ] Create a JSON key for this SA.
* [ ] **Important**: Minify the JSON into a single line for the GitHub Secret.


## 2. Infrastructure Setup (via Script)

* [ ] **Run Infrastructure Script**:
* [ ] Execute `bash setup_brazil_infra.sh` from your local terminal.
* [ ] Verify that the bucket `cabide-catalog-br` and the repo `cabide-repo` were created in `southamerica-east1`.

## 3. Google Drive Integration (For your Mother)

* [ ] **Create Catalog Folder**: In your mother's Google Drive, create a folder named `Catalogo Cabide AI`.
* [ ] **Share Folder**:
* [ ] Click "Share".
* [ ] Add the Service Account Email (e.g., `cabide-ai-sa@project-id.iam.gserviceaccount.com`).
* [ ] Set permission to **Editor**.

* [ ] **Extract Folder ID**:
* [ ] Open the folder in a browser.
* [ ] Copy the ID from the URL: `drive.google.com/drive/folders/YOUR_FOLDER_ID`.
* [ ] Save this to your `.env` or GitHub Secrets as `GDRIVE_FOLDER_ID`.

## 4. GitHub Secrets Configuration

Navigate to `Settings > Secrets and Variables > Actions` in your repository and add:

| Secret Name | Value |
| --- | --- |
| `GCP_PROJECT_ID` | Your Google Cloud Project ID |
| `GCP_SA_KEY` | The full JSON key for your Service Account |
| `GEMINI_API_KEY` | Your AI Studio API Key (Paid Tier) |
| `GCP_SERVICE_ACCOUNT_JSON` | The minified JSON key (same as above) |
| `GDRIVE_FOLDER_ID` | The ID of the shared Drive folder |

## 5. Final Verification

* [ ] **Test GCS Connectivity**: Check if the app can write a test image to the São Paulo bucket.
* [ ] **Test Drive Connectivity**: Verify if a generated image appears in your mother's Drive folder.
* [ ] **Verify Region**: Check the Cloud Run dashboard to ensure the service is running in `southamerica-east1` (São Paulo) to avoid latency.

---

### Pro-Tip: Billing Alerts

Since you are using a **Paid Tier** for high-fidelity images, I highly recommend setting a **Budget Alert** in the Google Cloud Billing console specifically for this project (e.g., set it to notify you when costs hit $10 or $20) to avoid surprises during heavy batch processing.
