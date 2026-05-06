# Font Patcher Thing
> Script to increase the line height of a font

<img width="778" alt="Screen Shot 2020-01-05 at 1 59 58 PM" src="https://user-images.githubusercontent.com/11488762/71784658-b16c1480-2fc3-11ea-893c-255e8b895cf0.png">

# Intro
This script shouldn't really exist, and patching fonts in this way isn't really such a good idea.
However, Emacs currently doesn't have proper support for adjusting line height,
as summarized in [this stack overflow question](https://stackoverflow.com/questions/26437034/emacs-line-height).
The only workaround that I have found to work reliably, is to patch the font itself to include the proper spacing.
So, here is a script that at least makes the process easy.

# Examples

The easiest way to run the script is to build the Docker image from the `Dockerfile` provided.

```bash
# build the image (only required once)
docker build -t font-patcher .
```

If you are using the examples below as is, make sure to copy your original font into the `fonts`
directory of this project so the files will be available inside the container.

### Patch a single font file

```bash
docker run --rm -v "$PWD":/work font-patcher \
    --factor=1.3 \
    --input="/work/fonts/Operator Mono.otf" \
    --outputDir="/work/fonts/patched"
```

### Patch multiple font files at once

This is really just the repetition of patching a single font file, but since it's so common, here is an example:

```bash
for x in fonts/OperatorMono/*; do
    docker run --rm -v "$PWD":/work font-patcher \
        --factor=1.3 \
        --input="/work/$x" \
        --outputDir="/work/fonts/patched"
done
```

