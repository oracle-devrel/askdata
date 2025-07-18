variable compartment_ocid {
    type = string
    }
variable region {
    type = string
}
variable "subnet_id" {
    type = string
}
variable "route1_backend_path" {
  type = string
}
variable "route1_backend_url" {
  type = string
}
variable "route2_backend_path" {
  type = string
}
variable "route2_backend_url" {
  type = string
}
variable "route3_backend_path" {
  type = string
}
variable "route3_backend_url" {
  type = string
}
variable "route4_backend_path" {
  type = string
}
variable "route4_backend_url" {
  type = string
}
variable "route5_backend_path" {
  type = string
}
variable "route5_backend_url" {
  type = string
}
variable "gateway_display_name" {
    type = string
}
variable "deployment_display_name" {
    type = string
}
variable "path_prefix" {
  type = string
}
variable "endpoint_type" {
  type = string
}
variable connect_timeout_in_seconds{
  type = string
}
variable "read_timeout_in_seconds" {
  type = number
}
variable "send_timeout_in_seconds" {
  type = number
}
variable "backend_type" {
  type = string
}
variable "freeform_tags" {
  type = map(string)
}
variable "idcs_endpoint" {
  type = string
}
variable "apigw_capp_client_id" {
  type = string
}
variable "apigw_capp_vault_secret_id" {
  type = string
}
variable "apigw_capp_vault_secret_version" {
  type = number
}