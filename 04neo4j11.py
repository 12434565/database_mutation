import os

import pandas as pd
import pymysql


conn = pymysql.connect(
    host="localhost",
    user="root",
    password="********",
    database="luad",
)

out_dir = "/Users/liulin/Desktop/database/github1123/database_mutation/neo4j1"
os.makedirs(out_dir, exist_ok=True)


def export_query(filename, query):
    df = pd.read_sql(query, conn)
    df.to_csv(os.path.join(out_dir, filename), index=False)
    return df


# ================================
# 1️⃣ base node / edge tables
# ================================
gene_df = export_query(
    "gene.csv",
    """
    SELECT *
    FROM gene
    WHERE gene_id IS NOT NULL
    """,
)

mutation_df = export_query(
    "mutation.csv",
    """
    SELECT *
    FROM mutations
    WHERE mutation_id IS NOT NULL
    """,
)

gene_mutation_df = export_query(
    "gene_mutation.csv",
    """
    SELECT *
    FROM gene_mutation
    WHERE gene_id IS NOT NULL
      AND mutation_id IS NOT NULL
    """,
)

sample_mutation_df = export_query(
    "sample_mutation.csv",
    """
    SELECT *
    FROM sample_mutation
    WHERE Sample_Id IS NOT NULL
      AND mutation_id IS NOT NULL
    """,
)

patient_df = export_query(
    "patient.csv",
    """
    SELECT *
    FROM patient
    WHERE PATIENT_ID IS NOT NULL
    """,
)

admission_df = export_query(
    "admission.csv",
    """
    SELECT *
    FROM admission
    WHERE case_id IS NOT NULL
    """,
)

sample_df = export_query(
    "sample.csv",
    """
    SELECT *
    FROM sample
    WHERE Sample_Id IS NOT NULL
    """,
)

# =========================
# mutation_big_table
# =========================
mutation_annotation_df = pd.read_sql(
    """
    SELECT *
    FROM mutation_annotation
    """,
    conn,
)

consequence_df = pd.read_sql(
    """
    SELECT *
    FROM consequence
    """,
    conn,
)

mutation_big = (
    sample_mutation_df
    .merge(
        mutation_df,
        on="mutation_id",
        how="left",
    )
    .merge(
        gene_mutation_df,
        on="mutation_id",
        how="left",
    )
    .merge(
        gene_df,
        on="gene_id",
        how="left",
    )
    .merge(
        mutation_annotation_df,
        on="mutation_id",
        how="left",
    )
    .merge(
        consequence_df,
        on="consequence_id",
        how="left",
    )
)

mutation_big.to_csv(
    os.path.join(out_dir, "mutation_big_table.csv"),
    index=False,
)

print(mutation_big.head())
print(mutation_big.shape)

# =========================
# sample_big_table
# =========================
sample_type_df = pd.read_sql(
    """
    SELECT *
    FROM sample_type
    """,
    conn,
)

score_df = pd.read_sql(
    """
    SELECT *
    FROM score
    """,
    conn,
)

cancer_subtype_df = pd.read_sql(
    """
    SELECT *
    FROM cancer_subtype
    """,
    conn,
)

cancer_type_df = pd.read_sql(
    """
    SELECT *
    FROM cancer_type
    """,
    conn,
)

sample_big = (
    sample_df
    .merge(
        admission_df,
        on="case_id",
        how="left",
        suffixes=("", "_admission"),
    )
    .merge(
        patient_df,
        on="PATIENT_ID",
        how="left",
    )
    .merge(
        sample_type_df,
        on="SAMPLE_TYPE_ID",
        how="left",
    )
    .merge(
        score_df,
        on="Sample_Id",
        how="left",
    )
    .merge(
        cancer_subtype_df,
        on="subtype_id",
        how="left",
    )
    .merge(
        cancer_type_df,
        on="ONCOTREE_CODE",
        how="left",
    )
)

sample_big.to_csv(
    os.path.join(out_dir, "sample_big_table.csv"),
    index=False,
)

print(sample_big.head())
print(sample_big.shape)

conn.close()
