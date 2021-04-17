'''
Created on 07/giu/2013

@author: davide
'''
import schedcat.model.tasks as tasks
from decimal import Decimal
from fractions import Fraction

class FixedRateTask(tasks.SporadicTask):
    
    def __init__(self, exec_cost, period, deadline=None, id=None, server=None, level=-1):
        super(FixedRateTask,self).__init__(exec_cost, period, deadline, id)
        self.server = server
        self.level = level
        self.children = []
        self.parent = None
        
    def dual_utilization(self):
        return Decimal(1) - self.utilization()
    
    def dual_util_frac(self):
        return Fraction(self.period - self.cost, self.period)
    
    def utilization(self):
        return Decimal(self.cost) / Decimal(self.period)
    
    def util_frac(self):
        return Fraction(self.cost, self.period)
    
    def get_children(self):
        return self.children
    
    @staticmethod
    def _aggregate(task_list, server, level):
        
        tot_util = Fraction()
        for t in task_list:
            tot_util += t.util_frac()
        new_task = FixedRateTask(tot_util.numerator, 
                                 tot_util.denominator, 
                                 tot_util.denominator, 
                                 server, 
                                 None,
                                 level)
        
        for t in task_list:
            t.parent = new_task
            t.server = server
            new_task.children.append(t)
        return new_task
    
    @staticmethod
    def serialize(task):
        obj = {
            'id': task.id,
            'cost': task.cost,
            'period': task.period,
            'level' : task.level,
            'children': []
        }
        if (task.level > 0):
            for ch in task.get_children():
                obj['children'].append(FixedRateTask.serialize(ch))
            
        return obj
        
        
    