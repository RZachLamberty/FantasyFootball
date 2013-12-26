###############################################################################
#                                                                             #
#   statparse.py                                                              #
#   10/27/2013                                                                #
#                                                                             #
#   Open up the CSV and parse it for various quantities which may be          #
#   plotted elsewhere                                                         #
#                                                                             #
###############################################################################

import argparse
import csv
import pylab
import scipy
import scipy.stats

from statgrab import CSV_NAME, W, P

#-----------------------#
#   Module Constants    #
#-----------------------#


#-----------------------#
#   Class to hold csv   #
#-----------------------#

class StatParser():
    """Load the CSV into a dictionary object and then parse it however you set
    fit!

    """
    def __init__(self):
        """durt"""
        self.load_csv()
        self.init_iterators()
        self.statArray = scipy.zeros((0, len(self.realTeams)))

    def __del__(self):
        """Close the csv"""
        self.fIn.close()

    def load_csv(self):
        """Just load the csv"""
        self.fIn = open(CSV_NAME, 'rb')
        self.csvIn = csv.DictReader(self.fIn)
        self.fieldnames = self.csvIn.fieldnames
        self.dataDic = {}
        for row in self.csvIn:
            self.dataDic[row['TEAM NAME']] = row

    def init_iterators(self):
        """Several iterators will be used in many functions. Pre-generate them

        """
        self.teams = self.dataDic.keys()
        self.realTeams = [el for el in self.teams if el not in ['STD', 'AV']]

        # weekly
        self.weekly = {}
        wStr = 'WEEK {}'
        pStr = 'ROUND {} - PLAYOFFS'
        self.gameStuff = ['OP', 'PTS FOR', 'PTS AGAINST']
        self.positions = ['QB', 'RB', 'RB/WR', 'WR', 'WR/TE', 'TE', 'D/ST',
                          'K', 'P']
        wKeys = self.gameStuff + self.positions
        for k in wKeys:
            self.weekly[k] = ['{} {}'.format(wStr, k).format(i)
                              for i in range(1, W + 1)]
            self.weekly[k] += ['{} {}'.format(pStr, k).format(i)
                               for i in range(1, P + 1)]

    # Default getters
    def opponents(self, teamName):
        return [self.dataDic[teamName][w]
                for w in self.weekly['OP']
                if self.dataDic[teamName][w]]

    # Point getters
    def points_for_total(self, teamName):
        return float(self.dataDic[teamName]['PF'])

    def points_against_total(self, teamName):
        return float(self.dataDic[teamName]['PA'])

    def points_for_by_week(self, teamName):
        return scipy.array([float(self.dataDic[teamName][w])
                            for w in self.weekly['PTS FOR']
                            if w in self.dataDic[teamName]
                            if self.dataDic[teamName][w]])

    def points_against_by_week(self, teamName):
        return scipy.array([float(self.dataDic[teamName][w])
                            for w in self.weekly['PTS AGAINST']
                            if w in self.dataDic[teamName]
                            if self.dataDic[teamName][w]])

    def position_points_by_week(self, teamName, position):
        return scipy.array([float(self.dataDic[teamName][w])
                            for w in self.weekly[position]
                            if w in self.dataDic[teamName]
                            if self.dataDic[teamName][w]])

    def fractional_position_points_by_week(self, teamName, position):
        tot = self.points_for_by_week(teamName)
        pos = self.position_points_by_week(teamName, position)[: len(tot)]
        return pos / tot

    # Point / av diffs
    def diff_points_for_total(self, teamName):
        """Total - average"""
        return self.points_for_total(teamName) - self.points_for_total('AV')

    def diff_points_against_total(self, teamName):
        """Total - average"""
        return self.points_against_total(teamName) - self.points_against_total('AV')

    def diff_points_for_by_week(self, teamName):
        """Total - average"""
        return self.points_for_by_week(teamName) - self.points_for_by_week('AV')

    def diff_points_against_by_week(self, teamName):
        """Total - average"""
        return self.points_against_by_week(teamName) - self.points_against_by_week('AV')

    def diff_position_points_by_week(self, teamName, position):
        """Total - average"""
        return self.position_points_by_week(teamName, position) - self.position_points_by_week('AV', position)

    def diff_fractional_position_points_by_week(self, teamName, position):
        """Total - average"""
        return self.fractional_position_points_by_week(teamName, position) - self.fractional_position_points_by_week('AV', position)

    # Record
    def win_percentages(self):
        w = lambda t: float(self.dataDic[t]['WINS'])
        l = lambda t: float(self.dataDic[t]['LOSSES'])
        return scipy.array([w(t) / (w(t) + l(t)) for t in self.realTeams])

    def against_the_field(self):
        wins = scipy.zeros((len(self.realTeams), len(self.weekly['OP'])))
        for (i, t) in enumerate(self.realTeams):
            for (j, w) in enumerate(self.weekly['PTS FOR']):
                for t2 in [el for el in self.realTeams if el != t]:
                    wins[i, j] += int(self.dataDic[t][w] > self.dataDic[t2][w]) if self.dataDic[t][w] else 0.0
                    wins[i, j] += .5 * int(self.dataDic[t][w] == self.dataDic[t2][w]) if self.dataDic[t][w] else 0.0

        losses = 11. - wins

        return scipy.average(wins, axis=1), scipy.std(wins, axis=1), scipy.average(losses, axis=1), scipy.std(losses, axis=1)

    def clutch_performance(self):
        """Record against the field in the playoffs only"""
        playoffs = [el for el in self.weekly['OP'] if 'PLAYOFFS' in el]
        wins = scipy.zeros((len(self.realTeams), len(playoffs)))
        for (i, t) in enumerate(self.realTeams):
            for (j, w) in enumerate(playoffs):
                for t2 in [el for el in self.realTeams if el != t]:
                    wins[i, j] += int(self.dataDic[t][w] > self.dataDic[t2][w]) if self.dataDic[t][w] else 0.0
                    wins[i, j] += .5 * int(self.dataDic[t][w] == self.dataDic[t2][w]) if self.dataDic[t][w] else 0.0

        losses = 11. - wins

        return (scipy.average(wins, axis=1),
                scipy.std(wins, axis=1),
                scipy.average(losses, axis=1),
                scipy.std(losses, axis=1))

    # Win factors
    def win_corr_array(self):
        self.construct_win_factors()
        w = self.win_percentages()
        lx, ly = self.statArray.shape
        if len(w) != ly:
            print 'Should be {0:} teams, and input should be n by {0:}'.format(w)
        z = scipy.zeros((lx, ly))
        for i in range(lx):
            z[i] = scipy.correlate(w, self.statArray[i]) / scipy.sum(self.statArray[i])
        return z

    def win_lin_array(self):
        self.construct_win_factors()
        w = self.win_percentages()
        lx, ly = self.statArray.shape
        if len(w) != ly:
            print 'Should be {0:} teams, and input should be n by {0:}'.format(w)
        z = scipy.zeros((lx, 5))
        for i in range(lx):
            z[i] = scipy.stats.linregress(w, self.statArray[i])
        return z

    def plot_lin_array(self):
        f = pylab.figure(figsize=(16, 6))
        s = f.add_subplot(111)
        z = scipy.absolute(self.win_lin_array())[:, 2]
        iZ = scipy.argsort(z)
        s.plot(z[iZ], ls='--', lw=2,
               marker='o', ms=7, mec='k', mew=2, mfc='white')
        s.set_xlim((-0.5, len(z) - 0.5))
        s.set_ylim((0.0, 1.0))
        f.show()

    def add_wf(self, winFactor, winFactorName):
        lx, ly = self.statArray.shape
        z = scipy.zeros((lx + 1, ly))
        if lx > 0:
            z[:-1, :] = self.statArray.copy()
        z[-1] = winFactor
        self.statArray = z.copy()

        self.statNames = scipy.array(list(self.statNames) + [winFactorName])

    def construct_win_factors(self):
        # Zero it all out
        self.statArray = scipy.zeros((0, len(self.realTeams)))
        self.statNames = scipy.zeros(0)

        # One basic one -- points against
        self.add_wf(self.wf_points_against(), 'op pts')

        # Position average
        for pos in self.positions:
            self.add_wf(self.wf_position_points_for(pos), pos)

        # Frac pos average
        for pos in self.positions:
            self.add_wf(self.wf_fractional_position_points_by_week(pos), '{} frac'.format(pos))

        # Position diffs
        #for pos in self.positions:
        #    self.add_wf(self.wf_diff_position_points_for(pos), 'diff pos points for')

        # Position diffs - fractional
        #for pos in self.positions:
        #    self.add_wf(self.wf_diff_fractional_position_points_for(pos), '')

        # Consistency (stds, team + pos)
        self.add_wf(self.wf_std(), 'pts std')
        for pos in self.positions:
            self.add_wf(self.wf_position_std(pos), '{} std'.format(pos))

        # divisions
        #for div in divSet:
        #    self.add_wf(self.wf_divisions(div))

    def wf_points_against(self):
        return scipy.array([-self.points_against_total(t)
                            for t in self.realTeams])

    def wf_position_points_for(self, position):
        return scipy.array([scipy.average(self.position_points_by_week(t, position))
                            for t in self.realTeams])

    def wf_fractional_position_points_by_week(self, position):
        return scipy.array([scipy.average(self.fractional_position_points_by_week(t, position))
                            for t in self.realTeams])

    def wf_diff_position_points_for(self, position):
        return scipy.array([scipy.average(self.diff_position_points_by_week(t, position))
                            for t in self.realTeams])

    def wf_diff_fractional_position_points_for(self, position):
        return scipy.array([scipy.average(self.diff_fractional_position_points_by_week(t, position))
                            for t in self.realTeams])

    def wf_std(self):
        return scipy.array([scipy.std(self.points_for_by_week(t))
                            for t in self.realTeams])

    def wf_position_std(self, position):
        return scipy.array([scipy.std(self.position_points_by_week(t, position))
                            for t in self.realTeams])

    # Other plots
    def plot_against_the_field(self):
        f = pylab.figure()
        s = f.add_subplot(111)

        w, wErr, l, lErr = self.against_the_field()
        q = w.argsort()
        N = len(w)
        s.errorbar(range(N), w[q], wErr[q] / scipy.sqrt(N), marker='o')
        s.set_xlim(-.5, N - .5)

        for (i, sI) in enumerate(q):
            x, y = i, w[sI]
            s.annotate(self.realTeams[sI], (x, y), (x + .15, y - .25))

        f.show()


#-----------------------#
#   Main routine        #
#-----------------------#

def main():
    """

    """
    return 0


#-----------------------#
#   Command line        #
#-----------------------#

def parse_args():
    """

    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-x', '--xample', help="whatevs", action="set_true")

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    main()
