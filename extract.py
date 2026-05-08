import pandas as pd
import re
import os
import pymysql

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="********",
    database="luad_oncosg"
)
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

# 1️⃣ 保留有 symbol 的（这个是主键语义）
gene_df = gene_df.dropna(subset=["Hugo_Symbol"])

# 2️⃣ 清洗 symbol
gene_df["Hugo_Symbol"] = (
    gene_df["Hugo_Symbol"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# 3️⃣ 去掉空 symbol
gene_df = gene_df[
    (gene_df["Hugo_Symbol"] != "") &
    (gene_df["Hugo_Symbol"] != "[NOT AVAILABLE]")
]

# 4️⃣ 处理 Entrez（关键修改在这里）
gene_df["Entrez_Gene_Id"] = (
    gene_df["Entrez_Gene_Id"]
    .astype(str)
    .str.strip()
)

# 🔥 把非法值 → None（数据库会变 NULL）
gene_df["Entrez_Gene_Id"] = gene_df["Entrez_Gene_Id"].replace(
    ["", "NA", "NaN", "nan", "None", "0"],  # 👈 关键
    None
)

# 5️⃣ 去重（放最后）
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
# admission_df = df[[ 
# ================================
# 8️⃣ admission 表（核心）
# ================================

# 从 patient + sample 合并必要信息
admission_df = df[[
    "PATIENT_ID_original",
    "SMOKING_STATUS",
    "SMOKING_PACK_YEARS",
    "OS_STATUS",
    "OS_MONTHS",
    "AGE",
    "STAGE"
]].copy()

# 重命名
admission_df = admission_df.rename(columns={
    "AGE": "patient_age"
})

# ================================
# 清洗（重要）
# ================================

# smoking_pack_years → float 保留两位
admission_df["SMOKING_PACK_YEARS"] = pd.to_numeric(
    admission_df["SMOKING_PACK_YEARS"], errors="coerce"
).round(2)
# OS_MONTHS → float
admission_df["OS_MONTHS"] = pd.to_numeric(
    admission_df["OS_MONTHS"], errors="coerce"
).round(2)
# OS_STATUS → boolean（0/1）
admission_df["OS_STATUS"] = (
    admission_df["OS_STATUS"]
    .astype(str)
    .str.split(":")
    .str[0]   # 取前面的 0 或 1
)

admission_df["OS_STATUS"] = pd.to_numeric(admission_df["OS_STATUS"], errors="coerce")
# ================================
# 去重（关键：一个 patient 一个 admission）
# ================================
admission_df = admission_df.drop_duplicates(subset=["PATIENT_ID_original"])
# ================================
# 🔥 mapping（最关键一步）
# ================================
# 读取 mapping（你刚刚导出的）
mapping_path = os.path.join(base_dir, "data/data_from_sql/01patient_mapping.csv")

mapping_df = pd.read_csv(
    mapping_path,
    header=None,
    names=["PATIENT_ID", "PATIENT_ID_original"]
)
patient_dict = dict(zip(
    mapping_df["PATIENT_ID_original"],
    mapping_df["PATIENT_ID"]
))
# 映射
admission_df["PATIENT_ID"] = admission_df["PATIENT_ID_original"].map(patient_dict)
# ================================
# 检查（必须做）
# ================================
missing = admission_df["PATIENT_ID"].isna().sum()
print(f"⚠️ missing PATIENT_ID mapping: {missing}")
# ================================
# 删除原始ID
# ================================
admission_df = admission_df.drop(columns=["PATIENT_ID_original"])
# ================================
# 保存
# ================================
admission_df = admission_df[[
    "PATIENT_ID",
    "SMOKING_STATUS",
    "SMOKING_PACK_YEARS",
    "OS_STATUS",
    "OS_MONTHS",
    "patient_age",
    "STAGE"
]]
out_admission = os.path.join(base_dir, "data/07admission_table.csv")
admission_df.to_csv(out_admission, index=False)
print("✅ admission table done")

# ================================
# 9️⃣ sample 表（最终稳定版）
# ================================

# 1️⃣ 从数据库读取 case mapping（不要用旧CSV）
case_df = pd.read_sql(
    "SELECT case_id, PATIENT_ID FROM admission",
    conn
)

case_df["PATIENT_ID"] = case_df["PATIENT_ID"].astype(str)

case_dict = dict(zip(
    case_df["PATIENT_ID"],
    case_df["case_id"]
))

# ================================
# 2️⃣ 基础数据
# ================================
sample_clean = sample_df.copy()

sample_clean["PATIENT_ID_original"] = (
    sample_clean["PATIENT_ID_original"]
    .astype(str)
    .str.strip()
)

# ================================
# 3️⃣ merge patient 信息
# ================================
sample_clean = sample_clean.merge(
    df[[
        "PATIENT_ID_original",
        "HISTOLOGICAL_GRADE",
        "EXOME_SEQ",
        "RNA_SEQ_ANALYSIS",
        "SEQUENCING_TYPE"
    ]],
    on="PATIENT_ID_original",
    how="left"
)

# ================================
# 4️⃣ Tumor barcode（直接用 SAMPLE_ID 更稳）
# ================================
sample_clean["Tumor_Sample_Barcode"] = sample_clean["SAMPLE_ID"]

# ================================
# 5️⃣ mapping
# ================================
sample_clean["PATIENT_ID"] = sample_clean["PATIENT_ID_original"].map(patient_dict)
sample_clean["PATIENT_ID"] = sample_clean["PATIENT_ID"].astype(str)

sample_clean["case_id"] = sample_clean["PATIENT_ID"].map(case_dict)

print("⚠️ missing PATIENT_ID:", sample_clean["PATIENT_ID"].isna().sum())
print("⚠️ missing case_id:", sample_clean["case_id"].isna().sum())

# ================================
# 6️⃣ 清洗（关键顺序）
# ================================

# 🔥 先处理字符串（不要破坏 None）
sample_clean["SAMPLE_TYPE_ID"] = sample_clean["SAMPLE_TYPE_ID"].str.strip()

# 数值
sample_clean["PURITY"] = pd.to_numeric(sample_clean["PURITY"], errors="coerce").round(4)
sample_clean["TMB_NONSYNONYMOUS"] = pd.to_numeric(
    sample_clean["TMB_NONSYNONYMOUS"], errors="coerce"
).round(6)

# 🔥 最后统一 NULL（关键！！）
sample_clean = sample_clean.replace({
    "NA": None,
    "": None,
    "nan": None,
    "NaN": None,
    "None": None
})
# sample_clean["SAMPLE_TYPE_ID"] = sample_clean["SAMPLE_TYPE_ID"].replace("", None)
sample_clean["SAMPLE_TYPE_ID"] = sample_clean["SAMPLE_TYPE_ID"].fillna("Primary")
# ================================
# 7️⃣ 列选择
# ================================
sample_out = sample_clean[[
    "SAMPLE_ID",
    "case_id",
    "PURITY",
    "SAMPLE_TYPE_ID",
    "SOMATIC_STATUS",
    "TMB_NONSYNONYMOUS",
    "ONCOTREE_CODE",
    "HISTOLOGICAL_GRADE",
    "EXOME_SEQ",
    "RNA_SEQ_ANALYSIS",
    "SEQUENCING_TYPE",
    "Tumor_Sample_Barcode"
]].copy()

sample_out = sample_out.rename(columns={
    "SAMPLE_ID": "Sample_Id_original"
})

# ================================
# 8️⃣ 保存
# ================================
out_sample = os.path.join(base_dir, "data/08sample_table.csv")
sample_out.to_csv(out_sample, index=False)

print("✅ sample table done")
# ================================
# 🔟 score 表（最终版）
# ================================

# ❗ 不要关连接（conn 还要用）
# conn.close() 这一行删掉！！！

# 1️⃣ 从数据库拿 mapping
score_map = pd.read_sql(
    "SELECT Sample_Id, Sample_Id_original FROM sample",
    conn
)

score_map["Sample_Id_original"] = score_map["Sample_Id_original"].astype(str)

sample_dict = dict(zip(
    score_map["Sample_Id_original"],
    score_map["Sample_Id"]
))

# ================================
# 2️⃣ 从 sample 原始文件提 score
# ================================

score_df = sample_df.copy()

# ⚠️ 只保留你需要的列
score_df = score_df[[
    "SAMPLE_ID",
    "IMSIG_B_CELLS",
    "IMSIG_INTERFERON",
    "IMSIG_MACROPHAGES",
    "IMSIG_MONOCYTES",
    "IMSIG_NEUTROPHILS",
    "IMSIG_NK_CELLS",
    "IMSIG_PLASMA_CELLS",
    "IMSIG_PROLIFERATION",
    "IMSIG_T_CELLS",
    "IMSIG_TRANSLATION"
]].copy()

# ================================
# 3️⃣ mapping Sample_Id
# ================================
score_df["Sample_Id"] = score_df["SAMPLE_ID"].map(sample_dict)

print("⚠️ missing Sample_Id:", score_df["Sample_Id"].isna().sum())

# ================================
# 4️⃣ 清洗数据（关键）
# ================================

score_cols = [
    "IMSIG_B_CELLS",
    "IMSIG_INTERFERON",
    "IMSIG_MACROPHAGES",
    "IMSIG_MONOCYTES",
    "IMSIG_NEUTROPHILS",
    "IMSIG_NK_CELLS",
    "IMSIG_PLASMA_CELLS",
    "IMSIG_PROLIFERATION",
    "IMSIG_T_CELLS",
    "IMSIG_TRANSLATION"
]

# 转数值（NA 自动变 NULL）
for col in score_cols:
    score_df[col] = pd.to_numeric(score_df[col], errors="coerce").round(6)

# ================================
# 5️⃣ 最终输出
# ================================
score_out = score_df[[
    "Sample_Id",
    *score_cols
]].copy()

# ❗ 删除没有 mapping 的（必须）
score_out = score_out.dropna(subset=["Sample_Id"])

# 转 int（数据库需要）
score_out["Sample_Id"] = score_out["Sample_Id"].astype(int)

# ================================
# 6️⃣ 保存
# ================================
out_score = os.path.join(base_dir, "data/09score_table.csv")
score_out.to_csv(out_score, index=False)

print("✅ score table done")

# ================================
# 🔟 treatment 表（最终版）
# ================================

# 1️⃣ 从数据库拿 case mapping
case_df = pd.read_sql(
    "SELECT case_id, PATIENT_ID FROM admission",
    conn
)

case_df["PATIENT_ID"] = case_df["PATIENT_ID"].astype(str)

case_dict = dict(zip(
    case_df["PATIENT_ID"],
    case_df["case_id"]
))

# ================================
# 2️⃣ 提取 treatment 信息（来自 patient 文件）
# ================================
treatment_df = df[[
    "PATIENT_ID_original",
    "TKI_TREATMENT",
    "CHEMOTHERAPY"
]].copy()

# ================================
# 3️⃣ mapping PATIENT_ID → case_id
# ================================
treatment_df["PATIENT_ID"] = treatment_df["PATIENT_ID_original"].map(patient_dict)
treatment_df["PATIENT_ID"] = treatment_df["PATIENT_ID"].astype(str)

treatment_df["case_id"] = treatment_df["PATIENT_ID"].map(case_dict)

print("⚠️ missing case_id:", treatment_df["case_id"].isna().sum())

# ================================
# 4️⃣ 清洗
# ================================

# TKI → boolean
treatment_df["TKI_TREATMENT"] = (
    treatment_df["TKI_TREATMENT"]
    .astype(str)
    .str.strip()
    .replace({
        "Yes": 1,
        "No": 0,
        "NA": None,
        "nan": None,   # 🔥 关键
        "": None
    })
)

# 再转成数值（让 None 变 NaN，方便导出）
treatment_df["TKI_TREATMENT"] = pd.to_numeric(
    treatment_df["TKI_TREATMENT"],
    errors="coerce"
)

# CHEMOTHERAPY → 直接保留字符串（后面做表）
treatment_df["CHEMOTHERAPY"] = (
    treatment_df["CHEMOTHERAPY"]
    .astype(str)
    .str.strip()
    .replace({
        "Yes": 1,
        "No": 0,
        "NA": None,
        "nan": None,
        "": None
    })
)

treatment_df["CHEMOTHERAPY"] = pd.to_numeric(
    treatment_df["CHEMOTHERAPY"],
    errors="coerce"
)

# ================================
# 5️⃣ 去重（一个 case 一行）
# ================================
treatment_df = treatment_df.drop_duplicates(subset=["case_id"])

# ================================
# 6️⃣ 输出
# ================================
treatment_out = treatment_df[[
    "case_id",
    "TKI_TREATMENT",
    "CHEMOTHERAPY"
]].copy()

out_treatment = os.path.join(base_dir, "data/10treatment_table.csv")
treatment_out.to_csv(out_treatment, index=False)

print("✅ treatment table done")
# ================================
# 🔟 mutation 表（最终版）
# ================================

# 1️⃣ 从数据库拿 gene mapping
gene_map = pd.read_sql(
    "SELECT gene_id, Hugo_Symbol FROM gene",
    conn
)

# 清洗（防止大小写/空格问题）
gene_map["Hugo_Symbol"] = (
    gene_map["Hugo_Symbol"]
    .astype(str)
    .str.strip()
    .str.upper()
)

gene_dict = dict(zip(
    gene_map["Hugo_Symbol"],
    gene_map["gene_id"]
))

# ================================
# 2️⃣ 基础 mutation 数据
# ================================
mut_df = mutation_df.copy()

# 清洗 symbol（必须和 gene 一致）
mut_df["Hugo_Symbol"] = (
    mut_df["Hugo_Symbol"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# ================================
# 3️⃣ 映射 gene_id
# ================================
mut_df["gene_id"] = mut_df["Hugo_Symbol"].map(gene_dict)

print("⚠️ missing gene_id:", mut_df["gene_id"].isna().sum())

# ================================
# 4️⃣ 数值清洗（关键）
# ================================
mut_df["Start_Position"] = pd.to_numeric(
    mut_df["Start_Position"], errors="coerce"
)

mut_df["End_Position"] = pd.to_numeric(
    mut_df["End_Position"], errors="coerce"
)

# ================================
# 5️⃣ 字符串清洗
# ================================
mut_df["Chromosome"] = mut_df["Chromosome"].astype(str).str.strip()
mut_df["Strand"] = mut_df["Strand"].astype(str).str.strip()
mut_df["NCBI_Build"] = mut_df["NCBI_Build"].astype(str).str.strip()

# 🔥 NULL 统一（非常重要）
mut_df = mut_df.replace({
    "NA": None,
    "": None,
    "nan": None,
    "NaN": None
})

# ================================
# 6️⃣ 去掉无效 mutation（否则 UNIQUE/NOT NULL 会炸）
# ================================
mut_df = mut_df.dropna(subset=[
    "Chromosome",
    "Start_Position",
    "End_Position",
    "Reference_Allele",
    "NCBI_Build"
])

# ================================
# 7️⃣ 去重（匹配你的 UNIQUE 约束）
# ================================
mut_df = mut_df.drop_duplicates(subset=[
    "Chromosome",
    "Start_Position",
    "End_Position",
    "Strand",
    "Reference_Allele",
    "NCBI_Build"
])

# ================================
# 8️⃣ 选列（严格对齐 SQL）
# ================================
mutation_out = mut_df[[
    "Chromosome",
    "Start_Position",
    "End_Position",
    "Strand",
    "NCBI_Build",
    "gene_id",
    "Variant_Classification",
    "Variant_Type",
    "Reference_Allele"
]].copy()
mut_df["gene_id"] = mut_df["gene_id"].where(
    pd.notna(mut_df["gene_id"]),
    None
)
# ================================
# 9️⃣ 保存
# ================================
out_mutation = os.path.join(base_dir, "data/11mutation_table.csv")
mutation_out.to_csv(out_mutation, index=False)

print("✅ mutation table done")

###################################
# ================================
# 🔟 sample_mutation 表（最终稳定版）
# ================================

# 1️⃣ mutation mapping（唯一键 → mutation_id）
mut_map = pd.read_sql("""
SELECT
    mutation_id,
    Chromosome,
    Start_Position,
    End_Position,
    Strand,
    Reference_Allele,
    NCBI_Build
FROM mutations
""", conn)

# 2️⃣ sample mapping（barcode → Sample_Id）
samp_map = pd.read_sql("""
SELECT Sample_Id, Sample_Id_original
FROM sample
""", conn)

# ================================
# 3️⃣ 清洗 mapping（防 join 失败）
# ================================
mut_map["Chromosome"] = mut_map["Chromosome"].astype(str).str.strip()
mut_map["Strand"] = mut_map["Strand"].astype(str).str.strip()
mut_map["Reference_Allele"] = mut_map["Reference_Allele"].astype(str).str.strip()
mut_map["NCBI_Build"] = mut_map["NCBI_Build"].astype(str).str.strip()

samp_map["Sample_Id_original"] = samp_map["Sample_Id_original"].astype(str).str.strip()

# ================================
# 4️⃣ 从 mutation 原始数据取字段
# ================================
sm_df = mutation_df[[
    "Tumor_Sample_Barcode",
    "Chromosome",
    "Start_Position",
    "End_Position",
    "Strand",
    "Reference_Allele",
    "NCBI_Build",
    "t_ref_count",
    "t_alt_count",
    "Tumor_Seq_Allele1",
    "Tumor_Seq_Allele2"
]].copy()

# ================================
# 5️⃣ 清洗（非常关键）
# ================================
sm_df["Tumor_Sample_Barcode"] = sm_df["Tumor_Sample_Barcode"].astype(str).str.strip()
sm_df["Chromosome"] = sm_df["Chromosome"].astype(str).str.strip()
sm_df["Strand"] = sm_df["Strand"].astype(str).str.strip()
sm_df["Reference_Allele"] = sm_df["Reference_Allele"].astype(str).str.strip()
sm_df["NCBI_Build"] = sm_df["NCBI_Build"].astype(str).str.strip()

sm_df["Start_Position"] = pd.to_numeric(sm_df["Start_Position"], errors="coerce")
sm_df["End_Position"]   = pd.to_numeric(sm_df["End_Position"], errors="coerce")

# 数值列
for c in ["t_ref_count", "t_alt_count"]:
    sm_df[c] = pd.to_numeric(sm_df[c], errors="coerce")

# 统一 NULL（防止 "" 进数据库报错）
sm_df = sm_df.replace({
    "NA": None,
    "": None,
    "nan": None,
    "NaN": None
})

# ================================
# 6️⃣ 映射 Sample_Id
# ================================
sm_df = sm_df.merge(
    samp_map,
    left_on="Tumor_Sample_Barcode",
    right_on="Sample_Id_original",
    how="left"
)

# ================================
# 7️⃣ 映射 mutation_id（核心 join）
# ================================
join_keys = [
    "Chromosome",
    "Start_Position",
    "End_Position",
    "Strand",
    "Reference_Allele",
    "NCBI_Build"
]

sm_df = sm_df.merge(
    mut_map,
    on=join_keys,
    how="left"
)

# ================================
# 8️⃣ 检查
# ================================
print("⚠️ missing Sample_Id:", sm_df["Sample_Id"].isna().sum())
print("⚠️ missing mutation_id:", sm_df["mutation_id"].isna().sum())

# ================================
# 9️⃣ 删除无法映射（避免 FK error）
# ================================
sm_df = sm_df.dropna(subset=["Sample_Id", "mutation_id"])

# 转 int（外键要求）
sm_df["Sample_Id"] = sm_df["Sample_Id"].astype(int)
sm_df["mutation_id"] = sm_df["mutation_id"].astype(int)

# ================================
# 🔟 去重（复合主键）
# ================================
sm_df = sm_df.drop_duplicates(subset=["Sample_Id", "mutation_id"])

# ================================
# 1️⃣1️⃣ 输出
# ================================
sm_out = sm_df[[
    "Sample_Id",
    "mutation_id",
    "t_ref_count",
    "t_alt_count",
    "Tumor_Seq_Allele1",
    "Tumor_Seq_Allele2"
]].copy()

# 保证整数列可为空
sm_out["t_ref_count"] = sm_out["t_ref_count"].astype("Int64")
sm_out["t_alt_count"] = sm_out["t_alt_count"].astype("Int64")

# ================================
# 1️⃣2️⃣ 保存
# ================================
out_sm = os.path.join(base_dir, "data/12sample_mutation_table.csv")
sm_out.to_csv(out_sm, index=False)

print("✅ sample_mutation table done")

# ================================
# 🔟 mutation_annotation 表（最终版）
# ================================

# 1️⃣ mutation mapping（唯一键 → mutation_id）
mut_map = pd.read_sql("""
SELECT
    mutation_id,
    Chromosome,
    Start_Position,
    End_Position,
    Strand,
    Reference_Allele,
    NCBI_Build
FROM mutations
""", conn)

# 2️⃣ consequence mapping（type → id）
con_map = pd.read_sql("""
SELECT consequence_id, consequence_type
FROM consequence
""", conn)

# ================================
# 3️⃣ 清洗 mapping
# ================================
for col in ["Chromosome", "Strand", "Reference_Allele", "NCBI_Build"]:
    mut_map[col] = mut_map[col].astype(str).str.strip()

con_map["consequence_type"] = con_map["consequence_type"].astype(str).str.strip().str.lower()

# ================================
# 4️⃣ 从 mutation 原始文件提取
# ================================
anno_df = mutation_df[[
    "Chromosome",
    "Start_Position",
    "End_Position",
    "Strand",
    "Reference_Allele",
    "NCBI_Build",
    "Transcript_ID",
    "Consequence",
    "RefSeq",
    "HGVSc",
    "HGVSp",
    "HGVSp_Short",
    "Codons",
    "Protein_position",
    "Amino_acid_change"
]].copy()

# ================================
# 5️⃣ 清洗
# ================================
for col in ["Chromosome", "Strand", "Reference_Allele", "NCBI_Build", "Transcript_ID"]:
    anno_df[col] = anno_df[col].astype(str).str.strip()

anno_df["Start_Position"] = pd.to_numeric(anno_df["Start_Position"], errors="coerce")
anno_df["End_Position"]   = pd.to_numeric(anno_df["End_Position"], errors="coerce")
anno_df["Protein_position"] = pd.to_numeric(anno_df["Protein_position"], errors="coerce")

# NA → NULL
anno_df = anno_df.replace({
    "NA": None,
    "": None,
    "nan": None,
    "NaN": None
})

# ================================
# 6️⃣ 拆分 consequence（关键）
# ================================
anno_df = anno_df.assign(
    consequence_type=anno_df["Consequence"].str.split(",")
).explode("consequence_type")

anno_df["consequence_type"] = (
    anno_df["consequence_type"]
    .astype(str)
    .str.strip()
    .str.lower()
)

# ================================
# 7️⃣ 映射 mutation_id
# ================================
join_keys = [
    "Chromosome",
    "Start_Position",
    "End_Position",
    "Strand",
    "Reference_Allele",
    "NCBI_Build"
]

anno_df = anno_df.merge(
    mut_map,
    on=join_keys,
    how="left"
)

# ================================
# 8️⃣ 映射 consequence_id
# ================================
anno_df = anno_df.merge(
    con_map,
    on="consequence_type",
    how="left"
)

print("⚠️ missing mutation_id:", anno_df["mutation_id"].isna().sum())
print("⚠️ missing consequence_id:", anno_df["consequence_id"].isna().sum())

# ================================
# 9️⃣ 删除无法映射（避免 FK error）
# ================================
anno_df = anno_df.dropna(subset=["mutation_id", "consequence_id", "Transcript_ID"])

anno_df["mutation_id"] = anno_df["mutation_id"].astype(int)
anno_df["consequence_id"] = anno_df["consequence_id"].astype(int)

# ================================
# 🔟 Amino_acid_change 生成（简单版）
# ================================
anno_df["Amino_acid_change"] = anno_df["Amino_acid_change"]

# ================================
# 1️⃣1️⃣ 去重（主键）
# ================================
anno_df = anno_df.drop_duplicates(
    subset=["mutation_id", "Transcript_ID", "consequence_id"]
)

# ================================
# 1️⃣2️⃣ 输出
# ================================
anno_out = anno_df[[
    "mutation_id",
    "Transcript_ID",
    "consequence_id",
    "RefSeq",
    "HGVSc",
    "HGVSp",
    "HGVSp_Short",
    "Codons",
    "Protein_position",
    "Amino_acid_change"
]].copy()

out_anno = os.path.join(base_dir, "data/13mutation_annotation_table.csv")
anno_out.to_csv(out_anno, index=False)

print("✅ mutation_annotation table done")


###############gene patch
# expression gene

expr_path = os.path.join(
    base_dir,
    "[done]data_mrna_seq_v2_rsem_zscores_ref_all_samples.txt"
)

expr_df = pd.read_csv(expr_path, sep="\t")

print("✅ expression loaded")
expr_genes = set(
    expr_df["Hugo_Symbol"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# 已有 gene 表
gene_map = pd.read_sql("SELECT Hugo_Symbol FROM gene", conn)

existing_genes = set(
    gene_map["Hugo_Symbol"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# 找缺失
missing_genes = expr_genes - existing_genes

print("missing genes:", len(missing_genes))
patch_df = pd.DataFrame({
    "Hugo_Symbol": list(missing_genes),
    "Entrez_Gene_Id": None
})

out_patch = os.path.join(base_dir, "data/gene_patch.csv")
patch_df.to_csv(out_patch, index=False)

print("✅ gene patch ready")


# ================================
# 🔟 gene_sample 表（最终版）
# ================================

# 1️⃣ 读 expression 文件
expr_path = os.path.join(
    base_dir,
    "[done]data_mrna_seq_v2_rsem_zscores_ref_all_samples.txt"
)
expr_df = pd.read_csv(expr_path, sep="\t")

# ================================
# 2️⃣ gene mapping（symbol → gene_id）
# ================================
gene_map = pd.read_sql("""
SELECT gene_id, Hugo_Symbol
FROM gene
""", conn)

gene_map["Hugo_Symbol"] = gene_map["Hugo_Symbol"].astype(str).str.strip().str.upper()

gene_dict = dict(zip(
    gene_map["Hugo_Symbol"],
    gene_map["gene_id"]
))

# ================================
# 3️⃣ sample mapping（A183 → Sample_Id）
# ================================
samp_map = pd.read_sql("""
SELECT Sample_Id, Sample_Id_original
FROM sample
""", conn)

samp_map["Sample_Id_original"] = samp_map["Sample_Id_original"].astype(str).str.strip()

sample_dict = dict(zip(
    samp_map["Sample_Id_original"],
    samp_map["Sample_Id"]
))

# ================================
# 4️⃣ melt（关键步骤！！！）
# ================================

# 前两列是 gene 信息，其余全是 sample
id_cols = ["Hugo_Symbol", "Entrez_Gene_Id"]

value_cols = [c for c in expr_df.columns if c not in id_cols]

long_df = expr_df.melt(
    id_vars=id_cols,
    value_vars=value_cols,
    var_name="Sample_Id_original",
    value_name="mRNA_expression"
)

# ================================
# 5️⃣ 清洗 gene
# ================================
long_df["Hugo_Symbol"] = (
    long_df["Hugo_Symbol"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# ================================
# 6️⃣ mapping gene_id
# ================================
long_df["gene_id"] = long_df["Hugo_Symbol"].map(gene_dict)

# ================================
# 7️⃣ mapping Sample_Id
# ================================
long_df["Sample_Id"] = long_df["Sample_Id_original"].map(sample_dict)

# ================================
# 8️⃣ expression 转数值
# ================================
long_df["mRNA_expression"] = pd.to_numeric(
    long_df["mRNA_expression"],
    errors="coerce"
).round(5)

# ================================
# 9️⃣ 检查
# ================================
print("⚠️ missing gene_id:", long_df["gene_id"].isna().sum())
print("⚠️ missing Sample_Id:", long_df["Sample_Id"].isna().sum())

# ================================
# 🔟 删除无法映射（避免 FK error）
# ================================
long_df = long_df.dropna(subset=["gene_id", "Sample_Id"])

# 转 int
long_df["gene_id"] = long_df["gene_id"].astype(int)
long_df["Sample_Id"] = long_df["Sample_Id"].astype(int)

# ================================
# 1️⃣1️⃣ 去重（主键）
# ================================
long_df = long_df.drop_duplicates(subset=["gene_id", "Sample_Id"])

# ================================
# 1️⃣2️⃣ 输出
# ================================
gene_sample_out = long_df[[
    "gene_id",
    "Sample_Id",
    "mRNA_expression"
]]

out_gene_sample = os.path.join(base_dir, "data/14gene_sample_table.csv")
gene_sample_out.to_csv(out_gene_sample, index=False)

print("✅ gene_sample table done")