"""Build the reader's minimal rare-Han fallback from a licensed HanaMinB font.

Build-only dependencies: fonttools[woff]. No system font is installed.
Usage: python backend/tools/dp_build_reader_rare_han.py --font HanaMinB.ttf --license LICENSE.txt
The original font/license are available from Debian fonts-hanazono 20170904.
Only the subset and its complete upstream license are shipped to readers.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = Path(BASE).parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font', type=Path, required=True)
    parser.add_argument('--license', type=Path, required=True)
    parser.add_argument('--unicodes', default='U+26795,U+2929A')
    args = parser.parse_args()
    import fontTools
    from fontTools import subset
    from fontTools.ttLib import TTFont
    codes = sorted({int(value.strip().upper().removeprefix('U+'), 16) for value in args.unicodes.split(',')})
    if not codes or any(not 0x20000 <= code <= 0x323AF for code in codes):
        parser.error('Only explicitly selected supplementary Han characters belong in this fallback.')
    license_text = args.license.read_text()
    if 'SIL OPEN FONT LICENSE Version 1.1' not in license_text:
        parser.error('The complete upstream OFL license is required.')
    font = TTFont(args.font, recalcTimestamp=False)
    missing = set(codes) - font.getBestCmap().keys()
    if missing:
        parser.error(f'Source font lacks requested glyphs: {sorted(missing)}')
    options = subset.Options()
    options.name_IDs = ['*']
    options.name_legacy = True
    options.name_languages = ['*']
    options.recalc_timestamp = False
    worker = subset.Subsetter(options=options)
    worker.populate(unicodes=codes)
    worker.subset(font)
    # The derivative must not use upstream Reserved Font Names as its family.
    names = {1:'DP Classical Han', 2:'Regular', 3:'DPClassicalHan-20261106',
             4:'DP Classical Han Regular', 5:'Version 1.000; DeepPhilosophy subset',
             6:'DPClassicalHan-Regular', 16:'DP Classical Han', 17:'Regular',
             18:'DP Classical Han Regular', 21:'DP Classical Han', 22:'Regular'}
    for record in font['name'].names:
        if record.nameID in names:
            record.string = names[record.nameID].encode(record.getEncoding())
    output = ROOT/'app/src/assets/fonts/classical-han.woff2'
    output.parent.mkdir(parents=True, exist_ok=True)
    font.flavor = 'woff2'
    font.save(output)
    built = TTFont(output)
    assert set(built.getBestCmap()) == set(codes)
    assert all(record.toUnicode() not in {'HanaMinB', '花園明朝B'}
               for record in built['name'].names if record.nameID in names)
    license_output = ROOT/'app/public/fonts/classical-han-LICENSE.txt'
    license_output.parent.mkdir(parents=True, exist_ok=True)
    license_output.write_bytes(args.license.read_bytes())
    print(json.dumps({'fontTools':fontTools.__version__, 'sourceFontSha256':hashlib.sha256(args.font.read_bytes()).hexdigest(),
                      'subsetSha256':hashlib.sha256(output.read_bytes()).hexdigest(), 'bytes':output.stat().st_size,
                      'family':'DP Classical Han', 'unicodeRange':[f'U+{code:X}' for code in codes],
                      'licenseSha256':hashlib.sha256(license_output.read_bytes()).hexdigest()}, indent=2))


if __name__ == '__main__':
    main()
