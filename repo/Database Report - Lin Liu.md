# Database Report - Lin Liu
**To have a better view, highly recommend click [this link](https://www.notion.so/llsp/Database-Report-Lin-Liu-35a06d13592280d084c8d06f0aa8961c?source=copy_link)**
# 1 project overview

## Summary

This project transforms the LUAD (OncoSG, 2020) study files into a structured mutation database. It cleans clinical, sample, mutation, and expression data with Python, loads the curated results into a normalized MySQL schema with 14 related tables, and then exports graph-friendly CSV files for downstream Neo4j use. The repository already includes both the raw study inputs and the generated intermediate CSV tables, so you can either reproduce the pipeline step by step or take the faster route and import the committed outputs directly.

## purpose and scope

### Purpose:

1. build one specific cancer type database from cBioPortal which has a large amount of different cancer type, mutation and patients information datasets.
2. In this project, we want to find interesting genes or variants within dataset. to achieve this goal, we use MySQL, Python and Neo4j. MySQL is a free SQL software, it allows user to run SQL query and build databases in local and server. Neo4j also is a software. it is used to find interesting genes and variants within datasets.

### Scope

project including:

- patient clinical information
- sample metadata
- mutation data
- mutation annotation
- gene expression
- immune score information
- cancer subtype information

project not including:

- raw sequencing FASTQ/BAM files
- imaging data
- longitudinal follow-up beyond OS
- normal tissue multi-omics

# 2 Data source

1. datasets are Lung Adenocarcinoma(LUAD, OncoSG, Nat Genet 2020) from cBioPortal. You can download raw data from this  website([https://www.cbioportal.org/study/summary?id=luad_oncosg_2020](https://www.cbioportal.org/study/summary?id=luad_oncosg_2020))
2. our database has 14 tables, including patient, sample, mutation, 3 main tables. also include admission, treatment, gene_sample et al. other tables. through this databases you are able to figure out what mutations happened in a specific patient and what consequence of that mutation causes.
3. This data source provide lots of information including mutations, patients, samples, and some statistics information.

# 3 data cleaning strategy

This writeup summarizes the data-cleaning logic that is explicitly implemented in the repository, mainly in `01extract.py` and the SQL load scripts. It focuses on what was actually changed in code. Where the code does not make the reason fully explicit, the note is left conservative rather than guessed.

## Global patterns

- Raw study identifiers were preserved first, then mapped to MySQL-generated IDs later in the pipeline.
- Text fields used for joins were often normalized with whitespace stripping and, where needed, case normalization.
- Placeholder missing values such as `""`, `NA`, `NaN`, `nan`, and `None` were repeatedly converted to SQL-style nulls.
- Numeric fields were usually cleaned with `pd.to_numeric(..., errors="coerce")`, so invalid values became null instead of stopping the pipeline.
- Duplicate removal was used heavily, especially where SQL keys or table semantics required one row per entity.
- Rows that could not be mapped to required foreign keys were often counted and then dropped before load.
- Some cleaning happened in stages because later tables depend on database IDs created by earlier loads.

## Core dimension tables

### 01 patient

- **Cleaning actions:** `PATIENT_ID` was renamed to `PATIENT_ID_original`; only `PATIENT_ID_original`, `SEX`, `ETHNICITY`, and `COHORT` were kept.
- **Data handling:** Exact duplicates were removed with `drop_duplicates()`. No explicit fill rule for missing `SEX`, `ETHNICITY`, or `COHORT` appears in code.
- **Reason visible in code:** The rename preserves the raw study ID while leaving room for the database-generated `PATIENT_ID`.

### 02 cancer_type

- **Cleaning actions:** `ONCOTREE_CODE`, `CANCER_TYPE`, and `CANCER_TYPE_DETAILED` were extracted from merged sample/patient context.
- **Data handling:** Duplicate rows were removed, and rows missing `ONCOTREE_CODE` were dropped.
- **Reason visible in code:** `ONCOTREE_CODE` is the downstream key, so rows without it would not support foreign-key use.

### 03 cancer_subtype

- **Cleaning actions:** `ADENOCARCINOMA_SUBTYPE_WHO2015` was split into `SUBTYPE_MAIN`, `SUBTYPE_DETAIL`, and `ICD_CODE`. ICD codes were extracted from parentheses with regex. Several subtype names were manually normalized, including `micropapillary`, `papillary`, `acinar`, `solid`, `lepidic`, `minimally invasive`, `mucinous`, and `NSCLC`.
- **Data handling:** Missing subtype values return null outputs. ICD codes are removed from the text after extraction. Duplicate rows were removed, and rows where all subtype outputs were empty were dropped.
- **Reason visible in code:** The raw subtype field mixes text labels and ICD codes, so it is being converted into a more structured relational form.

### 04 sample_type

- **Cleaning actions:** Only `SAMPLE_TYPE_ID` and `SAMPLE_CLASS` were kept. Both fields were stripped of surrounding whitespace, and `SAMPLE_TYPE_ID` was capitalized.
- **Data handling:** Duplicate rows were removed. Rows with missing `SAMPLE_TYPE_ID` were dropped.
- **Reason visible in code:** The script comments explicitly mention dropping missing sample types to avoid foreign-key problems. Capitalization appears intended to reduce duplicate variants caused by inconsistent case.

### 05 gene

- **Cleaning actions:** Only `Entrez_Gene_Id` and `Hugo_Symbol` were kept from mutation data. `Hugo_Symbol` was stripped and uppercased. Empty symbols and `[NOT AVAILABLE]` were removed. `Entrez_Gene_Id` was stripped.
- **Data handling:** Rows missing `Hugo_Symbol` were dropped. `Entrez_Gene_Id` placeholders such as `""`, `NA`, `NaN`, `nan`, `None`, and `0` were converted to null. Duplicates were removed after standardization.
- **Reason visible in code:** Gene symbols are treated as the main identity used for later mapping; invalid Entrez values were kept only as nulls rather than trusted as real IDs.

### 06 consequence

- **Cleaning actions:** The raw `Consequence` field was extracted, cast to string, split on commas, and exploded into one row per consequence value. The resulting labels were stripped and lowercased.
- **Data handling:** Rows missing `Consequence` were dropped. Empty split results were removed. Duplicate `consequence_type` values were removed.
- **Reason visible in code:** The SQL schema stores consequence types as a normalized lookup table with uniqueness, so a multi-valued text field had to be separated into distinct rows.

---

### 07 admission

- **Cleaning actions:** `AGE` was renamed to `patient_age`. `SMOKING_PACK_YEARS` and `OS_MONTHS` were coerced to numeric and rounded to 2 decimals. `OS_STATUS` was split on `:` and only the prefix was kept before numeric conversion. `CHEMOTHERAPY` and `TKI_TREATMENT` were normalized through `normalize_yes_no_flag(...)`.
- **Data handling:** One row per `PATIENT_ID_original` was kept. Raw patient IDs were mapped to database `PATIENT_ID` using `01patient_mapping.csv`. Missing patient mappings were counted and printed. Invalid numerics became null.
- **Reason visible in code:** The rename preserves a cleaner schema field name, and the comments explicitly say this table should have one admission row per patient. The `OS_STATUS` cleaning suggests the raw field contains composite text like `0:...` or `1:...`, and only the status prefix is needed.

### 08 sample

- **Cleaning actions:** Sample rows were merged with patient-derived fields such as `HISTOLOGICAL_GRADE`, `EXOME_SEQ`, `RNA_SEQ_ANALYSIS`, and `SEQUENCING_TYPE`. `Tumor_Sample_Barcode` was set directly from `SAMPLE_ID`. The subtype join fields were normalized with `normalize_optional_text(...)` before merging to `subtype_id`. `SAMPLE_TYPE_ID` was stripped. `PURITY` was coerced to numeric and rounded to 4 decimals. `TMB_NONSYNONYMOUS` was coerced to numeric and rounded to 6 decimals. `SAMPLE_ID` was renamed to `Sample_Id_original` in the final output.
- **Data handling:** Patient IDs were mapped to database `PATIENT_ID`, then to `case_id`. Standard null placeholders were normalized to null. Missing `SAMPLE_TYPE_ID` was filled with `"Primary"`. The script prints counts for missing `PATIENT_ID`, `case_id`, and `subtype_id` after mapping.
- **Reason visible in code:** The comment says using `SAMPLE_ID` directly as `Tumor_Sample_Barcode` is more stable. Filling missing sample type with `"Primary"` appears to be a foreign-key-oriented default, but the exact domain reason is not documented in code.

### 09 score

- **Cleaning actions:** Only the immune score columns plus `SAMPLE_ID` were kept. Each score column was coerced to numeric and rounded to 6 decimals.
- **Data handling:** `SAMPLE_ID` was mapped to database `Sample_Id`. Rows missing `Sample_Id` after mapping were dropped. `Sample_Id` was then cast to integer for load.
- **Reason visible in code:** The score table is keyed by database `Sample_Id`, so unmapped rows could not be loaded safely.

### 10 treatment

- **Current status:** No active standalone `treatment` table cleaning step is implemented in the current root-script workflow.
- **What changed in code:** Treatment-related values are currently cleaned inside `07 admission` as `chemotherapy_state` and `TKI_TREATMENT`.
- **Reason visible in code:** The current root SQL schema stores treatment fields on `admission`, and `03load_dependent_table.sql` does not load `10treatment_table.csv`.

---

### 11 mutations

- **Cleaning actions:** Gene symbols in both the lookup table and mutation data were stripped and uppercased before mapping to `gene_id`. `Start_Position` and `End_Position` were coerced to numeric. `Chromosome`, `Strand`, and `NCBI_Build` were stripped.
- **Data handling:** Standard placeholder strings were converted to null. Rows missing `Chromosome`, `Start_Position`, `End_Position`, `Reference_Allele`, or `NCBI_Build` were dropped. Duplicates were removed on the same fields used by the SQL uniqueness rule: `Chromosome`, `Start_Position`, `End_Position`, `Strand`, `Reference_Allele`, and `NCBI_Build`. Missing `gene_id` values were counted but did not automatically force the mutation row itself to be dropped.
- **Reason visible in code:** The script explicitly says invalid mutations are removed to avoid breaking SQL `UNIQUE` and `NOT NULL` constraints.

### 12 sample_mutation

- **Cleaning actions:** Join fields used to recover `Sample_Id` and `mutation_id` were stripped in both mapping tables and raw data. Position fields and read-count fields were coerced to numeric.
- **Data handling:** Standard placeholder strings were converted to null. `Tumor_Sample_Barcode` was mapped to `Sample_Id`, and mutation identity fields were mapped to `mutation_id`. Rows missing either key were dropped. Remaining keys were cast to integers. Duplicates were removed on the composite key (`Sample_Id`, `mutation_id`). `t_ref_count` and `t_alt_count` were exported as nullable integers.
- **Reason visible in code:** The comments explicitly say unmappable rows are removed to avoid foreign-key errors, and the deduplication matches the composite primary key in SQL.

### 13 mutation_annotation

- **Cleaning actions:** Mutation lookup fields were stripped, and consequence lookup values were stripped and lowercased. Raw annotation fields were stripped. `Start_Position`, `End_Position`, and `Protein_position` were coerced to numeric. `Consequence` was split on commas and exploded into one consequence per row.
- **Data handling:** Standard placeholder strings were converted to null. Consequence labels were normalized to lowercase for mapping. Rows missing `mutation_id`, `consequence_id`, or `Transcript_ID` were dropped. Remaining IDs were cast to integers. Duplicates were removed on (`mutation_id`, `Transcript_ID`, `consequence_id`).
- **Reason visible in code:** The comments explicitly say unmappable rows are removed to avoid foreign-key failures, and the deduplication matches the SQL primary key for this table.

---

### gene_patch

- **Cleaning actions:** Gene symbols from the expression file and the existing gene table were stripped and uppercased, then compared as sets.
- **Data handling:** Any expression gene missing from the gene table was written to `gene_patch.csv` with `Entrez_Gene_Id = NULL`.
- **Reason visible in code:** This patch step allows expression-linked genes missing from the mutation-derived gene table to be added before building `gene_sample`.

### 14 gene_sample

- **Cleaning actions:** The expression matrix was reshaped from wide to long with `melt`. Gene symbols were stripped and uppercased before mapping to `gene_id`. Sample column names were mapped to database `Sample_Id`. `mRNA_expression` was coerced to numeric and rounded to 5 decimals.
- **Data handling:** Rows missing `gene_id` or `Sample_Id` were dropped. Both keys were cast to integers. Duplicates were removed on (`gene_id`, `Sample_Id`).
- **Reason visible in code:** The SQL table stores one expression value per gene-sample pair, so wide expression data had to be normalized into long form. Unmappable rows were removed to avoid foreign-key failures.

## SQL load-time cleaning

- In `02load_independent_table.sql`, `consequence_type` is trimmed and empty strings are converted to null with `NULLIF(TRIM(@ctype), '')`.
- In `03load_dependent_table.sql`, the `admission` and `sample` loads use `NULLIF(TRIM(...), '')` so that empty strings are converted to null at load time for those fields.

# 4 important decisions(Database design decisions)

### LOAD DATA

there are two way to load data. one is using insert to upload one by one. the other is using `LOAD DATA LOCAL` . both of them have advantages and disadvantages. I select using load query because I don’t prefer repeating my job even ask LLM to repeat. however one problem using LOAD query is if one table’s foreign key is create by `auto_increment`  there will be some troubles. but it is solvable by loading data in a specific order.

so here i am going to introduce how to load data in my database.

first step is find tables which not rely on other tables. in my db they are patient, cancer_type, cancer_subtype, sample_type, gene and consequence. 

then, we should add tables which connect with these tables directly and known all foreign key already. In here, they are admission and mutation.

![image.png](Database%20Report%20-%20Lin%20Liu/image.png)

![image.png](Database%20Report%20-%20Lin%20Liu/image%201.png)

next is sample, treatment, mutation_annotation

next is sample mutation, gene_sample.

### Neo4j

Clinical information was merged into neo4j1/sample_big_table.csv
to simplify Neo4j graph import and reduce complex joins.

# 5 Normal form and deviations

## ER model

![ER (2).png](Database%20Report%20-%20Lin%20Liu/ER_(2).png)

## NF

### 1NF

requires all attributes to contain atomic values.

**patient**(ID, sex, cohort, ethnicity)

**sample**(Sample_Id, case_id, PURITY, SAMPLE_TYPE_ID,  SOMATIC_STATUS, TMB_NONSYNONYMOUS, ONCOTREE_CODE, HISTOLOGICAL_GRADE, EXOME_SEQ, RNA_SEQ_ANALYSIS, SEQUENCING_TYPE, Tumor_Sample_Barcode, 
SAMPLE_CLASS, 
IMSIG_B_CELLS, IMSIG_INTERFERON, IMSIG_MACROPHAGES, IMSIG_MONOCYTES, IMSIG_NEUTROPHILS, IMSIG_NK_CELLS, IMSIG_PLASMA_CELLS, IMSIG_PROLIFERATION, IMSIG_T_CELLS, IMSIG_TRANSLATION,
CANCER_TYPE, CANCER_TYPE_DETAILED, ~~subtype~~SUBTYPE_MAIN, SUBTYPE_DETAIL, ICD_CODE)

<aside>
📌

subtype are not undivided. so change it to SUBTYPE_MAIN, SUBTYPE_DETAIL, ICD_CODE

</aside>

**admission**(case_id, PATIENT_ID, SMOKING_STATUS, SMOKING_PACK_YEARS, OS_STATUS, OS_MONTHS, patient_age, STAGE)

**gene**(gene_id, Entrez_Gene_Id, Hugo_Symbol)

**gene-sample**(gene_id, Sample_Id, mRNA-expression)

**mutation**(mutation_id, Start_Position, End_Position, Chromosome, Strand, NCBI_Build, Variant_Classification, Variant_Type, Reference_Allele)

**mutation-gene**(mutation_id, gene_id)

**sample-mutation**(sample_id, mutation_id, t_ref_count, t_alt_count, Tumor_Seq_Allele1, Tumor_Seq_Allele2)

**consequence**(consequence_id, consequence_type)

**annotation**(mutation_id, Transcript_ID, consequence_id, RefSeq, HGVSc, HGVSp, HGVSp_Short, Codons, Protein_position, Amino_acid_change)

---

### 2NF

non-prime attributes must fully depend on the whole primary key

same with 1NF because gene-sample, sample-mutation, annotation tables don’t rely on single primary key.

### 3NF

**sample**(Sample_Id, case_id, PURITY,  SOMATIC_STATUS, TMB_NONSYNONYMOUS, HISTOLOGICAL_GRADE, EXOME_SEQ, RNA_SEQ_ANALYSIS, SEQUENCING_TYPE, Tumor_Sample_Barcode, subtype_id, score_id, SAMPLE_TYPE_ID)

**cancer_type**(ONCOTREE_CODE, CANCER_TYPE, CANCER_TYPE_DETAILED)

**cancer_subtype**(subtype_id, ONCOTREE_CODE, SUBTYPE_MAIN, SUBTYPE_DETAIL, ICD_CODE)

**sample_type**(SAMPLE_TYPE_ID, SAMPLE_CLASS)

**score**(score_id, IMSIG_B_CELLS, IMSIG_INTERFERON, IMSIG_MACROPHAGES, IMSIG_MONOCYTES, IMSIG_NEUTROPHILS, IMSIG_NK_CELLS, IMSIG_PLASMA_CELLS, IMSIG_PROLIFERATION, IMSIG_T_CELLS, IMSIG_TRANSLATION)

<aside>
📌

ONCOTREE_CODE → CANCER_TYPE

CANCER_TYPE → CANCER_TYPE_DETAILED

ICD_CODE → SUBTYPE_MAIN + SUBTYPE_DETAIL

sample_type_id → sample class

create three new table to store them

create score table to make table more flexible. not because of NF.

</aside>

**gene**(gene_id, Entrez_Gene_Id, Hugo_Symbol)

<aside>
📌

This table design makes sense because there are situations where either Entrez_Gene_Id or Hugo_Symbol is NULL. Therefore, we cannot use Entrez_Gene_Id as the primary key, since primary keys cannot contain NULL values. The same issue applies to Hugo_Symbol. As a result, a separate surrogate key gene_id is used as the primary key.

</aside>

### BCNF

<aside>
📌

The annotation table satisfies BCNF because the composite primary key (mutation_id, Transcript_ID) determines all non-key attributes. No non-key attribute independently determines another attribute, so every determinant is a candidate key.

</aside>

<aside>
📌

The cancer_subtype table does not violate BCNF because ICD_CODE cannot be used as a candidate key. Some subtype records have NULL ICD_CODE values, so ICD_CODE cannot uniquely determine SUBTYPE_MAIN and SUBTYPE_DETAIL for all tuples. Therefore, subtype_id is used as the primary key.

</aside>

### **4NF**

**Multivalued Dependency, MVD**

**patient**(ID, sex, cohort, ethnicity)

**sample**(Sample_Id, case_id, PURITY,  SOMATIC_STATUS, TMB_NONSYNONYMOUS, HISTOLOGICAL_GRADE, EXOME_SEQ, RNA_SEQ_ANALYSIS, SEQUENCING_TYPE, Tumor_Sample_Barcode, subtype_id, score_id, SAMPLE_TYPE_ID)

**cancer_type**(ONCOTREE_CODE, CANCER_TYPE, CANCER_TYPE_DETAILED)

**cancer_subtype**(subtype_id, ONCOTREE_CODE, SUBTYPE_MAIN, SUBTYPE_DETAIL, ICD_CODE)

**sample_type**(SAMPLE_TYPE_ID, SAMPLE_CLASS)

**score**(score_id, IMSIG_B_CELLS, IMSIG_INTERFERON, IMSIG_MACROPHAGES, IMSIG_MONOCYTES, IMSIG_NEUTROPHILS, IMSIG_NK_CELLS, IMSIG_PLASMA_CELLS, IMSIG_PROLIFERATION, IMSIG_T_CELLS, IMSIG_TRANSLATION)

**admission**(case_id, PATIENT_ID, SMOKING_STATUS, SMOKING_PACK_YEARS, OS_STATUS, OS_MONTHS, patient_age, STAGE)

**gene**(gene_id, Entrez_Gene_Id, Hugo_Symbol)

**gene-sample**(gene_id, Sample_Id, mRNA-expression)

**mutation**(mutation_id, Start_Position, End_Position, Chromosome, Strand, NCBI_Build, Variant_Classification, Variant_Type, Reference_Allele)

**mutation-gene**(mutation_id, gene_id)

**sample-mutation**(sample_id, mutation_id, t_ref_count, t_alt_count, Tumor_Seq_Allele1, Tumor_Seq_Allele2)

**consequence**(consequence_id, consequence_type)

**annotation**(mutation_id, Transcript_ID, consequence_id, RefSeq, HGVSc, HGVSp, HGVSp_Short, Codons, Protein_position, Amino_acid_change)

### 5 NF Diagram

5NF (Fifth Normal Form) eliminates join dependency. A table satisfies 5NF if it cannot be further decomposed into smaller tables without losing information or changing the original meaning of the data.

![QuickDBD-Free Diagram (4).png](Database%20Report%20-%20Lin%20Liu/QuickDBD-Free_Diagram_(4).png)

- old version
    
    ![1212.svg](Database%20Report%20-%20Lin%20Liu/1212.svg)
    
    ![QuickDBD-Free Diagram (3).png](Database%20Report%20-%20Lin%20Liu/QuickDBD-Free_Diagram_(3).png)
    

# 6 Relationships and constraints

[mysql> DESC admission;
+--------------------+--------------+------+-----+---------+----------------+
| Field              | Type         | Null | Key | Default | Extra          |
+--------------------+--------------+------+-----+---------+----------------+
| case_id            | int          | NO   | PRI | NULL    | auto_increment |
| PATIENT_ID         | int          | YES  | MUL | NULL    |                |
| SMOKING_STATUS     | varchar(50)  | YES  |     | NULL    |                |
| SMOKING_PACK_YEARS | decimal(6,2) | YES  |     | NULL    |                |
| OS_STATUS          | tinyint(1)   | YES  |     | NULL    |                |
| OS_MONTHS          | decimal(6,2) | YES  |     | NULL    |                |
| patient_age        | int          | YES  |     | NULL    |                |
| STAGE              | varchar(50)  | YES  |     | NULL    |                |
| chemotherapy_state | tinyint(1)   | YES  |     | NULL    |                |
| TKI_TREATMENT      | tinyint(1)   | YES  |     | NULL    |                |
+--------------------+--------------+------+-----+---------+----------------+
10 rows in set (0.01 sec)

mysql> DESC cancer_subtype;
+----------------+--------------+------+-----+---------+----------------+
| Field          | Type         | Null | Key | Default | Extra          |
+----------------+--------------+------+-----+---------+----------------+
| subtype_id     | int          | NO   | PRI | NULL    | auto_increment |
| ONCOTREE_CODE  | varchar(100) | YES  | MUL | NULL    |                |
| SUBTYPE_MAIN   | varchar(100) | YES  |     | NULL    |                |
| SUBTYPE_DETAIL | varchar(100) | YES  |     | NULL    |                |
| ICD_CODE       | varchar(20)  | YES  |     | NULL    |                |
+----------------+--------------+------+-----+---------+----------------+
5 rows in set (0.00 sec)

mysql> DESC cancer_type;
+----------------------+--------------+------+-----+---------+-------+
| Field                | Type         | Null | Key | Default | Extra |
+----------------------+--------------+------+-----+---------+-------+
| ONCOTREE_CODE        | varchar(100) | NO   | PRI | NULL    |       |
| CANCER_TYPE          | varchar(100) | YES  |     | NULL    |       |
| CANCER_TYPE_DETAILED | varchar(100) | YES  |     | NULL    |       |
+----------------------+--------------+------+-----+---------+-------+
3 rows in set (0.00 sec)

mysql> DESC consequence;
+------------------+--------------+------+-----+---------+----------------+
| Field            | Type         | Null | Key | Default | Extra          |
+------------------+--------------+------+-----+---------+----------------+
| consequence_id   | int          | NO   | PRI | NULL    | auto_increment |
| consequence_type | varchar(100) | YES  | UNI | NULL    |                |
+------------------+--------------+------+-----+---------+----------------+
2 rows in set (0.00 sec)

mysql> DESC gene;
+----------------+-------------+------+-----+---------+----------------+
| Field          | Type        | Null | Key | Default | Extra          |
+----------------+-------------+------+-----+---------+----------------+
| gene_id        | int         | NO   | PRI | NULL    | auto_increment |
| Entrez_Gene_Id | varchar(50) | YES  | MUL | NULL    |                |
| Hugo_Symbol    | varchar(50) | YES  |     | NULL    |                |
+----------------+-------------+------+-----+---------+----------------+
3 rows in set (0.00 sec)

mysql> DESC gene_mutation;
+-------------+------+------+-----+---------+-------+
| Field       | Type | Null | Key | Default | Extra |
+-------------+------+------+-----+---------+-------+
| gene_id     | int  | NO   | PRI | NULL    |       |
| mutation_id | int  | NO   | PRI | NULL    |       |
+-------------+------+------+-----+---------+-------+
2 rows in set (0.00 sec)

mysql> DESC gene_sample;
+-----------------+---------------+------+-----+---------+-------+
| Field           | Type          | Null | Key | Default | Extra |
+-----------------+---------------+------+-----+---------+-------+
| gene_id         | int           | NO   | PRI | NULL    |       |
| Sample_Id       | int           | NO   | PRI | NULL    |       |
| mRNA_expression | decimal(10,5) | YES  |     | NULL    |       |
+-----------------+---------------+------+-----+---------+-------+
3 rows in set (0.00 sec)

mysql> DESC mutation_annotation;
+-------------------+--------------+------+-----+---------+-------+
| Field             | Type         | Null | Key | Default | Extra |
+-------------------+--------------+------+-----+---------+-------+
| mutation_id       | int          | NO   | PRI | NULL    |       |
| Transcript_ID     | varchar(50)  | NO   | PRI | NULL    |       |
| consequence_id    | int          | NO   | PRI | NULL    |       |
| RefSeq            | varchar(50)  | YES  |     | NULL    |       |
| HGVSc             | varchar(100) | YES  |     | NULL    |       |
| HGVSp             | varchar(100) | YES  |     | NULL    |       |
| HGVSp_Short       | varchar(50)  | YES  |     | NULL    |       |
| Codons            | varchar(50)  | YES  |     | NULL    |       |
| Protein_position  | int          | YES  |     | NULL    |       |
| Amino_acid_change | varchar(50)  | YES  |     | NULL    |       |
+-------------------+--------------+------+-----+---------+-------+
10 rows in set (0.00 sec)

mysql> DESC mutations;
+------------------------+-------------+------+-----+---------+----------------+
| Field                  | Type        | Null | Key | Default | Extra          |
+------------------------+-------------+------+-----+---------+----------------+
| mutation_id            | int         | NO   | PRI | NULL    | auto_increment |
| Chromosome             | varchar(50) | NO   | MUL | NULL    |                |
| Start_Position         | int         | NO   |     | NULL    |                |
| End_Position           | int         | NO   |     | NULL    |                |
| Strand                 | char(1)     | YES  |     | NULL    |                |
| NCBI_Build             | varchar(50) | YES  |     | NULL    |                |
| Variant_Classification | varchar(50) | YES  |     | NULL    |                |
| Variant_Type           | varchar(50) | YES  |     | NULL    |                |
| Reference_Allele       | varchar(50) | YES  |     | NULL    |                |
+------------------------+-------------+------+-----+---------+----------------+
9 rows in set (0.01 sec)

mysql> DESC patient;
+---------------------+-------------+------+-----+---------+----------------+
| Field               | Type        | Null | Key | Default | Extra          |
+---------------------+-------------+------+-----+---------+----------------+
| PATIENT_ID          | int         | NO   | PRI | NULL    | auto_increment |
| PATIENT_ID_original | varchar(50) | YES  | UNI | NULL    |                |
| SEX                 | varchar(10) | YES  |     | NULL    |                |
| ETHNICITY           | varchar(50) | YES  |     | NULL    |                |
| COHORT              | varchar(50) | YES  |     | NULL    |                |
+---------------------+-------------+------+-----+---------+----------------+
5 rows in set (0.00 sec)

mysql> DESC sample;
+----------------------+---------------+------+-----+---------+----------------+
| Field                | Type          | Null | Key | Default | Extra          |
+----------------------+---------------+------+-----+---------+----------------+
| Sample_Id            | int           | NO   | PRI | NULL    | auto_increment |
| Sample_Id_original   | varchar(50)   | YES  |     | NULL    |                |
| case_id              | int           | YES  | MUL | NULL    |                |
| PURITY               | decimal(5,4)  | YES  |     | NULL    |                |
| SAMPLE_TYPE_ID       | varchar(50)   | YES  | MUL | NULL    |                |
| SOMATIC_STATUS       | varchar(50)   | YES  |     | NULL    |                |
| TMB_NONSYNONYMOUS    | decimal(10,6) | YES  |     | NULL    |                |
| subtype_id           | int           | YES  | MUL | NULL    |                |
| HISTOLOGICAL_GRADE   | varchar(50)   | YES  |     | NULL    |                |
| EXOME_SEQ            | varchar(50)   | YES  |     | NULL    |                |
| RNA_SEQ_ANALYSIS     | varchar(50)   | YES  |     | NULL    |                |
| SEQUENCING_TYPE      | varchar(50)   | YES  |     | NULL    |                |
| Tumor_Sample_Barcode | varchar(100)  | YES  |     | NULL    |                |
+----------------------+---------------+------+-----+---------+----------------+
13 rows in set (0.00 sec)

mysql> DESC sample_mutation;
+-------------------+-------------+------+-----+---------+-------+
| Field             | Type        | Null | Key | Default | Extra |
+-------------------+-------------+------+-----+---------+-------+
| Sample_Id         | int         | NO   | PRI | NULL    |       |
| mutation_id       | int         | NO   | PRI | NULL    |       |
| t_ref_count       | int         | YES  |     | NULL    |       |
| t_alt_count       | int         | YES  |     | NULL    |       |
| Tumor_Seq_Allele1 | varchar(50) | YES  |     | NULL    |       |
| Tumor_Seq_Allele2 | varchar(50) | YES  |     | NULL    |       |
+-------------------+-------------+------+-----+---------+-------+
6 rows in set (0.00 sec)

mysql> DESC sample_type;
+----------------+-------------+------+-----+---------+-------+
| Field          | Type        | Null | Key | Default | Extra |
+----------------+-------------+------+-----+---------+-------+
| SAMPLE_TYPE_ID | varchar(50) | NO   | PRI | NULL    |       |
| SAMPLE_CLASS   | varchar(50) | YES  |     | NULL    |       |
+----------------+-------------+------+-----+---------+-------+
2 rows in set (0.00 sec)

mysql> DESC score;
+---------------------+---------------+------+-----+---------+-------+
| Field               | Type          | Null | Key | Default | Extra |
+---------------------+---------------+------+-----+---------+-------+
| Sample_Id           | int           | NO   | PRI | NULL    |       |
| IMSIG_B_CELLS       | decimal(10,6) | YES  |     | NULL    |       |
| IMSIG_INTERFERON    | decimal(10,6) | YES  |     | NULL    |       |
| IMSIG_MACROPHAGES   | decimal(10,6) | YES  |     | NULL    |       |
| IMSIG_MONOCYTES     | decimal(10,6) | YES  |     | NULL    |       |
| IMSIG_NEUTROPHILS   | decimal(10,6) | YES  |     | NULL    |       |
| IMSIG_NK_CELLS      | decimal(10,6) | YES  |     | NULL    |       |
| IMSIG_PLASMA_CELLS  | decimal(10,6) | YES  |     | NULL    |       |
| IMSIG_PROLIFERATION | decimal(10,6) | YES  |     | NULL    |       |
| IMSIG_T_CELLS       | decimal(10,6) | YES  |     | NULL    |       |
| IMSIG_TRANSLATION   | decimal(10,6) | YES  |     | NULL    |       |
+---------------------+---------------+------+-----+---------+-------+
11 rows in set (0.00 sec)
](https://www.notion.so/mysql-DESC-admission--35a06d135922808193cbfff37de629f9?pvs=21) 

[QuickDBD-Free Diagram (3).png](https://www.notion.so/35a06d13592280b38d9fc3cc8713dc31?pvs=21) 

# 7 Data dictionary

```python
(base) ➜  database_mutation git:(main) tree -L 2
.
├── 01create_table.sql
├── 01extract.py
├── 02get_sql_data01.py
├── 02load_independent_table.sql
├── 03load_dependent_table.sql
├── 04neo4j11.py
├── ERmodel
├── README.md
├── diagram
│   ├── ER.png
│   ├── NF.png
│   └── neo4j.png
├── log.txt
├── luad_backup.sql
├── luad_oncosg_2020
│   ├── LICENSE
│   ├── [done]data_clinical_patient.txt
│   ├── [done]data_clinical_sample.txt
│   ├── [done]data_mrna_seq_v2_rsem_zscores_ref_all_samples.txt
│   ├── [done]data_mutations.txt
│   ├── data
│   ├── log.md
│   └── useless_files
├── neo4j1
│   ├── admission.csv
│   ├── gene.csv
│   ├── gene_mutation.csv
│   ├── gene_sample_filtered.csv
│   ├── mutation.csv
│   ├── mutation_big_table.csv
│   ├── patient.csv
│   ├── sample.csv
│   ├── sample_big_table.csv
│   └── sample_mutation.csv
├── scripts
│   ├── 01extract.py
│   ├── 02get_sql_data01.py
│   ├── 04neo4j11.py
│   └── a.sh
├── sql
│   ├── 01create_table.sql
│   ├── 02load_independent_table.sql
│   ├── 03load_dependent_table.sql
│   └── luad_backup.sql
└── tempCodeRunnerFile.py

8 directories, 38 files
```

## tables, primary keys, foreign keys, and relationship cardinalities when appropriate

```sql
mysql> show tables;
+---------------------+
| Tables_in_luad      |
+---------------------+
| admission           |
| cancer_subtype      |
| cancer_type         |
| consequence         |
| gene                |
| gene_mutation       |
| gene_sample         |
| mutation_annotation |
| mutations           |
| patient             |
| sample              |
| sample_mutation     |
| sample_type         |
| score               |
+---------------------+
14 rows in set (0.00 sec)
```

```sql
mysql> DESC admission;
+--------------------+--------------+------+-----+---------+----------------+
| Field              | Type         | Null | Key | Default | Extra          |
+--------------------+--------------+------+-----+---------+----------------+
| case_id            | int          | NO   | PRI | NULL    | auto_increment |
| PATIENT_ID         | int          | YES  | MUL | NULL    |                |
| SMOKING_STATUS     | varchar(50)  | YES  |     | NULL    |                |
| SMOKING_PACK_YEARS | decimal(6,2) | YES  |     | NULL    |                |
| OS_STATUS          | tinyint(1)   | YES  |     | NULL    |                |
| OS_MONTHS          | decimal(6,2) | YES  |     | NULL    |                |
| patient_age        | int          | YES  |     | NULL    |                |
| STAGE              | varchar(50)  | YES  |     | NULL    |                |
| chemotherapy_state | tinyint(1)   | YES  |     | NULL    |                |
| TKI_TREATMENT      | tinyint(1)   | YES  |     | NULL    |                |
+--------------------+--------------+------+-----+---------+----------------+
10 rows in set (0.01 sec)

mysql> DESC cancer_subtype;
+----------------+--------------+------+-----+---------+----------------+
| Field          | Type         | Null | Key | Default | Extra          |
+----------------+--------------+------+-----+---------+----------------+
| subtype_id     | int          | NO   | PRI | NULL    | auto_increment |
| ONCOTREE_CODE  | varchar(100) | YES  | MUL | NULL    |                |
| SUBTYPE_MAIN   | varchar(100) | YES  |     | NULL    |                |
| SUBTYPE_DETAIL | varchar(100) | YES  |     | NULL    |                |
| ICD_CODE       | varchar(20)  | YES  |     | NULL    |                |
+----------------+--------------+------+-----+---------+----------------+
5 rows in set (0.00 sec)

mysql> DESC cancer_type;
+----------------------+--------------+------+-----+---------+-------+
| Field                | Type         | Null | Key | Default | Extra |
+----------------------+--------------+------+-----+---------+-------+
| ONCOTREE_CODE        | varchar(100) | NO   | PRI | NULL    |       |
| CANCER_TYPE          | varchar(100) | YES  |     | NULL    |       |
| CANCER_TYPE_DETAILED | varchar(100) | YES  |     | NULL    |       |
+----------------------+--------------+------+-----+---------+-------+
3 rows in set (0.00 sec)

mysql> DESC consequence;
+------------------+--------------+------+-----+---------+----------------+
| Field            | Type         | Null | Key | Default | Extra          |
+------------------+--------------+------+-----+---------+----------------+
| consequence_id   | int          | NO   | PRI | NULL    | auto_increment |
| consequence_type | varchar(100) | YES  | UNI | NULL    |                |
+------------------+--------------+------+-----+---------+----------------+
2 rows in set (0.00 sec)

mysql> DESC gene;
+----------------+-------------+------+-----+---------+----------------+
| Field          | Type        | Null | Key | Default | Extra          |
+----------------+-------------+------+-----+---------+----------------+
| gene_id        | int         | NO   | PRI | NULL    | auto_increment |
| Entrez_Gene_Id | varchar(50) | YES  | MUL | NULL    |                |
| Hugo_Symbol    | varchar(50) | YES  |     | NULL    |                |
+----------------+-------------+------+-----+---------+----------------+
3 rows in set (0.00 sec)

mysql> DESC gene_mutation;
+-------------+------+------+-----+---------+-------+
| Field       | Type | Null | Key | Default | Extra |
+-------------+------+------+-----+---------+-------+
| gene_id     | int  | NO   | PRI | NULL    |       |
| mutation_id | int  | NO   | PRI | NULL    |       |
+-------------+------+------+-----+---------+-------+
2 rows in set (0.00 sec)

mysql> DESC gene_sample;
+-----------------+---------------+------+-----+---------+-------+
| Field           | Type          | Null | Key | Default | Extra |
+-----------------+---------------+------+-----+---------+-------+
| gene_id         | int           | NO   | PRI | NULL    |       |
| Sample_Id       | int           | NO   | PRI | NULL    |       |
| mRNA_expression | decimal(10,5) | YES  |     | NULL    |       |
+-----------------+---------------+------+-----+---------+-------+
3 rows in set (0.00 sec)

mysql> DESC mutation_annotation;
+-------------------+--------------+------+-----+---------+-------+
| Field             | Type         | Null | Key | Default | Extra |
+-------------------+--------------+------+-----+---------+-------+
| mutation_id       | int          | NO   | PRI | NULL    |       |
| Transcript_ID     | varchar(50)  | NO   | PRI | NULL    |       |
| consequence_id    | int          | NO   | PRI | NULL    |       |
| RefSeq            | varchar(50)  | YES  |     | NULL    |       |
| HGVSc             | varchar(100) | YES  |     | NULL    |       |
| HGVSp             | varchar(100) | YES  |     | NULL    |       |
| HGVSp_Short       | varchar(50)  | YES  |     | NULL    |       |
| Codons            | varchar(50)  | YES  |     | NULL    |       |
| Protein_position  | int          | YES  |     | NULL    |       |
| Amino_acid_change | varchar(50)  | YES  |     | NULL    |       |
+-------------------+--------------+------+-----+---------+-------+
10 rows in set (0.00 sec)

mysql> DESC mutations;
+------------------------+-------------+------+-----+---------+----------------+
| Field                  | Type        | Null | Key | Default | Extra          |
+------------------------+-------------+------+-----+---------+----------------+
| mutation_id            | int         | NO   | PRI | NULL    | auto_increment |
| Chromosome             | varchar(50) | NO   | MUL | NULL    |                |
| Start_Position         | int         | NO   |     | NULL    |                |
| End_Position           | int         | NO   |     | NULL    |                |
| Strand                 | char(1)     | YES  |     | NULL    |                |
| NCBI_Build             | varchar(50) | YES  |     | NULL    |                |
| Variant_Classification | varchar(50) | YES  |     | NULL    |                |
| Variant_Type           | varchar(50) | YES  |     | NULL    |                |
| Reference_Allele       | varchar(50) | YES  |     | NULL    |                |
+------------------------+-------------+------+-----+---------+----------------+
9 rows in set (0.01 sec)

mysql> DESC patient;
+---------------------+-------------+------+-----+---------+----------------+
| Field               | Type        | Null | Key | Default | Extra          |
+---------------------+-------------+------+-----+---------+----------------+
| PATIENT_ID          | int         | NO   | PRI | NULL    | auto_increment |
| PATIENT_ID_original | varchar(50) | YES  | UNI | NULL    |                |
| SEX                 | varchar(10) | YES  |     | NULL    |                |
| ETHNICITY           | varchar(50) | YES  |     | NULL    |                |
| COHORT              | varchar(50) | YES  |     | NULL    |                |
+---------------------+-------------+------+-----+---------+----------------+
5 rows in set (0.00 sec)

mysql> DESC sample;
+----------------------+---------------+------+-----+---------+----------------+
| Field                | Type          | Null | Key | Default | Extra          |
+----------------------+---------------+------+-----+---------+----------------+
| Sample_Id            | int           | NO   | PRI | NULL    | auto_increment |
| Sample_Id_original   | varchar(50)   | YES  |     | NULL    |                |
| case_id              | int           | YES  | MUL | NULL    |                |
| PURITY               | decimal(5,4)  | YES  |     | NULL    |                |
| SAMPLE_TYPE_ID       | varchar(50)   | YES  | MUL | NULL    |                |
| SOMATIC_STATUS       | varchar(50)   | YES  |     | NULL    |                |
| TMB_NONSYNONYMOUS    | decimal(10,6) | YES  |     | NULL    |                |
| subtype_id           | int           | YES  | MUL | NULL    |                |
| HISTOLOGICAL_GRADE   | varchar(50)   | YES  |     | NULL    |                |
| EXOME_SEQ            | varchar(50)   | YES  |     | NULL    |                |
| RNA_SEQ_ANALYSIS     | varchar(50)   | YES  |     | NULL    |                |
| SEQUENCING_TYPE      | varchar(50)   | YES  |     | NULL    |                |
| Tumor_Sample_Barcode | varchar(100)  | YES  |     | NULL    |                |
+----------------------+---------------+------+-----+---------+----------------+
13 rows in set (0.00 sec)

mysql> DESC sample_mutation;
+-------------------+-------------+------+-----+---------+-------+
| Field             | Type        | Null | Key | Default | Extra |
+-------------------+-------------+------+-----+---------+-------+
| Sample_Id         | int         | NO   | PRI | NULL    |       |
| mutation_id       | int         | NO   | PRI | NULL    |       |
| t_ref_count       | int         | YES  |     | NULL    |       |
| t_alt_count       | int         | YES  |     | NULL    |       |
| Tumor_Seq_Allele1 | varchar(50) | YES  |     | NULL    |       |
| Tumor_Seq_Allele2 | varchar(50) | YES  |     | NULL    |       |
+-------------------+-------------+------+-----+---------+-------+
6 rows in set (0.00 sec)

mysql> DESC sample_type;
+----------------+-------------+------+-----+---------+-------+
| Field          | Type        | Null | Key | Default | Extra |
+----------------+-------------+------+-----+---------+-------+
| SAMPLE_TYPE_ID | varchar(50) | NO   | PRI | NULL    |       |
| SAMPLE_CLASS   | varchar(50) | YES  |     | NULL    |       |
+----------------+-------------+------+-----+---------+-------+
2 rows in set (0.00 sec)

mysql> DESC score;
+---------------------+---------------+------+-----+---------+-------+
| Field               | Type          | Null | Key | Default | Extra |
+---------------------+---------------+------+-----+---------+-------+
| Sample_Id           | int           | NO   | PRI | NULL    |       |
| IMSIG_B_CELLS       | decimal(10,6) | YES  |     | NULL    |       |
| IMSIG_INTERFERON    | decimal(10,6) | YES  |     | NULL    |       |
| IMSIG_MACROPHAGES   | decimal(10,6) | YES  |     | NULL    |       |
| IMSIG_MONOCYTES     | decimal(10,6) | YES  |     | NULL    |       |
| IMSIG_NEUTROPHILS   | decimal(10,6) | YES  |     | NULL    |       |
| IMSIG_NK_CELLS      | decimal(10,6) | YES  |     | NULL    |       |
| IMSIG_PLASMA_CELLS  | decimal(10,6) | YES  |     | NULL    |       |
| IMSIG_PROLIFERATION | decimal(10,6) | YES  |     | NULL    |       |
| IMSIG_T_CELLS       | decimal(10,6) | YES  |     | NULL    |       |
| IMSIG_TRANSLATION   | decimal(10,6) | YES  |     | NULL    |       |
+---------------------+---------------+------+-----+---------+-------+
11 rows in set (0.00 sec)

```

# 8 Script map

| file name | desc | output |
| --- | --- | --- |
| 01create_table.sql | create and drop tables | empty tables |
| 01extract.py |   1. cleaning data and extract data to upload
  2. get auto increment primary data from db | 1-14 data file in  luad_oncosg_2020/data |
| 02load_independent_table.sql | load data to independent table like patient, gene… | tables are filled |
| 02get_sql_data01.py | get admission table auto increment primary data from db | get this file luad_oncosg_2020/data/data_from_sql/01patient_mapping.csv |
| 03load_dependent_table.sql | load tables which rely on other tables. | tables are filled |
| 04neo4j11.py | extract sample and mutation information from db | neo4j1/mutation_big_table.csv and neo4j1/sample_big_table.csv  |

# 9 Reproduction instructions

### Step 1: github and database preparation

```bash
git clone https://github.com/12434565/database_mutation.git
```

```sql
create database luad;
use luad;
```

### Step2.1: Easist way to recreate

using luad_oncosg.sql file directly is the most simple way to rectrate. this file are generated by this query: `mysqldump -u root -p luad > luad_backup.sql` 

you can run this query to load.

```bash
mysql -u root -p luad < luad_backup.sql
```

### Step 2.2: Another way to recreate(correct order)

when you want to re-create this database without using luad_oncosg.sql, the correct rank of using these scripts are 

<aside>
📌

1. 01create_table.sql
2. 01extract.py first 279 lines
3. 02load_independent_table.sql
4. 02get_sql_data01.py
5. 01extract.py
6. 03load_dependent_table.sql line 1-7
7. repeat 5 and 6 table by table
8. 04neo4j11.py

note: you can always run [extract.py](http://extract.py) before each time you load csv. 

</aside>

## final output

**DB**: A normalized LUAD relational database containing clinical, mutation, annotation, and expression information.

**Neo4j**: A biomedical graph database connecting samples, mutations, and genes.

**Query**: The database supports queries such as:

- recurrent mutations
- mutations associated with specific genes
- sample-level mutation networks

## tools version

| name | website | version | function |
| --- | --- | --- | --- |
| Quick Database Diagrams | https://www.quickdatabasediagrams.com/ | unkown | create quick ER model with query. |
| MySQL |  | 5.7.24 | relational database, SQL schema creation, CSV/dump import |
| Python |  | 3.12.7 | run extraction, mapping, and export scripts |
| Neo4j |  | 2.1.4 | graph-oriented target for exported CSV data |
| mac |  | MACOS26.3 | instead of using virtual box, I use local environment.  |

# 10 Neo4j result analysis

according to following png, we could find gene EGFR(orange) has most mutations(blue). and mutation 222 are the most common mutation in samples(yellow). 

Mutation 222 is a missense SNP located on chromosome 7 (GRCh37) at genomic position 55,259,515 on the positive strand, involving a T→G substitution in the EGFR gene. The codon change cTg/cGg results in a leucine-to-arginine amino acid substitution at position 858 (p.Leu858Arg, abbreviated as p.L858R), annotated as ENST00000275493.2:c.2573T>G and classified as a missense_variant. According to the UCSC/NCBI genome browser, EGFR L858R is a well-known activating mutation located in the tyrosine kinase domain of the epidermal growth factor receptor. Functionally, this mutation leads to constitutive activation of EGFR signaling even in the absence of ligand binding, continuously stimulating downstream pathways such as MAPK, PI3K-AKT, and STAT that promote cell proliferation and survival. EGFR L858R is one of the most common driver mutations in lung adenocarcinoma and is clinically significant because tumors carrying this mutation are often sensitive to EGFR tyrosine kinase inhibitors including gefitinib, erlotinib, and osimertinib.

![visualisation22.png](Database%20Report%20-%20Lin%20Liu/visualisation22.png)

# 11 Limitations and future work

## Limitations

1. data set only comes from LUAD OncoSG patient. instead of patients and health people.
2. data comes from database directly instead of raw sequencing data. Therefore, mutation calls, expression values, and clinical annotations depend on the quality and assumptions of the original study pipeline.

## future work

integrate proteomics, phosphoproteomics, methylation, and copy number variation data to support multi-omics analysis.

It could be more useful if we provide drug and more detail treatment information.

currently version of Refseq and other information in database are out of date. maybe it is possible to update them through mapping methods.

# 12 extra information

## Database published in github.

[https://github.com/12434565/database_mutation](https://github.com/12434565/database_mutation)

---

## Here is another work i did during this project.

[https://github.com/12434565/quickER](https://github.com/12434565/quickER)

We provide a local web-based tool that supports creating, viewing, and modifying database schemas interactively. Inspired by QuickDBD, this tool was developed to address several limitations of existing solutions, including paid access requirements and the lack of annotation and freeform editing features. Our platform allows users to rapidly generate draggable ER tables and relationship diagrams from QuickDBD-style schema text directly on a local localhost environment. In addition, users can add freehand annotations, comments, and sketches to the canvas, making the design process more flexible and presentation-friendly. The system also includes features such as zooming, fullscreen mode, erasing tools, and local version history, enabling users to iteratively refine database structures in a way similar to working with presentation slides or collaborative whiteboard sketches.