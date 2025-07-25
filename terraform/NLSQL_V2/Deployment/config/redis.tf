module "askdata_redis" {
  source = "../modules/redis"
  region = var.region
  compartment_id = var.app-compartment-id
  redis_cluster_display_name = "${var.object-prefix}-redis"
  redis_cluster_node_count = 3
  redis_cluster_node_memory_in_gbs = 16
  redis_cluster_software_version = "V7_0_5"
  subnet_id = var.private_subnet
}