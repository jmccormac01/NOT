"""
Cycle through all NOT/FIES RVs in DB and phase/plot them
"""
import argparse as ap
from contextlib import contextmanager
import numpy as np
import pymysql
import matplotlib
matplotlib.use('QT5Agg')
import matplotlib.pyplot as plt

# this comes from a quick check on the RV
# standards with CERES
RV_OFFSET = -84

def argParse():
    p = ap.ArgumentParser()
    p.add_argument('--swasp_id',
                   help='Specify a particular object')
    return p.parse_args()

@contextmanager
def openDb():
    with pymysql.connect(host='localhost',
                         db='eblm',
                         password='mysqlpassword') as cur:
        yield cur

def getUniqueFiesObjects():
    swasp_ids = []
    qry = """
        SELECT distinct(swasp_id)
        FROM eblm_fies
        WHERE swasp_id != 'None'
        """
    print(qry)
    with openDb() as cur:
        cur.execute(qry)
        results = cur.fetchall()
    for row in results:
        swasp_ids.append(row[0])
    return sorted(swasp_ids)

def getObjectParameters(swasp_id):
    qry = """
        SELECT period, epoch, current_status
        FROM eblm_parameters
        WHERE swasp_id=%s
        """
    print(qry, swasp_id)
    with openDb() as cur:
        cur.execute(qry, (swasp_id,))
        results = cur.fetchone()
    if results is None:
        return None, None, None
    else:
        period = results[0]
        epoch = results[1] + 2450000
        status = results[2]
        return period, epoch, status

def getFiesRvs(swasp_id):
    bjd, rv, rv_err, bis, bis_err = [], [], [], [], []
    qry = """
        SELECT
        bjd_mid, mask_velocity, mask_velocity_err,
        bisector, bisector_err
        FROM eblm_fies
        WHERE swasp_id=%s
        AND analyse=1
        """
    print(qry, swasp_id)
    with openDb() as cur:
        cur.execute(qry, (swasp_id,))
        results = cur.fetchall()
    for row in results:
        bjd.append(row[0])
        rv.append(row[1])
        rv_err.append(row[2])
        bis.append(row[3])
        bis_err.append(row[4])
    return np.array(bjd), np.array(rv), np.array(rv_err), \
           np.array(bis), np.array(bis_err)

if __name__ == "__main__":
    args = argParse()
    if args.swasp_id:
        swasp_ids = [args.swasp_id]
    else:
        swasp_ids = getUniqueFiesObjects()
    # loop over each object
    for swasp_id in swasp_ids:
        period, epoch, status = getObjectParameters(swasp_id)
        if period is None:
            print("Skipping {}...".format(swasp_id))
            continue
        bjd, rv, rv_err, bis, bis_err = getFiesRvs(swasp_id)
        phase = ((bjd - epoch)/period)%1
        rv = rv + RV_OFFSET
        print("Comments: {}".format(status))
        fig, ax = plt.subplots(2, 1, figsize=(10, 10))
        ax[0].plot(phase, rv, 'r.')
        ax[0].set_xlim(0, 1)
        ax[0].set_xlabel('Orbital Phase')
        ax[0].set_ylabel('Radial Velocity (km/s)')
        # rvs vs bisectors
        ax[1].plot(rv, bis, 'r.')
        ax[1].set_xlabel('Radial Velocity (km/s)')
        ax[1].set_ylabel('Bisector')
        plt.show()

