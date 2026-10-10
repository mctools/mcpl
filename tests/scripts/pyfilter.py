
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


# NEEDS: numpy

# Test selection and editing of particles with expressions in the Python API
# (ParticleFilter and ParticleEdit), and the python examples about selecting
# and editing particles.

import pathlib
import sys

import mcpldev as mcpl
import numpy as np
from mcpldev._physics import wavelength_from_ekin
from MCPLTestUtils.dirs import test_data_dir

example_file = test_data_dir.parent.parent.joinpath('examples','example.mcpl')

def test_expressions():
    with mcpl.MCPLFile(example_file) as f:
        b = f.read_block()
    wl = b.wavelength
    cases = [ ('ekin > 25keV && x <= 2cm + y && pdgcode != 22',
               (b.ekin>0.025)&(b.x<=2.0+b.y)&(b.pdgcode!=22)),
              ('pdgcode == neutron && ekin < 500keV', (b.pdgcode==2112)&(b.ekin<0.5)),
              ('!(pdgcode == gamma) || ekin > 1GeV', ~(b.pdgcode==22)|(b.ekin>1000)),
              ('0cm < x < 10mm && !(abs(y) >= 1cm)', (0<b.x)&(b.x<1.0)&~(np.abs(b.y)>=1)),
              ('sqrt(x**2+y**2) < 5cm', np.hypot(b.x,b.y)<5),
              ('sqrt(x^2+y^2) < 5cm', np.hypot(b.x,b.y)<5),
              ('hypot(x,y) < 0.05m', np.hypot(b.x,b.y)<5),
              ('hypot(x,y,z) < 25cm', np.sqrt(b.x**2+b.y**2+b.z**2)<25),
              ('x^2 + y^2 < 4cm^2', b.x**2+b.y**2 < 4),
              ('x^2 + y^2 < 400 mm^2', b.x**2+b.y**2 < 4),
              ('(pdgcode == neutron || pdgcode == gamma) && wavelength > 0.005Aa', wl > 0.005),
              ('(pdgcode == neutron || pdgcode == gamma) && wavelength > 0.0005nm', wl > 0.005),
              ('(pdgcode == neutron || pdgcode == gamma) && wavelength > 5e-13m', wl > 0.005),
              ('pdgcode == proton || (pdgcode == gamma && wavelength > 0.5Aa)', (wl > 0.5)|(b.pdgcode==2212)),
              ('pdgcode == neutron && wavelength > 0.005Aa', (b.pdgcode==2112)&(wl > 0.005)),
              ('pdgcode != neutron || wavelength > 0.005Aa', (b.pdgcode!=2112)|(wl > 0.005)),
              ('pdgcode == gamma and 0 < 2*wavelength < x', (b.pdgcode==22)&(wl*2e-8 < b.x)),
              ('uz > cos(10*pi/180)', b.uz > np.cos(np.radians(10))),
              ('acos(uz) < 10deg', np.arccos(b.uz) < np.radians(10)),
              ('time < 10us', b.time < 0.01),
              ('(userflags & 1) == 0 && weight == 1', np.ones(len(b),dtype=bool)),
              ('ekin/1meV % 2 < 1', np.mod(b.ekin/1e-9,2) < 1),
              ('max(abs(x),abs(y)) < 3cm', np.maximum(np.abs(b.x),np.abs(b.y)) < 3),
              ('ekin/keV > 500', b.ekin/1e-3 > 500),
              ('abs(x) < 1cm + 2mm', np.abs(b.x) < 1.2),
              ('1 < 2', np.ones(len(b),dtype=bool)),
              ('x > 0 && y <= -0', (b.x>0)&(b.y<=0)),
              ('0 < x < 2cm', (b.x>0)&(b.x<2)),
              ('ekin > 0 and time > 0 or z == 0', ((b.ekin>0)&(b.time>0))|(b.z==0)),
              ('userflags & 0x10', (b.userflags & 0x10) != 0),
              ('!(userflags & 1) && pdgcode != 0b0', ((b.userflags & 1) == 0)&(b.pdgcode!=0)),
              ('pdgcode == electron || pdgcode == positron', np.isin(b.pdgcode,(11,-11))),
              ('pdgcode == antielectron || pdgcode == photon', np.isin(b.pdgcode,(-11,22))),
              ('pdgcode == muon || pdgcode == antimuon || pdgcode == antiproton || pdgcode == antineutron',
               np.isin(b.pdgcode,(13,-13,-2212,-2112))) ]
    for expr, ref in cases:
        flt = mcpl.ParticleFilter(expr)
        sel = flt(b)
        print(f'{flt!r}: selects {np.sum(sel)}')
        assert sel.dtype == bool and np.array_equal(sel, ref), expr
    edit = mcpl.ParticleEdit('tmp = x, x = -y, y = tmp + 2cm, z *= 2, weight = weight*0.5, time += 1ms, pdgcode = neutron')
    r = edit(b)
    ok = ( np.allclose(r['x'],-b.y) and np.allclose(r['y'],b.x+2) and np.allclose(r['z'],2*b.z)
           and np.allclose(r['weight'],0.5*b.weight) and np.allclose(r['time'],b.time+1)
           and np.all(r['pdgcode']==2112) and r['pdgcode'].dtype.kind == 'i' )
    print(f'{edit!r}: fields {sorted(r)}, as expected: {ok}')
    assert ok
    n = b[b.pdgcode==2112]
    for ed, ref in ( ('wavelength = 1.8Aa', 1.8), ('wavelength = 0.18nm', 1.8),
                     ('wavelength = 1.8Aa + wavelength', 1.8+n.wavelength),
                     ('wavelength *= 2', 2*n.wavelength) ):
        r = mcpl.ParticleEdit(ed)(n)
        wl = wavelength_from_ekin(r['ekin'],n.pdgcode)
        print(f'ParticleEdit({ed!r}) as expected: {np.allclose(wl,ref)}')
        assert sorted(r) == ['ekin'] and np.allclose(wl,ref)
    r = mcpl.ParticleEdit('z = 0, x = -0, time = 0')(b)
    assert np.all(r['z']==0) and np.all(r['x']==0) and np.all(r['time']==0)
    #Statements are executed in order:
    for ed, checks in (
            ('x = -y, y = x', lambda r : np.allclose(r['x'],-b.y) and np.allclose(r['y'],-b.y)),
            ('x = 1cm, x += 1cm', lambda r : np.all(r['x']==2)),
            ('tmp = x, x = 2m, z = 2*tmp', lambda r : sorted(r) == ['x','z'] and np.allclose(r['z'],2*b.x)),
            ('a = ekin, ekin = 1MeV, ekin += a', lambda r : np.allclose(r['ekin'],1+b.ekin)),
            ('ekin *= 2, weight = ekin/MeV', lambda r : np.allclose(r['weight'],2*b.ekin)),
            ('swap(x,y)', lambda r : np.allclose(r['x'],b.y) and np.allclose(r['y'],b.x)),
            ('tmp = x, swap(tmp,y), x = tmp', lambda r : sorted(r) == ['x','y'] and np.allclose(r['x'],b.y)),
            ('rotate_z(90deg)', lambda r : ( sorted(r) == ['polx','poly','ux','uy','x','y']
                                             and np.allclose(r['x'],-b.y) and np.allclose(r['y'],b.x)
                                             and np.allclose(r['ux'],-b.uy) and np.allclose(r['uy'],b.ux) )),
            ('rotate_x(90deg)', lambda r : np.allclose(r['y'],-b.z) and np.allclose(r['z'],b.y)),
            ('rotate_y(90deg), x += 10cm', lambda r : np.allclose(r['x'],b.z+10) and np.allclose(r['z'],-b.x)),
            ('x += 10cm, rotate_y(pi/2)', lambda r : np.allclose(r['x'],b.z) and np.allclose(r['z'],-(b.x+10))),
            ('x = clamp(x, -1cm, 1cm), y = min(y, 1cm, 2mm), z = max(z, 0, 25cm)',
             lambda r : ( np.allclose(r['x'],np.clip(b.x,-1,1)) and np.allclose(r['y'],np.minimum(b.y,0.2))
                          and np.allclose(r['z'],np.maximum(b.z,25)) )) ):
        ok = checks(mcpl.ParticleEdit(ed)(b))
        print(f'ParticleEdit({ed!r}) as expected: {ok}')
        assert ok
    r = mcpl.ParticleEdit('wavelength = 1.8Aa, weight = wavelength/Aa, time = 0')(n)
    assert sorted(r) == ['ekin','time','weight'] and np.allclose(r['weight'],1.8)
    r = mcpl.ParticleEdit('ekin = 1MeV, wavelength = 2Aa')(n)
    assert np.allclose(wavelength_from_ekin(r['ekin']),2)
    r = mcpl.ParticleEdit('z += 1mm, time = time + 2us, ekin = 25meV')(b)
    assert np.allclose(r['z'],b.z+0.1) and np.allclose(r['time'],b.time+0.002) and np.allclose(r['ekin'],25e-9)
    r = mcpl.ParticleEdit('x = 2m*ux, y = uy*1m, ux = min(ux, 0.5), weight = 2')(b)
    assert ( np.allclose(r['x'], 200*b.ux) and np.allclose(r['y'], 100*b.uy)
             and np.allclose(r['ux'], np.minimum(b.ux,0.5)) and np.all(r['weight']==2) )
    for bad in ('wavelength > 1.8Aa', 'x > 0 && wavelength > 1.8Aa', 'pdgcode == proton || wavelength > 1Aa',
                'x < 2', 'x > 0.0001', 'x > 2 - 2', 'ekin > 0.025', 'wavelength > 1.8', 'x^2 + y^2 < 4',
                'x < 1meV', 'ekin > 2cm', 'sin(x) > 0', 'x^0.5 > 1cm', 'sqrt(x) < 2',
                'x + time > 0cm', 'ekin^x > 1', 'atan2(x, ekin) > 0', 'hypot(x) > 1cm',
                'hypot(x,ekin) > 1cm', 'abs(y) > 1cm + 1',
                'wl > 1Aa', 'dirx > 0', 't < 1ms', 'is_neutron', 'neutron_wl > 1Aa',
                'degrees(acos(uz)) < 10',
                'ekin = 1MeV', 'ekin > 1MeV & x < 2cm', 'foo > 1',
                "__import__('os').system('ls')", 'ekin', 'lambda: 1',
                'sin(x, y=1) > 0', 'x.real > 0', '[x][0] > 0', "x > 'a'", ''):
        try:
            mcpl.ParticleFilter(bad)(b)
            print(f'ParticleFilter({bad!r}): no error')
        except mcpl.MCPLError as e:
            print(f'ParticleFilter({bad!r}): {e}')
    for bad in ('x = 2*ux', 'x = 2', 'ekin = 0.025', 'wavelength = 1.8', 'z += 1',
                'x = 1meV', 'wavelength = 1keV', 'time = 2*x', 'weight = 1cm',
                'x', 'foo = 1', 'wl = 1.8Aa', 'tmp = x, x = y', 'Tmp = 1', 'tmp += 1cm', 'x = tmp', 'clamp = 1',
                'swap(x,ekin)', 'swap(x)', 'swap(x,2)', 'rotate_z(1cm)', 'rotate_q(1)',
                'rotate_z(1,2)', 'x = clamp(x,1cm)', 'x = min(x)',
                'x == 1cm', 'pi = 3', 'wl = 1Aa', 'x = 1cm; y = 1cm',
                'x = y = 1cm', 'x, y = y, x', '', 'pdgcode = 1.5'):
        try:
            mcpl.ParticleEdit(bad)(b)
            print(f'ParticleEdit({bad!r}): no error')
        except mcpl.MCPLError as e:
            print(f'ParticleEdit({bad!r}): {e}')

def run_example(name, *args):
    f = test_data_dir.parent.parent.joinpath('examples',name)
    code = f.read_text().replace('\nimport mcpl\n','\nimport mcpldev as mcpl\n')
    assert 'import mcpldev as mcpl' in code
    sys.argv = [ str(f), *args ]
    exec(compile(code,str(f),'exec'),{'__name__':'__main__'})  # noqa: S102

def test_examples():
    run_example('pyexample_filtermcpl', str(example_file), 'filtered.mcpl')
    with mcpl.MCPLFile('filtered.mcpl') as f:
        b = f.read_block()
        print(f'pyexample_filtermcpl wrote {f.nparticles} particles with comments {f.comments}')
        assert np.all(b.pdgcode==2112) and np.all(b.ekin<0.1)
    run_example('pyexample_editmcpl', str(example_file))
    for fn in ('neutrons.mcpl','gammas.mcpl'):
        assert pathlib.Path(fn).is_file()

if __name__ == '__main__':
    test_expressions()
    test_examples()
