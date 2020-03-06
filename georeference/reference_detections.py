"""
Example script that georeference detections done on an image where the
georeference was lost during the upload to Picterra
"""
import json
import gdal
from osgeo import osr

# Modify these two lines
# The filename of the .geojson containing the detection (downloaded from
# Picterra)
detections_fname = 'coconut_nongeo_06-03-20_1520.geojson'
# The filename of the original .tif file that was uploaded to Picterra
raster_fname = 'coconut.tif'

def nongeo_to_geo(nongeo_polygon, ds):
    """
    Args:
        polygon: A GeoJSON Polygon Geometry
    """
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(3857)
    wgs84_srs = osr.SpatialReference()
    wgs84_srs.ImportFromEPSG(4326)
    trf_to_pixel = osr.CoordinateTransformation(wgs84_srs, srs)

    ds_srs = osr.SpatialReference(wkt=ds.GetProjection())
    pixel_to_ds = osr.CoordinateTransformation(ds_srs, wgs84_srs)
    geot = ds.GetGeoTransform()

    out_polygon = {
        'type': 'Polygon',
        'coordinates': []
    }
    for ring in nongeo_polygon['coordinates']:
        out_ring = []
        for coord in ring:
            # Transform from nongeo to pixel
            x_geo, y_geo, _ = trf_to_pixel.TransformPoint(coord[0], coord[1])
            x = x_geo / 0.1
            y = y_geo / -0.1

            # Transform from pixel on ds to geo
            x += 0.5
            y += 0.5
            x_geo = geot[0] + x * geot[1] + y * geot[2]
            y_geo = geot[3] + x * geot[4] + y * geot[5]
            lng, lat, _ = pixel_to_ds.TransformPoint(x_geo, y_geo)

            out_ring.append((lng, lat))
        out_polygon['coordinates'].append(out_ring)
    return out_polygon

with open(detections_fname) as f:
    fc = json.load(f)

ds = gdal.Open(raster_fname)
assert ds is not None
out_fc = {
    'type': 'FeatureCollection',
    'features': []
}
for feature in fc['features']:
    poly = nongeo_to_geo(feature['geometry'], ds)
    out_fc['features'].append({
        'type': 'Feature',
        'geometry': poly
    })

with open('output.geojson', 'w') as f:
    json.dump(out_fc, f)
