# -*- coding:utf-8 -*-

# <pep8 compliant>

"""
# Pyqtree

Pyqtree is a pure Python spatial index for GIS or rendering usage.
It stores and quickly retrieves items from a 2x2 rectangular grid area,
and grows in depth and detail as more items are added.
The actual quad tree implementation is adapted from
[Matt Rasmussen's compbio library](https://github.com/mdrasmus/compbio/blob/master/rasmus/quadtree.py)
and extended for geospatial use.


## Platforms

Python 2 and 3.


## Dependencies

Pyqtree is written in pure Python and has no dependencies.


## Installing It

Installing Pyqtree can be done by opening your terminal or commandline and typing:

    pip install pyqtree

Alternatively, you can simply download the "pyqtree.py" file and place
it anywhere Python can import it, such as the Python site-packages folder.


## Example Usage

Start your script by importing the quad tree.

    from pyqtree import Index

Setup the spatial index, giving it a bounding box area to keep track of.
The bounding box being in a four-tuple: (xmin, ymin, xmax, ymax).

    spindex = Index(bbox=(0, 0, 100, 100))

Populate the index with items that you want to be retrieved at a later point,
along with each item's geographic bbox.

    # this example assumes you have a list of items with bbox attribute
    for item in items:
        spindex.insert(item, item.bbox)

Then when you have a region of interest and you wish to retrieve items from that region,
just use the index's intersect method. This quickly gives you a list of the stored items
whose bboxes intersects your region of interests.

    overlapbbox = (51, 51, 86, 86)
    matches = spindex.intersect(overlapbbox)

There are other things that can be done as well, but that's it for the main usage!


## More Information:

- [Home Page](http://github.com/karimbahgat/Pyqtree)
- [API Documentation](http://pythonhosted.org/Pyqtree)


## License:

This code is free to share, use, reuse, and modify according to the MIT license, see LICENSE.txt.


## Credits:

- Karim Bahgat (2015)
- Joschua Gandert (2016)

"""


__version__ = "0.25.0"

# PYTHON VERSION CHECK
import sys


PYTHON3 = int(sys.version[0]) == 3
if PYTHON3:
    xrange = range


class _QuadNode(object):
    def __init__(self, item, rect):
        self.item = item
        self.rect = rect


class _QuadTree(object):
    """
    Internal backend version of the index.
    The index being used behind the scenes. Has all the same methods as the user
    index, but requires more technical arguments when initiating it than the
    user-friendly version.
    """
    def __init__(self, x, y, width, height, max_items, max_depth, _depth=0):
        self.nodes = []
        self.children = []
        self.center = (x, y)
        self.width, self.height = width, height
        self.max_items = max_items
        self.max_depth = max_depth
        self._depth = _depth

    def _insert(self, item, bbox):
        if len(self.children) == 0:
            node = _QuadNode(item, bbox)
            self.nodes.append(node)
            if len(self.nodes) > self.max_items and self._depth < self.max_depth:
                self._split()
        else:
            self._insert_into_children(item, bbox)

    def _intersect(self, rect, results=None):
        if results is None:
            results = set()
        # search children
        if self.children:
            if rect[0] <= self.center[0]:
                if rect[1] <= self.center[1]:
                    self.children[0]._intersect(rect, results)
                if rect[3] >= self.center[1]:
                    self.children[1]._intersect(rect, results)
            if rect[2] >= self.center[0]:
                if rect[1] <= self.center[1]:
                    self.children[2]._intersect(rect, results)
                if rect[3] >= self.center[1]:
                    self.children[3]._intersect(rect, results)
        # search node at this level
        for node in self.nodes:
            if (node.rect[2] >= rect[0] and node.rect[0] <= rect[2] and
                    node.rect[3] >= rect[1] and node.rect[1] <= rect[3]):
                results.add(node.item)
        return results

    def _insert_into_children(self, item, rect):
        # if rect spans center then insert here
        if (rect[0] <= self.center[0] and rect[2] >= self.center[0] and
                rect[1] <= self.center[1] and rect[3] >= self.center[1]):
            node = _QuadNode(item, rect)
            self.nodes.append(node)
        else:
            # try to insert into children
            if rect[0] <= self.center[0]:
                if rect[1] <= self.center[1]:
                    self.children[0]._insert(item, rect)
                if rect[3] >= self.center[1]:
                    self.children[1]._insert(item, rect)
            if rect[2] > self.center[0]:
                if rect[1] <= self.center[1]:
                    self.children[2]._insert(item, rect)
                if rect[3] >= self.center[1]:
                    self.children[3]._insert(item, rect)

    def _split(self):
        quartwidth = self.width / 4.0
        quartheight = self.height / 4.0
        halfwidth = self.width / 2.0
        halfheight = self.height / 2.0
        x1 = self.center[0] - quartwidth
        x2 = self.center[0] + quartwidth
        y1 = self.center[1] - quartheight
        y2 = self.center[1] + quartheight
        new_depth = self._depth + 1
        self.children = [_QuadTree(x1, y1, halfwidth, halfheight,
                                   self.max_items, self.max_depth, new_depth),
                         _QuadTree(x1, y2, halfwidth, halfheight,
                                   self.max_items, self.max_depth, new_depth),
                         _QuadTree(x2, y1, halfwidth, halfheight,
                                   self.max_items, self.max_depth, new_depth),
                         _QuadTree(x2, y2, halfwidth, halfheight,
                                   self.max_items, self.max_depth, new_depth)]
        nodes = self.nodes
        self.nodes = []
        for node in nodes:
            self._insert_into_children(node.item, node.rect)
