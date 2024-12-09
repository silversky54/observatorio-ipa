import pytest
import ee
from observatorio_ipa.binary import (
    ic_snow_landcover_reclass,
    img_snow_landcover_reclass,
)

# FILE: src/observatorio_ipa/test_binary.py


# Initialize the Earth Engine module.
ee.Initialize()


def test_ic_snow_landcover_reclass():
    # Create mock data for ImageCollection and FeatureCollection
    mock_image = (
        ee.image.Image.constant(0)
        .rename("NDSI_Snow_Cover")
        .addBands(ee.image.Image.constant(0).rename("Snow_Albedo_Daily_Tile_Class"))
        .addBands(
            ee.image.Image.constant(0).rename("NDSI_Snow_Cover_Algorithm_Flags_QA")
        )
    )
    mock_collection = ee.imagecollection.ImageCollection([mock_image])
    mock_aoi = ee.featurecollection.FeatureCollection(
        [ee.feature.Feature(ee.geometry.Geometry.Point([0, 0]))]
    )

    # Call the function with the mock data
    result = ic_snow_landcover_reclass(mock_collection, mock_aoi, 40)

    # Assert the expected results
    assert isinstance(
        result, ee.imagecollection.ImageCollection
    )  # "Result should be an ImageCollection"

    band_names = result.first().bandNames().getInfo()
    assert (
        band_names is not None and "LandCover_class" in band_names
    )  # "Result should contain 'LandCover_class' band"

    assert len(band_names) == 1  # "Result should contain exactly one band"

    assert (
        result.size().getInfo() == 1
    )  # "Result should contain exactly one image in the collection"

    # TODO: assert that it raises an error if the required bands are not present in the ImageCollection


def test_img_snow_landcover_reclass():
    # Create mock data for Image
    mock_image = (
        ee.image.Image.constant(0)
        .rename("NDSI_Snow_Cover")
        .addBands(ee.image.Image.constant(0).rename("Snow_Albedo_Daily_Tile_Class"))
        .addBands(
            ee.image.Image.constant(0).rename("NDSI_Snow_Cover_Algorithm_Flags_QA")
        )
    )

    # Call the function with the mock data
    result = img_snow_landcover_reclass(mock_image, 40)

    # Assert the expected results
    assert isinstance(result, ee.image.Image)  # "Result should be an Image"

    band_names = result.bandNames().getInfo()
    assert (
        band_names is not None and "LandCover_class" in band_names
    )  # "Result should contain 'LandCover_class' band"

    assert len(band_names) == 4, "Result should contain exactly four bands"

    assert (
        result.get("Threshold_NDSI").getInfo() == 40
    ), "Threshold_NDSI property should be set to 40"

    # TODO: Add test to assert values of the 'LandCover_class' band
    # TODO: Assert that the 'LandCover_class' band values are 0, 50, or 100
    # TODO: Assert that the 'LandCover_class' band values are consistent with the input bands
    # TODO: Assert that it raises an error if the required bands are not present in the input image
