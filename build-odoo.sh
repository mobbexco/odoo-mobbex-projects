#!/bin/bash

# Modify the values as appropriate in your installation
PLUGIN_DIRECTORY=./payment_mobbex_checkout
CONTAINER_DIRECTORY=/usr/lib/python3/dist-packages/odoo/addons
CONTAINER_NAME=odoo-python-1

echo 'Copying modules files to the installation folder...'
docker cp $PLUGIN_DIRECTORY $CONTAINER_NAME:$CONTAINER_DIRECTORY

echo 'Giving permissions...'
docker exec $CONTAINER_NAME chmod -R 777 ./

echo 'Restarting containers...'
docker restart $CONTAINER_NAME odoo-ngrok-1 odoo-db-1

echo 'DONE!!! d;)'