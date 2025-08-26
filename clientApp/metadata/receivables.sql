-- Copyright (c) 2021, 2025 Oracle and/or its affiliates.
-- Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

-- Based on https://docs.oracle.com/en/cloud/saas/financials/25a/faofc/receivables-tables.html

-- RA_CUSTOMER_TRX table stores invoice, debit memo, and credit memo header information
CREATE TABLE RA_CUSTOMER_TRX (
    CUSTOMER_TRX_ID NUMBER(10), -- Primary key for transaction
    TRX_NUMBER VARCHAR(200), -- Transaction number
    BILL_TO_CUSTOMER_ID NUMBER(10), -- Billing customer ID
    TRX_DATE DATE -- Transaction date
);

-- RA_CUSTOMER_TRX_LINES table stores invoice, debit memo, and credit memo line level information
CREATE TABLE RA_CUSTOMER_TRX_LINES (
    CUSTOMER_TRX_LINE_ID NUMBER(10), -- Primary key for transaction line
    CUSTOMER_TRX_ID NUMBER(10), -- Foreign key to RA_CUSTOMER_TRX
    LINK_TO_CUST_TRX_LINE_ID NUMBER(10), -- Link to original invoice line for tax/freight
    LINE_TYPE VARCHAR(50), -- Type of line (CHARGES, FREIGHT, LINE, TAX)
    EXTENDED_AMOUNT NUMBER(38,2) -- Total amount for transaction line
);

-- AR_PAYMENT_SCHEDULES table stores customer balance information at the transaction level
CREATE TABLE AR_PAYMENT_SCHEDULES (
    PAYMENT_SCHEDULE_ID NUMBER(10), -- Primary key for payment schedule
    AMOUNT_DUE_ORIGINAL NUMBER(38,2), -- Original amount due
    AMOUNT_DUE_REMAINING NUMBER(38,2), -- Remaining balance
    CUSTOMER_TRX_ID NUMBER(10), -- Foreign key to RA_CUSTOMER_TRX for billing transactions
    CASH_RECEIPT_ID NUMBER(10), -- Foreign key to AR_CASH_RECEIPTS for payment transactions
    TRX_NUMBER VARCHAR(200), -- Transaction number
    STATUS VARCHAR(50), -- Status of transaction (open or closed)
    AMOUNT_APPLIED NUMBER(38,2), -- Sum of all transactions applied to balance
    CLASS VARCHAR(50) -- Transaction type (INV, DM, CM, CB, PMT)
);

-- AR_CASH_RECEIPTS table stores information about cash receipts
CREATE TABLE AR_CASH_RECEIPTS (
    CASH_RECEIPT_ID NUMBER(10), -- Primary key for cash receipt
    AMOUNT NUMBER(38,2), -- Net amount of receipt
    STATUS VARCHAR(50), -- Status of receipt (UNID, UNAPP, APP, REV, NSF, STOP)
    RECEIPT_NUMBER VARCHAR(200), -- Receipt number
    TYPE VARCHAR(50) -- Type of receipt (CASH or MISC)
);

-- RA_CUSTOMER_TRX.CUSTOMER_TRX_ID can be joined with RA_CUSTOMER_TRX_LINES.CUSTOMER_TRX_ID
-- RA_CUSTOMER_TRX.CUSTOMER_TRX_ID can be joined with AR_PAYMENT_SCHEDULES.CUSTOMER_TRX_ID
-- AR_CASH_RECEIPTS.CASH_RECEIPT_ID can be joined with AR_PAYMENT_SCHEDULES.CASH_RECEIPT_ID

