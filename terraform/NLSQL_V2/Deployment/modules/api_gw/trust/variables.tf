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
variable "gateway_display_name" {
    type = string
}
variable "deployment_display_name" {
    type = string
}
variable "path_prefix" {
  type = string
  default = "/v1"
}
variable "endpoint_type" {
  type = string
  default = "PUBLIC"
}
variable connect_timeout_in_seconds{
  type = number
  default = 75
}
variable "read_timeout_in_seconds" {
  type = number
  default = 300
}
variable "send_timeout_in_seconds" {
  type = number
  default = 300
}
variable "backend_type" {
  type = string
  default = "HTTP_BACKEND"
}
variable "freeform_tags" {
  type = map(string)
}