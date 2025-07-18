output "apigw_capp_vault_secret"{
    value = oci_vault_secret.apigw_capp_vault_secret
    sensitive = true
}