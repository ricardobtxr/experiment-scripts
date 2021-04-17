#!/usr/bin/env python
import json
import os
import ast
from optparse import OptionParser

def parseArgs () :
  parser = OptionParser("usage: %prog [options]")

  parser.add_option('-o', '--out-dir', dest='out_dir',
                      help='directory for data output',
                      default=("/home/ricardo/Dropbox/Mestrado/servers-overhead/"))

  parser.add_option('-i', '--input-dir', dest='input_dir',
                      help='directory for data input',
                      default=("/home/ricardo/Dropbox/Mestrado/servers-overhead/exps-sblp/"))

  parser.add_option('-f', '--out-file', dest='out_file',
                      help='name of the file for output',
                      default=("exps-sblp"))

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
        with open(schedFile, 'r') as sched_file:
          dictServers = {}
          lineList = sched_file.readlines()
          for line in lineList:
            fields = line.split()
            if fields[1] in dictServers:
              dictServers[fields[1]] = dictServers[fields[1]]+1
            else:
              dictServers[fields[1]] = 1
          with open(opts.out_dir+opts.out_file+'_servers.csv', 'a+') as f:
            for x in dictServers:
              f.write('{}\n'.format(dictServers[x]))
            f.close
          sched_file.close
      num = num + 1

if __name__ == '__main__':
  main()
