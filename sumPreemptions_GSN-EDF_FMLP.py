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
                      default=("/home/ricardo/litmus/experiment-scripts/run-gsn-edf/"))

  parser.add_option('-i', '--input-dir', dest='input_dir',
                      help='directory for data input',
                      default=("/home/ricardo/litmus/experiment-scripts/run-gsn-edf/"))

  parser.add_option('-f', '--out-file', dest='out_file',
                      help='name of the file for output',
                      default=("sum-preemptions-gsn-edf"))

  return parser.parse_args()

def main() :
  opts, _ = parseArgs()

  pasta = opts.input_dir
  diretorios = [os.path.join(pasta, nome) for nome in os.listdir(pasta)]

  for diretorio in diretorios:

    arquivos = [os.path.join(diretorio, nome) for nome in os.listdir(diretorio)]
    statsName = diretorio.split('/')[len(diretorio.split('/'))-1]
    schedFiles = [arq for arq in arquivos if arq.lower().endswith('stats_'+statsName+'.txt')]

    for schedFile in schedFiles:
      numRegistros = 0
      qtdPreempcoes = 0
      qtdMigracoes = 0
      with open(schedFile, 'r') as sched_file:
        for line in sched_file.readlines():
          if line.startswith("#"):
            continue
          numRegistros += 1
          lineSplit = line.split(",")
          qtdPreempcoes += int(lineSplit[9].strip())
          qtdMigracoes += int(lineSplit[10].strip().replace('\n',''))
      with open('%s/preemptions_migrations.txt' % (pasta), 'a') as outFile:
        outFile.write(schedFile+'\n')
        outFile.write('Preempções: {:>9d}\n'.format(qtdPreempcoes))
        outFile.write('Migrações: {:>9d}\n'.format(qtdMigracoes))
        outFile.write('Registros: {:>9d}\n'.format(numRegistros))
        outFile.write('Preempções Avg: {:>8.5f}\n'.format(float(qtdPreempcoes)/float(numRegistros)))
        outFile.write('Migrações Avg: {:>8.5f}\n'.format(float(qtdMigracoes)/float(numRegistros)))
          
if __name__ == '__main__':
  main()
