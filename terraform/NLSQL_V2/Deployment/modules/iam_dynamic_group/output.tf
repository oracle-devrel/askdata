output "instance_principal_dg" {
    value = oci_identity_dynamic_group.instance_principal_dynamic_group
}

output "business_apigw_dg"{
    value = oci_identity_dynamic_group.business_api_gw_dynamic_group
}