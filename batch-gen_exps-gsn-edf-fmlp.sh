#!/bin/bash

ne=100
u="0.075-0.35"
p="harmonic-2"
rn=4

for rd in 0.5 0.65 0.8 1
do
    for rw in 0.04 0.06
    do
        for ut in 2.0 2.5 3.0 3.5
        do

            ./gen_exps.py \
                -fr RUN_MrsP max_util=${ut} -n${ne} cpus=4 res_distr=${rd} res_weight=${rw} res_nmb=${rn} \
                -o exps-gsn-edf/gsn-edf_ut=${ut}_rd=${rd}_rw=${rw}_rn=${rn}_u=${u}_p=${p}

        done
    done
done

