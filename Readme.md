#Prittag

Prittag is a modified version of a tool I build for [Radio Tux](http://blog.radiotux.de/).
I created this version to serve the request made by Tim Pritlove in the [episode 01](http://tim.geekheim.de/2011/03/26/ls001-audio-dateiformate-feeds-und-itunes/) of the podcast "Der Lautsprecher" for a tool which could help him with automating his podcasts generation, so he easily could offer multiple audio formats without more work.

It writes the following tags to multiple OGG, MP3 or MP4 files:

- album
- album artist (album-artist)
- artist
- comment
- composer
- date
- disc
- genre
- lyrics
- number of discs (number-of-discs)
- number of tracks (number-of-tracks)
- title
- track

Additionally it can add an albumart (cover) to them.
It has native support for MP3 chapters and can embed the supported subset into MP4 files for convenience using mp4chaps.

The name was chosen according to the amazing tool [prittorrent](https://github.com/astro/prittorrent).

##Dependencies

- [Python 2.6](http://python.org) or higher (Not Python 3.x)
- [Mutagen](http://code.google.com/p/mutagen/)

##Installation
Download it to a place of your choice and install all dependencies.

##Usage
Prittag expects a XML file and at least one audio file as arguments.
The XML file tells Prittag which tags it should write into the files and is expected to look like example.xml.
By default Prittag will perform a  white space stripping on every tag and every line of multi line tags.
You can enable and disable this as well globally as for every single tag by adding the option `strip-space` and setting it either to `"yes"` or `"no"`.
For example:

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<tags strip-space="no">
    <title>FooBar</title>
    <lyrics strip-space="yes">
    Foo
    Bar
    </lyrics>
</tags>
```

Call Prittag from the command line like this: `./prittag.py foo.xml bar.mp3 bar.oga bar.m4a`

###Cover
* If you want to embed a cover art, you can provide the `<cover>` tag.

```xml
<tags>
    <cover src="cover.jpg" />
</tags>
```

* Prittag only supports embedding of JPG files.
* All paths given in the XML file are either absolute or relative to the location of this XML file.

###Chapters
If you want Prittag to embed chapters, add a `<chapters>` section into the `<tags>` section like this:

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<tags>
    <title>FooBar</title>
    <chapters>
        <chapter>
            <start>00:00:00.000</start>
    	    <stop>00:00:25.000</stop>
            <title>Opening</title>
    	    <description>Some
    	    Description
	        Text</description>
        	<image src="image.jpg" />
        </chapter>
    </chapters>
</tags>
```
* `<start>` and `<stop>` must have the format `hh:MM:ss:mm` where `MM` refers to minute and `mm` to milliseconds
* Each tag within a `<chapter>` tag may only be used once.
* And again:
    * Prittag only supports embedding of JPG files.
    * All paths given in the XML file are either absolute or relative to the location of this XML file.

####MP4
As mentioned before Prittag can embed a certain subset of the informatin from the `<chapters>` section into MP4 files.
For this purpose you must have *mp4chaps* from the [MP4v2 Library](http://code.google.com/p/mp4v2/) installed and availe on your path.
Set the `use_mp4chaps` attribute to `yes`:

```xml
<chapters use_mp4chaps="yes">
    <chapter>
...
```

The supported subset includes the following tags:

* `<start>`
* `<stop>` (reqired by the parser, but in fact not used)
* `<title>`
