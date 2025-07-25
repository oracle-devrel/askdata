module "oci_storage_bucket"{
    source = "../modules/buckets"
    compartment_id = var.app-compartment-id
    askoracle_bucket_display_name = "${var.object-prefix}-askdata"
    datascience_bucket_display_name = "${var.object-prefix}-datascience"
    namespace = var.storage-namespace
    freeform_tags = var.resource_tags
    region = var.region
}