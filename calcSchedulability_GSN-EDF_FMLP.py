#!/usr/bin/env python
import json
import os
import ast
import re
from optparse import OptionParser

def parseArgs () :
  parser = OptionParser("usage: %prog [options]")

  parser.add_option('-o', '--out-dir', dest='out_dir',
                      help='directory for data output',
                      default=("/home/ricardo/litmus/experiment-scripts/exps-gsn-edf/"))

  parser.add_option('-i', '--input-dir', dest='input_dir',
                      help='directory for data input',
                      default=("/home/ricardo/litmus/experiment-scripts/exps-gsn-edf/"))

  parser.add_option('-f', '--out-file', dest='out_file',
                      help='name of the file for output',
                      default=("exps-gsn-edf"))

  parser.add_option('-p', '--processors', dest='processors',
                      help='number of processors',
                      default=int(4))

  return parser.parse_args()

def main() :
  opts, _ = parseArgs()

  pasta = opts.input_dir
  processors = opts.processors
  diretorios = [os.path.join(pasta, nome) for nome in os.listdir(pasta)]

  for diretorio in diretorios:
    caminhos = [os.path.join(diretorio, nome) for nome in os.listdir(diretorio)]
    statsDir = diretorio.split('/')[len(diretorio.split('/'))-1]
    
    for caminho in caminhos:
      
      statsFile = caminho.split('/')[len(caminho.split('/'))-1]
      arquivos = [os.path.join(caminho, nome) for nome in os.listdir(caminho)]
      schedFiles = [arq for arq in arquivos if arq.lower().endswith("sched.py")]

      for schedFile in schedFiles:
        tasks = []
        taskId = 0
        with open(schedFile, 'r') as sched_file:
          for line in sched_file.readlines():
            lineSplit = line.replace('\n','').replace('   ',' ').replace('  ',' ').split(' ')
            if (lineSplit[0] == '-X'):
              tasks.append(JobConfig(taskId, lineSplit[6], lineSplit[7], lineSplit[3], lineSplit[5]))
            else:
              tasks.append(JobConfig(taskId, lineSplit[0], lineSplit[1]))
            taskId += 1
            
        calculator = schedulabilityCalculator(tasks, processors)
        calculator.calcule()
            
        with open('%s/schedulability.txt' % (pasta), 'a') as outFile:
          outFile.write('{initialUtilization:>8.5f}|{inflatedUtilization:>8.5f}|{maxTaskInflated:>8.5f}|{isSchedulable}|{statsName}\n'.format(
            statsName=statsDir+'/'+statsFile,
            initialUtilization=calculator.calculeInitialUtilization(), 
            inflatedUtilization=calculator.calculeInflatedUtilization(), 
            maxTaskInflated=calculator.calculeMaxTaskInflated(),
            isSchedulable=calculator.isSchedulable()))
 
            
class JobConfig(object):
  'Class for manipulating JOB parameters'
  
  def __init__ (self, *args, **kwargs): 
    if len(args) == 5:
      self.initWithResource(args[0], args[1], args[2], args[3], args[4])
    else:
      self.initNoResource(args[0], args[1], args[2])
      
  def initNoResource(self, taskId, wcet, period):
    self.taskId = taskId
    self.wcet = int(wcet)
    self.period = int(period)
    self.resource = None
    self.cs = 0
    self.busyWait = 0
    self.blockNPB = 0

  def initWithResource(self, taskId, wcet, period, resource, cs):
    self.taskId = taskId
    self.wcet = int(wcet)
    self.period = int(period)
    self.resource = resource
    self.cs = int(cs)
    self.busyWait = 0
    self.blockNPB = 0
    
  def getInitialUtilization(self):
    return float(self.wcet) / float(self.period)
  
  def getFinalUtilization(self):
    return float(self.getInflatedWCET()) / float(self.period)
  
  def getTotalBlock(self):
    return self.busyWait + self.blockNPB

  def getInflatedWCET(self):
    return self.wcet + self.getTotalBlock()
  
  
class schedulabilityCalculator(object):
  'Class for calculating schedulability'
  
  def __init__ (self, tasks, processors):
    self.tasks = tasks
    self.processors = processors
  
  def calcule(self):
    for task in self.tasks:
      if not task.resource is None:
        task.busyWait = self.calculeBusyWait(task) 
    for task in self.tasks:
      if not task.resource is None:
        task.blockNPB = self.calculeNPBlock(task)
        
  '''Must be called after calcule() method
  '''
  def calculeInflatedUtilization(self):
    inflatedUtilization = float(0)
    for task in self.tasks:
      inflatedUtilization += task.getFinalUtilization() 
    return inflatedUtilization
        
  '''Must be called after calcule() method
  '''
  def calculeInitialUtilization(self):
    utilization = float(0)
    for task in self.tasks:
      utilization += task.getInitialUtilization()
    return utilization

  def isSchedulable(self):
    return (self.calculeInflatedUtilization() <= self.processors - ((self.processors - 1) * self.calculeMaxTaskInflated()))
        
  '''Must be called after calcule() method
  '''
  def calculeMaxTaskInflated(self):
    inflatedUtilization = float(0)
    for task in self.tasks:
      inflatedUtilization = max(inflatedUtilization, task.getFinalUtilization())
    return inflatedUtilization
        
  def calculeBusyWait(self, task):
    maxBlockTime = 0
    count = 0
    if task.resource is None:
      return 0
    for task_block in self.tasks:
      if task.taskId != task_block.taskId and task.resource == task_block.resource:
        count += 1
        if task_block.cs > maxBlockTime:
          maxBlockTime = task_block.cs
    return min(self.processors - 1, count) * maxBlockTime
  
  '''Must be called after all tasks have seted busyWait property
  '''
  def calculeNPBlock(self, task):
    maxNPBlock = 0
    if task.resource is None:
      return 0
    for task_block in self.tasks:
      if task.taskId != task_block.taskId and task.resource == task_block.resource and task.period < task_block.period:
        maxNPBlock = max(maxNPBlock, task_block.cs + task_block.busyWait)
    return maxNPBlock 
  
if __name__ == '__main__':
  main()
  
  