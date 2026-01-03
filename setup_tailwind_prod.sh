#!/bin/bash

# setup_tailwind_prod.sh
# This script sets up Tailwind CSS for production to replace the CDN.

echo "🚀 Starting Tailwind CSS Production Setup..."

# 1. Initialize Node.js project if not already done
if [ ! -f "package.json" ]; then
    echo "📦 Initializing npm project..."
    npm init -y
fi

# 2. Install Tailwind CSS
echo "⬇️ Installing Tailwind CSS..."
npm install -D tailwindcss

# 3. Create tailwind.config.js with your custom theme
echo "⚙️ Creating tailwind.config.js..."
cat > tailwind.config.js <<EOL
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./blog/templates/**/*.html",
    "./blog/js/**/*.js",
    "./BACKEND/app/templates/**/*.html"
  ],
  theme: {
    extend: {
      fontFamily: {
        inter: ['Inter', 'sans-serif'],
        syne: ['Syne', 'sans-serif'],
      },
      colors: {
        base: 'var(--base)',
        'base-tint': 'var(--base-tint)',
        't-bright': 'var(--t-bright)',
        't-medium': 'var(--t-medium)',
        't-muted': 'var(--t-muted)',
        accent: 'var(--accent)',
        secondary: 'var(--secondary)',
        'stroke-elements': 'var(--stroke-elements)',
      },
      borderColor: {
        DEFAULT: 'var(--stroke-elements)',
      },
    },
  },
  plugins: [],
  corePlugins: {
    preflight: true,
  }
}
EOL

# 4. Create proper input CSS file
echo "🎨 Creating CSS input file..."
mkdir -p blog/css
cat > blog/css/input.css <<EOL
@tailwind base;
@tailwind components;
@tailwind utilities;
EOL

# 5. Build the CSS
echo "🔨 Building production CSS..."
npx tailwindcss -i ./blog/css/input.css -o ./blog/css/tailwind-output.css --minify

# 6. Verify the build
if [ -f "blog/css/tailwind-output.css" ]; then
    echo "✅ Success! Tailwind CSS has been built to blog/css/tailwind-output.css"
    echo "   Size: $(ls -sh blog/css/tailwind-output.css | awk '{print $1}')"
else
    echo "❌ Build failed. Please check the logs."
    exit 1
fi

echo ""
echo "📝 NEXT STEP: Update your HTML"
echo "To finish, you need to update blog/templates/base_blog.html:"
echo "1. Remove the <script src=\"https://cdn.tailwindcss.com\"></script> tag"
echo "2. Remove the <script>tailwind.config = ...</script> block"
echo "3. Add this line before your other CSS links:"
echo "   <link rel=\"stylesheet\" href=\"/blog/css/tailwind-output.css\">"
echo ""
echo "Would you like me to attempt to update base_blog.html automatically? (y/n)"
read -r response
if [[ "\$response" =~ ^([yY][eE][sS]|[yY])\$ ]]; then
    # Backup
    cp blog/templates/base_blog.html blog/templates/base_blog.html.bak
    
    # Simple replacement using sed (this is approximate)
    # We'll just comment out the CDN lines and add the link
    sed -i 's|<script src="https://cdn.tailwindcss.com"></script>|<!-- CDN Removed -->\n  <link rel="stylesheet" href="/blog/css/tailwind-output.css">|' blog/templates/base_blog.html
    
    echo "✅ base_blog.html updated. Backup saved as base_blog.html.bak"
    echo "⚠️  Note: You should manually remove the inline tailwind.config script block to clean up."
fi
