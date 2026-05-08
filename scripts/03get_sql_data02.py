import pandas as pd
import pymysql
import os

base_dir = "/Users/liulin/Desktop/database/project/luad_oncosg_2020/data/data_from_sql"
os.makedirs(base_dir, exist_ok=True)

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="********",
    database="luad_oncosg"
)

# =====================
# 2️⃣ case mapping
# =====================
case_df = pd.read_sql(
    "SELECT case_id, PATIENT_ID FROM admission",
    conn
)

case_path = os.path.join(base_dir, "02case_mapping.csv")
case_df.to_csv(case_path, index=False)

print("✅ case_mapping saved")

case_dict = dict(zip(
    case_df["PATIENT_ID"],
    case_df["case_id"]
))