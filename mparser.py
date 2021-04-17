#!/usr/bin/env python

import multiprocessing
import os
import glob
import sys
from optparse import OptionParser
import traceback
import re

import unit_trace
from unit_trace import ucheck
from unit_trace import ucheck2
from unit_trace import trace_reader


def parseArgs () :
    parser = OptionParser("usage: %prog [options] [data folders...]")

    parser.add_option('-o', '--out-dir', dest='out_dir',
                      help='directory for data output',
                      default=("%s/%s"% (os.getcwd(), 'parsed')))
    parser.add_option('-n', '--num-processes', default=1, type='int', dest='procs',
                      help='number of processed used for parsing')
    return parser.parse_args()

def parseData(folder_output) :
  folder, output = folder_output
  traces = glob.glob(folder+"/st*bin")
  specs = re.match(r'.*/sched=RUN_(.*)', folder)
  outputfile = output+"/parsed_"+specs.group(1)
  stream = trace_reader.trace_reader(traces)
  ucheck2.startcount(stream, folder, outputfile)
  return True

def removeLastSlash(x) :
  if x.endswith('/'):
    return x[:-1]
  return x

def main () :

  opts, folders = parseArgs()
  datafolders = map(removeLastSlash, folders)
  print "OPTS: ", opts
  print len(datafolders)
  
  pool = multiprocessing.Pool(processes=opts.procs)
  args = zip(folders, [opts.out_dir]*len(folders))
  enum = pool.imap_unordered(parseData, args)
  try :
    for result in enumerate(enum):
      print "Parsed file "+str(result)
    
    pool.close()
  except:
    pool.terminate()
    traceback.print_exc()
    raise Exception("Failed parsing!")
  finally:
    pool.join()
 
if __name__ == "__main__" :
  main()
