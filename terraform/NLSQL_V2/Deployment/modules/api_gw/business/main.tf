provider "oci" {
  region = var.region
}
resource oci_apigateway_gateway askdata_apigw {
  compartment_id = var.compartment_ocid
  display_name  = var.gateway_display_name
  endpoint_type = var.endpoint_type
  subnet_id = var.subnet_id
  freeform_tags = var.freeform_tags
}

resource oci_apigateway_deployment askdata_apigw_deployment {
  compartment_id = var.compartment_ocid
  display_name = var.deployment_display_name
  gateway_id  = oci_apigateway_gateway.askdata_apigw.id
  path_prefix = var.path_prefix
  specification {
    logging_policies {
      execution_log {
        log_level = "INFO"
      }
    }
    request_policies {
      mutual_tls {
        allowed_sans = [
        ]
        is_verified_certificate_required = "false"
      }
      authentication {
        is_anonymous_access_allowed = "false"
        token_auth_scheme = "Bearer"
        token_header = "Authorization"
        type = "TOKEN_AUTHENTICATION"
        validation_failure_policy {
          max_expiry_duration_in_hours = 1
          response_type = "CODE"
          scopes = ["openid"]
          type = "OAUTH2"
          use_cookies_for_intermediate_steps = false
          use_cookies_for_session            = false
          use_pkce                           = false
          client_details {
            type = "VALIDATION_BLOCK"
          }
          source_uri_details {
            type = "VALIDATION_BLOCK"
          }
        }
        validation_policy {
          is_ssl_verify_disabled      = false
          max_cache_duration_in_hours = 1
          type                        = "REMOTE_DISCOVERY"
          additional_validation_policy {
            audiences = []
            issuers   = [
              "https://identity.oraclecloud.com/",
              "${var.idcs_endpoint}",
              ]
          }
          client_details {
            client_id                    = var.apigw_capp_client_id
            client_secret_id             = var.apigw_capp_vault_secret_id
            client_secret_version_number = var.apigw_capp_vault_secret_version
            type                         = "CUSTOM"
          }
          source_uri_details {
          type = "DISCOVERY_URI"
          uri  = "${var.idcs_endpoint}:443/.well-known/openid-configuration"
          }
        }
      }
    }
    routes {
      backend {
        connect_timeout_in_seconds = var.connect_timeout_in_seconds
        read_timeout_in_seconds = var.read_timeout_in_seconds
        send_timeout_in_seconds = var.send_timeout_in_seconds
        type = var.backend_type
        url  = var.route1_backend_url
      }
      logging_policies {
      }
      methods = [
        "ANY",
      ]
      path = var.route1_backend_path
    }
    routes {
      backend {
        connect_timeout_in_seconds = var.connect_timeout_in_seconds
        read_timeout_in_seconds = var.read_timeout_in_seconds
        send_timeout_in_seconds = var.send_timeout_in_seconds
        type = var.backend_type
        url  = var.route2_backend_url
      }
      logging_policies {
      }
      methods = [
        "POST",
      ]
      path = var.route2_backend_path
    }
    routes {
      backend {
        connect_timeout_in_seconds = var.connect_timeout_in_seconds
        read_timeout_in_seconds = var.read_timeout_in_seconds
        send_timeout_in_seconds = var.send_timeout_in_seconds
        type = var.backend_type
        url  = var.route3_backend_url
      }
      logging_policies {
      }
      methods = [
        "POST",
      ]
      path = var.route3_backend_path
    }
    routes {
            backend {
                connect_timeout_in_seconds = var.connect_timeout_in_seconds
                read_timeout_in_seconds = var.read_timeout_in_seconds
                send_timeout_in_seconds = var.send_timeout_in_seconds
                type = var.backend_type
                url = var.route4_backend_url
            }
            logging_policies {
            }
            methods = ["ANY"]
            path = var.route4_backend_path
        }
        routes {
            backend {
                connect_timeout_in_seconds = var.connect_timeout_in_seconds
                read_timeout_in_seconds = var.read_timeout_in_seconds
                send_timeout_in_seconds = var.send_timeout_in_seconds
                type = var.backend_type
                url = var.route5_backend_url
            }
            logging_policies {
            }
            methods = ["ANY"]
            path = var.route5_backend_path
        }
  }
}