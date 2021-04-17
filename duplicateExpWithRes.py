#!/usr/bin/env python

from optparse import OptionParser
from gen.run_generators import RUNGeneratorRes
import os
import sys

def parse_args():
    parser = OptionParser("usage: %prog [options] [files...] "
                          "[generators...] [param=val[,val]...]")

    parser.add_option('-o', '--out-dir', dest='out_dir',
                      help='directory for data output',
                      default=("%s/%s"% (os.getcwd(), "RESEXPS")))

    return parser.parse_args()

def main():
  opts, inFolders = parse_args()
  distr = 0.8
  res_number = 3
  
  if not os.path.exists(opts.out_dir):
    os.mkdir(opts.out_dir)
  if opts.out_dir[-1] != '/':
    opts.out_dir = opts.out_dir+'/'
  
  for folder in inFolders:
    done = False
    trial = 0
    while (not done and trial < 50):
      try:
        if folder[-1] == '/':
          folder = folder[:-1]
        foldername = folder.strip().split('/')[-1]
        out_dir = opts.out_dir+foldername+"_res="+str(distr)+"/"
        if not os.path.exists(out_dir):
          os.mkdir(out_dir)
        
        
        generator = RUNGeneratorRes()
        generator.out_dir=out_dir

        params = {}

        ts = generator._create_taskset_from_file(params, res_number, folder, distr)

        generator._customize(ts, params)
        generator._write_schedule(dict(params.items() + [('task_set', ts)]))
        generator._write_params(params)
        done = True
      except:
        trial += 1
        continue

if __name__ == "__main__":
  main()
