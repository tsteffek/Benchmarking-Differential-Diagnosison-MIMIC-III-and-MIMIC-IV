from pathlib import Path

import jinja2

if __name__ == '__main__':
    tasks = {
        'dia_3': {
            'experiment': 'dia-3-eval-iv',
            'task_config': 'config_dia_3',
            'model_name': '/models/final/dia-3'
        },
        'pro_3': {
            'experiment': 'pro-3-eval-iv',
            'task_config': 'config_pro_3',
            'model_name': '/models/final/pro-3'
        },
        'dia_plus': {
            'experiment': 'dia-plus-eval-iv',
            'task_config': 'config_dia_plus',
            'model_name': '/models/final/dia-plus'
        },
        'pro_plus': {
            'experiment': 'pro-plus-eval-iv',
            'task_config': 'config_pro_plus',
            'model_name': '/models/final/pro-plus'
        },
        'los': {
            'experiment': 'los-eval-iv',
            'task_config': 'config_los',
            'model_name': '/models/final/los'
        },
        # 'icu_los': {
        #     'experiment': 'icu-los-eval-iv',
        #     'task_config': 'config_los_iv',
        #     'model_name': '/models/final/los'
        # },
        'mp': {
            'experiment': 'mp-eval-iv',
            'task_config': 'config_mp',
            'model_name': '/models/final/mp'
        },
    }
    datasets = ('', '_hosp', '_icu', '_iii_test', '_iv_icu', '_matching', '_icu_9', '_icu_10')

    with open(Path(__file__).parent / 'template.yaml') as f:
        template = jinja2.Template(f.read())
    for task_name, task in tasks.items():
        for dataset in datasets:
            with open(f'eval/{task_name}{dataset}.yaml', "w") as fh:
                fh.write(template.render(task | {
                    'experiment': (task['experiment'] + dataset).replace('_', '-'),
                    'task_config': '/data/configs/iv/eval/' + task['task_config'] + dataset + '.yaml'
                }))
