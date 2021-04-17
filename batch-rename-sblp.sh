#!/bin/bash

base_dir=run-sblp

for exp_dir in $(ls run-sblp/)
do

  for i in {0..99}
  do

    cd ${base_dir}/${exp_dir}
    mv sched=RUN_trial=${i} sched_RUN_trial_${i}
    #mv sched_RUN_trial_${i} sched=RUN_trial=${i} 
    cd ../..

  done
done

