
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

"""Particle expressions (selections and edits), which are evaluated with numpy
on blocks of particles."""

__all__ = [ 'ParticleEdit', 'ParticleFilter', 'ParticleValue' ]

import ast
import math
import re

from ._common import MCPLError
from ._numpy import np
from ._physics import _particle_names, ekin_from_wavelength, wavelength_from_ekin

_expr_fields = ( 'x', 'y', 'z', 'ux', 'uy', 'uz', 'polx', 'poly', 'polz',
                 'ekin', 'time', 'weight', 'pdgcode', 'userflags',
                 'wavelength' )
_expr_constants = { 'pi' : math.pi, **_particle_names }
#Dimensions (length,energy,time) and units of quantities in expressions. Values
#are internally in the units of MCPL (cm, MeV, ms), also for wavelengths:
_dim_none = (0,0,0)
_dim_L, _dim_E, _dim_T = (1,0,0), (0,1,0), (0,0,1)
_expr_units = { 'meV' : (1e-9,_dim_E), 'eV' : (1e-6,_dim_E),
                'keV' : (1e-3,_dim_E), 'MeV' : (1.0,_dim_E),
                'GeV' : (1e3,_dim_E), 'TeV' : (1e6,_dim_E),
                'ns' : (1e-6,_dim_T), 'us' : (1e-3,_dim_T),
                'ms' : (1.0,_dim_T), 's' : (1e3,_dim_T),
                'Aa' : (1e-8,_dim_L), 'nm' : (1e-7,_dim_L),
                'um' : (1e-4,_dim_L), 'mm' : (0.1,_dim_L),
                'cm' : (1.0,_dim_L), 'm' : (100.0,_dim_L),
                'km' : (1e5,_dim_L),
                'deg' : (math.pi/180,None), 'rad' : (1.0,None) }
_expr_field_dims = { 'x' : _dim_L, 'y' : _dim_L, 'z' : _dim_L,
                     'ekin' : _dim_E, 'time' : _dim_T,
                     'wavelength' : _dim_L }
_expr_wl_unit = 1e-8#wavelengths are in Aa in the Python API
#Example units to suggest in error messages:
_expr_unit_hints = { _dim_L : 'cm', _dim_E : 'MeV', _dim_T : 'ms' }
#Functions requiring dimensionless arguments:
_expr_functions_nodim = { 'exp' : np.exp, 'log' : np.log, 'log10' : np.log10,
                          'sin' : np.sin, 'cos' : np.cos, 'tan' : np.tan,
                          'asin' : np.arcsin, 'acos' : np.arccos,
                          'atan' : np.arctan }
#Functions keeping the units of the argument(s):
_expr_functions_samedim = { 'abs' : np.abs, 'floor' : np.floor,
                            'ceil' : np.ceil, 'min' : np.minimum,
                            'max' : np.maximum, 'hypot' : np.hypot,
                            'clamp' : np.clip }
#Functions used as statements in edits:
_edit_statements = ( 'swap', 'rotate_x', 'rotate_y', 'rotate_z' )
#Components of position, direction and polarisation changed by rotations:
_rotation_planes = { 'rotate_x' : ( ('y','z'), ('uy','uz'), ('poly','polz') ),
                     'rotate_y' : ( ('z','x'), ('uz','ux'), ('polz','polx') ),
                     'rotate_z' : ( ('x','y'), ('ux','uy'), ('polx','poly') ) }
_expr_functions = dict( sqrt = np.sqrt, atan2 = np.arctan2,
                        **_expr_functions_nodim, **_expr_functions_samedim )

def _expr_preprocess( expr ):
    """Translate C-like syntax (&&, ||, !) to Python syntax, ^ to ** (powers),
    and numbers with units (e.g. 25meV) to multiplications."""
    e = expr.replace('&&',' and ').replace('||',' or ').replace('^','**')
    e = re.sub(r'!(?!=)',' not ',e)
    units = '|'.join(sorted(_expr_units,key=len,reverse=True))
    #(a power directly after a unit only applies to the unit, e.g. 4cm^2):
    e = re.sub(r'(?<![\w.])((?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)\s*(' + units
               + r')\b(\s*\*\*\s*\d+)?',
               lambda m : f'({m.group(1)}*{m.group(2)}{m.group(3) or ""})', e)
    return e

def _expr_check( node, expr, variables = () ):
    """Check that only supported constructs are used in parsed expression
    (variables are names of variables defined in edits)"""
    ok_nodes = ( ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp,
                 ast.Not, ast.USub, ast.UAdd, ast.Invert, ast.BinOp, ast.Add,
                 ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.FloorDiv,
                 ast.BitAnd, ast.BitOr, ast.Compare, ast.Eq, ast.NotEq,
                 ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Name, ast.Load,
                 ast.Constant, ast.Call, ast.IfExp )
    for n in ast.walk(node):
        if not isinstance( n, ok_nodes ):
            raise MCPLError(f'Unsupported syntax in expression "{expr}"')
        if isinstance(n,ast.Constant) and not isinstance(n.value,(int,float)):
            raise MCPLError(f'Unsupported value in expression "{expr}"')
        if isinstance(n,ast.Call) and ( n.keywords or not (
                isinstance(n.func,ast.Name) and n.func.id in _expr_functions ) ):
            raise MCPLError(f'Unsupported function call in expression "{expr}"'
                            ' (available functions are: '
                            + ', '.join(sorted(_expr_functions)) + ')')
        if isinstance(n,ast.Name) and not ( n.id in _expr_fields
                                            or n.id in variables
                                            or n.id in _expr_constants
                                            or n.id in _expr_units
                                            or n.id in _expr_functions ):
            raise MCPLError(f'Unknown name "{n.id}" in expression "{expr}"'
                            ' (particle fields are: '
                            + ', '.join(_expr_fields) + ')')

def _expr_parse( expr, mode = 'eval' ):
    try:
        tree = ast.parse( _expr_preprocess(expr).strip(), mode = mode )
    except SyntaxError:
        hint = ' (use == for comparisons)' if mode == 'eval' and '=' in expr else ''
        raise MCPLError(f'Syntax error in expression "{expr}"{hint}')
    return tree

class _Q:
    """Value with dimension (length,energy,time) in an expression. Values
    without units (like plain numbers, or ux) have dimension None. A plain 0
    (zero is the same in all units) is marked with zero=True, and can be used
    with any units."""
    __slots__ = ('d','v','zero')
    def __init__( self, v, d = None, zero = False ):
        self.v, self.d = v, ( None if d == _dim_none else d )
        self.zero = zero

def _dimstr( d ):
    if d is None:
        return 'value without units'
    res = []
    for n, e in zip(('length','energy','time'),d):
        if e:
            res.append( n if e == 1 else f'{n}^{e}' )
    return '*'.join(res)

def _unit_hint( d ):
    u = _expr_unit_hints.get(d)
    return f' (add units, e.g. 2{u})' if u else ''

class _ExprEvaluator:
    """Evaluates parsed expression on a block of particles with numpy"""
    def __init__( self, block, expr, state = None ):
        self._block = block
        self._expr = expr
        self._cache = {}
        #Values of variables and modified fields (in edits):
        self.state = state if state is not None else {}
        #Particles for which the current part of the expression is used (None
        #for all), e.g. only those for which the left side of && is true:
        self.active = None
    def error( self, msg ):
        raise MCPLError(f'{msg} in expression "{self._expr}"')
    def name( self, n ):
        if n == 'wavelength':
            self._check_wavelength()
        if n in self.state:
            return self.state[n]
        if n == 'wavelength' and ( 'ekin' in self.state or 'pdgcode' in self.state ):
            #Wavelength of modified particles:
            return _Q(wavelength_from_ekin(self.name('ekin').v,
                                           self.name('pdgcode').v) * _expr_wl_unit,
                      _dim_L)
        if n in _expr_constants:
            return _Q(_expr_constants[n])
        if n in _expr_units:
            v, d = _expr_units[n]
            return _Q(v,d)
        if n not in self._cache:
            v = getattr(self._block,n)
            if n == 'wavelength':
                v = v * _expr_wl_unit
            self._cache[n] = _Q(v,_expr_field_dims.get(n))
        return self._cache[n]
    def _check_wavelength( self ):
        pdg = np.asarray(self.name('pdgcode').v)
        bad = ~np.isin(pdg,(2112,22))
        if self.active is not None:
            bad &= self.active
        if np.any(bad):
            raise MCPLError('The wavelength is only defined for neutrons and gammas,'
                            ' so select those before using it, e.g. "pdgcode =='
                            f' neutron && wavelength > 1.8Aa" (in expression "{self._expr}")')
    def _with_active( self, mask, node ):
        """Evaluate node, for the particles where mask is true (and which are
        currently active)"""
        prev = self.active
        mask = np.asarray(mask,dtype=bool)
        self.active = mask if prev is None else ( prev & mask )
        try:
            return self(node)
        finally:
            self.active = prev
    def same( self, a, b, what ):
        """Check that a and b have the same dimension (for +, -, comparisons,
        etc.) and return their values and the dimension."""
        if a.d != b.d and ( a.zero or b.zero ):
            return a.v, b.v, ( a.d or b.d )
        if a.d != b.d:
            hint = _unit_hint(a.d or b.d) if None in (a.d,b.d) else ''
            self.error(f'Incompatible units in {what}: {_dimstr(a.d)} and'
                       f' {_dimstr(b.d)}{hint}')
        return a.v, b.v, a.d
    def nodim( self, q, what ):
        if q.d is not None:
            self.error(f'{what} requires a value without units, not {_dimstr(q.d)}')
        return q.v
    def __call__( self, node ):
        ev = self
        if isinstance(node,ast.Expression):
            return ev(node.body)
        if isinstance(node,ast.Constant):
            return _Q(node.value,zero=(node.value==0))
        if isinstance(node,ast.Name):
            return self.name(node.id)
        if isinstance(node,ast.BoolOp):
            #Like in C, the right side of && (||) is only used for particles
            #where the left side is true (false):
            is_and = isinstance(node.op,ast.And)
            fct = np.logical_and if is_and else np.logical_or
            res = self.boolval(ev(node.values[0]))
            for v in node.values[1:]:
                b = self.boolval(self._with_active(res if is_and else ~np.asarray(res,dtype=bool),v))
                res = fct(res,b)
            return _Q(res)
        if isinstance(node,ast.UnaryOp):
            q = ev(node.operand)
            if isinstance(node.op,ast.Not):
                return _Q(np.logical_not(self.boolval(q)))
            if isinstance(node.op,ast.USub):
                return _Q(-q.v,q.d,zero=q.zero)
            if isinstance(node.op,ast.Invert):
                return _Q(np.invert(self._int(q,'~')))
            return q
        if isinstance(node,ast.BinOp):
            return self.binop(node.op,ev(node.left),ev(node.right))
        if isinstance(node,ast.Compare):
            fcts = { ast.Eq : np.equal, ast.NotEq : np.not_equal,
                     ast.Lt : np.less, ast.LtE : np.less_equal,
                     ast.Gt : np.greater, ast.GtE : np.greater_equal }
            left, res = ev(node.left), True
            for op, c in zip(node.ops,node.comparators):
                right = ev(c)
                a, b, _ = self.same(left,right,'comparison')
                res = np.logical_and(res,fcts[type(op)](a,b))
                left = right
            return _Q(res)
        if isinstance(node,ast.IfExp):
            test = np.asarray(self.boolval(ev(node.test)),dtype=bool)
            a, b, d = self.same(self._with_active(test,node.body),
                                self._with_active(~test,node.orelse),'if-else')
            return _Q(np.where(test,a,b),d)
        if isinstance(node,ast.Call):
            return self.call(node.func.id,[ev(a) for a in node.args])
        raise MCPLError('Unsupported expression')#should not happen
    def binop( self, op, a, b ):
        if isinstance(op,(ast.BitAnd,ast.BitOr)):
            sym = '&' if isinstance(op,ast.BitAnd) else '|'
            fct = np.bitwise_and if sym == '&' else np.bitwise_or
            return _Q(fct(self._int(a,sym),self._int(b,sym)))
        with np.errstate(divide='ignore',invalid='ignore'):
            if isinstance(op,(ast.Add,ast.Sub,ast.Mod,ast.FloorDiv)):
                x, y, d = self.same(a,b,'arithmetic')
                fct = { ast.Add : np.add, ast.Sub : np.subtract,
                        ast.Mod : np.mod, ast.FloorDiv : np.floor_divide }[type(op)]
                return _Q(fct(x,y),d)
            if isinstance(op,(ast.Mult,ast.Div)):
                if isinstance(op,ast.Mult):
                    v, sign = a.v * b.v, 1
                else:
                    v, sign = np.true_divide(a.v,b.v), -1
                da, db = a.d or _dim_none, b.d or _dim_none
                d = tuple( i + sign * j for i,j in zip(da,db) )
                return _Q(v,d)
            #Power:
            if b.d is not None:
                self.error(f'Exponent with units ({_dimstr(b.d)})')
            if a.d is None:
                return _Q(np.power(np.asarray(a.v,dtype=float),b.v))
            e = np.asarray(b.v)
            if e.ndim or float(e) != round(float(e)):
                self.error('Values with units can only be raised to integer powers')
            e = round(float(e))
            return _Q(np.power(np.asarray(a.v,dtype=float),e),
                      tuple( i * e for i in a.d ))
    def call( self, fname, args ):
        fct = _expr_functions[fname]
        with np.errstate(divide='ignore',invalid='ignore'):
            if fname in _expr_functions_nodim:
                return _Q(fct(*[self.nodim(q,f'{fname}(..)') for q in args]))
            if fname == 'sqrt':
                if len(args) != 1:
                    self.error('sqrt(..) takes one argument')
                q = args[0]
                if q.d is None:
                    return _Q(np.sqrt(q.v))
                if any( i % 2 for i in q.d ):
                    self.error(f'sqrt(..) of value with {_dimstr(q.d)}')
                return _Q(np.sqrt(q.v),tuple( i // 2 for i in q.d ))
            if fname == 'atan2':
                if len(args) != 2:
                    self.error('atan2(..) takes two arguments')
                y, x, _ = self.same(args[0],args[1],'atan2(..)')
                return _Q(np.arctan2(y,x))
            #Functions keeping units:
            if fname == 'hypot':
                if len(args) < 2:
                    self.error('hypot(..) takes two or more arguments')
                d = args[0].d
                for q in args[1:]:
                    self.same(args[0],q,'hypot(..)')
                return _Q(np.sqrt(sum( np.square(q.v) for q in args )),d)
            if len(args) == 1 and fname in ('abs','floor','ceil'):
                return _Q(fct(args[0].v),args[0].d)
            if fname == 'clamp':
                if len(args) != 3:
                    self.error('clamp(value,low,high) takes three arguments')
                v, lo, d = self.same(args[0],args[1],'clamp(..)')
                _, hi, _ = self.same(args[0],args[2],'clamp(..)')
                return _Q(np.minimum(np.maximum(v,lo),hi),d)
            if len(args) < 2 or fname not in ('min','max'):
                self.error(f'Wrong number of arguments for {fname}(..)')
            res, d = args[0].v, args[0].d
            for q in args[1:]:
                _, y, d2 = self.same(args[0],q,f'{fname}(..)')
                d = d or d2
                res = fct(res,y)
            return _Q(res,d)
    @staticmethod
    def boolval( q ):
        return np.asarray(q.v).astype(bool) if np.asarray(q.v).dtype != bool else q.v
    @staticmethod
    def _int( q, op ):
        a = np.asarray(q.v)
        if a.dtype.kind not in 'iub':
            raise MCPLError(f'The bitwise operator {op} requires integer operands'
                            ' (use && and || for logical and/or)')
        return a

class _EmptyBlock:
    """Block without particles, for checking expressions before use"""
    def __len__( self ):
        return 0
    def __getattr__( self, name ):
        return np.zeros(0,dtype = int if name in ('pdgcode','userflags') else float)

class ParticleFilter:
    """Selection of particles based on an expression, which is evaluated with
    numpy on blocks of particles. For instance:

       flt = ParticleFilter("pdgcode == neutron && ekin < 25meV && abs(x) <= 2mm")
       for block in mcplfile.particle_blocks:
           selected = block[ flt(block) ]

    The expression syntax is like in C: particle fields (x, y, z, ux, uy,
    uz, polx, poly, polz, ekin, time, weight, pdgcode, userflags, and
    wavelength), numbers, arithmetic (+, -, *, /, %, and ^ or ** for powers),
    comparisons (which can be chained, as in "0 < x < 2cm"), logical operations
    (&&, ||, ! or and, or, not), bitwise & and | on integers (e.g. on
    userflags, as in "userflags & 0x10", where like in C integers which are not
    0 are true), functions (sqrt, abs, floor, ceil, exp, log, log10,
    sin, cos, tan, asin, acos, atan, atan2, hypot, min, max), the constant
    pi, and the names neutron, antineutron, proton, antiproton, electron,
    positron (or antielectron), muon, antimuon, and gamma (or photon), which
    can be used for pdgcode values. The wavelength is only defined for
    neutrons and gammas, so it is an error to use it for other particles, and
    expressions must select neutrons or gammas before using it, as in
    "pdgcode == neutron && wavelength > 1.8Aa" (the right side of && is only
    evaluated for particles where the left side is true, and the right side
    of || only for particles where the left side is false, like in C).

    Values with units must always be given with units (except for a plain 0,
    as in "x > 0"): meV, eV, keV, MeV,
    GeV, TeV (energy), ns, us, ms, s (time), Aa, nm, um, mm, cm, m, km
    (length, also for wavelengths), as in "ekin < 25meV", "wavelength >
    0.18nm" or "x^2 + y^2 < 4cm^2". The units deg and rad can be used for
    angles (which are otherwise in radians), as in "acos(uz) < 10deg".
    Expressions with missing or inconsistent units, like "x < 2" or "x <
    1meV", are rejected.
    """
    def __init__( self, expression ):
        self._expr = expression
        self._tree = _expr_parse(expression)
        _expr_check(self._tree, expression)
        self(_EmptyBlock())#check units etc.
    @property
    def expression( self ):
        return self._expr
    def __call__( self, block ):
        """Return boolean array selecting particles in the block"""
        res = np.asarray(_ExprEvaluator(block,self._expr)(self._tree).v)
        if res.dtype.kind in 'iu':
            res = res != 0#like in C, e.g. for "userflags & 0x10"
        if res.dtype != bool:
            raise MCPLError(f'Expression "{self._expr}" is not a condition'
                            ' (e.g. a comparison)')
        return np.broadcast_to(res,(len(block),))
    def __repr__( self ):
        return f'ParticleFilter({self._expr!r})'

class ParticleValue:
    """Numerical value calculated from particle fields with an expression
    (with the syntax of ParticleFilter), for instance for histograms. The
    expression must not have units, so values with units must be divided by
    a unit, as in "ekin/MeV" or "hypot(x,y)/mm". Boolean expressions (like
    "x > 0cm") give 1 for true and 0 for false. For instance:

       val = ParticleValue("ekin/meV")
       for block in mcplfile.particle_blocks:
           print( val(block) )
    """
    def __init__( self, expression ):
        self._expr = expression
        self._tree = _expr_parse(expression)
        _expr_check(self._tree, expression)
        self(_EmptyBlock())#check units etc.
    @property
    def expression( self ):
        return self._expr
    def __call__( self, block ):
        """Return array with the values for the particles in the block"""
        q = _ExprEvaluator(block,self._expr)(self._tree)
        if q.d is not None:
            u = _expr_unit_hints.get(q.d)
            if u == 'cm' and 'wavelength' in self._expr:
                u = 'Aa'
            e = self._expr.strip()
            e = e if e.isidentifier() else f'({e})'
            hint = f', e.g. {e}/{u}' if u else ''
            raise MCPLError(f'Expression "{self._expr}" has units'
                            f' ({_dimstr(q.d)}), so divide it by a unit{hint}')
        v = np.asarray(q.v)
        if v.dtype == bool:
            v = v.astype(float)
        return np.broadcast_to(v,(len(block),))
    def __repr__( self ):
        return f'ParticleValue({self._expr!r})'

class ParticleEdit:
    """Modification of particle fields given by an expression with statements
    separated by commas, which are evaluated with numpy on blocks of particles.
    For instance:

       edit = ParticleEdit("rotate_z(90deg), z += 10cm, wavelength = 1.8Aa")
       for block in mcplfile.particle_blocks:
           outfile.add_particles( block, **edit(block) )

    The statements are executed in order, so each statement sees the results
    of the previous ones. The statements are:

      * Assignments to fields, like "x = 2m*ux" or "z += 1cm" (also -=, *=,
        and /=), where the right hand sides use the syntax of ParticleFilter.
        The values must have the units of the field (e.g. a length for x).
        Assigning wavelength changes the kinetic energy of neutrons and gammas.
      * Assignments to variables (lowercase names which are not names of
        fields, units, constants or functions), which can be used in later
        statements, for instance to keep original values: "tmp = x, x = y,
        y = tmp". Variables keep the units of their values.
      * swap(a,b), which exchanges the values of two fields (or variables)
        with the same units, e.g. "swap(x,y)".
      * rotate_x(angle), rotate_y(angle), rotate_z(angle), which rotate the
        position, direction and polarisation of the particles around the
        given axis (through the origin), e.g. "rotate_y(90deg)". The rotation
        is counter-clockwise when looking from the positive axis towards the
        origin.
    """
    _assignable = tuple( f for f in _expr_fields )
    def __init__( self, expression ):
        self._expr = expression
        self._statements = []
        variables, used = set(), set()
        def check_var( name ):
            if not ( name.isidentifier() and name == name.lower() ) or (
                    name in _expr_constants or name in _expr_units
                    or name in _expr_functions or name in _edit_statements ):
                raise MCPLError(f'Can not assign to "{name}" in "{expression}"'
                                ' (fields which can be assigned are: '
                                + ', '.join(self._assignable) + ', and other'
                                ' lowercase names can be used for variables)')
        for part in self._split(expression):
            tree = _expr_parse(part, mode = 'exec')
            stmt = tree.body[0] if len(tree.body) == 1 else None
            if ( isinstance(stmt,ast.Expr) and isinstance(stmt.value,ast.Call)
                 and isinstance(stmt.value.func,ast.Name)
                 and stmt.value.func.id in _edit_statements ):
                self._statements.append(self._parse_call(stmt.value,part,variables))
                continue
            if not isinstance(stmt,(ast.Assign,ast.AugAssign)):
                raise MCPLError(f'Expected assignments like "x = 2*y" (or'
                                ' swap(..) or rotate_x/y/z(..)) in'
                                f' "{expression}"')
            target = stmt.targets if isinstance(stmt,ast.Assign) else [stmt.target]
            if len(target) != 1 or not isinstance(target[0],ast.Name):
                raise MCPLError(f'Unsupported assignment "{part}" in "{expression}"')
            name = target[0].id
            if name not in self._assignable:
                check_var(name)
                if isinstance(stmt,ast.AugAssign) and name not in variables:
                    raise MCPLError(f'Variable "{name}" used before it is'
                                    f' assigned in "{expression}"')
            if isinstance(stmt,ast.AugAssign):
                value = ast.BinOp(left = ast.Name(id = name, ctx = ast.Load()),
                                  op = stmt.op, right = stmt.value)
            else:
                value = stmt.value
            value = ast.Expression(body = value)
            _expr_check(value, expression, variables)
            used.update( n.id for n in ast.walk(value)
                         if isinstance(n,ast.Name) and n.id in variables )
            if name not in self._assignable:
                variables.add(name)
            self._statements.append( ('assign', name, value) )
        for st in self._statements:
            if st[0] == 'swap':
                used.update( n for n in st[1:] if n in variables )
        used.update(getattr(self,'_used_in_angles',()))
        mod = set()
        for st in self._statements:
            if st[0] == 'assign' and st[1] in self._assignable:
                mod.add( 'ekin' if st[1] == 'wavelength' else st[1] )
            elif st[0] == 'swap':
                mod.update( n for n in st[1:] if n in self._assignable )
            elif st[0] in _rotation_planes:
                for plane in _rotation_planes[st[0]]:
                    mod.update(plane)
        self._modified = frozenset(mod)
        unused = sorted(variables - used)
        if unused:
            raise MCPLError(f'Variable "{unused[0]}" is assigned but never used'
                            f' in "{expression}" (fields which can be assigned'
                            ' are: ' + ', '.join(self._assignable) + ')')
        self(_EmptyBlock())#check units etc.

    def _parse_call( self, call, part, variables ):
        fname = call.func.id
        if call.keywords:
            raise MCPLError(f'Unsupported syntax "{part}" in "{self._expr}"')
        if fname == 'swap':
            if len(call.args) != 2 or not all( isinstance(a,ast.Name)
                                               for a in call.args ):
                raise MCPLError(f'swap(..) takes two fields (or variables)'
                                f' as arguments, as in swap(x,y), in "{self._expr}"')
            names = [ a.id for a in call.args ]
            for n in names:
                if n not in self._assignable and n not in variables:
                    raise MCPLError(f'Can not swap "{n}" in "{self._expr}"'
                                    ' (it is not a field or variable)')
            return ( 'swap', names[0], names[1] )
        if len(call.args) != 1:
            raise MCPLError(f'{fname}(..) takes one argument (an angle) in'
                            f' "{self._expr}"')
        angle = ast.Expression(body = call.args[0])
        _expr_check(angle, self._expr, variables)
        self._used_in_angles = getattr(self,'_used_in_angles',set())
        self._used_in_angles.update( n.id for n in ast.walk(angle)
                                     if isinstance(n,ast.Name) and n.id in variables )
        return ( fname, angle )

    @staticmethod
    def _split( expr ):
        parts, depth, cur = [], 0, ''
        for c in expr:
            if c in '([':
                depth += 1
            elif c in ')]':
                depth -= 1
            if c == ',' and depth == 0:
                parts.append(cur)
                cur = ''
            else:
                cur += c
        parts.append(cur)
        parts = [ p.strip() for p in parts if p.strip() ]
        if not parts:
            raise MCPLError('Empty edit expression')
        return parts

    @property
    def expression( self ):
        return self._expr

    @property
    def modified_fields( self ):
        """Names of the fields which the edit can modify (ekin for edits of
        the wavelength)."""
        return self._modified

    def __call__( self, block ):
        """Return dictionary with new values of the modified fields, which can
        be passed as keyword arguments to MCPLOutFile.add_particles together
        with the block."""
        ev = _ExprEvaluator(block,self._expr)
        state = ev.state
        modified = set()
        n = len(block)
        for st in self._statements:
            if st[0] == 'assign':
                _, name, value = st
                q = ev(value)
                if name in self._assignable:
                    d = _expr_field_dims.get(name)
                    if q.d != d and not q.zero:
                        what = _dimstr(q.d) if q.d is None else f'value with {_dimstr(q.d)}'
                        dname = 'unitless' if d is None else f'a {_dimstr(d)}'
                        dname = dname.replace('a energy','an energy')
                        hint = _unit_hint(d) if q.d is None else ''
                        raise MCPLError(f'Can not assign {what} to {name}, which is'
                                        f' {dname}{hint}, in expression "{self._expr}"')
                    v = np.broadcast_to(np.asarray(q.v,dtype=( float if name not in
                                                               ('pdgcode','userflags')
                                                               else None )),(n,))
                    if name == 'wavelength':
                        self._set_wavelength(ev,v,modified)
                        continue
                    q = _Q(v,d)
                    modified.add(name)
                state[name] = q
            elif st[0] == 'swap':
                _, a, b = st
                qa, qb = ev.name(a), ev.name(b)
                ev.same(qa,qb,'swap(..)')
                state[a], state[b] = qb, qa
                modified.update( e for e in (a,b) if e in self._assignable )
            else:
                fname, angle = st
                qa = ev(angle)
                if qa.d is not None:
                    ev.error(f'{fname}(..) requires an angle (e.g. 90deg), not'
                             f' {_dimstr(qa.d)}')
                c, s = np.cos(qa.v), np.sin(qa.v)
                for a, b in _rotation_planes[fname]:
                    va, vb = ev.name(a), ev.name(b)
                    state[a] = _Q(c * va.v - s * vb.v, va.d)
                    state[b] = _Q(s * va.v + c * vb.v, vb.d)
                    modified.update((a,b))
        res = {}
        for name in sorted(modified):
            v = np.asarray(state[name].v)
            if name in ('pdgcode','userflags') and v.dtype.kind not in 'iub':
                vi = np.round(v).astype(np.int64)
                if not np.all( vi == v ):
                    raise MCPLError(f'Non-integer values assigned to {name}')
                v = vi
            res[name] = np.broadcast_to(v,(n,))
        return res

    def _set_wavelength( self, ev, wl, modified ):
        """Set kinetic energy from wavelength (given in cm)"""
        pdg = np.asarray(ev.name('pdgcode').v)
        if not np.all( np.isin( pdg, (2112,22) ) ):
            raise MCPLError('wavelength can only be assigned to neutrons'
                            ' (pdgcode 2112) and gammas (pdgcode 22)'
                            f' in expression "{self._expr}"')
        ev.state['ekin'] = _Q(np.broadcast_to(ekin_from_wavelength(wl/_expr_wl_unit,pdg),
                                              wl.shape),_dim_E)
        modified.add('ekin')

    def __repr__( self ):
        return f'ParticleEdit({self._expr!r})'

def _as_filter(select):
    if isinstance(select,str):
        return ParticleFilter(select)
    return select

def _as_edit(edit):
    if isinstance(edit,str):
        return ParticleEdit(edit)
    return edit
