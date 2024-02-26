import numpy


def strike_dip_vector(strike, dip):
    # this code is from LoopStructural
    vec = numpy.zeros((len(strike), 3))
    s_r = numpy.deg2rad(strike)
    d_r = numpy.deg2rad(dip)
    vec[:, 0] = numpy.sin(d_r) * numpy.cos(s_r)
    vec[:, 1] = -numpy.sin(d_r) * numpy.sin(s_r)
    vec[:, 2] = numpy.cos(d_r)
    vec /= numpy.linalg.norm(vec, axis=1)[:, None]
    return vec
