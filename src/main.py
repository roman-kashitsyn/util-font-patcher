import argparse
from datetime import datetime
from pathlib import Path

NAME_IDS = {
    "copyright": 0,
    "familyname": 1,
    "unique_id": 3,
    "fullname": 4,
    "fontname": 6,
    "preferred_family": 16,
}

NAME_FIELDS = ("fontname", "familyname", "fullname")
METRIC_ADJUSTMENTS = (
    ("OS/2", "usWinAscent", 1, "os2_winascent"),
    ("OS/2", "sTypoAscender", 1, "os2_typoascent"),
    ("hhea", "ascent", 1, "hhea_ascent"),
    ("OS/2", "usWinDescent", 2, "os2_windescent"),
    ("OS/2", "sTypoDescender", 2, "os2_typodescent"),
    ("hhea", "descent", 2, "hhea_descent"),
)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="font-patcher",
        description="Font patcher to add line height to fonts",
    )
    parser.add_argument(
        "-f",
        "--factor",
        type=float,
        required=True,
        help="The factor by which to multiply the line height",
    )
    parser.add_argument(
        "-i",
        "--input",
        dest="input_path",
        required=True,
        help="The original font file",
    )
    parser.add_argument(
        "-o",
        "--outputDir",
        dest="output_dir",
        required=True,
        help="The directory to save the patched font",
    )
    parser.add_argument("--fontname", help="The name of the patched font")
    parser.add_argument(
        "--familyname",
        help="The family name of the patched font",
    )
    parser.add_argument(
        "--fullname",
        help="The name for humans of the patched font",
    )
    return parser


def parse_args(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.input_path = Path(args.input_path).expanduser().resolve()
    args.output_dir = Path(args.output_dir).expanduser().resolve()

    if not args.input_path.is_file():
        parser.error(f"Input font file not found: {args.input_path}")

    return args


def _load_ttfont(input_path):
    try:
        from fontTools.ttLib import TTFont
    except ImportError as exc:
        raise SystemExit(
            "\nUnable to import fontTools.\n"
            "Install dependencies with `python3 -m pip install -r requirements.txt` "
            "or run the Docker image."
        ) from exc

    return TTFont(str(input_path))


def _get_name_value(name_table, name_id, fallback=''):
    value = name_table.getDebugName(name_id)
    if value:
        return value
    return fallback


def _set_name_value(name_table, name_id, value):
    updated = False

    for record in name_table.names:
        if record.nameID != name_id:
            continue

        encoding = record.getEncoding() or 'utf_16_be'
        record.string = value.encode(encoding)
        updated = True

    if not updated:
        name_table.setName(value, name_id, 3, 1, 0x409)
        name_table.setName(value, name_id, 1, 0, 0)


def _update_cff_names(font, names):
    if "CFF " not in font:
        return

    cff = font["CFF "].cff.topDictIndex[0]
    cff.FullName = names["fullname"]
    cff.FamilyName = names["familyname"]
    cff.FontName = names["fontname"]


def _adjust_metric(table, attribute, factor, label):
    original = getattr(table, attribute)
    new = int(original * factor)

    print(f"Adjusting {label}: {original} -> {new}")
    setattr(table, attribute, new)


def _apply_metric_adjustments(font, factor):
    print()
    for table_name, attribute, multiplier, label in METRIC_ADJUSTMENTS:
        _adjust_metric(font[table_name], attribute, factor * multiplier, label)


def _build_names(name_table, input_path, factor_text, args):
    current_names = {
        "fontname": _get_name_value(name_table, NAME_IDS["fontname"], input_path.stem),
        "familyname": _get_name_value(name_table, NAME_IDS["familyname"]),
        "fullname": _get_name_value(name_table, NAME_IDS["fullname"]),
    }

    return {
        field: getattr(args, field) or f"{current_names[field]} {factor_text}"
        for field in NAME_FIELDS
    }


def _update_font_names(font, input_path, factor_text, args):
    name_table = font["name"]
    names = _build_names(name_table, input_path, factor_text, args)

    for field in NAME_FIELDS:
        _set_name_value(name_table, NAME_IDS[field], names[field])

    _set_name_value(
        name_table,
        NAME_IDS["copyright"],
        f"(c) {datetime.now().year} Acme Corp. All Rights Reserved.",
    )
    _set_name_value(name_table, NAME_IDS["unique_id"], names["fontname"])
    _set_name_value(name_table, NAME_IDS["preferred_family"], names["familyname"])
    _update_cff_names(font, names)
    return names


def main(argv=None):
    args = parse_args(argv)
    factor_text = str(args.factor)
    output_path = args.output_dir / f"{args.input_path.stem}Patched {factor_text}{args.input_path.suffix}"

    font = _load_ttfont(args.input_path)
    try:
        _apply_metric_adjustments(font, args.factor)
        names = _update_font_names(font, args.input_path, factor_text, args)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        font.save(str(output_path))
    finally:
        font.close()

    print()
    print("Successfully created patched font:")
    print(f"                         Fontname: {names['fontname']}")
    print(f"                      Family Name: {names['familyname']}")
    print(f"                  Name for Humans: {names['fullname']}")
    print()
    print(f"Saved patched font file: {output_path.name}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
