# CSS Inheritance Fix Guide

## Problem
Blog templates were shrinking and centering content due to CSS inheritance conflicts from base template styles.

## Solution Applied
### Preferred Fix: Fluid layout opt-in (recommended)
Use a template-level flag to disable Tailwind’s max-w-* clamping and mx-auto centering only when you want a full-width layout.

1) Base template: add data-fluid and scoped CSS
- Add a fluid flag on the main container so templates can opt in:
  - See [HTML.main()](blog/templates/base_blog.html:118)
  - See [HTML.style()](blog/templates/base_blog.html:107)

```html
<!-- base_blog.html -->
<main id="route-container" class="relative min-h-screen"
      data-fluid="{% block fluid_layout %}false{% endblock %}">
```

```html
<!-- base_blog.html: head -->
<style>
  /* Neutralize Tailwind container clamps in fluid mode only */
  main#route-container[data-fluid="true"] [class*="max-w-"] {
    max-width: none !important;
    width: 100% !important;
  }
  main#route-container[data-fluid="true"] .mx-auto {
    margin-left: 0 !important;
    margin-right: 0 !important;
  }
  main#route-container[data-fluid="true"] section {
    width: 100% !important;
  }
</style>
```

2) Per-template opt-in:
Place this in any template that should be full-width:
- See [Jinja.block()](blog/templates/template3-listing.html:3)
- See [Jinja.block()](blog/templates/template1-banner-image.html:3)
- See [Jinja.block()](blog/templates/template2-banner-video.html:3)

```jinja
{% block fluid_layout %}true{% endblock %}
```

3) Clean up old overrides:
Remove template-level DEBUG CSS and broad container overrides in favor of this opt-in. This avoids fighting Tailwind utilities and keeps nav/footer widths unchanged.

Why this works:
- Tailwind’s containers (max-w-7xl, max-w-4xl) plus mx-auto center and clamp width. The scoped CSS only un-does those utilities when data-fluid="true", preserving normal behavior elsewhere. This avoids blanket global overrides and regressions.

### Updated CSS Override Pattern
Replace generic container overrides with specific targeting:

```css
<style>
    /* Override container constraints for full-width template */
    /* Target the specific containers used in this template */
    .main-content-layout,
    .main-content-layout .content-grid {
        max-width: none !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Ensure full width for the main layout sections */
    .py-16.bg-white,
    .py-8.sm\:py-12.lg\:py-16.bg-gray-50 {
        max-width: none !important;
        margin: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
    
    /* Override the max-width constraints from base CSS */
    .main-content-layout .content-grid {
        max-width: none !important;
        padding: 0 1rem !important;
    }
    
    @media (min-width: 768px) {
        .main-content-layout .content-grid {
            padding: 0 2rem !important;
        }
    }
</style>
```

## Files Fixed
- ✅ template3-listing.html
- ✅ template1-banner-image.html  
- ✅ template2-banner-video.html

## Prevention Tips
1. **Use Specific Selectors**: Target exact containers, not generic class names
2. **Check CSS Cascade**: Be aware of base template styles that may override
3. **Test Responsive**: Always include media queries for mobile compatibility
4. **Use Browser DevTools**: Inspect elements to identify conflicting styles

## CSS Conflict Sources
- `blog/css/blog.css` - Global blog styles
- `blog/templates/css/blog-templates.css` - Design system styles
- TailwindCSS utilities - May conflict with custom styles

## Resolution
Templates now display at full width as intended, with proper responsive behavior.