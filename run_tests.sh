#!/bin/bash

function display_help() {
    echo "Usage: $0 [COMMAND]"
    echo "Commands:"
    echo "  pytest   - Run pytest to execute tests."
    echo "  black    - Run black for code formatting."
    echo "  isort    - Run isort to sort imports."
    echo "  help     - Display this help message."
}

function build_images(){
    echo "Building images..."
    docker compose build 2>&1 > /dev/null
}

if [ "$#" -ne 1 ]; then
    echo "Error: You must provide exactly one command."
    display_help
    exit 1
fi

COMMAND="$1"
case "$COMMAND" in
    pytest)
        build_images
        versions=("python27" "python36" "python310")
        for version in "${versions[@]}"
        do
            echo "Running $COMMAND in $version"
            docker compose run --rm $version $COMMAND -v
        done
        ;;
    black|isort)
        build_images
        # If black or isort, we only need to run in one version of python
        version="python310"
        echo "Running $COMMAND in $version"
        docker compose run --rm python310 $COMMAND /app
        ;;
    help)
        display_help
        ;;
    *)
        echo "Error: Invalid command '$COMMAND'"
        display_help
        exit 1
        ;;
esac

# Clean up
docker compose down 2&>1 > /dev/null
