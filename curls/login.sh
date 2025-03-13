#!/usr/bin/env bash

PASSWORD=testpassword123
USERNAME=test
curl -X POST "$_PLAYDO_URL"/api/login \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"$USERNAME\",
    \"password\": \"$PASSWORD\"
  }"
