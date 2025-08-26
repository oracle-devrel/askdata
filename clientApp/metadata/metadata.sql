-- Copyright (c) 2021, 2025 Oracle and/or its affiliates.
-- Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

-- ACCOUNT_PAYABLES_TBL table is used for storing account payables information

create TABLE ACCOUNT_PAYABLES_TBL (
	ACCOUNTS_PAYABLE_ID NUMBER(10), -- Accounts Payables id table Primary Key
	VENDOR_ID NUMBER(10), -- Vendor Id Join key for looking up Vendors
	INVOICE_NUMBER VARCHAR(200), -- Invoice number payable
	INVOICE_DATE DATE, -- Invoice Date
	GL_DATE DATE, -- General Ledger GL Date
	INVOICE_TYPE_ID NUMBER, -- Join key for looking up invoice type
	DUE_DATE DATE, -- Due Date
	PAST_DUE_DAYS NUMBER(38), -- Past due days
	AMOUNT_DUE NUMBER(38,2) -- Invoice Amount Due
);

create TABLE VENDORS (
	VENDOR_ID NUMBER(10), -- Unique Id for Vendor
	VENDOR_NAME VARCHAR(4000), -- Vendor Name for payables
	VENDOR_SITE_DETAILS VARCHAR(4000) -- Vendor Site Details
);

create TABLE INVOICE_TYPE_LOOKUP (
	INVOICE_TYPE_ID NUMBER, -- Unique key for invoice type lookup
	INVOICE_TYPE VARCHAR(100) -- Invoice Type description
);

-- ACCOUNT_PAYABLES_TBL.VENDOR_ID can be joined with VENDORS.VENDOR_ID
-- ACCOUNT_PAYABLES_TBL.INVOICE_TYPE_ID can be joined with INVOICE_TYPE_LOOKUP.INVOICE_TYPE_ID
