########################################################################
#                                                                      #
#   statgrab.py                                                        #
#   10/27/2013                                                         #
#                                                                      #
#   Use the fetcher routines to grab all the relevant information and  #
#   save it all to a csv (primary key is team name)                    #
#                                                                      #
########################################################################

import argparse
import collections
import csv
import itertools
import os
import scipy

import FFFetch

from FFLTeams import TEAMS
from TeamScoring import get_scores

#-----------------------#
#   Module Constants    #
#-----------------------#

# data fetcher
FETCHER = FFFetch.FFFetcher()

# csv stuff
W, P = 14, 3
CSV_NAME = './ffldata.csv'
STANDINGS_HEADERS = ['WINS', 'LOSSES', 'TIES', 'PF', 'PA']
SCORE_HEADERS = [x.format(i)
                 for i in range(1, W + 1)
                 for x in ['WEEK {0:} OP',
                           'WEEK {0:} PTS FOR',
                           'WEEK {0:} PTS AGAINST']]
SCORE_HEADERS += [x.format(i)
                  for i in range(1, P + 1)
                  for x in ['ROUND {0:} - PLAYOFFS OP',
                            'ROUND {0:} - PLAYOFFS PTS FOR',
                            'ROUND {0:} - PLAYOFFS PTS AGAINST']]
POSITIONS = ['QB',
             'RB',
             'RB/WR',
             'WR',
             'WR/TE',
             'TE',
             'D/ST',
             'K',
             'P']
STARTERS_HEADERS = [x.format(i, pos)
                    for i in range(1, W + 1)
                    for pos in POSITIONS
                    for x in ['WEEK {0:} {1:}']]
STARTERS_HEADERS += [x.format(i, pos)
                     for i in range(1, P + 1)
                     for pos in POSITIONS
                     for x in ['ROUND {0:} - PLAYOFFS {1:}']]

CSV_HEADERS = ['TEAM NAME', 'TEAM ABB', 'TEAM ID', 'OWNER']
CSV_HEADERS += STANDINGS_HEADERS
CSV_HEADERS += SCORE_HEADERS
CSV_HEADERS += STARTERS_HEADERS


#-----------------------#
#   Main routine        #
#-----------------------#

def main():
    """Create csv database to hold the ffl stats"""
    d = collections.defaultdict(dict)

    # Get data
    update_basics(d)
    update_scores(d)
    update_standings(d)
    update_position_scores(d)

    # avs / stds
    calc_avs_stds(d)

    #return d

    # Write to csv
    write_to_csv(d)


#-----------------------#
#   Fetch Data          #
#-----------------------#

def update_basics(d):
    """Add team information"""
    print 'Fetching basics... ',

    for owner, team in TEAMS.iteritems():
        d[team.teamName] = {k: '' for k in CSV_HEADERS}
        d[team.teamName]['OWNER'] = owner
        d[team.teamName]['TEAM NAME'] = team.teamName
        d[team.teamName]['TEAM ABB'] = team.teamAbb
        d[team.teamName]['TEAM ID'] = team.teamID

    print 'Done!'


def update_scores(d):
    """Add scores for every week"""
    print 'Fetching scores... ',

    scores = FETCHER.fetch('schedule', 'seasonScores')

    for row in scores:
        week, home, away, homeS, awayS = row

        if homeS == 'Box':
            pass
        else:
            d[home]['{0:} OP'.format(week)] = away
            d[home]['{0:} PTS FOR'.format(week)] = homeS
            d[home]['{0:} PTS AGAINST'.format(week)] = awayS

            d[away]['{0:} OP'.format(week)] = home
            d[away]['{0:} PTS FOR'.format(week)] = awayS
            d[away]['{0:} PTS AGAINST'.format(week)] = homeS

    print 'Done!'


def update_standings(d):
    """Add standings information"""
    print 'Fetching standings... ',

    standings = FETCHER.fetch('standings', 'seasonStandings')

    for teamName, teamStandings in standings.iteritems():
        d[teamName].update(teamStandings)

    print 'Done!'


def update_position_scores(d, W=17, T=12):
    """Cycle through all the teams for all the weeks.  Try to find the position
    scores, etc

    """
    weeks = range(1, W + 1)
    teams = range(1, T + 1)
    print 'Fetching position scores...'
    for (w, i) in itertools.product(weeks, teams):
        print '\tweek {0:}, team {1:}'.format(w, i)
        fmtDic = {'scoringPeriodId': w, 'teamId': i}
        try:
            x = FETCHER.fetch('scoreboard', 'playerScores', fmtDic=fmtDic)
            d[x['TEAM NAME']].update(x)
        except FFFetch.NoMatchup as e:
            print '\t\tNo matchup!'
    print '\tDone!'


#-----------------------#
#   Av and Std calcs    #
#-----------------------#

def calc_avs_stds(d):
    """For meaningful quantities, calculate the average and std dev across
    different teams

    """
    print 'Calculating avs and stds... ',

    teams = sorted(d.keys())
    t0 = teams[0]

    for f in CSV_HEADERS:
        try:
            d['AV'][f] = scipy.average([d[t][f] for t in teams])
            d['STD'][f] = scipy.std([d[t][f] for t in teams])
        except:
            d['AV'][f] = ''
            d['STD'][f] = ''

    d['AV']['TEAM NAME'] = 'AV'
    d['STD']['TEAM NAME'] = 'STD'

    print 'Done!'


#-----------------------#
#   Av and Std calcs    #
#-----------------------#

def write_to_csv(d):
    """duh"""
    print 'Saving to csv... ',

    teams = sorted(d.keys())

    with open(CSV_NAME, 'wb') as fOut:
        csvOut = csv.DictWriter(fOut, fieldnames=CSV_HEADERS)
        csvOut.writeheader()
        for teamName in teams:
            if teamName not in ['AV', 'STD']:
                csvOut.writerow(d[teamName])
        csvOut.writerow(d['AV'])
        csvOut.writerow(d['STD'])

    print 'Done!'

#-----------------------#
#   Command line        #
#-----------------------#

if __name__ == '__main__':
    main()
