codec_config = {
    'opus': {
        'suffix': '.ogg',
        'options': (
            '-acodec','libopus',
            '-vbr','off',
            '-b:a','192k',
            '-sample_fmt','s16',
            '-vn',
        )},
    'mp3-320': {
        'suffix': '.mp3',
        'options': (
            '-acodec','libmp3lame',
            '-b:a','320k',
            '-vn',
        )},
    'mp3-128': {
        'suffix': '.mp3',
        'options': (
            '-acodec','libmp3lame',
            '-b:a','128k',
            '-vn',
        )}
    }