-- when you load data, you may need to change the path of the file
-- also if you see "Loading local data is disabled", you can run the following command
-- SET GLOBAL local_infile = 1;
LOAD DATA LOCAL INFILE '/Users/liulin/Desktop/database/project/luad_oncosg_2020/data/01patient_table.csv'
INTO TABLE patient
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(PATIENT_ID_original, SEX, ETHNICITY, COHORT);
select * from patient limit 5;

-- 1️⃣ cancer_type
LOAD DATA LOCAL INFILE '/Users/liulin/Desktop/database/project/luad_oncosg_2020/data/02cancer_type_table.csv'
INTO TABLE cancer_type
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(ONCOTREE_CODE, CANCER_TYPE, CANCER_TYPE_DETAILED);
select * from cancer_type limit 5;

-- 2️⃣ cancer_subtype
LOAD DATA LOCAL INFILE '/Users/liulin/Desktop/database/project/luad_oncosg_2020/data/03subtype_table.csv'
INTO TABLE cancer_subtype
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(ONCOTREE_CODE, SUBTYPE_MAIN, SUBTYPE_DETAIL, ICD_CODE);
select * from cancer_subtype limit 5;

-- 3️⃣ sample_type
LOAD DATA LOCAL INFILE '/Users/liulin/Desktop/database/project/luad_oncosg_2020/data/04sample_type_table.csv'
INTO TABLE sample_type
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(SAMPLE_TYPE_ID, SAMPLE_CLASS);
select * from sample_type limit 5;

-- 4️⃣ gene
LOAD DATA LOCAL INFILE '/Users/liulin/Desktop/database/project/luad_oncosg_2020/data/05gene_table.csv'
INTO TABLE gene
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(Entrez_Gene_Id, Hugo_Symbol);
select * from gene limit 5;


-- 5️⃣ consequence
LOAD DATA LOCAL INFILE '/Users/liulin/Desktop/database/project/luad_oncosg_2020/data/06consequence_table.csv'
INTO TABLE consequence
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(@ctype)
SET consequence_type = NULLIF(TRIM(@ctype), '');
select * from consequence limit 5;