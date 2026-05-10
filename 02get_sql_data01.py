import pandas as pd
import pymysql
import os

base_dir = "/Users/liulin/Desktop/database/project/luad_oncosg_2020/data/data_from_sql"
os.makedirs(base_dir, exist_ok=True)

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="********",
    database="luad"
)

# =====================
# 1️⃣ patient mapping
# =====================
patient_df = pd.read_sql(
    "SELECT PATIENT_ID, PATIENT_ID_original FROM patient",
    conn
)

patient_path = os.path.join(base_dir, "01patient_mapping.csv")
patient_df.to_csv(patient_path, index=False)

print("✅ patient_mapping saved")

# 同时生成 dict（后面直接用）
patient_dict = dict(zip(
    patient_df["PATIENT_ID_original"],
    patient_df["PATIENT_ID"]
))
