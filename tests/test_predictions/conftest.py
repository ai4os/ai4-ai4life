"""Fixtures module for api predict. This is a configuration file designed
to prepare the tests function arguments on the test_*.py files located in
the same folder.

You can add new fixtures following the next structure:
```py
@pytest.fixture(scope="module", params=[{list of possible arguments}])
def argument_name(request):
    # You can add setup code here for your argument/fixture
    return request.param  # Argument that will be passed to the test
```
The fixture argument `request` includes the parameter generated by the
`params` list. Every test in the folder that uses the fixture will be run
at least once with each of the values inside `params` list unless specified
otherwise. The parameter is stored inside `request.param`.

When multiple fixtures are defined with more than one parameter, every tests
will run multiple times, each with one of all the possible combinations of
the generated parameters unless specified otherwise. For example, in the
following configuration:
```py
@pytest.fixture(scope="module", params=['a','b'])
def my_fixture1(request):
    return request.param

@pytest.fixture(scope="module", params=['x','y'])
def my_fixture2(request):
    return request.param
```
The for the test functions in this folder, the following combinations will
be generated:
    - Tests that use only one my_fixture1: ['a','b']
    - Tests that use only one my_fixture2: ['x','y']
    - Tests that use both: [('a','x'), ('a','y'), ('b','x'), ('b','y')]
    - Tests that use none of the fixtures: []

Be careful when using multiple fixtures with multiple parameters, as the
number of tests generated can grow exponentially.
"""

# pylint: disable=redefined-outer-name
import json
import os
import numpy as np
import pytest
from deepaas.model.v2.wrapper import UploadedFile

from bioimageio.core import load_description
from bioimageio.spec._internal.io import download

import api
import ai4life as aimodel

path = os.path.join(
    aimodel.config.MODELS_PATH, "filtered_models.json"
)
with open(path, "r") as file:
    models_data = json.load(file)
    model_names = list(models_data.keys())


#@pytest.fixture(scope="module")
def input_files(model_name):
    """Fixture to provide options dictionary for the model."""
    # Load the model
    model_name, icon = model_name.split(" ", 1)
    model = load_description(
        model_name, perform_io_checks=False
    )

    # Initialize inputs
    inputs = [d.test_tensor for d in model.inputs]
    options = {}

    for input_item in inputs:
        path = download(input_item).path
        content_type = "application/octet-stream"
        file_extension = os.path.splitext(path)[1]
        filename = os.path.basename(path).split("-")[-1]

        if input_item == inputs[0]:
            options["input_file"] = UploadedFile(
                filename,
                path,
                content_type,
                f"files{file_extension}",
            )
        else:
            filename_without_extension = filename.split(".")[0]
            if filename_without_extension in [
                "mask_prompts",
                "embeddings",
            ]:
                options[filename_without_extension] = UploadedFile(
                    filename,
                    path,
                    content_type,
                    f"files{file_extension}",
                )
            else:
                options[filename_without_extension] = np.load(path)

    return options


@pytest.fixture(scope="module", params=model_names)
def model_name(request):
    """Fixture to provide the model_name argument to api.predict."""

    return request.param


@pytest.fixture(scope="module", params=["application/json"])
def accept(request):
    """Fixture to provide the accept argument to api.predict."""
    return request.param


@pytest.fixture(scope="module")
def pred_kwds( model_name, accept):
    """Fixture to return arbitrary keyword arguments for predictions."""
    pred_kwds = {
        #"options": input_files,
        "model_name": model_name,
        "accept": accept,
    }
    print(f"the args for detections are {pred_kwds}")
    return {k: v for k, v in pred_kwds.items()}


@pytest.fixture(scope="module")
def test_predict(pred_kwds):
    """Test the predict function."""
    
    model_name = pred_kwds["model_name"]
    options = input_files(model_name)
    accept = pred_kwds["accept"]

    result = api.predict(model_name, accept, **options)
    return result, pred_kwds["accept"]
