# Import data
import time
import numpy as np
import plotly.io as io

# Define frames
import plotly.graph_objects as go

### read the volume
volume = np.load("realizations.npy")[0]
#### set the color scale
colorscales = [[0,'white'],[0.1, 'red'], [0.2,'blue'],[0.3,'green'],[0.4,'darkgoldenrod'], [0.5, 'lightgreen'], [0.6,'yellow'],[0.7,'black']]

####### creating slices for z axis

nb_frames0 = volume.shape[2]

fig0 = go.Figure(frames=[go.Frame(data=go.Surface(
    z=(k) * np.ones(volume[:,:,k].shape),
    surfacecolor=volume[:,:,k],
    cmin=1, cmax=13,
    colorscale=colorscales,
    opacityscale=[[0, 0], [1/13, 1], [1, 1]]),
    name=str(k) # you need to name the frame for the animation to behave properly
    )
    for k in range(nb_frames0)])

# Add data to be displayed before animation starts
fig0.add_trace(go.Surface(
    z=0 * np.ones(volume[:,:,0].shape),
    surfacecolor=volume[:,:,0],
    colorscale=colorscales,
    cmin=1, cmax=13,
    #colorbar=dict(thickness=20, ticklen=4)
    ))

def frame_args(duration):
    return {
            "frame": {"duration": duration},
            "mode": "immediate",
            "fromcurrent": True,
            "transition": {"duration": duration, "easing": "linear"},
        }
#create slider
sliders = [
            {
                "pad": {"b": 10, "t": 20},
                "len": 0.9,
                "x": 0.1,
                "y": 0,
                "currentvalue": {
                        "offset": 20,
                        "xanchor": "center",
                        "font": {
                          "color": '#888',
                          "size": 15
                        }
                      },
                "font": {"color": 'white'},
                "steps": [
                    {
                        "args": [[f.name], frame_args(0)],
                        "label": str(k),
                        "method": "animate",
                    }
                    for k, f in enumerate(fig0.frames)
                ],
            }
        ]

# Layout
fig0.update_layout(
         title="slice z",
         scene = dict(
            aspectratio=dict(x=1, y=1, z=1),
            xaxis = dict(visible=False),
            yaxis = dict(visible=False),
            zaxis=dict(visible=False),
            camera = dict(
                eye=dict(x=0, y=0.5, z=2.0)
            )
         ),
         updatemenus = [
            {
                "buttons": [
                    {
                        "args": [None, frame_args(50)],
                        "label": "&#9654;", # play symbol
                        "method": "animate",
                    },
                    {
                        "args": [[None], frame_args(0)],
                        "label": "&#9724;", # pause symbol
                        "method": "animate",
                    },
                ],
                "direction": "left",
                "pad": {"r": 10, "t": 70},
                "type": "buttons",
                "x": 0.1,
                "y": 0,
            }
         ],
         sliders=sliders
)

####### creating slice for y axis

nb_frames = volume.shape[1]

fig1 = go.Figure(frames=[go.Frame(data=go.Surface(

    z=(k) * np.ones(volume[:,k,:].shape),
    surfacecolor=volume[:,k,:],
    cmin=1, cmax=13,
    colorscale=colorscales,
    opacityscale=[[0, 0], [1/13, 1], [1, 1]]),
    name=str(k) # you need to name the frame for the animation to behave properly
    )
    for k in range(nb_frames)])

# Add data to be displayed before animation starts
fig1.add_trace(go.Surface(
    z=0 * np.ones(volume[:,0,:].shape),
    surfacecolor=volume[:,0,:],
    colorscale=colorscales,
    cmin=1, cmax=13,
    #colorbar=dict(thickness=20, ticklen=4)
    ))

def frame_args(duration):
    return {
            "frame": {"duration": duration},
            "mode": "immediate",
            "fromcurrent": True,
            "transition": {"duration": duration, "easing": "linear"},
        }
# create slider
sliders = [
            {
                "pad": {"b": 10, "t": 20},
                "len": 1.0,
                "x": 0.1,
                "y": 0,
                "currentvalue": {
                        "offset": 20,
                        "xanchor": "center",
                        "font": {
                          "color": '#888',
                          "size": 15
                        }
                      },
                "font": {"color": 'white'},
                "steps": [
                    {
                        "args": [[f.name], frame_args(0)],
                        "label": str(k),
                        "method": "animate",
                    }
                    for k, f in enumerate(fig1.frames)
                ],
            }
        ]

# Layout
fig1.update_layout(
         title="slice y",
         scene = dict(
            aspectratio=dict(x=1, y=1, z=1),
            xaxis = dict(visible=False),
            yaxis = dict(visible=False),
            zaxis=dict(visible=False),
            camera = dict(
                eye=dict(x=0, y=0.5, z=2.0)
            )
         ),
         updatemenus = [
            {
                "buttons": [
                    {
                        "args": [None, frame_args(50)],
                        "label": "&#9654;", # play symbol
                        "method": "animate",
                    },
                    {
                        "args": [[None], frame_args(0)],
                        "label": "&#9724;", # pause symbol
                        "method": "animate",
                    },
                ],
                "direction": "left",
                "pad": {"r": 10, "t": 70},
                "type": "buttons",
                "x": 0.1,
                "y": 0,
            }
         ],
         sliders=sliders
)

# store in the html 2 separated figures in a row (not as subplot)
with open('dataVisualization.html', 'w', encoding="utf-8") as f:
    f.writelines(io.to_html(fig0, include_plotlyjs='cnd', full_html=True))
    f.writelines(io.to_html(fig1, include_plotlyjs='cnd', full_html=True))
