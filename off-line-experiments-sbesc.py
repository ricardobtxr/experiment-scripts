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

debugging = False

NAMED_UTILS = {
  'UL': rv.uniform(0.001, 0.1), 
  'UM': rv.uniform(0.1, 0.3),
  'UV': rv.uniform(0.05, 0.45),
  'U1': rv.uniform(0.15, 0.3),
  'U2': rv.uniform(0.25, 0.35),
  'U3': rv.uniform(0.175, 0.275),
  'U4': rv.uniform(0.1, 0.2),
  'U5': rv.uniform(0.15, 0.3),
  'U6': rv.uniform(0.2, 0.4),
  'U7': rv.uniform(0.25, 0.5),
  'U8': rv.uniform(0.3, 0.6),
  'U9': rv.uniform(0.075, 0.45),
  'BM': rv.multimodal([(rv.uniform(0.001, 0.5), 6), (rv.uniform(  0.5, 0.9), 3)]),
  'EM': rv.exponential(0, 1, 0.25)}
NAMED_PERIODS = {
  'M': rv.uniform_int(20, 100), 
  'P1': rv.uniform_int(150, 250), 
  'P2': rv.uniform_int(200, 300), 
  'P2a': rv.uniform_int(100, 300), 
  'P3': rv.uniform_int(100, 1000), 
  'P4': rv.uniform_int(100, 2000), 
  'P5': rv.uniform_int(100, 500), 
  'P6': rv.uniform_int(100, 7000), 
  'P7': rv.uniform_int(100, 12000), 
  'P8': rv.uniform_int(100, 20000), 
  'P9': rv.uniform_int(20, 2000), 
  'L': rv.uniform_int(50, 250)}

def createString(exp):
  result = "\n"
  for e in exp:
    result += '{:>4d} {:>8.4f} | '.format(
      e['collaborative_tasks'], e['fg_initial_util'])
    result += '{:>8.4f} {:>8.5f} {:>6.2f} {:>8.5f} | '.format(
      e['fg_final_util'], e['fg_augment'], e['fg_servers'], e['fg_augment_gblock'])
    result += '{:>8.4f} {:>8.5f} {:>6.2f} {:>8.5f} | '.format(
      e['cg_final_util'], e['cg_augment'], e['cg_servers'], e['cg_augment_gblock'])
    result += '{:>8.4f} {:>8.5f} {:>6.2f} {:>8.5f} | '.format(
      e['SBLP.order_final_util'], e['SBLP.order_augment'], e['SBLP.order_servers'], e['SBLP.order_augment_gblock'])
    result += '{:>8.4f} {:>8.5f} {:>6.2f} {:>8.5f}\n'.format(
      e['SBLP.no_merge_final_util'], e['SBLP.no_merge_augment'], e['SBLP.no_merge_servers'], e['SBLP.no_merge_augment_gblock'])
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
    'SBLP.order_initial_util': 0.0, 'SBLP.order_final_util': 0.0, 'SBLP.order_augment': 0.0, 'SBLP.order_servers': 0.0, 'SBLP.order_avg_servers_per_res': 0.0, 'SBLP.order_augment_gblock': 0.0,
    'SBLP.no_merge_initial_util': 0.0, 'SBLP.no_merge_final_util': 0.0, 'SBLP.no_merge_augment': 0.0, 'SBLP.no_merge_servers': 0.0, 'SBLP.no_merge_avg_servers_per_res': 0.0, 'SBLP.no_merge_augment_gblock': 0.0
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

def printSystem(servers):
  for s in servers:
    print s.toString()

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
      record['fg_augment_gblock'] = sum(e[i]['fg_augment_gblock'] for e in validResults)/resultsLen

    validResults = [e for e in total if e[i]['cg_final_util']>0.0]
    if len(validResults) > 0:
      resultsLen = float(len(validResults))
      record['cg_final_util'] = sum(e[i]['cg_final_util'] for e in validResults)/resultsLen
      record['cg_initial_util'] = sum(e[i]['cg_initial_util'] for e in validResults)/resultsLen
      record['cg_augment'] = sum(e[i]['cg_augment'] for e in validResults)/resultsLen
      record['cg_servers'] = sum(e[i]['cg_servers'] for e in validResults)/resultsLen
      record['cg_augment_gblock'] = sum(e[i]['cg_augment_gblock'] for e in validResults)/resultsLen
      
    validResults = [e for e in total if e[i]['SBLP.order_final_util']>0.0]
    if len(validResults) > 0:
      resultsLen = float(len(validResults))
      record['SBLP.order_final_util'] = sum(e[i]['SBLP.order_final_util'] for e in validResults)/resultsLen
      record['SBLP.order_initial_util'] = sum(e[i]['SBLP.order_initial_util'] for e in validResults)/resultsLen
      record['SBLP.order_augment'] = sum(e[i]['SBLP.order_augment'] for e in validResults)/resultsLen
      record['SBLP.order_servers'] = sum(e[i]['SBLP.order_servers'] for e in validResults)/resultsLen
      record['SBLP.order_augment_gblock'] = sum(e[i]['SBLP.order_augment_gblock'] for e in validResults)/resultsLen

    validResults = [e for e in total if e[i]['SBLP.no_merge_final_util']>0.0]
    if len(validResults) > 0:
      resultsLen = float(len(validResults))
      record['SBLP.no_merge_final_util'] = sum(e[i]['SBLP.no_merge_final_util'] for e in validResults)/resultsLen
      record['SBLP.no_merge_initial_util'] = sum(e[i]['SBLP.no_merge_initial_util'] for e in validResults)/resultsLen
      record['SBLP.no_merge_augment'] = sum(e[i]['SBLP.no_merge_augment'] for e in validResults)/resultsLen
      record['SBLP.no_merge_servers'] = sum(e[i]['SBLP.no_merge_servers'] for e in validResults)/resultsLen
      record['SBLP.no_merge_augment_gblock'] = sum(e[i]['SBLP.no_merge_augment_gblock'] for e in validResults)/resultsLen

    result.append(record)
    
  return result

def oneExp(args):

  result = []
  ts = generateTaskSetBase(NAMED_PERIODS[args['taskPeriods']], NAMED_UTILS[args['taskUtils']], args['systemSize'])
  initialUtil = sum([float(x.cost)/float(x.period) for x in ts])

  # sbesc03, sbesc04 e sbesc05
  resManager = resmng.RandomResourceManager(range(0, args['totalResources']), 10, 200)

  result.append(getEmptyOutputRecord())
  result[0]['fg_final_util'] = initialUtil
  result[0]['cg_final_util'] = initialUtil
  
  for i in range(2, len(ts)+2, 2):

    if debugging:
      print "======================================="
      print "Execution %d"%i
      print "======================================="

    resManager.distributeResources(ts[i-2:i], args['maxResPerTask'])

    record = getEmptyOutputRecord()
    manageGeneralOutputInfo(ts, resManager.getAllResources(), i, record)
    
    # FINE GRAINED SERVERS
    groups = srm.manageResourcesFineGrained(sorted(ts[0:i]))
    if (groups is not None):
      manageSpecificOutputInfo(ts, groups, resManager.getAllResources(), initialUtil, i, record, 'fg')

      if debugging:
        print ""
        print "FG Servers"
        print "======================================="
        for g in groups:
          print "FG Servers - Group %d"%g
          printSystem(groups[g]._servers)
       
    # COARSE GRAINED SERVERS
    groups = srm.manageResources(resManager.getAllResources(), sorted(ts[0:i]), 
                                 SchedulabilityTestRUN(resManager.getAllResources(), ts[0:i]))
    if (groups is not None):
      manageSpecificOutputInfo(ts, groups, resManager.getAllResources(), initialUtil, i, record, 'cg')

      if debugging:
        print ""
        print "CG Servers"
        print "======================================="
        for g in groups:
          print "CG Servers - Group %d"%g
          printSystem(groups[g]._servers)
    
    # SBLP SERVERS - OBT
    resources = resManager.getResourcesOrderedByCost()
    groupsOBT = srm.manageResourcesOBT(resources, sorted(ts[0:i]), 
                                 SchedulabilityTestSBLP_OBT(resources, ts[0:i]), True)
    if (groupsOBT is not None):
      manageSpecificOutputInfo(ts, groupsOBT, resources, initialUtil, i, record, 'SBLP.order')

      if debugging:
        print ""
        print "OBT Servers"
        print "======================================="
        for g in groupsOBT:
          print "OBT Servers - Group %d"%g
          printSystem(groupsOBT[g]._servers)

    # SBLP SERVERS - OBT, no merge
    groupsOBT_nm = srm.manageResourcesOBT(resources, sorted(ts[0:i]), 
                                 SchedulabilityTestSBLP_OBT(resources, ts[0:i]), False)
    if (groupsOBT_nm is not None):
      manageSpecificOutputInfo(ts, groupsOBT_nm, resources, initialUtil, i, record, 'SBLP.no_merge')

      if debugging:
        print ""
        print "OBT (No Merge) Servers"
        print "======================================="
        for g in groupsOBT_nm:
          print "OBT (No Merge) Servers - Group %d"%g
          printSystem(groupsOBT_nm[g]._servers)

    result.append(record)
    
  return result

def main() :

  '''
  # for debugging purpose
  syssize = [20]
  periods = ['M']
  utils = ['UV'] 
  maxrpt = [2] 
  totres = [20] 
  numExps = 20

  '''
  # experiments execution
  syssize = [40]
  periods = ['M', 'L', 'P9']
  utils = ['UL', 'UM', 'UV'] 
  maxrpt = [4, 6] # (obs: maxrpt - 1, so [3, 6])
  totres = [20] 
  numExps = 100
  
  
  filepath = '/home/ricardo/litmus/experiment-scripts/data/sbesc08/'
  
  for s in syssize:
    for p in periods:
      for u in utils:
        for q in maxrpt:
          for r in totres:
            file_id = 's={}_q={}_r={}_u={}_p={}'.format(str(s),str(q-1),str(r),u,p)
            args = {
              'taskPeriods': p,
              'taskUtils': u,
              'systemSize': s,
              'totalResources': r,
              'maxResPerTask': q}
            
            
            #asynchronous call
            total = []
            pool = multiprocessing.Pool(processes=4)
            enum = pool.imap_unordered(oneExp, [args]*numExps)
            try :
              for result in enumerate(enum):
                total.append(result[1])

              pool.close()
              #print ":"
            except:
              pool.terminate()
              traceback.print_exc()
              raise Exception("Failed something!")
            finally:
              pool.join()  
            # end of asynchronous call
        
            '''
            # synchronous call
            total = []
            for i in range(0, numExps):
              total.append(oneExp(args))
            # end of synchronous call
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
