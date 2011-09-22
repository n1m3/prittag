#!/usr/bin/env python
# -*- coding: utf-8 -*-

#############################################################################
#  prittag - a tool for tagging mp3, ogg and aac files                      #
#                                                                           #
#  Copyright (c) 2010 Nils Mehrtens                                         #
#                                                                           #
#  prittag is free software; you can redistribute it and/or modify it       #
#  under the terms of the GNU General Public License                        #
#  as published by the Free Software Foundation;                            #
#  either version 3 of the License, or (at your option) any later version.  #
#  prittag is distributed in the hope that it will be useful, but           #
#  WITHOUT ANY WARRANTY; without even the implied warranty of               #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.                     #
#  See the GNU General Public License for more details.                     #
#                                                                           #
#  You should have received a copy of the GNU General Public License        #
#  along with this program; if not, see <http://www.gnu.org/licenses/>.     #
#############################################################################

import sys
import os
import base64
import string
import re
import traceback
import subprocess
from xml.etree import ElementTree

from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
from mutagen.mp4 import MP4, MP4Cover
import mutagen.id3 as id3

from mp3_chapter_frame import CHAP, CTOC


def parse_xml(path):
    tags = {}
    empty_tags = 0
    disable_strip_space_globally = False
    try:
        with open(path, 'r') as f:
            data = f.read()
    except:
        print 'failed to read %s' % str(path)
        sys.exit(1)
    try:
        xml = ElementTree.XML(data)
    except:
        print 'parsing XML failed!'
        traceback.print_exc()
        sys.exit(1)
        if 'strip-space' in xml.keys():
            if xml.get('strip-space') in ['No', 'no']:
                disable_strip_space_globally = True
    for child in xml.getchildren():
        key = str(child.tag)
        if key == 'chapters':
            chapters = child.getchildren()
            value = parse_chapters(chapters, disable_strip_space_globally)
        elif key == 'cover':
            value = child.get('src')
            if value:
                value = get_cover_path(value, path)
            else:
                print 'Error: cover tag has no valid src attribute.'
                sys.exit(1)
        else:
            value = child.text
            if value == None:
                empty_tags += 1
                continue
            else:
                value = unicode(value)
                value = strip_child(child, value, disable_strip_space_globally)

        tags[key] = value
    if len(tags) + empty_tags < len(xml.getchildren()):
        print "Error: there are duplicate tags!"
        sys.exit(1)
    for tag in tags:
        bad = False
        if tag in ['track', 'number-of-tracks', 'disc', 'number-of-discs']:
            value = tags[tag]
            try:
                value = int(value)
            except:
                bad = True
            if value < 0:
                bad = True
        if bad:
            print 'Bad value in <%s>: "%s" is not a positive integer!' %\
                    (str(tag), str(value))
            sys.exit(1)
    return tags


def parse_chapters(chapters, disable_strip_space_globally):
    use_mp4chaps = False
    if 'use_mp4chaps' in chapters.keys():
        if chapters.ge('use_mp4chaps') in ['Yes', 'yes']:
            use_mp4chaps = True
    chapters = [parse_chapter(chapter, disable_strip_space_globally)
                for chapter in chapters]
    return {'use_mp4chaps': use_mp4chaps, 'chapters': chapters}


def parse_chapter(chapter, disable_strip_space_globally):
    time_reg = re.compile('(\d\d):(\d\d):(\d\d).(\d\d\d)')
    parsed_chapter = {}
    for item in chapter:
        tag = item.tag
        if tag in ['start', 'stop']:
            value = item.text
            value = value.replace('\n', '').replace('\r', '').strip()
            time_ = time_reg.match(value)
            if time_ == None:
                print 'Error: %s is not a valid timestamp.' % str(value)
                print 'Please use the format hh:MM:ss.mmm, where M refers to'\
                        'minute and m to millisecond.'
                sys.exit(1)
            else:
                parsed_chapter[tag] = time_.groups()
        elif tag in ['description', 'title']:
            value = item.text
            value = strip_child(item, value, disable_strip_space_globally)
            parsed_chapter[tag] = value
        elif tag == 'image':
            src = item.get('src')
            if not src:
                print 'Error: image tag has no valid src attribute.'
                sys.exit(1)
            else:
                src = src.strip()
                parsed_chapter[tag] = src
        else:
            print 'Error: %s is not a valid chapter tag.' % tag
            sys.exit(1)
    return parsed_chapter


def get_cover_path(path, path_to_config):
    config_folder = os.path.split(path_to_config)[0]
    if path != os.path.abspath(path):
        #Make relativ path relativ to config file
        path = os.path.join(config_folder, path)
    return path

def strip_child(child, value, disable_strip_space_globally):
    if disable_strip_space_globally:
        if 'strip-space' in child.keys():
            if child.get('strip-space') in ['Yes', 'yes']:
                value = strip_string(value)
    else:
        if 'strip-space' in child.keys():
            if child.get('strip-space') not in ['No', 'no']:
                value = strip_string(value)
        else:
            value = strip_string(value)
    return value


def strip_string(string):
    if len(string.splitlines()) > 1:
        new_string = '\n'.join([i.strip() for i in string.splitlines()])
        new_string = new_string[1:]  # remove \n at the beginning of the string
        if string[len(string) - 1] != '\n':
            new_string = new_string[:len(new_string) - 1]
            #remove \n at the end of the string if wasn't present before
        return new_string

    else:
        return string.strip()


def tag_file(path, tags):
    file_type = get_file_type(path)
    if file_type in ['ogg', 'oga']:
        write_tags_to_ogg(path, tags)
    elif file_type == 'mp3':
        write_tags_to_mp3(path, tags)
    elif file_type in ['mp4', 'm4a', 'aac']:
        write_tags_to_mp4(path, tags)
    else:
        raise TypeError("%s is neither a mp3 nor an ogg nor a mp4 file" % path)


def get_file_type(path):
    ext = os.path.splitext(path)[1]
    ext = string.replace(ext, '.', '')
    ext = ext.lower()
    return ext


def write_tags_to_ogg(path, tags):
    audio = OggVorbis(path)
    for dest, source in [['TITLE', 'title'], ['COMPOSER', 'composer'],
                         ['ALBUM', 'album'], ['DATE', 'date'],
                         ['ARTIST', 'artist'], ['GENRE', 'genre'],
                         ['ALBUMARTIST', 'album-artist'],
                         ['TRACKNUMBER', 'track'],
                         ['TRACKTOTAL', 'number-of-tracks'], ['DISCNUMBER',
                          'disc'], ['COMMENT', 'comment']]:
        if source in tags:
            audio[dest] = tags[source]
    if 'cover' in tags:
        audio['coverartmime'] = 'image/jpeg'
        audio['coverartdescription'] = 'Cover'
        audio['coverarttype'] = '3'
        audio['coverart'] = get_ogg_coverart(tags['cover'])
    audio.save()


def get_ogg_coverart(path):
    with open(path, 'rb') as f:
        data = f.read()
    data = base64.b64encode(data)
    return data


def write_tags_to_mp3(path, tags):
    audio = MP3(path)
    for i, tag in [['title', 'TIT2'], ['artist', 'TPE1'], ['album', 'TALB'],
                   ['date', 'TDRC'], ['composer', 'TCOM'], ['genre', 'TCON'],
                   ['lyrics', 'USLT'], ['album-artist', 'TPE2'],
                   ['disc', 'TPOS'], ['comment', 'COMM']]:
        if i in tags:
            if tag == 'USLT':
                tag = id3.Frames[tag](encoding=3, text=tags[i], lang='eng')
                audio[tag.HashKey] = tag
            elif tag == 'COMM':
                tag = id3.Frames[tag](encoding=3, text=tags[i], lang='eng')
                audio[tag.HashKey] = tag
            else:
                tag = id3.Frames[tag](encoding=3, text=tags[i])
                audio[tag.HashKey] = tag
    if 'track' in tags:
        if 'number-of-tracks' in tags:
            num_tracks = tags['number-of-tracks']
        else:
            num_tracks = 0
        track_num = "%d/%d" % (int(tags['track']), int(num_tracks))
        tag = id3.Frames['TRCK'](encoding=3, text=track_num)
        audio[tag.HashKey] = tag
    if 'cover' in tags:
        image = get_mp3_coverart(tags['cover'])
        image = id3.APIC(3, 'image/jpeg', 3, 'Cover', image)
        audio[image.HashKey] = image
    if 'chapters' in tags:
        write_mp3_chapters(audio, tags['chapters']['chapters'])
    audio.save()


def get_mp3_coverart(path):
    with open(path, 'rb') as f:
        data = f.read()
    return str(data)


def write_mp3_chapters(audio, chapters):
    z = 0
    chapter_ids = []
    for chapter in chapters:
        z += 1
        chap_id = 'chap%s' % str(z).zfill(4)
        start = get_milliseconds(chapter['start'])
        stop = get_milliseconds(chapter['stop'])
        embeded_elements = []
        for tag in chapter:
            if tag == 'title':
                embeded_elements.append(id3.TIT2(encoding=3,
                                                 text=chapter[tag]))
            elif tag == 'description':
                embeded_elements.append(id3.TIT3(encoding=3,
                                                 text=chapter[tag]))
            elif tag == 'image':
                image = get_mp3_coverart(chapter[tag])
                image = id3.APIC(3, 'image/jpeg', 3, '', image)
                embeded_elements.append(image)
        chap = CHAP(element_id=chap_id, start=start, stop=stop,
              embeded_frames=embeded_elements)
        audio[chap_id] = chap
        chapter_ids.append(chap_id)
    ctoc = CTOC('ctoc0001', False, True, chapter_ids)
    audio['ctoc0001'] = ctoc


def get_milliseconds(time_stamp):
    hours, minutes, seconds, milliseconds = time_stamp
    hours, minutes = int(hours), int(minutes)
    seconds, milliseconds = int(seconds), int(milliseconds)
    return milliseconds + seconds * 1000 + minutes * 60 * 1000 +\
            hours * 60 * 60 * 1000


def write_tags_to_mp4(path, tags):
    audio = MP4(path)
    for dest, source in [['\xa9nam', 'title'], ['\xa9wrt', 'composer'],
                         ['\xa9alb', 'album'], ['\xa9day', 'date'],
                         ['\xa9ART', 'artist'], ['\xa9gen', 'genre'],
                         ['\xa9lyr', 'lyrics'], ['aART', 'album-artist'],
                         ['\xa9cmt', 'comment']]:
        if source in tags:
            audio[dest] = [tags[source]]
    if 'track' in tags:
        if 'number-of-tracks' in tags:
            num_tracks = int(tags['number-of-tracks'])
        else:
            num_tracks = 0
        audio['trkn'] = [(int(tags['track']), num_tracks)]
    if 'disc' in tags:
        if 'number-of-discs' in tags:
            num_disks = int(tags['number-of-discs'])
        else:
            num_disks = 0
        audio['disk'] = [(int(tags['disc']), num_disks)]
    if 'cover' in tags:
        audio['covr'] = [get_mp4_coverart(tags['cover'])]
    audio.save()
    if 'chapters' in tags:
        chapters = tags['chapters']
        if chapters['use_mp4chaps']:
            chapters = chapters['chapters']
            write_mp4_chapters(path, chapters)


def get_mp4_coverart(path):
    with open(path, 'rb') as f:
        data = f.read()
    cover = MP4Cover(data)
    return cover


def write_mp4_chapters(path, chapters):
    chapter_path = os.path.splitext(path)[0] + '.chapters.txt'
    data = ""
    for chapter in chapters:
        line = u"%s %s\n" % (chapter['start'], chapter['title'])
        line = line.encode('utf-8')
        data = ''.join((data, line))
    if data:
        try:
            with open(chapter_path, 'w') as f:
                f.write(data)
        except:
            print "couldn't write to %s" % chapter_path
        else:
            call_mp4_chaps(path)
            os.remove(chapter_path)


def call_mp4_chaps(path):
    popen = subprocess.Popen('mp4chaps -i %s' % path, shell=True)
    popen.wait()

if __name__ == "__main__":
    print '''prittag  Copyright (C) 2011 Nils Mehrtens
This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions; see http://www.gnu.org/licenses/gpl.html for details.
'''
    if len(sys.argv) < 3:
        print 'usage: %s <xml file with tags> <file to tag> '\
                '[<file to tag> ...]' % sys.argv[0]
        sys.exit(1)
    else:
        args = sys.argv[1:]
        for path in args:
            if not os.path.exists(path):
                print "%s doesn't exist." % path
                sys.exit(1)
            elif not os.path.isfile(path):
                print "%s is not a file." % path
                sys.exit(1)
        config = args[0]
        files = args[1:]
        tags = parse_xml(config)
        for file in files:
            print "Tagging %s ..." % file
            tag_file(file, tags)
