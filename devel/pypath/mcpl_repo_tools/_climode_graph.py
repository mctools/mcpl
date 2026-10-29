
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

def short_description():
    return 'Visualise the dependencies of the Python modules'

#Edge styles: imports outside of functions, only inside functions, and only by
#name (see MCPLTestUtils.pymoddeps):
edge_styles = ( 'solid', 'dashed', 'dotted' )

def load_graph():
    """The modules of the mcpl package, as {name: {imported module: kind}},
    with kind being an index in edge_styles"""
    import sys

    from .dirs import reporoot, testroot
    sys.path.insert(0, str(testroot / 'pypath'))
    from MCPLTestUtils.pymoddeps import package_imports
    graph = {}
    for name, imps in package_imports(reporoot / 'mcpl_python' / 'src' / 'mcpl').items():
        graph[name] = { d : kind for kind, mods in enumerate(imps[:3]) for d in mods }
    return graph

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

def graph_to_dot( graph, sizes, area, loaded, on_demand ):
    s = 'digraph G {\n    node [ fontsize = "12" shape=box ];\n'
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
            s += f'    "{d}" -> "{n}" [ color="grey" style={edge_styles[kind]} ];\n'
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

def display_image_data( data, fmt ):
    from io import BytesIO

    import matplotlib.image as mpimg
    import matplotlib.pyplot as plt
    plt.imshow(mpimg.imread(BytesIO(data),fmt))
    plt.axis('off')
    plt.tight_layout()
    plt.show()

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
    parser.add_argument( '-o', '--output', metavar = 'FILE',
                         help = 'Write the graph to this file (e.g. graph.png, graph.svg or graph.pdf) instead of showing it.' )
    args = parser.parse_args()

    import pathlib
    full_graph = load_graph()
    loaded, on_demand = None, set()
    if args.uses:
        loaded, on_demand = used_modules( full_graph, [ n for n in args.uses.split(',') if n ] )
    graph = full_graph if args.all else remove_implied( full_graph )
    sizes = { n : code_lines(n) for n in graph } if args.sloc or args.area else None
    dot_str = graph_to_dot( graph, sizes, args.area, loaded, on_demand )
    if args.output:
        out = pathlib.Path(args.output)
        fmt = out.suffix[1:] or 'png'
        out.write_bytes(render_dot( dot_str, fmt ))
        print(f'Wrote {out}')
    else:
        display_image_data( render_dot( dot_str, 'png' ), 'png' )
