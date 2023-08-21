import time

import pandas as pd
from pathlib import Path
from tabulate import tabulate

from utils.gem import ICDType, GEMTransform, simplify_codes


def create_dia_data(gem_dir: Path, labels_dir: Path, codes: pd.DataFrame, filtered_notes: pd.DataFrame) -> pd.DataFrame:
    return _create_dia_pro_data(filtered_notes=filtered_notes,
                                codes=codes,
                                gem_dir=gem_dir,
                                labels_dir=labels_dir / 'ALL_3_DIGIT_DIA_CODES.txt',
                                icd_type=ICDType.DIAGNOSES)


def create_pro_data(gem_dir: Path, labels_dir: Path, codes: pd.DataFrame, filtered_notes: pd.DataFrame) -> pd.DataFrame:
    return _create_dia_pro_data(filtered_notes=filtered_notes,
                                codes=codes,
                                gem_dir=gem_dir,
                                labels_dir=labels_dir / 'ALL_3_DIGIT_PRO_CODES.txt',
                                icd_type=ICDType.PROCEDURES)


def _create_dia_pro_data(filtered_notes: pd.DataFrame, codes: pd.DataFrame, gem_dir: Path, labels_dir: Path, icd_type: ICDType) -> pd.DataFrame:
    codes = transform_icd10_to_3_digit_icd9(gem_dir, icd_type, codes)
    codes = remove_model_unknown_labels(codes, labels_dir)

    labeled_admissions = extract_admissions_with_labels(codes)
    # print('\n' + tabulate(compute_admission_metrics(labeled_admissions, noncontaminated_subjects, icd_type), headers='firstrow', tablefmt='github'))

    labeled_admissions = labeled_admissions[~labeled_admissions.has_nan]
    labeled_admissions_notes = pd.merge(labeled_admissions, filtered_notes, left_index=True, right_index=True)

    return labeled_admissions_notes


def transform_icd10_to_3_digit_icd9(gem_dir: Path, icd_type: ICDType, codes: pd.DataFrame) -> pd.DataFrame:
    gem_transform = GEMTransform.from_gem_file(gem_dir, icd_type, 3)
    codes = gem_transform.transform_to_icd9(codes)
    codes.loc[codes.icd_version == 9, 'icd9'] = codes.icd_code[codes.icd_version == 9]
    codes.loc[:, 'icd9'] = simplify_codes(codes, 'icd9', 3)
    return codes


def remove_model_unknown_labels(codes: pd.DataFrame, labels_dir: Path) -> pd.DataFrame:
    prev_labels = len(codes)
    allowed_labels = load_labels(labels_dir)
    codes = pd.merge(codes, allowed_labels, on='icd9')
    print(f'{prev_labels - len(codes)}/{prev_labels} removed by merging with Label-list at {labels_dir}')
    return codes


def extract_admissions_with_labels(df: pd.DataFrame, col: str = 'icd9'):
    gb = df.drop_duplicates(['subject_id', 'hadm_id', col]).groupby(['subject_id', 'hadm_id'], dropna=False)
    admissions = gb[col].agg([lambda x: x.isna().any(), lambda x: x.str.cat(sep=',')]) \
        .rename(columns={'<lambda_0>': 'has_nan', '<lambda_1>': 'labels'})
    admissions['is_simplified'] = (~admissions.has_nan & gb['simplified'].any())
    admissions['is_mapped'] = ~(admissions.has_nan | admissions.is_simplified)

    return admissions.reset_index(level=0, names='subject_id')


def label_admission(admission: pd.DataFrame, icd_col: str):
    admission = admission.drop_duplicates(icd_col)
    has_nan = admission[icd_col].isna().any()
    return pd.Series((has_nan, not has_nan and admission['simplified'].any(), admission[icd_col].str.cat(sep=',')))


def load_labels(labels_dir: Path) -> pd.Series:
    with open(labels_dir) as f:
        labels = f.readline()
    return pd.Series(labels.split(' '), name='icd9')


def compute_admission_metrics(admissions: pd.DataFrame, non_contaminated_admissions: pd.Series, data_type: str):
    is_non_contaminated = admissions.index.isin(non_contaminated_admissions)
    contaminated = admissions[~is_non_contaminated]
    non_contaminated = admissions[is_non_contaminated]

    nc_mapped, nc_simple_mapped, nc_with_nan = _compute_admission_metrics(non_contaminated)
    c_mapped, c_simple_mapped, c_with_nan = _compute_admission_metrics(contaminated)
    return [[data_type, 'Completely Mapped', 'Contaminated Completely Mapped', 'Simplified', 'Contaminated Simplified', 'With at least 1 NaN', 'Contaminated With at least 1 NaN'],
            ['Admissions', nc_mapped, c_mapped, nc_simple_mapped, c_simple_mapped, nc_with_nan, c_with_nan],
            ['Total', nc_mapped + c_mapped, None, nc_simple_mapped + c_simple_mapped, None, nc_with_nan + c_with_nan, None]
            ]


def _compute_admission_metrics(df: pd.DataFrame):
    return df.is_mapped.sum(), df.is_simplified.sum(), df.has_nan.sum()
