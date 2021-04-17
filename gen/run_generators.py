import math
from decimal import *
from fractions import Fraction
import json
import schedcat.generator.tasks as tasks
from schedcat.model.tasks import SporadicTask
import schedcat.model.resources as resources
from gen.run_task import FixedRateTask
import run_exps
import edf_generators as edfGen
import random

TP_TBASE = """#for $t in $task_set
{} $t.cost $t.period
#end for"""
TP_RUN_TASK = TP_TBASE.format("-S $t.server")
TP_RUN_TASK_RES = TP_TBASE.format("-S $t.server #if len($t.resmodel)>0# -X RUN #for $r in $t.resmodel# -Q $r -L $t.resmodel[r].max_write_length #end for# #end if#")

MAX_TRIES = 100
def ignore(_):
    pass

class RUNGenerator(edfGen.EdfGenerator):
    def __init__(self, params={}, template=[TP_RUN_TASK]):
        super(RUNGenerator, self).__init__("RUN",
                                                   template, [], params)
        self.server_count = 0

    def print_header(self):
        return

    def print_msg(self, str):
        print str

    def _from_file(self, file_name):
        with open(file_name, 'r') as f:
            data = f.read().strip()
        try:
            schedule = eval(data)
        except:
            schedule = run_exps.convert_data(data)
        ts = []
        for task_conf in schedule['task']:
            (task, args) = (task_conf[0], task_conf[1])
            real_args = args.split()
            index = 0
            if '-S' in real_args:
                index = real_args.index('-S') + 2
            ts.append(SporadicTask(int(real_args[index + 0]), int(real_args[index + 1])))
        return ts

    def _create_exp(self, exp_params) :
        tries = 0
        done = False
        while not done :
            try :
                super(RUNGenerator, self)._create_exp(exp_params)
                done = True
            except Exception, e :
                tries += 1
                if tries >= MAX_TRIES :
                    print('Unfeasible parameters for {0} tasksets'.format(MAX_TRIES))
                    return
        self.print_msg("--- Found solution in %d tries"%(tries+1))
        return

    def _customize(self, taskset, exp_params):
        if 'max_util' in exp_params:
            print 'sched=RUN cpus={0} max_util={1} tasks={2}'.format(unicode(exp_params['cpus']), unicode(exp_params['max_util']), unicode(len(taskset)))
        else:
            print 'sched=RUN cpus={0} max_util={1} tasks={2}'.format(unicode(exp_params['cpus']), unicode('0.0'), unicode(len(taskset)))
        cpus  = exp_params['cpus']
        self.server_count = 0
        data = self._reductor(taskset, cpus, exp_params)
        tree_file = self.out_dir + "/tree.json"
        with open(tree_file, 'wa') as f:
            json.dump(data, f, indent=4)

    def _reductor(self, taskset, cpus, params):

        #First create fixed-rates
        n_tasks = len(taskset)
        #On heavy task case #tasks may be less than #cpus
        if (n_tasks < cpus):
            print 'attention: #cpus has changed from {0} to {1}'.format(unicode(cpus),unicode(n_tasks))
            cpus = n_tasks

        new_taskset = self._perform_first_packing(taskset, cpus, params)
        unit_server = self._reduce(new_taskset, 1)

        if (len(unit_server) != 1 or
                    (unit_server[0].util_frac() != Fraction(0,1) and
                     unit_server[0].util_frac() != Fraction(1,1))) :
            #not(unit_server[0].util_frac().numerator == unit_server[0].util_frac().denominator)):
            raise Exception('Not a Unit-Server')

        print 'Root level: {0}'.format(unicode(unit_server[0].level - 1))

        return FixedRateTask.serialize(unit_server[0])

    def _perform_first_packing(self, taskset, cpus, params) :

        t_id = 0
        fr_taskset = []
        tot_util = Fraction()

        for t in taskset:
            t.id = t_id
            fr_taskset.append(FixedRateTask(t.cost, t.period, t.deadline, t_id))
            t_id += 1
            tot_util += Fraction(t.cost, t.period)
        #Second distribuites unused cpu capacity (slack-pack)
        print 'Total utilization: {0}'.format(Decimal(tot_util.numerator)/Decimal(tot_util.denominator))

        unused_capacity = Fraction(cpus,1) - tot_util
        if (unused_capacity < Fraction()):
            raise Exception('Unfeasible Taskset')

        if 'slack_dist' in params and params['slack_dist'] == 'tasks':
            fr_taskset.sort(key=lambda x: x.util_frac(), reverse=True)
            self._distribuite_slack(fr_taskset, unused_capacity)
            new_taskset = self._pack(fr_taskset, cpus, 0)
            self._dual(new_taskset)
        else:
            new_taskset = self._pack(fr_taskset, cpus, 0)
            new_taskset.sort(key=lambda x: x.utilization(), reverse=True)
            self._distribuite_slack(new_taskset, unused_capacity)
            self._dual(new_taskset)

        for t in taskset:
            for fr_t in fr_taskset:
                if (fr_t.id == t.id):
                    t.server = fr_t.server

        return new_taskset


    def _slack_dist(self, ts, slack):

        n_tasks = len(ts)
        val_a = ts[0].dual_utilization()
        val_b = slack / Decimal(n_tasks)

        unused_capacity = slack

        task_extra_util = min(val_a, val_b)
        for t in ts:
            if (t.dual_utilization() <= task_extra_util):
                unused_capacity -= t.dual_utilization()
                t.cost = t.period
            else:
                tmp_util = t.utilization()
                t.cost += int(task_extra_util * Decimal(t.period))
                unused_capacity -= (t.utilization() - tmp_util)

        tries = 10
        while (unused_capacity > Decimal(0)) and (tries > 0):
            for t in ts:
                tmp_value = unused_capacity * Decimal(t.period)
                if (t.dual_utilization() >= unused_capacity) and tmp_value == int(tmp_value):
                    t.cost += int(tmp_value)
                    unused_capacity = Decimal(0)
                    break
            if (unused_capacity > Decimal(0)):
                for t in ts:
                    if (t.dual_utilization() <= unused_capacity):
                        unused_capacity -= t.dual_utilization()
                        t.cost = t.period
            tries -= 1

        if (unused_capacity > Decimal(0)):
            raise Exception('Still capacity unused: ' + str(unused_capacity))

    def _distribuite_slack(self, ts, slack):
        ts.sort(key=lambda x: x.util_frac(), reverse=True)
        i = 0
        unused_capacity = slack
        while (unused_capacity > Fraction()) and (i < len(ts)):
            t = ts[i]
            if (t.dual_util_frac() <= unused_capacity):
                unused_capacity -= t.dual_util_frac()
                t.cost = t.period
            else:
                tmp_frac = t.util_frac() + unused_capacity
                t.cost = tmp_frac.numerator
                t.period = tmp_frac.denominator
                unused_capacity = Fraction()
            i+=1
        if (unused_capacity > Fraction()):
            raise Exception('Still capacity unused: ' + str(unused_capacity))

    def _dual(self, taskset):
        for t in taskset:
            t.cost = t.period - t.cost

    def _pack(self, taskset, cpus, level):
        self.misfit = 0
        n_bins = cpus

        taskset.sort(key=lambda x: x.util_frac(), reverse=True)

        bins = RUNGenerator.worst_fit(taskset,
                                              n_bins,
                                              Fraction(1,1),
                                              lambda x: x.util_frac(),
                                              self._misfit)
        while (self.misfit > 0):
            #n_bins += math.ceil(self.misfit)
            n_bins += 1 #self.misfit
            self.misfit = 0
            bins = RUNGenerator.worst_fit(taskset,
                                                      n_bins,
                                                      Fraction(1,1),
                                                      lambda x: x.util_frac(),
                                                      self._misfit)
        servers = []
        for item in bins:
            tmp_server = FixedRateTask._aggregate(item, self.server_count, level)
            servers.append(tmp_server)
            self.server_count += 1

        self.misfit = 0
        return servers

    def _misfit(self, x):
        #self.misfit += x.dual_utilization()
        self.misfit += 1

    def _reduce(self, taskset, level):
        utilization = Fraction()
        for t in taskset:
            utilization += t.util_frac()

        new_taskset = self._pack(taskset,
                                         int(math.ceil(utilization)),
                                         level)
        self._dual(new_taskset)

        if (utilization <= Fraction(1,1)):
            return new_taskset
        else:
            return self._reduce(new_taskset, level + 1)

    def _create_taskset(self, params, periods, utils, max_util = None):

        if 'max_util' in params:
            max_util = float(params['max_util'])
            if (max_util < 0.0) or (max_util > float(params['cpus'])):
                raise Exception('Incorrect max_util')

            tg = tasks.TaskGenerator(period=periods, util=utils)
            ts = tg.make_task_set(max_tasks = None, max_util=max_util, squeeze=True)
            ts = [t for t in ts if t.cost > 0]
            #print ('#%d tasks' % len(ts))
            return ts
        else:
            return super(RUNGenerator, self)._create_taskset(params, periods, utils, float(params['cpus']))

    @staticmethod
    def worst_fit(items, bins, capacity=Fraction(1,1), weight=id, misfit=ignore, empty_bin=list):
        sets = [empty_bin() for _ in xrange(0, bins)]
        sums = [Fraction() for _ in xrange(0, bins)]
        for x in items:
            c = weight(x)
            # pick the bin where the item will leave the most space
            # after placing it, aka the bin with the least sum
            candidates = [s for s in sums if s + c <= capacity]
            if candidates:
                # fits somewhere
                i = sums.index(min(candidates))
                sets[i] += [x]
                sums[i] += c
            else:
                misfit(x)
        return sets

# =================================================================================================
# =================================================================================================
# =================================================================================================
# =================================================================================================

class RUNGeneratorRes(RUNGenerator):

    def __init__(self, params={}, template=[TP_RUN_TASK_RES]) :
        super(RUNGeneratorRes, self).__init__(template=template, params=params)

    def _create_taskset(self, params, periods, utils, max_util = None):

        paramsRes = [(x in params) for x in ['res_nmb', 'res_weight', 'res_distr', 'max_util', 'cpus']]
        if not all(paramsRes) :
            raise Exception('Some argument missing: res_nmb, res_weight, res_distr, max_util, cpus')

        ''' Generate system with resources '''
        import sys
        import schedRUN.model.SystemResourceGenerator as srg

        rd = float(params['res_distr'])
        rw = float(params['res_weight'])
        rn = int(params['res_nmb'])
        ul = float(params['max_util'])
        cl = int(params['cpus'])

        tg = srg.SystemResourcesGenerator(periodDistr=periods,
                                                  utilDistr=utils, resDistr=rd, resWeight=rw, resNumber=rn,
                                                  reqNumber=1, utilLimit=ul, cpuLimit=cl)
        ts = tg.generateTaskSetLinear()

        return ts

    def _custom_distribute(self, ts, collaborative, res_number):

        collts = sorted(ts, key=lambda x: x.cost, reverse=True)
        last = int(round(len(collts)*collaborative))
        collts = collts[:last]
        modtasks = len(collts)%res_number
        taskpergroup = (len(collts)-modtasks)/res_number
        for r in range(0, res_number):
            res_weight = random.randint(1,10)
            group = collts[:taskpergroup]
            collts = collts[taskpergroup:]
            if modtasks > 0:
                group.append(collts[0])
                collts = collts[1:]
                modtasks = modtasks -1
            res_len = max(1, int(round(group[-1].cost*res_weight/100.0)))
            for t in group:
                t.resmodel[r].add_write_request(res_len)


    def _create_taskset_from_file(self, params, res_number, folderpath, collaborative):
        ts = []

        """ read a taskset in sched.py done (-S option included) """
        with open (folderpath+"/sched.py", 'r') as f:
            index = 0
            for line in f:
                elements = line.split()
                c = int(elements[4])
                p = int(elements[5])
                temp = SporadicTask(c, p, p)
                temp.id = index
                index = index + 1
                ts.append(temp)
        """ distribute resources """
        resources.initialize_resource_model(ts)
        ts.sort(key=lambda x:x.cost, reverse=True)
        self._custom_distribute(ts, collaborative, res_number)

        """ create the params from params.py file """
        temp = {}
        with open (folderpath+"/params.py", 'r') as f:
            temp = eval(f.read())
        for key in temp:
            params[key] = temp[key]
        """ adding RES parameters """
        params['cpus'] = int(params['cpus'])
        params['res_nmb'] = res_number
        params['res_distr'] = collaborative
        params['res_weight'] = 0
        return ts

    def getHelper(self, resIds, taskset) :
        from schedRUN.schedulability.schedulabilityRUN import SchedulabilityTestRUN 
        return SchedulabilityTestRUN(resIds, taskset)

    def _perform_first_packing(self, taskset, cpus, params) :

        helper = self.getHelper(range(0, int(params['res_nmb'])), taskset)
        isSchedulable = helper.isSchedulable(int(params['cpus']))

        if not isSchedulable :
            raise Exception('Unfeasible Taskset with RUNRSP')

        params['final_util'] = "{0:f}".format(helper.getFinalUtilization())

        firstLevelServers = helper.getServers()
        new_taskset = []
        for server in firstLevelServers :
            newFixedRateTask = FixedRateTask(
                            exec_cost = server['cost'],
                            period    = server['period'],
                            deadline  = server['period'],
                            id        = self.server_count,
                            server    = None,
                            level     = 0)
            for t in server['tasks'] :
                t.server = self.server_count
                newFixedRateTask.children.append(t)

            new_taskset.append(newFixedRateTask)
            self.server_count += 1

        """ We know for sure that the taskset is schedulable, but it can be that
        the slack of the system is too big (the system can afford to have one
        or more unused processors). We manage accordingly such slack and reduce
        the number of necessary cpu to run the system. """
        systemUtilization = sum([Fraction(x.cost, x.period) for x in new_taskset])
        necessaryCPUs = int(math.ceil(float(systemUtilization.numerator)/systemUtilization.denominator))
        unused_capacity = Fraction(necessaryCPUs,1) - systemUtilization
        new_taskset.sort(key=lambda x: x.utilization(), reverse=True)
        self._distribuite_slack(new_taskset, unused_capacity)

        self._dual(new_taskset)

        return new_taskset


# =================================================================================================
# =================================================================================================
# =================================================================================================
# =================================================================================================

class RUNGeneratorMrsP(RUNGeneratorRes):

    def __init__(self, params={}, template=[TP_RUN_TASK_RES]) :
        super(RUNGeneratorMrsP, self).__init__(template=template, params=params)

    def getHelper(self, resIds, taskset) :
        from schedRUN.schedulability.schedulabilityRUN import schedulabilityMrsP_OBT 
        return schedulabilityMrsP_OBT(resIds, taskset)


# =================================================================================================
# =================================================================================================
# =================================================================================================
# =================================================================================================

class RUNGeneratorSBLP_OBT(RUNGeneratorRes):

    def __init__(self, params={}, template=[TP_RUN_TASK_RES]) :
        super(RUNGeneratorSBLP_OBT, self).__init__(template=template, params=params)

    def getHelper(self, resIds, taskset) :
        from schedRUN.schedulability.schedulabilityRUN import SchedulabilityTestSBLP_OBT 
        return SchedulabilityTestSBLP_OBT(resIds, taskset)

