import pandas as pd
import re
import os

# ================================
# 根目录
# ================================
base_dir = "/Users/liulin/Desktop/database/project/luad_oncosg_2020"

patient_path = os.path.join(base_dir, "[done]data_clinical_patient.txt")
sample_path = os.path.join(base_dir, "[done]data_clinical_sample.txt")
mutation_path = os.path.join(base_dir, "[done]data_mutations.txt")

out_patient = os.path.join(base_dir, "data/01patient_table.csv")
out_cancer = os.path.join(base_dir, "data/02cancer_type_table.csv")
out_subtype = os.path.join(base_dir, "data/03subtype_table.csv")



# ================================
# 读取数据
# ================================
df = pd.read_csv(patient_path, sep="\t", comment="#")
sample_df = pd.read_csv(sample_path, sep="\t", comment="#")
mutation_df = pd.read_csv(mutation_path, sep="\t", comment="#")


# ================================
# 1️⃣ 统一 ID（最重要一步）
# ================================
df = df.rename(columns={"PATIENT_ID": "PATIENT_ID_original"})
sample_df = sample_df.rename(columns={"PATIENT_ID": "PATIENT_ID_original"})


# ================================
# 2️⃣ patient 表
# ================================
patient_df = df[[
    "PATIENT_ID_original",
    "SEX",
    "ETHNICITY",
    "COHORT"
]].drop_duplicates().copy()

patient_df.to_csv(out_patient, index=False)


# ================================
# 3️⃣ subtype（来自 patient）
# ================================
subtype_df = df[[
    "PATIENT_ID_original",
    "ADENOCARCINOMA_SUBTYPE_WHO2015"
]].drop_duplicates(subset=["PATIENT_ID_original"])


# ================================
# 4️⃣ 合并（现在不会错）
# ================================
merged = sample_df.merge(
    subtype_df,
    on="PATIENT_ID_original",
    how="left"
)


# ================================
# 5️⃣ subtype 拆分
# ================================
def split_subtype(x):
    if pd.isna(x):
        return pd.Series([None, None, None])

    raw = x.strip()

    code_match = re.search(r"\((\d+)\)", raw)
    icd_code = code_match.group(1) if code_match else None
    raw = re.sub(r"\(\d+\)", "", raw).strip()

    raw_lower = raw.lower()

    if "micropapillary" in raw_lower:
        main = "Micropapillary adenocarcinoma"
        detail = None
    elif "papillary" in raw_lower:
        main = "Papillary adenocarcinoma"
        detail = None
    elif "acinar" in raw_lower:
        main = "Acinar adenocarcinoma"
        detail = None
    elif "solid" in raw_lower:
        main = "Solid adenocarcinoma"
        detail = None
    elif "lepidic" in raw_lower:
        main = "Lepidic adenocarcinoma"
        detail = None
    elif "minimally invasive" in raw_lower:
        main = "Minimally invasive adenocarcinoma"
        detail = raw.split(",",1)[1].strip() if "," in raw else None
    elif "mucinous" in raw_lower:
        main = "Invasive mucinous adenocarcinoma"
        detail = None
    elif raw_lower.startswith("nsclc"):
        parts = raw.split(",",1)
        main = parts[1].strip() if len(parts) > 1 else "NSCLC"
        detail = "NSCLC"
    else:
        if "," in raw:
            main, detail = raw.split(",", 1)
        else:
            main, detail = raw, None

    return pd.Series([main.strip(), detail.strip() if detail else None, icd_code])


merged[["SUBTYPE_MAIN", "SUBTYPE_DETAIL", "ICD_CODE"]] = \
    merged["ADENOCARCINOMA_SUBTYPE_WHO2015"].apply(split_subtype)


# ================================
# 6️⃣ cancer_type 表
# ================================
cancer_df = merged[[
    "ONCOTREE_CODE",
    "CANCER_TYPE",
    "CANCER_TYPE_DETAILED"
]].drop_duplicates().dropna(subset=["ONCOTREE_CODE"])

cancer_df.to_csv(out_cancer, index=False)


# ================================
# 7️⃣ subtype 表
# ================================
subtype_table = merged[[
    "ONCOTREE_CODE",
    "SUBTYPE_MAIN",
    "SUBTYPE_DETAIL",
    "ICD_CODE"
]].drop_duplicates()

subtype_table = subtype_table.dropna(
    how="all",
    subset=["SUBTYPE_MAIN", "SUBTYPE_DETAIL", "ICD_CODE"]
)

subtype_table.to_csv(out_subtype, index=False)


# patient v
# cancer_type v
# sample_type
sample_type_df = sample_df[[
    "SAMPLE_TYPE_ID",
    "SAMPLE_CLASS"
]].drop_duplicates()

# 去掉空值（防止 FK 问题）
sample_type_df = sample_type_df.dropna(subset=["SAMPLE_TYPE_ID"])

# 可选：去除前后空格（非常推荐）
sample_type_df["SAMPLE_TYPE_ID"] = sample_type_df["SAMPLE_TYPE_ID"].str.strip()
sample_type_df["SAMPLE_CLASS"] = sample_type_df["SAMPLE_CLASS"].str.strip()

# 可选：统一大小写（避免重复）
sample_type_df["SAMPLE_TYPE_ID"] = sample_type_df["SAMPLE_TYPE_ID"].str.capitalize()

# 输出路径
out_sample_type = os.path.join(base_dir, "data/04sample_type_table.csv")

# 保存
sample_type_df.to_csv(out_sample_type, index=False)
print("✅ Done")


# gene
# CREATE TABLE gene (
#     gene_id INT PRIMARY KEY,
#     Entrez_Gene_Id VARCHAR(50),
#     Hugo_Symbol VARCHAR(50)
# );
gene_df = mutation_df[[
    "Entrez_Gene_Id",
    "Hugo_Symbol"
]].copy()

# 去空值（非常关键）
gene_df = gene_df.dropna(subset=["Hugo_Symbol"])

# 清洗字符串
gene_df["Hugo_Symbol"] = (
    gene_df["Hugo_Symbol"]
    .astype(str)
    .str.strip()
    .str.upper()
)

gene_df = gene_df.dropna(subset=["Entrez_Gene_Id"])

gene_df["Entrez_Gene_Id"] = (
    gene_df["Entrez_Gene_Id"]
    .astype(str)
    .str.strip()
)

# 去掉异常 symbol
gene_df = gene_df[
    gene_df["Hugo_Symbol"] != ""
]

# 去重（放最后）
gene_df = gene_df.drop_duplicates()
# 保存
out_gene = os.path.join(base_dir, "data/05gene_table.csv")
gene_df.to_csv(out_gene, index=False)

print("✅ gene done")
# consequence
# -- =========================
# -- 13. consequence
# -- =========================
# CREATE TABLE consequence (
#     consequence_id INT AUTO_INCREMENT PRIMARY KEY,
#     consequence_type VARCHAR(100) UNIQUE
# );
consequence_df = mutation_df[[
    "Consequence"
]].copy()

# 1️⃣ 去空
consequence_df = consequence_df.dropna(subset=["Consequence"])

# 2️⃣ 转字符串（防止报错）
consequence_df["Consequence"] = consequence_df["Consequence"].astype(str)

# 3️⃣ 拆分多值（核心步骤）
consequence_df = consequence_df.assign(
    consequence_type=consequence_df["Consequence"].str.split(",")
).explode("consequence_type")

# 4️⃣ 清洗字符串
consequence_df["consequence_type"] = (
    consequence_df["consequence_type"]
    .str.strip()
    .str.lower()
)

# 5️⃣ 去掉空值
consequence_df = consequence_df[
    consequence_df["consequence_type"] != ""
]

# 6️⃣ 去重（非常关键，对应 UNIQUE）
consequence_df = consequence_df.drop_duplicates(subset=["consequence_type"])

# 7️⃣ 只保留需要的列
consequence_df = consequence_df[["consequence_type"]]

# 8️⃣ 保存
out_consequence = os.path.join(base_dir, "data/06consequence_table.csv")
consequence_df.to_csv(out_consequence, index=False)

print("✅ consequence table done")
# ---
admission_df = df[[ 
