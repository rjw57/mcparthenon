"""
Usage:
    makelevel (-h|--help)
    makelevel [-v|--verbose] <levelname> <texturemap> <depthmap>

Options:
    -h, --help      Show a brief usage summary.
    -v, --verbose   Increase verbosity of logging
"""
import docopt
import logging
import os

# HACK: pymclevel does not appear to install data correctly. Use our own copy.
os.environ['PYMCLEVEL_YAML_ROOT'] = os.path.join(os.path.dirname(__file__), 'data')
from pymclevel import mclevel
import numpy as np
from PIL import Image

log = logging.getLogger(__name__)

def main():
    # parse options
    opts = docopt.docopt(__doc__)
    logging.basicConfig(level=logging.INFO if opts['--verbose'] else logging.WARN)
    levelname = opts['<levelname>']
    texturemap_fn = opts['<texturemap>']
    depthmap_fn = opts['<depthmap>']

    log.info('Loading texture map...')
    tm_im = Image.open(texturemap_fn)

    log.info('Loading depth map...')
    dm_im = Image.open(depthmap_fn)

    tm_im = tm_im.resize((1920//2,1080//2), Image.ANTIALIAS)
    dm_im = dm_im.resize((1920//2,1080//2), Image.ANTIALIAS)

    # Flip images to correspond to MC's co-ord syste,
    tm_im = tm_im.transpose(Image.FLIP_LEFT_RIGHT)
    dm_im = dm_im.transpose(Image.FLIP_LEFT_RIGHT)

    alpha = np.asarray(tm_im.convert('RGBA'))[:,:,3].astype(np.float32)
    alpha /= alpha.max()

    texture = np.asarray(tm_im.convert('L')).astype(np.float32)
    texture /= texture.max()

    depth = np.asarray(dm_im.convert('L')).astype(np.float32)
    depth /= depth.max()

    if texture.shape != depth.shape:
        log.error('Texture map is {0[1]}x{0[0]} whereas depth map is {1[1]}x{1[0]}'.format(
            texture.shape, depth.shape))
        return 1

    log.info('Loading world...')
    world = mclevel.fromFile(levelname)

    xchunks, zchunks = tuple(s//16 for s in texture.shape)

    log.info('Creating empty chunks...')
    chunks = []
    dx, dz = (xchunks>>1), (zchunks>>1)
    for xchunk in np.arange(xchunks) - dx:
        for zchunk in np.arange(zchunks) - dz:
            chunks.append((xchunk, zchunk))
    world.createChunks(chunks)

    log.info('Processing chunks...')
    n_processed = 0
    for xchunk, zchunk in chunks:
        n_processed += 1
        if n_processed % 100 == 0:
            log.info('Processing chunk {0}/{1}'.format(n_processed, len(chunks)))
        chunk = world.getChunk(xchunk, zchunk)
        px, pz = (xchunk+dx)*16, (zchunk+dz)*16

        # Reset chunk
        chunk.Blocks[:] = world.materials.Air.ID
        chunk.Data[:] = 0

        colour = texture[px:(px+16), pz:(pz+16)]
        height = depth[px:(px+16), pz:(pz+16)]
        mask = alpha[px:(px+16), pz:(pz+16)]

        # Scale height
        height = np.where(mask > 0, height * 64 + 70, 10)

        # Get floor value of height / 16
        block_height = np.floor(height).astype(np.int32)
        drift_height = np.floor((height - block_height) * 9).astype(np.uint8)

        for x in range(colour.shape[0]):
            for z in range(colour.shape[0]):
                h = block_height[x,z]
                chunk.Blocks[x,z,:h] = world.materials.Snow.ID
                if drift_height[x,z] != 0:
                    chunk.Blocks[x,z,h] = world.materials.SnowLayer.ID
                    chunk.Data[x,z,h] = drift_height[x,z] - 1

        chunk.chunkChanged()

    world.generateLights()
    world.saveInPlace()

    return 0 # success

if __name__ == '__main__':
    import sys
    sys.exit(main())
