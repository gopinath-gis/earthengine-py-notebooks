# %%
"""
<table class="ee-notebook-buttons" align="left">
    <td><a target="_blank"  href="https://github.com/giswqs/earthengine-py-notebooks/tree/master/NAIP/ndwi_map.ipynb"><img width=32px src="https://www.tensorflow.org/images/GitHub-Mark-32px.png" /> View source on GitHub</a></td>
    <td><a target="_blank"  href="https://nbviewer.jupyter.org/github/giswqs/earthengine-py-notebooks/blob/master/NAIP/ndwi_map.ipynb"><img width=26px src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Jupyter_logo.svg/883px-Jupyter_logo.svg.png" />Notebook Viewer</a></td>
    <td><a target="_blank"  href="https://mybinder.org/v2/gh/giswqs/earthengine-py-notebooks/master?filepath=NAIP/ndwi_map.ipynb"><img width=58px src="https://mybinder.org/static/images/logo_social.png" />Run in binder</a></td>
    <td><a target="_blank"  href="https://colab.research.google.com/github/giswqs/earthengine-py-notebooks/blob/master/NAIP/ndwi_map.ipynb"><img src="https://www.tensorflow.org/images/colab_logo_32px.png" /> Run in Google Colab</a></td>
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
collection = ee.ImageCollection('USDA/NAIP/DOQQ')
fromFT = ee.FeatureCollection('ft:1CLldB-ULPyULBT2mxoRNv7enckVF0gCQoD2oH7XP')
polys = fromFT.geometry()
# polys = ee.Geometry.Polygon(
#         [[[-99.29615020751953, 46.725459351792374],
#           [-99.2116928100586, 46.72404725733022],
#           [-99.21443939208984, 46.772037733479884],
#           [-99.30267333984375, 46.77321343419932]]])

centroid = polys.centroid()
lng, lat = centroid.getInfo()['coordinates']
print("lng = {}, lat = {}".format(lng, lat))

lng_lat = ee.Geometry.Point(lng, lat)
naip = collection.filterBounds(polys)
naip_2015 = naip.filterDate('2015-01-01', '2015-12-31')
ppr = naip_2015.mosaic()

count = naip_2015.size().getInfo()
print("Count: ", count)

# print(naip_2015.size().getInfo())
vis = {'bands': ['N', 'R', 'G']}
Map.setCenter(lng, lat, 12)
Map.addLayer(ppr,vis)
# Map.addLayer(polys)

def NDWI(image):
    """A function to compute NDWI."""
    ndwi = image.normalizedDifference(['G', 'N'])
    ndwiViz = {'min': 0, 'max': 1, 'palette': ['00FFFF', '0000FF']}
    ndwiMasked = ndwi.updateMask(ndwi.gte(0.05))
    ndwi_bin = ndwiMasked.gt(0)
    patch_size = ndwi_bin.connectedPixelCount(500, True)
    large_patches = patch_size.eq(500)
    large_patches = large_patches.updateMask(large_patches)
    opened = large_patches.focal_min(1).focal_max(1)
    return opened

ndwi_collection = naip_2015.map(NDWI)
# Map.addLayer(ndwi_collection)
# print(ndwi_collection.getInfo())

# downConfig = {'scale': 10, "maxPixels": 1.0E13, 'driveFolder': 'image'}  # scale means resolution.
# img_lst = ndwi_collection.toList(100)
#
# taskParams = {
#     'driveFolder': 'image',
#     'driveFileNamePrefix': 'ndwi',
#     'fileFormat': 'KML'
# }
#
# for i in range(0, count):
#     image = ee.Image(img_lst.get(i))
#     name = image.get('system:index').getInfo()
#     print(name)
#     # task = ee.batch.Export.image(image, "ndwi2-" + name, downConfig)
#     # task.start()

mosaic = ndwi_collection.mosaic().clip(polys)
fc = mosaic.reduceToVectors(eightConnected=True, maxPixels=59568116121, crs=mosaic.projection(), scale=1)
# Map.addLayer(fc)
taskParams = {
    'driveFolder': 'image',
    'driveFileNamePrefix': 'water',
    'fileFormat': 'KML'
}

count = fromFT.size().getInfo()
Map.setCenter(lng, lat, 10)

for i in range(2, 2 + count):
    watershed = fromFT.filter(ee.Filter.eq('system:index', str(i)))
    re = fc.filterBounds(watershed)
    task = ee.batch.Export.table(re, 'watershed-' + str(i), taskParams)
    task.start()
    # Map.addLayer(fc)


# lpc = fromFT.filter(ee.Filter.eq('name', 'Little Pipestem Creek'))


# %%
"""
## Display Earth Engine data layers 
"""

# %%
Map.addLayerControl() # This line is not needed for ipyleaflet-based Map.
Map