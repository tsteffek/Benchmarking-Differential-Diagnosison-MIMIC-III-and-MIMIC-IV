import pandas as pd
import re


def create_mp_data(admissions: pd.DataFrame, filtered_notes: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts information needed for the task from the MIMIC dataset. Namely "text" column from NOTEEVENTS.csv and
    "HOSPITAL_EXPIRE_FLAG" from ADMISSIONS.csv. Filters specific admission sections for often occuring signal words.
    Creates 70/10/20 split over patients for train/val/test sets.
    """

    # append HOSPITAL_EXPIRE_FLAG to notes
    notes_with_expire_flag = pd.merge(filtered_notes, admissions[['hospital_expire_flag', 'subject_id']], how='left', left_index=True, right_index=True)

    # drop all rows without hospital expire flag
    notes_with_expire_flag = notes_with_expire_flag.dropna(how='any', subset=['hospital_expire_flag'], axis=0)

    # filter out written out death indications
    notes_with_expire_flag = remove_mentions_of_patients_death(notes_with_expire_flag)

    return notes_with_expire_flag


def remove_mentions_of_patients_death(df: pd.DataFrame):
    """
    Some notes contain mentions of the patient's death such as 'patient deceased'. If these occur in the sections
    PHYSICAL EXAM and MEDICATION ON ADMISSION, we can simply remove the mentions, because the conditions are not
    further elaborated in these sections. However, if the mentions occur in any other section, such as CHIEF COMPLAINT,
    we want to remove the whole sample, because the patient's passing if usually closer described in the text and an
    outcome prediction does not make sense in these cases.
    """

    death_indication_in_special_sections = re.compile(
        r"((?:PHYSICAL EXAM|MEDICATION ON ADMISSION):[^\n\n]*?)((?:patient|pt)?\s+(?:had\s|has\s)?(?:expired|died|passed away|deceased))",
        flags=re.IGNORECASE)

    death_indication_in_all_other_sections = re.compile(
        r"(?:patient|pt)\s+(?:had\s|has\s)?(?:expired|died|passed away|deceased)", flags=re.IGNORECASE)

    # first remove mentions in sections PHYSICAL EXAM and MEDICATION ON ADMISSION
    df['text'] = df['text'].replace(death_indication_in_special_sections, r"\1", regex=True)

    # if mentions can be found in any other section, remove whole sample
    df = df[~df['text'].str.contains(death_indication_in_all_other_sections)]

    # remove other samples with obvious death indications
    df = df[~df['text'].str.contains("he expired", flags=re.IGNORECASE)]  # does also match 'she expired'
    df = df[~df['text'].str.contains("pronounced expired", flags=re.IGNORECASE)]
    df = df[~df['text'].str.contains("time of death", flags=re.IGNORECASE)]

    return df
