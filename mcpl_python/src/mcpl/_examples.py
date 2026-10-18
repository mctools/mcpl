
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

"""Example files with many particles, for trying out mcpltool and the mcpl
Python package (mcpltool --create-examples). The particles are generated
from simple distributions, not by a simulation."""

__all__ = []

import pathlib

from ._common import MCPLError
from ._messages import _info
from ._numpy import np

_default_nparticles = 1_000_000
_blocksize = 1_000_000
_seed = 20171017
_comment = ( 'Example file made by mcpltool --create-examples, with particles'
             ' generated from simple distributions (not by a simulation)' )

#Energies in MeV, lengths in cm, times in ms:
_kT_300K = 2.585e-8
_kT_25K = 2.154e-9
_wavelength_to_ekin = 8.180420e-8#E[MeV] = this / (wavelength[Aa])^2

def _loguniform( rng, lo, hi, n ):
    return lo * ( hi / lo ) ** rng.random(n)

def _isotropic( rng, n ):
    uz = rng.uniform(-1.0,1.0,n)
    phi = rng.uniform(0.0,2*np.pi,n)
    r = np.sqrt(np.maximum(0.0,1.0-uz**2))
    return r*np.cos(phi), r*np.sin(phi), uz

def _cosine_law( rng, n ):
    """Directions into the +z half-space, distributed as from a surface which
    emits uniformly (a cosine law)"""
    uz = np.sqrt(rng.random(n))
    phi = rng.uniform(0.0,2*np.pi,n)
    r = np.sqrt(np.maximum(0.0,1.0-uz**2))
    return r*np.cos(phi), r*np.sin(phi), uz

def _neutron_source( rng, n ):
    """Neutrons leaving the 10cm x 10cm surface of a moderator: cold and
    thermal Maxwellian spectra, an epithermal 1/E part and a fast tail."""
    kind = rng.choice(4,size=n,p=[0.25,0.40,0.28,0.07])
    ekin = np.empty(n)
    for k,fct in enumerate([
            lambda m : rng.gamma(2.0,_kT_25K,m),
            lambda m : rng.gamma(2.0,_kT_300K,m),
            lambda m : _loguniform(rng,2e-7,1.0,m),
            lambda m : rng.gamma(2.0,1.3,m) ]):
        sel = kind == k
        ekin[sel] = fct(int(sel.sum()))
    ux, uy, uz = _cosine_law(rng,n)
    #Emission during a 2.86 ms pulse, with slower neutrons leaving later:
    time = ( rng.uniform(0.0,2.86,n)
             + rng.exponential(np.where(ekin<1e-6,0.15,0.005)) )
    return { 'pdgcode' : np.int32(2112), 'ekin' : ekin,
             'x' : rng.uniform(-5.0,5.0,n), 'y' : rng.uniform(-5.0,5.0,n),
             'z' : 0.0, 'ux' : ux, 'uy' : uy, 'uz' : uz, 'time' : time,
             'weight' : 1.0 }

_target_types = ( ( 2112, 0.55 ), ( 22, 0.30 ), ( 2212, 0.05 ), ( 11, 0.04 ),
                  ( -11, 0.02 ), ( 211, 0.02 ), ( -211, 0.01 ), ( 13, 0.01 ) )

def _target( rng, n ):
    """Mixed particles leaving the surface of a sphere with a radius of 20cm
    around a target hit by a proton beam."""
    codes = np.array([ c for c,_ in _target_types ],dtype=np.int32)
    probs = np.array([ p for _,p in _target_types ])
    pdgcode = codes[rng.choice(len(codes),size=n,p=probs/probs.sum())]
    ekin = np.empty(n)
    def fill( sel, fct ):
        ekin[sel] = fct(int(sel.sum()))
    neutron = pdgcode == 2112
    cascade = rng.random(n) < 0.2
    fill( neutron & ~cascade, lambda m : rng.gamma(2.0,1.5,m) )
    fill( neutron & cascade, lambda m : _loguniform(rng,20.0,2000.0,m) )
    gamma = pdgcode == 22
    line = rng.random(n)
    fill( gamma & ( line < 0.1 ), lambda m : np.full(m,2.223) )
    fill( gamma & ( line >= 0.1 ) & ( line < 0.2 ), lambda m : np.full(m,0.511) )
    fill( gamma & ( line >= 0.2 ), lambda m : rng.exponential(1.5,m) )
    fill( pdgcode == 2212, lambda m : _loguniform(rng,10.0,2000.0,m) )
    fill( np.abs(pdgcode) == 11, lambda m : rng.exponential(2.0,m) )
    fill( np.abs(pdgcode) == 211, lambda m : _loguniform(rng,50.0,1500.0,m) )
    fill( pdgcode == 13, lambda m : _loguniform(rng,10.0,1000.0,m) )
    #Positions on the sphere, and directions pointing outwards (more forward,
    #along the beam, for higher energies):
    nx, ny, nz = _isotropic(rng,n)
    dx, dy, dz = _isotropic(rng,n)
    forward = np.clip( np.log10(np.maximum(ekin,1e-3))/4.0, 0.0, 0.8 )
    dx, dy, dz = ( nx + dx, ny + dy, nz + dz + 4*forward )
    flip = dx*nx + dy*ny + dz*nz < 0.0
    dx, dy, dz = ( np.where(flip,-dx,dx), np.where(flip,-dy,dy),
                   np.where(flip,-dz,dz) )
    norm = np.sqrt(dx**2+dy**2+dz**2)
    return { 'pdgcode' : pdgcode, 'ekin' : ekin,
             'x' : 20.0*nx, 'y' : 20.0*ny, 'z' : 20.0*nz,
             'ux' : dx/norm, 'uy' : dy/norm, 'uz' : dz/norm,
             'time' : rng.exponential(np.where(neutron,1e-3,2e-6)),
             'weight' : rng.lognormal(0.0,0.5,n) }

_userdata_layout = 'nscat:uint8,pathlength:float32,origin:uint32'

def _polarised_beam( rng, n ):
    """Polarised neutrons with a wavelength around 1.8Aa in a beam along z,
    with userdata: the number of scatterings, the path length (in cm) and the
    number of the volume where they started."""
    wl = rng.normal(1.8,0.1,n)
    pol = np.array(_isotropic(rng,n)) * rng.uniform(0.5,1.0,n)
    pol[2] = np.abs(pol[2])#(mostly along +z)
    ux, uy = rng.normal(0.0,0.005,n), rng.normal(0.0,0.005,n)
    userdata = { 'nscat' : np.minimum(rng.poisson(1.2,n),255),
                 'pathlength' : rng.gamma(2.0,50.0,n),
                 'origin' : rng.integers(0,10,n) }
    return { 'pdgcode' : np.int32(2112), 'ekin' : _wavelength_to_ekin / wl**2,
             'x' : rng.normal(0.0,0.5,n), 'y' : rng.normal(0.0,0.5,n),
             'z' : 0.0, 'ux' : ux, 'uy' : uy,
             'uz' : np.sqrt(np.maximum(0.0,1.0-ux**2-uy**2)),
             'polx' : pol[0], 'poly' : pol[1], 'polz' : pol[2],
             'time' : rng.normal(5.0,0.2,n), 'weight' : 1.0,
             'userdata' : userdata }

_examples = (
    ( 'mcplexample_source.mcpl.gz', _neutron_source,
      {}, 'Neutrons leaving a moderator surface' ),
    ( 'mcplexample_target.mcpl.gz', _target,
      {}, 'Mixed particles leaving the surroundings of a target' ),
    ( 'mcplexample_beam.mcpl.gz', _polarised_beam,
      { 'opt_polarisation' : True, 'userdata_layout' : _userdata_layout },
      'Polarised neutron beam, with userdata' ),
)

def create_examples( nparticles = None, directory = '.', dry_run = False ):
    """Create the example files (each with nparticles particles, default 1
    million) in directory. Existing files are not overwritten. Returns the
    list of files created."""
    from ._writer import MCPLOutFile
    n = _default_nparticles if nparticles is None else nparticles
    if not ( isinstance(n,int) and n > 0 ):
        raise MCPLError(f'Invalid number of particles: {nparticles}')
    d = pathlib.Path(directory)
    names = [ d / fn for fn,*_ in _examples ]
    for fn in names:
        for f in ( fn, fn.with_suffix('') ):
            if f.exists():
                raise MCPLError(f'File {f.as_posix()} already exists')
    created = []
    for (fn,fct,options,descr), path in zip(_examples,names):
        _info(f'{"Would create" if dry_run else "Creating"} {path.as_posix()}'
              f' with {n} particles ({descr.lower()})')
        rng = np.random.default_rng(_seed)
        out = MCPLOutFile( path.with_suffix(''), sourcename = 'mcpltool',
                           comments = [ _comment, descr ],
                           _dry_run = dry_run, **options )
        try:
            todo = n
            while todo:
                m = min(todo,_blocksize)
                out.add_particles(**fct(rng,m))
                todo -= m
        except BaseException:
            out._abort()
            raise
        if dry_run:
            out.close()
            continue
        if not out.closeandgzip():
            raise MCPLError(f'Failed to gzip {path.with_suffix("").as_posix()}')
        created.append(path.as_posix())
    return created
