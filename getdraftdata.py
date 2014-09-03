#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
module: getdraftdata.py
author: Zach Lamberty
created: 2014-08-31

Description:
    Hit the web for draft data; save it localy or just return that ish

Usage:
    <usage>

"""

import argparse
import csv
import datetime
import lxml.html
import os
import requests

import zachlog


#-----------------------#
#   Module Constants    #
#-----------------------#

_ESPN_PREDICTION_BASE = "http://games.espn.go.com/ffl/tools/projections?leagueId={}"
_X_TABLE = 'table[@id="playertable_0"]'
_X_HEADER = 'tr[@class="playerTableBgRowSubhead tableSubHead"]'
_X_ROWS = 'tr[@class="pncPlayerRow playerTableBgRow0" or @class="pncPlayerRow playerTableBgRow1"]'
_X_PAGE_NAV = 'div[@class="paginationNav"]'
_OUT = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'ffl_data_%Y%m%d.csv'
)
_OUT = datetime.datetime.now().strftime(_OUT)

MASCOT = {
    '49ers': 'SF',
    'Bears': 'Chi',
    'Bengals': 'Cin',
    'Bills': 'Buf',
    'Broncos': 'Den',
    'Browns': 'Cle',
    'Buccaneers': 'TB',
    'Cardinals': 'Ari',
    'Chargers': 'SD',
    'Chiefs': 'KC',
    'Colts': 'Ind',
    'Cowboys': 'Dal',
    'Dolphins': 'Mia',
    'Eagles': 'Phi',
    'Falcons': 'Atl',
    'Giants': 'NYG',
    'Jaguars': 'Jax',
    'Jets': 'NYJ',
    'Lions': 'Det',
    'Packers': 'GB',
    'Panthers': 'Car',
    'Patriots': 'NE',
    'Raiders': 'Oak',
    'Rams': 'StL',
    'Ravens': 'Bal',
    'Redskins': 'Was',
    'Saints': 'NO',
    'Seahawks': 'Sea',
    'Steelers': 'Pit',
    'Texans': 'Hou',
    'Titans': 'Ten',
    'Vikings': 'Min',
}

# logging
zachlog.Config().configure()
logger = zachlog.getLogger(__name__)


#-------------------------------#
#   ESPN prediction info        #
#-------------------------------#

def espn_get_prediction_data(espnPredBase=_ESPN_PREDICTION_BASE,
                             leagueId=209006, xTable=_X_TABLE,
                             xHeader=_X_HEADER, xPageNav=_X_PAGE_NAV):
    """ Hit the websites and parse scoring predictions into a listdict """
    logger.info("Fetching ESPN prediction data")
    predictionData = []
    for pred in espn_prediction_pages(espnPredBase, leagueId, xTable, xHeader,
                                      xPageNav):
        predictionData += pred

    return predictionData


def espn_prediction_pages(espnPredBase=_ESPN_PREDICTION_BASE, leagueId=209006,
                          xTable=_X_TABLE, xHeader=_X_HEADER,
                          xPageNav=_X_PAGE_NAV):
    """ Create a generator which returns the html object of pages with
        prediction data tables on them

    """
    urlNext = None

    while True:
        # get new page and parse to html object
        url = urlNext if urlNext else espnPredBase.format(leagueId)
        logger.debug("parsing url {}".format(url))
        page = requests.get(url)
        html = lxml.html.fromstring(page.text)

        # check if it has info
        if espn_has_prediction_info(html, xTable, xHeader):
            # get next url and yield the parse table
            yield espn_get_prediction(html, xTable, xHeader)
            urlNext = espn_get_url_next(html)
            if urlNext is None:
                raise StopIteration()
        else:
            raise StopIteration()


def espn_has_prediction_info(h, xTable=_X_TABLE, xHeader=_X_HEADER):
    """ Check and see whether this html object contains a subheader row """
    return espn_get_prediction_headers(h, xTable, xHeader) is not None


def espn_get_prediction(html, xTable=_X_TABLE, xHeader=_X_HEADER, xRows=_X_ROWS):
    """ Parse the html text/object into a listdict of score prediction """
    headers = espn_get_prediction_headers(html, xTable, xHeader)

    if headers is None:
        raise ValueError("This is not a valid table page!")

    trs = html.xpath('//{}/{}'.format(xTable, xRows))

    def tr_to_vals(tr):
        return [t.text_content().strip() for t in tr.xpath('./td')]

    return [{h: v for (h, v) in zip(headers, tr_to_vals(tr))} for tr in trs]


def espn_get_url_next(html, xPageNav=_X_PAGE_NAV):
    """ Parse the html object for a "next" link of the expected type """
    try:
        return [h for h in html.xpath('//{}/a'.format(xPageNav))
                if 'NEXT' in h.text_content()][0].attrib['href']
    except:
        return None


def espn_get_prediction_headers(html, xTable=_X_TABLE, xHeader=_X_HEADER):
    try:
        xheaders = html.xpath('//{}//{}//td'.format(xTable, xHeader))
        return [h.text_content().strip() for h in xheaders]
    except:
        return None


def espn_prediction_to_file(outname=_OUT, espnPredBase=_ESPN_PREDICTION_BASE,
                            leagueId=209006, xTable=_X_TABLE,
                            xHeader=_X_HEADER, xPageNav=_X_PAGE_NAV):
    """ grab the info from the espn website and write that shit to file """
    pred = espn_get_prediction_data(espnPredBase, leagueId, xTable, xHeader, xPageNav)
    multiPosPred = []

    # clean up first
    for player in pred:
        # split out player team pos
        ptp = player.pop('PLAYER, TEAM POS')
        pt, pos = ptp.split(u"\xa0")[0:2]

        if 'D/ST' in pt:
            mascot = pt.split(' ')[0]
            playerName = pt
            playerTeam = MASCOT[mascot]
        else:
            playerName, playerTeam = pt.split(', ')

        splitName = playerName.split(' ')
        player['FIRST'] = splitName[0]
        player['LAST'] = ' '.join(splitName[1:])
        player['TEAM'] = playerTeam

        # Assign to the appropriate fantasy team
        player['F TEAM'] = player.pop('TYPE')

        # Some players have two positions. DAFUQ.
        posList = pos.split(', ')
        for (i, pos) in enumerate(posList):
            if i == 0:
                player['POS'] = pos
            else:
                newPlayer = player.copy()
                newPlayer['POS'] = pos
                multiPosPred.append(newPlayer)

    with open(outname, 'w') as fOut:
        csvOut = csv.DictWriter(fOut, fieldnames=pred[0].keys())
        csvOut.writeheader()
        csvOut.writerows(pred)
        if multiPosPred:
            csvOut.writerows(multiPosPred)


#-------------------------------#
#   Main routine                #
#-------------------------------#

def _parse_args():
    """ Take a log file from the commmand line """
    parser = argparse.ArgumentParser()
    parser.add_argument("-x", "--xample", help="An Example", action='store_true')

    args = parser.parse_args()

    return args


if __name__ == '__main__':

    args = _parse_args()

    main()
