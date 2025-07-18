variable "region" {
  type        = string
}
variable "compartment_id" {
  type        = string
}
variable "redis_cluster_display_name" {
  type        = string
}
variable "redis_cluster_node_count" {
  type        = number
}
variable "redis_cluster_node_memory_in_gbs" {
  type        = number
}
variable "redis_cluster_software_version" {
  type        = string
}
variable "subnet_id" {
  type        = string
}