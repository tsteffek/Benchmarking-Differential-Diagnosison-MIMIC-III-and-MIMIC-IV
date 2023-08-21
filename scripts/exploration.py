import pandas as pd

dtypes = dict(icd10cm='string', icd9cm='string', flags='string', approximate=bool, no_map=bool, combination=bool,
              scenario='int8', choice_list='int8')

icd10cmtoicd9gem = pd.read_csv('../data/icd10cmtoicd9gem.csv', dtype=dtypes)
icd10pcstoicd9gem = pd.read_csv('../data/icd10pcstoicd9gem.csv', dtype=dtypes)
icd10pcstoicd9gem.head()

def analyze(df: pd.DataFrame, main_col: str):
    codes_without_multiple_mappings = df.drop_duplicates(main_col, keep=False)

    codes_with_multiple_mappings = df[df.duplicated(main_col, keep=False)]
    distinct_codes_with_multiple_mappings = codes_with_multiple_mappings.drop_duplicates(main_col)

    combination = codes_with_multiple_mappings[codes_with_multiple_mappings['combination']]
    alternatives = codes_with_multiple_mappings[~codes_with_multiple_mappings['combination']]

    distinct_combination = codes_with_multiple_mappings[codes_with_multiple_mappings['combination']].drop_duplicates(main_col)
    distinct_alternatives = codes_with_multiple_mappings[~codes_with_multiple_mappings['combination']].drop_duplicates(main_col)

    c_a = pd.concat([distinct_combination, distinct_alternatives]).duplicated(main_col)
    print(len(c_a))

    results = [{
        'total': len(df)
    }, {
        'distinct': len(df.drop_duplicates(main_col)),
        'duplicates': sum(df.duplicated(main_col))
    }, {
        'no_map': sum(df['no_map']),
        '1to1': sum(~codes_without_multiple_mappings['no_map']),
        'multiple_mappings_distinct': len(distinct_codes_with_multiple_mappings),
        'multiple_mappings_duplicates': len(codes_with_multiple_mappings) - len(distinct_codes_with_multiple_mappings),
    }, {
        'no_map': sum(df['no_map']),
        '1to1_direct': sum(~codes_without_multiple_mappings['approximate']),
        '1to1_approximate': sum(codes_without_multiple_mappings['approximate'] & ~codes_without_multiple_mappings['no_map']),
        'combination_distinct': len(distinct_combination),
        'combination_duplicates': sum(codes_with_multiple_mappings['combination']) - len(distinct_combination),
        'alternatives_distinct': len(distinct_alternatives),
        'alternatives_duplicates': sum(~codes_with_multiple_mappings['combination']) - len(distinct_alternatives),
        'combination_and_alternative_distinct': sum(pd.concat([distinct_combination, distinct_alternatives]).duplicated(main_col)),
        'combination_and_alternative_duplicates': sum(pd.concat([distinct_combination, distinct_alternatives]).duplicated(main_col, keep=False))
    }]
    return results, [sum(result.values()) for result in results]


cm_results = analyze(icd10cmtoicd9gem, 'icd10cm')
cm_results