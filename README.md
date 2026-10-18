# Databricks101 — companion code for the 22-part Databricks blog series

Hands-on solution code for every exercise in the 22-part Databricks blog series, organized blog-by-blog. Each folder is a self-contained learning guide: an overview of the topic, the architecture diagram, a step-by-step concepts walkthrough, three hands-on exercises, and the full solution code.

> Code targets **Databricks Free Edition** wherever possible. All exercise data is generated synthetically inside the notebook — nothing to download. Where a feature needs a higher tier (DLT/serverless compute, GPU training, provisioned model serving), the folder README says so and the exercises include a Free Edition–compatible path.

## Blogs

| # | Blog | Folder |
|---|------|--------|
| 01 | What Is Databricks, Really? The Lakehouse Explained for Builders | [blog-01-what-is-databricks-lakehouse](./blog-01-what-is-databricks-lakehouse/) |
| 02 | Your First Databricks Workspace: Setup That Doesn't Haunt You Later | [blog-02-workspace-setup](./blog-02-workspace-setup/) |
| 03 | Delta Lake Deep Dive: ACID on Object Storage | [blog-03-delta-lake-deep-dive](./blog-03-delta-lake-deep-dive/) |
| 04 | Your First ETL Pipeline: CSV to Gold in 30 Minutes | [blog-04-first-etl-pipeline](./blog-04-first-etl-pipeline/) |
| 05 | Unity Catalog: One Governance Layer to Rule Them All | [blog-05-unity-catalog](./blog-05-unity-catalog/) |
| 06 | Structured Streaming in Production: Beyond the Tutorial | [blog-06-structured-streaming](./blog-06-structured-streaming/) |
| 07 | Delta Live Tables: Declarative Pipelines That Fix Themselves | [blog-07-delta-live-tables](./blog-07-delta-live-tables/) |
| 08 | Making Slow Queries Fast: A Databricks Tuning Playbook | [blog-08-performance-tuning](./blog-08-performance-tuning/) |
| 09 | Change Data Capture: Streaming Your Database to the Lakehouse | [blog-09-change-data-capture](./blog-09-change-data-capture/) |
| 10 | Workflows: Replacing Your Cron Jobs for Good | [blog-10-workflows-orchestration](./blog-10-workflows-orchestration/) |
| 11 | Databricks Asset Bundles: Infrastructure as Code Done Right | [blog-11-databricks-asset-bundles](./blog-11-databricks-asset-bundles/) |
| 12 | CI/CD for Data Pipelines with GitHub Actions | [blog-12-ci-cd-github-actions](./blog-12-ci-cd-github-actions/) |
| 13 | Testing Data Pipelines: Unit, Integration, and Data Quality Tests | [blog-13-testing-data-pipelines](./blog-13-testing-data-pipelines/) |
| 14 | Observability: Monitoring Pipelines Like Software | [blog-14-observability-monitoring-pipelines](./blog-14-observability-monitoring-pipelines/) |
| 15 | FinOps for Databricks: Stop Burning Money on Clusters | [blog-15-finops-databricks-costs](./blog-15-finops-databricks-costs/) |
| 16 | RAG on Databricks: From PDFs to Answers | [blog-16-rag-on-databricks](./blog-16-rag-on-databricks/) |
| 17 | Serve Open-Source LLMs Like APIs: Llama 3 on Databricks | [blog-17-serving-open-source-llms](./blog-17-serving-open-source-llms/) |
| 18 | Fine-Tune Mistral on Your Own Data: SFT, LoRA, and MLflow | [blog-18-fine-tuning-open-source-models](./blog-18-fine-tuning-open-source-models/) |
| 19 | AI Agents on Databricks: Tools, Memory, and Governance That Holds Up | [blog-19-ai-agents-tools-memory-governance](./blog-19-ai-agents-tools-memory-governance/) |
| 20 | Evaluating LLM Apps: Stop Shipping on Vibes | [blog-20-evaluating-llm-apps](./blog-20-evaluating-llm-apps/) |
| 21 | The Real-Time Lakehouse: Kafka to Sub-100ms Serving | [blog-21-real-time-lakehouse](./blog-21-real-time-lakehouse/) |
| 22 | One Lakehouse, Three Clouds: The Multi-Cloud Finale | [blog-22-multi-cloud-lakehouse](./blog-22-multi-cloud-lakehouse/) |

## Layout of each blog folder

```
blog-NN-<slug>/
├── README.md          # learning guide: overview, diagram, concepts, exercises, prerequisites
├── diagram.png        # architecture diagram from the blog post
├── diagram.svg        # vector version of the diagram
└── solution-N-*.py    # exercise solutions (.py, .sql, .yml, .sh, .json by language)
```

## How to use

1. Pick a blog folder and read its `README.md` — it walks through the concepts first.
2. Try the three hands-on exercises yourself (all data is generated in-notebook).
3. Compare against the `solution-N-*` files when you are done.
