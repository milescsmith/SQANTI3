#!/usr/bin/env python
# Script to generate a GFF3 file from SQANTI3 output and using a tappAS GFF3 as reference.

import logging
import math
import os
import sys
import time
from typing import Optional, Tuple, Dict, List
from tqdm import tqdm

# import argparse
import click
import gtfparse
import pandas as pd

# import bisect

# Global Variables
version = 1.5


NEWLINE = "\n"
TAB = "\t"

# Functions
def createGTFFromSqanti(
    file_exons: str, file_trans: str, file_junct: str, filename: str
) -> Tuple[
    Dict[str, List[str]], Dict[str, List[str]], Dict[str, List[str]], Dict[str, str]
]:
    logger = logging.getLogger("IsoAnnotLite_SQ1")
    source = "tappAS"
    aux = "."

    dc_coding: Dict[str, List[str]] = {}
    dc_gene: Dict[str, List[str]] = {}
    dc_SQstrand: Dict[str, str] = {}

    logger.debug(f"reading classification file {file_trans}")
    classification_df = pd.read_csv(file_trans, delimiter="\t")

    CLASS_COLUMN_NAMES = [
        "isoform",
        "chrom",
        "strand",
        "length",
        "structural_category",
        "associated_gene",
        "associated_transcript",
        "ORF_length",
        "CDS_start",
        "CDS_end",
    ]

    missing_names = [
        _ for _ in CLASS_COLUMN_NAMES if _ not in classification_df.columns
    ]

    if missing_names:
        logger.info(
            f"File classification does not have the necessary fields. "
            f"The columns {','.join(missing_names)} were not found in the "
            f"in the classification file."
        )
        sys.exit()

    # so, weird trick - it is *really* slow to append to a list or dataframe
    # however, you can add on to a dictionary really quickly.
    # also, you can easily convert a dictionary to a dataframe.
    # so,
    res = dict()
    i = 0

    # TODO: vectorize this?
    # add transcript, gene and CDS
    for row in tqdm(classification_df.itertuples(), total=len(classification_df)):
        # trans
        transcript = row.isoform  # fields[0]
        # source
        feature = "transcript"
        start = "1"
        end = row.length  # fields[3]
        # aux
        strand = row.strand  # fields[2]

        dc_SQstrand[str(transcript)] = strand  # saving strand

        desc = f"ID={row.associated_transcript}; primary_class={row.structural_category}{NEWLINE}"  # desc = "ID="+fields[7]+"; primary_class="+fields[5]+"\n"
        res[i] = {
            "seqname": transcript,
            "source": source,
            "feature": feature,
            "start": str(int(start)),
            "end": str(int(end)),
            "score": aux,
            "strand": strand,
            "frame": aux,
            "attribute": desc,
        }

        # gene
        transcript = row.isoform
        # source
        feature = "gene"
        start = "1"
        end = row.length
        # aux
        strand = row.strand
        desc = f"ID={row.associated_gene}; Name={row.associated_gene}; Desc={row.associated_gene}{NEWLINE}"

        i += 1
        res[i] = {
            "seqname": transcript,
            "source": source,
            "feature": feature,
            "start": str(int(start)),
            "end": str(int(end)),
            "score": aux,
            "strand": strand,
            "frame": aux,
            "attribute": desc,
        }

        # CDS
        transcript = row.isoform
        # source
        feature = "CDS"
        start = row.CDS_start  # 30
        end = row.CDS_end  # 31
        # aux
        strand = row.strand
        desc = f"ID=Protein_{transcript}; Name=Protein_{transcript}; Desc=Protein_{transcript}{NEWLINE}"
        if start != "NA" and not pd.isnull(start):
            prot_length = int(math.ceil((int(end) - int(start) - 1) / 3))
            i += 1
            res[i] = {
                "seqname": transcript,
                "source": source,
                "feature": feature,
                "start": str(int(start)),
                "end": str(int(end)),
                "score": aux,
                "strand": strand,
                "frame": aux,
                "attribute": desc,
            }
            i += 1
            res[i] = {
                "seqname": transcript,
                "source": source,
                "feature": "protein",
                "start": "1",
                "end": str(prot_length),
                "score": aux,
                "strand": strand,
                "frame": aux,
                "attribute": desc,
            }

            # res.write("\t".join([transcript,source, feature, str(int(start)), str(int(end)), aux, strand, aux, desc]))
            # res.write("\t".join([transcript,source,"protein","1",str(prot_length),aux,strand,aux,desc]))
        # else:
        # res.write("\t".join([transcript, source, feature, ".", ".", aux, strand, aux, desc]))

        # genomic
        desc = f"Chr={row.chrom}{NEWLINE}"

        # Gene
        gene = row.associated_gene
        category = row.structural_category
        transAssociated = row.associated_gene

        if transAssociated.startswith("ENS"):
            transAssociated = transAssociated.split(".")[
                0
            ]  # ENSMUS213123.1 -> #ENSMUS213123

        if transcript not in dc_gene:
            dc_gene[str(transcript)] = [gene, category, transAssociated]
        else:
            dc_gene[str(transcript)] = dc_gene[transcript] + [
                gene,
                category,
                transAssociated,
            ]

        # Coding Dictionary
        CDSstart = row.CDS_start  # 30
        CDSend = row.CDS_end  # 31
        orf = row.ORF_length  # 28

        if transcript not in dc_coding:
            dc_coding[str(transcript)] = [CDSstart, CDSend, orf]
        else:
            dc_coding[str(transcript)] = dc_coding[transcript] + [CDSstart, CDSend, orf]

        i += 1
        res[i] = {
            "seqname": transcript,
            "source": source,
            "feature": "genomic",
            "start": "1",
            "end": "1",
            "score": aux,
            "strand": strand,
            "frame": aux,
            "attribute": desc,
        }

        # Write TranscriptAttributes
        sourceAux = "TranscriptAttributes"
        lengthTranscript = row.length
        if not CDSstart == "NA" and not pd.isnull(row.CDS_start):
            # 3'UTR
            feature = "3UTR_Length"
            start = int(CDSend) + 1
            end = lengthTranscript
            desc = "ID=3UTR_Length; Name=3UTR_Length; Desc=3UTR_Length\n"
            i += 1
            res[i] = {
                "seqname": transcript,
                "source": sourceAux,
                "feature": feature,
                "start": str(int(start)),
                "end": str(int(end)),
                "score": aux,
                "strand": strand,
                "frame": aux,
                "attribute": desc,
            }

            # 5'UTR
            feature = "5UTR_Length"
            start = 1
            end = int(row.CDS_start) - 1 + 1  # 30
            desc = "ID=5UTR_Length; Name=5UTR_Length; Desc=5UTR_Length\n"
            i += 1
            res[i] = {
                "seqname": transcript,
                "source": sourceAux,
                "feature": feature,
                "start": str(int(start)),
                "end": str(int(end)),
                "score": aux,
                "strand": strand,
                "frame": aux,
                "attribute": desc,
            }

            # CDS
            feature = "CDS"
            start = CDSstart
            end = CDSend
            desc = "ID=CDS; Name=CDS; Desc=CDS\n"
            i += 1
            res[i] = {
                "seqname": transcript,
                "source": sourceAux,
                "feature": feature,
                "start": str(int(start)),
                "end": str(int(end)),
                "score": aux,
                "strand": strand,
                "frame": aux,
                "attribute": desc,
            }

            # polyA
            feature = "polyA_Site"
            start = lengthTranscript
            end = lengthTranscript
            desc = "ID=polyA_Site; Name=polyA_Site; Desc=polyA_Site\n"
            i += 1
            res[i] = {
                "seqname": transcript,
                "source": sourceAux,
                "feature": feature,
                "start": str(int(start)),
                "end": str(int(end)),
                "score": aux,
                "strand": strand,
                "frame": aux,
                "attribute": desc,
            }

    dc_exons: Dict[str, List[str]] = {}
    # add exons
    logger.debug(f"reading exon file {file_exons}")
    exons_df = gtfparse.read_gtf(file_exons)

    for row in tqdm(exons_df.itertuples(), total=len(exons_df)):
        transcript = row.transcript_id
        # source
        feature = row.feature
        if feature == "transcript":  # just want exons
            continue

        start = row.start
        end = row.end
        # aux
        strand = row.strand
        # desc = fields[8]
        desc = f"Chr={str(row.seqname)}{NEWLINE}"

        # Exons Dictionary
        if transcript not in dc_exons:
            dc_exons[str(transcript)] = [[start, end]]
        else:
            dc_exons[str(transcript)] = dc_exons[transcript] + [[start, end]]
        i += 1
        res[i] = {
            "seqname": transcript,
            "source": source,
            "feature": feature,
            "start": str(int(start)),
            "end": str(int(end)),
            "score": aux,
            "strand": strand,
            "frame": aux,
            "attribute": desc,
        }

    # add junctions
    logger.debug(f"reading junctions file {file_junct}")
    junct_df = pd.read_csv(file_junct, delimiter="\t")
    # header
    for row in tqdm(junct_df.itertuples(), total=len(junct_df)):
        transcript = row.isoform
        # source
        feature = "splice_junction"
        start = row.genomic_start_coord
        end = row.genomic_end_coord
        # aux
        strand = row.strand
        desc = f"ID={row.junction_number}_{row.canonical}; Chr={row.chrom}{NEWLINE}"
        i += 1
        res[i] = {
            "seqname": transcript,
            "source": source,
            "feature": feature,
            "start": str(int(start)),
            "end": str(int(end)),
            "score": aux,
            "strand": strand,
            "frame": aux,
            "attribute": desc,
        }

    logger.debug(f"length of dictionary: {len(res)}")
    logger.debug("converting dictionary to dataframe")
    results_df = pd.DataFrame.from_dict(
        res,
        orient="index",
        columns=[
            "seqname",
            "source",
            "feature",
            "start",
            "end",
            "score",
            "strand",
            "frame",
            "attribute",
        ],
    )
    results_df["attribute"] = results_df["attribute"].apply(lambda x: x.rstrip("\n"))
    logger.debug(f"results_df shape: {results_df.shape}")
    logger.debug(f"writing to new gtf {filename}")
    # gtfparse.df_to_gtf(df=results_df, filename=filename) # this is really slow.  no idea why
    results_df.to_csv(
        path_or_buf=filename,
        sep="\t",
        header=False,
        index=False,
        columns=[
            "seqname",
            "source",
            "feature",
            "start",
            "end",
            "score",
            "strand",
            "frame",
            "attribute",
        ],
    )
    return dc_exons, dc_coding, dc_gene, dc_SQstrand


def readGFF(
    gff3: str,
) -> Tuple[
    Dict[str, List[List[str]]], # dc_GFF3 
    Dict[int, List[str]],       # dc_GFF3exonsTrans
    Dict[str, List[List[int]]], # dc_GFF3transExons
    Dict[str, List[int]],       # dc_GFF3coding
    Dict[str, str],             # dc_GFF3strand
]:

    logger = logging.getLogger("IsoAnnotLite_SQ1")
    f = gtfparse.parse_gtf(gff3)
    # create dictionary for each transcript and dictionary for exons
    
    # So, like can't we just filter the dataframe and skip all this?
    dc_GFF3 = {}
    dc_GFF3exonsTrans = {}
    dc_GFF3transExons = {}
    dc_GFF3coding = {}
    dc_GFF3strand = {}
    try:
        assert len(f.columns) == 9
    except AssertionError:
        logging.exception(
            f"File {gff3} doesn't have the correct number of columns.  It should have 9, but actually has {len(f.columns)}."
        )


    for line in f.itertuples():

        # feature (transcript, gene, exons...)
        transcript = line.seqname
        feature = line.feature
        start = line.start
        end = line.end
        strand = line.strand

        if strand != ".":
            dc_GFF3strand[str(transcript)] = strand  # saving strand

        attributes = [_.strip() for _ in line.attribute.split(";")]
        if not attributes[-1].endswith("\n"):
            line = line + "\n"

        if feature == "exon":
            if str(transcript) not in dc_GFF3transExons:
                dc_GFF3transExons[str(transcript)] = [[int(start), int(end)]]
            else:
                dc_GFF3transExons[str(transcript)] = dc_GFF3transExons[
                    str(transcript)
                ] + [[int(start), int(end)]]
            if int(start) not in dc_GFF3exonsTrans:
                dc_GFF3exonsTrans[int(start)] = [transcript]
            else:
                dc_GFF3exonsTrans[int(start)] = dc_GFF3exonsTrans[int(start)] + [
                    transcript
                ]
        elif feature == "CDS":
            if str(transcript) not in dc_GFF3coding:
                dc_GFF3coding[str(transcript)] = [int(start), int(end)]
            else:
                dc_GFF3coding[str(transcript)] = dc_GFF3coding[str(transcript)] + [
                    int(start),
                    int(end),
                ]

        elif feature in [
            "splice_junction",
            "transcript",
            "gene",
            "protein",
            "genomic",
        ]:
            continue
        
        else:
            line_rep = (
                f"{line.seqname}{TAB}{line.source}{TAB}{line.feature}{TAB}"
                f"{line.start}{TAB}{line.end}{TAB}{line.score}{TAB}"
                f"{line.score}{TAB}{line.strand}{TAB}{line.frame}{TAB}"
                f"{line.attribute}{NEWLINE}"
            )
            if transcript not in dc_GFF3:
                dc_GFF3[str(transcript)] = [[start, end, line_rep]]
            else:
                dc_GFF3[str(transcript)] = dc_GFF3[transcript] + [
                    [start, end, line_rep]
                ]

    sorted(dc_GFF3exonsTrans.keys())
    return (dc_GFF3, dc_GFF3exonsTrans, dc_GFF3transExons, dc_GFF3coding, dc_GFF3strand)

def transformTransFeaturesToGenomic(
    dc_GFF3, dc_GFF3transExons, dc_GFF3coding, dc_GFF3strand
):
    logger = logging.getLogger("IsoAnnotLite_SQ1")
    newdc_GFF3 = {}
    bnegative = False

    for trans in dc_GFF3transExons.keys():
        if trans not in dc_GFF3:
            continue
        annot = dc_GFF3[trans]
        for values in annot:
            bProt = False
            line = values[2]
            fields = line.split("\t")
            text = fields[8].split(" ")
            strand = dc_GFF3strand[trans]

            start = 0
            end = 0
            startG = 0
            endG = 0
            # Transcript calculate normal - include CDS
            if text[-1].endswith("T\n") and not fields[3] == ".":
                start = int(fields[3])
                end = int(fields[4])
            elif text[-1].endswith("P\n") and not fields[3] == ".":
                start = int(fields[3])
                end = int(fields[4])
                bProt = True
            else:
                if trans not in newdc_GFF3:
                    newdc_GFF3[str(trans)] = [values]
                    continue
                else:
                    newdc_GFF3[str(trans)] = newdc_GFF3[trans] + [values]
                    continue

            totalDiff = end - start
            if not bProt:
                allExons = dc_GFF3transExons[trans]
            else:
                allExons = dc_GFF3coding[trans]
                if not allExons:
                    continue

            if strand == "+":
                allExons = sorted(allExons)
            else:
                allExons = sorted(allExons, reverse=True)

            bstart = False
            bend = False
            for exon in allExons:
                if totalDiff < 0:
                    bnegative = True
                    break

                # START already found
                if bstart:
                    if exon[0] + totalDiff - 1 <= exon[1]:  # pos ends here
                        end = exon[0] + totalDiff
                        endG = end
                        bend = True
                    else:  # pos ends in other exon and we add the final exon
                        totalDiff = totalDiff - (exon[1] - exon[0] + 1)

                # Search for START
                if exon[1] - exon[0] + 1 >= start and not bstart:  # pos starts here
                    start = exon[0] + int(start) - 1
                    startG = start
                    bstart = True
                    if start + totalDiff - 1 <= exon[1]:  # pos ends here
                        end = start + totalDiff
                        endG = end
                        bend = True
                    else:  # pos ends in other exon and we add the final exon
                        totalDiff = totalDiff - (exon[1] - start + 1)
                else:
                    # not in first exon, update the start and end pos substrating exon length
                    start = start - (exon[1] - exon[0] + 1)
                    end = end - (exon[1] - exon[0] + 1)

                if bend:
                    if not bProt:
                        if strand == "+":
                            NEWLINE = (
                                fields[0]
                                + "\t"
                                + fields[1]
                                + "\t"
                                + fields[2]
                                + "\t"
                                + str(startG)
                                + "\t"
                                + str(endG)
                                + "\t"
                                + fields[5]
                                + "\t"
                                + fields[6]
                                + "\t"
                                + fields[7]
                                + "\t"
                                + fields[8]
                            )
                        else:
                            NEWLINE = (
                                fields[0]
                                + "\t"
                                + fields[1]
                                + "\t"
                                + fields[2]
                                + "\t"
                                + str(endG)
                                + "\t"
                                + str(startG)
                                + "\t"
                                + fields[5]
                                + "\t"
                                + fields[6]
                                + "\t"
                                + fields[7]
                                + "\t"
                                + fields[8]
                            )
                        if trans not in newdc_GFF3:
                            newdc_GFF3[str(trans)] = [[startG, endG, NEWLINE]]
                            break
                        else:
                            newdc_GFF3[str(trans)] = newdc_GFF3[trans] + [
                                [startG, endG, NEWLINE]
                            ]
                            break
                    else:
                        if strand == "-":
                            aux = startG
                            startG = endG
                            endG = aux
                        if trans not in newdc_GFF3:
                            newdc_GFF3[str(trans)] = [[startG, endG, values[2]]]
                            break
                        else:
                            newdc_GFF3[str(trans)] = newdc_GFF3[trans] + [
                                [startG, endG, values[2]]
                            ]
                            break
            if bnegative:
                break

    return newdc_GFF3


def transformTransFeaturesToLocale(dc_GFF3, dc_SQexons):
    logger = logging.getLogger("IsoAnnotLite_SQ1")
    dc_newGFF3 = {}
    for trans in dc_GFF3.keys():
        annot = dc_GFF3[trans]
        line = annot[0]
        line = line.split("\t")
        strand = line[6]

        exons = dc_SQexons[trans]
        if strand == "+":
            exons = sorted(exons)
        else:
            exons = sorted(exons, reverse=True)
        start = 0
        end = 0
        for line in annot:
            fields = line.split("\t")
            text = fields[8].split(" ")
            if fields[1] == "tappAS":
                continue

            elif text[-1].endswith("T\n"):

                if strand == "+":
                    startG = fields[3]
                    endG = fields[4]
                else:
                    startG = fields[4]
                    endG = fields[3]
                bstart = False
                bend = False
                distance = 0  # other exons
                for ex in exons:
                    if not startG == "." or not endG == ".":
                        # SEARCH FOR START
                        if (
                            int(startG) >= int(ex[0])
                            and int(startG) <= int(ex[1])
                            and not bstart
                        ):  # start
                            start = (int(startG) - int(ex[0]) + 1) + distance
                            bstart = True
                            if int(endG) >= int(ex[0]) and int(endG) <= int(ex[1]):
                                end = start + (int(endG) - int(startG) + 1) - 1
                                bend = True
                                break
                            else:
                                distance = int(ex[1]) - int(startG) + 1
                                continue

                        elif not bstart:
                            distance = distance + (int(ex[1]) - int(ex[0]) + 1)

                        # SEARCH FOR END
                        if bstart:
                            if int(endG) >= int(ex[0]) and int(endG) <= int(ex[1]):
                                end = (
                                    (int(endG) - int(ex[0]) + 1) + distance + start - 1
                                )
                                bend = True
                                break
                            else:
                                distance = distance + (int(ex[1]) - int(ex[0]) + 1)
                    else:
                        start = startG
                        end = endG
                        bend = True
                        break
                if bend:  # to be sure in full-spliced match cases
                    NEWLINE = (
                        fields[0]
                        + "\t"
                        + fields[1]
                        + "\t"
                        + fields[2]
                        + "\t"
                        + str(int(start))
                        + "\t"
                        + str(int(end))
                        + "\t"
                        + fields[5]
                        + "\t"
                        + fields[6]
                        + "\t"
                        + fields[7]
                        + "\t"
                        + fields[8]
                    )
                    if trans not in dc_newGFF3:
                        dc_newGFF3[str(trans)] = [NEWLINE]
                    else:
                        dc_newGFF3[str(trans)] = dc_newGFF3[trans] + [NEWLINE]
            else:
                if trans not in dc_newGFF3:
                    dc_newGFF3[str(trans)] = [line]
                else:
                    dc_newGFF3[str(trans)] = dc_newGFF3[trans] + [line]
    return dc_newGFF3


def transformProtFeaturesToLocale(dc_GFF3, dc_SQexons, dc_SQcoding):
    logger = logging.getLogger("IsoAnnotLite_SQ1")
    dc_newGFF3 = {}
    for trans in dc_GFF3.keys():
        annot = dc_GFF3[trans]
        line = annot[0]
        line = line.split("\t")
        strand = line[6]

        exons = dc_SQexons[trans]
        if strand == "+":
            exons = sorted(exons)
        else:
            exons = sorted(exons, reverse=True)

        annot = dc_GFF3[trans]

        start = 0
        end = 0
        if trans not in dc_SQcoding:
            continue
        startcoding = dc_SQcoding[trans][0]
        startcoding = startcoding[0]
        if startcoding == "NA":
            continue

        for line in annot:
            fields = line.split("\t")
            text = fields[8].split(" ")
            if fields[1] == "tappAS":
                continue
            if text[-1].endswith("P\n"):
                startG = fields[3]
                endG = fields[4]

                bstart = False
                CDSstart = False
                distance = 0  # other exons
                for ex in exons:
                    if not startG == "." or not endG == ".":
                        if not CDSstart:  # CDS start
                            if (
                                int(startcoding) >= int(ex[0])
                                and int(startcoding) <= int(ex[1])
                                and not bstart
                            ):  # start

                                start = (
                                    int(startG) - int(ex[0]) + 1 + distance
                                )  # CDSstart
                                CDSstart = True
                            else:
                                distance = distance + int(ex[1]) - int(startG) + 1
                        if (
                            int(startG) >= int(ex[0])
                            and int(startG) <= int(ex[1])
                            and not bstart
                            and CDSstart
                        ):  # start

                            start = (
                                int(startG) - int(start) + 1 + distance
                            )  # diff between genomic pos and CDSstart
                            bstart = True
                            if int(endG) >= int(ex[0]) and int(endG) <= int(ex[1]):
                                end = start + int(endG) - int(startG) + 1
                                break
                            else:
                                distance = distance + int(ex[1]) - int(startG) + 1
                        else:
                            distance = int(ex[1]) - int(ex[0]) + 1
                        if bstart and CDSstart:
                            if int(endG) >= int(ex[0]) and int(endG) <= int(ex[1]):
                                end = int(endG) - int(ex[0]) + 1 + distance
                                break
                            else:
                                distance = distance + (int(ex[1]) - int(ex[0]) + 1)
                    else:
                        start = startG
                        end = endG
                NEWLINE = (
                    fields[0]
                    + "\t"
                    + fields[1]
                    + "\t"
                    + fields[2]
                    + "\t"
                    + str(int(start))
                    + "\t"
                    + str(int(end))
                    + "\t"
                    + fields[5]
                    + "\t"
                    + fields[6]
                    + "\t"
                    + fields[7]
                    + "\t"
                    + fields[8]
                )
                if trans not in dc_newGFF3:
                    dc_newGFF3[str(trans)] = [NEWLINE]
                else:
                    dc_newGFF3[str(trans)] = dc_newGFF3[trans] + [NEWLINE]
            else:
                if trans not in dc_newGFF3:
                    dc_newGFF3[str(trans)] = [line]
                else:
                    dc_newGFF3[str(trans)] = dc_newGFF3[trans] + [line]
    return dc_newGFF3


def transformCDStoGenomic(dc_SQcoding, dc_SQexons, dc_SQstrand):
    logger = logging.getLogger("IsoAnnotLite_SQ1")
    newdc_coding = {}
    bnegative = False

    for trans in dc_SQcoding.keys():
        newCDS = []
        aux = []
        CDS = dc_SQcoding[trans]

        if CDS[0] == "NA":
            if str(trans) not in newdc_coding:
                newdc_coding[str(trans)] = [CDS]
            else:
                newdc_coding[str(trans)] = newdc_coding[str(trans)] + [CDS]
            continue

        totalDiff = int(CDS[1]) - int(CDS[0])

        allExons = dc_SQexons[trans]
        if not allExons:
            continue

        if dc_SQstrand[trans] == "+":
            allExons = sorted(allExons)
        else:
            allExons = sorted(allExons, reverse=True)
        bstart = False
        bend = False
        start = 0
        end = 0
        for exon in allExons:
            if totalDiff < 0:
                logging.error("The difference can't be negative.")
                bnegative = True
                break

            # START already found
            if bstart:
                if exon[0] + totalDiff - 1 <= exon[1]:  # CDS ends here
                    end = exon[0] + totalDiff - 1
                    aux = [[exon[0], end]]
                    newCDS = newCDS + aux
                    bend = True
                else:  # CDS ends in other exon and we add the final exon
                    aux = [[exon[0], exon[1]]]
                    newCDS = newCDS + aux
                    totalDiff = totalDiff - (exon[1] - exon[0] + 1)

            # Search for START
            if exon[1] - exon[0] + 1 >= int(CDS[0]) and not bstart:  # CDS starts here
                start = exon[0] + int(CDS[0]) - 1
                bstart = True
                if start + totalDiff - 1 <= exon[1]:  # CDS ends here
                    end = start + totalDiff - 1
                    aux = [[start, end]]
                    newCDS = newCDS + aux
                    bend = True
                else:  # CDS ends in other exon and we add the final exon
                    aux = [[start, exon[1]]]
                    newCDS = newCDS + aux
                    totalDiff = totalDiff - (exon[1] - start + 1)

            if bend:
                if str(trans) not in newdc_coding:
                    newdc_coding[str(trans)] = newCDS
                else:
                    newdc_coding[str(trans)] = newdc_coding[str(trans)] + newCDS
                break
        if bnegative:
            break

    return newdc_coding


def checkSameCDS(dc_SQcoding, dc_GFF3coding, transSQ, transGFF3, strand):
    coding = True
    semicoding = True
    total_semi = 0
    total_annot = 0
    if transSQ in dc_SQcoding and transGFF3 in dc_GFF3coding:
        if transSQ not in dc_SQcoding[0][0] == "NA":
            # Tenemos rango de intervalos en los exones:
            #   Si coinciden todos es coding
            #   Si coinciden todos menos sub exons (inicio o final) es semicoding
            allExonsGFF3 = dc_GFF3coding[transGFF3]
            if strand == "+":
                allExonsGFF3 = sorted(allExonsGFF3)
            else:
                allExonsGFF3 = sorted(allExonsGFF3, reverse=True)
            for ex in allExonsGFF3:
                allExonsSQ = dc_SQcoding[transSQ]
                if strand == "+":
                    allExonsSQ = sorted(allExonsSQ)
                else:
                    allExonsSQ = sorted(allExonsSQ, reverse=True)

                if ex in allExonsSQ:
                    total_annot = total_annot + 1
                    continue
                else:
                    coding = False
                    semicoding = False  # Check if we found semicoding
                    for exSQ in allExonsSQ:
                        if ex[0] <= exSQ[0] and exSQ[1] <= ex[1]:  # Region inside
                            total_semi = total_semi + 1
                            semicoding = True
                            break
                        elif (
                            exSQ[0] <= ex[0] and exSQ[1] <= ex[1]
                        ):  # or region bigger by left
                            total_semi = total_semi + 1
                            semicoding = True
                            break
                        elif (
                            ex[0] <= exSQ[0] and ex[1] <= exSQ[1]
                        ):  # or region bigger by right
                            total_semi = total_semi + 1
                            semicoding = True
                            break
                        elif (
                            exSQ[0] <= ex[0] and ex[1] <= exSQ[1]
                        ):  # or region bigger by both sides
                            total_semi = total_semi + 1
                            semicoding = True
                            break

        if (
            total_annot == len(dc_GFF3coding[transGFF3])
            and transGFF3 not in dc_GFF3coding
        ):
            coding = True
        elif total_annot > 0 or total_semi > 0:
            semicoding = True
        else:
            coding = False
            semicoding = False
    return coding, semicoding


def checkFeatureInCDS(
    dc_SQcoding, dc_GFF3coding, transSQ, transGFF3, start, end, strand
):
    bstart = False
    if (
        not dc_SQcoding[transSQ][0] == "NA"
        and transSQ in dc_SQcoding
        and transGFF3 in dc_GFF3coding
    ):
        # Tenemos rango de intervalos en los exones:
        #   Si coinciden todos es coding
        #   Si coinciden todos menos sub exons (inicio o final) es semicoding
        allExonsGFF3 = dc_GFF3coding[transGFF3]
        allExonsSQ = dc_SQcoding[transSQ]

        if strand == "+":
            allExonsGFF3 = sorted(allExonsGFF3)
            allExonsGFF3 = sorted(allExonsSQ)
        else:
            allExonsGFF3 = sorted(allExonsGFF3, reverse=True)
            allExonsSQ = sorted(allExonsSQ, reverse=True)

        for ex in allExonsGFF3:

            #########
            #  END  #
            #########
            if bstart:
                if ex[0] <= end and end <= ex[1]:  # end in exon
                    if ex in allExonsSQ:  # if exon exist
                        return True
                    else:
                        for exSQ in allExonsSQ:  # we just need end subexon
                            if (
                                exSQ[0] == ex[0] and end <= exSQ[1]
                            ):  # and feature in range
                                return True
                        return False  # doesnt find the feture in same exon
                else:  # in next exon
                    if ex not in allExonsSQ:
                        return False  # end in another exons and we don't have that intermediate in SQ
                    else:
                        continue

            #########
            # START #
            #########
            if ex[0] <= start and start <= ex[1] and not bstart:  # start in exon
                if ex[0] <= end and end <= ex[1]:  # end in exon
                    if ex in allExonsSQ:  # if exon exist
                        return True
                    else:
                        for exSQ in allExonsSQ:  # we just need start and end in subexon
                            if (
                                exSQ[0] <= start
                                and start <= exSQ[1]
                                and exSQ[0] <= end
                                and end <= exSQ[1]
                            ):  # and feature in range
                                return True
                        return False  # doesnt find the feture in same exon
                else:  # we need an exSQ that ends in same position to continue
                    for exSQ in allExonsSQ:
                        if (
                            exSQ[0] <= start and ex[1] == exSQ[1]
                        ):  # at begining just start but end the same
                            bstart = True
    return False


def checkFeatureInTranscript(
    dc_SQexons, dc_GFF3transExons, transSQ, transGFF3, start, end, strand
):
    bstart = False
    bnotMiddleExon = False
    if transSQ in dc_SQexons and transGFF3 in dc_GFF3transExons:
        # Tenemos rango de intervalos en los exones:
        #   Si coinciden todos es coding
        #   Si coinciden todos menos sub exons (inicio o final) es semicoding
        allExonsGFF3 = dc_GFF3transExons[transGFF3]
        allExonsSQ = dc_SQexons[transSQ]
        if strand == "+":
            allExonsGFF3 = sorted(allExonsGFF3)
            allExonsSQ = sorted(allExonsSQ)
        else:
            allExonsGFF3 = sorted(allExonsGFF3, reverse=True)
            allExonsSQ = sorted(allExonsSQ, reverse=True)

        for ex in allExonsGFF3:
            if ex[0] <= start and start <= ex[1] and not bstart:  # Annot in exon
                for exSQ in allExonsSQ:  # Look for Start
                    if ex[0] <= end and end <= ex[1]:  # also end it's here
                        if ex in allExonsSQ:  # if exon exist
                            return True
                        elif (
                            exSQ[0] <= start
                            and start <= exSQ[1]
                            and exSQ[0] <= end
                            and end <= exSQ[1]
                        ):  # case when we have the end at same exon but with different length (although same genomic positions
                            return True

                    elif (
                        exSQ[0] <= start and start <= exSQ[1] and ex[1] == exSQ[1]
                    ):  # end in another exon, we need same ending
                        bstart = True
            elif bstart and ex[0] <= end and end <= ex[1]:  # End Annot in exon
                for exSQ in allExonsSQ:  # Look for End
                    if ex in allExonsSQ:  # if exon exist
                        return True
                    elif (
                        exSQ[0] <= end and end <= exSQ[1] and ex[0] == exSQ[0]
                    ):  # end in another exon, we need same exon start
                        return True
                    else:  # we need same exon
                        if not ex[0] == exSQ[0] and not ex[1] == exSQ[1]:
                            bnotMiddleExon = True  # We don't found the middle Exons
                            break
            else:
                continue

            if bnotMiddleExon:
                break

    return False


def mappingFeatures(
    dc_SQexons,
    dc_SQcoding,
    dc_SQtransGene,
    dc_GFF3exonsTrans,
    dc_GFF3transExons,
    dc_GFF3,
    dc_GFF3coding,
    filename,
):
    logger = logging.getLogger("IsoAnnotLite_SQ1")
    f = open(filename, "a+")
    print("\n")
    transcriptsAnnotated = 0
    totalAnotations = 0
    featuresAnnotated = 0
    for transSQ in dc_SQexons.keys():

        # Be carefully - not all tranSQ must be in SQtransGene
        if str(transSQ) not in dc_SQtransGene:
            continue

        perct = transcriptsAnnotated / len(dc_SQexons) * 100
        logger.info(f"{perct:.2f}% of transcripts annotated...")

        #######################
        # IF FULL-SPLICED-MATCH#
        #######################
        infoGenomic = dc_SQtransGene[transSQ]
        transGFF3 = infoGenomic[2]

        ###########################
        # IF NOT FULL-SPLICED-MATCH#
        ###########################
        val = ""
        if transGFF3 in dc_GFF3:  # Novel Transcript won't be annoted
            val = transGFF3 in dc_GFF3
        elif transSQ in dc_GFF3.get():
            transGFF3 = transSQ
            val = dc_GFF3[transGFF3]
        else:
            continue

        line = val[0][2].split("\t")
        strand = line[6]
        # Check if we had same CDS to add Protein information
        coding, semicoding = checkSameCDS(
            dc_SQcoding, dc_GFF3coding, transSQ, transGFF3, strand
        )

        for values in dc_GFF3[transGFF3]:
            fields = values[2].split("\t")
            text = fields[8].split(" ")
            strand = fields[6]
            if fields[1] == "tappAS":
                continue
            totalAnotations = totalAnotations + 1
            ####################
            # PROTEIN ANNOTATION#
            ####################
            if (
                text[-1].endswith("P\n")
                or text[-1].endswith("G\n")
                or text[-1].endswith("N\n")
            ):  # protein
                if coding:
                    index = values[2].find("\t")
                    if values[2].endswith("\n"):
                        featuresAnnotated = featuresAnnotated + 1
                        f.write(transSQ + values[2][index:])  # write line
                    else:
                        featuresAnnotated = featuresAnnotated + 1
                        f.write(transSQ + values[2][index:] + "\n")  # write line

                elif semicoding and not values[0] == "." and not values[1] == ".":
                    bannot = False
                    # funcion match annot to its our CDSexons and match to CDSexonsSQ
                    bannot = checkFeatureInCDS(
                        dc_SQcoding,
                        dc_GFF3coding,
                        transSQ,
                        transGFF3,
                        int(values[0]),
                        int(values[1]),
                        strand,
                    )
                    if bannot:
                        index = values[2].find("\t")
                        if values[2].endswith("\n"):
                            featuresAnnotated = featuresAnnotated + 1
                            f.write(transSQ + values[2][index:])  # write line
                        else:
                            featuresAnnotated = featuresAnnotated + 1
                            f.write(transSQ + values[2][index:] + "\n")  # write line

                elif semicoding and values[0] == "." and values[1] == ".":
                    index = values[2].find("\t")
                    if values[2].endswith("\n"):
                        featuresAnnotated = featuresAnnotated + 1
                        f.write(transSQ + values[2][index:])  # write line
                    else:
                        featuresAnnotated = featuresAnnotated + 1
                        f.write(transSQ + values[2][index:] + "\n")  # write line

            #######################
            # TRANSCRIPT ANNOTATION#
            #######################

            if (
                not values[0] == "."
                and not values[1] == "."
                and text[-1].endswith("T\n")
            ):
                bannot = False
                bannot = checkFeatureInTranscript(
                    dc_SQexons,
                    dc_GFF3transExons,
                    transSQ,
                    transGFF3,
                    int(values[0]),
                    int(values[1]),
                    strand,
                )

                if bannot:
                    index = values[2].find("\t")
                    if values[2].endswith("\n"):
                        featuresAnnotated = featuresAnnotated + 1
                        f.write(transSQ + values[2][index:])  # write line
                    else:
                        featuresAnnotated = featuresAnnotated + 1
                        f.write(transSQ + values[2][index:] + "\n")  # write line
        transcriptsAnnotated = transcriptsAnnotated + 1
    f.close()

    logger.info(
        f"Annoted a total of {str(featuresAnnotated)} annotation features from reference GFF3 file."
    )
    perct = featuresAnnotated / totalAnotations * 100
    logger.info(
        f"Annoted a total of {perct:%.2f}% of the reference GFF3 file annotations."
    )


# UPDATE GFF3 - new columns information
# def addPosType(res, line, posType):
#     if line.endswith(";"):
#         res.write(line + " PosType=" + posType + "\n")
#     else:
#         res.write(line[:-1] + "; PosType=" + posType + "\n")

#f.groupby('seqname')[['start','end']].apply(lambda x: x.values.tolist()).to_dict()
def updateGTF(filename, filenameMod):
    logger = logging.getLogger("IsoAnnotLite_SQ1")
    # open new file
    res = dict()
    # open annotation file and process all data
    f = gtfparse.parse_gtf(filename)
        # process all entries - no header line in file
    try:
        assert len(f.columns) == 9
    except AssertionError:
        logging.exception(
            f"File {filename} has an incorrect number of columns.  It should have 9, but actually has {len(f.columns)}."
        )

    #for i, line in enumerate(tqdm(f.iterrows(), total=len(f))):
    def process_line(line: pd.Series) -> pd.Series:
        line.attribute = line.attribute.replace("; ",";").rstrip(";")
        
        if not line.attribute.split(";")[-1].startswith("PosType"):

            if line.source == "tappAS":
                if line.feature in ("transcript","gene","CDS"):
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=T"
                elif line.feature in ("genomic","G","exon", "G","splice_junction"):
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=G"
                elif line.feature == "protein":
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"
                else:
                    logger.info(line)
            elif line.source == "COILS":
                if line.feature == "COILED":
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature {str(line.feature)} in source {str(line.source)}, using P type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"
            elif line.source == "GeneOntology":
                if line.feature in ("C", "cellular_component", "F", "molecular_function","P", "biological_process","eco"):
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=N"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature {str(line.feature)} in source {str(line.source)}, using N type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=N"

            elif line.source == "MOBIDB_LITE":
                if line.feature == "DISORDER":
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature {str(line.feature)} in source {str(line.source)}, using P type to annotate."
                    )
                    
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"

            elif line.source == "NMD":
                if line.feature == "NMD":
                    
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=T"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)}, using T type to annotate."
                    )
                    
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=T"

            elif line.source in ("PAR-CLIP", "PAR-clip"):
                if line.feature in (
                    "RNA_binding",
                    "RNA_Binding_Protein",
                    "RBP_Binding",
                ) or line.feature.startswith("RNA_binding_"):
                    
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=T"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)}, using T type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=T"

            elif line.source == "PFAM":
                if line.feature == "DOMAIN":
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"
                elif line.feature in ("CLAN", "clan"):
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=N"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)}, using N type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=N"

            elif line.source == "Provean":
                if line.feature == "FunctionalImpact":
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=N"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)} using N type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=N"

            elif line.source in ("REACTOME", "Reactome"):
                if line.feature in ("PATHWAY", "pathway", "Pathway"):
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=N"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)} using N type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=N"

            elif line.source == "RepeatMasker":
                if line.feature == "repeat":
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=T"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)}, using T type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=T"

            elif line.source == "SIGNALP_EUK":
                if line.feature == "SIGNAL":
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)} using P type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"

            elif line.source == "TMHMM":
                if line.feature == "TRANSMEM":
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)} using P type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"

            elif line.source == "TranscriptAttributes":
                line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=T"

            elif line.source == "UTRsite":
                if line.feature in ("uORF","5UTRmotif","PAS","3UTRmotif"):
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=T"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)}, using T type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=T"

            elif line.source in (
                "UniProtKB/Swiss-Prot_Phosphosite",
                "Swissprot_Phosphosite",
            ):
                if line.feature in ("ACT_SITE", "BINDING", "PTM", "MOTIF", "MOTIF", "COILED", "TRANSMEM","COMPBIAS","INTRAMEM","NON_STD",):
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)} using P type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"

            elif line.source in ("cNLS_mapper", "NLS_mapper"):
                if line.feature == "MOTIF":
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)}; using P type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"

            elif line.source in ("miRWalk", "mirWalk"):
                if line.feature in ("miRNA", "miRNA_Binding"):
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=T"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)}; using T type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=T"

            elif line.source == "scanForMotifs":
                if line.feature == "PAS":
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=T"
                elif line.feature in ("3UTRmotif", "3'UTRmotif"):
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=T"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)}; using T type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=T"

            elif line.source == "MetaCyc":
                if line.feature == "pathway":
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=N"
                    
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)}; using N type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=N"

            elif line.source == "KEGG":
                if line.feature in ("pathway", "Pathway"):
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=N"
                    
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)}; using N type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=N"

            elif line.source == "SUPERFAMILY":
                if line.feature == "DOMAIN":
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)}; using P type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"

            elif line.source == "SMART":
                if line.feature == "DOMAIN":
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)}; using P type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"

            elif line.source == "TIGRFAM":
                if line.feature == "DOMAIN":
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)}; using P type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"

            elif line.source == "psRNATarget":
                if line.feature == "miRNA":
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=T"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)}; using T type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=T"

            elif line.source == "CORUM":
                if line.feature == "Complex":
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)}; using P type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=P"

            elif line.source == "Orthologues":
                if line.feature == "S.tuberosum":
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=N"
                elif line.feature in ("A.thaliana"):
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=N"
                else:
                    logger.info(
                        f"IsoAnnotLite can not identify the feature  {str(line.feature)} in source {str(line.source)}; using N type to annotate."
                    )
                    line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=N"

            else:
                logger.info(
                    f"IsoAnnotLite can not identify the source {str(line.source)}, in line: {line}; using N type to annotate."
                )
                line.attribute = line.attribute.replace("; ",";").rstrip(";") + ";PosType=N"

            # break
        return line
    
    tqdm.pandas()
    f.progress_apply(process_line, axis='columns')
    f.to_csv(
        path_or_buf=filenameMod,
        sep="\t",
        header=False,
        index=False,
        columns=[
            "seqname",
            "source",
            "feature",
            "start",
            "end",
            "score",
            "strand",
            "frame",
            "attribute",
        ],
    )


def readGFFandGetData(filenameMod):
    # open annotation file and process all data
    dcTrans = {}
    dcExon = {}
    dcTransFeatures = {}
    dcGenomic = {}
    dcSpliceJunctions = {}
    dcProt = {}
    dcProtFeatures = {}
    dcTranscriptAttributes = {}

    # dcTransID = {}

    with open(filenameMod, "r") as f:
        # process all entries - no header line in file
        for line in f:
            if len(line) == 0:
                break
            else:
                if line and line[0] != "#":
                    fields = line.split("\t")
                    if len(fields) == 9:

                        transcript = fields[0]
                        text = fields[8].split(" ")
                        # transcriptID = text[0]
                        # transcriptID = transcriptID[3:-1]

                        if fields[1] == "tappAS":
                            if fields[2] in ["transcript", "gene", "CDS"]:
                                if str(transcript) not in dcTrans:
                                    dcTrans[str(transcript)] = [line]
                                else:
                                    dcTrans[str(transcript)] = dcTrans[
                                        str(transcript)
                                    ] + [line]
                            elif fields[2] in ["exon"]:
                                if str(transcript) not in dcExon:
                                    dcExon[str(transcript)] = [line]
                                else:
                                    dcExon[str(transcript)] = dcExon[
                                        str(transcript)
                                    ] + [line]
                            elif fields[2] in ["genomic"]:
                                if str(transcript) not in dcGenomic:
                                    dcGenomic[str(transcript)] = [line]
                                else:
                                    dcGenomic[str(transcript)] = dcGenomic[
                                        str(transcript)
                                    ] + [line]
                            elif fields[2] in ["splice_junction"]:
                                if str(transcript) not in dcSpliceJunctions:
                                    dcSpliceJunctions[str(transcript)] = [line]
                                else:
                                    dcSpliceJunctions[
                                        str(transcript)
                                    ] = dcSpliceJunctions[str(transcript)] + [line]
                            elif fields[2] in ["protein"]:
                                if str(transcript) not in dcProt:
                                    dcProt[str(transcript)] = [line]
                                else:
                                    dcProt[str(transcript)] = dcProt[
                                        str(transcript)
                                    ] + [line]
                        # Transcript Information
                        elif fields[1] == "TranscriptAttributes":
                            if str(transcript) not in dcTranscriptAttributes:
                                dcTranscriptAttributes[str(transcript)] = [line]
                            else:
                                dcTranscriptAttributes[
                                    str(transcript)
                                ] = dcTranscriptAttributes[str(transcript)] + [line]
                        # Feature information
                        else:
                            if text[-1].endswith("T\n"):
                                if str(transcript) not in dcTransFeatures:
                                    dcTransFeatures[str(transcript)] = [line]
                                else:
                                    dcTransFeatures[str(transcript)] = dcTransFeatures[
                                        str(transcript)
                                    ] + [line]
                            elif (
                                text[-1].endswith("P\n")
                                or text[-1].endswith("G\n")
                                or text[-1].endswith("N\n")
                            ):
                                if str(transcript) not in dcProtFeatures:
                                    dcProtFeatures[str(transcript)] = [line]
                                else:
                                    dcProtFeatures[str(transcript)] = dcProtFeatures[
                                        str(transcript)
                                    ] + [line]

    return (
        dcTrans,
        dcExon,
        dcTransFeatures,
        dcGenomic,
        dcSpliceJunctions,
        dcProt,
        dcProtFeatures,
        dcTranscriptAttributes,
    )


def generateFinalGFF3(
    dcTrans,
    dcExon,
    dcTransFeatures,
    dcGenomic,
    dcSpliceJunctions,
    dcProt,
    dcProtFeatures,
    dcTranscriptAttributes,
    filename,
):
    # open new file
    with open(filename, "w") as res:
        for SQtrans in dcTrans:
            strand = dcTrans[SQtrans][0].split("\t")[
                6
            ]  # why are we doing this?  does someone not understand dictionaries or pd.Series?

            if SQtrans in dcTrans:
                for line in dcTrans[SQtrans]:
                    res.write(line)

            # tf = dcTransFeatures[]
            if SQtrans in dcTransFeatures:
                for line in dcTransFeatures[SQtrans]:
                    res.write(line)

            if SQtrans in dcGenomic:
                for line in dcGenomic[SQtrans]:
                    res.write(line)

            if SQtrans in dcExon:
                if strand == "+":
                    for line in dcExon[SQtrans]:
                        res.write(line)
                else:
                    for i in range(len(dcExon[SQtrans]) - 1, -1, -1):
                        res.write(dcExon[SQtrans][i])

            if SQtrans in dcSpliceJunctions:
                for line in dcSpliceJunctions[SQtrans]:
                    res.write(line)

            if SQtrans in dcProt:
                for line in dcProt[SQtrans]:
                    res.write(line)

            if SQtrans in dcProtFeatures:
                for line in dcProtFeatures[SQtrans]:
                    res.write(line)

            if SQtrans in dcTranscriptAttributes:
                for line in dcTranscriptAttributes[SQtrans]:
                    res.write(line)


def isoannot(
    corrected: str,
    classification: str,
    junctions: str,
    output: Optional[str] = None,
    gff3: Optional[str] = None,
) -> None:
    # Running functionality
    logger = logging.getLogger("IsoAnnotLite_SQ1")
    logger.info(f"Running IsoAnnot Lite {str(version)}...")

    t1 = time.time()
    # corrected = input("Enter your file name for \"corrected.gtf\" file from SQANTI 3 (with extension): ")
    gtf = corrected
    # classification = input("Enter your file name for \"classification.txt\" file from SQANTI 3 (with extension): ")
    # junctions = input("Enter your file name for \"junctions.txt\" file from SQANTI 3 (with extension): ")
    # GFF3 download from tappAS.org/downloads

    ########################
    # MAPPING SQANTI FILES #
    ########################

    if gff3:
        # File names
        if output:
            filename = output
        else:
            filename = "tappAS_annot_from_SQANTI3.gff3"

        filenameMod = f"{filename[:-5]}_mod{filename[-5:]}"

        #################
        # START PROCESS #
        #################
        logger.info("Reading SQANTI 3 Files and creating an auxiliar GFF...")

        # dc_SQexons = {trans : [[start,end], [start,end]...]}
        # dc_SQcoding = {trans : [CDSstart, CDSend, orf]}
        # dc_SQtransGene = {trans : [gene, category, transAssociated]}
        dc_SQexons, dc_SQcoding, dc_SQtransGene, dc_SQstrand = createGTFFromSqanti(
            file_exons=gtf,
            file_trans=classification,
            file_junct=junctions,
            filename=filename,
        )

        logger.info("Reading reference annotation file and creating data variables...")
        # dc_GFF3 = {trans : [[start,end,line], [start,end,line], ...]}
        # dc_GFF3exonsTrans = {start : [trans, trans, ...]}
        # dc_GFF3transExons = {trans : [[start,end], [start,end]...]}
        # dc_GFF3coding = {trans : [CDSstart, CDSend]}
        (
            dc_GFF3,
            dc_GFF3exonsTrans,
            dc_GFF3transExons,
            dc_GFF3coding,
            dc_GFF3strand,
        ) = readGFF(
            gff3
        )  # dc_GFF3exons is sorted

        logger.info("Transforming CDS local positions to genomic position...")
        # Transformar características a posiciones genómicas //revisar
        dc_SQcoding = transformCDStoGenomic(dc_SQcoding, dc_SQexons, dc_SQstrand)
        dc_GFF3coding = transformCDStoGenomic(
            dc_GFF3coding, dc_GFF3transExons, dc_GFF3strand
        )

        logger.info(
            "Transforming feature local positions to genomic position in GFF3..."
        )
        # Transformar características a posiciones genómicas //revisar
        dc_GFF3_Genomic = transformTransFeaturesToGenomic(
            dc_GFF3, dc_GFF3transExons, dc_GFF3coding, dc_GFF3strand
        )

        logger.info("Mapping transcript features betweeen GFFs...")
        mappingFeatures(
            dc_SQexons,
            dc_SQcoding,
            dc_SQtransGene,
            dc_GFF3exonsTrans,
            dc_GFF3transExons,
            dc_GFF3_Genomic,
            dc_GFF3coding,
            filename,
        )  # edit tappAS_annotation_from_Sqanti file

        logger.info("Adding extra information to GFF3 columns...")
        updateGTF(filename, filenameMod)

        logger.info("Reading GFF3 to sort it correctly...")
        (
            dcTrans,
            dcExon,
            dcTransFeatures,
            dcGenomic,
            dcSpliceJunctions,
            dcProt,
            dcProtFeatures,
            dcTranscriptAttributes,
        ) = readGFFandGetData(filenameMod)

        # Remove old files
        os.remove(filename)
        os.remove(filenameMod)

        dcTransFeatures = transformTransFeaturesToLocale(dcTransFeatures, dc_SQexons)

        logger.info("Generating final GFF3...")
        generateFinalGFF3(
            dcTrans,
            dcExon,
            dcTransFeatures,
            dcGenomic,
            dcSpliceJunctions,
            dcProt,
            dcProtFeatures,
            dcTranscriptAttributes,
            filename,
        )

        t2 = time.time()
        logger.info(f"Time used to generate new GFF3: {(t2 - t1):%.2f} seconds.")

        logger.info(f"Exportation complete. Your GFF3 result is: '{filename}'")

    #####################
    # JUST SQANTI FILES #
    #####################

    else:
        # File names
        if output:
            filename = output
        else:
            filename = "tappAS_annotation_from_SQANTI3.gff3"
        filenameMod = f"{filename[:-5]}_mod{filename[-5:]}"

        #################
        # START PROCESS #
        #################
        logger.info("Reading SQANTI 3 Files and creating an auxiliary GFF...")

        # dc_SQexons = {trans : [[start,end], [start,end]...]}
        # dc_SQcoding = {trans : [CDSstart, CDSend, orf]}
        # dc_SQtransGene = {trans : [gene, category, transAssociated]}
        dc_SQexons, dc_SQcoding, dc_SQtransGene, dc_SQstrand = createGTFFromSqanti(
            gtf, classification, junctions, filename
        )

        logger.info("Adding extra information to relative columns...")
        updateGTF(filename, filenameMod)

        logger.info("Reading GFF3 to sort it correctly...")
        (
            dcTrans,
            dcExon,
            dcTransFeatures,
            dcGenomic,
            dcSpliceJunctions,
            dcProt,
            dcProtFeatures,
            dcTranscriptAttributes,
        ) = readGFFandGetData(filenameMod)

        # Remove old files
        os.remove(filename)
        os.remove(filenameMod)

        logger.info("Generating final GFF3...")
        generateFinalGFF3(
            dcTrans,
            dcExon,
            dcTransFeatures,
            dcGenomic,
            dcSpliceJunctions,
            dcProt,
            dcProtFeatures,
            dcTranscriptAttributes,
            filename,
        )

        t2 = time.time()
        logger.info(f"Time used to generate new GFF3: {(t2-t1):.2f} seconds.")

        logger.info(f"Exportation complete. Your GFF3 result is: '{filename}'")


@click.command()
@click.argument(
    "corrected", type=str,
)
@click.argument(
    "classification", type=str,
)
@click.argument(
    "junctions", type=str,
)
@click.option(
    "--gff3",
    type=str,
    default=None,
    help="tappAS GFF3 file to map its annotation to your SQANTI 3 data (only if you use the same reference genome in SQANTI 3)",
)
@click.option(
    "--output", type=str, default=None, help="path and name to use for output gtf",
)
@click.option(
    "--loglevel",
    type=click.Choice(["info", "debug"]),
    default="info",
    help="Debug option - what level of logging should be displayed on the console?",
    show_default=True,
)
@click.version_option()
@click.help_option(show_default=True)
def main(
    corrected: str,
    classification: str,
    junctions: str,
    gff3: Optional[str] = None,
    output: Optional[str] = None,
    loglevel=str,
) -> None:
    """
    IsoAnnotLite: Transform SQANTI 3 output files to generate GFF3 to tappAS.

    \b
    Parameters:
    -----------
    corrected:
        *_corrected.gtf file from SQANTI 3 output
    classification:
        *_classification.txt file from SQANTI 3 output
    junctions:
        *_junctions.txt file from SQANTI 3 output
    """
    # for handler in logging.root.handlers[:]:
    #     logging.root.removeHandler(handler)
    logger = logging.getLogger("IsoAnnotLite_SQ1")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    fh = logging.FileHandler(filename="isoannotlite_sq1.log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    st = logging.StreamHandler()
    if loglevel == "debug":
        st.setLevel(logging.DEBUG)
    else:
        st.setLevel(logging.INFO)
    st.setFormatter(formatter)
    logger.addHandler(st)

    logger.info(
        f"writing log file to {os.path.join(os.getcwd(), 'isoannotlite_sq1.log')}"
    )
    # path and prefix for output files
    corrected = os.path.abspath(corrected)
    if not os.path.isfile(corrected):
        logging.error(f"'{corrected}' doesn't exist")
        sys.exit()

    classification = os.path.abspath(classification)
    if not os.path.isfile(classification):
        logging.error(f"'{classification}' doesn't exist")
        sys.exit()

    junctions = os.path.abspath(junctions)
    if not os.path.isfile(junctions):
        logging.error(f"'{junctions}' doesn't exist")
        sys.exit()

    if gff3:
        gff3 = os.path.abspath(gff3)
        if not os.path.isfile(gff3):
            logging.error(f"'{gff3}' doesn't exist")
            sys.exit()
    isoannot(
        corrected=corrected,
        classification=classification,
        junctions=junctions,
        gff3=gff3,
        output=output,
    )
    logging.shutdown()


if __name__ == "__main__":
    main()
