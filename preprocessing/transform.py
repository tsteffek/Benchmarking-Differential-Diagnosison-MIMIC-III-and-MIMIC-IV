import click
import pandas as pd
from pathlib import Path

from tasks import create_dia_data, create_pro_data, create_mp_data, create_los_data
from utils.mimic_utils import filter_notes
from utils.separation_algorithms import get_matching_admissions, TIME_COLUMNS, split_by_patients, get_epy_admissions


@click.command()
@click.option('-d', '--data-dir', default=Path('./../mimic4-pg/data/'), help='directory of mimic4',
              type=click.Path(exists=True, file_okay=False, path_type=Path, executable=False))
@click.option('-o', '--output-dir', default=Path('./output/'), help='output directory',
              type=click.Path(exists=True, file_okay=False, path_type=Path, executable=False))
@click.option('-g', '--gem-dir', default=Path('./../mimic4-pg/data/gem/'), help='directory of gem data',
              type=click.Path(exists=True, file_okay=False, path_type=Path, executable=False))
@click.option('-t', '--tasks', type=click.Choice(['dia', 'pro', 'mp', 'los']), default=['dia', 'pro', 'mp', 'los'], multiple=True, help='tasks to prepare data for')
@click.option('-s', '--separation-algo', type=click.Choice(['matching', 'epy']), default=['matching', 'epy'], multiple=True, help='how to separate MIMIC-III data')
@click.option('-l', '--labels-dir', default=Path('./output/'), help='Filter possible labels by "ALL_3_DIGIT_DIA_CODES.txt" or "ALL_3_DIGIT_PRO_CODES.txt" in this directory',
              type=click.Path(exists=True, file_okay=False, path_type=Path, executable=False))
def main(data_dir: Path, gem_dir: Path, output_dir: Path, tasks: list[str], separation_algo: list[str], labels_dir: Path):
    hosp_dir = data_dir / 'mimic-iv-2.2' / 'hosp'
    admissions = pd.read_csv(hosp_dir / 'admissions.csv.gz', index_col='hadm_id', parse_dates=TIME_COLUMNS)

    icu_stays = pd.read_csv(data_dir / 'mimic-iv-2.2' / 'icu' / 'icustays.csv.gz', usecols=('subject_id', 'hadm_id', 'los',))
    # drop all duplicated admissions as they're hard to map to a letter
    icu_stays = icu_stays[~icu_stays.hadm_id.duplicated(keep=False)].set_index('hadm_id')

    dia_codes = pd.read_csv(hosp_dir / 'diagnoses_icd.csv.gz', dtype={'icd_version': int, 'subject_id': int, 'icd_code': str}, usecols=('icd_version', 'subject_id', 'icd_code', 'hadm_id'))
    pro_codes = pd.read_csv(hosp_dir / 'procedures_icd.csv.gz', dtype={'icd_version': int, 'subject_id': int, 'icd_code': str}, usecols=('icd_version', 'subject_id', 'icd_code', 'hadm_id'))

    if 'matching' in separation_algo:
        matching = get_matching_admissions(data_dir, admissions, dia_codes, pro_codes)
        split_matching = split_by_patients(data_dir, matching)
        separated = matching

    if 'epy' in separation_algo:
        patients = pd.read_csv(hosp_dir / 'patients.csv.gz', index_col='subject_id', usecols=('subject_id', 'anchor_year', 'anchor_year_group'))
        icu_admissions = pd.merge(icu_stays, admissions, on=['hadm_id', 'subject_id'])
        separated = get_epy_admissions(patients, icu_admissions)

        if 'matching' in separation_algo:
            separated = pd.merge(separated, matching, how='outer', on='hadm_id')

    subsets = {
        'hosp': admissions.loc[admissions.index.difference(separated.index).difference(icu_stays.index)].index,
        'icu': icu_stays.index,
        'iv_icu': icu_stays.index.difference(separated.index)
    }
    subsets |= {
        'icu_9': subsets['iv_icu'].difference(pro_codes[pro_codes.icd_version == 9].hadm_id).difference(dia_codes[dia_codes.icd_version == 9].hadm_id),
        'icu_10': subsets['iv_icu'].difference(pro_codes[pro_codes.icd_version == 10].hadm_id).difference(dia_codes[dia_codes.icd_version == 10].hadm_id)
    }
    if 'matching' in separation_algo:
        subsets |= {
            'iii_test': split_matching['test'].index if 'test' in split_matching else None,
            'matching': matching.index
        }

    notes = pd.read_csv(data_dir / 'mimic-iv-note-deidentified-free-text-clinical-notes-2.2' / 'note' / 'discharge.csv.gz', index_col='hadm_id')
    filtered_notes = filter_notes(notes, admission_text_only=True)

    if 'dia' in tasks:
        print('Creating dia dataset...')
        save_results('dia', output_dir, subsets,
                     create_dia_data(gem_dir, labels_dir, dia_codes, filtered_notes))
    if 'pro' in tasks:
        print('Creating pro dataset...')
        save_results('pro', output_dir, subsets,
                     create_pro_data(gem_dir, labels_dir, pro_codes, filtered_notes))
    if 'mp' in tasks:
        print('Creating mp dataset...')
        save_results('mp', output_dir, subsets,
                     create_mp_data(admissions, filtered_notes))
    if 'los' in tasks:
        print('Creating los dataset...')
        save_results('los', output_dir, subsets,
                     create_los_data(admissions, filtered_notes, icu_stays))


def save_results(task: str, output_dir: Path, subsets: dict[str, pd.Series], labeled_admissions_notes: pd.DataFrame):
    labeled_admissions_notes.to_csv(output_dir / f'{task}.csv', index=True)
    for subset, subset_admissions in subsets.items():
        is_subset = labeled_admissions_notes.index.isin(subset_admissions)
        labeled_admissions_notes[is_subset].to_csv(output_dir / f'{task}_{subset}.csv', index=True)


if __name__ == '__main__':
    main()
