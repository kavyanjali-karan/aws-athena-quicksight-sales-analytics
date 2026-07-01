# Design Decisions

## Why Athena
Amazon Athena was chosen because it provides serverless SQL analytics directly over data in S3. This keeps the architecture simple and aligns well with a portfolio-style BI engineering project.

## Why Glue
AWS Glue provides cataloging, schema management, and crawler-based discovery for the analytical tables used by Athena.

## Why Parquet
Parquet reduces storage cost and improves query performance for analytical workloads, especially for large transaction datasets.

## Why QuickSight
Amazon QuickSight enables fast dashboard delivery with SPICE and simplifies the handoff from data engineering to executive reporting.

## Why Serverless
The architecture avoids heavy infrastructure management and demonstrates modern cloud-native engineering practices suitable for rapid iteration.
