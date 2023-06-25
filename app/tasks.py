# this file will handle async computations
from rq import get_current_job
import os
import ArchPy 
import numpy as np
import geone
import geone.covModel as gcm
import os
import sys
from ArchPy.base import *
import pandas as pd
import shapely
import shutil
from shapely.geometry import Polygon, MultiPolygon, Point
import plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import app


#dictionary of units
dic_s_names_grouped = {'"Alte Seetone"':"Alte Seetone",
              "Bachschutt / Bachschuttkegel (undifferenziert)":"Hangschutt_Bachschutt",
              "Deckschicht":"SUP",
              "Hangschutt / Hanglehm (undifferenziert)":"Hangschutt_Bachschutt",
              "Interglaziale Seetone (Eemzeitliche Seetone)":"IGT",
              "Künstliche Auffüllung etc. (anthropogener Horizont, undifferenziert)":"SUP",
              "Moräne der Letzten Vergletscherung":"LGM",
              'Moräne der Vorletzten Vergletscherung ("Altmoräne")':"Altmorane",
              "Oppligen-Sand":"Oppligen-Sand",
              'Rückzugsschotter der Letzten Vergletscherung ("Felderschotter" und Äquivalente)':"LGMT",
              'Spät- bis postglaziale Schotter':"LGA",
              'Spät- bis postglaziale Stausedimente und Seeablagerungen (undifferenziert)':"LGL",
              'Spätglaziale Moräne (undifferenziert)':"LGMT",
              'Subrezente bis rezente Alluvionen (Fluss- und Bachschotter, Überschwemmungssediment, undifferenziert)':"YG",
              'Uttigen-Bümberg-Steghalde-Schotter':"Bumberg",
              'Alte Deltaschotter im Belpmoos':"Bumberg",
              'Verlandungssedimente, Sumpf, Ried':"SUP",
              'Vorletzteiszeitliche glaziolakustrische Ablagerungen und Schlammmoräne':"glacio_lac + schlamm",
              'Vorstossschotter der Letzten Vergletscherung (vorwiegend Münsingen- u. Karlsruhe-Schotter)':"Munsingen",
              'Rückzugsschotter der Vorletzten Vergletscherung, Kies-Sand-Komplex von Kleinhöchstetten':"Altmorane"}

dic_facies = {
           "OH":"others","OL":"others",'kunst':"others",'Pt':"others", 'Bl':"others","st":"others","St-Bl":"others","KA":"others",
           "S-SM":"Sand","S": "Sand","SP-SM":"Sand","SP":"Sand","SW":"Sand","S-SC":"Sand","SP-SC":"Sand","SW-SM":"Sand",
           "SM":"Clayey sand","SC":"Clayey sand","SC-SM":"Clayey sand",
           "GM":"Clayey gravel","GC":"Clayey gravel","GC-GM":"Clayey gravel",
           "G":"Gravel","G-GM":"Gravel","GW-GM":"Gravel","GP-GM":"Gravel","GP":"Gravel","GW":"Gravel","GP-GC":"Gravel","G-GC":"Gravel","GP-gM":"Gravel","GW-GC":"Gravel",
           "ML" : "Clay and silt", "CL-ML":"Clay and silt","CL":"Clay and silt","CM":"Clay and silt","CH":"Clay and silt",
           'FELS':"Bedrock"}

DATA_DIR = "app/data" # where our data is stored


def generate_visualization(volume):
    # convert to arrays
    values = volume
    (x, y, z) = volume.shape
    X, Y, Z = np.mgrid[0:x, 0:y, 0:z]
    X, Y, Z = X.flatten(), Y.flatten(), Z.flatten()

    # identify colorscale for the figures, goes from rane 0 to 1, as 0 is not going to be shown, the color doesn't matter but it is nice to point it out
    colorscales = [[0,'black'], [0.2,'yellow'], [0.4,'lightgreen'] , [0.6,'darkgoldenrod'], [0.8,'green'], [1,'blue']]

    ####### computation for whole figure, iso surface can plot contour of volume
    fig = go.Figure(data=go.Isosurface(
            x=Z,
            y=Y,
            z=-X,
            value=values.flatten(),
            isomin=1,  # indicate range min of "color scale" so 0 value not taken in account
            isomax=6, # indicate range max of "color scale"
            opacity=0.3, # needs to be small to see through all surfaces
            colorscale=colorscales, # assign color scale with the custom one
            #opacityscale=[[0, 0], [1/13, 1], [1, 1]], #input range to remove the 0 as colorization , redundancy with isomin, but safety measure
            caps=dict(x_show=False, y_show=False), # remove the color coded surfaces on the sides of the visualisation domain for clearer visualization
            #surface_count=5, # needs to be a large number for good volume rendering -> we reduced to get better performance
            showscale=False #remove colorbar
            ))

    fig.update_layout(autosize=True, margin=dict(l=20, r=20, t=20, b=20))


    ####### creating slices for z axis
    nb_frames0 = values.shape[2]

    fig0 = go.Figure(frames=[go.Frame(data=go.Surface(
        z=(k) * np.ones(values[:,:,k].shape),   # create surface based on k-th element of z slice, because animation or slider based
        surfacecolor=values[:,:,k],     #create color code surface based on k-th element of z slice, because animation or slider based
        cmin=1, cmax=6,     #for surface, indicate the minimum color and maximum, like iso for volume
        colorscale=colorscales, # assign color scale with the custom one
        opacityscale=[[0, 0], [1/13, 1], [1, 1]], #input range to remove the 0 as colorization , redundancy with isomin, but safety measure
        ),  
        name=str(k), # you need to name the frame for the animation to behave properly
        #showscale=False #remove colorbar
        )
        for k in range(nb_frames0)])

    # Add data to be displayed before animation starts
    fig0.add_trace(go.Surface(
        z=0 * np.ones(values[:,:,0].shape), # create surface based on first element of z slice
        surfacecolor=values[:,:,0], #create color code surface based on first element of z slice
        colorscale=colorscales, # assign color scale with the custom one
        cmin=1, cmax=6,    #for surface, indicate the minimum color and maximum, like iso for volume
        #colorbar=dict(thickness=20, ticklen=4)
        showscale=False #remove colorbar
        ))

    # define the animation transition, will also be used for the second slider
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
                    "currentvalue": {           # put current value as number above the slider force color font
                            "offset": 20,
                            "xanchor": "center",
                            "font": {
                              "color": '#888',
                              "size": 15
                            }
                          },
                    "font": {"color": 'white'}, # remove ticks because too many labels, put is same as the background
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
                aspectratio=dict(x=1, y=1, z=1),    # make the 3 axis of same ratio and step aspect
                xaxis = dict(visible=False),    # remove grid and axis label of x
                yaxis = dict(visible=False),    # remove grid and axis label of y
                zaxis=dict(visible=False),      # remove grid and axis label of z
                camera = dict(      # set camera layout to top view to better read the frame, rotate based on y to have the good orientation
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

    nb_frames = values.shape[1]

    fig1 = go.Figure(frames=[go.Frame(data=go.Surface(
        z=(k) * np.ones(values[:,k,:].shape),   # create surface based on k-th element of y slice, because animation or slider based
        surfacecolor=values[:,k,:],         #create color code surface based on k-th element of y slice, because animation or slider based
        cmin=1, cmax=6,     #for surface, indicate the minimum color and maximum, like iso for volume
        colorscale=colorscales, # assign color scale with the custom one
        opacityscale=[[0, 0], [1/13, 1], [1, 1]],  #input range to remove the 0 as colorization , redundancy with isomin, but safety measure
        ),
        name=str(k), # you need to name the frame for the animation to behave properly
        #showscale=False #remove colorbar
        )
        for k in range(nb_frames)])

    # Add data to be displayed before animation starts
    fig1.add_trace(go.Surface(
        z=0 * np.ones(values[:,0,:].shape), # create surface based on first element of y slice
        surfacecolor=values[:,0,:],  #create color code surface based on first element of y slice
        colorscale=colorscales, # assign color scale with the custom one
        cmin=1, cmax=6,    #for surface, indicate the minimum color and maximum, like iso for volume
        #colorbar=dict(thickness=20, ticklen=4)
        showscale=False #remove colorbar
        ))

    # create slider for figure 1
    sliders = [
                {
                    "pad": {"b": 10, "t": 20},
                    "len": 1.0,
                    "x": 0.1,
                    "y": 0,
                    "currentvalue": {           # put current value as number above the slider force color font
                            "offset": 20,
                            "xanchor": "center",
                            "font": {
                              "color": '#888',
                              "size": 15
                            }
                          },
                    "font": {"color": 'white'}, # remove ticks because too many labels, put is same as the background
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

    # Layout for figure 1
    fig1.update_layout(
             title="slice y",
             scene = dict(
                aspectratio=dict(x=1, y=1, z=1),    # make the 3 axis of same ratio and step aspect
                xaxis = dict(visible=False),    # remove grid and axis label of x
                yaxis = dict(visible=False),    # remove grid and axis label of y
                zaxis=dict(visible=False),      # remove grid and axis label of z
                camera = dict(      # set camera layout to top view to better read the frame, rotate based on y to have the good orientation
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

    html = plotly.io.to_html(fig, include_plotlyjs='cnd', full_html=True)
    html += plotly.io.to_html(fig0, include_plotlyjs='cnd', full_html=True)
    html += plotly.io.to_html(fig1, include_plotlyjs='cnd', full_html=True)

    return html


def preprocess_data():

    # paths
    ws = DATA_DIR
    bhs_path = os.path.join(ws, "all_BH.csv")
    all_layers = os.path.join(ws, "Layer_all_free.csv")
    mnt = os.path.join(ws, "MNT25.tif")
    bdrck_path = os.path.join(ws, "BEM25-2021_crop_Aar.tif")

    # load files
    poly_data = np.load(os.path.join(ws, "polygon_coord_3.npy"))  # the maximum extent
    lay = pd.read_csv(all_layers, error_bad_lines=False, sep=";", low_memory=False)
    bhs = pd.read_csv(bhs_path)

    # reload Arch_table
    T1 = ArchPy.inputs.import_project("Aar_geomodel", ws="working_dir", 
                                import_bhs=False, import_grid=False, import_results=False)  # load the yaml file
    # we have to add a working directory because archpy uses: if self.ws not in os.listdir(): os.mkdir(self.ws) instead of os.path.exists() -> bad practice...

    # create multipolygon shapely
    p1 = MultiPolygon([Polygon(p) for p in poly_data])

    # Extract bhs points
    bhs_points = []
    for i, (px, py) in enumerate(zip(bhs.BH_X_LV95, bhs.BH_Y_LV95)):
        po = shapely.geometry.Point(px, py)
        po.name = i  # set cell id as names to grid cells
        bhs_points.append(po)

    # check position, only keep points inside polygon
    l = np.array([po.name for po in bhs_points if po.intersects(p1)])

    #select bhs in zone
    bhs_sel = bhs.loc[np.array(l)]

    #select layers in zone
    lay_sel = lay[lay["BH_GEOQUAT_ID"].isin(bhs_sel["BH_GEOQUAT_ID"])] # layers selection

    # import geological database 
    db, list_bhs = load_bh_files(bhs_sel, lay_sel.reset_index(), lay_sel.reset_index(),
                              lbhs_bh_id_col="BH_GEOQUAT_ID", u_bh_id_col="BH_GEOQUAT_ID", fa_bh_id_col="BH_GEOQUAT_ID",
                              u_top_col = "LA_TOP_m",u_bot_col = "LA_BOT_m",u_ID = "LA_Lithostrati",
                              fa_top_col = "LA_TOP_m",fa_bot_col = "LA_BOT_m",fa_ID = "LA_USCS_IP_1",
                              bhx_col='BH_X_LV95', bhy_col='BH_Y_LV95', bhz_col='BH_Z_Alt_m', bh_depth_col='BH_TD_m',
                              dic_units_names = dic_s_names_grouped,
                              dic_facies_names = dic_facies, altitude = False)

    #adding boreholes
    all_boreholes = extract_bhs(db, list_bhs, T1, 
                            units_to_ignore=('Keine Angaben', 'Raintal-Deltaschotter', 'Hani-Deltaschotter', 'Fels'),
                            facies_to_ignore=('Bedrock', 'asfd'))

    # save boreholes for use
    with open(os.path.join(ws, "boreholes"), "wb") as f:
        pickle.dump(all_boreholes, f)


def AareModel(poly_data, spacing, depth, realizations):

    # paths
    ws = DATA_DIR
    bhs_path = os.path.join(ws, "all_BH.csv")
    all_layers = os.path.join(ws, "Layer_all_free.csv")
    mnt = os.path.join(ws, "MNT25.tif")
    bdrck_path = os.path.join(ws, "BEM25-2021_crop_Aar.tif")
    
    # reload Arch_table
    T1 = ArchPy.inputs.import_project("Aar_geomodel", ws="working_dir", 
                                import_bhs=False, import_grid=False, import_results=False)  # load the yaml file
    # we have to add a working directory because archpy uses: if self.ws not in os.listdir(): os.mkdir(self.ws) instead of os.path.exists() -> bad practice...

    # reload boreholes
    with open(os.path.join(ws, "boreholes"), "rb") as f:
        all_boreholes = pickle.load(f)

    # polygon
    p1 = MultiPolygon([Polygon(p) for p in poly_data])

    #grid 
    sx, sy, sz = spacing
    oz, z1 = depth
    xg = np.arange(p1.bounds[0],p1.bounds[2]+sx,sx)
    nx = len(xg)-1
    yg = np.arange(p1.bounds[1],p1.bounds[3]+sy,sy)
    ny = len(yg)-1
    zg = np.arange(oz,z1+sz,sz)
    nz = len(zg)-1
    dimensions = (nx, ny, nz)
    origin = (p1.bounds[0], p1.bounds[1], oz)
    (nreal_units, nreal_facies, nreal_prop) = realizations

    # Extract bhs points
    bhs_points = []
    for i, ibh in enumerate(all_boreholes):
        po = shapely.geometry.Point(ibh.x, ibh.y)
        po.name = i
        bhs_points.append(po) 

    #check position, only keep points inside polygon
    l = np.array([po.name for po in bhs_points if po.intersects(p1)])
    boreholes_sel = np.array(all_boreholes)[np.array(l)]

    ### remove units that doesn't appear in the data
    stratis_unique = []
    for bh in boreholes_sel:
        if bh.log_strati is not None:
            for s in bh.get_list_stratis():
                if s not in stratis_unique:
                    stratis_unique.append(s)
      
    # fix the issue with the instance of the boreholes
    for u in T1.get_all_units():
        T1.get_pile_master().remove_unit(u)
    for unit in stratis_unique:
        T1.get_pile_master().add_unit(unit)

    # create grid
    T1.add_grid(dimensions, spacing, origin, polygon=p1, top=mnt, bot=bdrck_path)
    T1.add_bh(boreholes_sel)

    # process
    T1.process_bhs()
    T1.compute_surf(nreal_units)

    return T1.get_units_domains_realizations()


def run_model(job_id, working_dir, poly_data, spacing, depth, realizations):

    print("starting")

    # beginning computation
    job =_set_progress_status(job_id, "running", True)

    #create working dir
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)

    # run model
    try:
        realizations = AareModel(poly_data, spacing, depth, realizations)

        # save model
        np.save(os.path.join(working_dir, "realizations.npy"), realizations)

        # finished
        job =_set_progress_status(job_id, "finished", True)

    except Exception as e:

        print("Exception: " + str(e))

        # finished
        job =_set_progress_status(job_id, "failed", True)


# we set the status
def _set_progress_status(job_id, status, complete):
    job = get_current_job()
    #job = Job.fetch(job_id, connection=app.redis)

    if job:
        # set status
        job.meta['status'] = status
        job.meta['complete'] = complete
        job.save_meta()

    return job

