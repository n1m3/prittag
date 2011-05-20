#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct
from StringIO import StringIO
from collections import namedtuple

AtomObject = namedtuple('AtomObject', ('length', 'type', 'data', 'level'))
AtomTreeObject = namedtuple('AtomTreeObject', ('length', 'type',
                                               'data','children'))
AtomTree = namedtuple('AtomTree', ('children'))
container_atoms = ('moov', 'udta', 'meta', 'ilst', 'trak', 'mdia', 'minf')

def read_atom(file_object, level=0):
    header = file_object.read(8)
    if len(header) == 0:
        return None
    try:
        atom_length, atom_type = struct.unpack('>i4s', header)
        atom_data = file_object.read(atom_length-8)
        atom = AtomObject(atom_length, atom_type, atom_data, level)
        return atom
    except:
        return None

def walk_atom_tree(file_object, level=0):
    while True:
        atom = read_atom(file_object, level)
        if atom == None:
            break
        if atom.type in container_atoms:
            virtual_file = StringIO(atom.data)
            for i in walk_atom_tree(virtual_file, level=level+1):
                yield i
            virtual_file.close()
        else:
            yield atom

def test():
    with open('test.mp4', 'rb') as mp4:
        for atom in walk_atom_tree(mp4):
            print "%s %s %d" % ('-'*4*(atom.level+1), atom.type, atom.length)
test()
