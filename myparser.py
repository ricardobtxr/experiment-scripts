#!/usr/bin/env python

import sys
import json
import numpy as np

Total = {
  'preemptCount':0,
  'migCount':0,
  'jobsCount':0,
  'missCount':0,
  'minLock':sys.maxint,
  'maxLock':0,
  'minUnlock':sys.maxint,
  'maxUnlock':0
}

def updateTable(dest, source):
  for key in source :
    if key not in dest :
      dest[key] = int(source[key])
    else :
      dest[key] += int(source[key])

def normalizeTable(table) :
  result = []
  keys = table.keys()
  maxValue = max([int(k) for k in keys])
#  result = np.zeros((maxValue+1,), dtype=numpy.int)
  result = [0]*(maxValue + 1)
  for key in table :
    result[int(key)] = int(table[key])
  return result

def toFileSimple (data, filepath) :
  with open(filepath, 'w') as f :
    import json
    json.dump(data, f)
   

def toFile (data, filepath, binsize) :
  output = normalizeTable(data)
  with open(filepath, 'w') as f :
    for i in  xrange(0, len(output)) :
      f.write("{0} {1}\n".format(binsize*i, output[i]))

def main() :
  args = sys.argv
  files = args[1:]
  
  tempLock = {}
  tempUnlock = {}
  tempSpin = {}
  
  for filepath in files :
    with open(filepath) as f :
      data = json.load(f)
      
      Total['preemptCount'] += int(data['preemptCount'])
      Total['migCount'] += int(data['migCount'])
      Total['jobsCount'] += int(data['jobsCount'])
      Total['missCount'] += int(data['missCount'])
      if int(data['minLock']) < Total['minLock'] :
        Total['minLock'] = int(data['minLock'])
      if int(data['maxLock']) > Total['maxLock'] :
        Total['maxLock'] = int(data['maxLock'])
      if int(data['minUnlock']) < Total['minUnlock'] :
        Total['minUnlock'] = int(data['minUnlock'])
      if int(data['maxUnlock']) > Total['maxUnlock'] :
        Total['maxUnlock'] = int(data['maxUnlock'])
      
      updateTable(tempLock, data['tableLock'])
      updateTable(tempUnlock, data['tableUnlock'])
      updateTable(tempSpin, data['tableSpin'])
      
  toFileSimple(Total, "generalData")
  toFile(tempLock, "overheadLock", 500)
  toFile(tempUnlock, "overheadUnlock", 500)
  toFile(tempSpin, "overheadSpin", 1)

if __name__ == '__main__':
    main()
