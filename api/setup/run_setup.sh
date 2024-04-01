#!/bin/bash

python schema_to_json.py

python load_cubes_to_db.py

python load_drilldowns_to_db.py