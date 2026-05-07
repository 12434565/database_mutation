-- CREATE DATABASE luad_oncosg;
-- USE luad_oncosg;
--------------------------------------------
-- if you do something wrong, how to restart:
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE admission;
DROP TABLE cancer_subtype;
DROP TABLE cancer_type;
DROP TABLE consequence;
DROP TABLE gene;
DROP TABLE gene_sample;
DROP TABLE mutation_annotation;
DROP TABLE mutations;
DROP TABLE patient;
DROP TABLE sample;
DROP TABLE sample_mutation;
DROP TABLE sample_type;
DROP TABLE score;
DROP TABLE treatment;
SET FOREIGN_KEY_CHECKS = 1;
--------------------------------------------
-- =========================
-- 1. patient v
-- =========================
CREATE TABLE patient (
    PATIENT_ID INT AUTO_INCREMENT PRIMARY KEY,
    PATIENT_ID_original VARCHAR(50) UNIQUE,
    SEX VARCHAR(10),
    ETHNICITY VARCHAR(50),
    COHORT VARCHAR(50)
);

-- =========================
-- 2. cancer_type v
-- =========================
CREATE TABLE cancer_type (
    ONCOTREE_CODE VARCHAR(100) PRIMARY KEY,
    CANCER_TYPE VARCHAR(100),
    CANCER_TYPE_DETAILED VARCHAR(100)
);

-- =========================
-- 3. cancer_subtype v
-- =========================
CREATE TABLE cancer_subtype (
    subtype_id INT AUTO_INCREMENT PRIMARY KEY,
    ONCOTREE_CODE VARCHAR(100),
    SUBTYPE_MAIN VARCHAR(100),
    SUBTYPE_DETAIL VARCHAR(100),
    ICD_CODE VARCHAR(20),

    UNIQUE (ONCOTREE_CODE, SUBTYPE_MAIN, SUBTYPE_DETAIL, ICD_CODE),

    FOREIGN KEY (ONCOTREE_CODE)
        REFERENCES cancer_type(ONCOTREE_CODE)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- =========================
-- 4. sample_type v
-- =========================
CREATE TABLE sample_type (
    SAMPLE_TYPE_ID VARCHAR(50) PRIMARY KEY,
    SAMPLE_CLASS VARCHAR(50)
);

-- =========================
-- 5. admission
-- =========================
CREATE TABLE admission (
    case_id INT AUTO_INCREMENT PRIMARY KEY,
    PATIENT_ID INT,
    SMOKING_STATUS VARCHAR(50),
    SMOKING_PACK_YEARS DECIMAL(6,2),
    OS_STATUS BOOLEAN,
    OS_MONTHS DECIMAL(6,2),
    patient_age INT,
    STAGE VARCHAR(50),
    

    FOREIGN KEY (PATIENT_ID)
        REFERENCES patient(PATIENT_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- =========================
-- 7. treatment
-- =========================
CREATE TABLE treatment (
    treatment_id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT,
    chemotherapy_state BOOLEAN,
    TKI_TREATMENT BOOLEAN,

    FOREIGN KEY (case_id)
        REFERENCES admission(case_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE

);

-- =========================
-- 8. sample（核心表）
-- =========================
CREATE TABLE sample (
    Sample_Id INT AUTO_INCREMENT PRIMARY KEY,
    Sample_Id_original VARCHAR(50),
    case_id INT,
    PURITY DECIMAL(5,4),
    SAMPLE_TYPE_ID VARCHAR(50),
    SOMATIC_STATUS VARCHAR(50),
    TMB_NONSYNONYMOUS DECIMAL(10,6),
    ONCOTREE_CODE VARCHAR(50),
    HISTOLOGICAL_GRADE VARCHAR(50),
    EXOME_SEQ VARCHAR(50),
    RNA_SEQ_ANALYSIS VARCHAR(50),
    SEQUENCING_TYPE VARCHAR(50),
    Tumor_Sample_Barcode VARCHAR(100),
    
    CHECK (PURITY >= 0 AND PURITY <= 1),

    FOREIGN KEY (case_id)
        REFERENCES admission(case_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    FOREIGN KEY (SAMPLE_TYPE_ID)
        REFERENCES sample_type(SAMPLE_TYPE_ID)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    FOREIGN KEY (ONCOTREE_CODE)
        REFERENCES cancer_type(ONCOTREE_CODE)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- =========================
-- 9. score（1:1）
-- =========================
CREATE TABLE score (
    Sample_Id INT PRIMARY KEY,
    IMSIG_B_CELLS DECIMAL(10,6),
    IMSIG_INTERFERON DECIMAL(10,6),
    IMSIG_MACROPHAGES DECIMAL(10,6),
    IMSIG_MONOCYTES DECIMAL(10,6),
    IMSIG_NEUTROPHILS DECIMAL(10,6),
    IMSIG_NK_CELLS DECIMAL(10,6),
    IMSIG_PLASMA_CELLS DECIMAL(10,6),
    IMSIG_PROLIFERATION DECIMAL(10,6),
    IMSIG_T_CELLS DECIMAL(10,6),
    IMSIG_TRANSLATION DECIMAL(10,6),

    FOREIGN KEY (Sample_Id)
        REFERENCES sample(Sample_Id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- =========================
-- 10. gene v
-- =========================
CREATE TABLE gene (
    gene_id INT AUTO_INCREMENT PRIMARY KEY,
    Entrez_Gene_Id VARCHAR(50),
    Hugo_Symbol VARCHAR(50),
    UNIQUE (Entrez_Gene_Id, Hugo_Symbol)
);

-- =========================
-- 11. gene_sample（多对多）
-- =========================
CREATE TABLE gene_sample (
    gene_id INT,
    Sample_Id INT,
    mRNA_expression DECIMAL(10,5),

    PRIMARY KEY (gene_id, Sample_Id),

    FOREIGN KEY (gene_id)
        REFERENCES gene(gene_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    FOREIGN KEY (Sample_Id)
        REFERENCES sample(Sample_Id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- =========================
-- 12. mutations
-- =========================
CREATE TABLE mutations (
    mutation_id INT AUTO_INCREMENT PRIMARY KEY,

    Chromosome VARCHAR(50) NOT NULL,
    Start_Position INT NOT NULL,
    End_Position INT NOT NULL,
    Strand CHAR(1),
    NCBI_Build VARCHAR(50),

    gene_id INT,

    Variant_Classification VARCHAR(50),
    Variant_Type VARCHAR(50),
    Reference_Allele VARCHAR(50),

    -- 🔥 防止重复 mutation（推荐）
    UNIQUE (
        Chromosome,
        Start_Position,
        End_Position,
        Strand,
        Reference_Allele,
        NCBI_Build
    ),

    FOREIGN KEY (gene_id)
        REFERENCES gene(gene_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- =========================
-- 13. consequence v
-- =========================
CREATE TABLE consequence (
    consequence_id INT AUTO_INCREMENT PRIMARY KEY,
    consequence_type VARCHAR(100) UNIQUE
);

-- =========================
-- 14. mutation_annotation（多对多） 
-- =========================
CREATE TABLE mutation_annotation (
    mutation_id INT NOT NULL,
    Transcript_ID VARCHAR(50) NOT NULL,
    consequence_id INT NOT NULL,

    RefSeq VARCHAR(50),

    HGVSc VARCHAR(100),
    HGVSp VARCHAR(100),
    HGVSp_Short VARCHAR(50),

    Codons VARCHAR(50),
    Protein_position INT,
    Amino_acid_change varchar(50),


    PRIMARY KEY (mutation_id, Transcript_ID, consequence_id),

    FOREIGN KEY (mutation_id)
        REFERENCES mutations(mutation_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    FOREIGN KEY (consequence_id)
        REFERENCES consequence(consequence_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- =========================
-- 15. sample_mutation（多对多）
-- =========================
CREATE TABLE sample_mutation (
    Sample_Id INT,
    mutation_id INT,
    t_ref_count INT,
    t_alt_count INT,
    Tumor_Seq_Allele1 VARCHAR(50),
    Tumor_Seq_Allele2 VARCHAR(50),

    PRIMARY KEY (Sample_Id, mutation_id),

    FOREIGN KEY (Sample_Id)
        REFERENCES sample(Sample_Id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    FOREIGN KEY (mutation_id)
        REFERENCES mutations(mutation_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- after this, you should see tables in db, as follows:
-- mysql> show tables;
-- +-----------------------+
-- | Tables_in_luad_oncosg |
-- +-----------------------+
-- | admission             |
-- | cancer_subtype        |
-- | cancer_type           |
-- | consequence           |
-- | gene                  |
-- | gene_sample           |
-- | mutation_annotation   |
-- | mutations             |
-- | patient               |
-- | sample                |
-- | sample_mutation       |
-- | sample_type           |
-- | score                 |
-- | treatment             |
-- +-----------------------+
-- 14 rows in set (0.01 sec)
