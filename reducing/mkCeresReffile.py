"""
"""
import os
import argparse as ap
from collections import (
    defaultdict,
    OrderedDict
    )
from contextlib import contextmanager
import glob as g
from astropy.io import fits
import astropy.units as u
from astropy.coordinates import SkyCoord
import pymysql

# pylint: disable=invalid-name
# pylint: disable=redefined-outer-name
# pylint: disable=no-member


def argParse():
    """
    """
    p = ap.ArgumentParser()
    p.add_argument('--filter', help='filter current data directory',
                   action='store_true')
    p.add_argument('--reffile',
                   help='output a reffile for current directory',
                   action='store_true')
    return p.parse_args()

@contextmanager
def openDB(host='localhost', database='eblm'):
    """
    """
    with pymysql.connect(host=host, database=database,
                         user='jmcc', password='mysqlpassword',
                         cursorclass=pymysql.cursors.DictCursor) as cur:
        yield cur

def findMatchingSwaspIds(target):
    """
    """
    qry = """
        SELECT swasp_id
        FROM eblm_parameters
        WHERE swasp_id LIKE '%{}%'
        OR current_status LIKE '%{}%'
        """.format(target, target)
    print(qry)
    with openDB() as cur:
        cur.execute(qry)
        results = cur.fetchall()
    return results

def findMatchingRvStandards(target):
    """
    """
    qry = """
        SELECT object_id
        FROM rv_standards
        WHERE object_id LIKE '%{}%'
        """.format(target)
    print(qry)
    with openDB() as cur:
        cur.execute(qry)
        results = cur.fetchall()
    return results

def logSpectrumToDb(image_id, object_name, swasp_id, night):
    """
    """
    qry = """
        INSERT INTO eblm_fies
        (image_id, object_name, swasp_id, night)
        VALUES
        (%s, %s, %s, %s)
        """
    qry_args = (image_id, object_name, swasp_id, night)
    print(qry)
    print(qry_args)
    with openDB() as cur:
        cur.execute(qry, qry_args)

def spectrumInDb(image_id):
    """
    """
    qry = """
        SELECT image_id
        FROM eblm_fies
        WHERE image_id=%s
        """
    with openDB() as cur:
        cur.execute(qry, image_id)
        results = cur.fetchall()
    if len(results) > 0:
        return True
    else:
        return False

def estimateSwaspId(c):
    """
    """
    if str(c.dec.dms.d).startswith('-'):
        joint = ''
        times = -1
    else:
        joint = '+'
        times = 1
    ra1 = "{:02d}".format(int(c.ra.hms.h))
    ra2 = "{:02d}".format(int(c.ra.hms.m))
    ra3 = "{:05.2f}".format(c.ra.hms.s)
    if times == -1:
        dec1 = "{:03d}".format(int(c.dec.dms.d))
    else:
        dec1 = "{:02d}".format(int(c.dec.dms.d))
    dec2 = "{:02d}".format(int(c.dec.dms.m)*times)
    dec3 = "{:04.1f}".format(c.dec.dms.s*times)
    # check for +ve or -ve
    coord = '1SWASPJ' + ra1 + ra2 + ra3 + joint + dec1 + dec2 + dec3
    return coord

def getCcfMask(st):
    """
    Determine best CCF mask for RVs
    based on stars spectral type
    """
    if st.lower().startswith('f') or st.lower().startswith('g') or \
        st.lower().startswith('a') or st.lower().startswith('b'):
        return 'G2'
    elif st.lower().startswith('k'):
        return 'K5'
    elif st.lower().startswith('m'):
        return 'M2'
    else:
        return None

def updateObjectKeyword(image, object_id):
    """
    """
    with fits.open(image, mode='update') as ff:
        hdr = ff[0].header
        old_object_id = hdr['OBJECT']
        print('Updating {} header:'.format(image))
        print('{} --> {}'.format(old_object_id, object_id))
        hdr.set('object', object_id)

def getReffileInfo(object_id):
    """
    """
    if not object_id.startswith('HD'):
        qry = """
            SELECT
            ra_hms, dec_dms, pm_ra_mas_y, pm_dec_mas_y,
            paramfit_spec_type
            FROM eblm_parameters
            WHERE swasp_id=%s
            """
    else:
        qry = """
            SELECT
            ra_hms, dec_dms, pm_ra_mas_y, pm_dec_mas_y,
            spec_type
            FROM rv_standards
            WHERE object_id=%s
            """
    print(qry, object_id)
    with openDB() as cur:
        cur.execute(qry, object_id)
        result = cur.fetchone()
    print(result)
    if not object_id.startswith('HD'):
        mask = getCcfMask(result['paramfit_spec_type'])
    else:
        mask = getCcfMask(result['spec_type'])
    ref_str = "{},{},{},{},{},1,{},4.0\n".format(object_id,
                                             result['ra_hms'],
                                             result['dec_dms'],
                                             result['pm_ra_mas_y'],
                                             result['pm_dec_mas_y'],
                                             mask)
    return ref_str

if __name__ == "__main__":
    args = argParse()
    night = os.getcwd().split('/')[-1].split('_')[1]
    print(night)
    templist = g.glob('FI*.fits')
    if args.filter:
        unmatched = defaultdict(list)
        for image in templist:
            # first look for image in database, skip if there
            if not spectrumInDb(image):
                hdr = fits.open(image)[0].header
                target_orig = hdr['TCSTGT']

                # clean up target names
                if 'EBLM' in target_orig:
                    target = target_orig.replace('EBLM', '')
                elif 'EB' in target_orig:
                    target = target_orig.replace('EB', '')
                elif target_orig.startswith('M') or target_orig.startswith('G'):
                    target = target_orig[1:]
                else:
                    target = target_orig

                ra = hdr['OBJRA']
                dec = hdr['OBJDEC']
                coord = SkyCoord(ra=ra*u.degree, dec=dec*u.degree, frame='icrs')
                coord_string = coord.to_string('hmsdms')
                estimated_swasp_id = estimateSwaspId(coord)
                imagetyp = hdr['IMAGETYP']
                exptime = hdr['EXPTIME']
                # look for the RV standards
                if target.startswith('HD'):
                    if imagetyp != 'COUNTTEST' and imagetyp != 'WAVE':
                        print("\n", image, imagetyp, exptime, target, coord_string)
                        matches = findMatchingRvStandards(target)
                        if len(matches) > 1:
                            print('Multiple matches for {}'.format(target))
                            ans = input('Fix this when this happens')
                            continue
                        if len(matches) == 1:
                            print('Found a match for {}'.format(target))
                            print(matches[0]['object_id'])
                            ans = input('Good?')
                            if ans.lower() == 'y':
                                logSpectrumToDb(image, target_orig,
                                                matches[0]['object_id'], night)
                                updateObjectKeyword(image, matches[0]['object_id'])
                            else:
                                print('Skipping bad match for {}'.format(image))
                                unmatched[matches[0]['object_id']].append(image)
                        else:
                            print('No matches found for {}...'.format(target))
                            unmatched[estimated_swasp_id].append(image)
                    else:
                        print('Skipping ancilary frame {}'.format(image))
                # look for science targets
                elif target != "":
                    if imagetyp != 'COUNTTEST' and imagetyp != 'WAVE':
                        print("\n", image, imagetyp, exptime, target, coord_string)
                        matches = findMatchingSwaspIds(target)
                        print(matches)
                        if len(matches) > 1:
                            print('Found multiple matches')
                            for n, match in enumerate(matches):
                                print(n, match['swasp_id'])
                            ans = int(input('Which is the right object?'))
                            estimated_swasp_id = matches[ans]['swasp_id']
                            logSpectrumToDb(image, target_orig,
                                            estimated_swasp_id, night)
                            updateObjectKeyword(image, estimated_swasp_id)
                        elif len(matches) == 1:
                            print('Found a match for {}'.format(target))
                            print(matches[0]['swasp_id'])
                            ans = input('Good?')
                            if ans.lower() == 'y':
                                logSpectrumToDb(image, target_orig,
                                                matches[0]['swasp_id'], night)
                                updateObjectKeyword(image, matches[0]['swasp_id'])
                            else:
                                print('Skipping bad match for {}'.format(image))
                                unmatched[estimated_swasp_id].append(image)
                        else:
                            print('No matches found for {}...'.format(target))
                            unmatched[estimated_swasp_id].append(image)
                    else:
                        print('Skipping ancilary frame {}'.format(image))
                else:
                    continue
            else:
                print('\n{} in DB already, skipping...'.format(image))

        # print quick summary of missing objects
        for i, j in sorted(unmatched.items()):
            print(i, j)
        print("N_unmatched: {}".format(len(unmatched)))
        print("For unmatched files update the TCSTGT keyword if in DB already")
    # make a reference file
    if args.reffile:
        reffile = OrderedDict()
        for image in templist:
            with fits.open(image) as ff:
                hdr = ff[0].header
                object_id = hdr['OBJECT']
                target = hdr['TCSTGT']
                imagetype = hdr['IMAGETYP']
            if target != '' and object_id not in reffile and imagetype == "":
                ref_str = getReffileInfo(object_id)
                reffile[object_id] = ref_str
        # print a summary
        with open('reffile.txt', 'w') as reffile_out:
            for ref_obj in sorted(reffile):
                reffile_out.write(reffile[ref_obj])


