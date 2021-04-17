
base_dir=run-mrsp

for exp_dir in $(ls run-mrsp/)
do
  echo "========================================================"
  echo "Processando ${exp_dir}"
  echo "========================================================"

  cd ${base_dir}/${exp_dir}

  rm overhead*
  rm *overhead*
  rm counts.csv

  # (1) Sort
  ft-sort-traces sched_RUN_trial_*/ft.bin 2>&1 | tee -a overhead-processing.log

  # (2) Split
  ft-extract-samples sched_RUN_trial_*/ft.bin 2>&1 | tee -a overhead-processing.log

  # (3) Combine
  ft-combine-samples --std ft_overhead*.float32 2>&1 | tee -a overhead-processing.log

  # (4) Count available samples
  ft-count-samples  combined-ft_overhead*.float32 > counts.csv

  # (5) Shuffle & truncate
  ft-select-samples counts.csv combined-ft_overhead*.float32 2>&1 | tee -a overhead-processing.log

  # (6) Compute statistics
  ft-compute-stats combined-ft_overhead*.sf32 > overhead.csv

  cd ../..

done
