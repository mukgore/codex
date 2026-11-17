"""Outward boxes for conditional IEEE arithmetic models, not a backend proof.

Transcendental padding is an explicit, unvalidated target-backend assumption.
mpmath.iv encloses real functions; that alone does not certify SciPy/Torch.
"""
import math

from mpmath import iv
import numpy as np

iv.dps = 40


class Unresolved(ValueError):
    pass


class Box:
    def __init__(self, lo, hi=None, bits=64):
        self.lo = np.asarray(lo, dtype=float)
        self.hi = np.asarray(lo if hi is None else hi, dtype=float)
        if (bits not in (32, 64) or self.lo.shape != self.hi.shape or
                not np.isfinite(self.lo).all() or not np.isfinite(self.hi).all() or (self.lo > self.hi).any()):
            raise Unresolved('INVALID_OR_NONFINITE_BOX')
        self.bits = bits

    @classmethod
    def rounded(cls, lo, hi, bits):
        lo, hi = np.nextafter(lo, -np.inf), np.nextafter(hi, np.inf)
        if bits == 32:
            lo = np.nextafter(np.asarray(lo, np.float32), np.float32(-np.inf)).astype(float)-1e-37
            hi = np.nextafter(np.asarray(hi, np.float32), np.float32(np.inf)).astype(float)+1e-37
        return cls(lo, hi, bits)

    def cast32(self):
        return Box.rounded(self.lo, self.hi, 32)

    def __getitem__(self, item): return Box(self.lo[item], self.hi[item], self.bits)
    def reshape(self, *shape): return Box(self.lo.reshape(*shape), self.hi.reshape(*shape), self.bits)
    @property
    def T(self): return Box(self.lo.T, self.hi.T, self.bits)
    def __neg__(self): return Box(-self.hi, -self.lo, self.bits)
    def other(self, value): return value if isinstance(value, Box) else Box(value, bits=self.bits)

    def __add__(self, value):
        b = self.other(value)
        return Box.rounded(self.lo+b.lo, self.hi+b.hi, max(self.bits, b.bits))
    __radd__ = __add__
    def __sub__(self, value): return self+-self.other(value)
    def __rsub__(self, value): return self.other(value)+-self

    def __mul__(self, value):
        b = self.other(value)
        endpoints = np.array(np.broadcast_arrays(self.lo*b.lo, self.lo*b.hi, self.hi*b.lo, self.hi*b.hi))
        return Box.rounded(endpoints.min(axis=0), endpoints.max(axis=0), max(self.bits, b.bits))
    __rmul__ = __mul__

    def __truediv__(self, value):
        b = self.other(value)
        if ((b.lo <= 0) & (b.hi >= 0)).any():
            raise Unresolved('DIVISOR_INCLUDES_ZERO')
        reciprocal = Box.rounded(1/b.hi, 1/b.lo, b.bits)
        return self*reciprocal

    def square(self):
        low = np.where((self.lo <= 0) & (self.hi >= 0), 0, np.minimum(self.lo**2, self.hi**2))
        high = np.maximum(self.lo**2, self.hi**2)
        result = Box.rounded(low, high, self.bits)
        return Box(np.maximum(result.lo, 0), result.hi, self.bits)

    def sqrt(self):
        if (self.lo < 0).any():
            raise Unresolved('NEGATIVE_SQRT_RANGE')
        result = Box.rounded(np.sqrt(self.lo), np.sqrt(self.hi), self.bits)
        return Box(np.maximum(result.lo, 0), result.hi, self.bits)

    def __matmul__(self, b):
        b = self.other(b)
        if self.lo.ndim < 2 or b.lo.ndim < 2 or self.lo.shape[-1] != b.lo.shape[-2]:
            raise Unresolved('MATRIX_SHAPE_MISMATCH')
        k = self.lo.shape[-1]; bits = max(self.bits, b.bits)
        if not 1 <= k <= 10000:
            raise Unresolved('DOT_PRODUCT_BUDGET')
        shape = np.broadcast_shapes(self.lo.shape[:-2], b.lo.shape[:-2])+(self.lo.shape[-2], b.lo.shape[-1])
        total = Box(np.zeros(shape)); absolute = Box(np.zeros(shape))
        for j in range(k):
            aterm = Box(self.lo[..., :, j, None], self.hi[..., :, j, None])
            bterm = Box(b.lo[..., None, j, :], b.hi[..., None, j, :])
            term = aterm*bterm
            total = total+term
            absolute = absolute+np.maximum(np.abs(term.lo), np.abs(term.hi))
        # Covers arbitrary ordinary product/reduction ordering and FMA under
        # the stated IEEE/no-overflow model, rather than matching one BLAS tree.
        unit = 2.**(-24 if bits == 32 else -53)
        gamma = np.nextafter(2*k*unit/(1-2*k*unit), np.inf)
        error = np.nextafter(gamma*absolute.hi+2*k*(1e-37 if bits == 32 else 0), np.inf)
        return Box.rounded(total.lo-error, total.hi+error, bits)


def pack(values, bits=None):
    flat = list(values)
    target = max(x.bits for x in flat) if bits is None else bits
    return Box(np.array([x.lo for x in flat]), np.array([x.hi for x in flat]), target)


def hull(values):
    return Box(np.minimum.reduce([x.lo for x in values]), np.maximum.reduce([x.hi for x in values]), max(x.bits for x in values))


def norm(value):
    squares = value.square().reshape(-1, 1)
    ones = Box(np.ones((1, len(squares.lo))), bits=value.bits)
    squared = ones@squares
    return Box(np.maximum(squared.lo, 0), squared.hi, value.bits).sqrt().reshape(())


def elementary(name, value, absolute_backend_error):
    if not math.isfinite(absolute_backend_error) or absolute_backend_error < 0:
        raise ValueError('Explicit finite nonnegative backend error assumption required')
    lower, upper = [], []
    for a, b in zip(value.lo.flat, value.hi.flat):
        result = getattr(iv, name)(iv.mpf([float(a), float(b)]))
        lower.append(float(result.a)); upper.append(float(result.b))
    lo = np.array(lower).reshape(value.lo.shape)-absolute_backend_error
    hi = np.array(upper).reshape(value.lo.shape)+absolute_backend_error
    return Box.rounded(lo, hi, value.bits)


def atan2_positive(y, x, absolute_backend_error):
    if float(y.lo) < 0 or float(x.lo) <= 0:
        raise Unresolved('ATAN2_POSITIVE_QUADRANT_NOT_RESOLVED')
    result = iv.atan2(iv.mpf([float(y.lo), float(y.hi)]), iv.mpf([float(x.lo), float(x.hi)]))
    return Box.rounded(float(result.a)-absolute_backend_error, float(result.b)+absolute_backend_error, 64)
