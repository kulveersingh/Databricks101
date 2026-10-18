# Fern & Field — Databricks naming
- Workspaces: fernfield-{env}-use1  (dev, staging, prod)
- Catalogs:   fernfield_{domain}_{env}   (domain: marketing, finance, dataeng)
- Schemas:    raw, curated, gold  (medallion layers)
- Clusters:   {team}-{purpose}  (ds-experiments, etl-nightly)
- Jobs:       {domain}-{pipeline}-{env}
- Rules: snake_case everywhere; no final/v2/new; no personal names.
