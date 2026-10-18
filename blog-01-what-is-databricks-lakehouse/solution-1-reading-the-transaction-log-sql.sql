-- Blog 01 — What Is Databricks, Really? The Lakehouse Explained for Builders
-- Exercise 1: reading the transaction log
-- Requires: Everything below runs on Databricks Free Edition. All data is generated inside the notebook — nothing to download.

-- Which version did what?
DESCRIBE HISTORY workspace.default.ex01_vendor_catalog;
