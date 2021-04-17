#!/usr/bin/env python

import sys
import math
import numpy as np

def mergeSamples(filename):
  maxvalue = 0;
  sumvalue = 0;
  count = 0;
  table={};
  with open(filename, 'r') as f:
    for line in f:
      value = int(line);
      index = int(math.floor(value/500.0));
      if index not in table.keys():
        table[index] = 0;
      table[index] += 1;
      sumvalue += value;
      count += 1;
      if value > maxvalue:
        maxvalue = value;
  with open('merge'+filename, 'w') as f:
    index = int(math.floor(maxvalue/500.0))+1;
    result = [0]*(index);
    for k in table.keys():
      result[k] = table[k];
    for i in range(0, index):
      f.write(str(i*500) + ", " + str(result[i])+"\n");

def main():
  mergeSamples("outputSCHED");
  #mergeSamples("outputLOCK");
  #mergeSamples("outputUNLOCK");

if __name__ == '__main__':
    main()
