#!/usr/bin/env python3
import logging as log
import argparse
import os
import pathlib
import re
import subprocess

from tinytag import TinyTag

from .version import __version__


def main():
    log.basicConfig(format='%(levelname)s: %(message)s')

    parser = argparse.ArgumentParser(prog='mutil')
    parser.add_argument(
        'files',
        metavar='file',
        nargs='*',
        type=pathlib.Path,
    )
    parser.add_argument(
        '-r',
        action='store_true',
        dest='rename',
        help='renames music',
    )
    parser.add_argument(
        '-s',
        dest='sort',
        help='sorts music into folders within a directory',
        metavar='directory',
        nargs=1,
        type=pathlib.Path,
    )
    parser.add_argument(
        '--remove-cover',
        action='store_true',
        help='removes cover art without re-encoding'
    )
    parser.add_argument(
        '-t',
        choices=['opus', 'mp3'],
        dest='transcode',
        help='transcode files using ffmpeg into specified format',
        nargs=1,
        type=str,
    )
    parser.add_argument(
        '--version',
        action='store_true',
        help='print version and exit',
    )

    logparser = parser.add_mutually_exclusive_group()
    logparser.add_argument(
        '-v',
        action='store_const',
        const='INFO',
        dest='loglevel',
        help='explain what is being done',
    )
    logparser.add_argument(
        '-q',
        action='store_const',
        const='ERROR',
        dest='loglevel',
        help='suppress warnings',
    )

    args = parser.parse_args()
    required = (args.rename,args.sort,args.transcode,args.remove_cover)

    if args.loglevel:
        log.getLogger().setLevel(args.loglevel)
    if args.version:
        print(__version__)
        exit()
    if len(args.files) < 1 or not any(required):
        parser.print_usage()
        exit()

    for file in args.files:
        s = Song(file)
        if args.sort: s.sort(args.sort[0])
        if args.rename: s.rename()
        if args.remove_cover: s.remove_cover()
        if args.transcode: s.transcode(args.transcode[0])


def get_loglevel():
    return log.getLevelName(log.getLogger().getEffectiveLevel()).lower()


def clean_str(s, repl_chr, trunc=None):
    '''
    Removes non-alphanumeric characters from string and replaces
    special characters with their most common substitution.
    '''
    # substitute char with d[char]
    exclude = r'[^a-zA-Z0-9]+'
    d = {
        "'": '',
        '$': 'S',
        '@': 'a',
        '&': 'and'
    }
    pattern = re.compile('|'.join(re.escape(key) for key in d.keys()))
    s = pattern.sub(lambda x: d[x.group()], s)
    # remove leading and trailing excluded characters
    s = re.sub(fr'^{exclude}|{exclude}$', '', s)
    s = re.sub(fr'{exclude}', repl_chr, s)
    if trunc: s = s[:trunc]
    return s


def clean_tracknumber(s):
    '''
    Takes string and removes non-numeric characters. Returns an
    integer. Returns None if string is empty.
    '''
    if not s: return None
    try: return int(s)
    except ValueError: return int(re.match(r'[0-9]+', s).group(0))


def move(src, dest):
    '''Renames a file without overwriting the destination.'''
    if not src.is_file():
        raise FileNotFoundError(str(src))
    if dest.exists() and not src.samefile(dest):
        raise FileExistsError(str(dest))
    if src == dest:
        return
    if not dest.parent.exists():
        dest.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
        log.info(f'mkdirs: {str(dest.parent)}')
    src.rename(dest)
    log.info(f'mv: {str(src)}  {str(dest)}')


class Song:
    def __init__(self, path):
        tags = TinyTag.get(path, duration=False)
        self.path = pathlib.Path(path)
        self.title = tags.title
        self.album = tags.album
        self.artist = tags.artist
        self.track = clean_tracknumber(tags.track)

    def _format_filename(self):
        '''Returns a filename string based on the song's metadata.'''
        ext = self.path.suffix
        s = str()
        if self.track: s += f'{self.track:02d}_'
        if self.title: s += clean_str(self.title, '_', trunc=64-len(s+ext))
        if len(s) < 1: raise ValueError(f'insufficent metadata: {self.path}')
        return s.rstrip('_') + ext

    def rename(self):
        '''Renames file to match metadata.'''
        dest = self.path.with_name(self._format_filename())
        move(self.path, dest)
        self.path = dest

    def sort(self, path):
        '''Sorts file into folders within a specified directory'''
        artist = clean_str(self.artist, ' ', trunc=64).lower()
        album = clean_str(self.album, ' ', trunc=64).lower()
        dest = path.joinpath(artist, album, self.path.name)
        move(self.path, dest)
        self.path = dest

    def transcode(self, format):
        '''Transcodes file into the specified format.'''
        path = self.path
        ffmpeg = ['ffmpeg','-v',get_loglevel(),'-hide_banner','-i']
        if format == 'opus':
            ext = '.ogg'
            opts = ['-acodec','libopus','-vbr','off',
                    '-b:a','192k','-sample_fmt','s16','-vn']
        elif format == 'mp3':
            ext = '.mp3'
            opts = ['-acodec','libmp3lame','-b:a','320k','-vn']
        else:
            raise ValueError(format)
        output = path.with_suffix(ext)
        cmd = (ffmpeg + [str(path)] + opts + [str(output)])
        subprocess.run(cmd)

    def remove_cover(self):
        '''
        Removes embeded cover art using `ffmpeg`. Renames the
        original file and appends `.old` to it. Does not
        re-encode.
        '''
        path = self.path
        temp = path.with_name('temp.' + path.name)
        old = pathlib.Path(str(path) + '.old')
        subprocess.run(
            ['ffmpeg','-v',get_loglevel(),'-hide_banner',
            '-i',str(path),'-c:a','copy','-vn',str(temp)]
        )
        move(path, old)
        move(temp, path)


if __name__ == "__main__":
    main()