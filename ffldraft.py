#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
module: ffldraft.py
author: Zach Lamberty
created: 2013-08-30

Description:
    <desc>

Usage:
    <usage>

"""

import csv
import datetime
import os
import pylab

import zachlog

from collections import defaultdict
from math import ceil, floor

pylab.close('All')


#---------------------------#
#   Module Constants        #
#---------------------------#

LEAGUE_TEAMS = {
    1: ['CL', 'Captain\'s Log', 'Dylan Thomson'],
    2: ['HPZ', 'Heavy Petting Zoo', 'Zach Lamberty'],
    3: ['ASS', 'Great White Sharts!', 'Jeff Miller'],
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
TEAM_LIST = sorted([v[0] for (k, v) in LEAGUE_TEAMS.items()])

F_DATA = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'ffl_data_20140901.csv'
)

POS_COLOR = {
    'K': 'm',
    'P': 'y',
    'QB': 'k',
    'WR': 'b',
    'RB': 'r',
    'TE': 'g',
    'D/ST': 'c',
}

POS_LIST = [
    'QB',
    'RB',
    'RB/WR',
    'WR',
    'WR/TE',
    'TE',
    'D/ST',
    'K',
]

# logging
zachlog.Config().configure()
logger = zachlog.getLogger(__name__)


#---------------------------#
#   Live Draft Class        #
#---------------------------#

class DraftData():
    """ A class object to calculate draft data, who to pick, etc. """
    def __init__(self, datafile=F_DATA):
        self.load_prediction_data(datafile)
        self.update_replacement_value()

        self.f1 = pylab.figure(1, figsize=[7.5, 5.5])
        self.f2 = pylab.figure(2, figsize=[12.5, 7.5])
        self.fScratch = pylab.figure(3, figsize=[7.5, 5.5])

        self.show_best_replacement_available()

    def load_prediction_data(self, datafile=F_DATA):
        """ Open the csv data and load it into an array """
        logger.info("Loading data file {}".format(datafile))

        with open(datafile, 'r') as fIn:
            d = list(csv.DictReader(fIn))

        # Make into integers and floats what is integers and floats,
        # also strip leading whitespace and split the team/pos into
        # team, pos
        logger.debug("Cleaning up loaded data")
        for player in d:
            # Clean values
            for (iType, i) in player.items():
                player[iType] = i = i.strip().replace('--', '0')
                try:
                    player[iType] = int(i)
                except ValueError:
                    try:
                        player[iType] = float(i)
                    except ValueError:
                        pass

            # Split team / position
            teampos = player.pop('Team Pos', None)
            if teampos:
                t, p = teampos.split(' ')
                player['TEAM'] = t
                player['POS'] = p

            # Split name
            playername = player.pop('Player', None)
            if playername:
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

    # Updating who has been drafted -- interactive
    def get_player_interactive(self, allowDrafted=False):
        """ Allow the user to select a player by initials """
        # Prompt the user to choose who has been drafted and on which team
        firstNameInit = raw_input('First Name Initial?\t')
        lastNameInit = raw_input('Last Name Initial? \t')

        print '\n'

        matches = []
        for player in sorted(self.predictionData, key=lambda x: x['RNK']):
            isMatch = all([
                player['FIRST'].lower().startswith(firstNameInit.lower()),
                player['LAST'].lower().startswith(lastNameInit.lower()),
            ])

            if isMatch and (allowDrafted or player['F TEAM'] == 'FA'):
                matches.append(player)
                print '# {RNK:>4}: {FIRST:} {LAST:}, {TEAM:} {POS:}'.format(**player)

        validRanks = [x['RNK'] for x in matches]
        players = None
        while True:
            r = int(raw_input('\nwhich rank is correct? (0 for none of the above)\t'))
            if r == 0:
                break
            elif r in validRanks:
                players = [x for x in matches if x['RNK'] == r]
                break
            else:
                print "\tThis is not a valid rank!"
                print "\tPlease choose from {}".format(validRanks)

        return players

    def get_team_interactive(self, leagueTeams=LEAGUE_TEAMS):
        """ Allow the user to select a team by team_id """
        print '\n'
        for (teamID, teamInfo) in leagueTeams.items():
            print str(teamID) + '\t' + '{:<4}, {:<23}, {:<15}'.format(*teamInfo)

        validTeamIds = leagueTeams.keys()
        teamId = None
        while True:
            tid = int(raw_input('\nWhich Team Drafted Him? (0 to break)\t'))
            if tid == 0:
                break
            elif tid in validTeamIds:
                teamId = tid
                break
            else:
                print "\tThis is not a valid team id!"
                print "\tPlease choose from {}".format(validTeamIds)

        return teamId

    def new_draft_interactive(self):
        """ Take in a draft notice and update everything accordingly """
        players = self.get_player_interactive()

        if players:
            teamId = self.get_team_interactive()
            self.been_drafted(players, LEAGUE_TEAMS[teamId][0])

    def false_draft_interactive(self):
        """ Undo a previous draft that has been rolled back (it always happens) """
        player = self.get_player_interactive(allowDrafted=True)

        self.been_drafted(player, 'FA')

    def been_drafted(self, players, teamName, posList=POS_LIST):
        """ Update the prediction data to indicate a draft """
        for player in players:
            player['F TEAM'] = teamName

            logger.info('{FIRST:} {LAST:} has been drafted by {F TEAM:}'.format(**player))

        self.update_replacement_value()
        self.show_best_replacement_available()
        self.state_of_draft(posList)

    # Updating who has been drafted -- from file
    def simulate_draft_from_file(self, fpicks, fteam, slow=False):
        """ Read in a series of picks and simulate the file from that """
        with open(fpicks, 'r') as fIn:
            draft = list(csv.DictReader(fIn))

        with open(fteam, 'r') as fIn:
            teams = list(csv.DictReader(fIn))

        teamDic = {}
        for t in teams:
            teamDic[int(t['team_id'])] = [str(t['team_id']), t['team_name'], t['team_name']]

        for d in draft:
            # tell user which player was picked and have them get that player
            # interactively
            print '\n{playerpos:} drafted by {team:}\n'.format(**d)

            flpos = d['playerpos'].split(' ')
            first = flpos[0]
            last = ' '.join(flpos[1:-1])

            # Find by name alone
            players = [player for player in self.predictionData
                       if player['FIRST'] == first and player['LAST'] == last]

            if not players:
                players = self.get_player_interactive()

            # try to look up the team in LEAUGE_TEAMS first, or else use teamDic
            teamIds = [v[0] for (k, v) in LEAGUE_TEAMS.items() if v[1] == d['team']]

            if not teamIds:
                teamId = self.get_team_interactive(leagueTeams=teamDic)
            else:
                teamId = teamIds[0]

            # update all plots as desired
            self.been_drafted(players, teamId)

            if slow:
                raw_input()

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

    def show_best_replacement_available(self, N=25):
        """ Extract the best N remaining players at each position, and determine
            what their replacement values are. Plot the series of replacement
            picks to give a future-looking view on the decision to not draft the
            calculated top remaining player

        """
        logger.info("calculating the top {} available at each position".format(N))
        positions = {el['POS'] for el in self.predictionData}
        topNDic = {pos: self.top_n(N=N, pos=pos, isFA=True) for pos in positions}
        goneDic = {pos: self.top_n(pos=pos, isFA=False) for pos in positions}

        # Prepare replacement value plotting, capn
        self.f1.clf()
        s1 = self.f1.add_subplot(111)

        for (pos, posList) in topNDic.items():
            try:
                # Update to have cumulative sums
                for (i, player) in enumerate(posList):
                    player['cum_repl_val'] = sum(p['repl_val'] for p in posList[:i + 1])

                best = posList[0]
                lab = "{}, {} {}".format(best['POS'], best['FIRST'], best['LAST'])
                c = POS_COLOR.get(pos, 'k')
                s1.plot([x['cum_repl_val'] for x in posList], color=c, marker='o',
                        mfc='w', mec=c, mew=2, lw=2, label=lab)
            except:
                logger.error('fuuuuuck')
                logger.info("pos     = {}".format(pos))
                logger.info("posList = {}".format(posList))
                raise

        s1.legend(loc='lower left', fontsize=10)
        s1.set_ylim((-200, 0))
        s1.set_xlim((-0.5, 24.5))

        logger.debug("Displaying")
        self.f1.show()

    def state_of_draft(self, posList=POS_LIST):
        """ Create an N-team panelled histogram plot which shows how each team
            is faring relative to the median value at each position, as well as
            how that would change if the best X is chosen in this next draft.
            To be updated and displayed after every draft pick.

            Perhaps also include a "residual"-esque plot of the pts lost by not
            chosing the next best player at that position (i.e. points lost to
            present mean, not by forgoing for replacement)

        """
        positions = {el['POS'] for el in self.predictionData}
        bestAvailable = {pos: self.top_n(N=1, pos=pos, isFA=True) for pos in positions}

        teamList = sorted({el['F TEAM'] for el in self.predictionData if not el['F TEAM'] == 'FA'})
        teamSummary = self.team_draft_summary(posList, teamList)

        # Total
        for (team, teamVals) in teamSummary.items():
            teamVals['TOTAL'] = {'PTS': sum(v.get('PTS', 0)
                                            for (k, v) in teamVals.items()
                                            if not 'flex_' in k)}

        # Calculate the median value at each position
        posVals = defaultdict(list)
        for (team, teamVals) in teamSummary.items():
            for (pos, bestAtPos) in teamVals.items():
                try:
                    posVals[pos].append(bestAtPos['PTS'])
                except:
                    pass

        avVals = {pos: (sum(vals) / len(vals)) if vals else 0.0
                  for (pos, vals) in posVals.items()}

        # binVals are the posVals minus the avVals
        binVals = {team: {pos: teamVals.get(pos, {}).get('PTS', 0) - avVal
                          for (pos, avVal) in avVals.items()}
                   for (team, teamVals) in teamSummary.items()}

        # Plot that shit
        N = len(teamList)
        J = floor(N ** .5)
        I = ceil(N / float(J))
        self.f2.clf()
        self.f2.subplots_adjust(left=0.04, bottom=0.06, right=0.98, top=0.95)

        flexKeys = sorted({k for (x, v) in binVals.items() for k in v.keys()
                           if 'flex_' in k})
        posListSpec = posList + flexKeys + ['TOTAL']
        lefts = [i for i in range(len(posListSpec))]
        width = 0.4
        mids = [i + width for i in range(len(posListSpec))]
        allVals = [v for (team, teamVals) in binVals.items() for (k, v) in teamVals.items()
                   if not 'flex_' in k]
        maxval = max(allVals)
        minval = min(allVals)
        for (i, team) in enumerate(sorted(teamSummary.keys())):
            sNow = self.f2.add_subplot(I, J, i + 1)

            # current vals -- starters
            sNow.bar(
                left=lefts[:len(posList)],
                height=[binVals[team][pos] for pos in posList],
                width=width,
                color='blue',
                alpha=0.75
            )

            # current vals -- flex
            if flexKeys:
                sNow.bar(
                    left=lefts[len(posList): len(posList) + len(flexKeys)],
                    height=[binVals[team][pos] for pos in flexKeys],
                    width=width,
                    color='blue',
                    alpha=0.35
                )

            # current vals -- total
            tot = binVals[team]['TOTAL']
            sNow.bar(
                left=lefts[-1],
                height=[tot],
                width=width,
                color='green' if tot > 0 else 'red'
            )

            sNow.set_title(team)
            sNow.set_xticks(mids)
            sNow.set_xticklabels(posListSpec, fontsize=8)
            sNow.set_ylim((minval, maxval))

        logger.debug("Displaying")
        self.f2.show()

    def team_draft_summary(self, posList=POS_LIST, teamList=TEAM_LIST):
        """ Return a list of all drafted players, binned by positions (best
            available)

        """
        tds = defaultdict(list)
        # collect all drafted players
        for player in self.predictionData:
            fteam = player['F TEAM']
            if fteam != 'FA':
                tds[fteam].append(player)

        # Bucket appropriately
        tdsBucket = defaultdict(lambda: defaultdict())

        # go thorugh all non-slash positions and pop out the best
        multiPos = [pos for pos in posList if '/' in pos and not pos == 'D/ST']
        singlePos = [pos for pos in posList if pos not in multiPos]
        for team in teamList:
            for pos in singlePos:
                try:
                    bestAtPos = max([t for t in tds[team] if t['POS'] == pos],
                                    key=lambda x: x['PTS'])
                    tds[team].remove(bestAtPos)
                except:
                    bestAtPos = {}

                tdsBucket[team][pos] = bestAtPos

            for pos in multiPos:
                try:
                    bestAtPos = max([t for t in tds[team] if t['POS'] in pos.split('/')],
                                    key=lambda x: x['PTS'])
                    tds[team].remove(bestAtPos)
                except:
                    bestAtPos = {}

                tdsBucket[team][pos] = bestAtPos

            # If anyone remains in tds[team] at this point, move them into flex
            # positions -- sort them according to their pts within the reamining
            # team
            for (i, player) in enumerate(sorted(tds[team], key=lambda x: -x['PTS'])):
                tdsBucket[team]['flex_{}'.format(i)] = player

        return tdsBucket

    def state_of_position(self, N=25, pos='QB'):
        """ Same as above, but for only one position and with all points labeled
            by position name

        """
        logger.info("calculating the top {} available {}s".format(N, pos))
        topN = self.top_n(N=N, pos=pos, isFA=True)

        self.fScratch.clf()
        s3 = self.fScratch.add_subplot(111)

        try:
            # Update to have cumulative sums
            for (i, player) in enumerate(topN):
                player['cum_repl_val'] = sum(p['repl_val'] for p in topN[:i])

            best = topN[0]
            lab = "Top {} {}".format(N, pos)
            c = POS_COLOR.get(pos, 'k')
            s3.plot([x['cum_repl_val'] for x in topN], color=c, marker='o',
                    mfc='w', mec=c, mew=2, lw=2, label=lab)

            # Annotating with player names
            for (i, player) in enumerate(topN):
                s3.annotate(
                    '{FIRST:} {LAST:}, {TEAM:}'.format(**player),
                    xy=(i, player['cum_repl_val']),
                    xytext=(i, 0.975 * player['cum_repl_val']),
                    rotation=50,
                    horizontalalignment='left',
                    verticalalignment='bottom',
                )

        except:
            logger.error('fuuuuuck')
            logger.info("pos  = {}".format(pos))
            logger.info("topN = {}".format(topN))
            raise

        s3.legend(loc='lower left', fontsize=10)

        logger.debug("Showing state of {}".format(pos))
        self.fScratch.show()
