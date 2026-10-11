
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
    return 'Generate reference documentation of the Python API'

def main( parser ):
    parser.init( """Generate the reference documentation of the public Python
    API of the mcpl package (from its docstrings), as Markdown which works both
    with the Jekyll website and with Sphinx (MyST). Prints it, or writes it to
    a file.""" )
    parser.add_argument( '-o','--output', metavar='FILE',
                         help='Write the documentation to FILE.' )
    parser.add_argument( '--jekyll', action='store_true',
                         help="""Add front matter for the page of the Jekyll
                         website (title, navigation title and weight).""" )
    parser.add_argument( '--check', metavar='FILE',
                         help="""Instead of writing, check that FILE has the
                         current documentation (with --jekyll if FILE has front
                         matter), and exit with an error if not.""" )
    parser.add_argument( '--strict', action='store_true',
                         help="""Fail if any public object of the API has no
                         docstring.""" )
    args = parser.parse_args()
    from .pyapidoc import generate
    fm = None
    if args.jekyll:
        fm = [ 'title: Python API reference', 'navtitle: Python (API)',
               'weight: 2', 'underconstruction: false' ]
    #(note for the Jekyll website, which still documents the latest release,
    #and a table of contents with sections, classes and functions like on the
    #other pages, made by kramdown):
    note = ( '{% include nextrelease.html msg="This page describes the Python'
             ' API of the next MCPL release." %}\n\n'
             '{::options toc_levels="2..3" /}\n\n'
             '- two magic lines for toc\n{:toc}' ) if args.jekyll else None
    text = generate( front_matter = fm, strict = args.strict, note = note )
    import pathlib
    if args.check:
        current = pathlib.Path(args.check).read_text(encoding='utf-8')
        if current != text:
            raise SystemExit(f'Error: {args.check} is not up to date (run'
                             ' mcpldevtool pyapi to update it)')
        print(f'{args.check} is up to date')
        return
    if args.output:
        pathlib.Path(args.output).write_text(text,encoding='utf-8')
        print(f'Wrote {args.output}')
    else:
        print(text)
