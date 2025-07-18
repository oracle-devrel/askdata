provider "oci" {
  region = var.region
}
resource "oci_oda_oda_instance" "askoracle_oda_instance" {
    compartment_id = var.compartment_ocid
    shape_name = var.shape_name
    display_name = var.oda_display_name
    }