#!/usr/bin/env bash
if [[ "$PLAYDO_DATABASE_PATH" == data/* ]]; then
    mkdir -p data # just in case using default data/playdo.db
fi
sqlite3 "$PLAYDO_DATABASE_PATH" < schema.sql
