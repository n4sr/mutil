import pathlib
import contextlib
import shutil
import tempfile

try:
    import pytest
except ImportError:
    print('error: pytest module not found. try: pip install pytest')
    exit(1)

from ..__main__ import Song, clean_string, parse_tracknumber

SAMPLE_DIR = pathlib.Path(__file__).with_name('samples')
assert SAMPLE_DIR.exists(), 'SAMPLE_DIR missing'
SONGFILE = SAMPLE_DIR.joinpath('songfile.mp3')
assert SONGFILE.exists(), 'songfile.mp3 missing'


@contextlib.contextmanager
def make_temp_directory():
    temp_dir = pathlib.Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


def test_clean_string():
    assert clean_string("'") == ''
    assert clean_string('@') == 'a'
    assert clean_string('$') == 'S'
    assert clean_string('&') == 'and'
    assert clean_string('!#%^*()') == ''
    assert clean_string('<>test+-string()') == 'test_string'


def test_parse_tracknumber():
    assert parse_tracknumber('1') == 1
    assert parse_tracknumber('009') == 9
    assert parse_tracknumber('2/10') == 2
    assert parse_tracknumber('5\x00') == 5


def test_Song_rename_existing_file():
    # exception when attempting to overwite an existing file
    with make_temp_directory() as temp_dir:
        existing_file = temp_dir.joinpath('existing_file')
        existing_file.touch()
        song_path = shutil.copy(SONGFILE, temp_dir.joinpath(SONGFILE.name))
        song = Song(song_path)
        with pytest.raises(FileExistsError):
            song.rename(existing_file)


def test_Song_rename_mkdir():
    # make parent directories as needed
    with make_temp_directory() as temp_dir:
        dest = temp_dir.joinpath('one','two',SONGFILE.name)
        song_path = shutil.copy(SONGFILE, temp_dir.joinpath(SONGFILE.name))
        song = Song(song_path)
        song.rename(dest)
        assert dest.exists()


def test_Song_sort():
    with make_temp_directory() as temp_dir:
        dest = temp_dir.joinpath('test_artist','test_album','songfile.mp3')
        song_path = shutil.copy(SONGFILE, temp_dir.joinpath(SONGFILE.name))
        song = Song(song_path)
        song.sort(temp_dir)
        assert song.path == dest


def test_Song_format_filename():
    song = Song(SONGFILE)
    assert song.format_filename().name == '01_Test_Song.mp3'


def test_Song_transcode():
    # TODO: loop through codec_config keys and transcode
    # TODO: add tests to check if output file is playable
    with make_temp_directory() as temp_dir:
        song_path = shutil.copy(SONGFILE, temp_dir.joinpath(SONGFILE.name))
        song = Song(song_path)
        song.transcode('opus')
        assert song.path.with_suffix('.ogg').exists()


def test_Song_remove_cover():
    # TODO: add embeded cover to SONGFILE
    # TODO: use tinytag to check input and output files for cover images
    pass