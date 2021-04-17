import sys
# sys.path.insert(1, '/home/luca/Desktop/AAAA/run_litmus_tool')

import model.SystemResourceGenerator as srg
import manager.ServerResourceManager as srm
from schedulability.schedulabilityRUN import SchedulabilityTestRUN as schedTestRUN

import expconfig as cfg

resDistr = .50
resWeight = .01
resNumb = 2
reqNumb = 1
utilLimit = 2.0
cpuLimit = 100

counter = 0
avgincrement = 0.0

taskSetGenerator = srg.SystemResourcesGenerator(
  cfg.NAMED_PERIODS['uni-moderate'],
  cfg.NAMED_UTILIZATIONS['uni-light'],
  resDistr, resWeight, resNumb, reqNumb, utilLimit, cpuLimit)

for i in range(0, 10) :
  ts = taskSetGenerator.generateTaskSetLinear(True)

  sched = schedTestRUN(range(0, taskSetGenerator._rn), ts)
  res = sched.isSchedulable(taskSetGenerator._cl)
  buf = sched.getServers()

  if not res :
    continue

  counter += 1
  temp = ((sum([float(x['cost'])/float(x['period']) for x in buf]) -
           sum([float(x.cost)/float(x.period) for x in ts]))/
           sum([float(x.cost)/float(x.period) for x in ts]))
  avgincrement += 100.0*temp
  print ("iteratation %d : increment %.4f%%"%(i, temp*100.0))

" FIND AVERAGE NUMBER OF SERVER PER RESOURCE "
print("Average increment : %.4f%%"%(avgincrement/counter))
'''
for s in buf :
  print "== Server %.6f / %.6f =============="%(float(s['cost'])/float(s['period']), sum([float(x.cost)/float(x.period) for x in s['tasks']]))
  print "cost: %d"%(s['cost'])
  print "period: %d"%(s['period'])
  print ", ".join([str(x.id) for x in s['tasks']])

interfaces = srm.manageResources(range(0, taskSetGenerator._rn), ts)

for i in interfaces :
  for s in interfaces[i]["servers"] :
    print s.toString()'''
