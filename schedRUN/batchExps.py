#!/usr/bin/env python

import expconfig as cfg
import model.SystemResourceGenerator as generator
import schedulability.schedulabilityRUN as mySched

#x = utilLimit, y=resDistr
def saveFile(fileName, Data, resN, reqN, resW):
  out_file = open(fileName,"w")

  out_file.write("# utilLimit, resDistr, success\n")

  for k1 in cfg.UL:
    for k2 in cfg.RD:
      out_file.write(str(k1)+" "+str(k2)+" "+str(Data[k1][k2][resN][reqN][resW])+"\n")
    out_file.write("\n")

  out_file.close()


def main():

#(self, periodDistr, utilDistr, resDistr, resWeight, resNumber, utilLimit, cpuLimit)

  schedResultRUN = {}
  surplusUtilRUN = {}

  for utilLimit in cfg.UL:
    schedResultRUN[utilLimit] = {}
    surplusUtilRUN[utilLimit] = {}

    for resDistr in cfg.RD:
      schedResultRUN[utilLimit][resDistr] = {}
      surplusUtilRUN[utilLimit][resDistr] = {}

      for resNumb in cfg.RN:
        schedResultRUN[utilLimit][resDistr][resNumb] = {}
        surplusUtilRUN[utilLimit][resDistr][resNumb] = {}

        for reqNumb in cfg.QN :
          schedResultRUN[utilLimit][resDistr][resNumb][reqNumb] = {}
          surplusUtilRUN[utilLimit][resDistr][resNumb][reqNumb] = {}

          for resWeight in cfg.RW:

            taskSetGenerator = generator.SystemResourcesGenerator(
              cfg.NAMED_PERIODS['uni-moderate'],
              cfg.NAMED_UTILIZATIONS['uni-medium'],
              resDistr, resWeight, resNumb, reqNumb, utilLimit, cfg.cpuLimit)

            averageSurplusRUN = []
            counterRUN = 0

            for i in range(0, cfg.NumExps):
              taskSet = taskSetGenerator.generateTaskSetLinear()
              initialUtil = sum([float(x.cost)/float(x.period) for x in taskSet])
              mySchedRUN = mySched.SchedulabilityTestRUN(range(0, resNumb), taskSet)

              if mySchedRUN.isSchedulable(cfg.cpuLimit) :
                counterRUN += 1
                averageSurplusRUN.append(100.0*(mySchedRUN.getFinalUtilization() - initialUtil)/initialUtil)

            schedResultRUN[utilLimit][resDistr][resNumb][reqNumb][resWeight] = float(counterRUN)/float(cfg.NumExps)
            surplusUtilRUN[utilLimit][resDistr][resNumb][reqNumb][resWeight] = sum(averageSurplusRUN)/float(max(len(averageSurplusRUN), 1))

  for resN in cfg.RN:
    for reqN in cfg.QN:
      for resW in cfg.RW:
        saveFile("/home/ricardo/litmus/experiment-scripts/output/RUNsched:"+str(resN)+":"+str(reqN)+":"+str(resW), schedResultRUN, resN, reqN, resW)
        saveFile("/home/ricardo/litmus/experiment-scripts/output/RUNsurpl:"+str(resN)+":"+str(reqN)+":"+str(resW), surplusUtilRUN, resN, reqN, resW)

if __name__ == '__main__':
  main()
