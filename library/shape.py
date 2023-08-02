#!/usr/bin/env python
"""
Shape, *a collection of clases and functions relating to Shapes*.

Shapes are a grid representation of ASCII graphics. Each point is denoted by an
x and y co-ordinate, where the co-ordinate 0, 0 is the top-left corner of any
shape. These shapes can be of any size, can be drawn onto each other, combined
into a single canvas, collected, split, sectioned, and iterated over.

See the `Shapes`_ section for ``Shape``, ``Box``, ``Column`` and related
classes.

"""

from . import coord
from . import collection
import warnings

def iterable (obj):
    """
    Returns either a boolean False value or the iter of obj.
    """
    try:
        return iter(obj)
    except TypeError:
        return False

class ShapeError (Exception):
    """
    A generic Shape-related error.
    """
    pass

class ShapeColumn (object):
    """
    ShapeColumn is merely a reference to a specific column of glyphs in a parent
    Shape class. It's implemented thus to allow swapping of the x and y
    co-ordinates when accessing a Shape as though it were a multi-dimensional
    array.

    Modifying via index (ShapeColumn[1]=None, for instance) will in fact
    modify the Shape.
    """
    def copy (self):
        """
        Returns the actual column object as a list. This column object is a
        copy, and any edits made to it are not reflected in the Shape.
        """
        return []
    def parent (self):
        """
        Returns the Shape to which this column belongs.
        """
        return None
    def col (self):
        """
        Returns the column number that this column is a representation of.
        """
        return -1
    def __str__ (self):
        """
        Returns a string representation of the column, where each glyph is
        followed by a new line.
        """
        return ""
    def __repr__ (self):
        """
        Returns a representation of the column as an object.
        """
        return "<ShapeColumn None: 'None'>"
    def __setitem__ (self, row, value):
        """
        Performs in-place assignation via ``self.parent()[Coord(self.column, row)]``
        ``= value`` (roughly). In fact, as the class is a closure, it does none of
        these.

        Provides index-based row access to the column, ie, column[1]="x".

        :``row``: The row that you wish to assign a value to.
        :``value``: The glyph you want to place. Either len(``value``) == 1
                    or ``value`` is None must be true for the assignation to
                    be successful.

        """
        pass
    def __getitem__ (self, row):
        """
        Returns the glpyh located at ``row``.

        :``row``: The row being requested for.
        """
        pass
    def __iter__ (self):
        """
        Provides iteration over the content of the column in the format of:
        tuple(Coord, glyph), where Coord equates to the glyph location in the
        Shape (rather than in this column), and the glyph is the relevant glyph.
        """
        pass

    def __eq__ (self, other):
        if not isinstance(other, ShapeColumn):
            return False
        return self.col() == other.col()
    def __ne__ (self, other):
        if not isinstance(other, ShapeColumn):
            return False
        return self.col() != other.col()
    def __lt__ (self, other):
        if not isinstance(other, ShapeColumn):
            return False
        return self.col() < other.col()
    def __le__ (self, other):
        if not isinstance(other, ShapeColumn):
            return False
        return self.col() <= other.col()
    def __gt__ (self, other):
        if not isinstance(other, ShapeColumn):
            return False
        return self.col() > other.col()
    def __ge__ (self, other):
        if not isinstance(other, ShapeColumn):
            return False
        return self.col() >= other.col()

_ShapeColumn = ShapeColumn

class ShapeRow (object):
    """
    ShapeRow is merely a reference to a specific row of glyphs in a parent Shape
    class. It reflects the implementation of the ShapeColumn which is thus
    implemented to allow swapping x and y co-ordinates when accessing a shape as
    though it were a multi-dimensional list.

    Modifying via index (ShapeRow[1]=None, for instance) will in fact modify the
    Shape.
    """
    def copy (self):
        """
        Returns the actual row object as a list. This row object is a
        copy, and any edits made to it are not reflected in the Shape.
        """
        return []
    def parent (self):
        """
        Returns the Shape to which this row belongs.
        """
        return None
    def row (self):
        """
        Returns the row number that this row is a representation of.
        """
        return -1
    def __str__ (self):
        """
        Returns a string representation of the row.
        """
        return ""
    def __repr__ (self):
        """
        Returns a representation of the row as an object.
        """
        return "<ShapeRow None: 'None'>"
    def __setitem__ (self, column, value):
        """
        Performs in-place assignation via self.parent()[Coord(self.row, column)]
        = value (roughly). In fact, as the class is a closure, it does none of
        these.

        Provides index-based column access to the row, ie, row[1]="x".

        :``column``: The column that you wish to assign a value to.
        :``value``: The glyph you want to place. Either len(``value``) == 1
                    or ``value`` is None must be true for the assignation to
                    be successful.
        """
        pass
    def __getitem__ (self, column):
        """
        Returns the glpyh located at ``column``.

        :``column``: The column being requested for.
        """
        pass
    def __iter__ (self):
        """
        Provides iteration over the content of the row in the format of:
        tuple(Coord, glyph), where Coord equates to the glyph location in the
        Shape (rather than in this row), and the glyph is the relevant glyph.
        """
        pass

    def __eq__ (self, other):
        if not isinstance(other, ShapeRow):
            return False
        return self.row() == other.row()
    def __ne__ (self, other):
        if not isinstance(other, ShapeRow):
            return False
        return self.row() != other.row()
    def __lt__ (self, other):
        if not isinstance(other, ShapeRow):
            return False
        return self.row() < other.row()
    def __le__ (self, other):
        if not isinstance(other, ShapeRow):
            return False
        return self.row() <= other.row()
    def __gt__ (self, other):
        if not isinstance(other, ShapeRow):
            return False
        return self.row() > other.row()
    def __ge__ (self, other):
        if not isinstance(other, ShapeRow):
            return False
        return self.row() >= other.row()

_ShapeRow = ShapeRow

class Shape (object):
    """
    Shapes consist of a canvas grid (with relative Coords). The shape can be
    anything. Shapes can be drawn onto other shapes and have shapes drawn onto
    them.

    Direct glyph access is provided by Shape[x][y], Shape[Coord(x, y)].

    Row and column access by ``row(number)`` and ``column(number)``. The ShapeRow
    and ShapeColumns respectively returned by these are references to the Shape.
    Modifications made to these will be reflected in the Shape.
    """
    _canvas = None
    def __init__ (self, *args, **kwargs):
        """
        Create a new shape.

        :``sh_list``: A list (or otherwise iterable) representation of a shape.
                      For example, passing [list("...."), list("....")] will
                      result in a 4x2 shape. If passed a Shape, will copy it and
                      create a new shape. *Default None*.
        :``width``: The width of the shape. If not 0, and ``sh_list`` has been
                    provided, and the width is greater than the shape instatiated
                    from ``sh_list``, the shape will be normalised to this width
                    and ``fill``. If ``sh_list`` is not provided, the shape
                    will be padded with ``fill``. *Default 0*.
        :``height``: Likewise with ``width``. *Default 0*.
        :``fill``: For padding purposes or blank, sized shapes, this character
                   will be used to fill the canvas. *Default None*.
        """
        sh_list, width, height, fill = None, 0, 0, None
        if kwargs:
            sh_list = kwargs.get("sh_list", None)
            width = kwargs.get("width", 0)
            height = kwargs.get("height", 0)
            fill = kwargs.get("fill", None)
        if args:
            # Either sh_list or width
            if len(args) >= 1:
                if iterable(args[0]):
                    sh_list = args[0]
                elif isinstance(args[0], int):
                    width = args[0]
                else:
                    raise ShapeError("Unexpected type '%s' for argument 1 of Shape::__init__. Expected iterable or int." % type(args[0]))

            # Must be width or height (can't have a fill for 0*0 shapes)
            if len(args) >= 2:
                if isinstance(args[1], int):
                    if sh_list is not None:
                        width = args[1]
                    else:
                        height = args[1]
                else:
                    raise ShapeError("Unexpected type '%s' for argument 2 of Shape::__init__. Expected iterable or int." % type(args[1]))

            # Must be height or fll.
            if len(args) >= 3:
                if isinstance(args[2], int):
                    height = args[2]
                else:
                    fill = args[2]

            # We have an sh_list and a width/height.
            if len(args) >= 4 and sh_list is not None:
                fill = args[3]

            if fill is not None and len(fill) != 1:
                raise ShapeError("Unexpected size %s for argument 'fill' of Shape::__init__. Expect None or single character, got '%s'." % (len(fill), fill))

            if len(args) >= 4 and sh_list is None:
                raise ShapeError("Unexpected arguments for Shape::__init__: '%s'." % (', '.join([str(x) for x in args[3:]])))

        self._canvas = []
        if not sh_list:
            for row in range(height):
                row = []
                for columnn in range(width):
                    row.append(fill)
                self._canvas.append(row)
        else:
            if isinstance(sh_list, Shape):
                sh_list = sh_list._canvas

            for row in sh_list:
                nrow = []
                for column in row:
                    nrow.append(column)
                self._canvas.append(nrow)

            if width != 0 and width > self.width():
                self.normalise(width=width, fill=fill)
            if height != 0 and height > self.height():
                self.normalise(height=height, fill=fill)

    def width (self):
        """
        Returns the smallest width that can contain the largest row of the
        shape. *Note: rows padded with None are not equivalent in length
        to rows without padding.*
        """
        width = 0
        for row in self._canvas:
            if not row:
                continue
            if len(row) > width:
                width = len(row)
        return width 

    def height (self):
        """
        Returns the smallest height that can contain the largest column of
        the shape. *Note: columns are uniform in size across the shape; as with
        rows, None padding is counted.*
        """
        return len(self._canvas)

    def size (self):
        """
        Returns the smallest box that can contain the shape. *Note: this counts
        padding characters (None) as normal glyphs. Thus, it is only possible
        to have varying lengths of rows, with the 'gap' being represented on
        the right side of the object.*
        """
        return coord.Size(self.width(), self.height())

    def column (self, column):
        """
        Returns a ShapeColumn containing all the glyphs in ``column``. See the
        ShapeColumn (closure) class definition for more information.

        :``column``: The column to return. Required.
        """
        class ShapeColumn (_ShapeColumn):
            __doc__ = _ShapeColumn.__doc__
            def copy (s):
                col = []
                for row in self._canvas:
                    col.append(row[column])
                return col
            copy.__doc__ = _ShapeColumn.copy.__doc__
            def parent (s):
                return self
            parent.__doc__ = _ShapeColumn.parent.__doc__
            def col (s):
                return column
            col.__doc__ = _ShapeColumn.col.__doc__
            def __str__ (s):
                return '\n'.join(str(x) for x in s.copy())
            __str__.__doc__ = _ShapeColumn.__str__.__doc__
            def __repr__ (s):
                return "<ShapeColumn %s: '%s'>" % (column, str(s.copy()))
            __repr__.__doc__ = _ShapeColumn.__str__.__doc__
            def __setitem__ (s, row, value):
                self._canvas[row][column] = value
            __setitem__.__doc__ = _ShapeColumn.__setitem__.__doc__
            def __getitem__ (s, row):
                return self._canvas[row][column]
            __getitem__.__doc__ = _ShapeColumn.__getitem__.__doc__
            def __iter__ (s):
                for i in range(self.height()):
                    yield (coord.Coord(column, i), self._canvas[i][column])
            __iter__.__doc__ = _ShapeColumn.__iter__.__doc__

        return ShapeColumn()

    def row (self, row):
        """
        Returns a ShapeRow containing all the glyphs in ``row``. See the
        ShapeRow (closure) class definition for more information.

        :``row``: The row to return. Required.
        """
        class ShapeRow (_ShapeRow):
            __doc__ = _ShapeRow.__doc__
            def copy (s):
                nrow = []
                for col in self._canvas[row]:
                    nrow.append(col)
                return nrow
            copy.__doc__ = _ShapeRow.copy.__doc__
            def parent (s):
                return self
            parent.__doc__ = _ShapeRow.parent.__doc__
            def row (s):
                return row
            def __str__ (s):
                return str(''.join([str(x) for x in s.copy()]))
            def __repr__ (s):
                return "<ShapeRow %s: '%s'>" % (row, self._canvas[row])
            def __setitem__ (s, column, value):
                self._canvas[row][column] = value
            def __getitem__ (s, column):
                return self._canvas[row][column]
            def __iter__ (s):
                for i in range(len(self._canvas[row])):
                    return (coord.Coord(i, row), self._canvas[row][i])

        return ShapeRow()

    def normalise (self, width=None, height=None, fill=None):
        """
        Extend either the width, the height, or both, of a Shape to the relevant
        value, using the provided fill value.

        :``width``: The width to which the Shape should be extended. This
                    integer value should be greater than the current width
                    of the Shape, or None to perform no width normalisation.
                    *Default None*.
        :``height``: The height to which the Shape should be extended. As per
                     ``width`` above. *Default None*.
        :``fill``: The fill character which should be used when extending
                   rows and columns. *Default None*.
        """
        assert width is None or isinstance(width, int)
        assert height is None or isinstance(height, int)

        if width is not None and width < self.width():
            raise ShapeError("can't normalise to less than maximum width.")

        if height is not None and height < self.height():
            raise ShapeError("can't normalise to less than maximum height.")

        if fill is not None and len(fill) != 1:
            raise ShapeError("can't normalise with character '%s'." % fill)

        if width == None and height == None:
            return

        if self._canvas == []:
            self._canvas = [[]]

        if width:
            for i in range(len(self._canvas)):
                while len(self._canvas[i]) < width:
                    self._canvas[i].append(fill)
        if height:
            if not width:
                width = self.width()
            while len(self._canvas) < height:
                new_row = []
                while len(new_row) < width:
                    new_row.append(fill)
                self._canvas.append(new_row)

    def trim (self, width=None, height=None, trim_left=False, trim_top=False):
        """
        The opposite of normalise in that it reduces the size of a Shape to the
        relevant width or height provided. For reducing width, it can remove
        columns from the right (default) or the left of the shape. For reducing
        height, it can remove rows from the bottom (default) or the top of the
        shape.

        :``width``: As per normalise, the number of columns to reduce the
                    shape to. Note: this is not the number of columns to
                    remove. *Default None*.
        :``height``: As per width, only regarding rows.
        :``trim_left``: Instead remove columns from the left of the shape.
                        *Default False*.
        :``trim_top``: Instead remove rows from the top of the shape. *Default*
                       *False*.
        """
        assert trim_left == False or trim_left == True
        assert trim_top == False or trim_top == True

        assert width is None or isinstance(width, int)
        assert height is None or isinstance(height, int)

        if width is not None:
            if trim_left:
                pop = 0
            else:
                pop = -1
            for i in range(len(self._canvas)):
                while len(self._canvas[i]) > width:
                    self._canvas[i].pop(pop)

        if height is not None:
            if trim_top:
                pop = 0
            else:
                pop = -1
            while len(self._canvas) > height:
                self._canvas.pop(pop)

    def pad (self, num_cols=0, num_rows=0, fill=None):
        """
        Like ``normalise``, this function increases the width and height of the
        current shape. However, unlike ``normalise``, ``pad`` performs
        operations to the left and to the top, rather than to the bottom and to
        the right.

        :``num_cols``: The number of columns to pad the shape to. *Default
                       0*.
        :``num_rows``: The number of rows to pad the shape to. *Default 0*.
        :``fill``: The character to use as fill. *Default None*.
        """
        assert fill is None or len(fill) == 1

        if num_cols == 0 and num_rows == 0:
            return

        if num_cols <= self.width() and num_rows <= self.height():
            return

        if self._canvas == []:
            self._canvas = [[]]

        if num_cols:
            for i in range(len(self._canvas)):
                while len(self._canvas[i]) < num_cols:
                    self._canvas[i].insert(0, fill)
        if num_rows:
            if not num_cols:
                num_cols = self.width()
            while len(self._canvas) < num_rows:
                new_row = []
                while len(new_row) < num_cols:
                    new_row.append(fill)
                self._canvas.insert(0, new_row)

    def draw_on (self, shape, offset=coord.Coord(0, 0), check_conflict=True, conflict_error=False):
        """
        Attempt to draw Shape instance ``shape`` on top of self, starting at
        offset ``offset``. Conflict checking is enable by default (ie, it will
        only draw glyphs from ``shape`` onto self if the relevant co-ordinate is
        None), but by default it will simply ignore errors.

        :``shape``: The shape which will be drawn upon this one. It is
                    presumed that this shape can be contained by self.
                    *Required*.
        :``offset``: The co-ordinates to begin drawing at (ie, starting with
                     the top left corner of ``shape`` (0, 0), it will begin
                     drawing from here). *Default 0, 0*.
        :``check_conflict``: Check for conflict before drawing. If true, it
                             will only copy a glyph from ``shape`` onto self if
                             self contains None at that location. *Default
                             True*.
        :``conflict_error``: If true, will raise a ShapeError upon conflicts.
                             Catching this error allows the detection of
                             accidental overwriting. *Default False*.
        """
        assert isinstance(shape, Shape)
        assert coord.Size(offset)+shape.size() <= self.size()
        for xy, char in shape:
            nxy = xy+offset
            if check_conflict and self[nxy] != None:
                if conflict_error:
                    raise ShapeError("Tried to blit foreign '%s' onto '%s' at %s!" % (char, self[nxy], nxy))
                else:
                    continue
            self[nxy] = char

    def section (self, section_start, section_stop=None):
        """
        Return a new Shape containing within it the content of the current shape
        from ``section_start`` to ``section_stop``.

        :``section_start``: The top left co-ordinates of the rectangle. If
                            ``section_stop`` has not been provided, it will be
                            assumed that the section should instead consist of
                            Coord(0, 0) to ``section_stop``.
        :``section_stop``: The bottom right co-ordinates of the rectangle. See
                           note regarding ``section_start``. *Default None*.
        """
        if section_stop is None:
            section_stop = section_start
            section_start = coord.Coord(0, 0)

        assert section_start < section_stop

        offset = section_stop - section_start

        new_shape = Shape(offset.x, offset.y)
        for c in coord.RectangleIterator(section_start, section_stop):
            new_shape[c-section_start] = self[c]

        return new_shape

    def wipe (self):
        """
        Iterate over the entire canvas and set every square to None.
        """
        for spot, glyph in self:
            self[spot] = None

    def center (self):
        """
        Return a coordinate roughly equivalent to the centre of the image. This
        relies on the assumption that the height and width are both equal;
        otherwise, there will be a few rows or columsn out on either side.
        """
        return coord.Coord(self.height()/2, self.width()/2)

    centre = center

    def __iter__ (self):
        """
        Provide an iterator that returns (Coord(x, y), self[x][y]) for each
        glyph within the Shape.
        """
        for rownum in range(len(self._canvas)):
            for colnum in range(len(self._canvas[rownum])):
                yield (coord.Coord(colnum, rownum), self._canvas[rownum][colnum])

    def __getitem__ (self, item):
        """
        Return either a glyph (if ``item`` is a Coord), or a column (if ``item``
        is an integer). Does **not** support slicing!

        :``item``: Either a Coord, in which case we return the actual item, or
                   an "x" axis integer. The latter will return a ShapeColumn
                   object that references the column.
        """
        if isinstance(item, coord.Coord):
            return self._canvas[item.y][item.x]
        elif isinstance(item, slice):
            raise Exception("Do not slice Shape!")
        else:
            return self.column(item)

    def __setitem__ (self, item, value):
        """
        Alter the glyph at ``item`` by replacing with ``value``. Does **not**
        support slicing.

        :``item``: A co-ordinate, in which case we perform direct assignation
                   of ``value`` to ``item``. The syntax of Shape[x][y] will not
                   actually be parsed by this function. Instead, it is parsed
                   as Shape.column(x)[y].
        :``value``: Either None, a single-character string, or a list, instance
                    of Shape or its subclass, Column. If passed a 1*x Shape it
                    will attempt to draw the Shape on top of itself (without
                    checking for conflict).
        """
        assert (value is None) or (isinstance(value, list) or isinstance(value, Shape) or isinstance(value, Column)) or (len(value) == 1)
        if isinstance(item, coord.Coord):
            self._canvas[item.y][item.x] = value
        elif isinstance(item, slice):
            raise ShapeError("Cannot slice Shape!")
        elif isinstance(item, int):
            if isinstance(value, list):
                value = Column(value)
            elif isinstance(value, Shape):
                value = Column(value)
            else:
                raise ShapeError("Invalid type '%s' for assignation to %s." % (type(value), item))
            self.draw_on(value, coord.Coord(item, 0), False, False)

    def __len__ (self):
        return self.width()

    def __repr__ (self):
        return "<Shape width=%s height=%s>" % self.size().as_tuple()

    def __str__ (self):
        """
        Translate a Shape into a string. None values are replaced with " ", and
        new lines ("\\n") are inserted at the end of each row.
        """
        result = ""
        for rownum, row in enumerate(self._canvas):
            for column in row:
                if column is None:
                    result += " "
                else:
                    result += column
            if rownum < len(self._canvas)-1:
                result += "\n"
        return result

class AutoShape (Shape):
    """
    An unsized Shape that expands to suit needs.
    """
    def __init__ (self, fill=None):
        """
        Initiate the automatic shape.

        :``fill``: What character should be used when normalising the shape.
        """
        self.fill = fill
        Shape.__init__(self, 0, 0, fill=fill)

    def size (self):
        """
        To compensate for the automatic sizing of the shape, size returns an
        "infinite" size. To get the actual size of the shape, use
        ``AutoShape::actual_size.``
        """
        return coord.AutoSize()

    def width (self):
        """
        To compensate for the automatic sizing of the shape, width returns an
        "inifinite" width. To get the actual width of the shape, use
        ``AutoShape::actual_width``.
        """
        return coord.AutoDimension()

    def height (self):
        """
        To compensate for the automatic sizing of the shape, height returns an
        "infinite" height. To get the actual height of the shape, use
        ``AutoShape::actual_width``.
        """
        return AutoDimension()

    def _actual_wrapper (function):
        """
        Performs hot-swapping of actual_width, actual_height and actual_size
        into the relevant width, height and size functions before executing
        the function. Once performed, hot-swaps the functions back again.

        :``function``: The function to be wrapped.
        """
        def _wrapper (self, *args, **kwargs):
            oh = self.height
            self.height = self.actual_height
            ow = self.width
            self.width = self.actual_width
            os = self.size
            self.size = self.actual_size
            ah = self.actual_height
            def cleanup():
                self.height = oh
                self.width = ow
                self.size = os
            try:
                result = function(self, *args, **kwargs)
            except:
                cleanup()
                raise

            cleanup()
            return result

        _wrapper.__name__ = function.__name__
        _wrapper.__doc__ =  function.__doc__
        _wrapper.__wraps__ = function
        return _wrapper

    actual_width = _actual_wrapper(Shape.width)
    actual_width.__doc__ = """
        To compensate for automatic sizing, actual widths of the AutoShape are
        accessed via suffixing "actual" to the function name.
        """

    actual_height = _actual_wrapper(Shape.height)
    actual_height.__doc__ = """
        To compensate for automatic sizing, actual heights of the AutoShape are
        accessed via suffixing "actual" to the function name.
        """

    actual_size = _actual_wrapper(Shape.size)
    actual_size.__doc__ = """
        To compensate for automatic sizing, actual sizes of the AutoShape are
        accessed via suffixing "actual" to the function name.
        """

    normalise = _actual_wrapper(Shape.normalise)

    def as_shape (self):
        """
        Attempts to convert the current AutoShape into a Shape, and then returns
        it.
        """
        return Shape(self._canvas)

    def __getitem__ (self, item):
        """
        Attempt to access ``item``. If ``item`` is outside of the bounds of the
        current shape, it is sized accordingly.

        :``item``: The item to be accessed.
        """
        if isinstance(item, coord.Coord):
            if item.x >= self.actual_width():
                self.normalise(width=item.x+1, fill=self.fill)
            if item.y >= self.actual_height():
                self.normalise(height=item.y+1, fill=self.fill)
        elif isinstance(item, int):
            if item >= self.actual_width():
                self.normalise(width=item+1, fill=self.fill)
        return Shape.__getitem__(self, item)

    def __setitem__ (self, item, value):
        """
        Attempt to set ``item`` to ``value``. If ``item`` if outside of the
        bounds of the current shape, it is sized accordingly.

        :``item``: The item to be set.
        :``value``: The value to be set.
        """
        if isinstance(item, coord.Coord):
            if item.x >= self.actual_width():
                self.normalise(width=item.x+1, fill=self.fill)
            if item.y >= self.actual_height():
                self.normalise(height=item.y+1, fill=self.fill)
        return Shape.__setitem__(self, item, value)


class Box (Shape):
    """
    A rectangular Shape that provides borders and perimeter access.
    """
    def __init__ (self, width, height, border=1, fill=None, border_fill=None):
        """
        Create a box.

        :``width``: How many characters wide the box should be.
        :``height``: How many characters tall the box should be.
        :``border``: The size of border to place. *Default 1*.
        :``fill``: The fill character of the box. *Default None*.
        :``border_fill``: The character to use when generating the border which
                          is drawn on top of the fill character (regardless of
                          conflicts).
        """
        self.border = border
        Shape.__init__(self, width, height, fill)
        for c in self.perimeter():
            self[c] = border_fill

    def perimeter (self):
        """
        Returns an iterator of Coords corresponding to the perimeter of the box,
        specifically the border define when initialising the box. If
        ``self.border`` == 0 then will return nothing.
        """
        if self.border < 1:
            return

        w, h = self.size()

        # Top section.
        for x in range(w):
            for y in range(self.border):
                yield coord.Coord(x, y)

        # Sides!
        for x in range(self.border):
            for y in range(self.border, h-self.border):
                yield coord.Coord(x, y)
                yield coord.Coord(w-x-1, y)

        # Bottom section
        for x in range(w):
            for y in range(h-self.border, h):
                yield coord.Coord(x, y)

class Column (Shape):
    """
    A single-character column of characters.
    """
    def __init__ (self, shape=None, height=None, fill=None):
        """
        Create a column.

        :``shape``: List of characters (or Shape or ShapeColumn) to fill our
                    column with.
        :``height``: Height to pad the column to. *Default None*.
        :``fill``: Padding character to use when padding the column. *Default
                   None*.
        """
        if isinstance(shape, ShapeColumn):
            shape = shape.copy()
        if isinstance(shape, Shape):
            assert shape.width() == 1
            Shape.__init__(self, shape, height=height, fill=fill)
        elif isinstance(shape, int):
            if height is not None:
                fill = height
            Shape.__init__(self, width=1, height=shape, fill=fill)
        elif shape is None:
            if height is None:
                height = 1
            Shape.__init__(self, width=1, height=height, fill=fill)
        else:
            nshape = []
            for column in shape:
                nshape.append([column])
            Shape.__init__(self, nshape, height=height, fill=fill)

class Row (Shape):
    """
    A single-character row of characters.
    """
    def __init__ (self, shape=None, width=None, fill=None):
        """
        Create a row.

        :``shape``: List of characters (or Shape or ShapeColumn) to fill our
                    row with.
        :``width``: Width to pad the row to. *Default None*.
        :``fill``: Padding character to use when padding the row. *Default
                   None*.
        """
        if isinstance(shape, ShapeColumn):
            shape = shape.copy()
        if isinstance(shape, Shape):
            assert shape.height() == 1
            Shape.__init__(self, shape, width=width, fill=fill)
        elif isinstance(shape, int):
            if width is not None:
                fill = width
            Shape.__init__(self, width=shape, height=1, fill=fill)
        elif shape is None:
            if width is None:
                width = 1
            Shape.__init__(self, width=width, height=1, fill=fill)
        else:
            nshape = []
            for row in shape:
                nshape.append([row])
            Shape.__init__(self, nshape, width=width, fill=fill)


def adjoin (shape1, shape2, overlap=0, top_offset=0, fill=None, join_left=False, skip_conflicts=False, collect=False, offset_both=False):
    """
    Take two shapes and combine them into one. This method places shapes
    side-by-side with ``shape1`` on the left and ``shape2`` on the right. If
    ``overlap`` is greater than zero, ``shape2`` will overlap ``shape1`` on the
    left by ``overlap``. Finally, the resultant shape will be padded using
    ``fill``.

    :``shape1``: The first shape. *Required*.
    :``shape2``: The second shape. *Required*.
    :``overlap``: How much to overlap ``shape1`` with ``shape2``. *Default*
                  *0*.
    :``top_offset``: If specified, once the overlap has been calculated, the
                     second shape will be vertically offset by ``top_offset``
                     from the "top" of the canvas. *Default 0*.
    :``fill``: The character to pad out the rest of the canvas if
               ``shape1.height() < shape2.height()`` or vice versa.
    :``join_left``: If true, will instead join ``shape2`` to the left of
                    ``shape1``. This is achieved by swapping the parameters.
                    *Default False*.
    :``skip_conflicts``: If true and ``overlap`` > 0, will not draw the parts of
                         ``shape2`` where they overlap with the parts of ``shape1``.
    :``collect``: If true, returns a ShapeCollection instead of a canvas.
                     *Default False*.
    :``offset_both``: If true, the ``top_offset`` will be applied to both
                      shapes. *Default False*.
    """
    cl_class = collection.ShapeCollection

    if (isinstance(shape1, collection.ShapeCollection) or isinstance(shape2, collection.ShapeCollection)) and not collect:
        warnings.warn("Passed a collection but ``collect=False``, assuming ``collect=True``.", SyntaxWarning, stacklevel=2)
        if isinstance(shape1, collection.ShapeCollection):
            cl_class = shape1.__class__
        else:
            cl_class = shape2.__class__
        collect = True

    if join_left:
        s1 = shape2
        shape2 = shape1
        shape1 = s1

    new_size = coord.Size(width=shape1.width()+shape2.width()-overlap, height=max(shape1.height(), shape2.height()))

    new_canvas = Shape(width=new_size.width, height=new_size.height, fill=fill)

    if offset_both:
        first_offset = coord.Coord(0, top_offset)

    if collect:
        if isinstance(shape1, collection.ShapeCollection):
            collect = shape1.copy()
        else:
            collect = cl_class()
            y = 0
            if offset_both:
                y = top_offset
            collect.append(collection.ShapeCoord(shape1, coord.Coord(max(collect.width(), 0), y)))
        if isinstance(shape2, collection.ShapeCollection):
            new_coord = coord.Coord(shape1.width()-overlap, top_offset)
            if shape1.width() < 0:
                new_coord = coord.Coord(0, 0)
            shape2.offset(new_coord)
            collect.extend(shape2)
        else:
            collect.append(collection.ShapeCoord(shape2, coord.Coord(shape1.width()-overlap, top_offset)))
        return collect
    else:
        new_canvas.draw_on(shape1, offset=first_offset, check_conflict=skip_conflicts)
        new_canvas.draw_on(shape2, offset=coord.Coord(shape1.width()-overlap, top_offset), check_conflict=skip_conflicts)
        return new_canvas

def underneath (shape1, shape2, left_offset=0, overlap=0, fill=None, join_top=False, skip_conflicts=False, offset_first=False, offset_second=True, collect=False):
    """
    Take two shapes and combine them into one by drawing ``shape1`` and then
    drawing ``shape2`` directly beneath it.

    :``shape1``: The first shape to be drawn. *Required*.
    :``shape2``: The second shape to be drawn; this will be drawn
                 underneath ``shape1``. *Required*.
    :``left_offset``: How many columns to offset the shapes by. *Default 0*.
    :``overlap``: How many rows ``shape2`` should overlap ``shape1``.
                  *Default 0*.
    :``fill``: Character to be used in filling out the canvas.
               *Default None*.
    :``join_top``: Draw ``shape2`` on top of ``shape1`` instead. *Default*
                   *False*.
    :``skip_conflicts``: Where ``shape2`` conflicts with ``shape1``, keep
                         ``shape1``'s glyphs. *Default False*
    :``offset_first``: Offset ``shape1`` by ``left_offset``. *Default False*.
    :``offset_second``: Offset ``shape2`` by ``left_offset``. *Default True*.
    :``collect``: If true, returns a ShapeCollection instead of a canvas.
                     *Default False*.
    """
    cl_class = collection.ShapeCollection

    if (isinstance(shape1, collection.ShapeCollection) or isinstance(shape2, collection.ShapeCollection)) and not collect:
        warnings.warn("Passed a collection but ``collect=False``, assuming ``collect=True``.", SyntaxWarning, stacklevel=2)
        if isinstance(shape1, collection.ShapeCollection):
            cl_class = shape1.__class__
        else:
            cl_class = shape2.__class__

        collect = True

    if join_top:
        s1 = shape2
        shape2 = shape1
        shape1 = s1

    new_size = coord.Size(width=max(shape1.width()+left_offset, shape2.width()+left_offset), height=shape1.height()+shape2.height())
    new_canvas = Shape(width=new_size.width, height=new_size.height-overlap, fill=fill)
    shape1_offset = coord.Coord(0, 0)
    shape2_offset = coord.Coord(0, shape1.height()-overlap)
    if offset_first:
        shape1_offset = coord.Coord(left_offset, 0)
    if offset_second:
        shape2_offset.x = left_offset
    if collect:
        if isinstance(shape1, collection.ShapeCollection):
            collect = shape1.copy()
        else:
            collect = cl_class()
            if collect.height() > 0:
                shape1_offset.y += collect.height()
                shape2_offset.y += collect.height()
            collect.append(collection.ShapeCoord(shape1, shape1_offset))

        if isinstance(shape2, collection.ShapeCollection):
            shape2.offset(shape2_offset)
            collect.extend(shape2)
        else:
            collect.append(collection.ShapeCoord(shape2, shape2_offset))
        return collect
    else:
        new_canvas.draw_on(shape1, shape1_offset)
        new_canvas.draw_on(shape2, shape2_offset, skip_conflicts)
        return new_canvas

def atop (shape1, shape2, left_offset=0, overlap=0, fill=None, join_bottom=False, skip_conflicts=False, offset_first=False, offset_second=True, collect=False):
    """
    Take two shapes and combine them into one by drawing ``shape1`` and then
    drawing ``shape2`` directly above it. This is an alias for ``underneath``
    with the ``join_top`` flag set to True.

    :``shape1``: The first shape to be drawn. *Required*.
    :``shape2``: The second shape to be drawn; this will be drawn
                 above ``shape1``. *Required*.
    :``left_offset``: How many columns to offset the shapes by. *Default 0*.
    :``overlap``: How many rows ``shape2`` should overlap ``shape1``.
                  *Default 0*.
    :``fill``: Character to be used in filling out the canvas.
               *Default None*.
    :``join_bottom``: Draw ``shape2`` beneath of ``shape1`` instead. *Default*
                      *False*.
    :``skip_conflicts``: Where ``shape2`` conflicts with ``shape1``, keep
                         ``shape1``'s glyphs. *Default False*
    :``offset_first``: Offset ``shape1`` by ``left_offset``. *Default False*.
    :``offset_second``: Offset ``shape2`` by ``left_offset``. *Default True*.
    :``collect``: If true, returns a ShapeCollection instead of a canvas.
                     *Default False*.
    """
    return underneath(shape1, shape2, left_offset, overlap, fill, not join_bottom, skip_conflicts, offset_first, offset_second, collect)
