import argparse
import os
import math
from PIL import Image


parser = argparse.ArgumentParser()
parser.add_argument('-n', '--name')
parser.add_argument('-c', '--cols', type=int)
parser.add_argument('icons')
parser.add_argument('output')
args = parser.parse_args()

args.name = args.name or os.path.basename(args.output)

icons = []
for name in os.listdir(args.icons):
    if name.startswith('.'):
        continue
    base, ext = os.path.splitext(name)
    if ext not in (('.png'), ):
        continue
    icons.append((base, os.path.join(args.icons, name)))

css = open(args.output + '.css', 'w')
css.write('''
.%(name)s {
    background-image: url('%(base)s.png'); 
    background-repeat: no-repeat;
    height: 16px;
    width: 16px;
    max-width: 16px !important;
    overflow: hidden;
    margin: 0 0 0 -3px !important;
    display:inline-block;
    vertical-align: middle;
}

''' % dict(name=args.name, base=os.path.basename(args.output)))

cols = args.cols or int(math.sqrt(len(icons)))
rows = int(math.ceil(len(icons) / float(cols)))

sprite = Image.new('RGBA', (16 * cols, 16 * rows))
for i, (name, path) in enumerate(sorted(icons)):
    col = i % cols
    row = i / cols
    img = Image.open(path)
    sprite.paste(img, (16 * col, 16 * row))
    css.write('.%s-%s { background-position: %s %s; }\n' % (args.name, name.replace('_', '-'),
        ('-%spx' % (16 * col)) if col else '0',
        ('-%spx' % (16 * row)) if row else '0',
    ))

sprite.save(args.output + '.png')

