#!/usr/bin/env python
'''
Created on 12/lug/2013

@author: davide
'''
import sys
import csv
import numpy as np
import os
from optparse import OptionParser

def_out_file = 'out_stat_overhead.csv'
def_release = 'ft_release.csv'
def_schedule = 'ft_schedule.csv'

def parse_args():
    parser = OptionParser("usage: %prog [options]")
    
    parser.add_option('-o', '--out-file', dest='out_file',
                      help='file for data output',
                      default=("%s/%s" % (os.getcwd(), def_out_file)))
    
    parser.add_option('-r', '--release', dest='ft_release',
                      help='ft release csv file',
                      default=("%s/%s" % (os.getcwd(), def_release)))
     
    parser.add_option('-s', '--schedule', dest='ft_schedule',
                      help='ft schedule csv file',
                      default=("%s/%s" % (os.getcwd(), def_schedule)))

    return parser.parse_args()

def main():
    opts, args = parse_args()
    dirname = os.path.dirname(opts.out_file)
    
    if not os.path.exists(dirname):
        raise Exception(dirname + ' not found')
    
    files = {
             'release': None,
             'schedule': None
    }
    
    if os.path.exists(opts.ft_release):
        files['release'] = opts.ft_release
    if os.path.exists(opts.ft_schedule):
        files['schedule'] = opts.ft_schedule
    
#     files['release'] = [s for s in args if 'release' in s]
#     files['schedule'] = [s for s in args if 'schedule' in s]
    
    data = []
    
    write = False
    
    for k in files.keys():
        if files[k] != None:
            try:  
                with open(files[k], 'rb') as f:
                    tmp_data = []
                    csv_data = csv.reader(f)
                    for row in csv_data:
                        tmp_data.append(long(row[2].strip()))
                    
                    max_value = max(tmp_data)
                    min_value = min(tmp_data)
                    avg_value = np.mean(tmp_data)
                    std_value = np.std(tmp_data)
                    sum_value = sum(tmp_data)
                    
                    data.append(max_value)
                    data.append(min_value)
                    data.append(long(avg_value))
                    data.append(long(std_value))
                    data.append(sum_value)
                    
                    write = True
                    
            except IOError:
                print k + ' file not found!'
        
    if write:
        with open(opts.out_file, 'wb') as f:
            writer = csv.writer(f)
            writer.writerow(data)
    else:
        print 'Nothing to write. You are probably missing some input files.'

if __name__ == '__main__':
    main()