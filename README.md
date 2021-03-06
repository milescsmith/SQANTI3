# SQANTI3

Last Updated: 12/16/2020 (v1.6)   SQANTI3 release!

## What is SQANTI3?

SQANTI3 is the newest version of the SQANTI tool ([publication](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5848618/)) that merges features from SQANTI, ([code repository](https://github.com/ConesaLab/SQANTI)) and SQANTI2 ([code repository](https://github.com/Magdoll/SQANTI2)), together with new additions. SQANTI3 will continue as an integrated development aiming to  providing you the best characterization possible for your new long read-defined transcriptome. SQANTI3 is the first module of the [Functional IsoTranscriptomics (FIT)](https://tappas.org/) framework, that also includes IsoAnnot and tappAS.


New features implemented in SQANTI3 not available in previous versions are:

* IsoAnnotLite implemented to generate tappAS compatible gff3 files. Gff3 output may incorporate functional annotation labels for model species supported by tappAS.
* CAGE peak definitions: CAGE peak will only be associated to a transcript when located upstream of the transcript stariting site. This option requires CAGE peak data.
* Updated `bite` definition and ISM subcategories `5prime_fragment` and `3prime_fragment`.
* Accepts several Short Reads expression files at the same time or as an expression matrix.
* New plots:
    *  Saturation curves (number of transcripts detected as a function of the sequencing depth)
    *  Distance to CAGE (if any).
    *  Reference transcript redundance (number of FSM and ISM with the same reference transcript match)
* Installation provided as a Conda yml environment file

## SQANTI3 HowTos

* <a href="#install">Setting up SQANTI3</a>
    * <a href="#Prerequisites"> Prerequisites
* <a href="#Running">Running SQANTI3 Quality Control</a>
    * <a href="#cage">Incorporating CAGE peak data</a>
    * <a href="#polya">Incorporating polyA site data or polyA motif list</a>
    * <a href="#flcount">Single or Multi-Sample FL Count Plotting</a>
    * <a href="#exp">Short Read Expression</a>
* <a href="#filter">Filtering Isoforms using SQANTI3</a>
* <a href="#explain">SQANTI3 Output Explanation</a>
    * <a href="#class">Classification Output Explanation</a>
    * <a href="#junction">Junction Output Explanation</a>
   

![Sqanti3 workflow](https://github.com/FJPardoPalacios/public_figures/blob/master/SQ3_qc.png)

<a name="Updates"/>

## Updates

2020.12.16 - updated to v1.6. Fixed `SQANTI3_report.R` num isoforms per gene plotting error.

2020.12.16 - updated to v1.5. Fixed mono-exonic mis-classification of antisense in edge cases.

2020.09.24 - updated to v1.3. Fixed minor printing bug in `SQANTI3_report.R`. Also `sqanti_qc3.py` supports file patterns again for coverage junction file input.

2020.09.23 - updated to v1.2. Fixed `SQANTI3_report.R` bug when there are no non-canonical junctions.

2020.09.15 - updated to v1.1. Fixed report script `_classification_TPM.txt` linebreak issue. rarefaction disabled for now.

2020.09.07 - updated to v1.0. Fixed SQANTI3 report missing figures (ex: intrapriming).

2020.05.12 - SQANTI3 first release.

<a name="Prerequisites"/>

! Note: Due to a dependency on [GMST](http://exon.gatech.edu/GeneMark/) for ORF
 prediction, SQANTI3 will only run on Linux systems; however, a Docker
 container is provided, which should allow for running on any system supported
 by Docker.

## Prerequisites

* Perl
* Minimap2
* Python (3.7)

### Python-related libraries

* pysam
* psutil
* bx-python
* BioPython
* BCBioGFF
* [cDNA_Cupcake](https://github.com/Magdoll/cDNA_Cupcake/wiki/Cupcake-ToFU:-supporting-scripts-for-Iso-Seq-after-clustering-step#install)

### R-related libraries

* R (>= 3.4.0)
* R packages (for `sqanti3_qc.py`): ggplot2, scales, reshape, gridExtra, grid, dplyr, NOISeq, ggplotify

### External scripts

* gtfToGenePred

<a name="install"/>

## Installing dependencies

We recommend using Anaconda (or, specifically, [Miniconda](https://docs.conda.io/en/latest/miniconda.html))
to facilitate installation of all dependencies.
Alternatively, you can use the Docker container. Please
follow the steps here to ensure an error-free installation. All the
dependencies will be installed automatically in a conda environment. The
installation will be done just once. When the environment has been entirely
built, you just need to activate the conda environment of SQANTI3 and run it!

1. Make sure you have installed Anaconda and it is updated.  Follow the
[directions for installing Miniconda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html)

2. Download or clone the SQANTI3 repository.

```
 git clone https://github.com/ConesaLab/SQANTI3.git
```

3. Create an environment and install the SQANTI3 dependencies:

At the command prompt, run the following command (substituting the path to
where the repository was cloned for <path_to_SQANTI3_DIR>):

```
conda env create -f <path_to_SQANTI3_DIR>/sqanti3_env.yml
```

This will install the all the required dependencies.  To then use SQANTI3, 
activate the environment:

```
conda activate sqanti3
```

  - Alternatively, `sqanti3_qc` can be run from a Docker container:

```
docker \
   run \
   -it \
   --mount target=/opt/refs,source=<path_to_refs>,type=bind \
   milescsmith/sqanti3 \
   sqanti3_qc [OPTIONS] ISOFORMS ANNOTATION GENOME
```

<a name="Running"/>

## Running SQANTI3 Quality Control (please read completely specially when planning to use tappAS for downstream analysis)

Before starting any SQANTI3 run, remember that you need to activate the SQANTI3 environment and add `cDNA_Cupcake/sequence` to `$PYTHONPATH`.

```
$ source activate SQANTI3.env
(SQANTI3.env)-bash-4.1$ export PYTHONPATH=$PYTHONPATH:<path_to>/cDNA_Cupcake/sequence/
```

#### Minimum Input to SQANTI3 QC

These are the minimal files needed to run SQANTI3:

*   **Long read-defined transcriptome**. It can be obtained from any of the 
available Third Generation Sequencing techonologies like Iso-Seq (PacBio) or
Nanopore. SQANTI3 accepts it in several formats such as FASTA, FASTQ and GTF
(using `--gtf` option). If you provide the sequences of your transcripts, a
mapping step will be performed initially with *minimap2*. It is strongly
recommended to collapse sequences into unique transcripts *BEFORE* running
SQANTI3 using [cDNA_Cupcake](https://github.com/Magdoll/cDNA_Cupcake/wiki/Cupcake-ToFU:-supporting-scripts-for-Iso-Seq-after-clustering-step#collapse)
or [TAMA](https://github.com/GenomeRIK/tama/wiki).

*   **Reference annotation** in GTF format. This file will be taken as
reference to describe the degree of novelty of each transcript. Some examples
of reference transcriptomes can be, for example,
[GENCODE](https://www.gencodegenes.org/releases/current.html)
 or [CHESS](http://ccb.jhu.edu/chess/).

*   **Reference genome**, in FASTA format. For example hg38. *Make sure your
annotation GTF is based on the correct ref genome version!* Please check that
the chromosome/scaffolds names are the same in the reference annotation and
the reference genome.

#### Optional inputs:

* CAGE Peak data (from FANTOM5). In SQANTI2, it was provided a version of
[CAGE Peak for hg38 genome](https://github.com/Magdoll/images_public/blob/master/SQANTI2_support_data/hg38.cage_peak_phase1and2combined_coord.bed.gz)
which was originally from [FANTOM5](http://fantom.gsc.riken.jp/5/datafiles/latest/extra/CAGE_peaks/).

* [Intropolis](https://github.com/nellore/intropolis/blob/master/README.md)
Junction BED file. In previous versions of SQANTI, it was provided a version of
[Intropolis for hg38 genome, modified into STAR junction format](https://github.com/Magdoll/images_public/tree/master/SQANTI2_support_data)
which is still valid.

* polyA motif list. A ranked  list of polyA motifs to find upstream of the 3'
end site. See [human polyA list](https://raw.githubusercontent.com/Magdoll/images_public/master/SQANTI2_support_data/human.polyA.list.txt)
for an example.

* FL count information. See <a href="#flcount">FL count section</a> to include 
Iso-Seq FL count information for each isoform.

* Short read expression. See <a href="#exp">Short Read Expression section</a> 
to include short read expression (RSEM or Kallisto output files or a 
user-defined expression matrix).

* tappAS-annotation file. A gff3 file which contains functional annotations of
a reference transcriptome (e.g. Ensembl) at the isoform level. When
`--isoAnnotLite` option is activated and a gff3 tappAS-like is provided,
SQANTI3 will run internally [isoAnnot Lite](https://isoannot.tappas.org/isoannot-lite/).
You can find some of them in this [repository](http://app.tappas.org/resources/downloads/gffs/).
For more information about tappAS functionalities visit its
[webpage](https://app.tappas.org/).


#### Running SQANTI3 Quality Control script

The script usage is:

```
Usage: sqanti3_qc [OPTIONS] ISOFORMS ANNOTATION GENOME

  Structural and Quality Annotation of Novel Transcript Isoforms

  Parameters:
  -----------
  isoforms:
      FASTA/FASTQ or gtf format; By default "FASTA/FASTQ". For GTF, use --gtf
  annotation:
      Reference annotation file in GTF format
  genome:
      Reference genome in fasta format

Options:
  --min_ref_len INTEGER           Minimum reference transcript length
                                  [default: 200]

  --force_id_ignore               Allow the usage of transcript IDs non
                                  related with PacBio's nomenclature (PB.X.Y)
                                  [default: False]

  --aligner_choice [minimap2|deSALT|gmap]
                                  [default: minimap2]
  --cage_peak TEXT                FANTOM5 Cage Peak (BED format, optional)
  --polyA_motif_list TEXT         Ranked list of polyA motifs (text, optional)
  --polyA_peak TEXT               PolyA Peak (BED format, optional)
  --phyloP_bed TEXT               PhyloP BED for conservation score (BED,
                                  optional)

  --skipORF                       Skip ORF prediction (to save time)
                                  [default: False]

  --is_fusion                     Input are fusion isoforms, must supply GTF
                                  as input using --gtf  [default: False]

  -g, --gtf                       Use when running SQANTI by using as input a
                                  gtf of isoforms  [default: False]

  -e, --expression TEXT           Expression matrix (supported: Kallisto tsv)
  -x, --gmap_index TEXT           Path and prefix of the reference index
                                  created by gmap_build. Mandatory if using
                                  GMAP unless -g option is specified.

  -t, --cpus INTEGER              Number of threads used during alignment by
                                  aligners.  [default: 10]

  -n, --chunks INTEGER            Number of chunks to split SQANTI3 analysis
                                  in for speed up.  [default: 1]

  -o, --output TEXT               Prefix for output files.
  -d, --directory TEXT            Directory for output files. Default:
                                  Directory where the script was run.

  -c, --coverage TEXT             Junction coverage files (provide a single
                                  file or a file pattern, ex:
                                  "mydir/*.junctions").

  -s, --sites TEXT                Set of splice sites to be considered as
                                  canonical (comma-separated list of splice
                                  sites).

  -w, --window INTEGER            Size of the window in the genomic DNA
                                  screened for Adenine content downstream of
                                  TTS

  --genename                      Use gene_name tag from GTF to define genes.
                                  Otherwise, gene_id used to define genes

  -fl, --fl_count TEXT            Full-length PacBio abundance file
  --skip_report                   Do not prepare pdf report.
  --isoAnnotLite                  Run isoAnnot Lite to output a tappAS-
                                  compatible gff3 file

  --gff3 TEXT                     Precomputed tappAS species specific GFF3
                                  file. It will serve as reference to transfer
                                  functional attributes

  --version                       Show the version and exit.
  --help                          Show this message and exit.
```
python sqanti3_qc.py --gtf input.gtf \
                     gencode.v35.annotation.gtf \
                     hg38.fa \
                     --cage_peak hg38.cage_peaks.chr13.bed --polyA_motif_list  polyA.list \
                     --expression rsemQuantification.chr13.isoforms.results \
                     --fl_count input.abundances.txt \
                     -c star.SJ.out.tab \
                     --isoAnnotLite --gff3 tappAS.input.gff3
                     
```
sqanti3_qc test_chr13_seqs.fasta \
    Homo_sapiens.GRCh38.86.chr13.gtf \
    Homo_sapiens.GRCh38.dna.chromosome.13.fa \
    --cage_peak hg38.cage_peaks.chr13.bed \
    --polyA_motif_list  polyA.list \
    --expression rsemQuantification.chr13.isoforms.results \
    --fl_count chr13_FL.abundances.txt \
    --coverage chr13_SR_support.star.SJ.out.tab \
    --isoAnnotLite \
    --gff3 tappAS.Homo_sapiens_GRCh38_Ensembl_86.chr13.gff3

```

It is *highly recommended* that you run SQANTI3 using an input GFF3/GTF (adding the `--gtf` option in front) instead of input fasta/fastq.

You can obtain the input GFF3/GTF using [Cupcake collapse](https://github.com/Magdoll/cDNA_Cupcake/wiki/Cupcake:-supporting-scripts-for-Iso-Seq-after-clustering-step#collapse)

There are two options related to parallelization. The first is `-t` (`--cpus`)
that designates the number of CPUs used by the aliger.
If your input is GTF (using `--gtf` option), the `-t` option has no effect.
The second is `-n` (`--chunks`) that chunks the input (GTF or fasta) into chunks
and run SQANTI3 in parallel before combining them.
Note that if you have `-t 30 -n 10`, then each chunk gets (30/10=3) CPUs.


### SQANTI3 Quality Control Output

You can look at the [example_out](https://github.com/ConesaLab/SQANTI3/tree/master/example/example_out)
subfolder for a sample output. The PDF file shows all the figures drawn using
R script [SQANTI3_report.R](https://github.com/ConesaLab/SQANTI3/blob/tree/master/utilities/SQANTI3_report.R),
taking the `melanoma_chr13_classification.txt` and `melanoma_chr13_junctions.txt`
of the same folder as input. If you know R well, you are free to modify the R
script to add new figures! We will be constantly adding new figures as well,
so check out <a href="#Updates">the updates section</a>

Detailed explanation of `_classification.txt` and `_junctions.txt`
<a href="#explain">below</a>.


<a name="cage"/>

### Incorporating CAGE peak data

CAGE peak data must be provided in BED file format where:
- column 1 is chromosome (chr1, chr2...)
- column 2 is 0-based start coordinate
- column 3 is 1-based end coordinate
- column 5 is strand information 

For human and mouse, you can download [refTSS](http://reftss.clst.riken.jp/reftss/Main_Page) BED files.

Provide the CAGE peak BED file with the `--cage_peak` parameter in `sqanti3_qc.py`.

Distance to the closest CAGE peak signal is the `dist_peak` and `within_peak` columns in the output `.classification.txt` file. 
See [here](https://github.com/ConesaLab/SQANTI3#classification-output-explanation) for more info.


<a name="polya"/>

### Incorporating polyA site data or polyA motif list


PolyA site data must be provided in BED file format where:
- column 1 is chromosome (chr1, chr2...)
- column 2 is 0-based start coordinate
- column 3 is 1-based end coordinate
- column 5 is strand information 

For human, mouse, and worm, you can download the [Atlas BED files](https://polyasite.unibas.ch/atlas#2).

Note however that the chromosomes in the BED files are missing the "chr" prefix!  
You can modify the downloaded bed file as shown below:

```
sed -i 's/^/chr/' atlas.clusters.2.0.GRCh38.96.bed
```
 
Provide the PolyA site BED file with the `--polyA_peak` parameter in `sqanti3_qc.py`.

Distance to the closest PolyA site is the `dist_to_polya_site` and `within_polya_site` columns in the output `.classification.txt` file. 
See [here](https://github.com/ConesaLab/SQANTI3#classification-output-explanation) for more info.


In addition, you can also provide a polyA motif list in the form of a text file. 
For example, the common polyA motifs for human are shown [here](https://github.com/ConesaLab/SQANTI3/blob/master/example/polyA.list)

Provide the PolyA site BED file with the `--polyA_motif_list` parameter in `sqanti3_qc.py`.

Distance to the closest PolyA site is the `polyA_motif` and `polyA_dist` columns in the output `.classification.txt` file. 
See [here](https://github.com/ConesaLab/SQANTI3#classification-output-explanation) for more info.



<a name="flcount"/>

### Single or Multi-Sample FL Count Plotting

`sqanti3_qc.py` supports single or multi-sample FL counts from PacBio Iso-Seq
pipeline. There are three acceptable formats.

#### Single Sample FL Count

A single sample FL Count file is automatically produced by the Iso-Seq With
Mapping pipeline in [SMRTLink/SMRTAnalysis](https://www.pacb.com/products-and-services/analytical-software/)
with the following format:

```
#
# -----------------
# Field explanation
# -----------------
# count_fl: Number of associated FL reads
# norm_fl: count_fl / total number of FL reads, mapped or unmapped
# Total Number of FL reads: 1065
#
pbid    count_fl        norm_fl
PB.1.1  2       1.8779e-03
PB.1.2  6       5.6338e-03
PB.1.3  3       2.8169e-03
PB.2.1  3       2.8169e-03
PB.3.1  2       1.8779e-03
PB.4.1  8       7.5117e-03

```


#### Multi Sample Chained FL Count

A multi-sample FL Count file produced by the [chain_samples.py](https://github.com/Magdoll/cDNA_Cupcake/wiki/Cupcake-ToFU:-supporting-scripts-for-Iso-Seq-after-clustering-step#chain) script in Cupcake will have the following format:

| superPBID | sample1 | sample2 |
| --------- | ------- | ------- |
| PB.1.2 | 3 | NA |
| PB.2.1 | 2 | NA |
| PB.3.1 | 2 | 2 |
| PB.3.2 | 5 | 3 |
| PB.3.3 | 5 | 2 |

This is a tab-delimited file.


#### Multi Sample Demux FL Count

A multi-sample Demux FL Count file produced by the [demux_isoseq_with_genome.py](https://github.com/Magdoll/cDNA_Cupcake/wiki/Tutorial:-Demultiplexing-SMRT-Link-Iso-Seq-Jobs) script in Cupcake will have the following format:

```
id,sample1,sample2
PB.1.1,3,10
PB.1.2,0,11
PB.1.3,4,4
```

This is a comma-delimited file.


#### SQANTI3 output of FL Count information

For each sample provided through the `--fl_count` option, `sqanti3_qc.py` will
create a column in the `_classification.txt` output file that is `FL.<sample>`.
Note that this is the raw FL count provided. The sum of all the FL reads
accross the samples associated to one transcript will be recorded in th `FL`
column of the `_classification.txt` output file.

When plotted, the script [SQANTI3_report.R](ConesaLab/SQANTI3/blob/tree/master/utilities/SQANTI3_report.R)
will convert the FL counts to TPM using the formula:

```
                           raw FL count for PB.X.Y in sample1
FL_TPM(PB.X.Y,sample1) = ------------------------------------- x 10^6
                               total FL count in sample1
```

Two additional columns, `FL_TPM.<sample>` and `FL_TPM.<sample>_log10` will be
added and output to a new classification file with the suffix
`_classification_TPM.txt`. Please, do not mix up `_classification_TPM.txt`
and `_classification.txt` files. The one used in subsequent scripts (filtering,
future isoAnnot, etc.) will be the `_classification.txt` one.


<a name="exp"/>

### Short Read Expression

Use `--expression` to optionally provide short read expression data. Two
formats are supported if you input one file per sample. In any case, you can
provide several expression data files as a chain of comma-separated paths or
by providing a directory were ONLY expression data is present. If more than one
file is provided, `iso_exp` column will represent the average expression value
accross all the files.

There is also the possibility of using as input an expression matrix, as a
tab-separated file, in which each transcript will be a row and each
sample/replicate a column. Transcript idientifiers must be the same than the
ones described in the *Long read-defined transcriptome* used as input and the
name for that column must be `ID`. The rest of the column names in the header
should be the sample/replicate identifier.

#### Kallisto Expression Input

Kallisto expression files have the format:

```
target_id   length  eff_length  est_counts  tpm
PB.1.1  1730    1447.8  0   0
PB.1.3  1958    1675.8  0   0
PB.2.1  213 54.454  0   0
PB.2.2  352 126.515 0   0
PB.3.1  153 40.3918 0   0
PB.4.1  1660    1377.8  0   0
PB.5.1  2767    2484.8  0   0
```

#### RSEM Expression Input

RSEM expression files have the format:

```
transcript_id   gene_id length  effective_length        expected_count  TPM     FPKM    IsoPct  posterior_mean_count    posterior_standard
_deviation_of_count     pme_TPM pme_FPKM        IsoPct_from_pme_TPM     TPM_ci_lower_bound      TPM_ci_upper_bound      FPKM_ci_lower_boun
d       FPKM_ci_upper_bound
PB.1.1  PB.1    1516    1369.11 8.00    0.05    0.22    100.00  8.00    0.00    0.06    0.25    100.00  0.0233365       0.0984532       0.
0981584 0.413561
PB.10.1 PB.10   1101    954.11  0.00    0.00    0.00    0.00    0.00    0.00    0.01    0.04    100.00  4.80946e-08     0.0283585       2.
01809e-07       0.11905
PB.100.1        PB.100  979     832.11  0.00    0.00    0.00    0.00    6.62    6.60    0.08    0.35    4.00    3.51054e-06     0.241555 1.47313e-05      1.01397
PB.100.2        PB.100  226     81.11   20.18   2.26    9.47    100.00  16.84   5.20    1.99    8.36    96.00   0.559201        3.45703 2.
34572   14.5141
```

<a name="filter"/>

### Filtering Isoforms using SQANTI3 output and a pre-defined rules

A lightweight filtering script named `sqanti3_RulesFilter` based on
SQANTI3 output is provided that filters for two things:
   1. intra-priming
   2. short read junction support.

The script usage is:
```
Usage: sqanti3_RulesFilter [OPTIONS] SQANTI_CLASS ISOFORMS ANNOTATION

  "Filtering of Isoforms based on SQANTI3 attributes

  Parameters:
  -----------
  sqanti_class:
      SQANTI classification output file
  isoforms:
      fasta/fastq isoform file to be filtered by SQANTI3
  annotation:
      GTF matching the input fasta/fastq
  junctions:
      junctions BED file generated by sqanti3_qc

Options:
  --sam TEXT                      (Optional) SAM alignment of the input
                                  fasta/fastq

  --faa TEXT                      (Optional) ORF prediction faa file to be
                                  filtered by SQANTI3

  -a, --intrapriming FLOAT RANGE  Adenine percentage at genomic 3' end to flag
                                  an isoform as intra-priming  [default: 0.6]

  -r, --runAlength INTEGER RANGE  Continuous run-A length at genomic 3' end to
                                  flag an isoform as intra-priming  [default:
                                  6]

  -m, --max_dist_to_known_end INTEGER
                                  Maximum distance to an annotated 3' end to
                                  preserve as a valid 3' end and not filter
                                  out  [default: 50]

  -c, --min_cov INTEGER           Minimum junction coverage for each isoform
                                  (only used if min_cov field is not 'NA')
                                  [default: 3]

  --filter_mono_exonic            Filter out all mono-exonic transcripts
                                  [default: False]

  --skipGTF                       Skip output of GTF  [default: False]
  --skipFaFq                      Skip output of isoform fasta/fastq
                                  [default: False]

  --skipJunction                  Skip output of junctions file  [default:
                                  False]

  --version                       Show the version and exit.
  --help                          Show this message and exit.
```

where 
   - `-a` determines the fraction of genomic 'A's above which the isoform will be filtered. The default is `-a 0.6`.
   - `-r` is another option for looking at genomic 'A's that looks at the immediate run-A length. The default is `-r 6`.
   - `-m` sets the maximum distance to an annotated 3' end (the `diff_to_gene_TTS` field in classification output) to offset the intrapriming rule.
   - `-c` is the filter for the minimum short read junction support (looking at the `min_cov` field in `_classification.txt`), and can only be used if you have short read data.

For example:

```
sqanti3_RulesFilter \
   test_classification.txt \
   test.renamed_corrected.fasta \
   test.gtf
```

The current filtering rules are as follow:

* If a transcript is FSM, then it is kept unless the 3' end is unreliable (intrapriming).
* If a transcript is not FSM, then it is kept only if all of below are true:
  1. 3' end is reliable.
  2. does not have a junction that is labeled as RTSwitching.
  3. all junctions are either canonical or has short read coverage above `-c` threshold.

<a name="explain"/>

### SQANTI3 Output Explanation


SQANTI/SQANTI2/SQANTI3 categorize each isoform by finding the best matching reference transcript in the following order:

* FSM (*Full Splice Match*): meaning the reference and query isoform have the same number of exons and each internal junction agree. The exact 5' start and 3' end can differ by any amount.

* ISM (*Incomplete Splice Match*): the query isoform has fewer 5' exons than the reference, but each internal junction agree. The exact 5' start and 3' end can differ by any amount.

* NIC (*Novel In Catalog*): the query isoform does not have a FSM or ISM match, but is using a combination of known donor/acceptor sites.

* NNC (*Novel Not in Catalog*): the query isoform does not have a FSM or ISM match, and has at least one donor or acceptor site that is not annotated.

* *Antisense*: the query isoform does not have overlap a same-strand reference gene but is anti-sense to an annotated gene.

* *Genic Intron*: the query isoform is completely contained within an annotated intron.

* *Genic Genomic*: the query isoform overlaps with introns and exons.

* *Intergenic*: the query isoform is in the intergenic region.

![sqanti_explain](https://github.com/FJPardoPalacios/public_figures/blob/master/figuras_class_SQ3.png)


Some of the classifications have further subtypes (the `subtype`) field in SQANTI3 classification output. They are explained below.

![ISM_subtype](https://github.com/FJPardoPalacios/public_figures/blob/master/figure_ism_subcat_SQ3.png)

Novel isoforms are subtyped based on whether they use a combination of known junctions (junctions are pairs of <donor>,<acceptor> sites), a combination of known splice sites (the individual donor and acceptor sites are known, but at least combination is novel), or at least one splice site (donor or acceptor) is novel.

![NIC_subtype](https://github.com/FJPardoPalacios/public_figures/blob/master/figure_nic_nnc_subcat_SQ3.png)

<a name="class"/>

#### Classification Output Explanation

The output `_classification.txt` has the following fields:

1. `isoform`: the isoform ID. Usually in `PB.X.Y` format.
2. `chrom`: chromosome.
3. `strand`: strand.
4. `length`: isoform length.
5. `exons`: number of exons.
6. `structural_category`: one of the categories ["full-splice_match", "incomplete-splice_match", "novel_in_catalog", "novel_not_in_catalog", "genic", "antisense", "fusion", "intergenic", "genic_intron"]
7. `associated_gene`: the reference gene name.
8. `associated_transcript`: the reference transcript name.
9. `ref_length`: reference transcript length.
10. `ref_exons`: reference transcript number of exons.
11. `diff_to_TSS`: distance of query isoform 5' start to reference transcript start end. Negative value means query starts downstream of reference.
12. `diff_to_TTS`: distance of query isoform 3' end to reference annotated end site. Negative value means query ends upstream of reference.
13. `diff_to_gene_TSS`: distance of query isoform 5' start to the closest start end of *any* transcripts of the matching gene. This field is different from `diff_to_TSS` since it's looking at all annotated starts of a gene. Negative value means query starts downstream of reference.
14. `diff_to_gene_TTS`: distance of query isoform 3' end to the closest end of *any* transcripts of the matching gene. Negative value means query ends upstream of reference.
13. `subcategory`: additional splicing categorization, separated by semi-colons. Categories include: `mono-exon`, `multi-exon`. Intron rentention is marked with `intron_retention`.
14. `RTS_stage`: TRUE if one of the junctions could be a RT switching artifact.
15. `all_canonical`: TRUE if all junctions have canonical splice sites.
16. `min_sample_cov`: sample with minimum coverage.
17. `min_cov`: minimum junction coverage based on short read STAR junction output file. NA if no short read given.
18. `min_cov_pos`: the junction that had the fewest coverage. NA if no short read data given.
19. `sd_cov`: standard deviation of junction coverage counts from short read data. NA if no short read data given.
20. `FL` or `FL.<sample>`: FL count associated with this isoform per sample if `--fl_count` is provided, otherwise NA.
21. `n_indels`: total number of indels based on alignment.
22. `n_indels_junc`: number of junctions in this isoform that have alignment indels near the junction site (indicating potentially unreliable junctions).
23. `bite`: TRUE if contains at least one "bite" positive SJ.
24. `iso_exp`: short read expression for this isoform if `--expression` is provided, otherwise NA.
25. `gene_exp`: short read expression for the gene associated with this isoform (summing over all isoforms) if `--expression` is provided, otherwise NA.
26. `ratio_exp`: ratio of `iso_exp` to `gene_exp` if `--expression` is provided, otherwise NA.
27. `FSM_class`: ignore this field for now.
28. `ORF_length`: predicted ORF length.
29. `CDS_length`: predicted CDS length.
30. `CDS_start`: CDS start.
31. `CDS_end`: CDS end.
32. `CDS_genomic_start`: genomic coordinate of the CDS start. If on - strand, this coord will be greater than the end.
33. `CDS_genomic_end`: genomic coordinate of the CDS end. If on - strand, this coord will be smaller than the start.
34. `predicted_NMD`: TRUE if there's a predicted ORF and CDS ends before the last junction; FALSE if otherwise. NA if non-coding.
35. `perc_A_downstreamTTS`: percent of genomic "A"s in the downstream 20 bp window. If this number if high (say > 0.8), the 3' end site of this isoform is probably not reliable.
36. `seq_A_downstream_TTS`: sequence of the downstream 20 bp window.
37. `dist_peak`: distance to closest TSS based on CAGE Peak data. Negative means upstream of TSS and positive means downstream of TSS. Strand-specific. SQANTI3 only searches for nearby CAGE Peaks within 10000 bp of the PacBio transcript start site. Will be `NA` if none are found within 10000 bp.
38. `within_peak`: TRUE if the PacBio transcript start site is within a CAGE Peak.
39. `polyA_motif`: if `--polyA_motif_list` is given, shows the top ranking polyA motif found within 50 bp upstream of end.
40. `polyA_dist`: if `--polyA_motif_list` is given, shows the location of the  last base of the hexamer. Position 0 is the putative poly(A) site. This distance is hence always negative because it is upstream.

<a name="junction"/>

### Junction Output Explanation


THe `.junctions.txt` file shows every junction for every PB isoform.
NOTE because of this the *same* junction might appear multiple times
if they are shared by multiple PB isoforms.

1. `isoform`: Isoform ID.
2. `junction_number`: The i-th junction of the isoform.
3. `chrom`: Chromosome.
4. `strand`: Strand.
5. `genomic_start_coord`: Start of the junction (1-based), note that if on - strand, this would be the junction acceptor site instead.
6. `genomic_end_coord`: End of the junction (1-based), note that if on - strand, this would be the junction donor site instead.
7. `transcript_coord`: Currently not implemented. Ignore.
8. `junction_category`: `known` if the (donor-acceptor) combination is annotated in the GTF file, `novel` otherwise. Note that it is possible to have a `novel` junction even though both the donor and acceptor site are known, since the combination might be novel.
9. `start_site_category`: `known` if the junction start site is annotated. If on - strand, this is actually the donor site.
10. `end_site_category`: `known` if the junction end site is annotated. If on - strand, this is actually the acceptor site.
11. `diff_to_Ref_start_site`: distance to closest annotated junction start site. If on - strand, this is actually the donor site.
12. `diff_to_Ref_end_site`: distance to closest annotated junction end site. If on - strand, this is actually the acceptor site.
13. `bite_junction`: Applies only to novel splice junctions. If the novel intron partially overlaps annotated exons the bite value is TRUE, otherwise it is FALSE.
14. `splice_site`: Splice motif.
15. `RTS_junction`: TRUE if junction is predicted to a template switching artifact.
16. `indel_near_junct`: TRUE if there is alignment indel error near the junction site, indicating potential junction incorrectness.
17. `sample_with_cov`: If `--coverage` (short read junction coverage info) is provided, shows the number of samples (cov files) that have short read that support this junction.
18. `total_coverage`: Total number of short read support from all samples that cover this junction.
