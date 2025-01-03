import pytest
from ee.ee_exception import EEException
from observatorio_ipa.gee.assets import check_asset_exists, check_container_exists


class TestCheckAssetExists:
    def test_asset_exists(self, mocker):
        mocker.patch(
            "observatorio_ipa.gee.assets.ee.data.getAsset",
            return_value={"type": "IMAGE"},
        )
        assert check_asset_exists("path/to/asset") == True

    def test_asset_does_not_exist(self, mocker):
        mocker.patch(
            "observatorio_ipa.gee.assets.ee.data.getAsset", side_effect=EEException
        )
        assert check_asset_exists("path/to/asset") == False

    def test_invalid_asset_type(self):
        with pytest.raises(ValueError, match="Invalid asset type: INVALID_TYPE"):
            check_asset_exists("path/to/asset", "INVALID_TYPE")

    def test_invalid_asset_type_input(self):
        with pytest.raises(TypeError, match="Invalid asset type: int"):
            check_asset_exists("path/to/asset", 1)  # type: ignore

    def test_getAsset_returns_none(self, mocker):
        mocker.patch(
            "observatorio_ipa.gee.assets.ee.data.getAsset",
            return_value=None,
        )
        assert check_asset_exists("path/to/asset") == False

    def test_asset_type_mismatch(self, mocker):
        mocker.patch(
            "observatorio_ipa.gee.assets.ee.data.getAsset",
            return_value={"type": "IMAGE"},
        )
        assert (
            check_asset_exists("observatorio_ipa.gee.assets.ee.data.getAsset", "TABLE")
            == False
        )

    def test_asset_type_match(self, mocker):
        mocker.patch(
            "observatorio_ipa.gee.assets.ee.data.getAsset",
            return_value={"type": "IMAGE"},
        )
        assert check_asset_exists("path/to/asset", "IMAGE") == True

    def test_invalid_asset_type_none(self, mocker):
        mocker.patch(
            "observatorio_ipa.gee.assets.ee.data.getAsset",
            return_value={"type": "IMAGE"},
        )
        assert check_asset_exists("path/to/asset", None) == True


class TestCheckContainerExists:
    def test_container_exists_folder(self, mocker):
        mocker.patch(
            "observatorio_ipa.gee.assets.ee.data.getAsset",
            return_value={"type": "FOLDER"},
        )
        assert check_container_exists("path/to/folder") == True

    def test_container_exists_image_collection(self, mocker):
        mocker.patch(
            "observatorio_ipa.gee.assets.ee.data.getAsset",
            return_value={"type": "IMAGE_COLLECTION"},
        )
        assert check_container_exists("path/to/image_collection") == True

    def test_container_does_not_exist(self, mocker):
        mocker.patch(
            "observatorio_ipa.gee.assets.ee.data.getAsset", side_effect=EEException
        )
        assert check_container_exists("path/to/folder") == False

    def test_container_invalid_type(self, mocker):
        mocker.patch(
            "observatorio_ipa.gee.assets.ee.data.getAsset",
            return_value={"type": "IMAGE"},
        )
        assert check_container_exists("path/to/folder") == False

    def test_getAsset_returns_none(self, mocker):
        mocker.patch(
            "observatorio_ipa.gee.assets.ee.data.getAsset",
            return_value=None,
        )
        assert check_container_exists("path/to/folder") == False
