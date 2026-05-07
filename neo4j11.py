import pandas as pd
import pymysql
import os

# ================================
# 连接数据库
# ================================
conn = pymysql.connect(
    host="localhost",
    user="root",
    password="Ll268723",
    database="luad_oncosg"
)

out_dir = "/Users/liulin/Desktop/database/project/neo4j1"

os.makedirs(out_dir, exist_ok=True)

# ================================
# 1️⃣ gene
# ================================
gene_df = pd.read_sql("""
SELECT gene_id, Hugo_Symbol
FROM gene
WHERE gene_id IS NOT NULL
""", conn)

gene_df.to_csv(os.path.join(out_dir, "gene.csv"), index=False)

# ================================
# 2️⃣ mutation
# ================================
mut_df = pd.read_sql("""
SELECT mutation_id, gene_id
FROM mutations
WHERE mutation_id IS NOT NULL AND gene_id IS NOT NULL
""", conn)

mut_df.to_csv(os.path.join(out_dir, "mutation.csv"), index=False)

# ================================
# 3️⃣ sample_mutation（核心🔥）
# ================================
sm_df = pd.read_sql("""
SELECT Sample_Id, mutation_id
FROM sample_mutation
WHERE Sample_Id IS NOT NULL AND mutation_id IS NOT NULL
""", conn)

sm_df.to_csv(os.path.join(out_dir, "sample_mutation.csv"), index=False)

print("✅ CSV 导出完成")