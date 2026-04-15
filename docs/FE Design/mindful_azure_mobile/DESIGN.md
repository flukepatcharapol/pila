# Design System Specification: The Digital Curator

## 1. Overview & Creative North Star
This design system is an editorial-first evolution of the 'Azure Studio Pro' aesthetic, optimized for a high-end mobile experience. Our Creative North Star is **"The Mindful Curator."** 

Unlike standard mobile frameworks that rely on rigid grids and heavy borders, this system prioritizes serenity, professional depth, and breathing room. We achieve a "custom" feel by using intentional asymmetry—such as staggered image placements and overlapping typography—to break the "template" look. This is a space of calm authority, designed specifically for the **Boston Pilates** brand, where the interface feels like a curated gallery rather than a utility app.

## 2. Color & Tonal Depth
The palette is rooted in deep sea blues and sophisticated teals, utilizing Material Design tokens to create a layered, "physical" UI.

*   **Primary Palette:** `primary` (#162839) and `primary_container` (#2C3E50) anchor the experience with professional weight.
*   **The "No-Line" Rule:** To maintain a premium editorial feel, **1px solid borders are strictly prohibited** for sectioning. Boundaries must be defined solely through background color shifts. For example, a `surface_container_low` section should sit against a `surface` background to define its edge.
*   **Surface Hierarchy:** Depth is created through nesting. Treat the UI as stacked sheets of fine paper:
    *   **Base:** `surface` (#fbf9fa)
    *   **Sectioning:** `surface_container_low` (#f5f3f4)
    *   **Interactive Cards:** `surface_container_lowest` (#ffffff)
*   **The "Glass & Gradient" Rule:** Floating elements (like navigation bars or modal headers) should utilize Glassmorphism: `surface` color at 80% opacity with a `24px` backdrop-blur. 
*   **Signature Textures:** For high-impact CTAs or Hero backgrounds, use a subtle linear gradient (135°) from `primary` (#162839) to `primary_container` (#2C3E50) to add "soul" and dimension.

## 3. Typography: The Editorial Voice
We use **Manrope** across all scales to ensure modern, geometric clarity that remains legible on small screens.

*   **Display & Headlines:** Use `display_md` (2.75rem) for hero statements. To achieve the editorial look, use tight letter-spacing (-0.02em) and generous line-height.
*   **Titles:** `title_lg` (1.375rem) should be used for section headers, often paired with an asymmetrical layout (e.g., left-aligned title with a right-aligned "view all" link).
*   **Body:** `body_lg` (1rem) is the workhorse. Always prioritize vertical stacking to ensure maximum readability and thumb-friendly interaction.
*   **Hierarchy Note:** Use `on_surface_variant` (#43474c) for secondary information to create a soft, intentional contrast that guides the eye without causing fatigue.

## 4. Elevation & Depth
In this system, elevation is a product of light and tone, not structure.

*   **Tonal Layering:** Avoid traditional shadows where possible. A `surface_container_highest` element sitting on a `surface` background provides enough natural "lift" for most UI needs.
*   **Ambient Shadows:** When an object must float (e.g., a "Book Now" FAB), use an extra-diffused shadow:
    *   *X: 0, Y: 8, Blur: 24, Spread: -4*
    *   *Color:* Use `primary` (#162839) at **6% opacity**. This mimics natural light reflecting off the deep blue palette.
*   **The "Ghost Border" Fallback:** If accessibility requires a container edge, use a "Ghost Border": `outline_variant` at 15% opacity. Never use 100% opaque lines.

## 5. Components & Interactions

### Buttons
*   **Primary:** High-gloss `primary` (#162839) background with `on_primary` (#ffffff) text. 
*   **Secondary:** `secondary_container` (#aaeff0) with `on_secondary_container` (#266e70).
*   **Styling:** All buttons use **ROUND_FOUR (1rem)** corner radius. Height must be at least **56px** to ensure "thumb-friendly" accessibility.

### Cards & Vertical Stacking
*   **Card Anatomy:** Use `surface_container_lowest` for card backgrounds. 
*   **Spacing:** Forbid divider lines. Use `24px` or `32px` of vertical white space to separate content blocks.
*   **The "Boston Pilates" Logo:** The logo should be placed in the `surface_bright` header with at least `24px` of padding on all sides to maintain its "Mindful Curator" integrity.

### Input Fields
*   **Styling:** Large, soft-rounded containers (`1rem`). 
*   **States:** Use a `2px` `secondary` (#1e686a) "Ghost Border" only on focus. Otherwise, use `surface_container_high` as the field background to create a "recessed" look.

### Navigation (The Mobile Dock)
*   A persistent bottom dock using Glassmorphism (`surface` at 85% opacity + blur).
*   Icons should use `on_surface_variant` (#43474c), switching to `primary` (#162839) when active, accompanied by a subtle `secondary_fixed` (#aaeff0) dot indicator.

## 6. Do's and Don'ts

### Do:
*   **Do** use asymmetrical margins (e.g., 24px left, 32px right) for editorial image captions.
*   **Do** prioritize vertical scrolling and large, tappable areas (minimum 48x48px).
*   **Do** use tonal shifts to indicate hierarchy; make the user "feel" the depth.
*   **Do** allow the **Boston Pilates** logo to breathe; never crowd it with icons or text.

### Don't:
*   **Don't** use 1px solid black or high-contrast borders.
*   **Don't** use standard "Drop Shadows" (dark grey/black).
*   **Don't** use horizontal carousels for primary navigation; stick to the "Mindful Curator" vertical stack for clarity.
*   **Don't** use sharp corners; every element must adhere to the **ROUND_FOUR (1rem)** or **full (pill)** rounding scale to maintain the serene personality.