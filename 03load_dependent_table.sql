LOAD DATA LOCAL INFILE '/Users/liulin/Desktop/database/project/luad_oncosg_2020/data/07admission_table.csv'
INTO TABLE admission
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(PATIENT_ID, SMOKING_STATUS, SMOKING_PACK_YEARS, OS_STATUS, OS_MONTHS, patient_age, STAGE);
select * from admission limit 5;

LOAD DATA LOCAL INFILE '/Users/liulin/Desktop/database/project/luad_oncosg_2020/data/08sample_table.csv'
INTO TABLE sample
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(Sample_Id_original, case_id, PURITY, SAMPLE_TYPE_ID, SOMATIC_STATUS,
 TMB_NONSYNONYMOUS, ONCOTREE_CODE, HISTOLOGICAL_GRADE,
 EXOME_SEQ, RNA_SEQ_ANALYSIS, SEQUENCING_TYPE, Tumor_Sample_Barcode);
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

LOAD DATA LOCAL INFILE '/Users/liulin/Desktop/database/project/luad_oncosg_2020/data/10treatment_table.csv'
INTO TABLE treatment
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(@case_id, @tki, @chemo)
SET
    case_id = @case_id,
    TKI_TREATMENT = NULLIF(@tki, ''),
    chemotherapy_state = NULLIF(@chemo, '');
SELECT * FROM treatment LIMIT 5;

-- TRUNCATE TABLE treatment;

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
    gene_id,
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