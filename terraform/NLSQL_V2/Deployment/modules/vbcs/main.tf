resource "oci_visual_builder_vb_instance" "test_vb_instance" {
    #Required
    compartment_id = var.compartment_id
    display_name = var.vbcs_instance_name
    node_count = 1
    freeform_tags = var.freeform_tags
}