output "trust_db_secret"{
    value = oci_vault_secret.apexdb_vault_secret
    sensitive = true
}