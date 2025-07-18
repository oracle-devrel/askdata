# resource "oci_datascience_project" "ds_project" {
#     #Required
#     compartment_id = var.compartment_id
#     display_name = var.project_display_name
#     freeform_tags = var.freeform_tags
# }

# # resource "oci_datascience_private_endpoint" "datascience_private_endpoint" {
# #     #Required
# #     compartment_id = var.compartment_id
# #     data_science_resource_type = "NOTEBOOK_SESSION"
# #     subnet_id = var.private_subnet

# #     #Optional
# #     display_name = var.datascience_private_endpoint_displayname
# #     freeform_tags = var.freeform_tags
# # }

# resource "oci_datascience_notebook_session" "datascience_notebook_session" {
#     compartment_id = var.compartment_id
#     project_id = oci_datascience_project.ds_project.id
#     display_name = var.notebook_session_display_name
#     freeform_tags = var.freeform_tags
#     notebook_session_config_details {
#         shape = var.notebook_session_shape
#         notebook_session_shape_config_details {
#             memory_in_gbs = var.notebook_shape_memory
#             ocpus = var.notebook_shape_ocpu
#         }
#         # private_endpoint_id = oci_datascience_private_endpoint.datascience_private_endpoint.id
#         # subnet_id = var.private_subnet
#     }
#     # notebook_session_configuration_details {
#     #     shape = var.notebook_session_shape
#     #     notebook_session_shape_config_details {
#     #         memory_in_gbs = var.notebook_shape_memory
#     #         ocpus = var.notebook_shape_ocpu
#     #     }
#     #     subnet_id = var.deployment_subnet
#     #     # private_endpoint_id = oci_datascience_private_endpoint.datascience_private_endpoint.id
#     # }

#     notebook_session_storage_mount_configuration_details_list {
#         destination_directory_name = "NLSQL"
#         destination_path = "/"
#         storage_type = "OBJECT_STORAGE"
#         bucket = var.datascience_bucket_id
#         namespace = var.storage_namespace
#         prefix = ""
#     }
# }