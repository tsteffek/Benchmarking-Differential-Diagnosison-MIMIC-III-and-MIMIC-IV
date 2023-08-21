from pathlib import Path

from enum import StrEnum

import pandas as pd
from tabulate import tabulate


class ICDType(StrEnum):
    PROCEDURES = 'pcs'
    DIAGNOSES = 'cm'

    @classmethod
    def of(cls, name: str):
        lower = name.lower()
        if lower in ['diagnoses', 'cm']:
            return cls.DIAGNOSES
        elif lower in ['procedures', 'pcs']:
            return cls.PROCEDURES
        else:
            raise ValueError('Unknown ICDType.')


ICD10_COL: str = 'icd10cm'
ICD9_COL: str = 'icd9cm'
GEM_DTYPES = {ICD10_COL: 'string', ICD9_COL: 'string', 'flags': 'string', 'approximate': bool, 'no_map': bool,
              'combination': bool, 'scenario': 'int8', 'choice_list': 'int8'}


def simplify_codes(df: pd.DataFrame, icd_col: str, digits: int) -> pd.Series:
    if '10' in icd_col:
        return df[icd_col].str.slice(0, digits)
    else:
        supplement_codes = df[icd_col].str.startswith(('E', 'V'))
        return pd.concat((
            df[icd_col][supplement_codes].str.slice(0, digits + 1),
            df[icd_col][~supplement_codes].str.slice(0, digits)
        ))


class GEMTransform:

    def __init__(self, icd10toicd9: pd.DataFrame, icd_type: ICDType, simplify: int = None):
        self.icd_type = icd_type
        icd10toicd9.set_index(ICD10_COL, inplace=True)
        icd10toicd9['simplified'] = False

        self.direct_mappings, remaining_mappings = self._extract_direct_mappings(icd10toicd9)

        if simplify is not None:
            simplified_direct_mappings, simplified_remaining_mappings = self._extract_direct_mappings(self.simplify_mappings(remaining_mappings, simplify))
            self.direct_mappings = pd.concat([self.direct_mappings, simplified_direct_mappings])

        self.print_metrics(icd10toicd9)

    def print_metrics(self, icd10toicd9):
        print('\n' + tabulate([
            ['type', 'mapped total', 'mapped simplified', 'mapped detail', 'total'],
            [
                self.icd_type,
                self.direct_mappings.index.nunique(),
                self.direct_mappings.index[self.direct_mappings['simplified']].nunique(),
                self.direct_mappings.index[~self.direct_mappings['simplified']].nunique(),
                icd10toicd9.index.nunique()
            ],
        ], headers='firstrow', tablefmt='github'))

    @classmethod
    def from_gem_file(cls, gem_dir: Path, icd_type: ICDType, simplify: int = None):
        return cls(pd.read_csv(gem_dir / f'icd10{icd_type}toicd9gem.csv', dtype=GEM_DTYPES), icd_type, simplify)

    @staticmethod
    def _extract_direct_mappings(icd10toicd9: pd.DataFrame):
        mappings = icd10toicd9[~icd10toicd9['no_map']]

        single_scenarios = mappings.loc[mappings.groupby(ICD10_COL).scenario.nunique() == 1]

        options_per_choice_list = single_scenarios.groupby([ICD10_COL, 'choice_list']).size()
        no_choice_single_scenario = single_scenarios.loc[options_per_choice_list.groupby(ICD10_COL).max() == 1]

        return no_choice_single_scenario, icd10toicd9.drop(no_choice_single_scenario.index)

    @staticmethod
    def simplify_mappings(icd10toicd9: pd.DataFrame, digits: int = 3, source_col: str = ICD10_COL, target_col: str = ICD9_COL):
        reindexed_df = icd10toicd9.reset_index()
        reindexed_df[target_col] = simplify_codes(reindexed_df, target_col, digits)
        remove_duplicated_1to1 = reindexed_df.drop_duplicates([source_col, target_col, 'scenario']).copy()
        remove_duplicated_1to1.loc[:, 'simplified'] = True
        return (GEMTransform._remove_duplicates_of_groups(remove_duplicated_1to1, source_col, target_col)
                .set_index(source_col))

    @staticmethod
    def _remove_duplicates_of_groups(df: pd.DataFrame, source_col: str, target_col: str):
        if len(df) == 0:
            return df
        groupby = [source_col, 'scenario']
        filtered = (df
                    .groupby([source_col, 'scenario', 'choice_list'])[target_col]
                    .agg(set).astype(str)
                    .reset_index()
                    .drop_duplicates([source_col, target_col])
                    .set_index(groupby))
        indexed_df = df.set_index(groupby)
        return indexed_df.drop(indexed_df.index.difference(filtered.index)).reset_index()

    def transform_to_icd9(self, df: pd.DataFrame, icd10_col: str = 'icd_code'):
        merged = (
            pd.merge(
                df,
                self.direct_mappings[[ICD9_COL, 'simplified']],
                how='left',
                left_on=icd10_col,
                right_index=True,
            )
            .rename(columns={ICD9_COL: 'icd9'})
            .reset_index(drop=True))

        merged['simplified'].fillna(False, inplace=True)

        return merged
