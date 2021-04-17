#!/usr/bin/env python
'''
Created on 25/lug/2013

@author: Davide Compagnin
'''

import sys
from decimal import Decimal
import json
import math
import re
import os
from fractions import gcd
from optparse import OptionParser

DEFAULTS = {'cpus'        : '4',
            'prog'        : 'rtspin',
            'heuristic'   : 'worst-fit',
            'in'          : 'sched.py',
            'out'         : 'tree.json'
}

def ignore(_):
    pass

def parse_args():
    parser = OptionParser("usage: %prog [options]")

    parser.add_option('-o', '--out-file', dest='out_file',
                      help='file for data output',
                      default=("%s/%s"% (os.getcwd(), DEFAULTS['out'])))
    parser.add_option('-i', '--in-file', dest='in_file',
                      help='file for data input',
                      default=("%s/%s"% (os.getcwd(), DEFAULTS['in'])))
    parser.add_option('-e', '--heuristic', dest='heuristic',
                      help='heuristic',
                      default=("%s"% DEFAULTS['heuristic']))
    parser.add_option('-p', '--processors', dest='cpus',
                      help='number of processors',
                      default=(DEFAULTS['cpus']))

    return parser.parse_args()

class PeriodicTask(object):
    def __init__(self, exec_cost, period, id=None):
        self.cost = exec_cost
        self.period = period
        self.id = id
        
    def utilization(self):
        return Decimal(self.cost) / Decimal(self.period)

class FixedRateTask(PeriodicTask):
    
    def __init__(self, exec_cost, period, id=None, server=None, level=-1):
        super(FixedRateTask,self).__init__(exec_cost, period, id)
        self.server = server
        self.level = level
        self.children = []
        self.parent = None
        
    def dual_utilization(self):
        return Decimal(1) - self.utilization()
    
    def get_children(self):
        return self.children

def aggregate(task_list, server, level):
    exec_cost = 0
    period = 1
    for t in task_list:
        exec_cost = (exec_cost * t.period) + (period * t.cost)
        period = period * t.period
    task_gcd = gcd(exec_cost, period)
    exec_cost /= task_gcd
    period /= task_gcd
    new_task = FixedRateTask(exec_cost, #period - exec_cost, 
                             period,
                             server, 
                             None, 
                             level)
    for t in task_list:
        t.parent = new_task
        t.server = server
        new_task.children.append(t)
    return new_task

def dual(taskset):
    for t in taskset:
        t.cost = t.period - t.cost
        
def worst_fit(items, bins, capacity=Decimal(1), weight=lambda x: x.utilization(), misfit=ignore, empty_bin=list):
    sets = [empty_bin() for _ in xrange(0, bins)]
    sums = [Decimal(0) for _ in xrange(0, bins)]
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

def best_fit(items, bins, capacity=Decimal(1), weight=lambda x: x.utilization(), misfit=ignore, empty_bin=list):
    sets = [empty_bin()  for _ in xrange(0, bins)]
    sums = [Decimal(0) for _ in xrange(0, bins)]
    for x in items:
        c = weight(x)
        # find the first bin that is sufficiently large
        idxs = range(0, bins)
        idxs.sort(key=lambda i: sums[i], reverse=True)
        for i in idxs:
            if sums[i] + c <= capacity:
                sets[i] += [x]
                sums[i] += c
                break
        else:
            misfit(x)
    return sets

def first_fit(items, bins, capacity=Decimal(1), weight=lambda x: x.utilization(), misfit=ignore,
              empty_bin=list):
    sets = [empty_bin() for _ in xrange(0, bins)]
    sums = [Decimal(0) for _ in xrange(0, bins)]
    for x in items:
        c = weight(x)
        for i in xrange(0, bins):
            if sums[i] + c <= capacity:
                sets[i] += [x]
                sums[i] += c
                break
        else:
            misfit(x)

    return sets

def next_fit(items, bins, capacity=Decimal(1), weight=lambda x: x.utilization(), misfit=ignore,
             empty_bin=list):
    sets = [empty_bin() for _ in xrange(0, bins)]
    cur  = 0
    s  = Decimal(0)
    for x in items:
        c = weight(x)
        while s + c > capacity:
            s = Decimal(0)
            cur += 1
            if cur == bins:
                misfit(x)
                return sets
        sets[cur] += [x]
        s += c
    return sets

def distribuite_slack(ts, slack):
    ts.sort(key=lambda x: x.utilization(), reverse=True)
    i = 0
    unused_capacity = slack
    while (unused_capacity > Decimal(0)) and (i < len(ts) + 100):
        t = ts[i]
        if (t.dual_utilization() <= unused_capacity):
            unused_capacity -= t.dual_utilization() 
            t.cost = t.period
        else:
            tmp_util = t.utilization()
            t.cost += int(unused_capacity * Decimal(t.period))
            unused_capacity -= (t.utilization() - tmp_util)
        i += 1
        
    if (unused_capacity > Decimal(0)):
        raise Exception('Still capacity unused: ' + str(unused_capacity))

def convert_data(data):
    '''Convert a non-python schedule file into the python format'''
    regex = re.compile(
        r"(?P<PROC>^"
            r"(?P<HEADER>/proc/[\w\-]+?/)?"
            r"(?P<ENTRY>[\w\-\/]+)"
              r"\s*{\s*(?P<CONTENT>.*?)\s*?}$)|"
        r"(?P<TASK>^"
            r"(?:(?P<PROG>[^\d\-\s][\w\.]*?) )?\s*"
            r"(?P<ARGS>[\w\-_\d\. \=]+)\s*$)",
        re.S|re.I|re.M)

    procs = []
    tasks = []

    for match in regex.finditer(data):
        if match.group("PROC"):
            header = match.group("HEADER") or "/proc/litmus/"
            loc  = "{}{}".format(header, match.group("ENTRY"))
            proc = (loc, match.group("CONTENT"))
            procs.append(proc)
        else:
            prog = match.group("PROG") or DEFAULTS['prog']
            spin = (prog, match.group("ARGS"))
            tasks.append(spin)

    return {'proc' : procs, 'task' : tasks}

def serialize(task):
    obj = {
        'id': task.id,
        'cost': task.cost,
        'period': task.period,
        'level' : task.level,
        'children': []
    }
    for ch in task.get_children():
        obj['children'].append(serialize(ch))
        
    return obj

HEURISTICS = {
              'worst-fit' : worst_fit,
              'best-fit'  : best_fit,
              'next-fit'  : next_fit,
              'first-fit' : first_fit,
}

class Reductor(object):
    def __init__(self, cpus=4, heuristic='worst-fit', in_file='sched.py', out_file='tree.json'):
        self.ts = []
        self.cpus = cpus
        if heuristic in HEURISTICS:
            self.heuristic = HEURISTICS[heuristic]
        self.in_file = in_file
        self.out_file = out_file
        self.misfits = 0
        self.servers = 0
        self.unit_server = None
        self.level = 0
        
    def _misfit(self, x):
        #self.misfit += x.dual_utilization()
        self.misfits += 1
    
    def reduce(self):
        #parsing schedule.py file
        with open(self.in_file, 'r') as f:
            data = f.read().strip()
        
        try:
            schedule = eval(data)
        except:
            schedule = convert_data(data)
        
        for task_conf in schedule['task']:
            
            (task, args) = (task_conf[0], task_conf[1])
            real_args = args.split()
            #Get two last arguments as cost and period respectively
            index = len(real_args) - 2
            self.ts.append(FixedRateTask(int(real_args[index + 0]), int(real_args[index + 1])))
        
        n_tasks = len(self.ts)
        #n_tasks may be less than cpus
        if (n_tasks < self.cpus):
            print 'Info: cpus has changed from {0} to {1}'.format(unicode(self.cpus),unicode(n_tasks))
            self.cpus = n_tasks
        
        tot_util = sum([t.utilization() for t in self.ts])
        print 'Info: total utilization {0}'.format(tot_util)
        
        unused_capacity = Decimal(self.cpus) - tot_util
        if (unused_capacity < Decimal(0)):
            print 'Error: unfeasible taskset'.format(tot_util)
            raise Exception('Unfeasible Taskset')
        
        new_ts = self._pack(self.ts, self.cpus)
        new_ts.sort(key=lambda x: x.utilization(), reverse=True)
        distribuite_slack(new_ts, unused_capacity)
        dual(new_ts)
        self.level = 1
        unit_server = self._reduce(new_ts)
        
        if (len(unit_server) != 1):
            print 'Error: not correctly reduced'.format(tot_util)
            raise Exception('not correctly reduced')
    
        if (unit_server[0].utilization() != Decimal(0) and unit_server[0].utilization() != Decimal(1)):
            print 'Error: not correctly reduced'.format(tot_util)
            raise Exception('not correctly reduced')
        
        self.unit_server = unit_server[0]
        print 'Info: tree level {0}'.format(unicode(self.unit_server.level - self.unit_server.utilization()))
        
    def serialize(self):
        if (self.unit_server != None):
            serialized = serialize(self.unit_server)
            with open(self.out_file, 'wa') as f:
                json.dump(serialized, f, indent=4)
        else:
            print 'Error: no unit-server'
        
    def _pack(self, taskset, cpus):
        self.misfits = 0
        n_bins = cpus
        
        taskset.sort(key=lambda x: x.utilization(), reverse=True)
        
        bins = self.heuristic(taskset, 
                          n_bins, 
                          Decimal(1), 
                          lambda x: x.utilization(), 
                          self._misfit)
        while (self.misfits > 0):
            #n_bins += math.ceil(self.misfit)
            n_bins += 1 #self.misfit
            self.misfits = 0
            bins = self.heuristic(taskset, 
                              n_bins, 
                              Decimal(1), 
                              lambda x: x.utilization(), 
                              self._misfit)    
        servers = []
        for item in bins:
            tmp_server = aggregate(item, self.servers, self.level)
            servers.append(tmp_server)
            self.servers += 1
        
        self.misfits = 0
        return servers
    
    def _reduce(self, taskset):
        utilization = sum([t.utilization() for t in taskset])
        new_taskset = self._pack(taskset, int(math.ceil(utilization)))
        dual(new_taskset)
        if len(new_taskset) == 1:
        #if (utilization == Decimal(1) or utilization == Decimal(0)):
            return new_taskset
        else:
            self.level += 1
            return self._reduce(new_taskset)
        
def main():
    opts, args = parse_args()
    
    reductor = Reductor(int(opts.cpus.strip()), opts.heuristic, opts.in_file, opts.out_file)
    
    reductor.reduce()
    reductor.serialize()
    
if __name__ == '__main__':
    main()