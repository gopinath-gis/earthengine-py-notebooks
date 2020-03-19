# %%
"""
<table class="ee-notebook-buttons" align="left">
    <td><a target="_blank"  href="https://github.com/giswqs/earthengine-py-notebooks/tree/master/Tutorials/Keiko/glad_alert.ipynb"><img width=32px src="https://www.tensorflow.org/images/GitHub-Mark-32px.png" /> View source on GitHub</a></td>
    <td><a target="_blank"  href="https://nbviewer.jupyter.org/github/giswqs/earthengine-py-notebooks/blob/master/Tutorials/Keiko/glad_alert.ipynb"><img width=26px src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Jupyter_logo.svg/883px-Jupyter_logo.svg.png" />Notebook Viewer</a></td>
    <td><a target="_blank"  href="https://mybinder.org/v2/gh/giswqs/earthengine-py-notebooks/master?filepath=Tutorials/Keiko/glad_alert.ipynb"><img width=58px src="https://mybinder.org/static/images/logo_social.png" />Run in binder</a></td>
    <td><a target="_blank"  href="https://colab.research.google.com/github/giswqs/earthengine-py-notebooks/blob/master/Tutorials/Keiko/glad_alert.ipynb"><img src="https://www.tensorflow.org/images/colab_logo_32px.png" /> Run in Google Colab</a></td>
</table>
"""

# %%
"""
## Install Earth Engine API and geemap
Install the [Earth Engine Python API](https://developers.google.com/earth-engine/python_install) and [geemap](https://github.com/giswqs/geemap). The **geemap** Python package is built upon the [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet) and [folium](https://github.com/python-visualization/folium) packages and implements several methods for interacting with Earth Engine data layers, such as `Map.addLayer()`, `Map.setCenter()`, and `Map.centerObject()`.
The following script checks if the geemap package has been installed. If not, it will install geemap, which automatically installs its [dependencies](https://github.com/giswqs/geemap#dependencies), including earthengine-api, folium, and ipyleaflet.

**Important note**: A key difference between folium and ipyleaflet is that ipyleaflet is built upon ipywidgets and allows bidirectional communication between the front-end and the backend enabling the use of the map to capture user input, while folium is meant for displaying static data only ([source](https://blog.jupyter.org/interactive-gis-in-jupyter-with-ipyleaflet-52f9657fa7a)). Note that [Google Colab](https://colab.research.google.com/) currently does not support ipyleaflet ([source](https://github.com/googlecolab/colabtools/issues/60#issuecomment-596225619)). Therefore, if you are using geemap with Google Colab, you should use [`import geemap.eefolium`](https://github.com/giswqs/geemap/blob/master/geemap/eefolium.py). If you are using geemap with [binder](https://mybinder.org/) or a local Jupyter notebook server, you can use [`import geemap`](https://github.com/giswqs/geemap/blob/master/geemap/geemap.py), which provides more functionalities for capturing user input (e.g., mouse-clicking and moving).
"""

# %%
# Installs geemap package
import subprocess

try:
    import geemap
except ImportError:
    print('geemap package not installed. Installing ...')
    subprocess.check_call(["python", '-m', 'pip', 'install', 'geemap'])

# Checks whether this notebook is running on Google Colab
try:
    import google.colab
    import geemap.eefolium as emap
except:
    import geemap as emap

# Authenticates and initializes Earth Engine
import ee

try:
    ee.Initialize()
except Exception as e:
    ee.Authenticate()
    ee.Initialize()  

# %%
"""
## Create an interactive map 
The default basemap is `Google Satellite`. [Additional basemaps](https://github.com/giswqs/geemap/blob/master/geemap/geemap.py#L13) can be added using the `Map.add_basemap()` function. 
"""

# %%
Map = emap.Map(center=[40,-100], zoom=4)
Map.add_basemap('ROADMAP') # Add Google Map
Map

# %%
"""
## Add Earth Engine Python script 
"""

# %%
# Add Earth Engine dataset
# Credits to: Keiko Nomura, Senior Analyst, Space Intelligence Ltd
# Source: https://medium.com/google-earth/10-tips-for-becoming-an-earth-engine-expert-b11aad9e598b
# GEE JS: https://code.earthengine.google.com/?scriptPath=users%2Fnkeikon%2Fmedium%3Afire_australia 

geometry = ee.Geometry.Polygon(
        [[[153.11338711694282, -28.12778417421283],
          [153.11338711694282, -28.189835226562256],
          [153.18943310693305, -28.189835226562256],
          [153.18943310693305, -28.12778417421283]]])
Map.centerObject(ee.FeatureCollection(geometry), 14)

imageDec = ee.Image('COPERNICUS/S2_SR/20191202T235239_20191202T235239_T56JNP')
Map.addLayer(imageDec, {
  'bands': ['B4', 'B3', 'B2'],
  'min': 0,
  'max': 1800
}, 'True colours (Dec 2019)')
Map.addLayer(imageDec, {
  'bands': ['B3', 'B3', 'B3'],
  'min': 0,
  'max': 1800
}, 'grey')

# GLAD Alert (tree loss alert) from the University of Maryland
UMD = ee.ImageCollection('projects/glad/alert/UpdResult')
print(UMD)

# conf19 is 2019 alert 3 means multiple alerts
ASIAalert = ee.Image('projects/glad/alert/UpdResult/01_01_ASIA') \
  .select(['conf19']).eq(3)

# Turn loss pixels into True colours and increase the green strength ('before' image)
imageLoss = imageDec.multiply(ASIAalert)
imageLoss_vis = imageLoss.selfMask().visualize(**{
  'bands': ['B4', 'B3', 'B2'],
  'min': 0,
  'max': 1800
})
Map.addLayer(imageLoss_vis, {
  'gamma': 0.6
}, '2019 loss alert pixels in True colours')

# It is still hard to see the loss area. You can circle them in red
# Scale the results in nominal value based on to the dataset's projection to display on the map
# Reprojecting with a specified scale ensures that pixel area does not change with zoom
buffered = ASIAalert.focal_max(50, 'circle', 'meters', 1)
bufferOnly = ASIAalert.add(buffered).eq(1)
prj = ASIAalert.projection()
scale = prj.nominalScale()
bufferScaled = bufferOnly.selfMask().reproject(prj.atScale(scale))
Map.addLayer(bufferScaled, {
  'palette': 'red'
}, 'highlight the loss alert pixels')

# Create a grey background for mosaic
noAlert = imageDec.multiply(ASIAalert.eq(0))
grey = noAlert.multiply(bufferScaled.unmask().eq(0))

# Export the image
imageMosaic = ee.ImageCollection([
  imageLoss_vis.visualize(**{
    'gamma': 0.6
  }),
  bufferScaled.visualize(**{
    'palette': 'red'
  }),
  grey.selfMask().visualize(**{
    'bands': ['B3', 'B3', 'B3'],
    'min': 0,
    'max': 1800
  })
]).mosaic()

#Map.addLayer(imageMosaic, {}, 'export')

# Export.image.toDrive({
#   'image': imageMosaic,
#   description: 'Alert',
#   'region': geometry,
#   crs: 'EPSG:3857',
#   'scale': 10
# })


# %%
"""
## Display Earth Engine data layers 
"""

# %%
Map.addLayerControl() # This line is not needed for ipyleaflet-based Map.
Map