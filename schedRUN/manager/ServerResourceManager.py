from schedRUN.model.ServerResourceInterface import ServerResourceInterface, ServerResourceInterface_RUNMrsP, InfoSRT

from schedRUN.model.SchedulingException import Unschedulable

from fractions import Fraction

''' determine a partitioning of the taskset in which each partition contains tasks that share the same resources.
    Return the partitioning as an associative array.
    RETURN:
    result[incremental_index] = array(InfoSRT)
      ._resIds = list of resources used by tasks;
      ._tasks = list of tasks that use the resources;
      ._servers = None '''
def findStronglyConnectedComponents(resources, taskset):
  groups = {}
  groupIndex = 0
  alreadyConsidered = []
  for r in resources :
    if r in alreadyConsidered :
      continue

    tempIds = set([r])
    tempTsk = set()
    idx = 0
    while idx < len(taskset) :
      t = taskset[idx]
      if t in tempTsk :
        idx += 1
        continue
      if len( tempIds.intersection(set(t.resmodel)) ) > 0 :
        tempTsk = tempTsk.union([t])
        if len( tempIds.union(set(t.resmodel)) ) > len(tempIds) :
          idx = -1
          tempIds = tempIds.union(set(t.resmodel.keys()))
      idx += 1
    alreadyConsidered.extend(tempIds)
    if len(tempTsk) == 0:
      continue #skips if the resource is not used by any task!
    groups[groupIndex] = InfoSRT(resIds= list(tempIds), tasks= list(tempTsk))
    groupIndex += 1
  return groups

''' determine a partitioning of the taskset in which each partition contains tasks that share the same resources.
    Return the partitioning as an associative array.
    RETURN:
    result[incremental_index] = array(InfoSRT)
      ._resIds = list of resources used by tasks;
      ._tasks = list of tasks that use the resources;
      ._servers = None '''
def findResourceOrderedComponents(resources, taskset):
  groups = {}
  groupIndex = 0
  taskConsidered = []
  
  for r in resources :
    origRes = set([r])
    tempIds = origRes
    tempTsk = set()
    idx = 0
    while idx < len(taskset) :
      t = taskset[idx]
      if t in taskConsidered :
        idx += 1
        continue
      if len( origRes.intersection(set(t.resmodel)) ) > 0 :
        tempTsk = tempTsk.union([t])
        taskConsidered.extend([t])
        if len( tempIds.union(set(t.resmodel)) ) > len(tempIds) :
          idx = -1
          tempIds = tempIds.union(set(t.resmodel.keys()))
      idx += 1
    if len(tempTsk) == 0:
      continue 
    groups[groupIndex] = InfoSRT(resIds= list(tempIds), tasks= list(tempTsk))
    groupIndex += 1
  return groups

def findExactSubsets(taskset):
  groups = {}
  groupIndex = 0
  for t in taskset :
    res = t.resmodel.keys()
    found = False
    for g in groups:
      if groups[g]._resIds == res :
        groups[g]._tasks.append(t)
        found = True
        break
    if not found:
      groups[groupIndex] = InfoSRT(resIds = res, tasks= [t])
      groupIndex += 1
  return groups
    
def createFineGrainedServers(subsets):
  for index in subsets :
    subsets[index]._servers = [ServerResourceInterface(subsets[index]._resIds, subsets[index]._tasks)]
  
  try:
    index = 0
    while index < len(subsets):
      somethingChanged = False
      for s in subsets[index]._servers:
        allServers = reduce(lambda x,y : x+y, [subsets[e]._servers for e in subsets], [])
        s.updateServerStatus(allServers)
        while s.getUtilization() > Fraction(1,1):
          s_index = subsets[index]._servers.index(s)
          if s_index == (len(subsets[index]._servers)-1):
            subsets[index]._servers.append(ServerResourceInterface(subsets[index]._resIds, []))
            allServers += [subsets[index]._servers[-1]]
          subsets[index]._servers[s_index+1].addTask(s.removeTask())
          s.updateServerStatus(allServers)
          somethingChanged = True
      if somethingChanged :
        index = 0
      else :
        index += 1

  except Unschedulable, e :
    return False

  return True

    
''' create the servers for the given tasks which use the same resources.
    RETURN:
      1) the list of servers containing the tasks. The servers contain the blocking term and the tasks
         store the incremented WCET
      2) None if it was not possible to create the servers, caused by the Unschedulable exception '''
def createServers(resources, tasks, schedulabilityTest = None):
  servers = []
  try :
    ''' sort the tasks hoping that it will help in reducing the number of servers '''
    tasks = sorted(tasks,
                   key=lambda x: max(map(lambda y: x.resmodel[y].max_write_length, x.resmodel)))
    ''' create the first server with all the tasks '''
    servers.append(schedulabilityTest.getServerResourceInterface(resources, tasks))
    index = 0
    while index < len(servers) :
      somethingChanged = False
      ''' manage the status of the server considering the actual distribution of tasks in the other
          servers. This is necessary to increment the WCET of tasks and to compute the blocking term '''
      servers[index].updateServerStatus(servers)
      
      ''' remove tasks till the rate of the considered server is <= 1.0 '''
      while servers[index].getUtilization() > Fraction(1,1) :
        ''' if it is necessary, create a new server for the removed tasks '''
        if index == (len(servers) - 1) :
          servers.append(schedulabilityTest.getServerResourceInterface(resources, []))
        ''' pick a task in the considered server and put it in the next server in line '''
        servers[index + 1].addTask(servers[index].removeTask())
        
        ''' something has changed, update the status of the considered server '''
        servers[index].updateServerStatus(servers)
        
        somethingChanged = True
      ''' if something has changed, it is necessary to reconsider its consequences on the previous servers '''
      if somethingChanged :
        index = 0
      else :
        index += 1

  except Unschedulable, e :
    return None

  return servers

''' manage the collaborative tasks supplied. Tries to create the servers that will contain the collaborative
    tasks and that account for the blocking term. Tells apart collaborative and not collaborative tasks.
    RETURN:
       '''
def manageResources(resources, taskset, schedulabilityTest = None):

  ''' groups together collaborative tasks '''
  groups = findStronglyConnectedComponents(resources, taskset);

  ''' create the servers that comply with RUNRSP for each group of collaborative tasks '''
  for index in groups :
    groups[index]._servers = createServers(groups[index]._resIds, groups[index]._tasks, 
                                           schedulabilityTest = schedulabilityTest)
    ''' if some group cannot generate servers it means that the taskset is unschedulable. Abort '''
    if groups[index]._servers == None :
      return None
  
  ''' create a group for independent tasks '''
  independentTasks = []
  for t in taskset :
    if len(t.resmodel) == 0 :
      independentTasks.append(t)
  if (len(independentTasks) != 0) :
    groups[len(groups)] = (InfoSRT(resIds=[], servers=[], tasks=independentTasks))

  return groups

def manageResourcesOBT(resources, taskset, schedulabilityTest = None, mergeServers = True, noIntersection = False):

  ''' groups together collaborative tasks '''
  groups = findResourceOrderedComponents(resources, taskset);

  ''' create the servers that comply with RUNRSP for each group of collaborative tasks '''
  for index in groups :
    groups[index]._servers = createServers(groups[index]._resIds, groups[index]._tasks, 
                                           schedulabilityTest = schedulabilityTest)
    ''' if some group cannot generate servers it means that the taskset is unschedulable. Abort '''
    if groups[index]._servers == None :
      return None
  
  # Merge the colaborativ servers, if its combined utilizations are less or equal than one
  groups = schedulabilityTest.mergeServersOrderedResources(groups, mergeServers, noIntersection)
    
  ''' create a group for independent tasks '''
  independentTasks = []
  for t in taskset :
    if len(t.resmodel) == 0 :
      independentTasks.append(t)
  if (len(independentTasks) != 0) :
    groups[len(groups)] = (InfoSRT(resIds=[], servers=[], tasks=independentTasks))

  return groups

def manageResourcesFineGrained(taskset):
  subsets = findExactSubsets(taskset)
  if not createFineGrainedServers(subsets):
    return None
  return subsets

def getResourcesOrderedByCost(taskset, resources):
  _resLength = {}
  _resRefCount = {}
  
  for r in resources:
    _resLength[r] = 0.0
    _resRefCount[r] = 0
  
  for t in taskset:
    for r in t.resmodel:
      _resLength[r] = max(_resLength[r], t.resmodel[r].max_write_length)
      _resRefCount[r] += 1
  
  resFactor = [(refCount-1)*resLength for refCount, resLength in zip(_resRefCount.values(), _resLength.values())]
  zipped_pairs = zip(resFactor, resources) 
  orderedResources = [resource for _, resource in sorted(zipped_pairs, reverse=True)] 
  return orderedResources 

