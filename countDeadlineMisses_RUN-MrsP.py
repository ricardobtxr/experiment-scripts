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
                      default=("/home/ricardo/litmus/experiment-scripts/run-sblp/"))

  parser.add_option('-i', '--input-dir', dest='input_dir',
                      help='directory for data input',
                      default=("/home/ricardo/litmus/experiment-scripts/run-sblp/"))

  parser.add_option('-f', '--out-file', dest='out_file',
                      help='name of the file for output',
                      default=("sum-preemptions-sblp"))

  return parser.parse_args()

def main() :
  opts, _ = parseArgs()

  pasta = opts.input_dir
  diretorios = [os.path.join(pasta, nome) for nome in os.listdir(pasta) if not nome.lower().endswith('.txt')]

  for diretorio in diretorios:

    arquivos = [os.path.join(diretorio, nome) for nome in os.listdir(diretorio) if nome.lower().endswith('stats.txt')]
    schedFiles = [arq for arq in arquivos]

    for schedFile in schedFiles:
      jobNo = float(0)
      qtdDeadlines = 0
      period = float(0)
      dlMiss = 0
      with open(schedFile, 'r') as sched_file:
        for line in sched_file.readlines():
          if line.startswith("#"):
            continue
          lineSplit = line.split(",")
          jobNo = float(lineSplit[1].strip())
          period = float(lineSplit[2].strip())
          dlMiss = int(lineSplit[4].strip())
          if dlMiss == 1:
            if (jobNo * period / float(1000000000)) <= float(30):
              qtdDeadlines += 1
      if (qtdDeadlines > 0):
        with open('%s/deadlines_missed.txt' % (pasta), 'a') as outFile:
          outFile.write(schedFile+'\n')
          outFile.write('Deadlines missed: {:>9d}\n'.format(qtdDeadlines))
          
if __name__ == '__main__':
  main()
