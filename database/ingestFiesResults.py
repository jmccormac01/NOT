"""
Script to ingest the results files from fiespipe.py
This is a copy of the ingestCafeResults.py script

Results file has the following structure:
    0-  Object name
    1-  MBJD
    2-  RV
    3-  error in RV
    4-  Bisector span
    5-  error in bisector span
    6-  instrument
    7-  pipeline
    8-  resolving power
    9-  Efective Temperture
    10- log(g)
    11- [Fe/H]
    12- v*sin(i)
    13- value of the continuum normalized CCF at it lowest point
    14- standard deviation of the gaussian fitted to the CCF
    15- Exposure time
    16- Signal to noise ratio at ~5150A
    17- path to the CCF plot file
"""
import os
import sys
import argparse as ap
import pymysql

# pylint: disable = invalid-name

def argParse():
    """
    Parse the command line arguments
    """
    parser = ap.ArgumentParser()
    parser.add_argument('--ingest',
                        help='Ingest the results to the database',
                        action='store_true')
    return parser.parse_args()

RESULTS_FILE = 'results.txt'

if __name__ == '__main__':
    args = argParse()
    db = pymysql.connect(host='localhost',
                         db='eblm',
                         password='mysqlpassword')
    if os.path.exists(RESULTS_FILE):
        night = os.getcwd().split('/')[-2].split('_')[1]
        night = "{}-{}-{}".format(night[:4], night[4:6], night[6:])
        print(night)
        f = open(RESULTS_FILE).readlines()
        for line in f:
            ls = line.rstrip().split()
            if len(ls) != 18:
                print('ERROR: Wrong number of columns in results.txt')
                sys.exit(1)
            obj = ls[0]
            if obj.startswith('1SWASP'):
                swasp_id = obj
            else:
                swasp_id = None
            bjd_mid = ls[1]
            mask_velocity = ls[2]
            mask_velocity_err = ls[3]
            bisector = ls[4]
            bisector_err = ls[5]
            mask_ccf_height = ls[13]
            mask_ccf_fwhm = ls[14]
            snr_5150 = ls[16]
            pdf_name = ls[17].split('/')[-1]
            image_id = '{}.fits'.format(pdf_name.split('.')[0])
            mask = pdf_name.split('.')[-2].split('_')[-1]
            qry = """
                REPLACE INTO eblm_fies (
                    image_id, swasp_id, object_name,
                    bjd_mid, mask, mask_velocity,
                    mask_velocity_err, mask_ccf_height,
                    mask_ccf_fwhm, bisector,
                    bisector_err, snr_5150, night, analyse
                    )
                VALUES (
                    '{}', '{}', '{}', {}, '{}', {},
                    {}, {}, {}, {}, {}, {}, '{}', 1
                    )
                """.format(image_id, swasp_id, obj,
                           bjd_mid, mask, mask_velocity,
                           mask_velocity_err, mask_ccf_height,
                           mask_ccf_fwhm, bisector,
                           bisector_err, snr_5150, night)
            print(qry)
            if args.ingest:
                with db.cursor() as cur:
                    cur.execute(qry)
                    db.commit()
    else:
        print('{} not found...'.format(RESULTS_FILE))
