resource "oci_dns_record" "lb_dns_record" {
    #Required
    zone_name_or_id = var.zone_ocid
    domain = var.lb_fqdn
    rtype = "A"

    #Optional
    rdata = var.lb_public_ip
}