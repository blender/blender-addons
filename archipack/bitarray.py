
import array

# -*- coding:utf-8 -*-

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110- 1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

# ----------------------------------------------------------
# Author: Stephen Leger (s-leger)
#
# ----------------------------------------------------------


class BitArray():

    def __init__(self, bitSize, fill=0):
        self.size = bitSize
        intSize = bitSize >> 5
        if (bitSize & 31):
            intSize += 1
        if fill == 1:
            fill = 4294967295
        else:
            fill = 0
        self.bitArray = array.array('I')
        self.bitArray.extend((fill,) * intSize)

    def __str__(self):
        return str(self.list)

    def bit_location(self, bit_num):
        return bit_num >> 5, bit_num & 31

    def test(self, bit_num):
        record, offset = self.bit_location(bit_num)
        mask = 1 << offset
        return(self.bitArray[record] & mask)

    def set(self, bit_num):
        record, offset = self.bit_location(bit_num)
        mask = 1 << offset
        self.bitArray[record] |= mask

    def clear(self, bit_num):
        record, offset = self.bit_location(bit_num)
        mask = ~(1 << offset)
        self.bitArray[record] &= mask

    def toggle(self, bit_num):
        record, offset = self.bit_location(bit_num)
        mask = 1 << offset
        self.bitArray[record] ^= mask

    @property
    def len(self):
        return len(self.bitArray)

    @property
    def copy(self):
        copy = BitArray(self.size)
        for i in range(self.len):
            copy.bitArray[i] = self.bitArray[i]
        return copy

    @property
    def list(self):
        return [x for x in range(self.size) if self.test(x) > 0]

    def none(self):
        for i in range(self.len):
            self.bitArray[i] = 0

    def reverse(self):
        for i in range(self.len):
            self.bitArray[i] = 4294967295 ^ self.bitArray[i]

    def all(self):
        for i in range(self.len):
            self.bitArray[i] = 4294967295
