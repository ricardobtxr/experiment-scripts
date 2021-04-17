#!/usr/bin/env python

import schedRUN.model.rv as rv
import schedRUN.model.ResourceManager as resmng
import schedRUN.manager.ServerResourceManager as srm
import schedcat.generator.tasks as tasks
import schedcat.model.resources as resources
import multiprocessing
import traceback
import math
from optparse import OptionParser
from schedRUN.schedulability.schedulabilityRUN import schedulabilityMrsP_OBT, SchedulabilityTestRUN

# ./moreResExp.py -o /home/luca/asddd/ -q1 -n1 -e1
def parseArgs () :
	parser = OptionParser("usage: %prog [options]")
	# debug params: -o /home/ricardo/litmus/experiment-scripts/data/moreResExps/exp1 -n 1 -q 1 -e 2
	parser.add_option('-o', '--out-dir', dest='out_dir',
	                  help='directory for data output',
	                  default=("/home/ricardo/litmus/experiment-scripts/data/moreResExp/exp00/"))
	parser.add_option('-q', '--processes-pool', type='int', dest='processes',
	                  help='number of processes used for parsing',
	                  default=8,)
	parser.add_option('-n', '--trials', type='int', dest='trials',
	                  help='number of experiment with configuration',
	                  default=10,)
	parser.add_option('-s', '--system-size', type='int', dest='systemSize',
	                  help='size of the system (number of tasks)',
	                  default=50)
	parser.add_option('-u', '--min-utilizations', type='float', dest='minUtil',
	                  help='minimum utilization for generated tasks',
	                  default=0.1)
	parser.add_option('-U', '--max-utilizations', type='float', dest='maxUtil',
	                  help='minimum utilization for generated tasks',
	                  default=0.3)
	parser.add_option('-p', '--min-periods', type='int', dest='minPeriod',
	                  help='minimum period for generated tasks, in milliseconds',
	                  default=10)
	parser.add_option('-P', '--max-periods', type='int', dest='maxPeriod',
	                  help='minimum period for generated tasks, in milliseconds',
	                  default=100)
	parser.add_option('-r', '--res-length', type='int', dest='resLength',
	                  help='length of critical section, in microseconds',
	                  default=500)
	parser.add_option('-R', '--requests-num', type='int', dest='numRequests',
	                  help='number of critical sections per task',
	                  default=1)
	parser.add_option('-e', '--resource-entropy', type='float', dest='resEntropy',
	                  help='degree of entropy in the distribution of resources',
	                  default=1.0)
	parser.add_option('-E', '--resources-per-task', type='int', dest='resPerTask',
	                  help='number of resources used by each task',
	                  default=1)
	return parser.parse_args()

def printArgs(opts) :
	print ""\
        "total experiments = {0}\n"\
    "output dir = {1}\n"\
    "number of processes to use = {2}\n"\
    "---------------------------\n".format(opts.trials, opts.out_dir, opts.processes) +\
    infoString(opts)

def infoString(opts) :
	return ""\
	       "taskset size = {0}\n"\
	  "task periods = uniform({1}, {2}) ms\n"\
	  "task utilization = uniform({3}, {4})\n"\
	  "critical section = {5} us\n"\
	  "number requests = {6}\n"\
	  "resources per task = {7}\n"\
	  "degree of entropy = {8}\n"\
	  "resources per group = {9}".format(opts.systemSize, opts.minPeriod, 
	                                     opts.maxPeriod, opts.minUtil, opts.maxUtil, opts.resLength, 
	  opts.numRequests, opts.resPerTask, opts.resEntropy, 
	  int(math.ceil(opts.resPerTask*opts.resEntropy)))

def save(output):
	for i in sorted(output.keys()):
		print i, output[i]['groupCount'], output[i]['serverCount'], output[i]['augment'], output[i]['util']

def createString(exp):
	result = "\n"
	for i in sorted(exp.keys()):
		result += '{:>4d} {:>6.3f} {:>6.3f} {:>9.5f} {:>9.5f}\n'.format(i, exp[i]['groupCount'], exp[i]['serverCount'], exp[i]['augment'], float(exp[i]['util']))
	return result+"\n"

def generateTaskSetBase(taskPeriod, taskUtil, systemSize):
	tg = tasks.TaskGenerator(taskPeriod, taskUtil)
	ts = tg.make_task_set(max_tasks = systemSize)
	ts = [t for t in ts if t.cost != 0]
	" scale the parameters such that we always consider times in microseconds "
	for i in range(0, len(ts)):
		ts[i].id = i
		ts[i].cost *= 1000
		ts[i].period *= 1000
	" initialize the resources in the model "
	resources.initialize_resource_model(ts)
	return ts


def oneExp(opts):

	resultFineGrain = {}
	resultCoarseGrain = {}
	resultMrsP = {}
	taskPeriod = rv.uniform_int(opts.minPeriod, opts.maxPeriod)
	taskUtil = rv.uniform(opts.minUtil, opts.maxUtil)
	ts = generateTaskSetBase(taskPeriod, taskUtil, opts.systemSize)
	initialUtil = sum([float(x.cost)/float(x.period) for x in ts])
	groupSize = int(math.ceil(opts.resPerTask*opts.resEntropy))
	resManager = resmng.GroupResourceManager(range(0, groupSize), groupSize)

	resultFineGrain[0] = {'util':initialUtil, 'groupCount':0, 'serverCount':0, 'augment':0.0}
	resultCoarseGrain[0] = {'util':initialUtil, 'groupCount':0, 'serverCount':0, 'augment':0.0}
	resultMrsP[0] = {'util':initialUtil, 'groupCount':0, 'serverCount':0, 'augment':0.0}
	for i in range(2, opts.systemSize+2, 2):
		resManager.distributeResources(ts[i-2:i], opts.resPerTask, opts.resLength, opts.numRequests)

		# FINE GRAINED SERVERS
		groups = srm.manageResourcesFineGrained(ts[0:i])
		if (groups is not None):
			servers = reduce(lambda x,y: x+y, [groups[g]._servers for g in groups])
			augmentedUtil = sum([x.getUtilization() for x in servers]) + sum([x.utilization() for x in ts[i:opts.systemSize]])
			augmentFactor = (augmentedUtil-initialUtil)/initialUtil
			resultFineGrain[i] = {'util': augmentedUtil, 'groupCount':len(groups), 'serverCount': len(servers), 'augment': augmentFactor}
		else :
			resultFineGrain[i] = {'util': 0.0, 'groupCount':0, 'serverCount': 0, 'augment': 0.0}

		# COARSE GRAINED SERVERS
		groups = srm.manageResources(resManager.getAllResources(), ts[0:i], 
		                             SchedulabilityTestRUN(resManager.getAllResources(), ts[0:i]))
		if (groups is not None):
			servers = reduce(lambda x,y: x+y, [groups[g]._servers for g in groups])
			augmentedUtil = sum([x.getUtilization() for x in servers]) + sum([x.utilization() for x in ts[i:opts.systemSize]])
			augmentFactor = (augmentedUtil-initialUtil)/initialUtil
			resultCoarseGrain[i] = {'util': augmentedUtil, 'groupCount':len(groups), 'serverCount': len(servers), 'augment': augmentFactor}
		else :
			resultCoarseGrain[i] = {'util': 0.0, 'groupCount':0, 'serverCount': 0, 'augment': 0.0}

		# MrsP SERVERS
		groups = srm.manageResources(resManager.getAllResources(), ts[0:i], 
	                                 schedulabilityMrsP_OBT(resManager.getAllResources(), ts[0:i]))
		if (groups is not None):
			servers = reduce(lambda x,y: x+y, [groups[g]._servers for g in groups])
			augmentedUtil = sum([x.getUtilization() for x in servers]) + sum([x.utilization() for x in ts[i:opts.systemSize]])
			augmentFactor = (augmentedUtil-initialUtil)/initialUtil
			resultMrsP[i] = {'util': augmentedUtil, 'groupCount':len(groups), 'serverCount': len(servers), 'augment': augmentFactor}
		else :
			resultMrsP[i] = {'util': 0.0, 'groupCount':0, 'serverCount': 0, 'augment': 0.0}

	return (resultFineGrain, resultCoarseGrain, resultMrsP)

def main() :
	opts, _ = parseArgs()
	printArgs(opts)
	totalFineGrain = {}
	totalCoarseGrain = {}
	totalMrsP = {}
	pool = multiprocessing.Pool(processes=opts.processes)
	enum = pool.imap_unordered(oneExp, [opts]*opts.trials)
	try :
		for result in enumerate(enum):
			print str(result[0])
			totalFineGrain[result[0]] = result[1][0]
			totalCoarseGrain[result[0]] = result[1][1]
			totalMrsP[result[0]] = result[1][2]

		pool.close()
	except:
		pool.terminate()
		traceback.print_exc()
		raise Exception("Failed something!")
	finally:
		pool.join()

	with open(opts.out_dir+'fullFine', 'w') as f:
		for key in totalFineGrain:
			f.write(createString(totalFineGrain[key]))
	with open(opts.out_dir+'fullCoarse', 'w') as f:
		for key in totalCoarseGrain:
			f.write(createString(totalCoarseGrain[key]))
	with open(opts.out_dir+'fullMrsP', 'w') as f:
		for key in totalMrsP:
			f.write(createString(totalMrsP[key]))
	with open(opts.out_dir+'averageFine', 'w') as f:
		result = {}
		for i in range(0, opts.systemSize+2, 2):
			result[i] = {
			    'util': sum([totalFineGrain[x][i]['util'] for x in totalFineGrain])/float(len(totalFineGrain)),
			    'groupCount': sum([totalFineGrain[x][i]['groupCount'] for x in totalFineGrain])/float(len(totalFineGrain)),
			    'serverCount': sum([totalFineGrain[x][i]['serverCount'] for x in totalFineGrain])/float(len(totalFineGrain)),
			    'augment': sum([totalFineGrain[x][i]['augment'] for x in totalFineGrain])/float(len(totalFineGrain))}
		f.write(createString(result))
	with open(opts.out_dir+'averageCoarse', 'w') as f:
		result = {}
		for i in range(0, opts.systemSize+2, 2):
			result[i] = {
			    'util': sum([totalCoarseGrain[x][i]['util'] for x in totalCoarseGrain])/float(len(totalCoarseGrain)),
			    'groupCount': sum([totalCoarseGrain[x][i]['groupCount'] for x in totalCoarseGrain])/float(len(totalCoarseGrain)),
			    'serverCount': sum([totalCoarseGrain[x][i]['serverCount'] for x in totalCoarseGrain])/float(len(totalCoarseGrain)),
			    'augment': sum([totalCoarseGrain[x][i]['augment'] for x in totalCoarseGrain])/float(len(totalCoarseGrain))}
		f.write(createString(result))

	with open(opts.out_dir+'averageMrsP', 'w') as f:
		result = {}
		for i in range(0, opts.systemSize+2, 2):
			result[i] = {
			    'util': sum([totalMrsP[x][i]['util'] for x in totalMrsP])/float(len(totalMrsP)),
			    'groupCount': sum([totalMrsP[x][i]['groupCount'] for x in totalMrsP])/float(len(totalMrsP)),
			    'serverCount': sum([totalMrsP[x][i]['serverCount'] for x in totalMrsP])/float(len(totalMrsP)),
			    'augment': sum([totalMrsP[x][i]['augment'] for x in totalMrsP])/float(len(totalMrsP))}
		f.write(createString(result))

	with open (opts.out_dir+'info', 'w') as f:
		f.write(infoString(opts))

def debug():
	opts, _ = parseArgs()
	printArgs(opts)
	k=oneExp(opts)
	for i in k :
		print "(("+str(i)+")) : [ ",
		for r in k[i]._resIds:
			print str(r)+" ",
		print "]"
		for t in k[i]._servers:
			print t.toString()
'''    for t in k[i]._tasks:
      print "\tid:"+str(t.id)+" -- [ ",
      for r in t.resmodel:
        print str(r)+" ",
      print " ]" '''

if __name__ == '__main__':
	main()
