data "oci_dns_zones" "lb_dns_zone" {
    compartment_id = var.compartment_id
    name = var.zone_name
    zone_type = "PRIMARY"
}