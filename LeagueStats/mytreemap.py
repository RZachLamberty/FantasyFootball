########################################################################
#                                                                      #
#   mytreemap.py                                                       #
#   10/27/2013                                                         #
#                                                                      #
#   plot a generic treemap                                             #
#                                                                      #
########################################################################

import pylab
import scipy

#-----------------------#
#   Module Constants    #
#-----------------------#

LEAF_TYPES = [int, float]
ROOT = 'ROOT NODE'


#-----------------------#
#   Class definitions   #
#-----------------------#

class MyRect(object):
    """It'll be easier to just do this than to constantly be calculating
    random crap

    """
    def __init__(self, lowerLeft=[0.0, 0.0], upperRight=[1.0, 1.0]):
        self.lowerLeft = lowerLeft
        self.upperRight = upperRight
        self.xMin, self.yMin = lowerLeft
        self.xMax, self.yMax = upperRight
        self.A = self.area()

    # Plotting getter
    def plot_coords(self):
        pass

    # Random calculation stuff
    def x_range(self):
        return float(self.xMax - self.xMin)

    def y_range(self):
        return float(self.yMax - self.yMin)

    def x_longer_than_y(self):
        return self.x_range() >= self.y_range()

    def area(self):
        return self.x_range() * self.y_range()


def rect_divide(rect, fracList):
    """Recursively divvy up the rectangle into pieces the side of elements in
    fracList; return a list of rectangles

    """
    x = []

    # Make sure that fracList is sorted and normalized
    fracList = scipy.array(sorted(fracList, reverse=True))
    fracList /= scipy.sum(fracList)

    # Catch "singles"
    if len(fracList) == 1:
        return [rect]

    # The largest piece gets errythin
    ll1 = list(rect.lowerLeft)
    ur1 = list(rect.upperRight)
    ll2 = list(rect.lowerLeft)
    ur2 = list(rect.upperRight)
    if rect.x_longer_than_y():
        ll2[0] = ur1[0] = ll1[0] + rect.x_range() * fracList[0]
    else:
        ll2[1] = ur1[1] = ll1[1] + rect.y_range() * fracList[0]

    rect1 = MyRect(lowerLeft=ll1, upperRight=ur1)
    rect2 = MyRect(lowerLeft=ll2, upperRight=ur2)
    x.append(rect1)

    if len(fracList) == 2:
        x.append(rect2)
    else:
        x += rect_divide(rect2, fracList[1:].copy())

    return x


class TreeMap(object):
    """A factory for treemaps in matplotlib"""

    def __init__(self, figsize=(8, 6)):
        self.f = pylab.figure(figsize=figsize)
        self.s = self.f.add_subplot(111)

    def __del__(self):
        pylab.close(self.f)

    # Make the treemap
    def treemap(self, tree, norm=None):
        """Create the treemap"""
        if norm is None:
            norm = self.treemax(tree)

        rectList = self.rect_list(tree)

        maxLevel = max([len(el[0]) for el in rectList])
        lineWidths = [maxLevel - len(el[0]) + 1 for el in rectList]
        bottomLevel = [not any([el2[0][:len(el[0])] == el[0]
                                for el2 in rectList
                                if el != el2])
                       for el in rectList]

        # plot em, dano
        for ((node, rect), lw, doFill) in zip(rectList, lineWidths, bottomLevel):
            r = pylab.Rectangle(xy=tuple(rect.lowerLeft),
                                width=rect.x_range(),
                                height=rect.y_range(),
                                lw=lw,
                                fill=doFill)
            self.s.add_patch(r)
            if doFill:
                self.s.annotate(str(node),
                                xy=tuple(rect.lowerLeft),
                                xytext=tuple([el + .02
                                              for el in rect.lowerLeft]))

        self.f.show()

    def draw_rectangle(self, rect, nodeLabel):
        """Draw the rectangle related to tree node label"""
        pylab.Rectangle()

    # calculate the rectangle dimensions
    def rect_list(self, tree):
        """Return a list of (node name path, ...), corners pairs"""
        treeSum = self.tree_sum(tree)
        treeFrac = self.tree_frac(treeSum)
        treeRects = self.tree_rects(treeFrac)
        nodeList = self.tree_nodes(treeRects)
        return sorted([(nodeTup, self.get_rect(treeRects, nodeTup))
                       for nodeTup in nodeList],
                      key=lambda x: (len(x), x))

    def tree_sum(self, tree):
        """Given a standard tree object, calculate (recursively) the sum of the
        leafs / subtrees

            tree = {a: subtree, ...}

            tree_sum = {a: leaf_sum(subtree), tree_sum(subtree)}

        """
        x = {}
        for (node, nodeVal) in tree.iteritems():
            if self.isleaf(nodeVal):
                x[node] = nodeVal,
            else:
                x[node] = self.tree_sum(nodeVal)

        leafSum = scipy.sum([n[0] for n in x.values()])

        return (leafSum, x)

    def tree_frac(self, treeSum):
        """Given a sum tree as constructed in tree_sum, replace the sum values
        with the fractional values (relative to a given level's sum)

        """
        x = {}
        levelSum, subTree = treeSum
        for (node, nodeVal) in subTree.iteritems():
            if len(nodeVal) == 1:
                x[node] = float(nodeVal[0]) / levelSum,
            else:
                x[node] = float(nodeVal[0]) / levelSum, self.tree_frac(nodeVal)

        return x

    def tree_rects(self, treeFrac, baseRect=MyRect()):
        x = {}

        # Sort the nodes by fractional size
        nodes = sorted(treeFrac.keys(), key=lambda x: -treeFrac[x][0])
        fracList = [treeFrac[n][0] for n in nodes]
        rects = rect_divide(baseRect, fracList)

        for (node, rect) in zip(nodes, rects):
            nodeVal = treeFrac[node]
            if len(nodeVal) == 1:
                x[node] = (rect,)
            else:
                x[node] = (rect, self.tree_rects(nodeVal[1], rect))

        return x

    def tree_nodes(self, tree):
        """Collect every tree path as a tuple"""
        x = []
        for (node, nodeVal) in tree.iteritems():
            x.append([node])
            if len(nodeVal) > 1:
                x += [[node] + el for el in self.tree_nodes(nodeVal[1])]

        return x

    def get_rect(self, treeRects, nodeTup):
        tree_ptr = dict(treeRects)
        for (i, n) in enumerate(nodeTup):
            tree_ptr = tree_ptr[n]
            if i == len(nodeTup) - 1:
                tree_ptr = tree_ptr[0]
            else:
                tree_ptr = tree_ptr[1]
        return tree_ptr

    # Tree walking / calculating utilities
    def treemax(self, tree):
        m = 0
        for node, nodeVal in tree.iteritems():
            if self.isleaf(nodeVal):
                m = max(m, nodeVal)
            else:
                m = max(m, self.treemax(nodeVal))
        return m

    def isleaf(self, nodeVal):
        """Determine whether the current node value is a leaf (int, float, etc)

        """
        return any([isinstance(nodeVal, t) for t in LEAF_TYPES])
