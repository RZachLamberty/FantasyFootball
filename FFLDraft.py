#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
module: FFLDraft.py
author: Zach Lamberty
created: 2013-08-30

Description:
    <desc>

Usage:
    <usage>

"""

import csv
import pylab
import scipy

pylab.close('All')

#---------------------#
#   Module Constants  #
#---------------------#

CSV_DTYPE = [
    ('ESPNRank', 'int32'),
    ('PlayerFirst', 'S15'),
    ('PlayerLast', 'S15'),
    ('Team', 'S4'),
    ('POS', 'S4'),
    ('F TEAM', 'S5'),
    ('CompAtt', 'S10'),
    ('PassYards', 'int32'),
    ('PassTD', 'int32'),
    ('PassInt', 'int32'),
    ('RushAtt', 'int32'),
    ('RushYards', 'int32'),
    ('RushTD', 'int32'),
    ('Receptions', 'int32'),
    ('RecYards', 'int32'),
    ('RecTD', 'int32'),
    ('PTS', 'float32'),
    ('ReplValue', 'float32')
]


LEAGUE_TEAMS = {
    1: ['CL', 'Captain\'s Log', 'Dylan Thomson'],
    2: ['HPZ', 'Heavy Petting Zoo', 'Zach Lamberty'],
    3: ['ASS', 'Great White Sharts', 'Jeff Miller'],
    4: ['HIT', 'I\'d Still Hit It', 'Collin Solberg'],
    5: ['JNZ', 'Just Noise', 'Ben Koch'],
    6: ['CFB', 'Chicken Fried Blumpkins', 'Brad Nicolai'],
    7: ['VEU', 'Very European Uppercuts', 'Jake Hillesheim'],
    8: ['GcR', 'Gotham City Rogues', 'Nick Igoe'],
    9: ['LMKS', 'DA Lil\' Mookies', 'Dana Kinsella'],
    10: ['FVT', 'Emergerd! Fertberl!', 'Andy Warmuth'],
    11: ['ST', 'Snail Trails', 'Michael Lubke'],
    12: ['BCB', 'Brew City Bruisers', 'Matt Hibberd'],
}

INT_INTEGER_SET = [0, 5, 6, 7, 8, 9, 10, 11, 12, 13]
FLOAT_INTEGER_SET = [14, 15]

PREDICTION_DATA_FILE = 'FFLDraftData.csv'

POS_COLOR = {
    'K': 'm',
    'P': 'y',
    'QB': 'k',
    'WR': 'b',
    'RB': 'r',
    'TE': 'g',
    'D/ST': 'c',
}
POS_LIST = POS_COLOR.keys()


#---------------------#
#   Module Functions  #
#---------------------#

class DraftData():
    """ A class object to calculate draft data, who to pick, etc. """
    def __init__(self):
        self.load_prediction_data()
        self.update_replacement_value()

        self.f1 = pylab.figure(1, figsize=[7.5, 5.5])
        self.f2 = pylab.figure(2, figsize=[7.5, 5.5])

        #self.best_replacement_available()

    def load_prediction_data(self):
        """ Open the csv data and load it into an array """
        with open(PREDICTION_DATA_FILE, 'r') as fIn:
            d = list(csv.DictReader(fIn))

        # Make into integers and floats what is integers and floats,
        # also strip leading whitespace and split the team/pos into
        # team, pos
        for player in d:
            # Clean values
            for (iType, i) in player.items():
                player[iType] = i = i.strip().replace('--', '0')
                try:
                    player[iType] = float(i)
                except ValueError:
                    pass

            # Split team / position
            t, p = player.pop('Team Pos').split(' ')
            player['TEAM'] = t
            player['POS'] = p

            # Split name
            fl = player.pop('Player').split(' ')
            player['FIRST'] = fl[0]
            player['LAST'] = ' '.join(fl[1:])

        self.predictionData = d

    def sort_prediction_vals(self):
        """ Sort based on whether they have been drafted already, then position,
            then predicted pts

        """
        self.predictionData = sorted(self.predictionData,
                                     key=lambda x: (x['F TEAM'], x['POS'],
                                                    -x['PTS']))

    # Updating who has been drafted
    def newDraft(self):
        """ Prompt the user to choose who has been drafted and on which team """
        #   Ask for last name
        firstNameInit = raw_input('First Name Initial?\t')
        lastNameInit = raw_input('Last Name Initial? \t')

        print '\n'
        for row in self.predictionData:
            rank, first, last, team, pos, fantTeam = list(row)[:6]
            firstRight = first.startswith(firstNameInit.lower()) or (first.startswith(firstNameInit.upper()))
            lastRight = last.startswith(lastNameInit.lower()) or (last.startswith(lastNameInit.upper()))
            if firstRight and lastRight:
                print str((rank, first, last, team, pos))

        thisRank = int(raw_input('\nwhich rank is correct? (0 for none of the above)\t'))

        if thisRank == 0:
            pass
        else:
            print '\n'
            for (teamID, teamInfo) in LEAGUE_TEAMS.iteritems():
                print str(teamID) + '\t' + '{:<4}, {:<23}, {:<15}'.format(*teamInfo)

            thisTeam = int(raw_input('\nWhich Team Drafted Him? (0 to break)\t'))
            if thisTeam == 0:
                pass
            else:
                thisTeamName = LEAGUE_TEAMS[thisTeam][0]

                self.beenDrafted(thisRank, thisTeamName)

    def beenDrafted(self, rank, fantTeam):
        """ Update the array to display who has been drafted by which team """
        if self.predictionData[rank][0] == rank:
            self.predictionData[rank][5] = fantTeam
        else:
            for row in self.predictionData:
                if row[0] == rank:
                    row[5] = fantTeam
                    break

        self.update_replacement_value()
        _relf_abestReplacementAvailable()

    def falseDraft(self):
        """ Undo a previous draft that has been rolled back (it always happens) """
        #   Ask for last name
        firstNameInit = raw_input('First Name Initial?\t')
        lastNameInit = raw_input('Last Name Initial? \t')

        print '\n'
        for row in self.predictionData:
            rank, first, last, team, pos, fantTeam = list(row)[:6]
            if first.startswith(firstNameInit) and last.startswith(lastNameInit):
                print str((rank, first, last, team, pos))

        thisRank = int(raw_input('\nwhich rank is correct? (0 for none of the above)\t'))

        self.beenDrafted(thisRank, 'FA')

    # Replacement Value Calculation
    def update_replacement_value(self):
        """ For every player in the draft, calculate their replacement value at
            their position.  We may generalize this

        """
        self.sort_prediction_vals()

        for (i, pNow) in enumerate(self.predictionData[:-1]):
            pNext = self.predictionData[i + 1]

            pNow['repl_val'] = (pNext['PTS'] - pNow['PTS']
                                if pNow['POS'] == pNext['POS']
                                else 0.0)

    def top_n(self, N=None, pos=None, isFA=None, onTeam=None):
        """ Return the top N people which satisfy the requirements passed in
            If you specify a position, that they are or are not a FA, or that
            they are on a specific team, the list will be filtered accordingly

        """
        self.sort_prediction_vals()
        filt = (el for el in self.predictionData
                if (pos is None or el['POS'] == pos)
                and (isFA is None or (el['F TEAM'] == 'FA') == isFA)
                and (onTeam is None or el['F TEAM'] == onTeam))

        N = N if N else len(self.predictionData)
        return sorted(filt, key=lambda x: -x['PTS'])[:N]

    def best_replacement_available(self, N=25):
        """ Extract the best N remaining players at each position, and determine
            what their replacement values and current "pain value" are.

        """
        topNDic = {pos: self.top_n(N=N, pos=pos, isFA=True) for pos in POS_LIST}
        goneDic = {pos: self.top_n(pos=pos, isFA=False) for pos in POS_LIST}

        # Prepare plotting, capn
        self.f1.clf()
        s1 = self.f1.add_subplot(111)

        for (pos, posList) in topNDic.items():
            # Update to have cumulative sums
            for (i, player) in enumerate(posList):
                player['cum_repl_val'] = sum(p['repl_val'] for p in posList[:i])

            s1.plot()

        for i in range(len(sortedVals)):
            rowNow = sortedVals[i]
            if rowNow[5] == 'FA':
                if i == len(sortedVals) - 1:
                    calcNow = True
                else:
                    rowNext = sortedVals[i + 1]

                    if rowNow[4] != rowNext[4]:
                        calcNow = True
                    else:
                        calcNow = False

                if calcNow:
                    row = list(rowNow)
                    rank, first, last, team, pos, fantTeam = row[:6]
                    points, replVal = row[-2:]

                    topNDic[pos] = [row, []]

                    for j in range(N):
                        ind = i - j
                        if (ind >= 0) and (sortedVals[ind][4] == pos):
                            topNDic[pos][1].append(sortedVals[ind][-2])
            else:
                row = list(rowNow)
                rank, first, last, team, pos, fantTeam = row[:6]
                points, replVal = row[-2:]

                if pos not in goneNowDic:
                    goneNowDic[pos] = []

                goneNowDic[pos].append(points)

        #   Best available
        replacementValueDic = {}
        for (pos, x) in topNDic.iteritems():
            row, l = x
            replacementValueDic[pos] = [row, scipy.cumsum(scipy.diff(l))]

        self.f1.clf()
        s1 = self.f1.add_subplot(111)

        for (pos, x) in replacementValueDic.iteritems():
            row, l = x
            lab = pos + ' '.join([','] + row[1:3])
            c = POS_COLOR[pos]
            s1.plot(l, color=c, marker='o', mfc='w', mec=c, mew=2, lw=2, label=lab)

        s1.legend(loc='lower left')
        s1.set_ylim((-200, 0))
        s1.set_xlim((-0.5, 24.5))
        self.f1.show()

        # How far behind
        self.f2.clf()
        s2 = self.f2.add_subplot(111)

        isLabel = False
        for (pos, l) in goneNowDic.iteritems():
            if pos in replacementValueDic:
                bestPointsLeft = replacementValueDic[pos][0][-2]
                l.reverse()
                pointsLost = scipy.array(l) - bestPointsLeft
                c = POS_COLOR[pos]
                s2.plot(pointsLost, color=c, marker='o', mfc='w', mec=c, mew=2, lw=2, label=pos)
                isLabel = True

        if isLabel:
            s2.legend(loc='lower left')
        self.f2.show()
