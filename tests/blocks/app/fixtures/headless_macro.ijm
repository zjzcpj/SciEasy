// T-TRK-015 headless Fiji macro for AppBlock integration audit.
//
// Invoked by tests/blocks/app/test_appblock_fiji_integration.py via
// the Fiji ``--headless -macro <macro> <args_file>`` CLI. The macro
// argument is a filesystem path to a plain-text file containing
// exactly two lines:
//
//     <input_image_path>
//     <output_image_path>
//
// This indirection is required because the AppBlock command validator
// rejects argv entries containing shell metacharacters such as the
// parentheses in the T-TRK-003 test image filename, so the image paths
// cannot be passed directly on the command line.
//
// The macro opens the input image, applies a 2.0-sigma Gaussian blur,
// saves the result as a TIFF at the output path, and exits. When
// running headless, the Fiji process terminates naturally once the
// macro returns.

argsFile = getArgument();
if (argsFile == "" || !File.exists(argsFile)) {
    exit("headless_macro.ijm: expected an existing args file path, got: " + argsFile);
}

contents = File.openAsString(argsFile);
lines = split(contents, "\n");
if (lengthOf(lines) < 2) {
    exit("headless_macro.ijm: args file must have at least 2 lines, got " + lengthOf(lines));
}

// Strip trailing CR on Windows line endings.
inputPath = replace(lines[0], "\r", "");
outputPath = replace(lines[1], "\r", "");

open(inputPath);
run("Gaussian Blur...", "sigma=2");
saveAs("Tiff", outputPath);
close();
