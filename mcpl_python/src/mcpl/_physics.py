
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

"""Physics data, like the descriptions of PDG codes."""

__all__ = []

_db_pdg = None
_db_elem = None
def _pdg_database(pdgcode):
    global _db_pdg, _db_elem
    if _db_pdg is None:
        _db_pdg = { 12:'nu_e',14:'nu_mu',16:'nu_tau',-12:'nu_e-bar',-14:'nu_mu-bar',
                    -16:'nu_tau-bar',2112:'n',2212:'p',-2112:'n-bar',-2212:'p-bar',
                    22:'gamma',11:'e-',-11:'e+',13:'mu-',-13:'mu+',15:'tau-',-15:'tau+',
                    211:'pi+',-211:'pi-',111:'pi0',321:'K+',-321:'K-',130:'Klong',
                    310:'Kshort',-1000010020:'D-bar',-1000010030:'T-bar',1000010020:'D',
                    1000010030:'T',1000020040:'alpha',-1000020040:'alpha-bar' }
    r=_db_pdg.get(pdgcode,None)
    if r is not None:
        return r
    if _db_elem is None:
        _db_elem = ['H',  'He', 'Li', 'Be', 'B',  'C',  'N',  'O',  'F',  'Ne',
                    'Na', 'Mg', 'Al', 'Si', 'P' , 'S',  'Cl', 'Ar', 'K',  'Ca', 'Sc',
                    'Ti', 'V',  'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge',
                    'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y',  'Zr', 'Nb', 'Mo', 'Tc',
                    'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'I',  'Xe',
                    'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb',
                    'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'W',  'Re', 'Os',
                    'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr',
                    'Ra', 'Ac', 'Th', 'Pa', 'U',  'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf',
                    'Es', 'Fm', 'Md', 'No', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs', 'Mt',
                    'Ds', 'Rg']
    if pdgcode>0 and pdgcode//100000000==10:
        III = pdgcode % 10
        pdgcode //= 10
        AAA = pdgcode%1000
        pdgcode //= 1000
        ZZZ = pdgcode%1000
        pdgcode //= 1000
        L = pdgcode % 10
        pdgcode //= 10
        if pdgcode==10 and ZZZ>0 and AAA>0:
            if L==0 and III==0 and ZZZ < len(_db_elem)+1:
                return f'{_db_elem[ZZZ-1]}{AAA}'
            s = f'ion(Z={ZZZ},A={AAA}'
            if L:
                s += f',L={L}'
            if III:
                s += f',I={III}'
            s += ')'
            return s
    return None
