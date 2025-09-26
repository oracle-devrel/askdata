-- Copyright (c) 2021, 2025 Oracle and/or its affiliates.
-- Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

-- Reference: Oracle Fusion Cloud SCM Documentation
-- https://docs.oracle.com/en/cloud/saas/supply-chain-management/

-- INV_ORG: Stores inventory organization information
CREATE TABLE INV_ORG (
    INV_ORG_ID NUMBER(10),          -- Primary key for inventory org
    ORG_CODE VARCHAR2(30),          -- Organization code
    ORG_NAME VARCHAR2(100),         -- Organization name
    LOCATION_ID NUMBER(10)          -- Foreign key to location
);

-- INV_ITEMS: Stores inventory item master information
CREATE TABLE INV_ITEMS (
    ITEM_ID NUMBER(10),             -- Primary key for inventory item
    ITEM_NUMBER VARCHAR2(50),       -- Item number/SKU
    ITEM_DESCRIPTION VARCHAR2(255), -- Item description
    ITEM_TYPE VARCHAR2(30)          -- Item type (FG, RM, etc.)
);

-- INV_ONHAND_QTY: Stores on-hand quantity by organization and item
CREATE TABLE INV_ONHAND_QTY (
    ONHAND_ID NUMBER(10),           -- Primary key
    INV_ORG_ID NUMBER(10),          -- Foreign key to INV_ORG
    ITEM_ID NUMBER(10),             -- Foreign key to INV_ITEMS
    QTY_ON_HAND NUMBER(14,2),       -- Quantity on hand
    AS_OF_DATE DATE                 -- Date of quantity measurement
);

-- PO_HEADERS: Stores purchase order header data
CREATE TABLE PO_HEADERS (
    PO_HEADER_ID NUMBER(10),        -- Primary key for PO headers
    PO_NUMBER VARCHAR2(50),         -- Purchase order number
    SUPPLIER_ID NUMBER(10),         -- Foreign key to supplier (not modeled here)
    ORG_ID NUMBER(10),              -- Foreign key to INV_ORG
    ORDER_DATE DATE,                -- Order date
    STATUS VARCHAR2(30)             -- PO status (OPEN, CLOSED, etc.)
);

-- Key Relationships:
-- INV_ORG.INV_ORG_ID = INV_ONHAND_QTY.INV_ORG_ID = PO_HEADERS.ORG_ID
-- INV_ITEMS.ITEM_ID = INV_ONHAND_QTY.ITEM_ID