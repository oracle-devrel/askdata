variable "region"{
    type = string
}
variable "display_name" {
  type = string
}
variable "idcs_endpoint" {
  type = string
}

variable "oda_redirect_uri" {
    type = list(string)
}