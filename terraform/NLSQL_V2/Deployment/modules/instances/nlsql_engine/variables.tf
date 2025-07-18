variable "display_name" {
  type = string
}
variable "compartment_id" {
  type = string
}
variable "region" {
  type = string
}
variable "availability_domain" {
  type = string
}
variable "subnet_id" {
  type = string
}
variable "instance_shape" {
  type = string
}
variable "image_ocid" {
  type = string
}
variable "ssh_public_key" {
  type = string
}
variable "memory_gbs" {
  type = number
}
variable "ocpu_count" {
  type = number
}
variable "boot_volume_size_in_gbs" {
  type = number
}
variable "cloud_agent_plugins" {
  type = map(string)
}
variable "user_tags" {
  type = map(string)
}