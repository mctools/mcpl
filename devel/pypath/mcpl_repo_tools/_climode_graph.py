
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

import pathlib


def short_description():
    return 'Visualise the dependencies of the Python modules'

#Edge styles: imports outside of functions, only inside functions, and only by
#name (see MCPLTestUtils.pymoddeps):
edge_styles = ( 'solid', 'dashed', 'dotted' )

def _test_utils():
    import sys

    from .dirs import testroot
    if str(testroot / 'pypath') not in sys.path:
        sys.path.insert(0, str(testroot / 'pypath'))

def _src():
    from .dirs import reporoot
    return reporoot / 'mcpl_python' / 'src'

def load_graph():
    """The modules of the mcpl package, as {name: {imported module: kind}},
    with kind being an index in edge_styles"""
    _test_utils()
    from MCPLTestUtils.pymoddeps import import_graph
    return import_graph( _src() / 'mcpl' )

def get_scenarios():
    """The scenarios of MCPLTestUtils.pyscenarios, as (key, title, code)"""
    _test_utils()
    from MCPLTestUtils.pyscenarios import scenarios
    return scenarios

def run_scenario( code ):
    """Runs the code of a scenario with the mcpl package of the repository, and
    returns (the modules it imports, the imports as (importing module, imported
    module))"""
    import os
    import tempfile

    from .dirs import testroot
    _test_utils()
    from MCPLTestUtils.pyscenarios import prepare_files
    from MCPLTestUtils.pyscenarios import run_scenario as run
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        try:
            prepare_files(testroot / 'data')
            mods, _, imports = run(code, 'mcpl', [ _src() ])
        finally:
            os.chdir(cwd)
    return mods, imports

def remove_implied( graph ):
    """Without the imports which are implied by others of the same or a
    stronger kind (i.e. if a imports b which imports c, an import of c by a is
    not shown, unless the imports via b are only inside functions while a
    imports c outside of them, and so on)"""
    def implied( n, skip, kind ):
        seen, todo = set(), [ d for d, k in graph[n].items() if d != skip and k <= kind ]
        while todo:
            d = todo.pop()
            if d not in seen:
                seen.add(d)
                todo += [ dd for dd, k in graph[d].items() if k <= kind ]
        return skip in seen
    return { n : { d : k for d, k in deps.items() if not implied(n, d, k) }
             for n, deps in graph.items() }

def code_lines( name ):
    """Lines of the module which are not blank or comments"""
    from .dirs import reporoot
    f = reporoot / 'mcpl_python' / 'src' / 'mcpl' / f'{name}.py'
    return sum( 1 for line in f.read_text().splitlines()
                if line.strip() and not line.lstrip().startswith('#') )

def imported( graph, names, kinds ):
    """The modules imported by the named ones, also indirectly, following only
    imports of the given kinds (including the named modules)"""
    seen, todo = set(), list(names)
    while todo:
        n = todo.pop()
        if n not in seen:
            seen.add(n)
            todo += [ d for d, k in graph[n].items() if k in kinds ]
    return seen

def used_modules( graph, names ):
    """The modules loaded when the named modules are imported (with the
    package, i.e. __init__, which Python always imports first), and those which
    they import on demand (inside functions or by name), when that code runs"""
    for n in names:
        if n not in graph:
            raise SystemExit(f'no module "{n}" (modules: {", ".join(sorted(graph))})')
    loaded = imported( graph, [ '__init__', *names ], ( 0, ) )
    on_demand = { d for n in names for d, k in graph[n].items() if k != 0 }
    return loaded, imported( graph, on_demand, ( 0, 1, 2 ) ) - loaded

def graph_to_dot( graph, sizes, area, loaded, on_demand, used_imports = (), title = None ):
    s = 'digraph G {\n    node [ fontsize = "12" shape=box ];\n'
    if title:
        #(the lines left aligned, at the top):
        lbl = ''.join( line.replace('\\','\\\\').replace('"','\\"') + '\\l'
                       for line in title.splitlines() )
        s += f'    labelloc=t; labeljust=l; fontsize=20; label="{lbl}";\n'
    largest = max(sizes.values()) if sizes else 1
    for n in sorted(graph):
        public = not n.startswith('_') or n in ( '__init__', '__main__' )
        color = 'red' if public else 'black'
        if loaded is not None and n not in loaded | on_demand:
            color = 'pink' if public else 'grey'
        lbl = n if sizes is None else f'{n}\\n{sizes[n]}'
        opts = f'label="{lbl}" color="{color}" fontcolor="{color}"'
        if loaded is not None and n in loaded | on_demand:
            fill = 'lightskyblue' if n in loaded else '#d4ebfc'
            opts += f' style=filled fillcolor="{fill}"'
        if area:
            #(the area of the box proportional to the lines of code, and the
            #font size growing with it):
            r = ( sizes[n] / largest ) ** 0.5
            w = 3.0 * r
            opts += f' width={max(w,0.6):.2f} height={max(0.5*w,0.4):.2f} fontsize={10+18*r:.1f}'
        s += f'    "{n}" [ {opts} ];\n'
    for n in sorted(graph):
        for d, kind in sorted(graph[n].items()):
            color = 'black' if ( n, d ) in used_imports else 'grey'
            s += f'    "{d}" -> "{n}" [ color="{color}" style={edge_styles[kind]} ];\n'
    return s + '}\n'

def render_dot( dot_str, fmt ):
    import pathlib
    import shutil
    import subprocess
    import tempfile
    if not shutil.which('dot'):
        raise SystemExit('command "dot" not found (needs the graphviz package)')
    with tempfile.TemporaryDirectory() as tmpdir:
        f1, f2, f3 = ( pathlib.Path(tmpdir) / n for n in ( 'g1.dot', 'g2.dot', f'g.{fmt}' ) )
        f1.write_text(dot_str)
        if shutil.which('unflatten'):
            #(a less wide layout, but not all installations of graphviz have it):
            subprocess.run(['unflatten','-l3','-c7',f1,'-o',f2], check = True)
        else:
            f2 = f1
        subprocess.run(['dot',f2,f'-T{fmt}',f'-o{f3}'], check = True, capture_output = True)
        return f3.read_bytes()

def display_image_data( data, fmt, stepping = False ):
    """Shows the image, and returns False if Escape was pressed (when stepping
    through several images)"""
    from io import BytesIO

    import matplotlib.image as mpimg
    import matplotlib.pyplot as plt
    fig = plt.figure()
    plt.imshow(mpimg.imread(BytesIO(data),fmt))
    plt.axis('off')
    plt.tight_layout()
    result = [ True ]
    if stepping:
        def on_key( event ):
            if event.key in ( ' ', 'right', 'n', 'escape' ):
                result[0] = event.key != 'escape'
                plt.close(fig)
        fig.canvas.mpl_connect('key_press_event', on_key)
    plt.show()
    return result[0]

def main( parser ):
    parser.init( """Visualise the dependencies of the modules of the mcpl Python
    package. An arrow from a to b means that b imports a: solid if imported
    outside of functions, dashed if only inside functions, and dotted if only
    by name (when used). Public modules are red. Imports implied by others are
    not shown, unless --all is given.""" )
    parser.add_argument( '--all', action = 'store_true',
                         help = 'Show all imports, also those implied by others.' )
    parser.add_argument( '-s', '--sloc', action = 'store_true',
                         help = 'Show the number of lines of code of each module (without blank and comment lines).' )
    parser.add_argument( '-a', '--area', action = 'store_true',
                         help = 'Make the area of each module proportional to its lines of code (implies --sloc).' )
    parser.add_argument( '-u', '--uses', metavar = 'MODULES',
                         help = ('Highlight the modules loaded when importing these modules (separated by commas,'
                                 ' e.g. _reader, _writer or _scipp), in blue, and those they import on demand,'
                                 ' when that code runs, in light blue.') )
    parser.add_argument( '-S', '--scenario', metavar = 'NAME',
                         help = ('Run a scenario of using the package (as in the pyimports test, e.g.'
                                 ' read, write or tool_hist, "list" to list them, or "all" to step through'
                                 ' all of them), and highlight the modules it imports in blue and the imports'
                                 ' which load them in black. The graph shows the scenario and its code.') )
    parser.add_argument( '-o', '--output', metavar = 'FILE',
                         help = 'Write the graph to this file (e.g. graph.png, graph.svg or graph.pdf) instead of showing it.' )
    args = parser.parse_args()

    full_graph = load_graph()
    if args.uses and args.scenario:
        parser.error('--uses and --scenario can not be combined')
    if not args.scenario:
        loaded, on_demand = None, set()
        if args.uses:
            loaded, on_demand = used_modules( full_graph, [ n for n in args.uses.split(',') if n ] )
        show( args, full_graph, loaded, on_demand )
        return
    scenarios = get_scenarios()
    keys = [ k for k, _, _ in scenarios ]
    if args.scenario not in keys + [ 'all' ]:
        raise SystemExit('Scenarios:\n' + ''.join( f'  {k:<18} {t}\n' for k, t, _ in scenarios ))
    todo = [ sc for sc in scenarios if args.scenario in ( 'all', sc[0] ) ]
    if len(todo) > 1 and not args.output:
        print('Press space, n or the right arrow (or close the window) for the next'
              ' scenario, and Escape to stop.')
    for i, ( key, title, code ) in enumerate(todo):
        loaded, used_imports = run_scenario( code )
        desc = f'Scenario {key}: {title}' + ( f' ({i+1}/{len(todo)})' if len(todo) > 1 else '' )
        desc += ''.join( f'\n    {line}' for line in code.splitlines() )
        output = args.output
        if output and len(todo) > 1:
            #(one file per scenario):
            out = pathlib.Path(output)
            output = out.with_name(f'{out.stem}_{key}{out.suffix}')
        if not show( args, full_graph, loaded, set(), used_imports, desc, output, len(todo) > 1 ):
            break

def show( args, full_graph, loaded, on_demand, used_imports = (), title = None,
          output = None, stepping = False ):
    """Draws the graph, to the output file or else in a window (then returning
    False if the user wants to stop stepping through graphs)"""
    graph = full_graph if args.all else remove_implied( full_graph )
    graph = { n : dict(deps) for n, deps in graph.items() }
    for n, d in used_imports:
        #(always showing the imports which loaded the modules):
        graph[n][d] = full_graph[n][d]
    sizes = { n : code_lines(n) for n in graph } if args.sloc or args.area else None
    dot_str = graph_to_dot( graph, sizes, args.area, loaded, on_demand, used_imports, title )
    output = output or args.output
    if output:
        out = pathlib.Path(output)
        fmt = out.suffix[1:] or 'png'
        out.write_bytes(render_dot( dot_str, fmt ))
        print(f'Wrote {out}')
        return True
    return display_image_data( render_dot( dot_str, 'png' ), 'png', stepping )
