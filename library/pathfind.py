#!/usr/bin/env python
from functools import cmp_to_key

from library import feature, coord

INFINITY = 10000


def cmp(x, y):
    if x < y:
        return -1
    elif x > y:
        return 1
    else:
        return 0


class Grid (object):
    """
    A generic grid of values.
    """
    def __init__ (self, size, value = None):
        """
        Initialise the grid with a given value.

        :``size``: A coordinate representing the size of the grid. *Required*.
        :``value``: A value used to initialise the grid. *Default None*.
        """
        self.grid = []
        self._width  = size.x
        self._height = size.y
        for row in range(size.y):
            row = []
            for column in range(size.x):
                row.append(value)
            self.grid.append(row)

    def size (self):
        """
        Returns the size of the grid.
        """
        return coord.Coord(self._width, self._height)

    def __getvalue__ (self, pos):
        """
        Returns the grid value at a given position.

        :``pos``: A position within the grid. *Required*.
        """
        # assert isinstance(pos, coord.Coord)
        assert (pos.y < self._height)
        assert (pos.x < self._width)
        return self.grid[pos.y][pos.x]

    def __setvalue__ (self, pos, value):
        """
        Updates the grid value at a given position.

        :``pos``: A position within the grid. *Required*.
        :``value``: The new value. *Required*.
        """
        # assert isinstance(pos, coord.Coord)
        assert (pos.y < self._height)
        assert (pos.x < self._width)
        self.grid[pos.y][pos.x] = value

class DistanceGrid (Grid):
    """
    A grid of distances for various positions to an initial point.
    """
    def __init__ (self, size, value = INFINITY):
        Grid.__init__(self, size, value)

class PrevGrid (Grid):
    """
    A grid of predecessors for coordinates on a path.
    """
    pass

class Pathfind (object):
    """
    An object to handle pathfinding calculations.
    """
    def __init__ (self, grid, start, target=None, target_condition=None, pos_condition=None):
        """
        Create a new Pathfind object.

        :``grid``: A FeatureGrid representation of the map. *Required*.
        :``start``: The starting coordinate. *Required*.
        :``target``: The target coordinate for the path. *Default None*.
        :``target_condition``: A method taking a Coord parameter, and an
                   alternative condition for finding a valid targt. *Default None*.
                   At least one of ``target`` and ``target_condition`` needs
                   to be valid.
        :``pos_condition``: A method taking a Coord parameter. Used to limit
                   coordinates considered for the path beyond the basic
                   traversability checks. *Default None*.
        """
        assert(start < grid.size() and target < grid.size())
        assert(target != None or target_condition != None)
        self.fgrid  = grid
        self.start  = start
        self.target = target
        self.dgrid  = DistanceGrid(self.fgrid.size(), INFINITY)
        self.pgrid  = PrevGrid(self.fgrid.size())
        self.target_condition    = target_condition
        self.check_pos_condition = pos_condition

    def path_exists (self):
        """
        Returns whether a path from start to target can be found.
        """
        if self.start == self.target:
            return True

        return self.pathfind() != None

    def get_path (self):
        """
        Returns the path leading from start to target as a list of coordinates.
        """
        if self.start == self.target:
            return [self.start]

        if self.pathfind() == None:
            return None
        path = self.backtrack(self.target)
        return path

    def backtrack (self, begin):
        """
        Once the pathfinding is completed, this method returns a list of 
        coordinates to represent the path.

        :``begin``: The end point of the path. *Required*.
        """
        path = []
        next = begin
        while next != None:
            path.append(next)
            next = self.pgrid.__getvalue__(next)
        return path

    def check_target (self, pos):
        """
        Returns whether the target has been reached or an alternative
        target condition has been met.

        :``pos``: The coordinate that is currently being looked at. *Required*.
        """
        if pos == self.target:
            return True

        if self.target_condition != None and self.target_condition(pos):
            return True

        return False

    def add_neighbours (self, curr, include_diagonals=False):
        """
        Checks all neighbouring squares of a given position and, if they
        haven't been handled yet, adds them to a list of candidate points.
        Also updates their distance and predecessor, as necessary.

        :``curr``: The current position within the grid. *Required*.
        :``include_diagonals``: If true, also checks diagonally adjacent
        squares. *Default false*.
        """
        for pos in coord.AdjacencyIterator(curr, include_diagonals):
            if not self.fgrid.__getitem__(pos).traversable():
                continue
            if self.check_pos_condition and not self.check_pos_condition(pos):
                continue

            new_dist = self.dgrid.__getvalue__(curr) + 1
            if pos in self.nlist:
                if self.dgrid.__getvalue__(pos) > new_dist:
                    # print "Old distance(%s): %s, old prev: (%s)" % (pos, self.dgrid.__getvalue__(pos), self.pgrid.__getvalue__(pos))
                    self.dgrid.__setvalue__(pos, new_dist)
                    self.pgrid.__setvalue__(pos, curr)
                    # print "Change distance(%s) to %s, prev to (%s)" % (pos, new_dist, curr)
            elif self.dgrid.__getvalue__(pos) == INFINITY:
                # print "Set distance(%s) to %s, prev to (%s)" % (pos, new_dist, curr)
                self.dgrid.__setvalue__(pos, new_dist)
                self.pgrid.__setvalue__(pos, curr)
                self.nlist.append(pos)

            if self.check_target(pos):
                if self.target == None:
                    self.target = pos
                return True

        return False

    def pathfind (self):
        """
        Starts pathfinding and returns the next coordinate on the path from
        start to target, or None if no path was found.
        """
        self.nlist = [self.start]
        self.dgrid.__setvalue__(self.start, 0)

        while len(self.nlist) > 0:
            curr = self.nlist[0]
            self.nlist.remove(curr)
            if self.add_neighbours(curr):
                return curr
            #self.nlist.sort(cmp=lambda a, b: cmp(self.dgrid.__getvalue__(a), self.dgrid.__getvalue__(b)))
            _cmp = lambda a, b: cmp(self.dgrid.__getvalue__(a), self.dgrid.__getvalue__(b))
            self.nlist.sort(key=cmp_to_key(_cmp))
        return None
