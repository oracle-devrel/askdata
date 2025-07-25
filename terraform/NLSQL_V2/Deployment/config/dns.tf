# locals {
#   zone_ocid = "<dns-zone-ocid>"
#   lb_fqdn = "<your-fqdn>"
# }

# # module "name" {
# #   source = "../modules/dns_record"
# #   zone_ocid = local.zone_ocid
# #   lb_fqdn = local.lb_fqdn
# #   lb_public_ip = module.trust_lb.trust_lb.ip_addresses[0]
# # }