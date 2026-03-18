---
description: Hexadian Corporation corporate UI style guide — color palette, layout, typography, components, and Tailwind reference classes. Apply when building or modifying any Hexadian web frontend.
applyTo: "**/*.{tsx,jsx,css,html}"
---

# Hexadian UI Style Guide

Reference guide for applying Hexadian Corporation's corporate styling to web apps.
Derived from `hexadian-blueprints-old` and `hexadian-auth-service` (auth-portal, auth-backoffice).

---

## Required Assets

Place these files in `public/brand/` (or the equivalent path for your stack):

| File                             | Usage                                       |
|----------------------------------|---------------------------------------------|
| `hxn_back.jpg`                   | Full-screen background image                |
| `HEXADIAN-Background_Round.png`  | Main round Hexadian logo                    |
| `mbtc_black.png`                 | MBTC badge (bottom-right corner)            |

---

## Color Palette

| Token          | Hex / value              | Usage                                |
|----------------|--------------------------|--------------------------------------|
| `--bg`         | `#0f0f0f`                | Base background / fallback (no image)|
| `--card`       | `#1c1c1c`                | Card and modal background            |
| `--accent`     | `#b8a96a`                | Primary buttons, highlights          |
| `--text`       | `#e6eef6`                | Primary text                         |
| `--muted`      | `#888888`                | Secondary text / subtitles           |
| `--very-muted` | `#555555`                | Tertiary text / hints                |
| `--border`     | `rgba(255,255,255,0.04)` | Card borders                         |

---

## Login / Centered Page Layout

```
┌────────────────────────────────────────────────┐
│  [background hxn_back.jpg + black overlay 60%] │
│                                                │
│           [Logo 80×80px]                       │
│        [Muted subtitle]                        │
│  ┌──────────────────────────────┐              │
│  │           Card               │              │
│  │    (form content)            │              │
│  └──────────────────────────────┘              │
│                                   [MBTC 100px] │
└────────────────────────────────────────────────┘
```

### Background
- Full-screen background image (`background-size: cover`, `background-position: center`)
- Semi-transparent black overlay on top: `rgba(0,0,0,0.6)`

### Main Logo
- Image: `HEXADIAN-Background_Round.png`
- Size: **80×80px**
- Horizontally centered, no box or shadow around it
- Bottom spacing to subtitle: ~12px

### Subtitle Below Logo
- Small text (`font-size: 0.875rem` / `text-sm`)
- Color: `#888888`

### Content Card
```css
border-radius: 14px;
border: 1px solid rgba(255, 255, 255, 0.04);
background: #1c1c1c;
padding: 32px;
box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
max-width: 448px;   /* ~max-w-md */
width: 100%;
```

### MBTC Badge
- Image: `mbtc_black.png`
- Position: **fixed** (`position: fixed`), **bottom-right** corner
- `bottom: 16px`, `right: 20px`
- Size: **100×100px**

---

## Typography

- Font: system (sans-serif by default, no Google Fonts)
- Section headings: `font-size: 1.25rem`, `font-weight: 600`, color `#e6eef6`
- Form text / body: `font-size: 0.875rem`, color `#e6eef6`
- Muted text: color `#888888`
- Very muted text / hints: `font-size: 0.75rem`, color `#555555`

---

## Inputs

```css
background: #111111;
border: 1px solid rgba(255, 255, 255, 0.08);
border-radius: 8px;
padding: 10px 14px;
color: #e6eef6;
font-size: 0.875rem;
width: 100%;
outline: none;
transition: border-color 0.2s;
```

Focus:
```css
border-color: rgba(255, 255, 255, 0.20);
```

---

## Buttons

### Primary
```css
background: #b8a96a;
color: #0f0f0f;
border: none;
border-radius: 8px;
padding: 10px 20px;
font-size: 0.875rem;
font-weight: 600;
cursor: pointer;
transition: opacity 0.2s;
```
Hover: `opacity: 0.85`

### Ghost / Secondary
```css
background: transparent;
color: #888888;
border: 1px solid rgba(255, 255, 255, 0.12);
border-radius: 8px;
padding: 10px 20px;
font-size: 0.875rem;
cursor: pointer;
transition: border-color 0.2s, color 0.2s;
```
Hover: `border-color: rgba(255,255,255,0.25)`, `color: #e6eef6`

### Danger / Destructive
```css
background: rgba(220, 38, 38, 0.15);
color: #f87171;
border: 1px solid rgba(220, 38, 38, 0.30);
```

---

## App Header (if applicable)

```css
background: rgba(15, 15, 15, 0.85);
backdrop-filter: blur(8px);
border-bottom: 1px solid rgba(255, 255, 255, 0.06);
padding: 12px 24px;
display: flex;
align-items: center;
justify-content: space-between;
position: sticky;
top: 0;
z-index: 100;
```

Logo in header: `height: 40px; width: auto`

---

## Tailwind CSS — Quick Reference Classes

If using Tailwind, these are the equivalent classes used across Hexadian apps:

| Element           | Tailwind Classes                                                                                     |
|-------------------|------------------------------------------------------------------------------------------------------|
| Root container    | `relative flex min-h-screen items-center justify-center bg-[#0f0f0f] bg-cover bg-center px-4`       |
| Overlay           | `absolute inset-0 bg-black/60`                                                                       |
| Centered wrapper  | `relative z-10 w-full max-w-md space-y-8`                                                           |
| Main logo         | `h-20 w-20`                                                                                          |
| Logo subtitle     | `text-sm text-[#888888]`                                                                             |
| Card              | `rounded-[14px] border border-white/[0.04] bg-[#1c1c1c] p-8 shadow-[0_10px_30px_rgba(0,0,0,0.45)]` |
| MBTC badge        | `fixed bottom-4 right-5 h-[100px] w-[100px]`                                                        |
| Card title        | `text-xl font-semibold text-[#e6eef6]`                                                               |
| Muted text        | `text-sm text-[#888888]`                                                                             |
| Very muted text   | `text-xs text-[#555555]`                                                                             |

---

## Implementation Checklist

- [ ] Copy `hxn_back.jpg`, `HEXADIAN-Background_Round.png`, `mbtc_black.png` to `public/brand/`
- [ ] Background with image + 60% black overlay
- [ ] Logo 80×80px centered, no box around it
- [ ] Muted subtitle below the logo
- [ ] Card with border-radius 14px, background `#1c1c1c`, subtle border, shadow
- [ ] MBTC badge fixed 100×100px in bottom-right corner
