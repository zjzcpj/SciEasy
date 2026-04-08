"""SciEasy imaging plugin - Phase 11 imaging blocks landed so far."""

from __future__ import annotations

from scieasy_blocks_imaging.io.load_image import LoadImage
from scieasy_blocks_imaging.io.save_image import SaveImage
from scieasy_blocks_imaging.morphology.edge_detect import EdgeDetect
from scieasy_blocks_imaging.morphology.fft_filter import FFTFilter
from scieasy_blocks_imaging.morphology.morphology_op import MorphologyOp
from scieasy_blocks_imaging.morphology.ridge_filter import RidgeFilter
from scieasy_blocks_imaging.morphology.sharpen import Sharpen
from scieasy_blocks_imaging.preprocess.axis_ops import AxisMerge, AxisSplit
from scieasy_blocks_imaging.preprocess.background_subtract import BackgroundSubtract
from scieasy_blocks_imaging.preprocess.convert_dtype import ConvertDType
from scieasy_blocks_imaging.preprocess.denoise import Denoise
from scieasy_blocks_imaging.preprocess.flat_field_correct import FlatFieldCorrect
from scieasy_blocks_imaging.preprocess.geometry import Crop, Flip, Pad, Resize, Rotate
from scieasy_blocks_imaging.preprocess.normalize import Normalize
from scieasy_blocks_imaging.segmentation.blob_detect import BlobDetect
from scieasy_blocks_imaging.segmentation.cellpose_segment import CellposeSegment
from scieasy_blocks_imaging.segmentation.cleanup import (
    ExpandLabels,
    FillHoles,
    RemoveBorderObjects,
    RemoveSmallObjects,
    ShrinkLabels,
)
from scieasy_blocks_imaging.segmentation.connected_components import ConnectedComponents
from scieasy_blocks_imaging.segmentation.threshold import Threshold
from scieasy_blocks_imaging.segmentation.watershed import Watershed
from scieasy_blocks_imaging.types import Image, Label, Mask, Transform


def get_types() -> list[type]:
    """Return the imaging plugin's exported type classes."""
    return [Image, Mask, Label, Transform]


def get_blocks() -> list[type]:
    """Return the imaging plugin's exported block classes landed so far."""
    return [
        LoadImage,
        SaveImage,
        Denoise,
        BackgroundSubtract,
        Normalize,
        FlatFieldCorrect,
        Rotate,
        Flip,
        Crop,
        Pad,
        Resize,
        ConvertDType,
        AxisSplit,
        AxisMerge,
        MorphologyOp,
        EdgeDetect,
        RidgeFilter,
        Sharpen,
        FFTFilter,
        Threshold,
        Watershed,
        CellposeSegment,
        BlobDetect,
        ConnectedComponents,
        RemoveSmallObjects,
        RemoveBorderObjects,
        FillHoles,
        ExpandLabels,
        ShrinkLabels,
    ]


__all__ = [
    "AxisMerge",
    "AxisSplit",
    "BackgroundSubtract",
    "BlobDetect",
    "CellposeSegment",
    "ConnectedComponents",
    "ConvertDType",
    "Crop",
    "Denoise",
    "EdgeDetect",
    "ExpandLabels",
    "FFTFilter",
    "FillHoles",
    "FlatFieldCorrect",
    "Flip",
    "Image",
    "Label",
    "LoadImage",
    "Mask",
    "MorphologyOp",
    "Normalize",
    "Pad",
    "RemoveBorderObjects",
    "RemoveSmallObjects",
    "Resize",
    "RidgeFilter",
    "Rotate",
    "SaveImage",
    "Sharpen",
    "ShrinkLabels",
    "Threshold",
    "Transform",
    "Watershed",
    "get_blocks",
    "get_types",
]
