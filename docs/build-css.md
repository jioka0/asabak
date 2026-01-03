# How to Build Tailwind CSS for Production

We use a local build of Tailwind CSS instead of the CDN for better performance and to avoid console warnings. This guide explains how to rebuild the CSS when you make changes.

## Why we do this
Using the CDN in production causes high CPU usage on the client side (JIT compiler running in the browser) and shows warnings. A pre-built CSS file is much faster.

## The Setup
- **Source Config:** `tailwind.config.js` (in root)
- **Input CSS:** `blog/css/input.css`
- **Output CSS:** `blog/css/tailwind-output.css`
- **Tool:** Standalone `tailwindcss` binary (Linux x64)

## How to Rebuild CSS

If you change classes in your HTML or JavaScript files, you need to rebuild the CSS file.

### On the Server (Recommended)

Since we installed the standalone executable on the server, just run:

```bash
# From project root directory
./build-css.sh
```

If that script doesn't exist, you can run the binary directly:

```bash
./tailwindcss -i ./blog/css/input.css -o ./blog/css/tailwind-output.css --minify
```

### Initial Server Setup (One-time)

If setting up a new server, run these commands to download the tool:

1. **Download the standalone executable:**
   ```bash
   curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64
   ```

2. **Make it executable:**
   ```bash
   chmod +x tailwindcss-linux-x64
   mv tailwindcss-linux-x64 tailwindcss
   ```

3. **Create the build script:**
   ```bash
   echo '#!/bin/bash
   ./tailwindcss -i ./blog/css/input.css -o ./blog/css/tailwind-output.css --minify' > build-css.sh
   chmod +x build-css.sh
   ```

4. **Run the first build:**
   ```bash
   ./build-css.sh
   ```
