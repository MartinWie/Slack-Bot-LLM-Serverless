#!/bin/bash

# Run pytest
pytest

# Check if pytest was successful
if [ $? -eq 0 ]
then
    echo "Pytest passed, executing git push"
    git push
else
    echo "Pytest failed, not executing git push"
fi
