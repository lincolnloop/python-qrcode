'''
Test multiple versions of specific parameters and create a comparison image.
Usage:
    python _make_example.py [-h] -e EXAMPLE -o OUTPUT -p PARAM [PARAM ...] [-c COLUMNS]
'''

import os
import io
import math
import argparse
import cairosvg
import matplotlib.pyplot as plt
from PIL import Image

DATA = 'https://github.com/lincolnloop/python-qrcode'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--example', required=True, help='Path to the example script from ./docs/examples')
    parser.add_argument('-p', '--param', required=True, nargs='+', help='List of parameters to test')
    parser.add_argument('-c', '--columns', help='Number of columns in the image. Defaults to number of parameters.', type=int)
    return parser.parse_args()


def generate_images(example_filename: str, params: list[str]):
    images = []
    for param in params:
        status = os.system(f'python {example_filename} {DATA} {param}')
        if status != 0:
            raise RuntimeError(f'Error creating image for {param}')
        if os.path.exists('example.png'):
            images.append(Image.open('example.png'))
        if os.path.exists('example.svg'):
            png_bytes = cairosvg.svg2png(url='example.svg')
            images.append(Image.open(io.BytesIO(png_bytes)))
        os.system('find example.png example.svg -delete 2>/dev/null')
    return images


def create_comparison_image(images: list[Image.Image], params: list[str], output_filename: str, columns: int):
    rows = math.ceil(len(params) / columns)
    fig, axes = plt.subplots(rows, columns, figsize=(columns * 3, rows * 3 + 0.5))
    for ax, img, label in zip(axes.flat, images, params):
        ax.imshow(img)
        ax.set_title(label)
    for ax in axes.flat:
        ax.axis('off')
    fig.tight_layout()
    plt.savefig(output_filename)


if __name__ == '__main__':
    args = parse_args()
    images = generate_images(args.example, args.param)
    create_comparison_image(images, args.param, args.example.replace('.py', '.png'), args.columns or len(args.param))
