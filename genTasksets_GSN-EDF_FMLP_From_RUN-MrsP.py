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

  return parser.parse_args()

def main() :
  opts, _ = parseArgs()

  pasta = opts.input_dir
  diretorios = [os.path.join(pasta, nome) for nome in os.listdir(pasta)]

  for diretorio in diretorios:
    caminhos = [os.path.join(diretorio, nome) for nome in os.listdir(diretorio)]
    
    num = 0

    for caminho in caminhos:

      if num > 99:
        break
        
      arquivos = [os.path.join(caminho, nome) for nome in os.listdir(caminho)]
      schedFiles = [arq for arq in arquivos if arq.lower().endswith("sched.py")]

      for schedFile in schedFiles:
        with open(schedFile, 'rw+') as sched_file:
          linesOut = []
          for line in sched_file.readlines():
            lineTrans = line.replace('RUN', 'GSN-EDF')
            lineTrans = re.sub('-S [0-9]  ', '', lineTrans)
            linesOut.append(lineTrans)
          sched_file.seek(0)          
          for lineOut in linesOut:
            sched_file.write(lineOut)
          sched_file.truncate()

if __name__ == '__main__':
  main()
