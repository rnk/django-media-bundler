# media_bundler/bundle.py

"""A simple 2D bin packing algorithm for making sprites."""

import math


class Box(object):

    """A simple 2D rectangle with width and height attributes.  Immutable."""

    def __init__(self, width, height):
        self.__width = width
        self.__height = height

    @property
    def width(self): return self.__width

    @property
    def height(self): return self.__height

    def __eq__(self, other):
        return self.width == other.width and self.height == other.height

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return "Box(%r, %r)" % (self.width, self.height)


def pack_boxes(boxes, max_width=None):
    """Approximately packs boxes in a rectangle with minimal area.

    Basic algorithm:
    - Pick a width so that our rectangle comes out squarish.
    - Sort the boxes by their width.
    - While there are more boxes, attempt to fill a horizontal strip:
      - For each box that we haven't already placed, if it fits in the strip,
        place it, otherwise continue checking the rest of the boxes.
    """
    if max_width is None:
        total_area = sum(box.width * box.height for box in boxes)
        max_width = max(max(box.width for box in boxes),
                        int(math.sqrt(total_area)))
    unplaced = sorted(boxes, key=lambda box: (-box.height, -box.width))
    packing = []
    y_off = 0
    while unplaced:
        strip_width = 0
        strip_height = 0
        next_unplaced = []
        for box in unplaced:
            if strip_width + box.width <= max_width:
                packing.append((strip_width, y_off, box))
                strip_width += box.width
                strip_height = max(strip_height, box.height)
            else:
                next_unplaced.append(box)
        y_off += strip_height
        unplaced = next_unplaced
    return (max_width, y_off, packing)


def boxes_overlap((x1, y1, box1), (x2, y2, box2)):
    """Return True if the two boxes at (x1, y1) and (x2, y2) overlap."""
    left1 = x1
    top1 = y1
    right1 = x1 + box1.width
    bottom1 = y1 + box1.height
    left2 = x2
    top2 = y2
    right2 = x2 + box2.width
    bottom2 = y2 + box2.height
    return ((left2 <= left1  <  right2 and top2 <= top1    <  bottom2) or
            (left2 <  right1 <= right2 and top2 <= top1    <  bottom2) or
            (left2 <= left1  <  right2 and top2 <  bottom1 <= bottom2) or
            (left2 <  right1 <= right2 and top2 <  bottom1 <= bottom2))


def check_no_overlap(packing):
    """Return True if none of the boxes in the packing overlap."""
    # TODO(rnk): It would be great if we could avoid comparing each box twice.
    for left in packing:
        for right in packing:
            if left == right:
                continue
            if boxes_overlap(left, right):
                return False
    return True
