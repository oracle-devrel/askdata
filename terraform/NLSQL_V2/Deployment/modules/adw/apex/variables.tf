variable "region" {
  type        = string
}
variable "compartment_ocid" {
  type        = string
}
variable "admin_password" {
  type        = string
}
variable "wallet_password" {
  type        = string
}
variable "db_name" {
  type        = string
}
variable "cpu_core_count" {
  type        = number
}
variable "data_storage_size_in_tbs" {
  type        = number
}
variable "display_name" {
  type        = string
}
variable "user_tags" {
  type = map(string)
}
variable "db_version" {
  type = string
}
variable "subnet_id" {
  type = string
}