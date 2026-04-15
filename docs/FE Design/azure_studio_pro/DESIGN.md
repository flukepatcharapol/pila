# Design System Document

## 1. Overview & Creative North Star
**Creative North Star: The Mindful Curator**

This design system is built to transform studio management from a chaotic administrative task into a serene, editorial experience. Inspired by the precision and flow of Pilates, the system rejects the "cluttered dashboard" aesthetic in favor of **The Mindful Curator**—a philosophy that prioritizes high-contrast typography, intentional asymmetry, and a deep sense of atmospheric layering. 

We move beyond standard templates by treating the screen as a gallery space. By utilizing expansive whitespace and high-end editorial font scales, we create an interface that feels bespoke, premium, and calm. The target is desktop and tablet-first, ensuring that studio owners and instructors have a command center that feels as professional as their boutique environment.

---

## 2. Colors
Our palette is rooted in tonal depth, using "Deep Sea Blue" as an anchor of authority and "Muted Teal" as a breath of kinetic energy.

### Core Tokens
- **Primary:** `#162839` (Deep Sea) – Used for primary navigation and high-level headers.
- **Secondary:** `#395f94` (Steel Blue) – Used for supportive interactive elements.
- **Tertiary/Accent:** `#54b6b5` (Muted Teal) – Used sparingly for key conversion points and success states.
- **Surface:** `#f8fafb` (Soft White) – Our foundational canvas.

### The "No-Line" Rule
To maintain a high-end feel, **1px solid borders are prohibited for sectioning.** We do not use "boxes" to separate content. Boundaries must be defined solely through background color shifts. For example, a `surface-container-low` sidebar sitting against a `surface` main content area creates a natural, modern division without the visual noise of a line.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers. Use the `surface-container` tiers to create "nested" depth:
*   **Lowest (`#ffffff`):** For the most prominent interactive cards and action modules.
*   **Low (`#f2f4f5`):** For secondary content areas.
*   **High/Highest (`#e6e8e9`):** For inactive background regions or "sunken" utility trays.

### Glass & Gradient Rule
Floating elements (such as navigation bars or active session overlays) should utilize **Glassmorphism**. Use a semi-transparent surface color with a `backdrop-blur(12px)` effect. Main CTAs should not be flat; apply a subtle linear gradient from `primary` to `primary_container` to provide a sense of "soul" and professional polish.

---

## 3. Typography
The typography system uses a dual-font approach to balance authoritative editorial style with functional clarity.

*   **Display & Headlines (Manrope):** Chosen for its geometric precision and modern Thai support (Kanit/Sarabun fallbacks). Use `display-lg` (3.5rem) and `headline-md` (1.75rem) to create clear, magazine-style entry points into data.
*   **Body & Titles (Inter):** The workhorse font. `body-md` (0.875rem) ensures dense studio schedules remain legible.
*   **Hierarchy as Identity:** Use tight letter-spacing for headlines to feel "premium" and wider line-heights for body text to promote readability during fast-paced studio hours.

---

## 4. Elevation & Depth
We convey hierarchy through **Tonal Layering** rather than traditional structural shadows.

*   **The Layering Principle:** Place a `surface-container-lowest` card on a `surface-container-low` background. The subtle shift from a soft grey to a pure white creates a "soft lift" that feels architectural rather than digital.
*   **Ambient Shadows:** For elements that must truly "float" (like a student profile modal), use an extra-diffused shadow. 
    *   *Spec:* `0px 20px 40px rgba(25, 28, 29, 0.06)`. 
    *   The shadow color must be a tint of the `on-surface` color, never pure black.
*   **The Ghost Border:** If accessibility requires a container boundary, use the `outline-variant` token at **15% opacity**. This creates a "suggestion" of a line rather than a hard barrier.

---

## 5. Components

### Buttons
*   **Primary:** Gradient fill (`primary` to `primary_container`), white text, `lg` (0.5rem) roundedness.
*   **Secondary:** Ghost style using a `secondary` text color on a `surface-container-highest` background. No border.
*   **Tertiary:** Text-only with a subtle `on-tertiary-container` underline on hover.

### Cards & Lists
*   **The Rule of Flow:** Forbid the use of divider lines between list items. Instead, use a `1.5rem` vertical gap. For lists of students or sessions, use alternating tonal backgrounds (`surface` vs `surface-container-low`) to define rows.
*   **Boutique Cards:** Use `xl` (0.75rem) corner radius. Content should be padded generously (at least `2rem`).

### Signature Components for Pilates Management
*   **The Session Chip:** Small, high-contrast chips using `tertiary_fixed` for class types (e.g., "Reformer," "Mat"). These should feel like premium labels.
*   **Capacity Gauges:** Instead of standard progress bars, use subtle tonal rings. A `secondary_container` track with a `secondary` fill, utilizing a soft glow when a class is at 100% capacity.
*   **Interactive Schedule:** A high-end grid that uses "Glassmorphism" for booked slots, allowing the background colors of the studio's daily rhythm to peek through.

---

## 6. Do's and Don'ts

### Do
*   **Do** use intentional asymmetry. A large display heading on the left balanced by a "glass" card on the right feels more premium than a centered layout.
*   **Do** prioritize Thai legibility. Ensure line-height for Thai characters is 1.6x the font size to prevent clipping of tone marks.
*   **Do** use "Breathing Room." If you think there is enough whitespace, add 20% more.

### Don'ts
*   **Don't** use 100% black text. Always use `on-surface` (#191c1d) for a softer, more sophisticated contrast.
*   **Don't** use default Material Design shadows. They are too heavy for a "boutique" feel. Stick to tonal shifts and ambient, low-opacity blurs.
*   **Don't** use dividers to separate sections. Use the `surface-container` tiers or empty space to guide the eye.