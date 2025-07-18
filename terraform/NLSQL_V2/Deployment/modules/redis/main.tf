provider "oci" {
  region = var.region
}

resource "oci_redis_redis_cluster" "askdata_redis_cluster" {
  compartment_id         = var.compartment_id
  display_name           = var.redis_cluster_display_name
  node_count             = var.redis_cluster_node_count
  node_memory_in_gbs     = var.redis_cluster_node_memory_in_gbs
  software_version       = var.redis_cluster_software_version
  subnet_id              = var.subnet_id
}