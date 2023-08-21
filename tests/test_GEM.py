from pathlib import Path

import pandas as pd
import pandas.testing
import pytest

from utils.gem import ICDType, GEM_DTYPES, GEMTransform, ICD10_COL


class TestGEM:
    @pytest.fixture
    def gem_dir(self) -> Path:
        return Path(__file__).parent / 'resources'

    @pytest.fixture
    def icd_type_in_resources(self):
        return ICDType.DIAGNOSES

    @pytest.fixture
    def gem_icd10toicd9(self, gem_dir: Path) -> pd.DataFrame:
        return pd.read_csv(gem_dir / 'icd10cmtoicd9gem.csv', dtype=GEM_DTYPES)

    @pytest.fixture
    def direct_mappings(self, gem_dir: Path) -> pd.DataFrame:
        return pd.read_csv(gem_dir / 'icd10cmtoicd9_direct_mappings.csv', dtype=GEM_DTYPES | {'simplified': bool}, index_col=ICD10_COL)

    def test_calculates_correct_mappings(self, gem_icd10toicd9, icd_type_in_resources, direct_mappings):
        transform = GEMTransform(gem_icd10toicd9, icd_type_in_resources, 3)
        sorting_columns = ['icd10cm', 'scenario', 'choice_list']
        pandas.testing.assert_frame_equal(
            transform.direct_mappings.sort_values(sorting_columns),
            direct_mappings.sort_values(sorting_columns)
        )

    def test_calculates_correct_mappings_from_file(self, gem_dir, icd_type_in_resources, direct_mappings):
        transform = GEMTransform.from_gem_file(gem_dir, icd_type_in_resources, 3)
        sorting_columns = ['icd10cm', 'scenario', 'choice_list']
        pandas.testing.assert_frame_equal(
            transform.direct_mappings.sort_values(sorting_columns),
            direct_mappings.sort_values(sorting_columns)
        )
