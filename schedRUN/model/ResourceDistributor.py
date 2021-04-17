import random

''' Distribute resources to tasks linearly. Each task uses one resource.
    resRange       = list of IDs of resources that can be used.
    resWeight      = percentage of the min WCET of tasks (using the resource)
        that a task spends using the resource. If it is a list of a single
        element, then every resource will use the same value. Otherwise the
        list must contain one element for every resource.
    resRequest     = max number of requests that a task can perform on a given
        resource. If it is a list of a single element, then every task will
        use the same value. Otherwise the list must contain one element for
        every resource (every task using the resource use this value).
    fixedRequests  = if True then each task performs resRequests on each
        resource. Otherwise each task performs random[1, resRequests].
    ts             = set of tasks that must use the resources.

    Example =
      import ResourceDistribution as rd
      rd.distributeLinear(
        [0,    1,    2,    3,    4,    5,    6,    7],
        [0.05, 0.03, 0.02, 0.06, 0.05, 0.04, 0.05, 0.03],
        [5,    2,    3,    1,    3,    4,    2,    3],
        False,
        ts)
'''
def distributeLinear(resRange, resWeight, resRequest, fixedRequests, ts) :

  if len(ts) < len(resRange) :
    resRange = range(0, len(ts))
  
  a = len(ts)/len(resRange)
  b = len(ts)%len(resRange)
  index = 0

  "STEP1) initialize the bins: one per resource."
  bins = {}
  for r in resRange :
    bins[r] = []
    findex = index+a
    if b > 0 :
      findex +=1
      b -= 1
    bins[r].extend(ts[index:findex])
    index = findex
  "STEP2) determine which task uses which resource: distribute the tasks to the bins linearly."
  '''
  index = 0
  for t in ts :
    bins[resRange[index]].append(t)
    index = (index+1)%len(resRange)
  '''
  random.seed()
  index = 0
  for r in resRange :
    "STEP3) parsing initial information. Determining the size of the requests per resource."
    partialCost = 0.0
    if len(resWeight) == 1 :
      partialCost = resWeight[0]
    elif len(resWeight) == len(resRange) :
      partialCost = resWeight[index]
    else :
      raise ValueError("DistributeLinear: E1) incompatible dimensions.")
    resCost = max(1, int(min([1000000]+[x.cost for x in bins[r]])*partialCost))

    "STEP4) parsing initial information. Determining the maximum number of requests per task."
    numreq = 0
    if len(resRequest) == 1 :
      numreq = resRequest[0]
    elif len(resRequest) == len(resRange) :
      numreq = resRequest[index]
    else :
      raise ValueError("DistributeLinear: E2) incompatible dimensions.")

    for t in bins[r] :

      "STEP5) insert variability in the number of requests if requested."
      if not fixedRequests :
        numreq = random.randint(1, numreq)

      "STEP6) let the task perform the requests."
      for _ in range(0, numreq) :
        t.resmodel[r].add_write_request(resCost)

    index = index + 1

  return

''' Randomly distribute resources to tasks.
    resRange = IDs of resources that can be used.
    resWeight = percentage of the minimum WCET of tasks that a task
                spends using the resource.
    maxResPerTask = maximum number of different resources that each task can use.
    maxResRequests = maximum number of requests that each task can perform on a
                given resource.
    fixedRequests = if True then each task performs maxResRequests on each
                resource. Otherwise each task performs random[1, maxResRequests].
    ts = set of tasks that must use the resources.

    Example =
      import ResourceDistribution as rd
      rd.distributeRandom(range(0,4), [0.05], 2, 3, True, ts[:len(ts)/2])
      rd.distributeRandom(range(4,8), [0.05], 2, 3, True, ts[len(ts)/2:])
'''
def distributeRandom(resRange, resWeight, maxResPerTask, maxResRequests, fixedRequests, ts) :
  "STEP1) initialize the bins: one per resource."
  bins = {}
  for r in resRange :
    bins[r] = []

  "STEP2) determine which task uses which resource."
  for t in ts :
    resCount = random.randint(1, maxResPerTask)
    usedRes = random.sample(resRange, resCount)
    for r in usedRes :
      bins[r].append(t)

  index = 0
  for r in resRange :
    "STEP3) determine the worst case for the resource."
    partialCost = 0.0
    if len(resWeight) == 1 :
      partialCost = resWeight[0]
    elif len(resWeight) == len(resRange) :
      partialCost = resWeight[index]
    else :
      raise ValueError("DistributeRandom: E1) incompatible dimensions.")

    resCost = max(1, int(min([1000000]+[x.cost for x in bins[r]])*partialCost))

    for t in bins[r] :
      "STEP4) determine the number of requests each task performs."
      numreq = maxResRequests
      if not fixedRequests :
        numreq = random.randint(1, maxResRequests)

      "STEP5) tell the task to perform its requests."
      for _ in range(0, numreq) :
        t.resmodel[r].add_write_request(resCost)

    index = index + 1

  return

