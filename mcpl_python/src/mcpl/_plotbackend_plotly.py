
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

"""Plotting backend using plotly (figures are shown in a web browser or saved
as HTML files, or as image files if the kaleido module is installed)."""

__all__ = []

from ._numpy import np
from ._plotbackend import PlotBackend, numbered_filenames
from .plotting import Bars, Hist2D, StepHist, Text

requirement = 'plotly'

def is_available():
    import importlib.util
    return importlib.util.find_spec('plotly') is not None

def _has_kaleido():
    import importlib.util
    return importlib.util.find_spec('kaleido') is not None

class Backend(PlotBackend):
    """Plotting with plotly."""
    name = 'plotly'

    def __init__( self ):
        self.formats = ('html','png','pdf','svg') if _has_kaleido() else ('html',)

    def show( self, figures ):
        for f in figures:
            self._draw(f).show()

    def save( self, figures, filename ):
        ext = self.check_format(filename)
        if ext == 'html':
            #All figures in one HTML file:
            parts = [ self._draw(f).to_html(full_html=False,
                                            include_plotlyjs=(i==0))
                      for i,f in enumerate(figures) ]
            import pathlib
            pathlib.Path(filename).write_text('<html><head><meta charset="utf-8"/></head><body>\n'
                                              + '\n'.join(parts) + '\n</body></html>\n')
            return [ filename ]
        fns = numbered_filenames(filename,len(figures))
        for f, fn in zip(figures,fns):
            self._draw(f).write_image(fn)
        return fns

    def _draw( self, figure ):
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        nr, nc = figure.nrows, figure.ncols
        fig = make_subplots(rows=nr,cols=nc,
                            subplot_titles=[ p.title or '' for p in figure.panels ])
        colors = fig.layout.template.layout.colorway or [ None ]
        for i,panel in enumerate(figure.panels):
            row, col = i // nc + 1, i % nc + 1
            self._draw_panel(go,fig,panel,row,col,colors)
        if figure.title:
            fig.update_layout(title_text=figure.title.replace('\n','<br>'))
        big = nr * nc > 1
        fig.update_layout(height=( 850 if big else 550 ),
                          width=( 1500 if big else 800 ))
        return fig

    def _draw_panel( self, go, fig, panel, row, col, colors ):
        import math

        for i,item in enumerate(panel.items):
            if isinstance(item,StepHist):
                c = item.color if item.color is not None else i
                v = np.asarray(item.values,dtype=float)
                y = np.append(v,v[-1:]) if len(v) else v
                if panel.logy:
                    y = np.where(y>0,y,np.nan)
                fig.add_trace(go.Scatter(x=item.edges,y=y,mode='lines',
                                         line_shape='hv',name=item.label or '',
                                         showlegend=item.label is not None,
                                         line={'color': colors[c%len(colors)]}),
                              row=row,col=col)
            elif isinstance(item,Hist2D):
                v = np.asarray(item.values,dtype=float).T
                if item.logz:
                    with np.errstate(divide='ignore'):
                        v = np.where(v>0,np.log10(v),np.nan)
                xc = 0.5*(np.asarray(item.xedges[1:])+np.asarray(item.xedges[:-1]))
                yc = 0.5*(np.asarray(item.yedges[1:])+np.asarray(item.yedges[:-1]))
                fig.add_trace(go.Heatmap(x=xc,y=yc,z=v,showscale=True,
                                         colorbar={'title': 'log10' if item.logz else ''}),
                              row=row,col=col)
            elif isinstance(item,Bars):
                if item.horizontal:
                    fig.add_trace(go.Bar(x=list(item.values),y=list(item.labels),
                                         orientation='h',showlegend=False),
                                  row=row,col=col)
                    fig.update_yaxes(autorange='reversed',row=row,col=col)
                else:
                    fig.add_trace(go.Bar(x=list(item.labels),y=list(item.values),
                                         showlegend=False),row=row,col=col)
            elif isinstance(item,Text):
                fig.add_annotation(text=item.text,showarrow=False,row=row,col=col,
                                   xref='x domain',yref='y domain',x=0.5,y=0.5)
        if panel.logx:
            fig.update_xaxes(type='log',row=row,col=col)
        if panel.logy:
            fig.update_yaxes(type='log',row=row,col=col)
        def rng(lim,log):
            return [ math.log10(e) for e in lim ] if log else list(lim)
        if panel.xlim:
            fig.update_xaxes(range=rng(panel.xlim,panel.logx),row=row,col=col)
        if panel.ylim:
            fig.update_yaxes(range=rng(panel.ylim,panel.logy),row=row,col=col)
        if panel.xlabel:
            fig.update_xaxes(title_text=panel.xlabel.replace('\n','<br>'),row=row,col=col)
        if panel.ylabel:
            fig.update_yaxes(title_text=panel.ylabel,row=row,col=col)
