from fractions import Fraction

import schedRUN.manager.ServerResourceManager as srm
from schedRUN.model.ServerResourceInterface import ServerResourceInterface, ServerResourceInterface_RUNMrsP, InfoSRT

class SchedulabilityTestRUN(object) :

    def __init__ (self, resources, taskset, packingAlgo = ServerResourceInterface.worstFitAutoBins):
        self._res = resources
        self._ts = taskset
        self._servers = []
        self._packingAlgo = packingAlgo
        return

    def getServerResourceInterface(self, resIds = None, tasks = None, servers = None) :
        return ServerResourceInterface(resIds=resIds, tasksList=tasks)

    def getServers(self) :
        return self._servers

    def getFinalUtilization(self) :
        result = sum([float(x['cost'])/float(x['period']) for x in self._servers])
        return result;

    def getOriginalUtilization(self) :
        result = sum([float(x['original_util'].numerator)/float(x['original_util'].denominator)
                  for x in self._servers ])
        return result;

    ''' create the servers for collaborative tasks and the set of independent tasks '''
    def generateGroups(self):
        return srm.manageResources(self._res, self._ts, schedulabilityTest = self)

    ''' Determines whether the taskset is schedulable given the cpu limit. If it is, it is possible to
        later recover the packing for which the taskset is schedulable with getServer().
        NB: limit must be an integer, representing the number of cpus of the platform. '''
    def isSchedulable(self, limit) :
        result = True

        groups = self.generateGroups()

        ''' if some problem while creating the servers for collaborative tasks (i.e.: some task has WCET
        greater than period or it is impossible to create the servers at all) then the taskset is not
        schedulable '''
        if groups == None :
            return False
        ''' check the total augmented utilization of the taskset '''
        totalUtil = Fraction()
        independentTaskIndex = -1
        for index in groups :
            if len(groups[index]._resIds) != 0 :
                totalUtil += sum([s.getUtilization() for s in groups[index]._servers])
            else :
                totalUtil += sum(Fraction(t.cost, t.period) for t in groups[index]._tasks)
                if independentTaskIndex != -1 :
                    print "Multiple independent task servers. ERROR!"
                independentTaskIndex = index
        if totalUtil > Fraction(limit, 1) :
            return False

        ''' from hereafter the taskset is schedulable. let us manage the independent tasks
        and create the servers for them '''
        if independentTaskIndex != -1 :
            independentTasks = sorted(groups[independentTaskIndex]._tasks, key=lambda x: float(x.cost)/float(x.period), reverse=True)
            groups[independentTaskIndex]._servers = self._packingAlgo(independentTasks)

        ''' let us create servers representing the packing of the tasks '''
        serverIndex = 0
        for index in groups :
            if len(groups[index]._resIds) != 0 :
                self._servers.extend(
            [{'cost'  : x.getUtilization().numerator,
            'period': x.getUtilization().denominator,
            'tasks' : x._tasks} for x in groups[index]._servers])
            else :
                self._servers.extend(
            [{'cost'  : sum([Fraction(y.cost, y.period) for y in x]).numerator,
            'period': sum([Fraction(y.cost, y.period) for y in x]).denominator,
            'tasks' : x} for x in groups[index]._servers])

        return True

class SchedulabilityTestSBLP_OBT(SchedulabilityTestRUN) :

    def __init__ (self, resources, taskset, packingAlgo = ServerResourceInterface.worstFitAutoBins):
        self._res = resources
        self._ts = taskset
        self._servers = []
        self._packingAlgo = packingAlgo
        return

    ''' This function combine groups of servers into only one group '''
    def mergeCollaborativeGroups(self, groups):
        if groups == None :
            return groups
        group = InfoSRT(resIds=[], tasks=[], servers=[])
        for groupOther in groups:
            group.merge(groups[groupOther])
        return group

    def mergeServersOrderedResources(self, groups, doMerge = True, noIntersection = False) :
        return self._mergeServersOrderedResources(groups, doMerge, False)

    ''' This function combine pairs of servers if its summed utilizations are below or equals to 1 '''
    def _mergeServersOrderedResources(self, groups, doMerge = True, noIntersection = False) :
        group = self.mergeCollaborativeGroups(groups)
        newGroup = {}
        if group == None :
            return group  
        index = 0
        if doMerge:
            while index < len(group._servers):
                server_1 = group._servers[index]
                server_1_resIds = set(server_1._resIds)
                if (index < len(group._servers) - 1):
                    for server_2 in group._servers[index + 1: ]:
                        if (server_1.getUtilization() + server_2.getUtilization() <= Fraction(1,1) 
                        and (noIntersection or server_1_resIds.intersection(set(server_2._resIds)))):
                            self.mergeServers(server_1, server_2, group._servers)          
                            index = -1
                            break
                server_1.updateServerStatus(group._servers) 
                index += 1
        
        newGroup[0] = group

        return newGroup
    
    def mergeServers(self, server_1, server_2, servers) :
        server_1._resIds = list(set(server_1._resIds).union(set(server_2._resIds)))
        server_1.addTasks(server_2._tasks)
        servers.remove(server_2)
        return
    
    ''' create the servers for collaborative tasks and the set of independent tasks '''
    def generateGroups(self):
        resources = srm.getResourcesOrderedByCost(self._ts, self._res)
        groups = srm.manageResourcesOBT(resources, self._ts, schedulabilityTest = self)
        return groups 
    
# =================================================================================================
# =================================================================================================
# =================================================================================================
# =================================================================================================

class schedulabilityMrsP_OBT(SchedulabilityTestSBLP_OBT) :

    def __init__ (self, resources, taskset, packingAlgo = ServerResourceInterface.worstFitAutoBins):
        super(schedulabilityMrsP_OBT, self).__init__(resources=resources, taskset=taskset, packingAlgo=packingAlgo)

    def getServerResourceInterface(self, resIds = None, tasks = None, servers = None) :
        return ServerResourceInterface_RUNMrsP(resIds=resIds, tasksList=tasks)

    def mergeServersOrderedResources(self, groups, doMerge = True, noIntersection = False) :
        groups = self._mergeServersOrderedResources(groups, doMerge, False)
        if noIntersection:
            ''' Aditional step which merges also unrelated groups '''
            groups = self._mergeServersOrderedResources(groups, doMerge, noIntersection)
        return groups
