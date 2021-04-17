from fractions import Fraction

import schedcat.generator.tasks as tasks
import schedcat.model.resources as resources

from schedRUN.model.SchedulingException import Unschedulable

''' Class gathering the coarse information about Servers, Resources and Tasks '''
class InfoSRT(object):
  def __init__(self, resIds = None, tasks = None, servers = None):
    self._resIds = resIds
    self._tasks = tasks
    self._servers = servers
    
  def merge(self, other):
    self._resIds.extend(other._resIds)
    self._tasks.extend(other._tasks)
    self._servers.extend(other._servers)
    return    

''' Class representing a possible server for RUN. Used to estimate the blocking
    terms for RUNRSP.'''
class ServerResourceInterface(object):

  def __init__(self, resIds, tasksList):
    self._resIds = resIds
    self._tasks = tasksList
    self._innerSurplus = Fraction()
    return

  ''' Add a list of tasks in the task subset of the server. '''
  def addTasks(self, newTasks):
    self._tasks.extend(newTasks)
    return

  ''' Add a task in the task subset of the server. '''
  def addTask(self, newTask):
    self._tasks.append(newTask)
    return

  ''' Add a list of tasks in the task subset of the server. '''
  def addResources(self, newResources):
    self._resIds.extend(newResources)
    return

  ''' Get the rate of the server. It comprises both the rate of its children and the
      augmented cost due to the blocking term that can be suffered by them. '''
  def getUtilization(self):
    utilizationFinal = sum([Fraction(t.augmentedCost, t.period) for t in self._tasks]) + self._innerSurplus
    return utilizationFinal

  ''' Get the utilization of the server. It comprises both the rate of its children and the
      augmented cost due to the blocking term that can be suffered by them, but without server inflation. '''
  def getUtilizationPartial(self):
    utilizationPartial =  sum([Fraction(t.augmentedCost, t.period) for t in self._tasks]) 
    return utilizationPartial

  def getUtilizationOriginal(self):
    return sum([Fraction(t.cost, t.period) for t in self._tasks]) 

  ''' Remove the first task in the task subset of the server '''
  def removeTask(self):
    if len(self._tasks) == 1 :
      raise Unschedulable("[ServerResourceInterface:removeTask] Server %d has no more tasks to remove."%(self._id))
    return self._tasks.pop(0)

  ''' Find the max request length for resource r that the tasks inside the
      server can perform. If t is defined its requests are not considered. '''
  def _getMaxRequestExcept(self, r, t) :
    tasksToConsider = [x for x in self._tasks if r in x.resmodel and x is not t]
    if len(tasksToConsider) == 0 :
      return 0
    return max(map(lambda x: x.resmodel[r].max_write_length, tasksToConsider))

  ''' Return the max interference that the server produces for other servers
      when performing a request on resource r. '''
  def getExternalBlocking(self, r) :
    return self._getMaxRequestExcept(r, None)

  ''' Return the max interference that task t suffers from the tasks in
      the same server for any resource that these tasks use. '''
  def getInternalBlocking(self, t, outerBlocking) :
    if t not in self._tasks :
      raise ValueError("[ServerResourceInterface:getInternalBlocking] Task %d not in server %d!"%(t.id, self._id))

    allRequests = [0]
    for r in self._resIds :
      temp = self._getMaxRequestExcept(r, t)
      if temp > 0 :
        allRequests.append(temp + outerBlocking[r])
    return max(allRequests)

  def getMinTasksPeriod(self):
    minTaskPeriod = 0
    for t in self._tasks :
      if minTaskPeriod == 0:
        minTaskPeriod = t.period
      else:
        minTaskPeriod = min(minTaskPeriod, t.period)
    return minTaskPeriod

  ''' Update the status of the server:
      1) update the augmented cost of its children given the global distribution of the tasks in
         the up-to-date list of all servers.
      2) update the blocking term given the distribution of the tasks in all servers '''
  def updateServerStatus(self, allServers):
    otherServers = [x for x in allServers if x != self]
    ''' externalBlocking(resource_i) = length of the FIFO queue due to other servers '''
    externalBlocking = {}
    for r in self._resIds :
      externalBlocking[r] = sum([x.getExternalBlocking(r) for x in otherServers])

    maxSurplus = Fraction()
    for t in self._tasks :
      taskCost = t.cost
      for r in t.resmodel :
        ''' increment the cost of requests because of parallelism '''
        taskCost += externalBlocking[r]*t.resmodel[r].max_writes
        ''' compute the increment on the server due to blocked task '''        
        maxSurplus = max(maxSurplus, Fraction(self.getInternalBlocking(t, externalBlocking), self.getMinTasksPeriod()))

      t.augmentedCost = taskCost
      if taskCost > t.period :
        raise Unschedulable("Task%d(%d,%d) has effective c=%d"%(t.id, t.cost, t.period, t.augmentedCost))
    self._innerSurplus = maxSurplus
    return

  ''' String representation the information stored inside the server '''
  def toString(self) :
    iniUtil=Fraction()
    finUtil=Fraction()
    formatRes="Resources :  "
    formatTsk="Task{:<4d}:   "
    result = ""
    for r in self._resIds:
      formatRes += "{:^7d}".format(r)
      formatTsk += "{:>3d}({:1d}) "
    formatTsk += " :: {:>4d}({:>4d})/{:>4d} -> {:>7f}/{:>7f}"
    for t in self._tasks :
      val = []
      val.append(t.id)
      for r in self._resIds :
        if r in t.resmodel :
          val.append(t.resmodel[r].max_write_length)
          val.append(t.resmodel[r].max_writes)
        else :
          val.append(0)
          val.append(0)
      val.append(t.cost)
      val.append(t.augmentedCost)
      val.append(t.period)
      val.append(float(t.cost)/float(t.period))
      val.append(float(t.augmentedCost)/float(t.period))
      result += formatTsk.format(*val)
      result += "\n"
      iniUtil += Fraction(t.cost, t.period)
      finUtil += Fraction(t.augmentedCost,t.period)
    result = "Server\n\tInitialUtil=%f\n\tFinalUtil  =%f\n\tsurplus = %g/%g\n"%(float(iniUtil),float(finUtil+self._innerSurplus),self._innerSurplus.numerator,self._innerSurplus.denominator) + formatRes + "\n" + result
    return result

  @staticmethod
  def worstFitAutoBins(items, capacity=Fraction(1,1), weight=lambda x: Fraction(x.cost,x.period), empty_bin=list):
    sets = []
    sums = []
    for x in items:
      c = weight(x)
      # pick the bin where the item will leave the most space
      # after placing it, aka the bin with the least sum
      candidates = [s for s in sums if s + c <= capacity]
      index = -1
      if candidates :
        # fits somewhere
        index = sums.index(min(candidates))
      else :
        sets.append(empty_bin())
        sums.append(Fraction())
        index = len(sets)-1

      if index == -1 :
        print "ServerResourceInterface: SOME ERROR WHILE BIN PACKING"
      sets[index] += [x]
      sums[index] += c

    return sets

# =================================================================================================
# =================================================================================================
# =================================================================================================
# =================================================================================================

class ServerResourceInterface_RUNMrsP(ServerResourceInterface) :

  def __init__ (self, resIds = None, tasksList = None):
    super(ServerResourceInterface_RUNMrsP, self).__init__(resIds=resIds, tasksList=tasksList)

  ''' Update the Augmented Cost of the tasks of the server '''
  def updateServerStatus(self, allServers):

    otherServers = [x for x in allServers if x != self]
    ''' externalBlocking(resource_i) = length of the FIFO queue due to other servers '''
    externalBlocking = {}
    for r in self._resIds :
      externalBlocking[r] = sum([x.getExternalBlocking(r) for x in otherServers])

    maxSurplus = Fraction()
    for t in self._tasks :
      taskCost = t.cost

      internalBlocking = 0
      for r in t.resmodel :
        ''' increment the cost of requests because of parallelism '''
        taskCost += externalBlocking[r] * t.resmodel[r].max_writes
        ''' get the max internal blocking a task can suffer for a resource (SRP like property) '''
        internalBlocking = max(internalBlocking, self.getLocalBlockingTime(t, r, externalBlocking[r]))
        maxSurplus = max(maxSurplus, Fraction(internalBlocking, t.period))

      t.augmentedCost = taskCost 

      if t.augmentedCost > t.period :
        raise Unschedulable("Task%d(%d,%d) has effective c=%d"%(t.id, t.cost, t.period, t.augmentedCost))

      self._innerSurplus = maxSurplus
    
    return

  ''' Return the max interference that task t suffers from the tasks in
      the same server for any resource that these tasks use. '''
  def getLocalBlockingTime(self, t, r, outerBlocking_r) :
    localBlockingTime = 0

    blockingTasks = [x for x in self._tasks 
                     if x.period > t.period 
                     and x != t
                     and r in self._resIds 
                     and self.comparePreemptionLevel(x, t)]

    if len(blockingTasks) == 0 :
      return 0

    for blockingTask in blockingTasks:
      for blockingResource in blockingTask.resmodel:
        localBlockingTime = max(localBlockingTime, blockingTask.resmodel[blockingResource].max_write_length)

    if localBlockingTime > 0:
      localBlockingTime += outerBlocking_r

    return localBlockingTime
  
  def comparePreemptionLevel(self, x, t):
    preemtionLevel = self.getPreemptionLevelForTask(x)
    return (preemtionLevel != -1 and preemtionLevel <= t.period)
    
  def getPreemptionLevelForTask(self, t):
    taskPeriod = t.period
    for r in t.resmodel :
      periodAux = self.getMinTaskPeriodForResource(r)
      if periodAux == -1:
        continue
      taskPeriod = min(taskPeriod, periodAux)
    return taskPeriod
    
  def getMinTaskPeriodForResource(self, r):
    taskPeriod = -1
    for t in self._tasks:
      if r in t.resmodel:
        if taskPeriod == -1:
          taskPeriod = t.period
        else:
          taskPeriod = min(taskPeriod, t.period)
    return taskPeriod
    