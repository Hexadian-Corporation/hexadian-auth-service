# Hexadian UI Style Guide

Guía de referencia para aplicar el estilo corporativo de Hexadian Corporation a nuevas apps web.
Derivada de `hexadian-blueprints-old` y `hexadian-auth-service` (auth-portal, auth-backoffice).

---

## Assets requeridos

Coloca estos ficheros en `public/brand/` (o equivalente en tu stack):

| Fichero                          | Uso                                         |
|----------------------------------|---------------------------------------------|
| `hxn_back.jpg`                   | Imagen de fondo de pantalla completa        |
| `HEXADIAN-Background_Round.png`  | Logo principal redondo de Hexadian          |
| `mbtc_black.png`                 | Badge MBTC (esquina inferior derecha)       |

---

## Paleta de colores

| Token          | Hex / valor              | Uso                                  |
|----------------|--------------------------|--------------------------------------|
| `--bg`         | `#0f0f0f`                | Fondo base / fallback sin imagen     |
| `--card`       | `#1c1c1c`                | Fondo de tarjetas y modales          |
| `--accent`     | `#b8a96a`                | Botones primarios, highlights        |
| `--text`       | `#e6eef6`                | Texto principal                      |
| `--muted`      | `#888888`                | Texto secundario / subtítulos        |
| `--very-muted` | `#555555`                | Texto terciario / hints              |
| `--border`     | `rgba(255,255,255,0.04)` | Bordes de tarjetas                   |

---

## Estructura de pantalla de login / página centrada

```
┌────────────────────────────────────────────────┐
│  [fondo hxn_back.jpg + overlay negro 60%]      │
│                                                │
│           [Logo 80×80px]                       │
│        [Subtítulo muted]                       │
│  ┌──────────────────────────────┐              │
│  │         Tarjeta              │              │
│  │  (contenido del formulario)  │              │
│  └──────────────────────────────┘              │
│                                   [MBTC 100px] │
└────────────────────────────────────────────────┘
```

### Fondo
- Imagen de fondo a pantalla completa (`background-size: cover`, `background-position: center`)
- Overlay negro semitransparente encima: `rgba(0,0,0,0.6)`

### Logo principal
- Imagen `HEXADIAN-Background_Round.png`
- Tamaño: **80×80px**
- Centrado horizontalmente, sin caja ni sombra alrededor
- Separación inferior hasta el subtítulo: ~12px

### Subtítulo bajo el logo
- Texto pequeño (`font-size: 0.875rem` / `text-sm`)
- Color `#888888`
- Ejemplo: `"Hexadian Authentication Portal"`, `"Auth Backoffice"`

### Tarjeta de contenido
```css
border-radius: 14px;
border: 1px solid rgba(255, 255, 255, 0.04);
background: #1c1c1c;
padding: 32px;
box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
max-width: 448px;   /* ~max-w-md */
width: 100%;
```

### Badge MBTC
- Imagen `mbtc_black.png`
- Posición: **fija** (`position: fixed`), esquina **inferior derecha**
- `bottom: 16px`, `right: 20px`
- Tamaño: **100×100px**

---

## Tipografía

- Fuente: sistema (sans-serif por defecto, sin Google Fonts)
- Títulos de sección: `font-size: 1.25rem`, `font-weight: 600`, color `#e6eef6`
- Texto de formulario / body: `font-size: 0.875rem`, color `#e6eef6`
- Texto muted: color `#888888`
- Texto muy muted / hints: `font-size: 0.75rem`, color `#555555`

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

## Botones

### Primario
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

### Ghost / secundario
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

### Peligro / destructivo
```css
background: rgba(220, 38, 38, 0.15);
color: #f87171;
border: 1px solid rgba(220, 38, 38, 0.30);
```

---

## Header de app (si aplica)

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

Logo en header: `height: 40px; width: auto`

---

## Tailwind CSS — clases de referencia rápida

Si usas Tailwind, estas son las clases equivalentes usadas en auth-portal / auth-backoffice:

| Elemento          | Clases Tailwind                                                                                      |
|-------------------|------------------------------------------------------------------------------------------------------|
| Contenedor raíz   | `relative flex min-h-screen items-center justify-center bg-[#0f0f0f] bg-cover bg-center px-4`       |
| Overlay           | `absolute inset-0 bg-black/60`                                                                       |
| Wrapper centrado  | `relative z-10 w-full max-w-md space-y-8`                                                           |
| Logo principal    | `h-20 w-20`                                                                                          |
| Subtítulo logo    | `text-sm text-[#888888]`                                                                             |
| Tarjeta           | `rounded-[14px] border border-white/[0.04] bg-[#1c1c1c] p-8 shadow-[0_10px_30px_rgba(0,0,0,0.45)]` |
| Badge MBTC        | `fixed bottom-4 right-5 h-[100px] w-[100px]`                                                        |
| Título tarjeta    | `text-xl font-semibold text-[#e6eef6]`                                                               |
| Texto muted       | `text-sm text-[#888888]`                                                                             |
| Texto muy muted   | `text-xs text-[#555555]`                                                                             |

---

## Checklist de implementación

- [ ] Copiar `hxn_back.jpg`, `HEXADIAN-Background_Round.png`, `mbtc_black.png` a `public/brand/`
- [ ] Fondo con imagen + overlay negro 60%
- [ ] Logo 80×80px centrado, sin caja alrededor
- [ ] Subtítulo muted bajo el logo
- [ ] Tarjeta con border-radius 14px, fondo `#1c1c1c`, borde sutil, sombra
- [ ] Badge MBTC fijo 100×100px en esquina inferior derecha
