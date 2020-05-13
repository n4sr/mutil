#!/usr/bin/env python3
import logging as log
import argparse
import os
import pathlib
import re
import subprocess

from tinytag import TinyTag

from .codec_options import codec_config
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
        type=pathlib.Path,
    )
    parser.add_argument(
        '--remove-cover',
        action='store_true',
        help='removes cover art without re-encoding',
    )
    parser.add_argument(
        '-t',
        choices=codec_config.keys(),
        dest='transcode',
        help='transcode files using ffmpeg into specified format',
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
    required = (args.rename, args.sort, args.transcode, args.remove_cover)

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
        if args.sort: s.sort(args.sort)
        if args.rename: s.rename(s.format_filename())
        if args.remove_cover: s.remove_cover()
        if args.transcode: s.transcode(args.transcode)


def get_loglevel():
    return log.getLevelName(log.getLogger().getEffectiveLevel()).lower()


def clean_string(string, trim=None):
    '''
    Replaces non-alphanumeric characters in string with
    underscores and other common substitutions.
    '''
    exclude = r'[^a-zA-Z0-9]+'
    substitutions = {
        "'": '',
        '$': 'S',
        '@': 'a',
        '&': 'and',
    }
    pattern = '|'.join(re.escape(key) for key in substitutions.keys())
    pattern = re.compile(pattern)
    string = pattern.sub(lambda x: substitutions[x.group()], string)
    string = re.sub(fr'^{exclude}|{exclude}$', '', string)
    string = re.sub(fr'{exclude}', '_', string)
    if trim: string = string[:trim]
    return string


def parse_tracknumber(s):
    '''
    Takes string and removes non-numeric characters. Returns an
    integer. Returns None if string is empty.
    '''
    if not isinstance(s, str):
        raise TypeError(f'expects str; got {type(s).__name__}')
    if len(s) < 1:
        return None
    return int(re.match(r'^[0-9]+', s).group(0))


class Song:
    def __init__(self, path):
        tags = TinyTag.get(path, duration=False)
        self.path = pathlib.Path(path)
        self.title = tags.title
        self.album = tags.album
        self.artist = tags.artist
        self.track = parse_tracknumber(tags.track)

    def format_filename(self):
        '''Returns a filename string based on the song's metadata.'''
        s = str()
        if self.track: s += f'{self.track:02d}_'
        if self.title: s += clean_string(self.title,
                                         trim=64-len(s+self.path.suffix))
        if len(s) < 1: raise ValueError(f'insufficent metadata: {self.path}')
        return self.path.with_name(s.rstrip('_') + self.path.suffix)

    def rename(self, dest):
        '''Renames file to match metadata.'''
        if not self.path.is_file():
            raise FileNotFoundError(str(self.path))
        if dest.exists() and not self.path.samefile(dest):
            raise FileExistsError(str(dest))
        if self.path == dest:
            return
        if not dest.parent.exists():
            dest.parent.mkdir(exist_ok=True, parents=True, mode=0o755)
        self.path.rename(dest)
        self.path = dest

    def sort(self, path):
        '''Sorts file into folders within a specified directory'''
        artist = clean_string(self.artist, trim=64).lower()
        album = clean_string(self.album, trim=64).lower()
        dest = path.joinpath(artist, album, self.path.name)
        self.rename(dest)

    def transcode(self, codec):
        '''Transcodes file into the specified codec.'''
        if codec not in codec_config.keys():
            raise ValueError('unsupported codec: ' + codec)
        output = self.path.with_suffix(codec_config[codec]['suffix'])
        if output.exists():
            raise FileExistsError(str(output))
        print(f'transcoding: {self.path}...')
        subprocess.run([
            'ffmpeg',
            '-hide_banner',
            '-v',get_loglevel(),
            '-i',str(self.path),
            *codec_config[codec]['options'],
            str(output),
        ])

    def remove_cover(self):
        '''
        Removes embeded cover art using `ffmpeg`. Renames the original
        file and appends `.old` to it. Does not re-encode.
        '''
        temp = self.path.with_name('temp.' + self.path.name)
        old = self.path.parent.joinpath('mutil_backup~', self.path.name)
        if not old.parent.exists():
            old.parent.mkdir(mode=0o755)
        subprocess.run((
            'ffmpeg',
            '-hide_banner',
            '-v',get_loglevel(),
            '-i',str(self.path),
            '-c:a','copy',
            '-vn',
            str(temp)
            ))
        try:
            self.path.rename(old)
        except FileExistsError:
            temp.unlink()
            raise
        temp.rename(self.path)


if __name__ == "__main__":
    main()