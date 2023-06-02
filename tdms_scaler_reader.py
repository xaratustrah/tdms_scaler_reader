#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Reading scalar channels in TDMS files

2023 Xaratustrah
Jun 2023 David
'''

import numpy as np
import os, sys
import argparse
from loguru import logger
from nptdms import TdmsFile


def read_tdms_scaler(filename, channel=5):
    chan = f'{channel:02}'
    tdms_file = TdmsFile.read(filename)
    dcct_channel = tdms_file['SCData'][f'CHANNEL_{chan}']
    timestamp_channel = tdms_file['SCTimestamps']['TimeStamp']
    b = dcct_channel[:]
    n=1024
    delta_cnt = (b[(n-1):] - b[:-(n-1)])[::n]
    delta_t = np.diff(timestamp_channel[:]) / np.timedelta64(1, 's')
    try:
        return timestamp_channel[0:-1], delta_cnt[0:-1] / delta_t
    except ValueError: #operands could not be broadcast together with shapes (249,) (250,), when file is not "complete" 
        return timestamp_channel[0:-1], delta_cnt[:] / delta_t


def main():
   
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='+', type=str,
                        help='Name of the input files.')
    parser.add_argument('-o', '--outdir', type=str, default='.',
                        help='output directory.')
    parser.add_argument('-n', '--outfilename', type=str, default='results',
                        help='output filename.')
    parser.add_argument('-c', '--channel', type=int, default=5,
                        help='TDMS channel')

    args = parser.parse_args()
    
    logger.info(f'Using channel {args.channel}')
    
    if args.outdir:
        # handle trailing slash properly
        outfilepath = os.path.join(args.outdir, '')

    logger.remove()
    logger.add(sys.stdout, level='INFO')
    logger.add(outfilepath + f'{parser.prog}.log', level='DEBUG')

    tt = []
    ff = []
    
    for file in args.filenames:
        logger.info(f'Processing file {file}')
        try:
            t, f = read_tdms_scaler(file, channel=args.channel)
            tt.extend(t)
            ff.extend(f)
            
        except(ValueError):
            logger.warning(f'Invalid data in {file}')
            continue
        
        except(EOFError, KeyboardInterrupt):
            logger.error('User cancelled. Aborting...')
            sys.exit()
    
    tta = np.asarray(tt)
    ffa = np.asarray(ff)
    
    logger.info(f'Saving results.')
    np.savez_compressed(f'{outfilepath}/{args.outfilename}', t=tta, f=ffa)

# ----------------------------------------

if __name__ == '__main__':
    main()
