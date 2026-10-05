"""
Generador de Visualización Web Interactiva Premium para el Metro de Madrid.
Produce un archivo HTML 100% autónomo, moderno y responsive que incluye:
1. Mapa de red georreferenciado e interactivo con Vis.js.
2. Buscador inteligente de estaciones con autocompletado y zoom automático.
3. Leyenda oficial de líneas con filtro interactivo y aislamiento de líneas.
4. Calculador y visualizador de rutas óptimas (menor tiempo y menor número de transbordos) con itinerario paso a paso.
5. Simulador visual de resiliencia y fallos (cierre de estaciones completas o tramos de vía) con análisis de conectividad y rutas alternativas.
6. Modo oscuro unificado, diseño glassmorphism y cero dependencias locales rotas (todo vía CDN confiable).
"""

import json

# Diccionario oficial de colores del Metro de Madrid
COLORES_LINEAS = {
    '1': '#0097D6', 'L1': '#0097D6',
    '2': '#FF2A14', 'L2': '#FF2A14',
    '3': '#FFD100', 'L3': '#FFD100',
    '4': '#93351C', 'L4': '#93351C',
    '5': '#80C23D', 'L5': '#80C23D',
    '6': '#A8A9AD', 'L6': '#A8A9AD',
    '7': '#F68315', 'L7': '#F68315',
    '8': '#E35F92', 'L8': '#E35F92',
    '9': '#8B1E91', 'L9': '#8B1E91',
    '10': '#0039A6', 'L10': '#0039A6',
    '11': '#009139', 'L11': '#009139',
    '12': '#A19100', 'L12': '#A19100',
    'R': '#FFFFFF', 'LR': '#FFFFFF',
    'Transbordo': '#E2E8F0'
}

NOMBRES_LINEAS = {
    'L1': 'Línea 1 (Pinar de Chamartín - Valdecarros)',
    'L2': 'Línea 2 (Las Rosas - Cuatro Caminos)',
    'L3': 'Línea 3 (Villaverde Alto - Moncloa)',
    'L4': 'Línea 4 (Argüelles - Pinar de Chamartín)',
    'L5': 'Línea 5 (Alameda de Osuna - Casa de Campo)',
    'L6': 'Línea 6 (Circular)',
    'L7': 'Línea 7 (Hospital de Henares - Pitis)',
    'L8': 'Línea 8 (Nuevos Ministerios - Aeropuerto T4)',
    'L9': 'Línea 9 (Paco de Lucía - Arganda del Rey)',
    'L10': 'Línea 10 (Hospital Infanta Sofía - Puerta del Sur)',
    'L11': 'Línea 11 (Plaza Elíptica - La Fortuna)',
    'L12': 'Línea 12 (MetroSur)',
    'R': 'Ramal (Ópera - Príncipe Pío)'
}

def format_time_min_sec(decimal_minutes):
    if decimal_minutes is None or decimal_minutes == float('inf'):
        return "--:--"
    total_seconds = int(round(float(decimal_minutes) * 60))
    m = total_seconds // 60
    s = total_seconds % 60
    return f"{m}:{s:02d}"

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>__TITLE__</title>
    
    <!-- CDNs Estables y Seguros: Bootstrap 5, FontAwesome 6, Vis-Network 9.1.2, Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/dist/vis-network.min.css" />
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js"></script>

    <style>
        :root {
            --bg-canvas: #0b0f19;
            --bg-panel: rgba(15, 23, 42, 0.95);
            --bg-panel-subtle: rgba(30, 41, 59, 0.85);
            --border-subtle: rgba(255, 255, 255, 0.1);
            --border-active: rgba(0, 151, 214, 0.5);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --metro-red: #FF2A14;
            --metro-blue: #0097D6;
            --metro-accent: #00E5FF;
            --metro-green: #10b981;
            --metro-warning: #f59e0b;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg-canvas);
            color: var(--text-primary);
            overflow: hidden;
            height: 100vh;
            width: 100vw;
        }

        #mynetwork {
            position: absolute;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: radial-gradient(circle at 50% 50%, #131b2e 0%, #080c14 100%);
            z-index: 1;
        }

        /* Barra Superior Flotante */
        .top-navbar {
            position: fixed;
            top: 16px;
            left: 16px;
            right: 16px;
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 20px;
            background: var(--bg-panel);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid var(--border-subtle);
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
            pointer-events: auto;
        }

        .brand-section {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .brand-logo-rhombus {
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, #FF2A14 50%, #0097D6 50%);
            transform: rotate(45deg);
            border: 2px solid #FFFFFF;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 15px rgba(255, 42, 20, 0.4);
        }

        .brand-title {
            font-size: 1.15rem;
            font-weight: 700;
            letter-spacing: -0.3px;
            color: #ffffff;
            margin: 0;
            line-height: 1.2;
        }

        .brand-subtitle {
            font-size: 0.75rem;
            color: var(--text-secondary);
            font-weight: 400;
        }

        .kpi-badges {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .kpi-chip {
            display: flex;
            align-items: center;
            gap: 6px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-subtle);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.78rem;
            color: var(--text-secondary);
            font-weight: 500;
        }

        .kpi-chip b {
            color: #ffffff;
        }

        .top-actions {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-action {
            background: rgba(255, 255, 255, 0.07);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            padding: 7px 14px;
            border-radius: 10px;
            font-size: 0.82rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 7px;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .btn-action:hover {
            background: rgba(255, 255, 255, 0.15);
            border-color: rgba(255, 255, 255, 0.25);
            color: #ffffff;
            transform: translateY(-1px);
        }

        .btn-action.btn-reset {
            background: rgba(239, 68, 68, 0.15);
            border-color: rgba(239, 68, 68, 0.35);
            color: #fca5a5;
        }

        .btn-action.btn-reset:hover {
            background: rgba(239, 68, 68, 0.3);
            color: #ffffff;
        }

        /* Panel Lateral (Sidebar Drawer) */
        .sidebar-drawer {
            position: fixed;
            top: 86px;
            left: 16px;
            width: 440px;
            max-height: calc(100vh - 104px);
            z-index: 999;
            background: var(--bg-panel);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--border-subtle);
            border-radius: 18px;
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.3s ease;
        }

        .sidebar-drawer.collapsed {
            transform: translateX(-480px);
            opacity: 0;
            pointer-events: none;
        }

        /* Pestañas del Panel */
        .sidebar-tabs {
            display: flex;
            background: rgba(0, 0, 0, 0.3);
            border-bottom: 1px solid var(--border-subtle);
            padding: 6px;
            gap: 4px;
        }

        .sidebar-tab-btn {
            flex: 1;
            padding: 8px 4px;
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-size: 0.78rem;
            font-weight: 600;
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            transition: all 0.2s ease;
        }

        .sidebar-tab-btn i {
            font-size: 1rem;
        }

        .sidebar-tab-btn.active {
            background: rgba(0, 151, 214, 0.2);
            color: #00E5FF;
            border: 1px solid rgba(0, 229, 255, 0.3);
        }

        .sidebar-tab-btn:hover:not(.active) {
            background: rgba(255, 255, 255, 0.05);
            color: #ffffff;
        }

        .sidebar-tab-content {
            padding: 18px;
            overflow-y: auto;
            flex: 1;
            scrollbar-width: thin;
            scrollbar-color: rgba(255, 255, 255, 0.2) transparent;
        }

        .sidebar-tab-content::-webkit-scrollbar {
            width: 5px;
        }

        .sidebar-tab-content::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
        }

        .tab-pane {
            display: none;
        }

        .tab-pane.active {
            display: block;
            animation: fadeIn 0.25s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(4px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .search-box {
            position: relative;
            margin-bottom: 14px;
        }

        .search-input {
            width: 100%;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 10px 14px 10px 40px;
            color: #ffffff;
            font-size: 0.88rem;
            outline: none;
            transition: all 0.2s;
        }

        .search-input:focus {
            border-color: #00E5FF;
            box-shadow: 0 0 10px rgba(0, 229, 255, 0.25);
            background: rgba(0, 0, 0, 0.6);
        }

        .search-icon {
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            font-size: 0.95rem;
        }

        .autocomplete-dropdown {
            position: absolute;
            top: 105%;
            left: 0;
            right: 0;
            background: #0f172a;
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            max-height: 250px;
            overflow-y: auto;
            z-index: 1050;
            display: none;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.7);
        }

        .autocomplete-item {
            padding: 10px 14px;
            cursor: pointer;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: background 0.15s;
        }

        .autocomplete-item:hover {
            background: rgba(0, 151, 214, 0.2);
        }

        .station-card {
            background: var(--bg-panel-subtle);
            border: 1px solid var(--border-subtle);
            border-radius: 14px;
            padding: 16px;
            margin-top: 12px;
        }

        .station-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 12px;
        }

        .station-name {
            font-size: 1.25rem;
            font-weight: 700;
            color: #ffffff;
            line-height: 1.2;
        }

        .line-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 32px;
            height: 24px;
            padding: 0 8px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.76rem;
            color: #ffffff;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        }

        .station-meta-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
            margin: 12px 0;
        }

        .meta-pill {
            background: rgba(0, 0, 0, 0.25);
            padding: 8px 10px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.04);
        }

        .meta-pill-label {
            font-size: 0.7rem;
            color: var(--text-muted);
            text-transform: uppercase;
            font-weight: 600;
        }

        .meta-pill-val {
            font-size: 0.9rem;
            font-weight: 600;
            color: #ffffff;
        }

        .quick-actions-bar {
            display: flex;
            gap: 8px;
            margin-top: 12px;
        }

        .btn-quick {
            flex: 1;
            padding: 7px 6px;
            font-size: 0.75rem;
            border-radius: 8px;
            border: 1px solid var(--border-subtle);
            background: rgba(255, 255, 255, 0.05);
            color: #e2e8f0;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
            transition: all 0.2s;
        }

        .btn-quick:hover {
            background: rgba(255, 255, 255, 0.15);
            color: #ffffff;
        }

        .lines-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
            margin-top: 10px;
        }

        .line-card {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 10px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            transition: all 0.2s;
        }

        .line-card:hover {
            border-color: rgba(255, 255, 255, 0.3);
            background: rgba(255, 255, 255, 0.06);
            transform: translateY(-1px);
        }

        .line-card.active {
            border-color: #00E5FF;
            background: rgba(0, 229, 255, 0.15);
            box-shadow: 0 0 12px rgba(0, 229, 255, 0.2);
        }

        .form-label-custom {
            font-size: 0.78rem;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
            display: block;
        }

        .form-select-custom, .form-control-custom {
            width: 100%;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 9px 12px;
            color: #ffffff;
            font-size: 0.85rem;
            margin-bottom: 12px;
            outline: none;
        }

        .form-select-custom:focus, .form-control-custom:focus {
            border-color: #00E5FF;
            box-shadow: 0 0 8px rgba(0, 229, 255, 0.25);
        }

        .btn-calc {
            width: 100%;
            padding: 11px;
            background: linear-gradient(135deg, #0097D6, #005691);
            color: #ffffff;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            box-shadow: 0 4px 15px rgba(0, 151, 214, 0.3);
            transition: all 0.2s;
        }

        .btn-calc:hover {
            background: linear-gradient(135deg, #00b0f0, #006eb8);
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(0, 151, 214, 0.45);
        }

        .btn-danger-custom {
            width: 100%;
            padding: 11px;
            background: linear-gradient(135deg, #FF2A14, #b91c1c);
            color: #ffffff;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.88rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            box-shadow: 0 4px 15px rgba(255, 42, 20, 0.3);
            transition: all 0.2s;
        }

        .btn-danger-custom:hover {
            background: linear-gradient(135deg, #ff4433, #dc2626);
            transform: translateY(-1px);
        }

        .route-summary-card {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 12px;
            padding: 12px;
            margin: 14px 0;
        }

        .route-timeline {
            margin-top: 14px;
            position: relative;
            padding-left: 20px;
        }

        .route-timeline::before {
            content: '';
            position: absolute;
            top: 8px;
            bottom: 8px;
            left: 6px;
            width: 2px;
            background: rgba(255, 255, 255, 0.15);
        }

        .timeline-step {
            position: relative;
            margin-bottom: 14px;
        }

        .timeline-step::before {
            content: '';
            position: absolute;
            left: -18px;
            top: 4px;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #00E5FF;
            border: 2px solid #0f172a;
        }

        .timeline-step.transfer::before {
            background: #f59e0b;
        }

        .timeline-step.destination::before {
            background: #ef4444;
        }

        .step-title {
            font-size: 0.85rem;
            font-weight: 600;
            color: #ffffff;
        }

        .step-desc {
            font-size: 0.76rem;
            color: var(--text-secondary);
        }

        .btn-toggle-sidebar {
            position: fixed;
            top: 96px;
            left: 468px;
            z-index: 1000;
            width: 36px;
            height: 36px;
            background: var(--bg-panel);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.4);
            transition: all 0.3s;
        }

        .btn-toggle-sidebar.collapsed {
            left: 16px;
        }

        .btn-toggle-sidebar:hover {
            background: rgba(255, 255, 255, 0.15);
            color: #ffffff;
        }

        div.vis-tooltip {
            background-color: #0f172a !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 8px !important;
            padding: 8px 12px !important;
            font-family: 'Outfit', sans-serif !important;
            font-size: 12px !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6) !important;
            z-index: 10000 !important;
        }

        .failure-alert-box {
            padding: 12px;
            border-radius: 10px;
            margin-top: 12px;
            font-size: 0.82rem;
            line-height: 1.4;
        }

        .failure-alert-box.connected {
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.4);
            color: #6ee7b7;
        }

        .failure-alert-box.disconnected {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.4);
            color: #fca5a5;
        }
    </style>
</head>
<body>

    <div id="mynetwork"></div>

    <header class="top-navbar">
        <div class="brand-section">
            <div class="brand-logo-rhombus"></div>
            <div>
                <h1 class="brand-title">Metro de Madrid</h1>
                <div class="brand-subtitle">Red Georreferenciada &amp; Análisis de Grafos</div>
            </div>
        </div>

        <div class="kpi-badges d-none d-lg-flex">
            <div class="kpi-chip"><i class="fa-solid fa-code-branch text-info"></i> <span><b>__NODES_COUNT__</b> Andenes</span></div>
            <div class="kpi-chip"><i class="fa-solid fa-location-dot text-danger"></i> <span><b>__STATIONS_COUNT__</b> Estaciones</span></div>
            <div class="kpi-chip"><i class="fa-solid fa-train text-warning"></i> <span><b>13</b> Líneas</span></div>
            <div class="kpi-chip"><i class="fa-solid fa-arrows-split-up-and-left text-success"></i> <span><b>__EDGES_COUNT__</b> Tramos</span></div>
        </div>

        <div class="top-actions">
            <button class="btn-action" onclick="resetNetworkView()" title="Centrar todo el mapa"><i class="fa-solid fa-crosshairs"></i> <span class="d-none d-sm-inline">Centrar</span></button>
            <button class="btn-action btn-reset" onclick="resetAllState()" title="Restablecer filtros, rutas y simulaciones"><i class="fa-solid fa-rotate-left"></i> <span class="d-none d-sm-inline">Restablecer</span></button>
            <button class="btn-action" onclick="toggleFullscreen()" title="Pantalla completa"><i class="fa-solid fa-expand"></i></button>
        </div>
    </header>

    <button id="toggle-sidebar-btn" class="btn-toggle-sidebar" onclick="toggleSidebar()" title="Mostrar/Ocultar Panel">
        <i class="fa-solid fa-chevron-left" id="toggle-sidebar-icon"></i>
    </button>

    <aside id="sidebar-drawer" class="sidebar-drawer">
        <nav class="sidebar-tabs">
            <button class="sidebar-tab-btn active" onclick="switchTab('tab-stations')">
                <i class="fa-solid fa-magnifying-glass"></i>
                <span>Estaciones</span>
            </button>
            <button class="sidebar-tab-btn" onclick="switchTab('tab-lines')">
                <i class="fa-solid fa-layer-group"></i>
                <span>Líneas</span>
            </button>
            <button class="sidebar-tab-btn" onclick="switchTab('tab-routes')">
                <i class="fa-solid fa-route"></i>
                <span>Rutas</span>
            </button>
            <button class="sidebar-tab-btn" onclick="switchTab('tab-simulate')">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <span>Simulador</span>
            </button>
        </nav>

        <div class="sidebar-tab-content">

            <!-- PESTAÑA 1: ESTACIONES & BÚSQUEDA -->
            <div id="tab-stations" class="tab-pane active">
                <div class="search-box">
                    <i class="fa-solid fa-magnifying-glass search-icon"></i>
                    <input type="text" id="station-search" class="search-input" placeholder="Buscar estación (ej. Sol, Atocha, Gran Vía)..." oninput="handleStationSearch(this.value)">
                    <div id="station-autocomplete" class="autocomplete-dropdown"></div>
                </div>

                <div id="station-details-placeholder" class="text-center py-4" style="color: var(--text-muted);">
                    <i class="fa-solid fa-train-subway fa-2x mb-2" style="opacity: 0.3;"></i>
                    <p class="mb-0" style="font-size: 0.85rem;">Haz clic en cualquier andén del mapa o busca una estación arriba para ver sus detalles y conexiones.</p>
                </div>

                <div id="station-card" class="station-card" style="display: none;">
                    <div class="station-header">
                        <div>
                            <h3 id="card-station-name" class="station-name">Nombre Estación</h3>
                            <div class="text-muted" style="font-size: 0.75rem;">Estación de la red de Metro de Madrid</div>
                        </div>
                        <div id="card-station-lines" class="d-flex flex-wrap gap-1"></div>
                    </div>

                    <div class="station-meta-grid">
                        <div class="meta-pill">
                            <div class="meta-pill-label">Andenes / Vías</div>
                            <div id="card-station-platforms" class="meta-pill-val">0</div>
                        </div>
                        <div class="meta-pill">
                            <div class="meta-pill-label">Conexiones Directas</div>
                            <div id="card-station-degree" class="meta-pill-val">0</div>
                        </div>
                        <div class="meta-pill">
                            <div class="meta-pill-label">Latitud</div>
                            <div id="card-station-lat" class="meta-pill-val" style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">--</div>
                        </div>
                        <div class="meta-pill">
                            <div class="meta-pill-label">Longitud</div>
                            <div id="card-station-lon" class="meta-pill-val" style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">--</div>
                        </div>
                    </div>

                    <div style="margin-top: 10px;">
                        <span class="form-label-custom">Andenes y Transbordos:</span>
                        <div id="card-station-nodes-list" class="d-flex flex-column gap-1" style="font-size: 0.8rem;"></div>
                    </div>

                    <div class="quick-actions-bar">
                        <button class="btn-quick" onclick="setAsRouteOrigin()"><i class="fa-solid fa-circle-dot text-success"></i> Fijar Origen</button>
                        <button class="btn-quick" onclick="setAsRouteDest()"><i class="fa-solid fa-location-dot text-danger"></i> Fijar Destino</button>
                        <button class="btn-quick" onclick="simulateCurrentStationClosure()"><i class="fa-solid fa-ban text-warning"></i> Simular Cierre</button>
                    </div>
                </div>
            </div>

            <!-- PESTAÑA 2: LÍNEAS Y LEYENDA -->
            <div id="tab-lines" class="tab-pane">
                <div class="d-flex align-items-center justify-content-between mb-2">
                    <span class="form-label-custom mb-0">Filtro por Línea Oficial</span>
                    <button class="btn btn-sm btn-link text-info text-decoration-none p-0" style="font-size: 0.78rem;" onclick="filterLine('ALL')">Mostrar Todas</button>
                </div>
                <p style="font-size: 0.78rem; color: var(--text-secondary); margin-bottom: 12px;">
                    Haz clic en una línea para aislarla en el mapa. Las demás líneas se atenuarán.
                </p>

                <div id="lines-container" class="lines-grid"></div>
            </div>

            <!-- PESTAÑA 3: CALCULADOR DE RUTAS -->
            <div id="tab-routes" class="tab-pane">
                <div class="mb-3">
                    <label class="form-label-custom">Estación Origen</label>
                    <select id="route-origin" class="form-select-custom"></select>
                </div>

                <div class="d-flex justify-content-center my-1">
                    <button class="btn btn-sm" style="background: rgba(255,255,255,0.08); color: var(--metro-accent); border: 1px solid var(--border-subtle); border-radius: 50%; width: 32px; height: 32px;" onclick="swapRouteStations()" title="Invertir origen y destino">
                        <i class="fa-solid fa-arrow-down-up-across-line"></i>
                    </button>
                </div>

                <div class="mb-3">
                    <label class="form-label-custom">Estación Destino</label>
                    <select id="route-dest" class="form-select-custom"></select>
                </div>

                <div class="mb-3">
                    <label class="form-label-custom">Criterio de Búsqueda</label>
                    <div class="d-flex gap-2">
                        <label class="btn-quick flex-fill" style="cursor: pointer;">
                            <input type="radio" name="route-criteria" value="time" checked class="me-1"> Menor Tiempo
                        </label>
                        <label class="btn-quick flex-fill" style="cursor: pointer;">
                            <input type="radio" name="route-criteria" value="transfers" class="me-1"> Menos Transbordos
                        </label>
                    </div>
                </div>

                <button class="btn-calc" onclick="calculateAndDisplayRoute()">
                    <i class="fa-solid fa-diamond-turn-right"></i> Calcular Ruta Óptima
                </button>

                <div id="route-results-container" style="display: none;">
                    <div id="route-summary" class="route-summary-card"></div>

                    <div class="d-flex justify-content-between align-items-center mt-3">
                        <span class="form-label-custom mb-0">Itinerario Paso a Paso</span>
                        <button class="btn btn-sm btn-link text-danger text-decoration-none p-0" style="font-size: 0.78rem;" onclick="clearRouteHighlight()">Limpiar Ruta</button>
                    </div>

                    <div id="route-steps" class="route-timeline"></div>
                </div>
            </div>

            <!-- PESTAÑA 4: SIMULADOR DE FALLOS Y RESILIENCIA -->
            <div id="tab-simulate" class="tab-pane">
                <div class="mb-3">
                    <label class="form-label-custom">Tipo de Simulación</label>
                    <div class="d-flex gap-2">
                        <label class="btn-quick flex-fill" style="cursor: pointer;">
                            <input type="radio" name="sim-mode" value="station" checked onchange="toggleSimMode(this.value)" class="me-1"> Cierre Estación
                        </label>
                        <label class="btn-quick flex-fill" style="cursor: pointer;">
                            <input type="radio" name="sim-mode" value="edge" onchange="toggleSimMode(this.value)" class="me-1"> Corte de Tramo
                        </label>
                    </div>
                </div>

                <div id="sim-station-controls">
                    <div class="mb-3">
                        <label class="form-label-custom">Seleccionar Estación a Clausurar</label>
                        <select id="sim-station-select" class="form-select-custom"></select>
                    </div>
                    <button class="btn-danger-custom" onclick="simulateStationRemoval()">
                        <i class="fa-solid fa-triangle-exclamation"></i> Simular Cierre de Estación
                    </button>
                </div>

                <div id="sim-edge-controls" style="display: none;">
                    <div class="mb-2">
                        <label class="form-label-custom">Estación A del Tramo</label>
                        <select id="sim-edge-u" class="form-select-custom" onchange="updateSimEdgeTargets()"></select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label-custom">Estación B Conectada</label>
                        <select id="sim-edge-v" class="form-select-custom"></select>
                    </div>
                    <button class="btn-danger-custom" onclick="simulateEdgeRemoval()">
                        <i class="fa-solid fa-scissors"></i> Simular Corte de Tramo
                    </button>
                </div>

                <div id="sim-results" style="display: none;">
                    <div id="sim-alert" class="failure-alert-box mt-3"></div>
                    <div id="sim-details" style="font-size: 0.8rem; margin-top: 10px; color: var(--text-secondary);"></div>
                    <button class="btn-action w-100 justify-content-center mt-3" onclick="resetAllState()">
                        <i class="fa-solid fa-wrench"></i> Restablecer Red Completa
                    </button>
                </div>
            </div>

        </div>
    </aside>

    <script>
        const rawNodes = __NODES_JSON__;
        const rawEdges = __EDGES_JSON__;
        const physicalStations = __STATIONS_JSON__;
        const linesSummary = __LINES_JSON__;
        const lineColors = __LINE_COLORS_JSON__;

        let network = null;
        let nodesDataSet = null;
        let edgesDataSet = null;
        let selectedStationData = null;
        let activeRoutePath = null;
        let activeLineFilter = 'ALL';

        const nodeMap = new Map();
        rawNodes.forEach(n => nodeMap.set(n.id, n));

        const edgeMap = new Map();
        rawEdges.forEach(e => edgeMap.set(e.id, e));

        const stationMap = new Map();
        physicalStations.forEach(s => stationMap.set(s.nombre, s));

        window.addEventListener('DOMContentLoaded', () => {
            initVisNetwork();
            populateUISelects();
            renderLinesLegend();
        });

        function initVisNetwork() {
            const container = document.getElementById('mynetwork');

            nodesDataSet = new vis.DataSet(rawNodes.map(n => ({
                id: n.id,
                label: n.label,
                x: n.x,
                y: n.y,
                size: n.size,
                color: {
                    background: n.color,
                    border: '#FFFFFF',
                    highlight: {
                        background: '#FFFFFF',
                        border: n.color
                    }
                },
                shape: 'dot',
                borderWidth: 2,
                borderWidthSelected: 4,
                font: {
                    size: 13,
                    color: '#ffffff',
                    strokeWidth: 2,
                    strokeColor: '#000000',
                    face: 'Outfit, sans-serif'
                },
                title: `<div style="font-family: Outfit, sans-serif; padding: 4px;">
                            <strong style="color: #00E5FF; font-size: 14px;">${n.nombre}</strong><br>
                            Línea: <b>${n.linea}</b><br>
                            Conexiones directas: ${n.grado}<br>
                            <span style="font-size: 11px; color: #94a3b8;">Clic para ver detalles</span>
                        </div>`
            })));

            edgesDataSet = new vis.DataSet(rawEdges.map(e => ({
                id: e.id,
                from: e.from,
                to: e.to,
                color: {
                    color: e.color,
                    highlight: '#00E5FF',
                    hover: '#FFFFFF'
                },
                width: e.width,
                dashes: e.dashes,
                title: `<div style="font-family: Outfit, sans-serif; padding: 3px;">
                            ${e.title}
                        </div>`
            })));

            const data = {
                nodes: nodesDataSet,
                edges: edgesDataSet
            };

            const options = {
                physics: {
                    enabled: false
                },
                interaction: {
                    hover: true,
                    tooltipDelay: 120,
                    zoomView: true,
                    dragView: true,
                    multiselect: false
                },
                edges: {
                    smooth: false
                }
            };

            network = new vis.Network(container, data, options);

            network.on('click', function(params) {
                if (params.nodes && params.nodes.length > 0) {
                    const nodeId = params.nodes[0];
                    const node = nodeMap.get(nodeId);
                    if (node) {
                        const station = stationMap.get(node.nombre);
                        if (station) {
                            displayStationDetails(station);
                            switchTab('tab-stations');
                        }
                    }
                }
            });
        }

        function populateUISelects() {
            const originSelect = document.getElementById('route-origin');
            const destSelect = document.getElementById('route-dest');
            const simStationSelect = document.getElementById('sim-station-select');
            const simEdgeUSelect = document.getElementById('sim-edge-u');

            physicalStations.forEach(st => {
                const opt1 = new Option(st.nombre, st.nombre);
                const opt2 = new Option(st.nombre, st.nombre);
                const opt3 = new Option(st.nombre, st.nombre);
                const opt4 = new Option(st.nombre, st.nombre);

                originSelect.add(opt1);
                destSelect.add(opt2);
                simStationSelect.add(opt3);
                simEdgeUSelect.add(opt4);
            });

            if (stationMap.has('Sol')) originSelect.value = 'Sol';
            if (stationMap.has('Nuevos Ministerios')) destSelect.value = 'Nuevos Ministerios';

            updateSimEdgeTargets();
        }

        function renderLinesLegend() {
            const container = document.getElementById('lines-container');
            container.innerHTML = '';

            linesSummary.forEach(l => {
                const card = document.createElement('div');
                card.className = 'line-card';
                card.id = `line-btn-${l.code}`;
                card.onclick = () => toggleLineFilter(l.code);

                const textColor = (l.code === '3' || l.code === 'R') ? '#000000' : '#FFFFFF';

                card.innerHTML = `
                    <div class="d-flex align-items-center gap-2">
                        <span class="line-badge" style="background-color: ${l.color}; color: ${textColor};">${l.code}</span>
                        <div style="font-size: 0.8rem; font-weight: 500; color: #ffffff;">${l.code === 'R' ? 'Ramal' : 'Línea ' + l.code.replace('L','')}</div>
                    </div>
                    <span style="font-size: 0.72rem; color: var(--text-muted);">${l.station_count} and.</span>
                `;
                container.appendChild(card);
            });
        }

        function switchTab(tabId) {
            document.querySelectorAll('.sidebar-tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));

            const targetPane = document.getElementById(tabId);
            if (targetPane) targetPane.classList.add('active');

            const tabMap = {
                'tab-stations': 0,
                'tab-lines': 1,
                'tab-routes': 2,
                'tab-simulate': 3
            };
            const buttons = document.querySelectorAll('.sidebar-tab-btn');
            if (buttons[tabMap[tabId]]) {
                buttons[tabMap[tabId]].classList.add('active');
            }

            const sidebar = document.getElementById('sidebar-drawer');
            if (sidebar.classList.contains('collapsed')) {
                toggleSidebar();
            }
        }

        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar-drawer');
            const toggleBtn = document.getElementById('toggle-sidebar-btn');
            const icon = document.getElementById('toggle-sidebar-icon');

            sidebar.classList.toggle('collapsed');
            toggleBtn.classList.toggle('collapsed');

            if (sidebar.classList.contains('collapsed')) {
                icon.className = 'fa-solid fa-chevron-right';
            } else {
                icon.className = 'fa-solid fa-chevron-left';
            }
        }

        function handleStationSearch(query) {
            const dropdown = document.getElementById('station-autocomplete');
            if (!query || query.trim().length === 0) {
                dropdown.style.display = 'none';
                return;
            }

            const q = query.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
            const matches = physicalStations.filter(st => {
                const norm = st.nombre.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                return norm.includes(q);
            }).slice(0, 10);

            if (matches.length === 0) {
                dropdown.style.display = 'none';
                return;
            }

            dropdown.innerHTML = '';
            matches.forEach(st => {
                const item = document.createElement('div');
                item.className = 'autocomplete-item';
                
                const badgesHtml = st.lineas.map(l => {
                    const bg = lineColors[l] || '#0097D6';
                    const fg = (l === '3' || l === 'R') ? '#000000' : '#FFFFFF';
                    return `<span class="line-badge" style="background-color: ${bg}; color: ${fg}; font-size: 0.65rem; height: 18px; min-width: 24px; padding: 0 4px;">${l}</span>`;
                }).join(' ');

                item.innerHTML = `
                    <div style="font-weight: 500; font-size: 0.85rem; color: #ffffff;">${st.nombre}</div>
                    <div class="d-flex gap-1">${badgesHtml}</div>
                `;
                item.onclick = () => {
                    displayStationDetails(st);
                    focusOnStation(st);
                    dropdown.style.display = 'none';
                    document.getElementById('station-search').value = st.nombre;
                };
                dropdown.appendChild(item);
            });
            dropdown.style.display = 'block';
        }

        function displayStationDetails(station) {
            selectedStationData = station;
            document.getElementById('station-details-placeholder').style.display = 'none';
            const card = document.getElementById('station-card');
            card.style.display = 'block';

            document.getElementById('card-station-name').innerText = station.nombre;
            document.getElementById('card-station-platforms').innerText = station.nodos.length;
            document.getElementById('card-station-lat').innerText = station.lat.toFixed(5);
            document.getElementById('card-station-lon').innerText = station.lon.toFixed(5);

            let totalDegree = 0;
            station.nodos.forEach(nid => {
                const n = nodeMap.get(nid);
                if (n) totalDegree += n.grado;
            });
            document.getElementById('card-station-degree').innerText = totalDegree;

            const linesContainer = document.getElementById('card-station-lines');
            linesContainer.innerHTML = '';
            station.lineas.forEach(l => {
                const badge = document.createElement('span');
                badge.className = 'line-badge';
                badge.style.backgroundColor = lineColors[l] || '#0097D6';
                badge.style.color = (l === '3' || l === 'R') ? '#000000' : '#FFFFFF';
                badge.innerText = l;
                linesContainer.appendChild(badge);
            });

            const nodesList = document.getElementById('card-station-nodes-list');
            nodesList.innerHTML = '';
            station.nodos.forEach(nid => {
                const n = nodeMap.get(nid);
                const bg = lineColors[n.linea] || '#0097D6';
                const fg = (n.linea === '3' || n.linea === 'R') ? '#000000' : '#FFFFFF';
                
                const item = document.createElement('div');
                item.className = 'd-flex align-items-center justify-content-between p-2 rounded';
                item.style.background = 'rgba(0,0,0,0.2)';
                item.innerHTML = `
                    <div class="d-flex align-items-center gap-2">
                        <span class="line-badge" style="background-color: ${bg}; color: ${fg}; font-size: 0.65rem; height: 18px; min-width: 24px; padding: 0 4px;">${n.linea}</span>
                        <span style="color: #e2e8f0;">${nid}</span>
                    </div>
                    <button class="btn btn-sm btn-link text-info p-0 text-decoration-none" onclick="focusOnNode('${nid}')">
                        <i class="fa-solid fa-magnifying-glass-plus"></i> Ver
                    </button>
                `;
                nodesList.appendChild(item);
            });
        }

        function focusOnStation(station) {
            if (station && station.nodos.length > 0) {
                network.fit({
                    nodes: station.nodos,
                    animation: {
                        duration: 600,
                        easingFunction: 'easeInOutQuad'
                    }
                });
            }
        }

        function focusOnNode(nodeId) {
            network.focus(nodeId, {
                scale: 1.4,
                animation: {
                    duration: 500,
                    easingFunction: 'easeInOutQuad'
                }
            });
        }

        function setAsRouteOrigin() {
            if (!selectedStationData) return;
            document.getElementById('route-origin').value = selectedStationData.nombre;
            switchTab('tab-routes');
        }

        function setAsRouteDest() {
            if (!selectedStationData) return;
            document.getElementById('route-dest').value = selectedStationData.nombre;
            switchTab('tab-routes');
        }

        function simulateCurrentStationClosure() {
            if (!selectedStationData) return;
            document.getElementById('sim-station-select').value = selectedStationData.nombre;
            switchTab('tab-simulate');
            document.querySelector('input[name="sim-mode"][value="station"]').checked = true;
            toggleSimMode('station');
            simulateStationRemoval();
        }

        function toggleLineFilter(lineCode) {
            if (activeLineFilter === lineCode) {
                filterLine('ALL');
            } else {
                filterLine(lineCode);
            }
        }

        function filterLine(lineCode) {
            activeLineFilter = lineCode;

            document.querySelectorAll('.line-card').forEach(c => c.classList.remove('active'));
            if (lineCode !== 'ALL') {
                const activeCard = document.getElementById(`line-btn-${lineCode}`);
                if (activeCard) activeCard.classList.add('active');
            }

            if (lineCode === 'ALL') {
                const nodeUpdates = rawNodes.map(n => ({
                    id: n.id,
                    color: {
                        background: n.color,
                        border: '#FFFFFF'
                    },
                    font: { color: '#ffffff' }
                }));
                const edgeUpdates = rawEdges.map(e => ({
                    id: e.id,
                    color: { color: e.color },
                    width: e.width
                }));
                nodesDataSet.update(nodeUpdates);
                edgesDataSet.update(edgeUpdates);
                return;
            }

            const matchingNodes = [];
            const nodeUpdates = rawNodes.map(n => {
                const isMatch = (n.linea === lineCode);
                if (isMatch) matchingNodes.push(n.id);
                return {
                    id: n.id,
                    color: isMatch ? { background: n.color, border: '#FFFFFF' } : { background: '#1e293b', border: '#334155' },
                    font: { color: isMatch ? '#ffffff' : 'transparent' }
                };
            });

            const edgeUpdates = rawEdges.map(e => {
                const isMatch = (e.linea === lineCode);
                return {
                    id: e.id,
                    color: isMatch ? { color: e.color } : { color: 'rgba(255,255,255,0.04)' },
                    width: isMatch ? 4.5 : 1
                };
            });

            nodesDataSet.update(nodeUpdates);
            edgesDataSet.update(edgeUpdates);

            if (matchingNodes.length > 0) {
                network.fit({
                    nodes: matchingNodes,
                    animation: { duration: 700 }
                });
            }
        }

        function swapRouteStations() {
            const origin = document.getElementById('route-origin');
            const dest = document.getElementById('route-dest');
            const temp = origin.value;
            origin.value = dest.value;
            dest.value = temp;
        }

        function dijkstraMetro(startNodeIds, endNodeIds, transferPenalty = 0, excludedNodes = new Set(), excludedEdges = new Set()) {
            const dist = new Map();
            const prev = new Map();
            const prevEdge = new Map();
            const pq = new Set();

            rawNodes.forEach(n => {
                if (!excludedNodes.has(n.id)) {
                    dist.set(n.id, Infinity);
                    pq.add(n.id);
                }
            });

            startNodeIds.forEach(id => {
                if (!excludedNodes.has(id)) dist.set(id, 0);
            });

            const adj = new Map();
            rawNodes.forEach(n => adj.set(n.id, []));
            rawEdges.forEach(e => {
                if (!excludedEdges.has(e.id) && !excludedNodes.has(e.from) && !excludedNodes.has(e.to)) {
                    adj.get(e.from).push(e);
                    adj.get(e.to).push(e);
                }
            });

            while (pq.size > 0) {
                let u = null;
                let minDist = Infinity;
                pq.forEach(id => {
                    if (dist.get(id) < minDist) {
                        minDist = dist.get(id);
                        u = id;
                    }
                });

                if (u === null || minDist === Infinity) break;
                if (endNodeIds.includes(u)) {
                    const pathNodes = [];
                    const pathEdges = [];
                    let curr = u;
                    while (curr) {
                        pathNodes.unshift(curr);
                        const pe = prevEdge.get(curr);
                        if (pe) pathEdges.unshift(pe);
                        curr = prev.get(curr);
                    }
                    return {
                        targetNode: u,
                        totalCost: dist.get(u),
                        pathNodes,
                        pathEdges
                    };
                }

                pq.delete(u);

                const edges = adj.get(u) || [];
                for (const e of edges) {
                    const v = (e.from === u) ? e.to : e.from;
                    if (!pq.has(v)) continue;

                    let cost = e.tiempo;
                    if (e.tipo === 'transbordo') {
                        cost += transferPenalty;
                    }

                    const alt = dist.get(u) + cost;
                    if (alt < dist.get(v)) {
                        dist.set(v, alt);
                        prev.set(v, u);
                        prevEdge.set(v, e);
                    }
                }
            }

            return null;
        }

        function calculateAndDisplayRoute() {
            const originName = document.getElementById('route-origin').value;
            const destName = document.getElementById('route-dest').value;

            if (originName === destName) {
                alert("Por favor selecciona estaciones de origen y destino diferentes.");
                return;
            }

            const originStation = stationMap.get(originName);
            const destStation = stationMap.get(destName);
            if (!originStation || !destStation) return;

            const criteria = document.querySelector('input[name="route-criteria"]:checked').value;
            const transferPenalty = (criteria === 'transfers') ? 1000 : 0;

            const result = dijkstraMetro(originStation.nodos, destStation.nodos, transferPenalty);
            if (!result) {
                alert("No fue posible encontrar una ruta disponible entre estas estaciones.");
                return;
            }

            activeRoutePath = result;

            let totalTrainTime = 0;
            let totalWalkTime = 0;
            let transferCount = 0;

            result.pathEdges.forEach(e => {
                if (e.tipo === 'transbordo') {
                    totalWalkTime += e.tiempo;
                    transferCount++;
                } else {
                    totalTrainTime += e.tiempo;
                }
            });

            const totalTime = totalTrainTime + totalWalkTime;

            const pathNodeSet = new Set(result.pathNodes);
            const pathEdgeSet = new Set(result.pathEdges.map(e => e.id));

            const nodeUpdates = rawNodes.map(n => {
                const isPath = pathNodeSet.has(n.id);
                if (isPath) {
                    const isStart = (n.id === result.pathNodes[0]);
                    const isEnd = (n.id === result.pathNodes[result.pathNodes.length - 1]);
                    return {
                        id: n.id,
                        size: isStart || isEnd ? 30 : 24,
                        color: {
                            background: isStart ? '#FFFF00' : (isEnd ? '#FF2A14' : '#00FF66'),
                            border: '#FFFFFF'
                        },
                        font: { color: '#FFFFFF', size: 14, strokeWidth: 3 }
                    };
                } else {
                    return {
                        id: n.id,
                        color: { background: '#1e293b', border: '#334155' },
                        font: { color: 'transparent' }
                    };
                }
            });

            const edgeUpdates = rawEdges.map(e => {
                const isPath = pathEdgeSet.has(e.id);
                return {
                    id: e.id,
                    color: isPath ? { color: '#00FF66' } : { color: 'rgba(255,255,255,0.03)' },
                    width: isPath ? 6 : 1
                };
            });

            nodesDataSet.update(nodeUpdates);
            edgesDataSet.update(edgeUpdates);

            network.fit({
                nodes: result.pathNodes,
                animation: { duration: 700 }
            });

            const formatTime = (min) => {
                const m = Math.floor(min);
                const s = Math.round((min - m) * 60);
                return `${m} min ${s < 10 ? '0' : ''}${s} seg`;
            };

            const summaryContainer = document.getElementById('route-summary');
            summaryContainer.innerHTML = `
                <div class="d-flex align-items-center justify-content-between mb-2">
                    <span style="font-weight: 700; color: #10b981; font-size: 1.05rem;">
                        <i class="fa-solid fa-clock"></i> ${formatTime(totalTime)}
                    </span>
                    <span class="badge bg-success">${criteria === 'transfers' ? 'Menos Transbordos' : 'Ruta Más Rápida'}</span>
                </div>
                <div class="row g-2 text-center" style="font-size: 0.76rem;">
                    <div class="col-4">
                        <div class="p-1 rounded" style="background: rgba(0,0,0,0.2);">
                            <span class="text-muted d-block">Tren</span>
                            <b class="text-white">${totalTrainTime.toFixed(1)} min</b>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="p-1 rounded" style="background: rgba(0,0,0,0.2);">
                            <span class="text-muted d-block">Transbordos</span>
                            <b class="text-white">${transferCount} (${totalWalkTime.toFixed(1)} min)</b>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="p-1 rounded" style="background: rgba(0,0,0,0.2);">
                            <span class="text-muted d-block">Paradas</span>
                            <b class="text-white">${result.pathNodes.length - transferCount}</b>
                        </div>
                    </div>
                </div>
            `;

            const stepsContainer = document.getElementById('route-steps');
            stepsContainer.innerHTML = '';

            result.pathNodes.forEach((nid, idx) => {
                const node = nodeMap.get(nid);
                const isStart = (idx === 0);
                const isEnd = (idx === result.pathNodes.length - 1);

                if (isStart) {
                    const step = document.createElement('div');
                    step.className = 'timeline-step';
                    step.innerHTML = `
                        <div class="step-title">🟢 Iniciar viaje en ${node.nombre}</div>
                        <div class="step-desc">Subir al andén de la <b>Línea ${node.linea}</b></div>
                    `;
                    stepsContainer.appendChild(step);
                    return;
                }

                const incomingEdge = result.pathEdges[idx - 1];
                if (incomingEdge && incomingEdge.tipo === 'transbordo') {
                    const step = document.createElement('div');
                    step.className = 'timeline-step transfer';
                    step.innerHTML = `
                        <div class="step-title">🚶 Transbordo en ${node.nombre}</div>
                        <div class="step-desc">Pasillo peatonal hacia <b>Línea ${node.linea}</b> (~${incomingEdge.tiempo_str} min)</div>
                    `;
                    stepsContainer.appendChild(step);
                }

                if (isEnd) {
                    const step = document.createElement('div');
                    step.className = 'timeline-step destination';
                    step.innerHTML = `
                        <div class="step-title">🏁 Llegada a ${node.nombre}</div>
                        <div class="step-desc">Fin de trayecto en Línea ${node.linea}</div>
                    `;
                    stepsContainer.appendChild(step);
                }
            });

            document.getElementById('route-results-container').style.display = 'block';
        }

        function clearRouteHighlight() {
            activeRoutePath = null;
            document.getElementById('route-results-container').style.display = 'none';
            filterLine('ALL');
        }

        function toggleSimMode(mode) {
            if (mode === 'station') {
                document.getElementById('sim-station-controls').style.display = 'block';
                document.getElementById('sim-edge-controls').style.display = 'none';
            } else {
                document.getElementById('sim-station-controls').style.display = 'none';
                document.getElementById('sim-edge-controls').style.display = 'block';
                updateSimEdgeTargets();
            }
            document.getElementById('sim-results').style.display = 'none';
        }

        function updateSimEdgeTargets() {
            const uStationName = document.getElementById('sim-edge-u').value;
            const vSelect = document.getElementById('sim-edge-v');
            vSelect.innerHTML = '';

            const uStation = stationMap.get(uStationName);
            if (!uStation) return;

            const neighborStations = new Set();
            rawEdges.forEach(e => {
                if (e.tipo === 'via') {
                    const uNode = nodeMap.get(e.from);
                    const vNode = nodeMap.get(e.to);
                    if (uNode && vNode) {
                        if (uNode.nombre === uStationName && vNode.nombre !== uStationName) {
                            neighborStations.add(vNode.nombre);
                        } else if (vNode.nombre === uStationName && uNode.nombre !== uStationName) {
                            neighborStations.add(uNode.nombre);
                        }
                    }
                }
            });

            Array.from(neighborStations).sort().forEach(name => {
                vSelect.add(new Option(name, name));
            });
        }

        function getConnectedComponents(activeNodeIds, activeEdges) {
            const adj = new Map();
            activeNodeIds.forEach(id => adj.set(id, []));
            activeEdges.forEach(e => {
                if (adj.has(e.from) && adj.has(e.to)) {
                    adj.get(e.from).push(e.to);
                    adj.get(e.to).push(e.from);
                }
            });

            const visited = new Set();
            const components = [];

            activeNodeIds.forEach(id => {
                if (!visited.has(id)) {
                    const comp = [];
                    const queue = [id];
                    visited.add(id);

                    while (queue.length > 0) {
                        const curr = queue.shift();
                        comp.push(curr);
                        const neighbors = adj.get(curr) || [];
                        neighbors.forEach(nxt => {
                            if (!visited.has(nxt)) {
                                visited.add(nxt);
                                queue.push(nxt);
                            }
                        });
                    }
                    components.push(comp);
                }
            });

            return components.sort((a, b) => b.length - a.length);
        }

        function simulateStationRemoval() {
            const stationName = document.getElementById('sim-station-select').value;
            const station = stationMap.get(stationName);
            if (!station) return;

            const closedNodesSet = new Set(station.nodos);
            const remainingNodes = rawNodes.filter(n => !closedNodesSet.has(n.id)).map(n => n.id);
            const remainingEdges = rawEdges.filter(e => !closedNodesSet.has(e.from) && !closedNodesSet.has(e.to));

            const components = getConnectedComponents(remainingNodes, remainingEdges);
            const isConnected = (components.length <= 1);

            const nodeUpdates = rawNodes.map(n => {
                if (closedNodesSet.has(n.id)) {
                    return {
                        id: n.id,
                        size: 28,
                        shape: 'diamond',
                        color: { background: '#FF0000', border: '#FFFFFF' },
                        font: { color: '#FF3333', size: 14 }
                    };
                } else {
                    return {
                        id: n.id,
                        color: { background: n.color, border: '#FFFFFF' },
                        font: { color: '#ffffff' }
                    };
                }
            });

            const edgeUpdates = rawEdges.map(e => {
                if (closedNodesSet.has(e.from) || closedNodesSet.has(e.to)) {
                    return {
                        id: e.id,
                        color: { color: '#FF2A14' },
                        width: 3.5,
                        dashes: true
                    };
                } else {
                    return {
                        id: e.id,
                        color: { color: e.color },
                        width: e.width,
                        dashes: e.dashes
                    };
                }
            });

            nodesDataSet.update(nodeUpdates);
            edgesDataSet.update(edgeUpdates);

            const resultsBox = document.getElementById('sim-results');
            const alertBox = document.getElementById('sim-alert');
            const detailsBox = document.getElementById('sim-details');

            resultsBox.style.display = 'block';

            if (isConnected) {
                alertBox.className = 'failure-alert-box connected';
                alertBox.innerHTML = `
                    <strong><i class="fa-solid fa-circle-check"></i> Red Sigue Conectada</strong><br>
                    El cierre de <b>${stationName}</b> (${station.nodos.length} andenes) no fragmenta la red. Los pasajeros pueden usar rutas alternativas.
                `;
                detailsBox.innerHTML = `Componentes resultantes: <b>1</b> | Andenes operativos: <b>${remainingNodes.length}</b>`;
            } else {
                alertBox.className = 'failure-alert-box disconnected';
                const isolatedCount = remainingNodes.length - components[0].length;
                alertBox.innerHTML = `
                    <strong><i class="fa-solid fa-triangle-exclamation"></i> ¡ALERTA: RED FRAGMENTADA!</strong><br>
                    La clausura de <b>${stationName}</b> dividió la red en <b>${components.length} partes desconectadas</b>. Hay <b>${isolatedCount} andenes aislados</b> del bloque principal.
                `;
                detailsBox.innerHTML = `
                    Componente principal: <b>${components[0].length} andenes</b>.<br>
                    Fragmentos aislados: <b>${components.length - 1}</b> (${isolatedCount} andenes).
                `;
            }

            network.fit({
                nodes: station.nodos,
                animation: { duration: 600 }
            });
        }

        function simulateEdgeRemoval() {
            const uStationName = document.getElementById('sim-edge-u').value;
            const vStationName = document.getElementById('sim-edge-v').value;

            const targetEdge = rawEdges.find(e => {
                if (e.tipo !== 'via') return false;
                const uNode = nodeMap.get(e.from);
                const vNode = nodeMap.get(e.to);
                return (uNode.nombre === uStationName && vNode.nombre === vStationName) ||
                       (vNode.nombre === uStationName && uNode.nombre === vStationName);
            });

            if (!targetEdge) {
                alert("No se encontró un tramo directo entre estas dos estaciones.");
                return;
            }

            const excludedEdges = new Set([targetEdge.id]);
            const uStation = stationMap.get(uStationName);
            const vStation = stationMap.get(vStationName);

            const altResult = dijkstraMetro(uStation.nodos, vStation.nodos, 0, new Set(), excludedEdges);

            const altPathSet = altResult ? new Set(altResult.pathNodes) : new Set();
            const altEdgeSet = altResult ? new Set(altResult.pathEdges.map(e => e.id)) : new Set();

            const nodeUpdates = rawNodes.map(n => {
                if (altPathSet.has(n.id)) {
                    return {
                        id: n.id,
                        size: 24,
                        color: { background: '#00FF66', border: '#FFFFFF' },
                        font: { color: '#FFFFFF', size: 13 }
                    };
                } else {
                    return {
                        id: n.id,
                        color: { background: n.color, border: '#FFFFFF' },
                        font: { color: '#ffffff' }
                    };
                }
            });

            const edgeUpdates = rawEdges.map(e => {
                if (e.id === targetEdge.id) {
                    return {
                        id: e.id,
                        color: { color: '#FF0000' },
                        width: 6,
                        dashes: true
                    };
                } else if (altEdgeSet.has(e.id)) {
                    return {
                        id: e.id,
                        color: { color: '#00FF66' },
                        width: 5
                    };
                } else {
                    return {
                        id: e.id,
                        color: { color: e.color },
                        width: e.width
                    };
                }
            });

            nodesDataSet.update(nodeUpdates);
            edgesDataSet.update(edgeUpdates);

            const resultsBox = document.getElementById('sim-results');
            const alertBox = document.getElementById('sim-alert');
            const detailsBox = document.getElementById('sim-details');

            resultsBox.style.display = 'block';

            if (altResult) {
                const extraTime = altResult.totalCost - targetEdge.tiempo;
                alertBox.className = 'failure-alert-box connected';
                alertBox.innerHTML = `
                    <strong><i class="fa-solid fa-circle-check"></i> Tramo Cerrado (Ruta Alternativa Disponible)</strong><br>
                    Corte del tramo <b>${uStationName} ⟷ ${vStationName}</b>.<br>
                    Ruta alternativa más rápida: <b>${altResult.totalCost.toFixed(1)} min</b> (+${extraTime.toFixed(1)} min respecto al tramo directo).
                `;
                detailsBox.innerHTML = `La red sigue unida y los pasajeros disponen de itinerario de desvío (resaltado en verde).`;
            } else {
                alertBox.className = 'failure-alert-box disconnected';
                alertBox.innerHTML = `
                    <strong><i class="fa-solid fa-triangle-exclamation"></i> ¡ALERTA: TRAMO PUENTE CRÍTICO!</strong><br>
                    El tramo <b>${uStationName} ⟷ ${vStationName}</b> es un puente fundamental. Su corte aísla porciones de la red sin posibilidad de desvío.
                `;
                detailsBox.innerHTML = `No existe camino alternativo disponible entre ambos extremos.`;
            }

            network.fit({
                nodes: [targetEdge.from, targetEdge.to],
                animation: { duration: 600 }
            });
        }

        function resetNetworkView() {
            if (network) {
                network.fit({
                    animation: {
                        duration: 600,
                        easingFunction: 'easeInOutQuad'
                    }
                });
            }
        }

        function resetAllState() {
            activeRoutePath = null;
            activeLineFilter = 'ALL';
            selectedStationData = null;

            document.getElementById('route-results-container').style.display = 'none';
            document.getElementById('sim-results').style.display = 'none';
            document.getElementById('station-details-placeholder').style.display = 'block';
            document.getElementById('station-card').style.display = 'none';
            document.getElementById('station-search').value = '';

            filterLine('ALL');
            resetNetworkView();
        }

        function toggleFullscreen() {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(err => {
                    console.log("Error al activar pantalla completa:", err);
                });
            } else {
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                }
            }
        }
    </script>
</body>
</html>
"""

def generate_metro_interactive_html(G, pos, output_file="metro_madrid_pyvis.html", title="Metro de Madrid — Red y Análisis de Grafos"):
    """
    Construye la página web completa y la guarda en output_file usando sustitución segura de plantillas.
    """
    grados = dict(G.degree())
    
    # 1. Preparar lista de nodos (andenes)
    nodes_data = []
    physical_stations_map = {}
    
    for node, data in G.nodes(data=True):
        nombre = data.get('nombre', node)
        linea = data.get('linea', '')
        grado = grados.get(node, 1)
        lat = data.get('lat', 40.4168)
        lon = data.get('lon', -3.7038)
        color = COLORES_LINEAS.get(linea, '#00E5FF')
        
        size = grado * 3.2 + 13
        x, y = pos.get(node, (0, 0))
        
        if nombre not in physical_stations_map:
            physical_stations_map[nombre] = {
                'nombre': nombre,
                'nodos': [],
                'lineas': set(),
                'lat': lat,
                'lon': lon
            }
        physical_stations_map[nombre]['nodos'].append(node)
        if linea:
            physical_stations_map[nombre]['lineas'].add(linea)
            
        nodes_data.append({
            'id': node,
            'label': f"{nombre} ({linea})",
            'nombre': nombre,
            'linea': linea,
            'color': color,
            'size': size,
            'grado': grado,
            'x': round(x, 2),
            'y': round(y, 2),
            'lat': lat,
            'lon': lon
        })
        
    for st in physical_stations_map.values():
        st['lineas'] = sorted(list(st['lineas']))
        
    physical_stations_list = sorted(list(physical_stations_map.values()), key=lambda x: x['nombre'].lower())
    
    # 2. Preparar aristas
    edges_data = []
    for i, (u, v, data) in enumerate(G.edges(data=True)):
        tiempo = data.get('tiempo', 2.0)
        linea = data.get('linea', '')
        tipo = data.get('tipo', 'via')
        tiempo_str = format_time_min_sec(tiempo)
        
        if tipo == 'transbordo':
            color = "#FFFFFF"
            dashes = True
            width = 2.0
            title_text = f"Pasillo peatonal de transbordo ({tiempo_str} min)"
        else:
            color = COLORES_LINEAS.get(linea, '#888888')
            dashes = False
            width = 3.5
            title_text = f"Tramo Línea {linea}: {tiempo_str} min"
            
        edges_data.append({
            'id': f"e_{i}",
            'from': u,
            'to': v,
            'tiempo': round(tiempo, 2),
            'tiempo_str': tiempo_str,
            'linea': linea if tipo != 'transbordo' else 'Transbordo',
            'tipo': tipo,
            'color': color,
            'dashes': dashes,
            'width': width,
            'title': title_text
        })
        
    # 3. Preparar líneas
    lines_summary = []
    all_lines = ['L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8', 'L9', 'L10', 'L11', 'L12', 'R']
    for line_code in all_lines:
        line_nodes = [n for n, d in G.nodes(data=True) if d.get('linea') == line_code]
        lines_summary.append({
            'code': line_code,
            'name': NOMBRES_LINEAS.get(line_code, f"Línea {line_code}"),
            'color': COLORES_LINEAS.get(line_code, '#0097D6'),
            'station_count': len(line_nodes)
        })
        
    # Serializar JSON
    nodes_json = json.dumps(nodes_data, ensure_ascii=False)
    edges_json = json.dumps(edges_data, ensure_ascii=False)
    stations_json = json.dumps(physical_stations_list, ensure_ascii=False)
    lines_json = json.dumps(lines_summary, ensure_ascii=False)
    colors_json = json.dumps(COLORES_LINEAS, ensure_ascii=False)
    
    # Reemplazo seguro en la plantilla
    html = HTML_TEMPLATE
    html = html.replace('__TITLE__', title)
    html = html.replace('__NODES_COUNT__', str(len(G.nodes)))
    html = html.replace('__STATIONS_COUNT__', str(len(physical_stations_list)))
    html = html.replace('__EDGES_COUNT__', str(len(G.edges)))
    html = html.replace('__NODES_JSON__', nodes_json)
    html = html.replace('__EDGES_JSON__', edges_json)
    html = html.replace('__STATIONS_JSON__', stations_json)
    html = html.replace('__LINES_JSON__', lines_json)
    html = html.replace('__LINE_COLORS_JSON__', colors_json)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
        
    print(f"Visualización interactiva guardada en: {output_file}")
