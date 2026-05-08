import pandas as pd
import pymysql
import os

# ================================
# 连接数据库
# ================================
conn = pymysql.connect(
    host="localhost",
    user="root",
    password="********",
    database="luad_oncosg"
)

out_dir = "/Users/liulin/Desktop/database/project/neo4j1"

os.makedirs(out_dir, exist_ok=True)

# ================================
# 1️⃣ gene
# ================================
gene_df = pd.read_sql("""
SELECT *
FROM gene
WHERE gene_id IS NOT NULL
""", conn)

gene_df.to_csv(os.path.join(out_dir, "gene.csv"), index=False)

# ================================
# 2️⃣ mutation
# ================================
mut_df = pd.read_sql("""
SELECT *
FROM mutations
WHERE mutation_id IS NOT NULL AND gene_id IS NOT NULL
""", conn)

mut_df.to_csv(os.path.join(out_dir, "mutation.csv"), index=False)

# ================================
# 3️⃣ sample_mutation（核心🔥）
# ================================
sm_df = pd.read_sql("""
SELECT *
FROM sample_mutation
WHERE Sample_Id IS NOT NULL AND mutation_id IS NOT NULL
""", conn)

sm_df.to_csv(os.path.join(out_dir, "sample_mutation.csv"), index=False)
patient_df = pd.read_sql("""
SELECT *
FROM patient
WHERE PATIENT_ID IS NOT NULL
""", conn)

patient_df.to_csv(
    os.path.join(out_dir, "patient.csv"),
    index=False
)
admission_df = pd.read_sql("""
SELECT *
FROM admission
WHERE case_id IS NOT NULL
""", conn)

admission_df.to_csv(
    os.path.join(out_dir, "admission.csv"),
    index=False
)
sample_df = pd.read_sql("""
SELECT * 
FROM sample
WHERE Sample_Id IS NOT NULL
""", conn)

sample_df.to_csv(
    os.path.join(out_dir, "sample.csv"),
    index=False
)

# =========================
# read tables
# =========================

mutation = pd.read_sql("""
SELECT *
FROM mutations
""", conn)

gene = pd.read_sql("""
SELECT *
FROM gene
""", conn)

sample_mutation = pd.read_sql("""
SELECT *
FROM sample_mutation
""", conn)

mutation_annotation = pd.read_sql("""
SELECT *
FROM mutation_annotation
""", conn)

consequence = pd.read_sql("""
SELECT *
FROM consequence
""", conn)

# =========================
# joins
# =========================

mutation_big = (
    sample_mutation

    # mutation info
    .merge(
        mutation,
        on="mutation_id",
        how="left"
    )

    # gene info
    .merge(
        gene,
        on="gene_id",
        how="left"
    )

    # annotation
    .merge(
        mutation_annotation,
        on="mutation_id",
        how="left"
    )

    # consequence
    .merge(
        consequence,
        on="consequence_id",
        how="left"
    )
)

# =========================
# export
# =========================

mutation_big.to_csv(
    os.path.join(out_dir, "mutation_big_table.csv"),
    index=False
)

print(mutation_big.head())
print(mutation_big.shape)

import pandas as pd
import os

# =========================
# read tables
# =========================

patient = pd.read_sql("SELECT * FROM patient", conn)

admission = pd.read_sql("""
SELECT *
FROM admission
""", conn)

treatment = pd.read_sql("""
SELECT *
FROM treatment
""", conn)

sample = pd.read_sql("""
SELECT *
FROM sample
""", conn)

sample_type = pd.read_sql("""
SELECT *
FROM sample_type
""", conn)

score = pd.read_sql("""
SELECT *
FROM score
""", conn)

cancer_type = pd.read_sql("""
SELECT *
FROM cancer_type
""", conn)

# =========================
# joins
# =========================

sample_big = (
    sample

    # admission
    .merge(
        admission,
        on="case_id",
        how="left",
        suffixes=("", "_admission")
    )

    # patient
    .merge(
        patient,
        on="PATIENT_ID",
        how="left"
    )

    # treatment
    .merge(
        treatment,
        on="case_id",
        how="left"
    )

    # sample type
    .merge(
        sample_type,
        on="SAMPLE_TYPE_ID",
        how="left"
    )

    # score
    .merge(
        score,
        on="Sample_Id",
        how="left"
    )

    # cancer type
    .merge(
        cancer_type,
        on="ONCOTREE_CODE",
        how="left"
    )
)

# =========================
# export
# =========================

sample_big.to_csv(
    os.path.join(out_dir, "sample_big_table.csv"),
    index=False
)

print(sample_big.head())
print(sample_big.shape)