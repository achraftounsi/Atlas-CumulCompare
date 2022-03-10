import collections
import datetime
import os
from subprocess import Popen, PIPE, STDOUT

import folium
import numpy as np
import pandas as pd
from branca.element import Template, MacroElement
from cartopy import crs as ccrs
from cv2 import imread
from folium.plugins import FloatImage
from folium.plugins import MeasureControl
from folium.plugins import MiniMap
from folium.raster_layers import ImageOverlay
from matplotlib import colors
from matplotlib import pyplot as plt

from tqdm import tqdm

from src.assets import build_close_locations, ppf_estimates, locations
from src.tools import map_settings, add_gif


def generate_coordinates(window_size, lat_min, lat_max, lon_min, lon_max):
    lat = [e / 100 for e in range(int(lat_max * 100), int(lat_min * 100), -(window_size))]
    lon = [e / 100 for e in range(int(lon_min * 100), int(lon_max * 100), window_size)]
    return lon, lat


def generate_utc_texts(save_path):
    # Get the name of the files
    file_names = {os.path.getmtime(os.path.join(save_path, 'img', f)): os.path.join(save_path, 'img', f) for f in
                  os.listdir(os.path.join(save_path, 'img')) if
                  os.path.isfile(os.path.join(save_path, 'img', f)) and f.endswith('png')}
    od = collections.OrderedDict(sorted(file_names.items()))
    od = [od[_key][-16:-4] for _key in list(od)]
    od = [f'{_key[8:10]}:{_key[10:]} {_key[4:6]}/{_key[6:8]}/{_key[:4]} UTC' for _key in od]
    return od


def save_figs(likelihoods, save_path, window_size):
    lat_min = 20
    lat_max = 55
    lon_min = -130
    lon_max = -60

    lon, lat = generate_coordinates(window_size, lat_min, lat_max, lon_min, lon_max)

    # Boundaries of map: [western lon, eastern lon, southern lat, northern lat]
    domain = [lon_min, lon_max, lat_min, lat_max]

    lon_ticks = [-81, -73, -64]
    lat_ticks = [36, 38, 41, 44]

    fig = plt.figure(figsize=(20, 14))
    ax = plt.axes(projection=ccrs.PlateCarree())

    map_settings(ax, lon_ticks, lat_ticks, domain)

    bar = 'rainbow'  # Color map for colorbar and plot
    max_color = 'darkred'  # Color for Rad data > 1
    # Plotting settings for AOD data
    color_map = plt.get_cmap(bar)
    color_map.set_over(max_color)

    levels = [round(e / 14, 2) * 50 for e in range(15)]
    norm = colors.BoundaryNorm(levels, len(levels))
    aod = likelihoods
    aod[aod <= 0.99] = None
    pcm = ax.contourf(lon, lat, aod, norm=norm, levels=levels, extend='both',
                      colors=('#606060', '#67627D', '#5F5B8E', '#4B67AB',
                              '#4A9BAC', '#56B864', '#91CE4E', '#D0DB45',
                              '#DBB642', '#DB9D48', '#DB7B50', '#D15F5E',
                              '#B43A66', '#93164E', '#541029'))
    fig.patch.set_visible(False)
    ax.axis('off')
    file_res = 1800

    name = os.path.join(save_path, 'Cumul.png')
    fig.savefig(name, bbox_inches='tight', dpi=file_res, pad_inches=0)


def generate_gif(save_path):
    cmd = ["convert", "-delay", '100', '-colors', '16', '-fuzz', '2%', '-loop', '0', '-dispose background',
           os.path.join(save_path, 'Cumul.png'),
           os.path.join(save_path, 'Cumul.gif')]
    cmd = ' '.join(cmd)
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
    output = p.stdout.read()
    print(output)


def generate_map(save_path):
    _url = 'https://server.arcgisonline.com/ArcGIS/rest/services/Specialty/DeLorme_World_Base_Map/MapServer/tile/{z}/{y}/{x}'

    m = folium.Map([40.749044, -73.983306],
                   # tiles='cartodbdark_matter',
                   tiles='cartodbpositron',
                   zoom_start=8,
                   min_zoom=6,
                   max_zoom=12,
                   prefer_canvas=True,
                   max_bounds=True
                   )

    #     folium.LayerControl(collapsed=False).add_to(m)

    url = (
        "MRMS.png"
    )
    FloatImage(url, bottom=80, left=5).add_to(m)

    template = """
        {% macro html(this, kwargs) %}
       <!doctype html>
    <html lang="en">
         <!doctype html>
    <html lang="en">
    <head>
            <meta charset="UTF-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Document</title>


        </head>
        <body>




      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>jQuery UI Draggable - Default functionality</title>
      <link rel="stylesheet" href="//code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">
      <script src="https://code.jquery.com/jquery-1.12.4.js"></script>
      <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>
      <script>
      $( function() {
        $( "#maplegend" ).draggable({
                        start: function (event, ui) {
                            $(this).css({
                                right: "auto",
                                top: "auto",
                                bottom: "auto"
                            });
                        }
                    });
    });
      </script>
    <div id='maplegend' class='maplegend' 
        style='position: absolute; z-index:9999;
         border-radius:0px; padding: 10px; font-size:14px; right: 21px; bottom: 20px;'>
          <span  valign="middle"; align="center"; style="background-color: transparent ; color: black;font-weight: bold; font-size: 180%; " id="txt" ></span>
    <div class='legend-scale'>
      <ul class='legend-labels'>


           <li><span valign="middle"; align="center"; style="background: rgb(255, 255, 255); color: rgb(0, 0, 0);font-weight: bold; font-size: 100%;">  Prob  </span></li>
         <li><span valign="middle"; align="center"; style="background: rgba(255, 0, 0); color: rgb(255, 255, 255);font-weight: bold; font-size: 120%;">  1  </span></li>
         <li><span valign="middle"; align="center"; style="background: rgba(225, 90, 0); color: rgb(255, 255, 255);font-weight: bold; font-size: 120%;">  0.92  </span></li>
             <li><span valign="middle"; align="center"; style="background:  rgba(234, 162, 62, 0.87); color: rgb(0, 0, 0);font-weight: bold; font-size: 120%;">  0.85  </span></li>
        <li><span valign="middle"; align="center"; style="background: rgba(255,255,0); color: rgb(0, 0, 0);font-weight: bold; font-size: 120%;">0.77</span></li>
        <li><span valign="middle"; align="center"; style="background: rgba(193, 229, 60, 0.87); color: rgb(0, 0, 0);font-weight: bold; font-size: 120%;">0.69</span></li>
        <li><span valign="middle"; align="center"; style="background: rgba(153, 220, 69, 0.87); color: rgb(0, 0, 0);font-weight: bold; font-size: 120%;">0.62</span></li>
        <li><span valign="middle"; align="center";  style="background: rgba(69, 206, 66, 0.87); color: rgb(0, 0, 0);font-weight: bold; font-size: 120%;">0.54</span></li>
        <li><span valign="middle"; align="center"; style="background: rgba(78, 194, 98, 0.87); color: rgb(0, 0, 0);font-weight: bold; font-size: 120%;">0.46</span></li>
        <li><span valign="middle"; align="center";  style="background: rgba(71, 177, 139, 0.87); color: rgb(255, 255, 255);font-weight: bold; font-size: 120%;">0.38</span></li>
        <li><span valign="middle"; align="center"; style="background: rgba(64, 160, 180, 0.87); color: rgb(255, 255, 255);font-weight: bold; font-size: 120%;">0.31</span></li>
        <li><span valign="middle"; align="center"; style="background: rgba(67, 105, 196, 0.75); color: rgb(255, 255, 255);font-weight: bold; font-size: 120%;">0.23</span></li>
        <li><span valign="middle"; align="center"; style="background: rgba(79, 87, 183, 0.58); color: rgb(255, 255, 255);font-weight: bold; font-size: 120%;">0.15</span></li>
        <li><span valign="middle"; align="center";  style="background: rgba(82, 71, 141, 0); color: rgb(255, 255, 255);font-weight: bold; font-size: 120%;">0</span></li>
      </ul>
    </div>
    </div>
    </body>
    </html>
    <style type='text/css'>
      .maplegend .legend-title {
        text-align: left;
        margin-bottom: 5px;
        font-weight: bold;
        font-size: 100%;
        }
      .maplegend .legend-scale ul {
        margin: 0;
        margin-bottom: 5px;
        padding: 0;
        float: right;
        list-style: none;
        }
      .maplegend .legend-scale ul li {
        font-size: 80%;
        list-style: none;
        margin-left: 0;
        line-height: 18px;
        margin-bottom: 2px;
        }
      .maplegend ul.legend-labels li span {
        display: block;
        float: left;
        height: 16px;
        width: 30px;
        margin-right: 5px;
        margin-left: 0;
        border: 1px solid #999;
        }
      .maplegend .legend-source {
        font-size: 80%;
        color: #777;
        clear: both;
        }
      .maplegend a {
        color: #777;
        }
    /*////*/
        body{
                    background: #000;
                }
            /*h1{ 
                text-align: center;
                font-size: 24pt;
                background-color: transparent;
                color: white;

                }*/

    </style>
        {% endmacro %}"""

    macro = MacroElement()
    macro._template = Template(template)

    m.get_root().add_child(macro)

    lat_min = 20
    lat_max = 55
    lon_min = -130
    lon_max = -60

    minimap = MiniMap(toggle_display=True, position="bottomleft")
    m.add_child(minimap)
    m.add_child(MeasureControl())

    # # read in png file to numpy array
    # data = imread('Cumul.png')
    #
    # # Overlay the image
    # m.add_children(ImageOverlay(data, opacity=0.5, bounds=[[lat_min, lon_min], [lat_max, lon_max]]))
    # folium.TileLayer(_url, attr='Tiles &copy; Esri &mdash; Copyright: &copy;2012 DeLorme', name='DeLorme').add_to(m)m.add_child(colormap)
    add_gif(m, 'Cumulation', os.path.join(save_path, 'Cumul.gif'), [[lat_min, lon_min], [lat_max, lon_max]], True)


    # os.system(f'rm *.grib2')
    # os.system(f'rm *.nc')
    print('saving map...')
    m.fit_bounds((lat_max, lon_max), (lat_min, lon_min))
    m.save(os.path.join(save_path, "index.html"))
