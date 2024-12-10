# Cloud Function with Workload Identity Federation and GitHub Actions Deployment - Test

This project demonstrates deploying a Cloud Function using Workload Identity Federation and GitHub Actions for continuous integration and continuous deployment (CI/CD).  

## Overview

This project automates the deployment of a Cloud Function via Workload Identity Federation. The CI/CD pipeline is managed by GitHub Actions, streamlining the deployment process.

## Key Features

* **Workload Identity Federation:** Enhances security by eliminating the need for service account key management.
* **GitHub Actions CI/CD:** Automates the build and deployment process on every push to the specified branch.
* **Secure Configuration:** Workload Identity Federation Provider and service account information are stored securely in GitHub Action variables to avoid exposing sensitive information in code.

## Workflow

1. **Code Change:**  A developer pushes code changes to the designated branch in the GitHub repository.

2. **GitHub Actions Trigger:** This triggers the GitHub Actions workflow defined in `.github/workflows/deploy-function.yml`.

3. **Authentication:** The workflow uses Workload Identity Federation to authenticate to Google Cloud.  This is accomplished by configuring a trust relationship between a GitHub OIDC provider and a Google service account. The workflow obtains an access token to act as the Google service account, avoiding the need to manage service account keys directly.

4. **Deploy Cloud Function:** The workflow uses the `gcloud functions deploy` command to deploy the Cloud Function code.  The command utilizes the obtained access token for authentication.

## GitHub Actions Configuration

The workflow file defines the steps for building and deploying the Cloud Function.  The following sections are crucial:

* **`permissions:`**: Grants the workflow the necessary permissions within Google Cloud. In this case, the workflow requires permissions to deploy Cloud Functions and potentially access other resources depending on the function's requirements.
* **`on:`**: Specifies the events that trigger the workflow. Typically, this is set to `push` on a specific branch.
* **`jobs:`**: Defines the jobs to run within the workflow. In this case, a `deploy` job would handle the deployment process.
* **`steps:`**: Lists the individual steps within each job.  This might include steps like checking out the code, setting up the environment, building the project, deploying to Cloud Functions, and running tests. Note that in this process, the `google-github-actions/setup-gcloud` is responsible for handling the workload identity federation configuration and `google-github-actions/deploy-cloud-functions` deploys and configures the cloud functions to use WIF.

## Setup and Deployment

1. **Create GitHub Repository:** Create a new GitHub repository and push the project code to it.
2. **Configure GitHub Actions Variables:** Store WIF information (provider and SA) as GitHub Action variables. The `deploy-function.yml` workflow file references these variables during deployment.
3. **Configure Workload Identity Federation:** Follow Google Cloud's documentation to establish a trust relationship between the GitHub repository's OIDC provider and a Google service account. Grant the service account the necessary permissions in your Google Cloud project for deploying and managing Cloud Functions.  The `deploy-function.yml` will use this configuration under the `google-github-actions/auth` action, where `workload_identity_provider` will be configured.


This setup ensures a secure and automated deployment process for your Cloud Function, eliminating the need for service account key management while maximizing performance through concurrent API calls.
