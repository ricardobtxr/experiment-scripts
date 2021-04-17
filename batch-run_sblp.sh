#!/bin/bash

base_dir=exps-sblp

for exp_dir in $(ls exps-sblp/)
do
  echo "========================================================"
  echo "Processando ${exp_dir}"
  echo "========================================================"

  ./run_exps.py \
         ${base_dir}/${exp_dir}/sched=RUN_trial=0 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=1 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=2 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=3 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=4 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=5 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=6 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=7 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=8 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=9 \
         ${base_dir}/${exp_dir}/sched=RUN_trial=10 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=11 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=12 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=13 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=14 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=15 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=16 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=17 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=18 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=19 \
         ${base_dir}/${exp_dir}/sched=RUN_trial=20 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=21 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=22 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=23 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=24 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=25 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=26 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=27 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=28 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=29 \
         ${base_dir}/${exp_dir}/sched=RUN_trial=30 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=31 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=32 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=33 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=34 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=35 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=36 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=37 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=38 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=39 \
         ${base_dir}/${exp_dir}/sched=RUN_trial=40 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=41 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=42 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=43 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=44 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=45 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=46 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=47 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=48 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=49 \
         ${base_dir}/${exp_dir}/sched=RUN_trial=50 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=51 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=52 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=53 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=54 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=55 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=56 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=57 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=58 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=59 \
         ${base_dir}/${exp_dir}/sched=RUN_trial=60 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=61 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=62 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=63 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=64 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=65 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=66 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=67 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=68 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=69 \
         ${base_dir}/${exp_dir}/sched=RUN_trial=70 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=71 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=72 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=73 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=74 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=75 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=76 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=77 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=78 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=79 \
         ${base_dir}/${exp_dir}/sched=RUN_trial=80 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=81 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=82 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=83 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=84 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=85 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=86 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=87 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=88 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=89 \
         ${base_dir}/${exp_dir}/sched=RUN_trial=90 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=91 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=92 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=93 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=94 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=95 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=96 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=97 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=98 \
  	 ${base_dir}/${exp_dir}/sched=RUN_trial=99 \
	 -o run-sblp/${exp_dir}

done

echo "========================================================"
echo "Final dos experimentos"
echo "========================================================"

