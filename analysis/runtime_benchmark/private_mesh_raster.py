"""Opaque orthographic CPU z-buffer for private mesh diagnostic videos.

Pixel centers, linear barycentric depth, larger native z nearer, two-sided
triangles, flat color. No lens, texture, AA, shadows or security approval.
"""
import numpy as np

VERSION = 'orthographic_pixel_center_barycentric_zbuffer_v1'
BACKGROUND_FACE = np.uint16(65535)


def rasterize(xy, depth, faces, colors, *, width=512, height=420):
    xy = np.asarray(xy, float); depth = np.asarray(depth, float)
    faces = np.asarray(faces); colors = np.asarray(colors)
    if (xy.ndim != 2 or xy.shape[1] != 2 or depth.shape != (len(xy),)
            or not np.isfinite(xy).all() or not np.isfinite(depth).all()):
        raise ValueError('Finite complete projected vertices and depth required')
    if (faces.dtype.kind not in 'iu' or faces.ndim != 2 or faces.shape[1] != 3
            or not 1 <= len(faces) < int(BACKGROUND_FACE) or faces.min() < 0 or faces.max() >= len(xy)
            or colors.shape != (len(faces), 3) or colors.dtype != np.uint8):
        raise ValueError('Bounded integer faces and uint8 BGR face colors required')
    if type(width) is not int or type(height) is not int or not 1 <= min(width, height) <= max(width, height) <= 1024:
        raise ValueError('Bounded explicit raster dimensions required')
    image = np.full((height, width, 3), (40, 32, 24), np.uint8)
    zbuffer = np.full((height, width), -np.inf)
    ids = np.full((height, width), BACKGROUND_FACE, np.uint16)
    degenerate = 0
    for fid, face in enumerate(faces):
        triangle = xy[face]; z = depth[face]
        x0, y0 = triangle[0]; x1, y1 = triangle[1]; x2, y2 = triangle[2]
        denominator = (y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
        if abs(denominator) <= 1e-10:
            degenerate += 1; continue
        left, top = np.maximum(np.floor(triangle.min(axis=0)).astype(int), [0, 0])
        right, bottom = np.minimum(np.ceil(triangle.max(axis=0)).astype(int), [width, height])
        if right <= left or bottom <= top:
            continue
        yy, xx = np.mgrid[top:bottom, left:right]; xx = xx+.5; yy = yy+.5
        w0 = ((y1-y2)*(xx-x2)+(x2-x1)*(yy-y2))/denominator
        w1 = ((y2-y0)*(xx-x2)+(x0-x2)*(yy-y2))/denominator
        w2 = 1.-w0-w1
        inside = (w0 >= -1e-10)&(w1 >= -1e-10)&(w2 >= -1e-10)
        candidate = w0*z[0]+w1*z[1]+w2*z[2]
        block = zbuffer[top:bottom, left:right]
        nearer = inside&(candidate > block)
        block[nearer] = candidate[nearer]
        image[top:bottom, left:right][nearer] = colors[fid]
        ids[top:bottom, left:right][nearer] = fid
    zbuffer[ids == BACKGROUND_FACE] = np.nan
    return image, ids, zbuffer.astype(np.float32), {'projected_degenerate_faces_n': degenerate,
        'visible_pixels_n': int((ids != BACKGROUND_FACE).sum()), 'version': VERSION}
