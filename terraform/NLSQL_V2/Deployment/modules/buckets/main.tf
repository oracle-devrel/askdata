provider "oci" {
  region = var.region
}
resource "oci_objectstorage_bucket" "askoracle_bucket" {
    compartment_id = var.compartment_id
    name           = var.askoracle_bucket_display_name
    namespace      = var.namespace
    versioning     = "Enabled"
    freeform_tags = var.freeform_tags
}

# resource "oci_objectstorage_bucket" "datascience_bucket" {
#     compartment_id = var.compartment_id
#     name           = var.datascience_bucket_display_name
#     namespace      = var.namespace
#     versioning     = "Enabled"
#     freeform_tags = var.freeform_tags
# }