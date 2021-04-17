#!/bin/bash

ut=3.5
ne=105
u="0.075-0.325"
p="harmonic-2"

for rd in 0.5 0.65 0.8 1
do
    for rw in 0.04 0.06
    do
        for rn in 4
        do

            ./gen_exps.py \
                -fr RUN_MrsP max_util=${ut} -n${ne} cpus=4 res_distr=${rd} res_weight=${rw} res_nmb=${rn} \
                -o exps-new/mrsp_ut=${ut}_rd=${rd}_rw=${rw}_rn=${rn}_u=${u}_p=${p}

            ./gen_exps.py \
                -fr RUN_SBLP max_util=${ut} -n${ne} cpus=4 res_distr=${rd} res_weight=${rw} res_nmb=${rn} \
                -o exps-new/sblp_ut=${ut}_rd=${rd}_rw=${rw}_rn=${rn}_u=${u}_p=${p}

            ./gen_exps.py \
                -fr RUN_SBLP_OBT max_util=${ut} -n${ne} cpus=4 res_distr=${rd} res_weight=${rw} res_nmb=${rn} \
                -o exps-new/sblp_ut=${ut}_rd=${rd}_rw=${rw}_rn=${rn}_u=${u}_p=${p}

        done
    done
done

