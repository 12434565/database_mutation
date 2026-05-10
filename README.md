<div align="center">

# database_mutation

A staged Python + MySQL project that transforms **LUAD (OncoSG, 2020)** clinical, mutation, and expression files into a normalized relational database and a set of Neo4j-ready CSV exports. The repository includes the raw study files, generated intermediate CSV tables, multiple SQL dump snapshots, schema diagrams, and the scripts needed to rebuild or reuse the database.

`Python` `MySQL` `SQL` `pandas` `PyMySQL` `Bioinformatics` `Neo4j export`

</div>

## Tools Used

| Tool | Purpose in this project |
| --- | --- |
| Python | Data cleaning, reshaping, mapping IDs, and exporting staged CSV files |
| MySQL | Main relational database target |
| SQL | Schema creation and staged data loading |
| pandas | Reading, joining, pivoting, and exporting tabular data |
| PyMySQL | Python-to-MySQL connectivity |
| Neo4j | Downstream graph-oriented export target |

## Repository Contents

### Key root files

| File | Description |
| --- | --- |
| `01extract.py` | Main staged extractor that converts raw study files into CSV tables |
| `02get_sql_data01.py` | Exports MySQL-generated patient mappings back into CSV |
| `01create_table.sql` | Creates the current 14-table schema |
| `02load_independent_table.sql` | Loads independent tables such as `patient`, `gene`, and `consequence` |
| `03load_dependent_table.sql` | Loads dependent tables such as `admission`, `sample`, `mutations`, and relationship tables |
| `04neo4j11.py` | Exports graph-oriented CSV files from MySQL into `neo4j1/` |
| `luad_backup.sql` | Another SQL dump snapshot, closer to the current schema |
| `ERmodel` | Early plain-text ER draft |

### Main folders

| Folder | Description |
| --- | --- |
| `diagram/` | ER and Neo4j diagrams, plus an NF diagram image |
| `luad_oncosg_2020/` | Raw study files, generated CSV outputs, and project notes |
| `luad_oncosg_2020/data/` | Staged CSV files used for MySQL import |
| `luad_oncosg_2020/data/data_from_sql/` | ID mapping files exported from MySQL |
| `neo4j1/` | Committed Neo4j-oriented CSV exports |
| `scripts/` | Mirrored copies of the root Python scripts |
| `sql/` | Mirrored or archived SQL files and dump files |

## Data Source Summary

The dataset metadata in `luad_oncosg_2020/useless_files/meta_study.txt` identifies the source as:

**Study:** Lung Adenocarcinoma (OncoSG, Nat Genet 2020)  
**Study ID:** `luad_oncosg_2020`  
**Cancer type:** `LUAD`  
**PMID:** `32015526`  
**Description:** Whole-exome and transcriptome sequencing of **305** East Asian lung adenocarcinomas with matched normals

The main committed raw inputs are:

- `luad_oncosg_2020/[done]data_clinical_patient.txt`
- `luad_oncosg_2020/[done]data_clinical_sample.txt`
- `luad_oncosg_2020/[done]data_mutations.txt`
- `luad_oncosg_2020/[done]data_mrna_seq_v2_rsem_zscores_ref_all_samples.txt`

## Setup Requirements And Dependencies

You will need:

- Python 3
- MySQL
- `pandas`
- `PyMySQL`

Example environment setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas PyMySQL
```

For MySQL local file loading, you may also need:

```sql
SET GLOBAL local_infile = 1;
```

and a MySQL client started with `--local-infile=1`.

## Before You Run Anything

The runnable scripts contain hard-coded absolute paths and plaintext credentials copied from the original development environment.

Update these files before rerunning the project:

- `01extract.py`
- `02get_sql_data01.py`
- `04neo4j11.py`
- `02load_independent_table.sql`
- `03load_dependent_table.sql`

Important environment note:

- `01extract.py` connects to `luad`
- `04neo4j11.py` connects to `luad`
- `02get_sql_data01.py` connects to `luad_oncosg`

Normalize the database name before rerunning the staged workflow.

The hard-coded paths currently look like:

```text
/Users/liulin/Desktop/database/...
```

Replace them with your own absolute path to this repository.

Also review the reset block at the top of `01create_table.sql` before running it against a non-empty database.

## Exact Run Order

There are two practical ways to reproduce the database.

### Option A: Recommended fast path using the committed CSV files

This is the simplest and most reliable path if your goal is to recreate the database defined by the current numbered root scripts.

1. Update the hard-coded file paths in `02load_independent_table.sql` and `03load_dependent_table.sql`.
2. Create the target database `luad_oncosg`.
3. Run `01create_table.sql`.
4. Run `02load_independent_table.sql`.
5. Run `03load_dependent_table.sql`.
6. Optionally run `04neo4j11.py` to regenerate the Neo4j exports.

Example MySQL session:

```sql
CREATE DATABASE IF NOT EXISTS luad_oncosg;
USE luad_oncosg;
SOURCE /absolute/path/to/database_mutation/01create_table.sql;
SOURCE /absolute/path/to/database_mutation/02load_independent_table.sql;
SOURCE /absolute/path/to/database_mutation/03load_dependent_table.sql;
```

### Option B: Full staged rebuild from the raw study files

This route is more reproducible, but it is also more manual because `01extract.py` depends on mappings generated by earlier database loads.

1. Update paths, credentials, and database names in the Python and SQL files listed above.
2. Create the target database and run `01create_table.sql`.
3. Run `python 01extract.py` for **pass 1**.
   This produces the early CSV files such as `01patient_table.csv` through `06consequence_table.csv`. It may stop once later mapping files are needed.
4. Run `02load_independent_table.sql`.
   This loads `patient`, `cancer_type`, `cancer_subtype`, `sample_type`, `gene`, and `consequence`.
5. Run `python 02get_sql_data01.py`.
   This produces `luad_oncosg_2020/data/data_from_sql/01patient_mapping.csv`.
6. Run `python 01extract.py` for **pass 2**.
   This generates `07admission_table.csv`.
7. In `03load_dependent_table.sql`, run only the **admission** block.
8. Run `python 01extract.py` for **pass 3**.
   After `admission` exists in MySQL, this pass can generate `08sample_table.csv`, `11mutation_table.csv`, and `15gene_mutation_table.csv`, and it can refresh downstream CSVs that depend on `admission.case_id`.
9. In `03load_dependent_table.sql`, run the blocks for:
   - `sample`
   - `mutations`
   - `gene_mutation`
10. Run `python 01extract.py` for **pass 4**.
    After `sample` and `mutations` exist in MySQL, this pass can generate usable versions of:
   - `09score_table.csv`
   - `12sample_mutation_table.csv`
   - `13mutation_annotation_table.csv`
   - `gene_patch.csv`
   - `14gene_sample_table.csv`
11. In `03load_dependent_table.sql`, run the blocks for:
   - `score`
   - `sample_mutation`
   - `mutation_annotation`
   - `gene_patch`
12. If `gene_patch.csv` is not empty, run `python 01extract.py` for **pass 5** so that `14gene_sample_table.csv` can include the newly inserted genes.
13. Run the final `gene_sample` block from `03load_dependent_table.sql`.
14. Optionally run `python 04neo4j11.py`.

## SQL Dump Import Instructions

The current repository includes `luad_backup.sql` at the root and `sql/luad_backup.sql` as its mirrored copy.

### `luad_backup.sql`

This dump includes `gene_mutation`, so it is closer to the current design than older snapshots, but it is still a snapshot rather than the authoritative latest workflow.

Example import:

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS luad_oncosg;"
mysql -u root -p luad_oncosg < /absolute/path/to/database_mutation/luad_backup.sql
```

Practical rule:

- use the numbered root scripts if you want the latest scripted workflow
- use the dump file if you want to restore a historical database state quickly

## Diagrams And Documentation

| Asset | Location |
| --- | --- |
| ER diagram | `diagram/ER.png` |
| Neo4j diagram | `diagram/neo4j.png` |
| NF diagram | `diagram/NF.png` |
| Documentation write-up / working notes | `luad_oncosg_2020/log.md` |
| Early schema draft | `ERmodel` |

## Expected Final Result

After a successful run, you should have:

- a MySQL database named `luad_oncosg` with the current **14-table** schema:
  - `patient`
  - `cancer_type`
  - `cancer_subtype`
  - `sample_type`
  - `admission`
  - `sample`
  - `score`
  - `gene`
  - `gene_sample`
  - `mutations`
  - `gene_mutation`
  - `consequence`
  - `mutation_annotation`
  - `sample_mutation`
- staged CSV outputs in `luad_oncosg_2020/data/`
- Neo4j-oriented CSV outputs in `neo4j1/`, including:
  - `patient.csv`
  - `admission.csv`
  - `sample.csv`
  - `gene.csv`
  - `mutation.csv`
  - `gene_mutation.csv`
  - `sample_mutation.csv`
  - `sample_big_table.csv`
  - `mutation_big_table.csv`

Typical committed output scale in this repository:

| Output | Rows |
| --- | ---: |
| `01patient_table.csv` | 305 |
| `07admission_table.csv` | 305 |
| `08sample_table.csv` | 305 |
| `09score_table.csv` | 305 |
| `05gene_table.csv` | 18,625 |
| `11mutation_table.csv` | 72,650 |
| `15gene_mutation_table.csv` | 71,101 |
| `12sample_mutation_table.csv` | 73,388 |
| `13mutation_annotation_table.csv` | 76,186 |
| `14gene_sample_table.csv` | 3,174,158 |

If you can load the database, regenerate the Neo4j exports, and match the current schema and staged outputs above, the project has been reproduced successfully.
