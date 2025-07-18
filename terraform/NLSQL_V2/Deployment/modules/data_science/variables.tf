variable "compartment_id" {
  type = string
}
variable "project_display_name" {
  type = string
}
variable "freeform_tags" {
  type = map(string)
}
variable "notebook_session_display_name" {
  type = string
}
variable "notebook_session_shape"{
    type = string
}
variable "deployment_subnet" {
  type = string
}
variable "datascience_bucket_id" {
  type = string
}
variable "storage_namespace" {
  type = string
}
variable "datascience_private_endpoint_displayname" {
    type = string
}
variable "notebook_shape_memory" {
  type = number
}
variable "notebook_shape_ocpu" {
  type = number
}