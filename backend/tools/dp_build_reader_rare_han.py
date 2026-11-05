"""Build a minimal reader fallback from a licensed classical Chinese font.

Build-only dependencies: fonttools[woff]. No system font is installed.
Usage: python backend/tools/dp_build_reader_rare_han.py --font HanaMinB.ttf --license LICENSE.txt --unicodes U+26795,U+2929A
Hanazono sources: Debian fonts-hanazono 20170904 (OFL).
Newer CJK source: BabelStone Han 16.0.3 (original Arphic Public License).
Different licenses remain in separate files; font outlines are never merged.
Only the subset and its complete upstream license are shipped to readers.
"""
import argparse
import hashlib
import json
import os
from datetime import date
from pathlib import Path

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = Path(BASE).parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font', type=Path, required=True)
    parser.add_argument('--license', type=Path, required=True)
    parser.add_argument('--unicodes', required=True,
                        help='Explicit reviewed codepoint set; never silently shrink the published subset to a legacy default.')
    parser.add_argument('--output', type=Path, default=ROOT/'app/src/assets/fonts/classical-han.woff2')
    parser.add_argument('--license-output', type=Path, default=ROOT/'app/public/fonts/classical-han-LICENSE.txt')
    parser.add_argument('--license-kind', choices=['ofl','arphic'], default='ofl')
    parser.add_argument('--family', default='DP Classical Han')
    parser.add_argument('--build-date', default=date.today().isoformat())
    args = parser.parse_args()
    import fontTools
    from fontTools import subset
    from fontTools.ttLib import TTFont
    codes = sorted({int(value.strip().upper().removeprefix('U+'), 16) for value in args.unicodes.split(',')})
    if not codes or any(not (0x3400 <= code <= 0x4DBF or 0x20000 <= code <= 0x323AF
                            or 0x2630 <= code <= 0x2637 or 0x4DC0 <= code <= 0x4DFF) for code in codes):
        parser.error('Only selected rare Han or explicitly sourced trigram/hexagram signs belong in this fallback.')
    license_text = args.license.read_text()
    if args.license_kind == 'ofl' and 'SIL OPEN FONT LICENSE Version 1.1' not in license_text:
        parser.error('The complete upstream OFL license is required.')
    if args.license_kind == 'arphic' and not ('ARPHIC PUBLIC LICENSE' in license_text
            and 'Copyright (C) 1999 Arphic' in license_text and 'Preamble' in license_text):
        parser.error('The complete original unrestricted Arphic license is required.')
    if any(name in args.family.lower() for name in ['hanamin','hanazono','babelstone']):
        parser.error('Use a new derivative font family name, retaining upstream attribution separately.')
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
    family=args.family; postscript=family.replace(' ','')
    notice=(f'Modified {args.build_date}: selected source glyphs only; removed other codepoints, '
            f'converted to WOFF2 and renamed {family}. Original glyph outlines retained. '
            f'Build source: backend/tools/dp_build_reader_rare_han.py; license: /fonts/{args.license_output.name}.')
    names = {1:family, 2:'Regular', 3:postscript+'-'+args.build_date.replace('-',''),
             4:family+' Regular', 5:'Version 1.001; '+notice,
             6:postscript+'-Regular', 16:family, 17:'Regular',
             18:family+' Regular', 21:family, 22:'Regular'}
    for record in font['name'].names:
        if record.nameID in names:
            record.string = names[record.nameID].encode(record.getEncoding())
    font['name'].setName(notice,10,3,1,0x409)
    output = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    font.flavor = 'woff2'
    font.save(output)
    built = TTFont(output)
    assert set(built.getBestCmap()) == set(codes)
    assert built['name'].getDebugName(10) == notice
    assert all(record.toUnicode() == names[record.nameID]
               for record in built['name'].names if record.nameID in names)
    license_output = args.license_output
    license_output.parent.mkdir(parents=True, exist_ok=True)
    license_output.write_bytes(args.license.read_bytes())
    print(json.dumps({'fontTools':fontTools.__version__, 'sourceFontSha256':hashlib.sha256(args.font.read_bytes()).hexdigest(),
                      'subsetSha256':hashlib.sha256(output.read_bytes()).hexdigest(), 'bytes':output.stat().st_size,
                      'family':family, 'licenseKind':args.license_kind, 'modificationNotice':notice, 'unicodeRange':[f'U+{code:X}' for code in codes],
                      'licenseSha256':hashlib.sha256(license_output.read_bytes()).hexdigest()}, indent=2))


if __name__ == '__main__':
    main()
