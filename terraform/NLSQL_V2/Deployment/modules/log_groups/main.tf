resource "oci_logging_log_group" "lb_access_log" {
    compartment_id = var.compartment_id
    display_name = var.lb_access_loggp_name
    freeform_tags = var.freeform_tags
}


resource "oci_logging_log_group" "lb_error_log" {
    compartment_id = var.compartment_id
    display_name = var.lb_error_loggp_name
    freeform_tags = var.freeform_tags
}