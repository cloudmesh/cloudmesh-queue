#!/usr/bin/env python

import os
from submitqueue import SubmitQueue

field_tests = [
    #    ["CHD", "CSMOKING", "CANCER", "svi_minority", "Estbeds"],
    #    [],
    #    ['Population'],
    #    ['Insurance'],
    ['Nbeds'],
    # ['Nbeds_per1000'],
    # ['Nhosp'],
    # ['Estbeds'],
    # ['senior_percent'],
    # ['black_percent'],
    # ['Percentblacks'],
    # ['Percenthispanics'],
    # ['pop_density_2010'],
    # ['poverty_percent'],
    # ['svi_minority'],
    # ['svi_overall'],
    # ['CASTHMA'],
    # ['HIGHCHOL'],
    # ['DIABETES'],
    # ['OBESITY'],
    # ['CANCER'],
    # ['STROKE'],
    # ['MHLTH'],
    # ['CSMOKING'],
    # ['CHOLSCREEN'],
    # ['INSURANCE'],
    # ['CHD'],
    # ['CHECKUP'],
    # ['KIDNEY'],
    # ['BINGE'],
    # ['LPA'],
    # ['ARTHRITIS'],
    # ['BPMED'],
    # ['PHLTH'],
    # ['BPHIGH'],
    # ['COPD'],
    # ['PVI']
]

job_queue = SubmitQueue()

for fields in field_tests:
    fnames = ",".join(fields)

    # for days in range(1, 15):
    for days in range(1, 2):
        # os.system (f"./cloudmesh/timeseries/predict/lstm-predict-n.py
        # --fields={fnames} --daysin={days}")

        job_queue.generate(experiment=f'exp{days}-{fnames}',
                           name=f'job{days}-{fnames}',
                           expected_run_time='1h',
                           remote_output='.',
                           remote_mc_name='romeo',
                           parameters={'fields': fnames,
                                       'daysin': days,
                                       'n': 2,
                                       'data': './cm/cloudmesh-timeseries/data'
                                       }
                           )

# submit s/b outside of sweep.py
job_queue.submit()

print("Fetch status of the job from remote server:")
job_queue.get_status('job1')
