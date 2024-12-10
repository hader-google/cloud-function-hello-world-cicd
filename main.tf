provider "google" {
  project = "hader-poc-001"
  region  = "us-central1"
}

terraform {
 backend "gcs" {
   bucket  = "hello-world-state-file"
   prefix  = "/"
 }
}

resource "google_cloud_run_service" "app_service" {
  name     = "hello-world"
  location = "us-central1"
  
  template {
    spec {
      containers {
        image = "${var.location}-docker.pkg.dev/${var.project_id}/${var.repo_name}/${var.image_name}:${var.image_tag}"
      }
    }
  }
}  