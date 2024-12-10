variable "project_id" {
  type        = string
  description = "Project ID"
  default     = "psenapati-sample"
}

variable "repo_name" {
  type        = string
  description = "Artifact Registry repo name"
  default     = "github-to-cr"
}

variable "location" {
  type        = string
  description = "Artifact Registry repo location"
  default     = "us"
}

variable "image_name" {
  type        = string
  description = "Docker Image name"
  default     = "hello-world"
}

variable "image_tag" {
  type = string
  default = "latest"
}