import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

import numpy as np

X, Y, Z = np.mgrid[-1:1:30j, -1:1:30j, -1:1:30j]
#values = np.cos(np.pi * X) * np.cos(np.pi * Z) * np.sin(np.pi * Y)

values = np.load("realizations.npy")[0]
nb_frames = values.shape[2]


fig = go.Figure(data=go.Isosurface(
    x=X.flatten(),
    y=Y.flatten(),
    z=Z.flatten(),
    value=values.flatten(),
    isomin=1,
    isomax=12,
    opacity=0.5,
    # needs to be small to see through all surfaces
    #surface_count=21,  # needs to be a large number for good volume rendering
    caps=dict(x_show=False, y_show=False),
    ))


# Initialize figure with 2 3D subplots
#fig = make_subplots(
#    rows=1, cols=3,
#    specs=[[{'type': 'volume'}, {'type': 'volume'}, {'type': 'volume'}]]
#)

#
# Generate data (dummy 3D volume)
#
volume_dummy_full = go.Volume(
    x = values[0],
    y = values[1],
    z = values[2],
    value=values.flatten(),
    cmin=-1,
    cmax=13,
    opacity=0.1,  # needs to be small to see through all surfaces
)

volume_dummy_sliced_Z = go.Volume(
    x=X.flatten(),
    y=Y.flatten(),
    z=Z.flatten(),
    value=values.flatten(),
    isomin=-0.1,
    isomax=0.8,
    opacity=0.5,  # needs to be small to see through all surfaces
    surface_count=21,  # needs to be a large number for good volume rendering
    slices_z=dict(show=True, locations=[0.4]),
    surface=dict(fill=0.1, pattern='odd'),
    caps=dict(x_show=False, y_show=False, z_show=False),  # no caps
)

volume_dummy_sliced_X = go.Volume(
    x=X.flatten(),
    y=Y.flatten(),
    z=Z.flatten(),
    value=values.flatten(),
    isomin=-0.1,
    isomax=0.8,
    opacity=0.5,  # needs to be small to see through all surfaces
    surface_count=21,  # needs to be a large number for good volume rendering
    slices_x=dict(show=True, locations=[0.4]),
    surface=dict(fill=0.1, pattern='odd'),
    caps=dict(x_show=False, y_show=False, z_show=False),  # no caps
)

#
# Add volume/surfaces to subplots
#
#fig.add_trace(
#    volume_dummy_full,
#    #row=1, col=1
#)
#fig.add_trace(
#    volume_dummy_sliced_Z,
#    row=1, col=2
#)
#fig.add_trace(
#    volume_dummy_sliced_X,
#    row=1, col=3
#)

# Event Handlers


# Write to HTML
fig.write_html("dataVisualization.html")