#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct
from StringIO import StringIO

container_atoms = ('moov', 'udta', 'meta', 'ilst', 'trak', 'mdia', 'minf')

def read_atom(file_object):
    header = file_object.read(8)
    if len(header) == 0:
        return None
    try:
        atom_length, atom_type = struct.unpack('>i4s', header)
        if atom_length == 1:
            #extended size atom
            atom_length = struct.unpack('>Q', file_object.read(8))
        if atom_length == 0:
            #top level atom -> read the rest of the file object
            atom_data = file_object.read()
        else:
            atom_data = file_object.read(atom_length-8)
        atom = {'length' : atom_length, 'data' : atom_data, 'type' : atom_type}
        return atom
    except:
        return None

def get_atom_tree(file_object):
    def get_atoms(file_object):
        atoms = []
        while True:
            atom = read_atom(file_object)
            children = []
            if atom == None:
                break
            if atom['type'] in container_atoms:
                virtual_file = StringIO(atom['data'])
                for i in get_atoms(virtual_file):
                    if i != None:
                        children.append(i)
                virtual_file.close()
                atom['children'] = children
                del(atom['data'])
            atoms.append(atom)
        return atoms

    atom_tree = get_atoms(file_object)
    return atom_tree

def test():
    with open('test.mp4', 'rb') as mp4:
        tree = get_atom_tree(mp4)
    return tree
tree = test()
