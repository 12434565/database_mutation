import pandas as pd

# 读取文件（跳过前面注释行）
df = pd.read_csv("data_clinical_patient.txt", sep="\t", comment="#")

# -------------------------
# 1. 处理 OS_STATUS
# -------------------------
# 提取冒号前的数字
df["OS_STATUS"] = df["OS_STATUS"].str.split(":").str[0]

# 转为数值（无法转换的变成 NaN）
df["OS_STATUS"] = pd.to_numeric(df["OS_STATUS"], errors="coerce")

# -------------------------
# 2. 处理 OS_MONTHS
# -------------------------
df["OS_MONTHS"] = pd.to_numeric(df["OS_MONTHS"], errors="coerce")

# -------------------------
# 3. 删除 NA（只针对这两列）
# -------------------------
df = df.dropna(subset=["OS_STATUS", "OS_MONTHS"])

# -------------------------
# 4. 转换类型
# -------------------------
df["OS_STATUS"] = df["OS_STATUS"].astype(int)

# -------------------------
# 5. 保存文件
# -------------------------
df.to_csv("01clean_data/01clinical_patient_cleaned.txt", sep="\t", index=False)