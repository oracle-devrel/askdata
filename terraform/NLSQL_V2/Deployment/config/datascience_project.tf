locals {
  notebook_session_shape = "VM.Standard.E4.Flex"
  notebook_shape_memory = 32
  notebook_shape_ocpu = 2
}

# module "datascience_project" {
#   source = "../modules/data_science"
#   compartment_id = var.app-compartment-id
#   project_display_name = "${var.object-prefix}-project"
#   freeform_tags = var.resource_tags
#   notebook_session_display_name = "${var.object-prefix}-notebook"
#   notebook_session_shape = local.notebook_session_shape
#   deployment_subnet = var.private_subnet
#   datascience_bucket_id = module.oci_storage_bucket.datascience_bucket.id
#   storage_namespace = var.storage-namespace
#   datascience_private_endpoint_displayname = "${var.object-prefix}-privateendpoint"
#   notebook_shape_memory = local.notebook_shape_memory
#   notebook_shape_ocpu = local.notebook_shape_ocpu
# }