import pytest
import ee
from observatorio_ipa.spatial_4 import (
    impute_TAC_kernel4,
    spatial_4,
    DEFAULT_PROJECTION,
    DEFAULT_SCALE,
)

# FILE: tests/test_spatial_4.py


# Initialize the Earth Engine module.
ee.Initialize()


def test_impute_TAC_kernel4():
    # Create mock data for Image
    mock_image = (
        ee.image.Image.constant(0)
        .rename("TAC")
        .addBands(ee.image.Image.constant(10).rename("QA_CR"))
    )

    # Define kernel cells (4 neighboring pixels)
    weights = [[0, 1, 0], [1, 0, 1], [0, 1, 0]]
    kernel_w = ee.kernel.Kernel.fixed(weights=weights)

    # Incorporate MODIS projection and adjust scale
    projection = ee.projection.Projection(DEFAULT_PROJECTION).atScale(DEFAULT_SCALE)

    # Call the function with the mock data
    result = impute_TAC_kernel4(mock_image, projection, kernel_w)

    # Assert the expected results
    assert isinstance(result, ee.image.Image), "Result should be an Image"

    band_names = result.bandNames().getInfo()
    assert band_names is not None, "Result should contain band names"

    if band_names:
        assert "TAC" in band_names, "Result should contain 'TAC' band"
        assert "QA_CR" in band_names, "Result should contain 'QA_CR' band"

    tac_values = (
        result.select("TAC")
        .reduceRegion(ee.reducer.Reducer.toList(), None, 1)
        .get("TAC")
        .getInfo()
    )
    assert (
        50 in tac_values or 100 in tac_values  #! This might be wrong
    ), "TAC band should have the correct values"

    qa_values = (
        result.select("QA_CR")
        .reduceRegion(ee.reducer.Reducer.toList(), None, 1)
        .get("QA_CR")
        .getInfo()
    )
    assert 40 in qa_values, "QA_CR band should have the correct values"


def test_spatial_4():
    # Create mock data for ImageCollection
    mock_image = (
        ee.image.Image.constant(0)
        .rename("TAC")
        .addBands(ee.image.Image.constant(10).rename("QA_CR"))
    )
    mock_image_2 = (
        ee.image.Image.constant(50)
        .rename("TAC")
        .addBands(ee.image.Image.constant(11).rename("QA_CR"))
    )
    mock_collection = ee.imagecollection.ImageCollection([mock_image, mock_image_2])

    # Define kernel cells (4 neighboring pixels)
    weights = [[0, 1, 0], [1, 0, 1], [0, 1, 0]]
    kernel_w = ee.kernel.Kernel.fixed(weights=weights)

    # Incorporate MODIS projection and adjust scale
    projection = ee.projection.Projection(DEFAULT_PROJECTION).atScale(DEFAULT_SCALE)

    # Call the function with the mock data
    result = spatial_4(mock_collection)

    # Assert the expected results
    assert isinstance(
        result, ee.imagecollection.ImageCollection
    ), "Result should be an ImageCollection"

    assert (
        result.size().getInfo() == 2
    ), "Result should contain two images in the collection"

    band_names = result.first().bandNames().getInfo()
    assert band_names is not None, "Result should contain band names"

    if band_names:
        assert "TAC" in band_names, "Result should contain 'TAC' band"
        assert "QA_CR" in band_names, "Result should contain 'QA_CR' band"
