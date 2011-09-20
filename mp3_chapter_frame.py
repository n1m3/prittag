# -*- coding: utf-8 -*-
"""
This module offers an additional ID3 Frames not implementet in mutagen,
ehich are CHAP and CTOC as defined in http://www.id3.org/id3v2-chapters-1.0.
At the moment this implementation supports write only.
"""
from struct import unpack, pack

from mutagen.id3 import IntegerSpec, StringSpec, BinaryDataSpec, Frame, ID3, BitPaddedInt

class CHAP(Frame):
    """
    The chapter frame specified in http://www.id3.org/id3v2-chapters-1.0
    """
    _framespec = [StringSpec('element_id',8),IntegerSpec('start'),
                  IntegerSpec('stop'), IntegerSpec('start_offset'),
                  IntegerSpec('stop_offset')]
    def __init__(self, element_id, start, stop, start_offset=0xffffffff,
                 stop_offset=0xffffffff, embeded_frames = []):
        super(CHAP,self).__init__(element_id=element_id,
                                  start=start,stop=stop,
                                  start_offset=0xffffffff,
                                 stop_offset=0xffffffff)
        self.embeded_frames = embeded_frames
    def _writeData(self):
        def save_frame(frame):
            #Copied from mutagen.id3.ID3
            flags = 0
            framedata = frame._writeData()
            datasize = BitPaddedInt.to_str(len(framedata), width=4)
            header = pack('>4s4sH', type(frame).__name__, datasize, flags)
            return header + framedata

        data = super(CHAP, self)._writeData()
        for frame in self.embeded_frames:
            frame = save_frame(frame)
            data += frame
        return data

class CTOC(Frame):
    """
    The table of contents frame specified in http://www.id3.org/id3v2-chapters-1.0
    """
    _framespec = [StringSpec('element_id',8),BinaryDataSpec('flags')]
    def __init__(self, element_id, has_parent, ordered, child_element_ids,
                 embeded_frames=[]):
        self.has_parent = has_parent
        self.ordered = ordered
        self.child_element_ids = child_element_ids
        flags = []
        for i in (self.has_parent, self.ordered):
            if i:
                flags.append('1')
            else:
                flags.append('0')
        flags = int(''.join(flags))
        flags = pack('>H', flags)
        self.embeded_frames = embeded_frames
        super(CTOC,self).__init__(element_id, flags)

    def _writeData(self):
        def save_frame(frame):
            #Copied from mutagen.id3.ID3
            flags = 0
            framedata = frame._writeData()
            datasize = BitPaddedInt.to_str(len(framedata), width=4)
            header = pack('>4s4sH', type(frame).__name__, datasize, flags)
            return header + framedata
        data = super(CTOC, self)._writeData()
        for frame in self.embeded_frames:
            frame = save_frame(frame)
            data += frame
        return data
