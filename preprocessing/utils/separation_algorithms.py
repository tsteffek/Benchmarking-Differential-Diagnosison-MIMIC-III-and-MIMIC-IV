from pathlib import Path

import pandas as pd

TIME_COLUMNS = ['admittime', 'dischtime']


def get_epy_admissions(patients: pd.DataFrame, icu_admissions: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    year_diff = (patients['anchor_year'] - patients['anchor_year_group'].str[:4].astype('int')).rename('year_diff')
    adm_with_year = pd.merge(icu_admissions.reset_index(), year_diff, on='subject_id')
    adm_with_year['earliest_possible_dischyear'] = adm_with_year.dischtime.dt.year - adm_with_year.year_diff
    pre2012_adm = adm_with_year[adm_with_year['earliest_possible_dischyear'] <= 2012].drop_duplicates('hadm_id')
    return pre2012_adm.set_index('hadm_id')


def get_matching_admissions(data_dir: Path, admissions: pd.DataFrame, dia_codes: pd.DataFrame, pro_codes: pd.DataFrame):
    iii_adm = load_mimic_iii_admissions_with_icd_codes(data_dir)
    admissions = add_required_columns(admissions, dia_codes, pro_codes)
    admissions_9 = admissions[(admissions.dia_version != 10) & (admissions.pro_version != 10)]

    matching = pd.merge(admissions_9.reset_index(), iii_adm, on=moments_and_intervals(*TIME_COLUMNS), suffixes=('', '_iii')).set_index('hadm_id')
    matching = matching[((matching.pro == matching.pro_iii) & (matching.dia == matching.dia_iii))]

    return matching


def load_mimic_iii_admissions_with_icd_codes(data_dir: Path):
    mimiciii_dir = data_dir / 'mimiciii'

    adm = pd.read_csv(mimiciii_dir / 'ADMISSIONS.csv', parse_dates=list(map(str.upper, TIME_COLUMNS)))
    dia = pd.read_csv(mimiciii_dir / 'DIAGNOSES_ICD.csv', dtype={'ICD9_CODE': str}, usecols=['HADM_ID', 'SUBJECT_ID', 'ICD9_CODE']).rename({'ICD9_CODE': 'icd_code'}, axis=1)
    pro = pd.read_csv(mimiciii_dir / 'PROCEDURES_ICD.csv', dtype={'ICD9_CODE': str}, usecols=['HADM_ID', 'SUBJECT_ID', 'ICD9_CODE']).rename({'ICD9_CODE': 'icd_code'}, axis=1)

    for df in [adm, dia, pro]:
        df.rename(str.lower, axis=1, inplace=True)

    return add_required_columns(adm, dia, pro)


def add_required_columns(admissions: pd.DataFrame, dia_codes: pd.DataFrame, pro_codes: pd.DataFrame):
    admissions = add_codes_to_adm(admissions, dia_codes, 'dia')
    admissions = add_codes_to_adm(admissions, pro_codes, 'pro')
    times_to_moment(admissions, *TIME_COLUMNS)
    return admissions


def add_codes_to_adm(admissions: pd.DataFrame, codes: pd.DataFrame, code_type: str):
    if 'icd_version' in codes.columns:
        combined_codes = codes \
            .dropna() \
            .groupby(['hadm_id', 'subject_id', 'icd_version']) \
            .agg(set) \
            .reset_index('icd_version') \
            .rename({'icd_version': code_type + '_version', 'icd_code': code_type}, axis=1)
    else:
        combined_codes = codes \
            .dropna() \
            .groupby(['hadm_id', 'subject_id']) \
            .agg(set) \
            .rename({'icd_code': code_type}, axis=1)

    adm_with_codes = pd.merge(admissions, combined_codes, how='left', on=['hadm_id', 'subject_id'])
    nans = adm_with_codes[code_type].isna()
    adm_with_codes.loc[nans, code_type] = adm_with_codes[code_type][nans].apply(lambda x: set())

    return adm_with_codes


def moments_and_intervals(*times: str):
    return ([t.replace('time', 'moment') for t in times]
            + [t.replace('time', 'interval') for t in times if t != 'admittime'])


def times_to_moment(df: pd.DataFrame, *times: str):
    for t in times:
        df[t.replace('time', 'moment')] = df[t].dt.time
        if t != 'admittime':
            df[t.replace('time', 'interval')] = (df[t] - df['admittime']).dt.total_seconds()


def split_by_patients(data_dir: Path, admissions):
    data_splits = {"train": pd.read_csv(data_dir / 'splits' / 'mimic_train.csv'),
                   "val": pd.read_csv(data_dir / 'splits' / 'mimic_val.csv'),
                   "test": pd.read_csv(data_dir / 'splits' / 'mimic_test.csv')}

    return {splitname: admissions[admissions.subject_id_iii.isin(split.SUBJECT_ID)].sample(frac=1) for splitname, split in data_splits.items()}
