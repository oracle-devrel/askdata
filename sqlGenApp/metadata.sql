-- ACCOUNT_PAYABLES_TBL table is used for storing account payables information

create TABLE ACCOUNT_PAYABLES_TBL (
	VENDOR_NAME VARCHAR(16777216), -- Vendor Name for payables
	VENDOR_NUMBER NUMBER(38,0), -- Vendor Number for payables
	VENDOR_SITE_DETAILS VARCHAR(16777216), -- Vendor Site Details
	INVOICE_NUMBER VARCHAR(16777216), -- Invoice number payable
	INVOICE_DATE DATE, -- Invoice Date
	GL_DATE DATE, -- General Ledger GL Date
	INVOICE_TYPE VARCHAR(16777216), -- Invoice Payable Type
	DUE_DATE DATE, -- Invoice Date
	PAST_DUE_DAYS NUMBER(38,0), -- Past due date
	AMOUNT_DUE NUMBER(38,2) -- Invoice Amount Due
);
