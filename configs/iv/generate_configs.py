from pathlib import Path

import jinja2

if __name__ == '__main__':
    tasks = {
        'dia_3': {
            'experiment': 'dia_3_iv',
            'multilabel': 'true',
            'metric': 'binary_classification_metrics',
            'test_file': 'dia',
            'label_list': 'ALL_3_DIGIT_DIA_CODES.txt',
            'label': 'labels'
        },
        'pro_3': {
            'experiment': 'pro_3_iv',
            'multilabel': 'true',
            'metric': 'binary_classification_metrics',
            'test_file': 'pro',
            'label_list': 'ALL_3_DIGIT_PRO_CODES.txt',
            'label': 'labels'
        },
        'dia_plus': {
            'experiment': 'dia_plus_iv',
            'multilabel': 'true',
            'metric': 'binary_classification_metrics',
            'test_file': 'dia',
            'label_list': 'ALL_DIAGNOSES_PLUS_CODES.txt',
            'label': 'labels'
        },
        'pro_plus': {
            'experiment': 'pro_plus_iv',
            'multilabel': 'true',
            'metric': 'binary_classification_metrics',
            'test_file': 'pro',
            'label_list': 'ALL_PROCEDURES_PLUS_CODES.txt',
            'label': 'labels'
        },
        'los': {
            'experiment': 'los_iv',
            'multilabel': 'false',
            'metric': 'multiclass_classification_metrics',
            'test_file': 'los',
            'label_list': ["0", "1", "2", "3"],
            'label': 'los_label'
        },
        'mp': {
            'experiment': 'mp_iv',
            'multilabel': 'false',
            'metric': 'binary_classification_metrics',
            'test_file': 'mp',
            'label_list': ["0", "1"],
            'label': 'hospital_expire_flag'
        }
    }
    datasets = ('', '_hosp', '_icu', '_iii_test', '_iv_icu', '_matching', '_icu_9', '_icu_10')

    with open(Path(__file__).parent / 'template.yaml') as f:
        template = jinja2.Template(f.read())
    for task_name, task in tasks.items():
        for dataset in datasets:
            with open(f'eval/config_{task_name}{dataset}.yaml', "w") as fh:
                fh.write(template.render(task | {
                    'experiment': task['experiment'] + dataset,
                    'test_file': task['test_file'] + dataset + '.csv'
                }))
