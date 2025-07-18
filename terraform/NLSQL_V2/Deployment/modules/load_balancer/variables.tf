variable "compartment_id" {
  type = string
}
variable "region" {
  type = string
}
variable "trust_lb_display_name" {
  type = string
}
variable "lb_public_subnet" {
  type = string
}
variable "trustlb_backend_set_name" {
  type = string
}
variable "trustlb_backend_set_urlpath" {
  type = string
}
variable "trustapp_instance_ip" {
  type = string
}
variable "trustapp_listener_name" {
  type = string
}
variable "trustapp_listener_certificate_id" {
    type = string
}
variable "trustapp_lb_hostname" {
  type = string
}
variable "freeform_tags" {
  type = map(string)
}
variable "backend_port" {
  type = string
}
variable "lb_healthcheck_port" {
  type = string
}
variable "healtcheck_returncode" {
  type = string
}