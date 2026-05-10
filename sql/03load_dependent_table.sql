LOAD DATA LOCAL INFILE '/Users/liulin/Desktop/database/project/luad_oncosg_2020/data/07admission_table.csv'
INTO TABLE admission
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(@PATIENT_ID, @SMOKING_STATUS, @SMOKING_PACK_YEARS, @OS_STATUS, @OS_MONTHS, @patient_age, @STAGE, @chemotherapy_state, @TKI_TREATMENT)
SET
    PATIENT_ID = NULLIF(TRIM(@PATIENT_ID), ''),
    SMOKING_STATUS = NULLIF(TRIM(@SMOKING_STATUS), ''),
    SMOKING_PACK_YEARS = NULLIF(TRIM(@SMOKING_PACK_YEARS), ''),
    OS_STATUS = NULLIF(TRIM(@OS_STATUS), ''),
    OS_MONTHS = NULLIF(TRIM(@OS_MONTHS), ''),
    patient_age = NULLIF(TRIM(@patient_age), ''),
    STAGE = NULLIF(TRIM(@STAGE), ''),
    chemotherapy_state = NULLIF(TRIM(@chemotherapy_state), ''),
    TKI_TREATMENT = NULLIF(TRIM(@TKI_TREATMENT), '');
select * from admission limit 5;

LOAD DATA LOCAL INFILE '/Users/liulin/Desktop/database/project/luad_oncosg_2020/data/08sample_table.csv'
INTO TABLE sample
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(@Sample_Id_original, @case_id, @PURITY, @SAMPLE_TYPE_ID, @SOMATIC_STATUS,
 @TMB_NONSYNONYMOUS, @subtype_id, @HISTOLOGICAL_GRADE,
 @EXOME_SEQ, @RNA_SEQ_ANALYSIS, @SEQUENCING_TYPE, @Tumor_Sample_Barcode)
SET
    Sample_Id_original = NULLIF(TRIM(@Sample_Id_original), ''),
    case_id = NULLIF(TRIM(@case_id), ''),
    PURITY = NULLIF(TRIM(@PURITY), ''),
    SAMPLE_TYPE_ID = NULLIF(TRIM(@SAMPLE_TYPE_ID), ''),
    SOMATIC_STATUS = NULLIF(TRIM(@SOMATIC_STATUS), ''),
    TMB_NONSYNONYMOUS = NULLIF(TRIM(@TMB_NONSYNONYMOUS), ''),
    subtype_id = NULLIF(TRIM(@subtype_id), ''),
    HISTOLOGICAL_GRADE = NULLIF(TRIM(@HISTOLOGICAL_GRADE), ''),
    EXOME_SEQ = NULLIF(TRIM(@EXOME_SEQ), ''),
    RNA_SEQ_ANALYSIS = NULLIF(TRIM(@RNA_SEQ_ANALYSIS), ''),
    SEQUENCING_TYPE = NULLIF(TRIM(@SEQUENCING_TYPE), ''),
    Tumor_Sample_Barcode = NULLIF(TRIM(@Tumor_Sample_Barcode), '');
 select * from sample limit 5;

LOAD DATA LOCAL INFILE '/Users/liulin/Desktop/database/project/luad_oncosg_2020/data/09score_table.csv'
INTO TABLE score
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    Sample_Id,
    IMSIG_B_CELLS,
    IMSIG_INTERFERON,
    IMSIG_MACROPHAGES,
    IMSIG_MONOCYTES,
    IMSIG_NEUTROPHILS,
    IMSIG_NK_CELLS,
    IMSIG_PLASMA_CELLS,
    IMSIG_PROLIFERATION,
    IMSIG_T_CELLS,
    IMSIG_TRANSLATION
);
select * from score limit 5;

LOAD DATA LOCAL INFILE '/Users/liulin/Desktop/database/project/luad_oncosg_2020/data/11mutation_table.csv'
INTO TABLE mutations
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    Chromosome,
    Start_Position,
    End_Position,
    Strand,
    NCBI_Build,
    Variant_Classification,
    Variant_Type,
    Reference_Allele
);
-- TRUNCATE TABLE mutations;
-- SHOW WARNINGS LIMIT 20;
-- SET FOREIGN_KEY_CHECKS = 0;
-- -- TRUNCATE TABLE mutation_annotation;
-- TRUNCATE TABLE mutations;
-- SET FOREIGN_KEY_CHECKS = 1;

LOAD DATA LOCAL INFILE '/Users/liulin/Desktop/database/project/luad_oncosg_2020/data/15gene_mutation_table.csv'
INTO TABLE gene_mutation
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    gene_id,
    mutation_id
);

LOAD DATA LOCAL INFILE '/Users/liulin/Desktop/database/project/luad_oncosg_2020/data/12sample_mutation_table.csv'
INTO TABLE sample_mutation
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    Sample_Id,
    mutation_id,
    t_ref_count,
    t_alt_count,
    Tumor_Seq_Allele1,
    Tumor_Seq_Allele2
);

LOAD DATA LOCAL INFILE '/Users/liulin/Desktop/database/project/luad_oncosg_2020/data/13mutation_annotation_table.csv'
INTO TABLE mutation_annotation
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    mutation_id,
    Transcript_ID,
    consequence_id,
    RefSeq,
    HGVSc,
    HGVSp,
    HGVSp_Short,
    Codons,
    Protein_position,
    Amino_acid_change
);


LOAD DATA LOCAL INFILE '/Users/liulin/Desktop/database/project/luad_oncosg_2020/data/gene_patch.csv'
INTO TABLE gene
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(Hugo_Symbol, Entrez_Gene_Id);

LOAD DATA LOCAL INFILE '/Users/liulin/Desktop/database/project/luad_oncosg_2020/data/14gene_sample_table.csv'
INTO TABLE gene_sample
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    gene_id,
    Sample_Id,
    mRNA_expression
);
