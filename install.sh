#!/usr/bin/env bash
mkdir -p data
sqlite3 data/app.db < schema.sql
