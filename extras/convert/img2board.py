#!/usr/bin/env python3
from argparse import ArgumentParser
from pyhocon import ConfigFactory
from PIL import Image, ImageColor
from PIL.ImagePalette import ImagePalette
from pathlib import Path
import sys

argparser = ArgumentParser(description='Converts the given board (and placemap, if applicable) to default_board.dat and placemap.dat.')
argparser.add_argument('board', help='board image path', default='default_board.png')
argparser.add_argument('placemap', nargs='?', help='placemap image path', default='placemap.png')
# Default assumes user copied extras/ to <instance>/.
argparser.add_argument('--palette', '-p', help='palette.conf directory or path', default='../../palette.conf')
argparser.add_argument('--output', '-o', help='output directory path', default='./')
argparser.add_argument('--dither', '-d', help='whether to dither the palette conversion', action='store_true')
args = argparser.parse_args()

# Assign all of the absolute resolved paths.
board_path = Path(args.board).absolute().resolve()
placemap_path = Path(args.placemap).absolute().resolve()
palette_path = Path(args.palette).absolute().resolve()
output_path = Path(args.output).absolute().resolve()
output_board_path = output_path.joinpath('default_board.dat')
output_placemap_path = output_path.joinpath('placemap.dat')
dither = 1 if args.dither else 0

# Allows for using a directory as the palette path (e.g. `.`).
if palette_path.is_dir():
    palette_path = palette_path.joinpath('palette.conf')

# Manual input isn't feasible through arguments.
if not palette_path.exists():
    print('Could not find palette configuration at the given path.')
    sys.exit(1)

# Parse the palette configuration and extract hex colors.
palette_conf = ConfigFactory().parse_file(str(palette_path))
colors = palette_conf['colors']
hex_colors = [color.value for color in colors]

# Convert all hex colors to RGB tuples.
rgb_colors = [ImageColor.getrgb('#' + hex_color) for hex_color in hex_colors]

# Open the board image.
board_img = Image.open(str(board_path))
board_pix = board_img.load()
width, height = board_img.size

# If a placemap wasn't provided, generate one with the board size.
if placemap_path.exists():
    placemap_image = Image.open(str(placemap_path))
    if placemap_image.mode != 'RGBA':
        placemap_image.putalpha(255)
else:
    print('Could not find placemap at the given path; using generated.')
    placemap_image = Image.new('RGBA', board_img.size, color=(0, 0, 0, 255))
placemap_pix = placemap_image.load()

# Create a sample Image based on the palette.
palette_img = Image.new('P', (len(rgb_colors), 1))
for idx, rgb in enumerate(rgb_colors):
    palette_img.putpixel((idx, 0), rgb)

# Quantize colors in the board image to the palette.
qt_board_img = board_img.convert('RGB').quantize(palette=palette_img, dither=dither)
qt_board_pix = qt_board_img.load()

# Save the quantized board image to default_board.dat.
with open(str(output_board_path), 'wb+') as file:
    file.truncate()
    for y in range(height):
        for x in range(width):
            pix = board_pix[x, y]
            idx = qt_board_pix[x, y]
            # If the pixel isn't completely opaque, assume it's transparent.
            if board_img.mode == 'RGBA' and pix[3] != 255:
                file.write(bytes([255]))
                continue
            file.write(bytes([idx]))

# Save the placemap to placemap.dat.
with open(str(output_placemap_path), 'wb+') as file:
    file.truncate()
    for y in range(height):
        for x in range(width):
            pix = placemap_pix[x, y]
            file.write(bytes([255 if pix[3] == 255 else 0]))
