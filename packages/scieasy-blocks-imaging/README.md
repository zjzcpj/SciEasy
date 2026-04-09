# scieasy-blocks-imaging

Phase 11 imaging plugin for SciEasy.

The package ships 35 implemented imaging ticket deliverables covering 51
concrete block classes across IO, preprocess, morphology, segmentation,
measurement, registration, projection, math, visualization, and interactive
AppBlocks. The primary public types are `Image`, `Mask`, and `Label`;
registration also uses the internal helper type `Transform`.

Blocks:
- IO: `LoadImage`, `SaveImage`
- Preprocess: `Denoise`, `BackgroundSubtract`, `Normalize`, `FlatFieldCorrect`, `Rotate`, `Flip`, `Crop`, `Pad`, `Resize`, `ConvertDType`, `AxisSplit`, `AxisMerge`
- Morphology: `MorphologyOp`, `EdgeDetect`, `RidgeFilter`, `Sharpen`, `FFTFilter`
- Segmentation: `Threshold`, `Watershed`, `CellposeSegment`, `BlobDetect`, `ConnectedComponents`, `RemoveSmallObjects`, `RemoveBorderObjects`, `FillHoles`, `ExpandLabels`, `ShrinkLabels`
- Measurement: `RegionProps`, `PairwiseDistance`, `Colocalization`
- Registration: `ComputeRegistration`, `ApplyTransform`, `RegisterSeries`
- Projection: `AxisProjection`, `SelectSlice`
- Math: `AddScalar`, `SubtractScalar`, `MultiplyScalar`, `DivideScalar`, `ImageCalculator`
- Visualization: `RenderPseudoColor`, `RenderOverlay`, `RenderMontage`, `RenderMovie`, `RenderHistogram`
- Interactive: `FijiBlock`, `NapariBlock`, `CellProfilerBlock`, `QuPathBlock`

Phase 12 deferrals remain unchanged: `Deconvolve` and `TrackObjects`.

Entry points:
- `scieasy.blocks = scieasy_blocks_imaging:get_block_package`
- `scieasy.types = scieasy_blocks_imaging:get_types`
