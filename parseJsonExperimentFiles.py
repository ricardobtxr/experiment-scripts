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
            paramFiles = [arq for arq in arquivos if arq.lower().endswith("params.py")]
        
            for paramFile in paramFiles:
                with open(paramFile, 'r') as json_file:
                    contents = json_file.read()
                    data = ast.literal_eval(contents)
                    with open(opts.out_dir+opts.out_file+'_params.py', 'a+') as f:
                        f.write('{}|{}|{}|{}\n'.format(
                            data['res_distr'], 
                            data['res_weight'], 
                            data['max_util'], 
                            data['final_util']))
                        f.close
                    json_file.close
    
if __name__ == '__main__':
    main()
