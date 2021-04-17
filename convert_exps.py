#!/usr/bin/env python
'''
Created on 25/giu/2013

@author: davide
'''
import sys
import run_exps
import schedcat.model.tasks as tasks

def _pack(taskset, cpus):
  # Partition using worst-fit for most even distribution
  utils = [0]*cpus
  tasks = [0]*cpus
  for t in taskset:
    t.cpu = utils.index(min(utils))
    utils[t.cpu] += t.utilization()
    if utils[t.cpu] > 1.0:
      print 'Capacity exceeded on bin {0}'.format(t.cpu)
    tasks[t.cpu] += 1

def main():

  if len(sys.argv) != 3:
    raise Exception("Invalid parameters")

  fname = sys.argv[1]
  cpus = int(sys.argv[2])

  with open(fname, 'r') as f:
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

    if '-p'in real_args:
      index = real_args.index('-p') + 2

    ts.append(tasks.SporadicTask(int(real_args[index + 0]), int(real_args[index + 1])))

  ts.sort(key=lambda x: x.utilization(), reverse=True)
  _pack(ts, cpus)
  with open('out_sched.py', 'w') as out_file:
    for t in ts:
      out_file.write("-p {0} {1} {2}\n".format(t.cpu, t.cost, t.period))

if __name__ == '__main__':
  main()