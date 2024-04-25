#!/bin/bash
# Run tests in each Python environment
versions=("python27" "python36" "python310")

for version in "${versions[@]}"
do
    echo "Running tests in $version"
    docker-compose run --rm $version pytest -v
done
