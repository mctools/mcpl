
################################################################################
##                                                                            ##
##  This file is part of MCPL (see https://mctools.github.io/mcpl/)           ##
##                                                                            ##
##  Copyright 2015-2026 MCPL developers.                                      ##
##                                                                            ##
##  Licensed under the Apache License, Version 2.0 (the "License");           ##
##  you may not use this file except in compliance with the License.          ##
##  You may obtain a copy of the License at                                   ##
##                                                                            ##
##      http://www.apache.org/licenses/LICENSE-2.0                            ##
##                                                                            ##
##  Unless required by applicable law or agreed to in writing, software       ##
##  distributed under the License is distributed on an "AS IS" BASIS,         ##
##  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  ##
##  See the License for the specific language governing permissions and       ##
##  limitations under the License.                                            ##
##                                                                            ##
################################################################################

"""Particles and blocks of particles read from MCPL files."""

__all__ = ['MCPLParticle', 'MCPLParticleBlock']

from ._numpy import np, np_stack
from ._physics import wavelength_from_ekin


class MCPLParticle:
    """Object representing a single particle"""

    def __init__(self,block,idx):
        """For internal use only - users should not normally create MCPLParticle objects themselves"""
        self._b = block#can we make it a weak ref, to make sure multiple blocks are not kept around?
        self._i = idx
    @property
    def position(self):
        """position as 3-dimensional array [cm]"""
        return self._b.position[self._i]
    @property
    def direction(self):
        """normalised momentum direction as 3-dimensional array"""
        return self._b.direction[self._i]
    @property
    def polarisation(self):
        """polarisation vector as 3-dimensional array"""
        return self._b.polarisation[self._i]
    @property
    def x(self):
        """x-coordinate of position [cm]"""
        return self._b.x[self._i]
    @property
    def y(self):
        """y-coordinate of position [cm]"""
        return self._b.y[self._i]
    @property
    def z(self):
        """z-coordinate of position [cm]"""
        return self._b.z[self._i]
    @property
    def ux(self):
        """x-coordinate of normalised momentum direction"""
        return self._b.ux[self._i]
    @property
    def uy(self):
        """y-coordinate of normalised momentum direction"""
        return self._b.uy[self._i]
    @property
    def uz(self):
        """z-coordinate of normalised momentum direction"""
        return self._b.uz[self._i]
    @property
    def polx(self):
        """x-coordinate of polarisation vector"""
        return self._b.polx[self._i]
    @property
    def poly(self):
        """y-coordinate of polarisation vector"""
        return self._b.poly[self._i]
    @property
    def polz(self):
        """z-coordinate of polarisation vector"""
        return self._b.polz[self._i]
    @property
    def ekin(self):
        """kinetic energy [MeV]"""
        return self._b.ekin[self._i]
    @property
    def time(self):
        """time-stamp [millisecond]"""
        return self._b.time[self._i]
    @property
    def weight(self):
        """weight or intensity"""
        return self._b.weight[self._i]
    @property
    def userflags(self):
        """custom per-particle flags"""
        return self._b.userflags[self._i]
    @property
    def wavelength(self):
        """wavelength [Aa] of neutrons and gammas (NaN for other particles)"""
        return wavelength_from_ekin(self.ekin, self.pdgcode)
    @property
    def pdgcode(self):
        """MC particle number from the Particle Data Group (2112=neutron, 22=gamma, ...)"""
        return self._b.pdgcode[self._i]
    @property
    def file_index(self):
        """Particle position in file (counting from 0)"""
        return self._b._offset + self._i

class MCPLParticleBlock:
    """Object representing a block of particle. Fields are arrays rather than single
    numbers, but otherwise have the same meaning as on the MCPLParticle class."""

    def __init__(self,opt_polarisation,opt_userflags,opt_globalw,opt_globalpdg,fmtversion):
        """For internal use only - users should not normally create MCPLParticle objects themselves"""
        #empty block (set offset to max int to ensure d<0 in contains_ipos and get_by_global:
        self._offset = 9223372036854775807
        #non-constant columns (never the same in all blocks):
        self._data = ()
        #potentially constant columns (first entry says whether non-constant, second is cache):
        self._polx = [opt_polarisation,None]
        self._poly = [opt_polarisation,None]
        self._polz = [opt_polarisation,None]
        self._uf = [bool(opt_userflags),None]
        self._w = [not opt_globalw,None]
        self._pdg = [not opt_globalpdg,None]
        self._opt_globalw = opt_globalw
        self._opt_globalpdg = opt_globalpdg
        self._fmtversion = fmtversion
        self._view_pos = None
        self._view_pol = None
        self._view_dir = None
        self._pos_cache,self._pol_cache = None,None#extra ndarrays for numpy 1.14 issue

    def _set_data(self,data,file_offset):
        #always present, but must unpack:
        self._ux,self._uy,self._uz,self._ekin = None,None,None,None
        self._view_dir = None

        #reset non-constant columns:
        for ncc in [self._polx,self._poly,self._polz,self._uf,self._w,self._pdg]:
            if ncc[0]:
                ncc[1]=None
        self._view_pos = None
        if self._polx[0]:
            self._view_pol = None

        if data is None:
            self._offset = 9223372036854775807
            self._data = ()
        else:
            self._data = data
            self._offset = file_offset

    def contains_ipos(self,ipos):
        d=ipos-self._offset
        return d>=0 and d<len(self._data)

    def __getitem__(self,ipos):
        """Access single particle in block by local position in block (not global position in file)"""
        if ipos>=0 and ipos<len(self._data):
            return MCPLParticle(self,ipos)
        return None

    def get_by_global(self,ipos):
        """Access single particle in block by global position in file"""
        d = ipos - self._offset
        if d>=0 and d<len(self._data):
            return MCPLParticle(self,d)
        return None

    @property
    def particles(self):
        """Use to iterate over all particles in block:

           for p in theblock.particles:
               print p.x,p.y,p.z
        """
        for i in range(len(self._data)):
            yield self[i]

    def __len__(self):
        return len(self._data)

    @property
    def wavelength(self):
        """wavelength [Aa] of neutrons and gammas (NaN for other particles)"""
        return wavelength_from_ekin(self.ekin, self.pdgcode)

    @property
    def file_offset(self):
        """Particle position in file of first particle in block (counting from 0)"""
        return self._offset

    @property
    def polx(self):
        x = self._polx
        if x[0]:
            if x[1] is None:
                x[1] = self._data['polx'].astype(float)
            return x[1]
        if x[1] is None or len(x[1]) != len(self._data):
            x[1] = np.zeros(len(self._data),dtype=float)
        return x[1]

    @property
    def poly(self):
        x = self._poly
        if x[0]:
            if x[1] is None:
                x[1] = self._data['poly'].astype(float)
            return x[1]
        if x[1] is None or len(x[1]) != len(self._data):
            x[1] = np.zeros(len(self._data),dtype=float)
        return x[1]

    @property
    def polz(self):
        x = self._polz
        if x[0]:
            if x[1] is None:
                x[1] = self._data['polz'].astype(float)
            return x[1]
        if x[1] is None or len(x[1]) != len(self._data):
            x[1] = np.zeros(len(self._data),dtype=float)
        return x[1]

    @property
    def pdgcode(self):
        x = self._pdg
        if x[0]:
            if x[1] is None:
                x[1] = self._data['pdg']
            return x[1]
        if x[1] is None or len(x[1]) != len(self._data):
            x[1] = self._opt_globalpdg * np.ones(len(self._data),dtype=int)
        return x[1]

    @property
    def weight(self):
        x = self._w
        if x[0]:
            if x[1] is None:
                x[1] = self._data['w'].astype(float)
            return x[1]
        if x[1] is None or len(x[1]) != len(self._data):
            x[1] = self._opt_globalw * np.ones(len(self._data),dtype=float)
        return x[1]

    @property
    def userflags(self):
        x = self._uf
        if x[0]:
            if x[1] is None:
                x[1] = self._data['uf']
            return x[1]
        if x[1] is None or len(x[1]) != len(self._data):
            x[1] = np.zeros(len(self._data),dtype=np.uint32)
        return x[1]

    @property
    def position(self):
        if self._view_pos is None:
            self._view_pos = np_stack((self.x,self.y,self.z),axis=1)
        return self._view_pos

    @property
    def polarisation(self):
        if self._view_pol is None or len(self._view_pol) != len(self._data):
            self._view_pol = np_stack((self.polx,self.poly,self.polz),axis=1)
        return self._view_pol

    @property
    def direction(self):
        if self._view_dir is None:
            if self._ux is None:
                self._unpack()
            self._view_dir = np_stack((self._ux,self._uy,self._uz),axis=1)
        return self._view_dir

    @property
    def x(self):
        return self._data['x']
    @property
    def y(self):
        return self._data['y']
    @property
    def z(self):
        return self._data['z']
    @property
    def time(self):
        return self._data['t']
    @property
    def ux(self):
        if self._ux is None:
            self._unpack()
        return self._ux
    @property
    def uy(self):
        if self._uy is None:
            self._unpack()
        return self._uy
    @property
    def uz(self):
        if self._uz is None:
            self._unpack()
        return self._uz
    @property
    def ekin(self):
        if self._ekin is None:
           self._ekin = abs(self._data['uve3']).astype(float)
        return self._ekin

    def _unpack(self):
        #On demand unpacking of unit vector. We have to make a version of
        #mcpl.c's mcpl_unitvect_unpack_adaptproj which can be efficiently
        #delegated to the compiled numpy library:
        if self._fmtversion==2:
            return self._unpack_legacy()#old packing scheme
        in0 = self._data['uve1'].astype(float)
        in1 = self._data['uve2'].astype(float)
        #NB: numpy 1.3 does not have copysign fct, only signbit:
        in2 = np.where(np.signbit(self._data['uve3']),-1.0,1.0)
        #reciprocals without zero division (fallback value will never be used):
        in0inv = 1.0/np.where(in0!=0.0,in0,1.0)
        in1inv = 1.0/np.where(in1!=0.0,in1,1.0)
        conda = (np.abs(in0)>1.0)
        condb = np.logical_and(np.logical_not(conda),(np.abs(in1)>1.0))
        #nb, reuse intermediate results below:
        in0sq = np.square(in0)
        in1sq = np.square(in1)
        self._ux = np.where(conda,
                            in2 * np.sqrt(np.clip(1.0-(in1sq+np.square(in0inv)),0.0,1.0)),
                            in0)
        self._uy = np.where(condb,
                            in2 * np.sqrt(np.clip(1.0-(in0sq+np.square(in1inv)),0.0,1.0)),
                            in1)
        self._uz = np.where(conda,
                            in0inv,
                            np.where(condb,
                                     in1inv,
                                     in2 * np.sqrt(np.clip(1.0-(in0sq+in1sq),0.0,1.0))))

    def _unpack_legacy(self):
        in0 = self._data['uve1'].astype(float)
        in1 = self._data['uve2'].astype(float)
        abs_in0 = np.abs(in0)
        abs_in1 = np.abs(in1)
        self._uz = (1.0 - abs_in0) - abs_in1
        zneg = ( self._uz < 0.0 )
        not_zneg = np.logical_not(zneg)
        self._ux = not_zneg * in0 + zneg * ( 1.0 - abs_in1 ) * np.where(in0 >= 0.0,1.0,-1.0)
        self._uy = not_zneg * in1 + zneg * ( 1.0 - abs_in0 ) * np.where(in1 >= 0.0,1.0,-1.0)
        n = 1.0 / np.sqrt(np.square(self._ux)+np.square(self._uy)+np.square(self._uz))
        self._ux *= n
        self._uy *= n
        self._uz *= n
        self._uz = np.where(np.signbit(self._data['uve3']),0.0,self._uz)
