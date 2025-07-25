module "askdata_oda"{
    source = "../modules/oda"
    oda_display_name = "${var.object-prefix}-oda"
    compartment_ocid = var.app-compartment-id
    region = var.region
    shape_name = "DEVELOPMENT"
}