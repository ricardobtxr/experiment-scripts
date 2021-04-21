#!/bin/bash

base_dir=run-gsn-edf

for exp_dir in $(ls run-gsn-edf/)
do

  echo "Processando ${exp_dir}"

  rm ${base_dir}/${exp_dir}/stats.txt

  for i in {0..99}
  do
    st-job-stats -n rtspin ${base_dir}/${exp_dir}/sched_RUN_trial_${i}/st-*.bin \
	 > ${base_dir}/${exp_dir}/sched_RUN_trial_${i}/stats.txt

    cat ${base_dir}/${exp_dir}/sched_RUN_trial_${i}/stats.txt \
         >> ${base_dir}/${exp_dir}/stats_${exp_dir}.txt

  done

done
