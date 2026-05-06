import subprocess
import sys
import tempfile
import unittest

from datetime import datetime
from pathlib import Path

from fontTools.ttLib import TTFont


REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN_SCRIPT = REPO_ROOT / 'src' / 'main.py'
TEST_FONT = REPO_ROOT / 'tests' / 'fixtures' / 'Inconsolata_Condensed-Medium.ttf'


def _get_name_value(name_table, name_id, fallback=''):
    value = name_table.getDebugName(name_id)
    if value:
        return value
    return fallback


class MainTest(unittest.TestCase):
    def test_main_patches_real_font_metrics_and_names(self):
        factor = '1.25'
        factor_value = float(factor)

        if not TEST_FONT.is_file():
            self.skipTest('Test font not found: {}'.format(TEST_FONT))

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_dir = temp_path / 'patched'

            original_font = TTFont(str(TEST_FONT))
            self.addCleanup(original_font.close)

            original_names = {
                'fontname': _get_name_value(original_font['name'], 6, TEST_FONT.stem),
                'familyname': _get_name_value(original_font['name'], 1),
                'fullname': _get_name_value(original_font['name'], 4),
            }

            expected_names = {
                attr: '{} {}'.format(original_names[attr], factor)
                for attr in ['fontname', 'familyname', 'fullname']
            }

            result = subprocess.run(
                [
                    sys.executable,
                    str(MAIN_SCRIPT),
                    '--factor={}'.format(factor),
                    '--input={}'.format(TEST_FONT),
                    '--outputDir={}'.format(output_dir),
                ],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            patched_font = output_dir / '{}Patched {}{}'.format(TEST_FONT.stem, factor, TEST_FONT.suffix)
            self.assertTrue(patched_font.exists(), patched_font)

            font = TTFont(str(patched_font))
            self.addCleanup(font.close)

            self.assertEqual(font['OS/2'].usWinAscent, int(original_font['OS/2'].usWinAscent * factor_value))
            self.assertEqual(font['OS/2'].sTypoAscender, int(original_font['OS/2'].sTypoAscender * factor_value))
            self.assertEqual(font['hhea'].ascent, int(original_font['hhea'].ascent * factor_value))

            self.assertEqual(font['OS/2'].usWinDescent, int(original_font['OS/2'].usWinDescent * factor_value * 2))
            self.assertEqual(font['OS/2'].sTypoDescender, int(original_font['OS/2'].sTypoDescender * factor_value * 2))
            self.assertEqual(font['hhea'].descent, int(original_font['hhea'].descent * factor_value * 2))

            self.assertEqual(font['name'].getDebugName(6), expected_names['fontname'])
            self.assertEqual(font['name'].getDebugName(1), expected_names['familyname'])
            self.assertEqual(font['name'].getDebugName(4), expected_names['fullname'])
            self.assertEqual(font['name'].getDebugName(3), expected_names['fontname'])
            self.assertEqual(font['name'].getDebugName(16), expected_names['familyname'])
            self.assertEqual(
                font['name'].getDebugName(0),
                '(c) {} Acme Corp. All Rights Reserved.'.format(datetime.now().year),
            )


if __name__ == '__main__':
    unittest.main()
