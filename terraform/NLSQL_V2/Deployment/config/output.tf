# output "trust_app_instance" {
#     value = module.trust_python_app.instances
# }
# output "askoracle_bucket" {
#   value = module.oci_storage_bucket.askoracle_bucket
# }
# output "askdata_redis"{
#     value = module.askdata_redis.redis_cluster
# }
# output "apigw_idcs_capp" {
#   value = module.idcs_confidential_app_apigw.apigw_idcs_capp
# }
# output "nlsql_engine_instance" {
#     value = module.nlsql_engine_app.instances
# }
# output "apex_adw"{
#     value = module.apex_adw.apex_adw
#     sensitive = true
# }
# output "business_adw"{
#     value = module.business_adw.business_adw
#     sensitive = true
# }
# output "idcs_capp" {
#   value = module.idcs_confidential_app_apigw.idcs_capp
# }
# output "api_gateway" {
#   value = module.api_gw.api_gateway
# }
# output "apigw_deployment"{
#     value = moduel.api_gw.apigw_deployment
# }
# output "askdata_bucket"{
#   value = module.oci_storage_bucket.askoracle_bucket
# }
# output "datascience_bucket"{
#   value = module.oci_storage_bucket.datascience_bucket
# }
# output "datascience_private_endpoint" {
#   value = "Pending"
# }

# output "load_balancer_ip"{
#   value = module.trust_loadbalancer.trust_lb
# }

output "trust_instance_private_ip"{
    value = module.trust_python_app.trust_app_instance.private_ip
}
output "engine_instance_private_ip"{
    value = module.nlsql_engine_app.nlsql_engine_instance.private_ip
}
output "engine_instance_public_ip"{
    value = module.nlsql_engine_app.nlsql_engine_instance.public_ip
}
output "trust_api_gw_ip"{
    value = module.trust_api_gw.apigw.ip_addresses
}
output "business_api_gw_ip"{
    value = module.business_api_gw.api_gateway.ip_addresses
}