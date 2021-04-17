#!/usr/bin/env python
import json
import os
import ast
from optparse import OptionParser

def parseArgs () :
  parser = OptionParser("usage: %prog [options]")

  parser.add_option('-o', '--out-dir', dest='out_dir',
                      help='directory for data output',
                      default=("/home/ricardo/litmus/experiment-scripts/data/"))

  parser.add_option('-i', '--input-dir', dest='input_dir',
                      help='directory for data input',
                      default=("/home/ricardo/litmus/experiment-scripts/exps-sblp-obt/"))

  parser.add_option('-f', '--out-file', dest='out_file',
                      help='name of the file for output',
                      default=("sblp-obt"))

  return parser.parse_args()

def main() :
  opts, _ = parseArgs()

  pasta = opts.input_dir
  diretorios = [os.path.join(pasta, nome) for nome in os.listdir(pasta)]

  for diretorio in diretorios:
    caminhos = [os.path.join(diretorio, nome) for nome in os.listdir(diretorio)]

    for caminho in caminhos:

      arquivos = [os.path.join(caminho, nome) for nome in os.listdir(caminho)]
      schedFiles = [arq for arq in arquivos if arq.lower().endswith("sched.py")]

      for schedFile in schedFiles:
        with open(schedFile, 'r') as sched_file:
          dictServers = {}
          lineList = sched_file.readlines()
          for line in lineList:
            fields = line.split()
            dictServers[fields[1]] = 1
          with open(opts.out_dir+opts.out_file+'_servers.csv', 'a+') as f:
            f.write('{}\n'.format(len(dictServers)))
            f.close
          sched_file.close

if __name__ == '__main__':
  main()
