#!/usr/bin/env bash

set -e

if [ -z "$1" ]; then
    echo "Missing PAAS space argument"
    echo "  deploy.sh staging|production"
    exit 1
fi

PAAS_SPACE=$1
wget -q -O - https://packages.cloudfoundry.org/debian/cli.cloudfoundry.org.key | sudo apt-key add -
echo "deb http://packages.cloudfoundry.org/debian stable main" | sudo tee /etc/apt/sources.list.d/cloudfoundry-cli.list
sudo apt-get update && sudo apt-get install cf-cli

cf login -u $PAAS_USER -p $PAAS_PASSWORD -a https://api.cloud.service.gov.uk -o gds-performance-platform -s $PAAS_SPACE

# bind services
cf bind-service $PAAS_SERVICE redis-poc

# set environmental variables
cf set-env $PAAS_SERVICE ENVIRONMENT $PAAS_SPACE
cf set-env $PAAS_SERVICE SECRET_KEY $APP_SECRET_KEY
cf set-env $PAAS_SERVICE BACKDROP_HOST $APP_BACKDROP_HOST
cf set-env $PAAS_SERVICE ADMIN_HOST https://$PAAS_SERVICE-$PAAS_SPACE.cloudapps.digital
cf set-env $PAAS_SERVICE STAGECRAFT_HOST https://stagecraft-$PAAS_SPACE.cloudapps.digital
cf set-env $PAAS_SERVICE SIGNON_BASE_URL $APP_SIGNON_BASE_URL
cf set-env $PAAS_SERVICE SIGNON_OAUTH_ID $APP_SIGNON_OAUTH_ID
cf set-env $PAAS_SERVICE SIGNON_OAUTH_SECRET $APP_SIGNON_OAUTH_SECRET

# deploy apps
cf push $PAAS_SERVICE

# create and map routes
cf map-route $PAAS_SERVICE cloudapps.digital --hostname $PAAS_SERVICE-$PAAS_SPACE