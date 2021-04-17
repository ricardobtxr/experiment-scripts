#!/bin/bash

base_dir=run-sblp-obt

for exp_dir in $(ls run-sblp-obt/)
do

  echo "Processando ${exp_dir}"

  rm -f ${base_dir}/${exp_dir}/stats.txt

  for i in {0..99}
  do
    st-job-stats -n rtspin ${base_dir}/${exp_dir}/sched_RUN_trial_${i}/st-*.bin \
	 > ${base_dir}/${exp_dir}/sched_RUN_trial_${i}/stats.txt

    cat ${base_dir}/${exp_dir}/sched_RUN_trial_${i}/stats.txt \
         >> ${base_dir}/${exp_dir}/stats.txt

  done

done
