#!/bin/bash

docker build -t bigchaindb/nginx_3scale:2.0.0-alpha .

docker push bigchaindb/nginx_3scale:2.0.0-alpha
