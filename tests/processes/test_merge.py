# import pytest
# import ee
# from observatorio_ipa.merge import (
#     calculate_TAC,
#     calculate_TA_QA,
#     add_missing_band,
#     merge,
# )

# # FILE: tests/test_merge.py


# # Initialize the Earth Engine module.
# ee.Initialize()


# def test_calculate_TAC():
#     # Create mock data for Image
#     mock_image = (
#         ee.image.Image.constant(0)
#         .rename("LandCover_T")
#         .addBands(ee.image.Image.constant(50).rename("LandCover_A"))
#     )

#     # Call the function with the mock data
#     result = calculate_TAC(mock_image)

#     # Assert the expected results
#     assert isinstance(result, ee.image.Image), "Result should be an Image"

#     band_names = result.bandNames().getInfo()

#     assert band_names is not None, "Result should contain band names"

#     if band_names:
#         assert "TAC" in band_names, "Result should contain 'TAC' band"

#     tac_values = (
#         result.select("TAC")
#         .reduceRegion(ee.reducer.Reducer.toList(), None, 1)
#         .get("TAC")
#         .getInfo()
#     )
#     assert (
#         50 in tac_values
#     ), "TAC band should have the maximum value between 'LandCover_T' and 'LandCover_A'"


# def test_calculate_TA_QA():
#     # Create mock data for Image
#     mock_image = (
#         ee.image.Image.constant(0)
#         .rename("LandCover_T")
#         .addBands(ee.image.Image.constant(50).rename("LandCover_A"))
#     )

#     # Call the function with the mock data
#     result = calculate_TA_QA(mock_image)

#     # Assert the expected results
#     assert isinstance(result, ee.image.Image), "Result should be an Image"

#     band_names = result.bandNames().getInfo()

#     assert band_names is not None, "Result should contain band names"

#     if band_names:
#         assert "QA_CR" in band_names, "Result should contain 'QA_CR' band"

#     qa_values = (
#         result.select("QA_CR")
#         .reduceRegion(ee.reducer.Reducer.toList(), None, 1)
#         .get("QA_CR")
#         .getInfo()
#     )
#     assert 11 in qa_values, "QA_CR band should have the correct recoded values"


# def test_add_missing_band():
#     # Create mock data for Image
#     mock_image = ee.image.Image.constant(0).rename("existing_band")

#     # Call the function with the mock data
#     result = add_missing_band(mock_image, "new_band")

#     # Assert the expected results
#     assert isinstance(result, ee.image.Image), "Result should be an Image"

#     band_names = result.bandNames().getInfo()

#     assert band_names is not None, "Result should contain band names"

#     if band_names:
#         assert "new_band" in band_names, "Result should contain 'new_band'"

#     assert band_names == [
#         "existing_band",
#         "new_band",
#     ], "Result should contain both bands"


# def test_merge():
#     # Create mock data for ImageCollection
#     mock_image_MOD = (
#         ee.image.Image.constant(0).rename("LandCover_class").set("system:time_start", 1)
#     )
#     mock_image_MYD = (
#         ee.image.Image.constant(50)
#         .rename("LandCover_class")
#         .set("system:time_start", 1)
#     )
#     mock_MOD_ic = ee.imagecollection.ImageCollection([mock_image_MOD])
#     mock_MYD_ic = ee.imagecollection.ImageCollection([mock_image_MYD])

#     # Call the function with the mock data
#     result = merge(mock_MOD_ic, mock_MYD_ic)

#     # Assert the expected results
#     assert isinstance(
#         result, ee.imagecollection.ImageCollection
#     ), "Result should be an ImageCollection"

#     first_image = result.first()
#     band_names = first_image.bandNames().getInfo()
#     if band_names:
#         assert "TAC" in band_names, "Result should contain 'TAC' band"
#         assert "QA_CR" in band_names, "Result should contain 'QA_CR' band"

#     assert band_names == [
#         "TAC",
#         "QA_CR",
#     ], "Result should have exact bands 'TAC' and 'QA_CR'"

#     tac_values = (
#         first_image.select("TAC")
#         .reduceRegion(ee.reducer.Reducer.toList(), None, 1)
#         .get("TAC")
#         .getInfo()
#     )
#     assert 50 in tac_values, "TAC band should have the correct values"

#     qa_values = (
#         first_image.select("QA_CR")
#         .reduceRegion(ee.reducer.Reducer.toList(), None, 1)
#         .get("QA_CR")
#         .getInfo()
#     )
#     assert 12 in qa_values, "QA_CR band should have the correct values"

#     assert (
#         result.size().getInfo() == 1
#     ), "Result should contain exactly one image in the collection"
