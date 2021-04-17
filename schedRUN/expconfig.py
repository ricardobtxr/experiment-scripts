import numpy as np
import random
import model.rv as rv

NumExps = 1
cpuLimit  = 3

minUtilLimit = 1.0
maxUtilLimit = cpuLimit
deltaUtilLimit = 0.1

minResDistr = 0.1
maxResDistr = 0.7
deltaResDistr = 0.025

minResWeight = 0.05
maxResWeight = 0.25
deltaResWeight = 0.025

minResNumb = 1
maxResNumb = 20
deltaResNumb = 2

minReqNumb = 1
maxReqNumb = 10
deltaReqNumb = 1

#UL = np.arange(minUtilLimit, maxUtilLimit+deltaUtilLimit, deltaUtilLimit) # utilization limit
#RD = np.arange(minResDistr,  maxResDistr +deltaResDistr,  deltaResDistr) # resDistr
UL = [2.4]
RD = [0.3]

#RW = np.arange(minResWeight, maxResWeight+deltaRerWeight, deltaResWeight)
#RN = np.arange(minResNumb,   maxResNumb  +deltaRedNumb,   deltaResNumb)

#RW = [0.05, 0.15, 0.25] # resource weight
RW = [0.05] # resource weight
# RN = [5, 12, 20] # resource number
RN = [5] # resource number
QN = [1] # number of requisitions 

NAMED_PERIODS = {
    'harmonic'      : rv.uniform_choice([25, 50, 100, 200]),
    'uni-short'     : rv.uniform_int( 3,  33),
    'uni-moderate'  : rv.uniform_int(10, 100),
    'uni-long'      : rv.uniform_int(50, 250),
}

NAMED_UTILIZATIONS = {
    'uni-very-light': rv.uniform(0.0001, 0.001),
    'uni-light'     : rv.uniform(0.001, 0.1),
    'uni-medium'    : rv.uniform(  0.1, 0.4),
    'uni-heavy'     : rv.uniform(  0.5, 0.9),
    'uni-mixed'     : rv.uniform(0.001, .4),

    'exp-light'     : rv.exponential(0, 1, 0.10),
    'exp-medium'    : rv.exponential(0, 1, 0.25),
    'exp-heavy'     : rv.exponential(0, 1, 0.50),

    'bimo-light'    : rv.multimodal([(rv.uniform(0.001, 0.5), 8),
                                     (rv.uniform(  0.5, 0.9), 1)]),
    'bimo-medium'   : rv.multimodal([(rv.uniform(0.001, 0.5), 6),
                                     (rv.uniform(  0.5, 0.9), 3)]),
    'bimo-heavy'    : rv.multimodal([(rv.uniform(0.001, 0.5), 4),
                                     (rv.uniform(  0.5, 0.9), 5)]),
    'bimo-hheavy'   : rv.multimodal([(rv.uniform(0.1, 0.5), 3),
                                     (rv.uniform(  0.5, 0.9), 6)]),
}
