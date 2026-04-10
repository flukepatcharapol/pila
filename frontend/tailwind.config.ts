// tailwind.config.ts
//
// Tailwind CSS configuration สำหรับ Studio Management FE
// วางไว้ที่ root ของ frontend/ project
// ต้อง sync กับ globals.css CSS variables เสมอ
// เหตุผล: Tailwind utilities ต้องใช้ design tokens เดียวกับ CSS variables

import type { Config } from "tailwindcss";

const config: Config = {
  // ─── Dark Mode ────────────────────────────────────────────────────────────────
  // ใช้ class-based: เพิ่ม class "dark" ที่ <html> element ผ่าน Settings toggle
  darkMode: "class",

  // ─── Content Paths ───────────────────────────────────────────────────────────
  // บอก Tailwind ว่า class names อยู่ที่ไหน เพื่อ purge unused styles
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx}",        // React components
    "./tests/fe/**/*.{ts,tsx}",  // Test helpers (ถ้ามี class names)
  ],

  theme: {
    extend: {
      // ─── Colors ─────────────────────────────────────────────────────────────
      // ต้อง match กับ CSS variables ใน globals.css ทุกค่า
      colors: {
        // Primary — Deep Sea Blue
        primary: {
          DEFAULT:   "#162839",
          container: "#2c3e50",
          fixed:     "#d1e4fb",
          "fixed-dim": "#b5c8df",
        },
        "on-primary": {
          DEFAULT:   "#ffffff",
          container: "#96a9be",
          "fixed-variant": "#36485b",
        },
        "inverse-primary": "#b5c8df",

        // Secondary — Steel Blue
        secondary: {
          DEFAULT:   "#395f94",
          container: "#9ec2fe",
          fixed:     "#d5e3ff",
          "fixed-dim": "#a7c8ff",
        },
        "on-secondary": {
          DEFAULT:   "#ffffff",
          container: "#284f83",
          "fixed-variant": "#1e477b",
        },

        // Tertiary/Accent — Muted Teal
        tertiary: {
          DEFAULT:   "#54b6b5",
          container: "#004444",
          fixed:     "#93f2f2",
        },
        "on-tertiary": {
          DEFAULT:   "#ffffff",
          container: "#54b6b5",
          "fixed-variant": "#004f4f",
        },

        // Surface Hierarchy
        surface: {
          DEFAULT:   "#f8fafb",
          dim:       "#d8dadb",
          bright:    "#f8fafb",
          tint:      "#4e6073",
        },
        "surface-container": {
          lowest:  "#ffffff",
          low:     "#f2f4f5",
          DEFAULT: "#eceeef",  // ใช้ไม่บ่อย
          high:    "#e6e8e9",
          highest: "#e1e3e4",
        },
        background: "#f8fafb",
        "inverse-surface": "#2d3132",

        // Text Colors
        "on-surface": {
          DEFAULT: "#191c1d",
          variant: "#43474c",
        },
        "inverse-on-surface": "#eff1f2",

        // Outline
        outline: {
          DEFAULT: "#73777f",
          variant: "#c4c6cd",
        },

        // Error
        error: {
          DEFAULT:   "#ba1a1a",
          container: "#ffdad6",
        },
        "on-error": {
          DEFAULT:   "#ffffff",
          container: "#410002",
        },
      },

      // ─── Typography ─────────────────────────────────────────────────────────
      fontFamily: {
        // Display/Headline — Manrope with Thai fallbacks
        display:  ["Manrope", "Kanit", "Sarabun", "sans-serif"],
        headline: ["Manrope", "Kanit", "Sarabun", "sans-serif"],

        // Body/Label — Inter
        body:     ["Inter", "sans-serif"],
        label:    ["Inter", "sans-serif"],

        // Shorthand aliases
        manrope:  ["Manrope", "Kanit", "Sarabun", "sans-serif"],
        inter:    ["Inter", "sans-serif"],
      },

      fontSize: {
        // Display scale
        "display-lg": ["3.5rem",  { lineHeight: "1.1", letterSpacing: "-0.03em" }],
        "display-md": ["2.8rem",  { lineHeight: "1.1", letterSpacing: "-0.02em" }],
        "display-sm": ["2.25rem", { lineHeight: "1.2", letterSpacing: "-0.02em" }],

        // Headline scale
        "headline-lg": ["2rem",    { lineHeight: "1.2", letterSpacing: "-0.02em" }],
        "headline-md": ["1.75rem", { lineHeight: "1.2", letterSpacing: "-0.02em" }],
        "headline-sm": ["1.5rem",  { lineHeight: "1.25", letterSpacing: "-0.01em" }],

        // Title scale
        "title-lg":    ["1.375rem", { lineHeight: "1.3" }],
        "title-md":    ["1.125rem", { lineHeight: "1.4" }],
        "title-sm":    ["0.875rem", { lineHeight: "1.4", fontWeight: "600" }],

        // Body scale
        "body-lg":     ["1rem",    { lineHeight: "1.5" }],
        "body-md":     ["0.875rem", { lineHeight: "1.5" }],
        "body-sm":     ["0.75rem",  { lineHeight: "1.5" }],

        // Label scale
        "label-lg":    ["0.875rem", { lineHeight: "1.4", letterSpacing: "0.01em" }],
        "label-md":    ["0.75rem",  { lineHeight: "1.4", letterSpacing: "0.01em" }],
        "label-sm":    ["0.6875rem",{ lineHeight: "1.4", letterSpacing: "0.01em" }],
      },

      lineHeight: {
        // Thai text — ต้องมี line-height พิเศษสำหรับ tone marks
        thai: "1.6",
        tight: "1.2",
        normal: "1.5",
      },

      // ─── Shadows ────────────────────────────────────────────────────────────
      boxShadow: {
        // Ambient shadow — ใช้แทน shadow ทั่วไปทุกกรณี
        ambient: "0px 20px 40px rgba(25, 28, 29, 0.06)",
        // Elevated card shadow
        elevated: "0px 8px 24px rgba(25, 28, 29, 0.08)",
        // Ghost border simulation
        "ghost-border": "0 0 0 1px rgba(196, 198, 205, 0.15)",
        // None override
        none: "none",
      },

      // ─── Border Radius ───────────────────────────────────────────────────────
      borderRadius: {
        sm:   "0.25rem",
        md:   "0.5rem",
        lg:   "0.75rem",
        xl:   "1rem",
        "2xl": "1.25rem",
        "3xl": "1.5rem",
      },

      // ─── Backdrop Blur ───────────────────────────────────────────────────────
      backdropBlur: {
        // Standard blur สำหรับ glassmorphism (ต้องใช้ค่านี้เสมอ)
        glass: "12px",
        // Header blur ที่เบากว่า
        header: "20px",
      },

      // ─── Spacing ─────────────────────────────────────────────────────────────
      // ใช้ Tailwind default scale + custom values
      spacing: {
        "18": "4.5rem",
        "72": "18rem",
        "84": "21rem",
        "96": "24rem",
      },

      // ─── Sidebar Width ───────────────────────────────────────────────────────
      width: {
        sidebar: "18rem", // 288px — fixed sidebar width
      },

      // ─── Z-Index ─────────────────────────────────────────────────────────────
      zIndex: {
        sidebar: "40",
        header:  "50",
        overlay: "60",
        modal:   "70",
        toast:   "80",
      },

      // ─── Animation ───────────────────────────────────────────────────────────
      keyframes: {
        "fade-in-up": {
          "0%":   { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-in-right": {
          "0%":   { opacity: "0", transform: "translateX(16px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "slide-in-left": {
          "0%":   { opacity: "0", transform: "translateX(-16px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        shimmer: {
          "0%":   { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "fade-in-up":      "fade-in-up 200ms ease both",
        "slide-in-right":  "slide-in-right 200ms ease both",
        "slide-in-left":   "slide-in-left 200ms ease both",
        shimmer:           "shimmer 1.5s infinite linear",
      },
    },
  },

  plugins: [
    // Tailwind Forms — normalize form elements
    require("@tailwindcss/forms")({
      strategy: "class", // ใช้ class-based เพื่อไม่กระทบ global styles
    }),

    // Tailwind Container Queries (optional)
    require("@tailwindcss/container-queries"),
  ],
};

export default config;
