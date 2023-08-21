import argparse
import re

import pandas as pd
import os
import csv


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mimic_dir', required=True)
    parser.add_argument('--save_dir', required=True)
    parser.add_argument('--admission_only', default=False)
    parser.add_argument('--seed', default=123, type=int)

    return parser.parse_args()


def filter_notes(notes_df: pd.DataFrame, admission_text_only=False) -> pd.DataFrame:
    """
    Keep only Discharge Summaries and filter out Newborn admissions. Replace duplicates and join reports with
    their addendums. If admission_text_only is True, filter all sections that are not known at admission time.
    """
    # strip texts from leading and trailing and white spaces
    notes_df["text"] = notes_df["text"].str.strip()

    # remove entries without subject id or text
    notes_df = notes_df.dropna(subset=["subject_id", "text"])

    if admission_text_only:
        # reduce text to admission-only text
        notes_df = filter_admission_text(notes_df)

    return notes_df


def filter_admission_text(notes_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter text information by section and only keep sections that are known on admission time.
    """
    admission_sections = {
        "chief_complaint": "chief complaint:",
        "present_illness": "present illness:",
        "medical_history": "medical history:",
        "medication_adm": "medications on admission:",
        "allergies": "allergies:",
        "physical_exam": "physical exam:",
        "family_history": "family history:",
        "social_history": "social history:"
    }

    # replace linebreak indicators
    # notes_df['text'] = notes_df['text'].str.replace("\n", "\\n")
    notes_df['text'] = notes_df['text'].str.replace("___\nFamily History:", "___\n\nFamily History:", flags=re.IGNORECASE)

    # extract each section by regex
    for key, section in admission_sections.items():
        notes_df[key] = notes_df.text.str.extract('{}([\\s\\S]+?)\n\\s*?\n[^(\\\\|\\d|\\.)]+?:'.format(section), flags=re.IGNORECASE)

        notes_df[key] = notes_df[key].str.replace('\n', ' ')
        notes_df[key] = notes_df[key].str.strip()
        notes_df[key] = notes_df[key].fillna("")
        notes_df.loc[notes_df[key].str.startswith("[]"), key] = ""

    # filter notes with missing main information
    notes_df = notes_df[(notes_df.chief_complaint != "") | (notes_df.present_illness != "") |
                        (notes_df.medical_history != "")]

    # add section headers and combine into TEXT_ADMISSION
    notes_df = notes_df.assign(text="CHIEF COMPLAINT: " + notes_df.chief_complaint.astype(str)
                                    + '\n\n' +
                                    "PRESENT ILLNESS: " + notes_df.present_illness.astype(str)
                                    + '\n\n' +
                                    "MEDICAL HISTORY: " + notes_df.medical_history.astype(str)
                                    + '\n\n' +
                                    "MEDICATION ON ADMISSION: " + notes_df.medication_adm.astype(str)
                                    + '\n\n' +
                                    "ALLERGIES: " + notes_df.allergies.astype(str)
                                    + '\n\n' +
                                    "PHYSICAL EXAM: " + notes_df.physical_exam.astype(str)
                                    + '\n\n' +
                                    "FAMILY HISTORY: " + notes_df.family_history.astype(str)
                                    + '\n\n' +
                                    "SOCIAL HISTORY: " + notes_df.social_history.astype(str))['text']

    return notes_df


def save_mimic_split_patient_wise(df, label_column, save_dir, task_name, seed, column_list=None):
    """
    Splits a MIMIC dataframe into 70/10/20 train, val, test with no patient occuring in more than one set.
    Uses ROW_ID as ID column and save to save_path.
    """
    if column_list is None:
        column_list = ["ID", "TEXT", label_column]

    # Load prebuilt MIMIC patient splits
    data_split = {"train": pd.read_csv("tasks/mimic_train.csv"),
                  "val": pd.read_csv("tasks/mimic_val.csv"),
                  "test": pd.read_csv("tasks/mimic_test.csv")}

    # Use row id as general id and cast to int
    df = df.rename(columns={'HADM_ID': 'ID'})
    df.ID = df.ID.astype(int)

    # Create path to task data
    os.makedirs(save_dir, exist_ok=True)

    # Save splits to data folder
    for split_name in ["train", "val", "test"]:
        split_set = df[df.SUBJECT_ID.isin(data_split[split_name].SUBJECT_ID)].sample(frac=1,
                                                                                     random_state=seed)[column_list]

        # lower case column names
        split_set.columns = map(str.lower, split_set.columns)

        split_set.to_csv(os.path.join(save_dir, "{}_{}.csv".format(task_name, split_name)),
                         index=False,
                         quoting=csv.QUOTE_ALL)
