"""Test scaffold for T-IMG-001 — imaging type classes.

All tests are skipped pending impl agent. Test names mirror the
acceptance criteria in ``docs/specs/phase11-imaging-block-spec.md``
§T-IMG-001 (lines 762-787).
"""

from __future__ import annotations

import pytest


class TestImage:
    def test_image_required_axes_yx(self) -> None:
        pytest.skip("T-IMG-001 impl pending")

    def test_image_allowed_axes_full_alphabet(self) -> None:
        pytest.skip("T-IMG-001 impl pending")

    def test_image_2d_construction(self) -> None:
        pytest.skip("T-IMG-001 impl pending")

    def test_image_3d_zyx_construction(self) -> None:
        pytest.skip("T-IMG-001 impl pending")

    def test_image_5d_tzcyx_construction(self) -> None:
        pytest.skip("T-IMG-001 impl pending")

    def test_image_6d_tzclambdayx_construction(self) -> None:
        pytest.skip("T-IMG-001 impl pending")

    def test_image_meta_pixel_size_pq_round_trip(self) -> None:
        pytest.skip("T-IMG-001 impl pending")

    def test_image_meta_channels_list_channel_info(self) -> None:
        pytest.skip("T-IMG-001 impl pending")

    def test_image_meta_json_round_trip(self) -> None:
        pytest.skip("T-IMG-001 impl pending")

    def test_image_serialise_reconstruct_round_trip(self) -> None:
        pytest.skip("T-IMG-001 impl pending")


class TestMask:
    def test_mask_dtype_bool_required(self) -> None:
        pytest.skip("T-IMG-001 impl pending")

    def test_mask_dtype_float_raises_value_error(self) -> None:
        pytest.skip("T-IMG-001 impl pending")

    def test_mask_inherits_image_axes(self) -> None:
        pytest.skip("T-IMG-001 impl pending")


class TestLabel:
    def test_label_with_raster_only(self) -> None:
        pytest.skip("T-IMG-001 impl pending")

    def test_label_with_polygons_only(self) -> None:
        pytest.skip("T-IMG-001 impl pending")

    def test_label_with_both_slots(self) -> None:
        pytest.skip("T-IMG-001 impl pending")

    def test_label_neither_slot_raises_value_error(self) -> None:
        pytest.skip("T-IMG-001 impl pending")

    def test_label_meta_round_trip(self) -> None:
        pytest.skip("T-IMG-001 impl pending")


class TestTransform:
    def test_transform_2d_affine_shape(self) -> None:
        pytest.skip("T-IMG-001 impl pending")

    def test_transform_3d_affine_shape(self) -> None:
        pytest.skip("T-IMG-001 impl pending")

    def test_transform_meta_transform_type_required(self) -> None:
        pytest.skip("T-IMG-001 impl pending")


class TestPluginEntryPoint:
    def test_get_types_returns_four_classes(self) -> None:
        pytest.skip("T-IMG-001 impl pending")
