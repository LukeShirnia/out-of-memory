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
        # Broken into two parts.
        # First part: Run nearly all tests on a collection of python versions
        # Second part: Run system tests on different distrubutions

        # Part 1
        build_images
        versions=("python27" "python36" "python310")
        for version in "${versions[@]}"
        do
            echo "Running $COMMAND in $version"
            docker compose run --rm $version $COMMAND -v --ignore=tests/test_system.py
        done

        # Part 2
        # Run system tests
        distributions=("amazonlinux" "centos7")
        for distro in "${distributions[@]}"
        do
            echo "Running $COMMAND in $distro"
            docker compose run --rm $distro $COMMAND -v tests/test_system.py -p no:cacheprovider
        done
        ;;
    black|isort)
        build_images
        # If black or isort, we only need to run in one version of python
        version="python310"
        echo "Running $COMMAND in $version"
        docker compose run --rm $version $COMMAND /app
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
