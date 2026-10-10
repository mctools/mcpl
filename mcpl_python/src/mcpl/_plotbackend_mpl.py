
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

"""Plotting backend using matplotlib."""

__all__ = []

from ._common import _determine_version
from ._numpy import np
from ._plotbackend import PlotBackend, numbered_filenames
from .plotting import Bars, Hist2D, StepHist, Text

requirement = 'matplotlib'

def is_available():
    import importlib.util
    return importlib.util.find_spec('matplotlib') is not None

class Backend(PlotBackend):
    """Plotting with matplotlib. The mpl_backend argument can be used to select
    a matplotlib backend (e.g. 'agg')."""
    name = 'matplotlib'
    formats = ('pdf','png','svg')

    def __init__( self, mpl_backend = None ):
        import matplotlib
        if mpl_backend:
            matplotlib.use(mpl_backend)
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print()
            print("ERROR: importing matplotlib succeeded, but importing matplotlib.pyplot failed.")
            print("ERROR: This is rather unusual, an is perhaps related to issues with your chosen")
            print("ERROR: matplotlib backend, which you might have set globally in a matplotlib")
            print("ERROR: configuration file.")
            print()
            raise
        self._plt = plt

    def show( self, figures ):
        for f in figures:
            self._draw(f)
        self._plt.show()

    def save( self, figures, filename ):
        ext = self.check_format(filename)
        plt = self._plt
        if ext == 'pdf':
            from matplotlib.backends.backend_pdf import PdfPages

            with PdfPages(filename) as pdf:
                for f in figures:
                    pdf.savefig(self._draw(f))
                    plt.close()
                d = pdf.infodict()
                d['Title'] = f'Plots made with mcpl.py version {_determine_version()}'
                d['Author'] = f'mcpl.py v{_determine_version()}'
                d['Subject'] = 'mcpl plots'
                d['Keywords'] = 'mcpl'
            return [ filename ]
        fns = numbered_filenames(filename,len(figures))
        for f, fn in zip(figures,fns):
            self._draw(f).savefig(fn)
            plt.close()
        return fns

    def _draw( self, figure ):
        import matplotlib.ticker
        plt = self._plt
        big = figure.nrows * figure.ncols > 1
        fig, axs = plt.subplots(figure.nrows,figure.ncols,squeeze=False,
                                figsize=( (15,8.5) if big else (8,6) ))
        if figure.title:
            fig.suptitle(figure.title)
        axlist = list(axs.flat)
        for ax, panel in zip(axlist,figure.panels):
            self._draw_panel(fig,ax,panel)
        for ax in axlist[len(figure.panels):]:
            ax.set_visible(False)
        for ax in axlist:
            #Avoid overlapping labels on log axes spanning less than a decade:
            ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
            ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        fig.tight_layout()
        return fig

    def _draw_panel( self, fig, ax, panel ):
        import matplotlib.colors
        has_legend = False
        for i,item in enumerate(panel.items):
            if isinstance(item,StepHist):
                c = item.color if item.color is not None else i
                ax.stairs(item.values,item.edges,label=item.label,
                          linewidth=1.5,color=f'C{c%10}')
                has_legend |= item.label is not None
            elif isinstance(item,Hist2D):
                v = np.where(item.values>0,item.values,np.nan) if item.logz else item.values
                if np.isfinite(v).any():
                    im = ax.pcolormesh(item.xedges,item.yedges,np.asarray(v).T,
                                       norm=( matplotlib.colors.LogNorm()
                                              if item.logz else None ))
                    fig.colorbar(im,ax=ax)
            elif isinstance(item,Bars):
                pos = list(range(len(item.values)))
                if item.horizontal:
                    ax.barh(pos,item.values)
                    ax.set_yticks(pos)
                    ax.set_yticklabels(item.labels,fontsize='small')
                    ax.invert_yaxis()
                else:
                    ax.bar(pos,item.values,width=0.7,linewidth=0)
                    ax.set_xticks(pos)
                    ax.set_xticklabels(item.labels,fontsize='small')
            elif isinstance(item,Text):
                ax.text(0.5,0.5,item.text,ha='center',va='center',
                        transform=ax.transAxes)
        if panel.logx:
            ax.set_xscale('log')
        if panel.logy:
            ax.set_yscale('log')
        if panel.xlim:
            ax.set_xlim(*panel.xlim)
        if panel.ylim:
            ax.set_ylim(*panel.ylim)
        if panel.title:
            ax.set_title(panel.title)
        if panel.xlabel:
            ax.set_xlabel(panel.xlabel,fontsize='small')
        if panel.ylabel:
            ax.set_ylabel(panel.ylabel)
        if has_legend:
            ax.legend(fontsize='small')
        ax.grid(alpha=0.3)
