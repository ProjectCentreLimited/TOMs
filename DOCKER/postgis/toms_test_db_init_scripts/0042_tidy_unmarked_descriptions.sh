#!/bin/bash
psql -U postgres -d "TOMs_Test" -a -f "/io/test/data/0042_tidy_unmarked_descriptions.sql"
