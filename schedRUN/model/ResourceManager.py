import random

class AbstractResourceManager(object):
  def __init__ (self, resources):
    self._res = resources
  
  def distributeResources(self, tasks, resPerTask):
    assert False
  
  def getAllResources(self):
    return self._res

class GroupResourceManager(AbstractResourceManager):

  def __init__ (self, resources, groupSize):
    AbstractResourceManager.__init__(self, resources)
    self._gSize = groupSize
    self._groups = []
    i = 0
    while i+self._gSize < len(self._res) :
      self._groups.append(self._res[i:i+self._gSize])
      i += self._gSize
    if i != len(self._res):
      self._groups.append(self._res[i-self._gSize:])
    self._resLength = {}
    for r in self._res :
      self._resLength[r] = random.randint(10, 150)
    
    
  def distributeResources(self, tasks, resPerTask, resLength, numRequests=1):
    for t in tasks:
      selectedGroup = random.choice(self._groups)
      resources = random.sample(selectedGroup, resPerTask)
#      resources = []
#      for k in range(0,resPerTask):
#        resources.append(random.choice(selectedGroup))
      for _ in range(0, numRequests):
        map(lambda x : t.resmodel[x].add_write_request(self._resLength[x]), resources)

class RandomResourceManager(AbstractResourceManager):

  def __init__(self, resources, minCost = 10, maxCost = 150):
    AbstractResourceManager.__init__(self, resources)
    self._resLength = {}
    self._resRefCount = {}
    for r in self._res:
      self._resLength[r] = random.randint(minCost, maxCost)
      self._resRefCount[r] = 0
  
  def distributeResources(self, tasks, maxResPerTask, maxRequestsCount=1):
    for t in tasks:
      resources = []
      for _ in range(1, maxResPerTask):
        resources.append(random.choice(self._res))
      totalResCost = 0
      for r in resources:
        self._resRefCount[r] += 1        
        for _ in range(0, maxRequestsCount) :
          if totalResCost + self._resLength[r] <= t.cost:
            t.resmodel[r].add_write_request(self._resLength[r])
            totalResCost += self._resLength[r]
          else:
            break
      if totalResCost == 0:
        t.resmodel[resources[0]].add_write_request(t.cost)

  def getResourcesOrderedByCost(self):
    resFactor = [(refCount-1)*resLength for refCount, resLength in zip(self._resRefCount.values(), self._resLength.values())]
    zipped_pairs = zip(resFactor, self._res) 
    resources = [resource for _, resource in sorted(zipped_pairs, reverse=True)] 
    return resources 

      

