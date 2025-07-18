provider "oci" {
  region = var.region
}

resource "oci_database_autonomous_database" "business_adw_instance" {
  admin_password           = var.admin_password
  compartment_id           = var.compartment_ocid
  db_name                  = var.db_name
  compute_count           = var.cpu_core_count
  compute_model          = "ECPU"
  data_storage_size_in_tbs = var.data_storage_size_in_tbs
  db_workload    = "DW" # Specify the workload type, "DW" for Data Warehouse
  display_name   = var.display_name
  freeform_tags = var.user_tags
  db_version = var.db_version
}
# resource "oci_database_autonomous_database_wallet" "business_adw_wallet" {
#   autonomous_database_id = oci_database_autonomous_database.adw_instance.id
#   password               = var.wallet_password
#   base64_encode_content  = "true"
# }
# resource "local_file" "adw_wallet_file" {
#   content_base64 = oci_database_autonomous_database_wallet.business_adw_wallet.content
#   filename       = "${path.module}/wallet.zip"
# }