#!/usr/bin/env python

import schedRUN.model.rv as rv
import schedRUN.model.ResourceManager as resmng
import schedRUN.manager.ServerResourceManager as srm
import schedcat.generator.tasks as tasks
import schedcat.model.resources as resources
import multiprocessing
import traceback
import math
from schedRUN.schedulability.schedulabilityRUN import schedulabilityMrsP_OBT, SchedulabilityTestRUN, SchedulabilityTestSBLP_OBT

NAMED_UTILS = {
  'L': rv.uniform(0.01, 0.1), 
  'M': rv.uniform(0.1, 0.3),
  'H': rv.uniform(0.3, 0.5),
  'V': rv.uniform(0.01, 0.5)
}

NAMED_PERIODS = {
  'S': rv.uniform_int(50, 150), 
  'M': rv.uniform_int(150, 500),
  'L': rv.uniform_int(500, 2000),
  'V': rv.uniform_int(50, 2000) 
}

debugging = False

def printSystem(servers):
  for s in servers:
    print s.toString()

def createString(exp):
  result = "\n"
  for e in exp:
    result += '{:>4d}; {:>8.4f} | '.format(
      e['collaborative_tasks'], e['fg_initial_util'])
    result += '{:>8.4f}; {:>8.5f}; {:>8.5f}; {:>6.2f} | '.format(
      e['fg_final_util'], e['fg_augment'], e['fg_augment_gblock'], e['fg_servers'])
    result += '{:>8.4f}; {:>8.5f}; {:>8.5f}; {:>6.2f} | '.format(
      e['cg_final_util'], e['cg_augment'], e['cg_augment_gblock'], e['cg_servers'])
    result += '{:>8.4f}; {:>8.5f}; {:>8.5f}; {:>6.2f} | '.format(
      e['OBT_S_final_util'], e['OBT_S_augment'], e['OBT_S_augment_gblock'], e['OBT_S_servers'])
    result += '{:>8.4f}; {:>8.5f}; {:>8.5f}; {:>6.2f}\n'.format(
      e['OBT_M_final_util'], e['OBT_M_augment'], e['OBT_M_augment_gblock'], e['OBT_M_servers'])
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

def getEmptyOutputRecord() :
  return {
    'collaborative_tasks': 0, 
    'avg_res_per_scc': 0.0, 
    'avg_tasks_per_scc': 0.0, 
    'avg_tasks_per_res': 0.0,
    'fg_initial_util': 0.0, 'fg_final_util': 0.0, 'fg_augment': 0.0, 'fg_servers': 0.0, 'fg_avg_servers_per_res': 0.0, 'fg_augment_gblock': 0.0,
    'cg_initial_util': 0.0, 'cg_final_util': 0.0, 'cg_augment': 0.0, 'cg_servers': 0.0, 'cg_avg_servers_per_res': 0.0, 'cg_augment_gblock': 0.0,
    'OBT_S_initial_util': 0.0, 'OBT_S_final_util': 0.0, 'OBT_S_augment': 0.0, 'OBT_S_servers': 0.0, 'OBT_S_avg_servers_per_res': 0.0, 'OBT_S_augment_gblock': 0.0,
    'OBT_M_initial_util': 0.0, 'OBT_M_final_util': 0.0, 'OBT_M_augment': 0.0, 'OBT_M_servers': 0.0, 'OBT_M_avg_servers_per_res': 0.0, 'OBT_M_augment_gblock': 0.0
    }

def manageGeneralOutputInfo(ts, resources, i, record):
  record['collaborative_tasks'] = i
  scc = [e for e in srm.findStronglyConnectedComponents(resources, ts[0:i]).values() if len(e._tasks)>0]
  if len(scc)<= 0:
    return
  ''' from here on, there is at least one task using at least one resource '''
  
  record['avg_res_per_scc'] = sum([len(e._resIds) for e in scc])/len(scc)
  record['avg_tasks_per_scc'] = sum([len(e._tasks) for e in scc])/len(scc)
  resCount = 0
  tpr = 0
  for r in resources:
    temp = len([t for t in ts if r in t.resmodel])
    if temp > 0:
      tpr += temp
      resCount += 1
  
  record['avg_tasks_per_res'] = float(tpr)/resCount

def printServerDebugging(prefix, groups):
  if debugging:
    print ""
    print prefix
    print "======================================="
    for g in groups:
      print prefix + " - Group %d"%g
      printSystem(groups[g]._servers)

def manageSpecificOutputInfo(ts, groups, resources, initialUtil, i, record, prefix):
  servers = reduce(lambda x, y: x+y, [groups[g]._servers for g in groups])
  finalUtil = float(sum([x.getUtilization() for x in servers]) + sum([x.utilization() for x in ts[i:]]))
  partialUtil = float(sum([x.getUtilizationPartial() for x in servers]) + sum([x.utilization() for x in ts[i:]]))
  record[prefix+'_final_util'] = finalUtil
  record[prefix+'_initial_util'] = initialUtil
  record[prefix+'_augment'] = (finalUtil-initialUtil)/float(initialUtil)
  record[prefix+'_augment_gblock'] = (partialUtil-initialUtil)/float(initialUtil)
  record[prefix+'_servers'] = len(servers)
  resCount = 0
  spr = 0
  for r in resources:
    temp = len([s for s in servers if r in s._resIds])
    if temp > 0:
      spr += temp
      resCount += 1
  if resCount > 0:
    record[prefix+'_avg_servers_per_res'] = float(spr)/resCount
  printServerDebugging(prefix, groups)

def createAvg(total):
  result = []
  totalLen = float(len(total))
  
  for i in range(0,len(total[0])):
    record = getEmptyOutputRecord()
    record['collaborative_tasks'] = total[0][i]['collaborative_tasks']
    record['avg_res_per_scc'] = sum([e[i]['avg_res_per_scc'] for e in total])/totalLen
    record['avg_tasks_per_scc'] = sum([e[i]['avg_tasks_per_scc'] for e in total])/totalLen
    record['avg_tasks_per_res'] = sum([e[i]['avg_tasks_per_res'] for e in total])/totalLen
    
    validResults = [e for e in total if e[i]['fg_final_util']>0.0]
    if len(validResults) > 0:
      resultsLen = float(len(validResults))
      record['fg_final_util'] = sum(e[i]['fg_final_util'] for e in validResults)/resultsLen
      record['fg_initial_util'] = sum(e[i]['fg_initial_util'] for e in validResults)/resultsLen
      record['fg_augment'] = sum(e[i]['fg_augment'] for e in validResults)/resultsLen
      record['fg_servers'] = sum(e[i]['fg_servers'] for e in validResults)/resultsLen
      record['fg_avg_servers_per_res'] = sum(e[i]['fg_avg_servers_per_res'] for e in validResults)/resultsLen
      record['fg_augment_gblock'] = sum(e[i]['fg_augment_gblock'] for e in validResults)/resultsLen

    validResults = [e for e in total if e[i]['cg_final_util']>0.0]
    if len(validResults) > 0:
      resultsLen = float(len(validResults))
      record['cg_final_util'] = sum(e[i]['cg_final_util'] for e in validResults)/resultsLen
      record['cg_initial_util'] = sum(e[i]['cg_initial_util'] for e in validResults)/resultsLen
      record['cg_augment'] = sum(e[i]['cg_augment'] for e in validResults)/resultsLen
      record['cg_servers'] = sum(e[i]['cg_servers'] for e in validResults)/resultsLen
      record['cg_avg_servers_per_res'] = sum(e[i]['cg_avg_servers_per_res'] for e in validResults)/resultsLen
      record['cg_augment_gblock'] = sum(e[i]['cg_augment_gblock'] for e in validResults)/resultsLen
      
    validResults = [e for e in total if e[i]['OBT_S_final_util']>0.0]
    if len(validResults) > 0:
      resultsLen = float(len(validResults))
      record['OBT_S_final_util'] = sum(e[i]['OBT_S_final_util'] for e in validResults)/resultsLen
      record['OBT_S_initial_util'] = sum(e[i]['OBT_S_initial_util'] for e in validResults)/resultsLen
      record['OBT_S_augment'] = sum(e[i]['OBT_S_augment'] for e in validResults)/resultsLen
      record['OBT_S_servers'] = sum(e[i]['OBT_S_servers'] for e in validResults)/resultsLen
      record['OBT_S_avg_servers_per_res'] = sum(e[i]['OBT_S_avg_servers_per_res'] for e in validResults)/resultsLen
      record['OBT_S_augment_gblock'] = sum(e[i]['OBT_S_augment_gblock'] for e in validResults)/resultsLen

    validResults = [e for e in total if e[i]['OBT_M_final_util']>0.0]
    if len(validResults) > 0:
      resultsLen = float(len(validResults))
      record['OBT_M_final_util'] = sum(e[i]['OBT_M_final_util'] for e in validResults)/resultsLen
      record['OBT_M_initial_util'] = sum(e[i]['OBT_M_initial_util'] for e in validResults)/resultsLen
      record['OBT_M_augment'] = sum(e[i]['OBT_M_augment'] for e in validResults)/resultsLen
      record['OBT_M_servers'] = sum(e[i]['OBT_M_servers'] for e in validResults)/resultsLen
      record['OBT_M_avg_servers_per_res'] = sum(e[i]['OBT_M_avg_servers_per_res'] for e in validResults)/resultsLen
      record['OBT_M_augment_gblock'] = sum(e[i]['OBT_M_augment_gblock'] for e in validResults)/resultsLen

    result.append(record)
    
  return result

def printHeadDebugging(i):
  if debugging:
    print "======================================="
    print "Execution %d"%i
    print "======================================="

def oneExp(args):

  result = []
  ts = generateTaskSetBase(NAMED_PERIODS[args['taskPeriods']], NAMED_UTILS[args['taskUtils']], args['systemSize'])
  initialUtil = sum([float(x.cost)/float(x.period) for x in ts])

  resManager = resmng.RandomResourceManager(range(0, args['totalResources']), args['csMin'], args['csMax'])

  result.append(getEmptyOutputRecord())
  result[0]['fg_final_util'] = initialUtil
  result[0]['cg_final_util'] = initialUtil
  
  try:
    
    for i in range(2, len(ts)+2, 2):
      
      printHeadDebugging(i)
      resManager.distributeResources(ts[i-2:i], args['maxResPerTask'])
      record = getEmptyOutputRecord()
      manageGeneralOutputInfo(ts, resManager.getAllResources(), i, record)
      
      # FINE GRAINED SERVERS
      groupsFG = srm.manageResourcesFineGrained(sorted(ts[0:i]))
      if (groupsFG is not None):
        manageSpecificOutputInfo(ts, groupsFG, resManager.getAllResources(), initialUtil, i, record, 'fg')
         
      # COARSE GRAINED SERVERS
      groupsCG = srm.manageResources(resManager.getAllResources(), sorted(ts[0:i]), 
                                   SchedulabilityTestRUN(resManager.getAllResources(), ts[0:i]))
      if (groupsCG is not None):
        manageSpecificOutputInfo(ts, groupsCG, resManager.getAllResources(), initialUtil, i, record, 'cg')
      
      # SBLP SERVERS - OBT
      resources = resManager.getResourcesOrderedByCost()
      groupsOBT = srm.manageResourcesOBT(resources, sorted(ts[0:i]), 
                                   SchedulabilityTestSBLP_OBT(resources, ts[0:i]), True)
      if (groupsOBT is not None):
        manageSpecificOutputInfo(ts, groupsOBT, resources, initialUtil, i, record, 'OBT_S')
  
      # MrsP SERVERS - OBT
      resources = resManager.getResourcesOrderedByCost()
      groupsMrsP = srm.manageResourcesOBT(resources, sorted(ts[0:i]), 
                                   schedulabilityMrsP_OBT(resources, ts[0:i]), True, True)
      if (groupsMrsP is not None):
        manageSpecificOutputInfo(ts, groupsMrsP, resources, initialUtil, i, record, 'OBT_M')
  
      result.append(record)
  
  except:
    print "Failed processing { " + ', '.join("{!s}={!r}".format(key,val) for (key,val) in args.items()) + " } "
    result = [] 
    
  return result

def main() :
  
  '''
  # for debugging purpose
  syssize = [6]
  periods = ['L']
  utils = ['UV'] 
  maxrpt = [5] 
  totres = [18] 
  numExps = 5
  csMin = 10
  csMax = 100
  filepath = '/home/ricardo/litmus/experiment-scripts/data/test01/'
  '''
  # experiments execution
  syssize = [40]
  periods = ['S', 'M', 'L', 'V']
  utils = ['L', 'M', 'H', 'V'] 
  maxrpt = [4, 7]
  totres = [20, 30]
  numExps = 100
  csMin = 50
  csMax = 200
  filepath = '/home/ricardo/litmus/experiment-scripts/data/exp02/'
  
  for s in syssize:
    for p in periods:
      for u in utils:
        for q in maxrpt:
          for r in totres:
            file_id = 's={}_p={}_u={}_q={}_r={}_c={}_{}'.format(str(s), p, u, str(q-1), str(r), csMin, csMax)
            args = {
              'taskPeriods': p,
              'taskUtils': u,
              'systemSize': s,
              'totalResources': r,
              'maxResPerTask': q,
              'csMin': csMin,
              'csMax': csMax
            }
            
            #asynchronous call
            total = []
            pool = multiprocessing.Pool(processes=4)
            enum = pool.imap_unordered(oneExp, [args]*numExps)
            try :
              for result in enumerate(enum):
                if len(result) > 0:
                  total.append(result[1])
              pool.close()
              print ":"
            except:
              pool.terminate()
              traceback.print_exc()
              raise Exception("Failed something!")
            finally:
              pool.join()
              
            '''
            # synchronous call for debugging purpose
            total = []
            for i in range(0, numExps):
              total.append(oneExp(args))
            '''
            
            print file_id
            with open(filepath+'full_'+file_id, 'w') as f:
              for exp in total:
                f.write(createString(exp))
            with open(filepath+'avg_'+file_id, 'w') as f:
              f.write(createString(createAvg(total)))
              

def debug():
  pass
    
if __name__ == '__main__':
  main()
