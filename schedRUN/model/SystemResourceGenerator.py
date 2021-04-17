import schedcat.generator.tasks as tasks
import schedcat.model.resources as resources

import schedRUN.model.ResourceDistributor as rd

SCALING_PARAM = 1

class SystemResourcesGenerator(object):

  def __init__(self, periodDistr, utilDistr, resDistr, resWeight, resNumber, reqNumber, utilLimit, cpuLimit):
    ''' periodDistr and utilDistr functions used to generate independent task set.
        resDistr:  real number in [0, 1], determines the percentage of tasks that use the resource.
        resWeight: real number in (0, 1), determines the time spent in using a resource by a task.
        resNumber: integer representing the number of resources used by the system.
        reqNumber: integer representing the number of requests made towards a resource.
        utilLimit: limit for the total utilization of the system.
        cpuLimit:  number of CPU available to schedule the system
        Resources are distributed sequentially to the tasks until the limit of resDistr is reached. '''
    self._tg = tasks.TaskGenerator(periodDistr, utilDistr)
    self._rd = resDistr
    self._rw = resWeight
    self._rn = resNumber
    self._qn = reqNumber
    self._ul = utilLimit
    self._cl = cpuLimit

    # temporary data structures for support:
    # 1) the task set
    # 2) the servers
    self._ts = []
    self._rs = {}

  def generateTaskSetBase(self):
    " let's clear previous data "
    self._rs = {}
    self._ts = []
    " create a task set with the specified utilization "
    self._ts = self._tg.make_task_set(max_util = self._ul, squeeze=True)
    self._ts = [t for t in self._ts if t.cost != 0]
    " scale the parameters (otherwise for low percentage we obtain always 1) "
    for i in range(0, len(self._ts)):
      self._ts[i].id = i
      self._ts[i].cost *= SCALING_PARAM
      self._ts[i].period *= SCALING_PARAM
    " initialize the resources in the model "
    resources.initialize_resource_model(self._ts)


  def generateTaskSetLinear(self, fixedRequests = True):
    self.generateTaskSetBase()
    numRequesters = int(round(len(self._ts)*self._rd))

    #self._ts.sort(key=lambda x: float(x.cost)/float(x.period), reverse=True)
    self._ts.sort(key=lambda x: x.cost, reverse=True)

    rd.distributeLinear(
      range(0, self._rn),       # number of resources
      [self._rw],               # weight of resources
      [self._qn],               # number of requests per resource
      fixedRequests,            # whether the task resources randomly or always _qn times
      self._ts[:numRequesters]) # number of tasks using the resources

    return self._ts

  def generateTaskSetRandom(self, maxResPerTask = 1, fixedRequests = True):
    self.generateTaskSetBase()
    numRequesters = int(round(len(self._ts)*self._rd))

    rd.distributeRandom(
      range(0,self._rn),        # number of resources
      [self._rw],               # weight of resources
      maxResPerTask,            # max number of resources used per task
      self._qn,                 # number of requests per resource
      fixedRequests,            # whether the task resources randomly or always _qn times
      self._ts[:numRequesters]) # tasks using resources

    return self._ts
