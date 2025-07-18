output "trust_adw_private_ip" {
    value = oci_database_autonomous_database.apex_adw_instance.private_endpoint_ip
}