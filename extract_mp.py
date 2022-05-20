"""
Extract by location
"""

import json
import logging
import os
from pathlib import Path
import shutil
import sys
import geopandas as gp

LOG_FORMAT = '[%(levelname)s] %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=LOG_FORMAT)


def load_inputs(input_path):
    inputs_desc = json.load(open(input_path))
    inputs = inputs_desc.get('inputs')
    parameters = inputs_desc.get('parameters')
    return inputs, parameters


def main():
    WORKING_DIR = os.getenv('DELAIRSTACK_PROCESS_WORKDIR')
    if not WORKING_DIR:
        raise KeyError('DELAIRSTACK_PROCESS_WORKDIR environment variable must be defined')
    WORKING_DIR = Path(WORKING_DIR).resolve()

    logging.debug('Extracting inputs and parameters...')

    # Retrieve inputs and parameters from inputs.json
    inputs, parameters = load_inputs(WORKING_DIR / 'inputs.json')

    # Get info for the inputs
    microplots = inputs.get('microplots')
    microplots_path = inputs['microplots']['components'][0]['path']
    logging.info('Microplots dataset: {name!r} (id: {id!r})'.format(
        name=microplots['name'],
        id=microplots['_id']))

    polygon = inputs.get('polygon')
    polygon_path = inputs['polygon']['components'][0]['path']
    logging.info('Polygon dataset: {name!r} (id: {id!r})'.format(
        name=polygon['name'],
        id=polygon['_id']))

    out_filename = parameters.get('output_file_name')
    out_filename_ok = out_filename+'.geojson'
    logging.info('Outfile name: {name!r} '.format(
        name=out_filename_ok))

    predicate = parameters.get('predicate')
    logging.info('Predicate: {name!r} '.format(
        name=predicate))

    # Simulate computation
    logging.info('Computing extraction by location...')
    gdf_mp = gp.read_file(microplots_path)
    gdf_poly = gp.read_file(polygon_path)
    gdf_extract = gp.sjoin(gdf_mp, gdf_poly, how='inner', predicate=predicate)

    # Create the output vector
    logging.debug('Creating the output vector')
    outpath = WORKING_DIR / out_filename_ok
    gdf_extract.to_file(outpath, driver='GeoJSON')

    # Create the outputs.json to describe the deliverable and its path
    logging.debug('Creating the outputs.json')
    output = {
        "outputs": {
            "selected_microplots": {  # Must match the name of deliverable in extract_mp.yaml
                "type": "vector",
                "format": "json",
                "name": out_filename,
                "components": [
                    {
                        "name": "vector",
                        "path": str(outpath)
                    }
                ]
            }
        },
        "version": "0.1"
    }
    with open(WORKING_DIR / 'outputs.json', 'w+') as f:
        json.dump(output, f)

    logging.info('End of processing.')


if __name__ == '__main__':
    main()
