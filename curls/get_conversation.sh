#!/usr/bin/env bash

ID_TO_GET=1
curl "$_PLAYDO_URL"/api/conversations/$ID_TO_GET \
  -H "Authorization: Bearer $PLAYDO_JWT_TOKEN"
