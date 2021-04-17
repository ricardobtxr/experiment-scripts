#!/usr/bin/env python

import schedRUN.model.rv as rv
import schedRUN.manager.ServerResourceManager as srm
import schedcat.generator.tasks as tasks
import schedcat.model.resources as resources
import multiprocessing
import traceback
from optparse import OptionParser

def parseArgs () :
    parser = OptionParser("usage: %prog [options]")

    parser.add_option('-o', '--out-dir', dest='out_dir',
                      help='directory for data output',
                      default=("/home/ricardo/litmus/experiment-scripts/data/"))
    parser.add_option('-q', '--processes-pool', type='int', dest='processes',
                      help='number of processes used for parsing',
                      default=1,)
    parser.add_option('-n', '--trials', type='int', dest='trials',
                      help='number of experiment with configuration',
                      default=1,)
    parser.add_option('-s', '--system-size', type='int', dest='systemSize',
                      help='size of the system (number of tasks)',
                      default=10)
    parser.add_option('-u', '--min-utilizations', type='float', dest='minUtil',
                      help='minimum utilization for generated tasks',
                      default=0.1)
    parser.add_option('-U', '--max-utilizations', type='float', dest='maxUtil',
                      help='minimum utilization for generated tasks',
                      default=0.4)
    parser.add_option('-p', '--min-periods', type='int', dest='minPeriod',
                      help='minimum period for generated tasks, in milliseconds',
                      default=10)
    parser.add_option('-P', '--max-periods', type='int', dest='maxPeriod',
                      help='minimum period for generated tasks, in milliseconds',
                      default=100)
    parser.add_option('-r', '--res-length', type='int', dest='resLength',
                      help='length of critical section, in microseconds',
                      default=100)
    parser.add_option('-R', '--requests-num', type='int', dest='numRequests',
                      help='number of critical sections per task',
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
      "number requests = {6}\n".format(opts.systemSize, opts.minPeriod, 
      opts.maxPeriod, opts.minUtil, opts.maxUtil, opts.resLength, 
      opts.numRequests)

def save(output):
    for i in sorted(output.keys()):
        print i, output[i]['serverCount'], output[i]['augment'], output[i]['util']

def createString(exp):
    result = "\n"
    for i in sorted(exp.keys()):
        result += '{:>4d} {:>6.3f} {:>9.5f} {:>9.5f}\n'.format(i, exp[i]['serverCount'], exp[i]['augment'], float(exp[i]['util']))
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
    result = {}
    taskPeriod = rv.uniform_int(opts.minPeriod, opts.maxPeriod)
    taskUtil = rv.uniform(opts.minUtil, opts.maxUtil)
    ts = generateTaskSetBase(taskPeriod, taskUtil, opts.systemSize)
    initialUtil = sum([float(x.cost)/float(x.period) for x in ts])
    result[0] = {'util':initialUtil, 'serverCount':0, 'augment':0.0}
    for i in range(2, opts.systemSize+2, 2):
        for k in range(0, opts.numRequests):
            map(lambda x : x.resmodel[1].add_write_request(opts.resLength), ts[i-2:i])
        servers = srm.createServers([1], ts[0:i])
        if (servers is not None):
            augmentedUtil = sum([x.getUtilization() for x in servers]) + sum([0]+[x.utilization() for x in ts[i:opts.systemSize]])
            augmentFactor = (augmentedUtil-initialUtil)/initialUtil
            result[i] = {'util': augmentedUtil, 'serverCount': len(servers), 'augment': augmentFactor}
        else :
            result[i] = {'util': 0.0, 'serverCount': 0, 'augment': 0.0}
    return result

def main() :
    opts, _ = parseArgs()
    printArgs(opts)
    total = {}
    pool = multiprocessing.Pool(processes=opts.processes)
    enum = pool.imap_unordered(oneExp, [opts]*opts.trials)
    try :
        for result in enumerate(enum):
            print str(result[0])
            total[result[0]] = result[1]
    
        pool.close()
    except:
        pool.terminate()
        traceback.print_exc()
        raise Exception("Failed something!")
    finally:
        pool.join()
    
    with open(opts.out_dir+'full', 'w') as f:
        for key in total:
            f.write(createString(total[key]))
    with open(opts.out_dir+'average', 'w') as f:
        result = {}
        for i in range(0, opts.systemSize+2, 2):
            result[i] = {
              'util': sum([total[x][i]['util'] for x in total])/float(len(total)),
              'serverCount': sum([total[x][i]['serverCount'] for x in total])/float(len(total)),
              'augment': sum([total[x][i]['augment'] for x in total])/float(len(total))}
        f.write(createString(result))
    with open (opts.out_dir+'info', 'w') as f:
        f.write(infoString(opts))
    
if __name__ == '__main__':
    main()
