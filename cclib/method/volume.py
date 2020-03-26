# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, the cclib development team
#
# This file is part of cclib (http://cclib.github.io) and is distributed under
# the terms of the BSD 3-Clause License.

"""Calculation methods related to volume based on cclib data."""

from __future__ import print_function
import copy

import numpy

from cclib.parser.utils import convertor
from cclib.parser.utils import find_package

_found_pyquante = find_package("PyQuante")
if _found_pyquante:
    from PyQuante.CGBF import CGBF
    from cclib.bridge import cclib2pyquante

_found_pyvtk = find_package("pyvtk")
if _found_pyvtk:
    from pyvtk import *
    from pyvtk.DataSetAttr import *


def _check_pyvtk(found_pyvtk):
    if not found_pyvtk:
        raise ImportError("You must install `pyvtk` to use this function")


class Volume(object):
    """Represent a volume in space.

    Required parameters:
       origin -- the bottom left hand corner of the volume
       topcorner -- the top right hand corner
       spacing -- the distance between the points in the cube

    Attributes:
       data -- a NumPy array of values for each point in the volume
               (set to zero at initialisation)
       numpts -- the numbers of points in the (x,y,z) directions
    """

    def __init__(self, origin, topcorner, spacing):

        self.origin = numpy.asarray(origin, dtype=float)
        self.topcorner = numpy.asarray(topcorner, dtype=float)
        self.spacing = numpy.asarray(spacing, dtype=float)
        self.numpts = []
        for i in range(3):
            self.numpts.append(int((self.topcorner[i] - self.origin[i]) / self.spacing[i] + 1))
        self.data = numpy.zeros(tuple(self.numpts), "d")

    def __str__(self):
        """Return a string representation."""
        return "Volume %s to %s (density: %s)" % (self.origin, self.topcorner,
                                                  self.spacing)

    def write(self, filename, fformat="Cube"):
        """Write the volume to a file."""

        fformat = fformat.lower()

        writers = {
            "vtk": self.writeasvtk,
            "cube": self.writeascube,
        }

        if fformat not in writers:
            raise RuntimeError("File format must be either VTK or Cube")

        writers[fformat](filename)

    def writeasvtk(self, filename):
        _check_pyvtk(_found_pyvtk)
        ranges = (numpy.arange(self.data.shape[2]),
                  numpy.arange(self.data.shape[1]),
                  numpy.arange(self.data.shape[0]))
        v = VtkData(RectilinearGrid(*ranges), "Test",
                    PointData(Scalars(self.data.ravel(), "from cclib", "default")))
        v.tofile(filename)

    def integrate(self):
        boxvol = (self.spacing[0] * self.spacing[1] * self.spacing[2] *
                  convertor(1, "Angstrom", "bohr") ** 3)
        return sum(self.data.ravel()) * boxvol

    def integrate_square(self):
        boxvol = (self.spacing[0] * self.spacing[1] * self.spacing[2] *
                  convertor(1, "Angstrom", "bohr") ** 3)
        return sum(self.data.ravel() ** 2) * boxvol
    
def grad_cartesian(func, boundaryCondition):
        gradf = copy.copy(volume)
        gradf.data = numpy.zeros(gradf.data.shape, "d")

        conversion = convertor(1, "bohr", "Angstrom")
        x = numpy.arange(gradf.origin[0], gradf.topcorner[0] + gradf.spacing[0], gradf.spacing[0]) / conversion
        y = numpy.arange(gradf.origin[1], gradf.topcorner[1] + gradf.spacing[1], gradf.spacing[1]) / conversion
        z = numpy.arange(gradf.origin[2], gradf.topcorner[2] + gradf.spacing[2], gradf.spacing[2]) / conversion

        der_x = numpy.zeros(numpy.size(x))
        der_y = numpy.zeros(numpy.size(y))
        der_z = numpy.zeros(numpy.size(z))

        if(boundaryCondition == "Periodic"):
            for xval in enumerate(x):
                for yval in enumerate(y):
                    for zval in enumerate(z):                    
                        if(xval == x[-1]):
                            der_x[xval] = (func.origin[0], yval, zval] - func[xval, yval, zval]) / func.spacing[0]
                        if(yval == y[-1]):
                            der_y[xval] = (xval, func.origin[1], zval] - func[xval, yval, zval]) / func.spacing[1]
                        if(zval == z[-1]):                        
                            der_z[zval] = (xval, yval, func.origin[2]] - func[xval, yval, zval]) / func.spacing[2]
                        else:
                            der_x = (func[xval + func.spacing[0], yval, zval] - func[xval, yval, zval]) / func.spacing[0]
                            der_y = (func[xval, yval + func.spacing[1], zval] - func[xval, yval, zval]) / func.spacing[1]
                            der_z = (func[xval, yval, zval + func.spacing[2]] - func[xval, yval, zval]) / func.spacing[2]

                        gradf.data[xval, yval, zval] = der_x[xval] + der_y[yval] + der_z[zval]
        else:
            print("Invalid Boundary Condition passed to the Gradient")
        return gradf

    def laplacian_cartesian(func, boundaryCondition):
        lapf = copy.copy(volume)
        lapf.data = numpy.zeros(lapf.data.shape, "d")

        conversion = convertor(1, "bohr", "Angstrom")
        x = numpy.arange(lapf.origin[0], lapf.topcorner[0] + lapf.spacing[0], lapf.spacing[0]) / conversion
        y = numpy.arange(lapf.origin[1], lapf.topcorner[1] + lapf.spacing[1], lapf.spacing[1]) / conversion
        z = numpy.arange(lapf.origin[2], lapf.topcorner[2] + lapf.spacing[2], lapf.spacing[2]) / conversion

        der2_x = numpy.zeros(numpy.size(x))
        der2_y = numpy.zeros(numpy.size(y))
        der2_z = numpy.zeros(numpy.size(z))

        if(boundaryCondition == "Periodic"):
            for xval in enumerate(x):
                for yval in enumerate(y):
                    for zval in enumerate(z):
                        if(xval == x[0]):
                            der2_x[xval] = (func[xval + func.spacing[0], yval, zval] - (2 * func[xval, yval, zval]) + func[func.topcorner[0], yval, zval) / (func.spacing[0] ** 2)
                        if(xval == x[-1]):                        
                            der2_x[xval] = (func[func.origin[0], yval, zval] - (2 * func[xval, yval, zval]) + func[xval - func.spacing[0], yval, zval) / (func.spacing[0] ** 2)

                        if(yval == y[0]):
                            der2_y[yval] = (func[xval, yval + func.spacing[1], zval] - (2 * func[xval, yval, zval]) + func[xval, func.topcorner[1], zval) / (func.spacing[1] ** 2)
                        if(yval == y[-1]):
                            der2_y[yval] = (func[xval, func.origin[1], zval] - (2 * func[xval, yval, zval]) + func[xval, yval - func.spacing[1], zval) / (func.spacing[1] ** 2)
                        
                        if(zval == z[0]):
                            der2_z[zval] = (func[xval, yval, zval + func.spacing[2]] - (2 * func[xval, yval, zval]) + func[xval, yval, func.topcorner[2]) / (func.spacing[2] ** 2)
                        if(zval == z[-1]):
                            der2_z[zval] = (func[xval, yval, func.origin[2]] - (2 * func[xval, yval, zval]) + func[xval, yval, zval - func.spacing[2]) / (func.spacing[2] ** 2)

                        else:
                            der2_x = (func[xval + func.spacing[0], yval, zval] - (2 * func[xval, yval, zval]) + func[xval - func.spacing[0], yval, zval) / (func.spacing[0] ** 2)
                            der2_y = (func[xval, yval + func.spacing[1], zval] - (2 * func[xval, yval, zval]) + func[xval, yval - func.spacing[1], zval) / (func.spacing[1] ** 2)
                            der2_z = (func[xval, yval, zval + func.spacing[2]] - (2 * func[xval, yval, zval]) + func[xval, yval, zval - func.spacing[2]) / (func.spacing[2] ** 2)

                        lapf.data[xval, yval, zval] = der2_x[xval] + der2_y[yval] + der2_z[zval]
        else:
            print("Invalid Boundary Condition passed to the Laplacian")
        return lapf
                                                                                                                     
    def writeascube(self, filename):
        # Remember that the units are bohr, not Angstroms
        def convert(x):
            return convertor(x, "Angstrom", "bohr")
        ans = []
        ans.append("Cube file generated by cclib")
        ans.append("")
        format = "%4d%12.6f%12.6f%12.6f"
        origin = [convert(x) for x in self.origin]
        ans.append(format % (0, origin[0], origin[1], origin[2]))
        ans.append(format % (self.data.shape[0], convert(self.spacing[0]), 0.0, 0.0))
        ans.append(format % (self.data.shape[1], 0.0, convert(self.spacing[1]), 0.0))
        ans.append(format % (self.data.shape[2], 0.0, 0.0, convert(self.spacing[2])))
        line = []
        for i in range(self.data.shape[0]):
            for j in range(self.data.shape[1]):
                for k in range(self.data.shape[2]):
                    line.append(scinotation(self.data[i, j, k]))
                    if len(line) == 6:
                        ans.append(" ".join(line))
                        line = []
                if line:
                    ans.append(" ".join(line))
                    line = []
        with open(filename, "w") as outputfile:
            outputfile.write("\n".join(ans))


def scinotation(num):
    """Write in scientific notation."""
    ans = "%10.5E" % num
    broken = ans.split("E")
    exponent = int(broken[1])
    if exponent < -99:
        return "  0.000E+00"
    if exponent < 0:
        sign = "-"
    else:
        sign = "+"
    return ("%sE%s%s" % (broken[0], sign, broken[1][-2:])).rjust(12)


def getbfs(coords, gbasis):
    """Convenience function for both wavefunction and density based on PyQuante Ints.py."""
    mymol = cclib2pyquante.makepyquante(coords, [0 for _ in coords])

    sym2powerlist = {
        'S' : [(0, 0, 0)],
        'P' : [(1, 0, 0), (0, 1, 0), (0, 0, 1)],
        'D' : [(2, 0, 0), (0, 2, 0), (0, 0, 2), (1, 1, 0), (0, 1, 1), (1, 0, 1)],
        'F' : [(3, 0, 0), (2, 1, 0), (2, 0, 1), (1, 2, 0), (1, 1, 1), (1, 0, 2),
               (0, 3, 0), (0, 2, 1), (0, 1, 2), (0, 0, 3)]
        }

    bfs = []
    for i, atom in enumerate(mymol):
        bs = gbasis[i]
        for sym, prims in bs:
            for power in sym2powerlist[sym]:
                bf = CGBF(atom.pos(), power)
                for expnt, coef in prims:
                    bf.add_primitive(expnt, coef)
                bf.normalize()
                bfs.append(bf)

    return bfs


def wavefunction(coords, mocoeffs, gbasis, volume):
    """Calculate the magnitude of the wavefunction at every point in a volume.

    Attributes:
        coords -- the coordinates of the atoms
        mocoeffs -- mocoeffs for one eigenvalue
        gbasis -- gbasis from a parser object
        volume -- a template Volume object (will not be altered)
    """
    bfs = getbfs(coords, gbasis)

    wavefn = copy.copy(volume)
    wavefn.data = numpy.zeros(wavefn.data.shape, "d")

    conversion = convertor(1, "bohr", "Angstrom")
    x = numpy.arange(wavefn.origin[0], wavefn.topcorner[0] + wavefn.spacing[0], wavefn.spacing[0]) / conversion
    y = numpy.arange(wavefn.origin[1], wavefn.topcorner[1] + wavefn.spacing[1], wavefn.spacing[1]) / conversion
    z = numpy.arange(wavefn.origin[2], wavefn.topcorner[2] + wavefn.spacing[2], wavefn.spacing[2]) / conversion

    for bs in range(len(bfs)):
        data = numpy.zeros(wavefn.data.shape, "d")
        for i, xval in enumerate(x):
            for j, yval in enumerate(y):
                for k, zval in enumerate(z):
                    data[i, j, k] = bfs[bs].amp(xval, yval, zval)
        data *= mocoeffs[bs]
        wavefn.data += data

    return wavefn


def electrondensity(coords, mocoeffslist, gbasis, volume):
    """Calculate the magnitude of the electron density at every point in a volume.

    Attributes:
        coords -- the coordinates of the atoms
        mocoeffs -- mocoeffs for all of the occupied eigenvalues
        gbasis -- gbasis from a parser object
        volume -- a template Volume object (will not be altered)

    Note: mocoeffs is a list of NumPy arrays. The list will be of length 1
          for restricted calculations, and length 2 for unrestricted.
    """
    bfs = getbfs(coords, gbasis)

    density = copy.copy(volume)
    density.data = numpy.zeros(density.data.shape, "d")

    conversion = convertor(1, "bohr", "Angstrom")
    x = numpy.arange(density.origin[0], density.topcorner[0] + density.spacing[0], density.spacing[0]) / conversion
    y = numpy.arange(density.origin[1], density.topcorner[1] + density.spacing[1], density.spacing[1]) / conversion
    z = numpy.arange(density.origin[2], density.topcorner[2] + density.spacing[2], density.spacing[2]) / conversion

    for mocoeffs in mocoeffslist:
        for mocoeff in mocoeffs:
            wavefn = numpy.zeros(density.data.shape, "d")
            for bs in range(len(bfs)):
                data = numpy.zeros(density.data.shape, "d")
                for i, xval in enumerate(x):
                    for j, yval in enumerate(y):
                        tmp = []
                        for zval in z:
                            tmp.append(bfs[bs].amp(xval, yval, zval))
                        data[i, j, :] = tmp
                data *= mocoeff[bs]
                wavefn += data
            density.data += wavefn ** 2

    # TODO ROHF
    if len(mocoeffslist) == 1:
        density.data *= 2.0

    return density


del find_package
