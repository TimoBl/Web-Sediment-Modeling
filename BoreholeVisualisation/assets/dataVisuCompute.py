import plotly.graph_objects as go
import plotly.express as px

import numpy as np
X, Y, Z = np.mgrid[-1:1:30j, -1:1:30j, -1:1:30j]
values =    np.cos(np.pi*X) * np.cos(np.pi*Z) * np.sin(np.pi*Y)

fig = go.Figure(data=go.Volume(
    x=X.flatten(),
    y=Y.flatten(),
    z=Z.flatten(),
    value=values.flatten(),
    isomin=-0.1,
    isomax=0.8,
    opacity=1.0, # needs to be small to see through all surfaces
    surface_count=21, # needs to be a large number for good volume rendering
    ))

fig.write_html("dataVisualization.html")