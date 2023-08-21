import pandas as pd


def create_los_data(admissions: pd.DataFrame, filtered_notes: pd.DataFrame, icu_admissions: pd.DataFrame) -> pd.DataFrame:
    """
     Extracts information needed for the task from the MIMIC dataset. Namely 'TEXT' column from NOTEEVENTS.csv and
     'admittime' and 'dischtime' from ADMISSIONS.csv.
     Creates 70/10/20 split over patients for train/val/test sets.
    """

    # Calculating the Length of Stay in days per admission
    admissions['admittime'] = pd.to_datetime(admissions['admittime'])
    admissions['dischtime'] = pd.to_datetime(admissions['dischtime'])

    admissions['los_days'] = round(
        (admissions['dischtime'] - admissions['admittime']).dt.total_seconds() / (24 * 60 * 60), 1)

    admissions['los_iv'] = admissions['los_days'].copy()
    admissions.loc[icu_admissions.index, 'los_iv'] = icu_admissions.los

    # Creation of Label
    '''
        <= 3: 0
        > 3 & <= 7: 1
        > 7 & <= 14: 2
        >14: 3
    '''
    for source_col, target_col in zip(['los_days', 'los_iv'], ['los_label', 'los_label_iv']):
        admissions.loc[admissions[source_col] <= 3, target_col] = 0
        admissions.loc[(admissions[source_col] > 3) & (
                admissions[source_col] <= 7), target_col] = 1
        admissions.loc[(admissions[source_col] > 7) & (
                admissions[source_col] <= 14), target_col] = 2
        admissions.loc[(admissions[source_col] > 14), target_col] = 3
        admissions[target_col] = admissions[target_col].astype(int)

    # Keeping the required variables
    admissions = admissions[['subject_id', 'los_label', 'los_label_iv', 'hospital_expire_flag']]

    # Merging Mimic Notes data with Admissions data
    notes_adm_df = pd.merge(filtered_notes, admissions, left_index=True, right_index=True)

    # Removing records where the patient died within a given hospitalization
    notes_adm_df = notes_adm_df[notes_adm_df['hospital_expire_flag'] == 0]
    return notes_adm_df[['subject_id', 'text', 'los_label', 'los_label_iv']]
