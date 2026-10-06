"""
Generador de Visualización y Presentación Interactiva Final para el Metro de Madrid.
Incorpora:
1. Estructura Topológica Global (Nodos, aristas de vía y transbordo, densidad, diámetro, pesos temporales).
2. Rutas Óptimas Comparativas (Tiempos en minutos y segundos, comparativa lado a lado).
3. Rutas de Contingencia / Desvíos ante Incidencias: Cálculo de rutas alternativas tras eliminar una estación completa, una línea específica o un tramo de vía cortado, con cálculo de sobrecosto y trazado en el mapa.
4. Análisis de Centralidad (Rankings de Grado y Betweenness Centrality con localización interactiva).
5. Simulación de Robustez y Fallos (Cierre de estación completa O de una línea específica en estaciones multilínea, y corte de tramos con botón directo para probar rutas de desvío).
6. Puntos Críticos de Articulación (Puntos únicos de fallo y estaciones críticas con simulación en 1 clic).
7. Distribución de Grados (Histograma interactivo con Chart.js, estadísticas descriptivas y Top de estaciones con mayor grado).
8. Nodos de menor tamaño y mayor nitidez visual con iluminación interactiva de aristas al pasar el cursor.
9. Separación de altura perfecta sin solapamientos entre la barra superior y el panel lateral.
"""

import json
import numpy as np
import networkx as nx

try:
    from metrics import get_all_metrics, get_top_stations_by_degree, get_top_stations_by_betweenness, aggregate_station_metrics
    from robustness import identify_critical_stations, identify_articulation_points
    from algorithms import find_route_with_disruption
except ImportError:
    from src.metrics import get_all_metrics, get_top_stations_by_degree, get_top_stations_by_betweenness, aggregate_station_metrics
    from src.robustness import identify_critical_stations, identify_articulation_points
    from src.algorithms import find_route_with_disruption

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
    if m == 0:
        return f"{s} s"
    if s == 0:
        return f"{m} min"
    return f"{m} min {s:02d} s"

PRESENTATION_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>__TITLE__</title>
    
    <!-- CDNs Estables: Bootstrap 5, FontAwesome 6, Vis-Network 9.1.2, Chart.js 4.4, Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/dist/vis-network.min.css" />
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>

    <style>
        :root {
            --bg-canvas: #090d16;
            --bg-panel: rgba(15, 23, 42, 0.96);
            --bg-panel-subtle: rgba(30, 41, 59, 0.88);
            --bg-card-inner: rgba(15, 23, 42, 0.75);
            --border-subtle: rgba(255, 255, 255, 0.12);
            --border-active: rgba(0, 229, 255, 0.6);
            
            /* Textos con maximo contraste para proyeccion y lectura */
            --text-primary: #ffffff;
            --text-secondary: #f1f5f9;
            --text-muted: #cbd5e1;
            --text-dim: #94a3b8;
            
            /* Paleta tematica Metro */
            --metro-red: #FF2A14;
            --metro-blue: #0097D6;
            --metro-accent: #00E5FF;
            --metro-green: #10b981;
            --metro-warning: #f59e0b;
            --metro-purple: #c084fc;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg-canvas);
            color: var(--text-secondary);
            overflow: hidden;
            height: 100vh;
            width: 100vw;
        }

        .text-dim { color: var(--text-dim) !important; }
        .text-muted-custom { color: var(--text-muted) !important; }

        #mynetwork {
            position: absolute;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: radial-gradient(circle at 50% 50%, #162035 0%, #070a13 100%);
            z-index: 1;
        }

        /* Barra Superior Flotante */
        .top-navbar {
            position: fixed;
            top: 12px;
            left: 14px;
            right: 14px;
            height: 56px;
            max-height: 56px;
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 18px;
            background: var(--bg-panel);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--border-subtle);
            border-radius: 14px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.55);
            pointer-events: auto;
            flex-wrap: nowrap;
        }

        .brand-section {
            display: flex;
            align-items: center;
            gap: 12px;
            flex-shrink: 0;
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
            box-shadow: 0 0 14px rgba(255, 42, 20, 0.5);
            flex-shrink: 0;
        }

        .brand-title {
            font-size: 1.15rem;
            font-weight: 800;
            letter-spacing: -0.3px;
            color: #ffffff;
            margin: 0;
            line-height: 1.15;
        }

        .brand-subtitle {
            font-size: 0.74rem;
            color: var(--metro-accent);
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
            line-height: 1.1;
        }

        /* Cluster Central de Métricas del Header */
        .header-metrics-cluster {
            display: flex;
            align-items: center;
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid var(--border-subtle);
            border-radius: 24px;
            padding: 4px 12px;
            gap: 12px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(8px);
        }

        .metrics-subgroup {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.78rem;
        }

        .subgroup-label {
            font-size: 0.68rem;
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.5px;
            color: var(--text-dim);
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .metric-pill {
            color: var(--text-secondary);
            font-size: 0.78rem;
            white-space: nowrap;
        }

        .metric-pill b {
            color: #ffffff;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
        }

        .cluster-divider {
            width: 1px;
            height: 18px;
            background: rgba(255, 255, 255, 0.15);
        }

        .metric-pill-highlight {
            display: flex;
            align-items: center;
            gap: 6px;
            background: rgba(250, 204, 21, 0.12);
            border: 1px solid rgba(250, 204, 21, 0.35);
            padding: 3px 10px;
            border-radius: 14px;
            font-size: 0.78rem;
            color: #fef08a;
            cursor: pointer;
            transition: all 0.2s ease;
            white-space: nowrap;
        }

        .metric-pill-highlight:hover {
            background: rgba(250, 204, 21, 0.24);
            border-color: #facc15;
            transform: translateY(-1px);
            box-shadow: 0 0 12px rgba(250, 204, 21, 0.35);
        }

        .metric-pill-highlight b {
            color: #ffffff;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 800;
        }

        .badge-route-hint {
            background: rgba(0, 229, 255, 0.2);
            color: #00E5FF;
            border: 1px solid rgba(0, 229, 255, 0.4);
            padding: 1px 6px;
            border-radius: 8px;
            font-size: 0.68rem;
            font-weight: 700;
            margin-left: 2px;
        }

        /* Cluster Derecho de Acciones */
        .header-actions-cluster {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-shrink: 0;
            flex-wrap: nowrap;
        }

        .actions-button-group {
            display: flex;
            align-items: center;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 2px;
            gap: 2px;
            flex-wrap: nowrap;
        }

        .actions-button-group .btn-action {
            background: transparent;
            border: none;
            padding: 6px 11px;
            border-radius: 8px;
            font-size: 0.78rem;
        }

        .actions-button-group .btn-action:hover {
            background: rgba(255, 255, 255, 0.14);
            color: #00E5FF;
            transform: none;
        }

        .actions-button-group .btn-action.btn-reset {
            background: rgba(239, 68, 68, 0.16);
            color: #fca5a5;
        }

        .actions-button-group .btn-action.btn-reset:hover {
            background: rgba(239, 68, 68, 0.35);
            color: #ffffff;
        }

        .actions-divider {
            width: 1px;
            height: 18px;
            background: rgba(255, 255, 255, 0.15);
            margin: 0 4px;
        }

        .btn-action {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid var(--border-subtle);
            color: #ffffff;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            white-space: nowrap;
        }

        .btn-action:hover {
            background: rgba(255, 255, 255, 0.18);
            border-color: rgba(255, 255, 255, 0.3);
            color: #00E5FF;
            transform: translateY(-1px);
        }

        .btn-action.btn-reset {
            background: rgba(239, 68, 68, 0.18);
            border-color: rgba(239, 68, 68, 0.4);
            color: #fca5a5;
        }

        .btn-action.btn-reset:hover {
            background: rgba(239, 68, 68, 0.35);
            color: #ffffff;
        }

        /* Panel Lateral (Sidebar Drawer) */
        .sidebar-drawer {
            position: fixed;
            top: 78px;
            left: 14px;
            width: 485px;
            max-width: 95vw;
            max-height: calc(100vh - 92px);
            z-index: 999;
            background: var(--bg-panel);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            border: 1px solid var(--border-subtle);
            border-radius: 16px;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.6);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            transition: width 0.3s cubic-bezier(0.16, 1, 0.3, 1), transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.3s ease;
        }

        .sidebar-drawer.expanded {
            width: 760px;
        }

        .sidebar-drawer.collapsed {
            transform: translateX(-800px);
            opacity: 0;
            pointer-events: none;
        }

        /* Barra de Pestañas del Panel */
        .sidebar-tabs {
            display: flex;
            background: rgba(0, 0, 0, 0.38);
            border-bottom: 1px solid var(--border-subtle);
            padding: 6px;
            gap: 4px;
            overflow-x: auto;
            scrollbar-width: none;
        }

        .sidebar-tabs::-webkit-scrollbar {
            display: none;
        }

        .sidebar-tab-btn {
            flex: 1 1 0;
            min-width: 58px;
            padding: 7px 2px;
            background: transparent;
            border: none;
            color: var(--text-dim);
            font-size: 0.72rem;
            font-weight: 600;
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            transition: all 0.2s ease;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .sidebar-tab-btn i {
            font-size: 0.95rem;
        }

        .sidebar-tab-btn.active {
            background: rgba(0, 229, 255, 0.16);
            color: #00E5FF;
            border: 1px solid rgba(0, 229, 255, 0.38);
            box-shadow: 0 2px 8px rgba(0, 229, 255, 0.18);
        }

        .sidebar-tab-btn:hover:not(.active) {
            background: rgba(255, 255, 255, 0.08);
            color: #ffffff;
        }

        .sidebar-tab-content {
            padding: 16px 16px 48px 16px;
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

        /* Insignia de encabezado temático */
        .section-header-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            background: rgba(0, 229, 255, 0.14);
            border: 1px solid rgba(0, 229, 255, 0.35);
            border-radius: 12px;
            color: #00E5FF;
            font-size: 0.74rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }

        .section-main-title {
            font-size: 1.18rem;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 6px;
            line-height: 1.3;
        }

        .section-desc {
            font-size: 0.83rem;
            color: var(--text-muted);
            margin-bottom: 14px;
            line-height: 1.45;
        }

        /* Cards y contenedores */
        .info-card-box {
            background: var(--bg-panel-subtle);
            border: 1px solid var(--border-subtle);
            border-radius: 14px;
            padding: 14px;
            margin-bottom: 14px;
        }

        .info-card-header {
            font-size: 0.88rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .grid-2col {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }

        .grid-3col {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
        }

        .metric-stat-box {
            background: var(--bg-card-inner);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            padding: 10px;
            text-align: center;
        }

        .metric-stat-val {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.25rem;
            font-weight: 800;
            color: #ffffff;
            line-height: 1.1;
        }

        .metric-stat-label {
            font-size: 0.72rem;
            color: var(--text-dim);
            font-weight: 600;
            margin-top: 4px;
            text-transform: uppercase;
        }

        /* Buscador */
        .search-box {
            position: relative;
            margin-bottom: 14px;
        }

        .search-input {
            width: 100%;
            background: rgba(0, 0, 0, 0.45);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 10px 14px 10px 40px;
            color: #ffffff;
            font-size: 0.9rem;
            outline: none;
            transition: all 0.2s;
        }

        .search-input:focus {
            border-color: #00E5FF;
            box-shadow: 0 0 10px rgba(0, 229, 255, 0.3);
            background: rgba(0, 0, 0, 0.7);
        }

        .search-icon {
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-dim);
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
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.75);
        }

        .autocomplete-item {
            padding: 10px 14px;
            cursor: pointer;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: background 0.15s;
        }

        .autocomplete-item:hover {
            background: rgba(0, 151, 214, 0.25);
        }

        .station-card {
            background: var(--bg-panel-subtle);
            border: 1px solid var(--border-subtle);
            border-radius: 14px;
            padding: 16px;
            margin-top: 12px;
        }

        .station-name {
            font-size: 1.3rem;
            font-weight: 800;
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
            font-weight: 800;
            font-size: 0.78rem;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        }

        .form-label-custom {
            font-size: 0.78rem;
            font-weight: 700;
            color: var(--text-muted);
            margin-bottom: 6px;
            display: block;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }

        .form-select-custom {
            width: 100%;
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 9px 12px;
            color: #ffffff;
            font-size: 0.88rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .form-select-custom option {
            background-color: #0f172a;
            color: #ffffff;
        }

        .form-select-custom:focus {
            border-color: #00E5FF;
        }

        .btn-calc {
            width: 100%;
            background: linear-gradient(135deg, #0097D6, #005f88);
            border: none;
            color: #ffffff;
            padding: 11px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 0.9rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 0.2s;
            box-shadow: 0 4px 14px rgba(0, 151, 214, 0.35);
        }

        .btn-calc:hover {
            background: linear-gradient(135deg, #00b4ff, #0077aa);
            transform: translateY(-1px);
            box-shadow: 0 6px 18px rgba(0, 151, 214, 0.5);
        }

        .btn-quick {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s;
        }

        .btn-quick:hover {
            background: rgba(255, 255, 255, 0.16);
            color: #ffffff;
        }

        .btn-danger-custom {
            width: 100%;
            background: linear-gradient(135deg, #FF2A14, #b91c1c);
            border: none;
            color: #ffffff;
            padding: 10px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 0.88rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 0.2s;
            box-shadow: 0 4px 12px rgba(255, 42, 20, 0.35);
        }

        .btn-danger-custom:hover {
            background: linear-gradient(135deg, #ff4d3a, #dc2626);
            transform: translateY(-1px);
        }

        /* Tabla de rankings con alto contraste */
        .ranking-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.82rem;
        }

        .ranking-table th {
            color: var(--text-dim);
            font-weight: 700;
            text-transform: uppercase;
            font-size: 0.7rem;
            padding: 8px 6px;
            border-bottom: 1px solid var(--border-subtle);
            text-align: left;
        }

        .ranking-table td {
            padding: 8px 6px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            color: #ffffff;
            vertical-align: middle;
        }

        .ranking-table tr:hover td {
            background: rgba(0, 229, 255, 0.08);
        }

        .rank-pos {
            font-family: 'JetBrains Mono', monospace;
            font-weight: 800;
            color: var(--metro-accent);
            width: 26px;
        }

        .rank-val {
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
            color: #10b981;
        }

        .btn-table-action {
            padding: 4px 8px;
            font-size: 0.72rem;
            font-weight: 600;
            border-radius: 6px;
            border: 1px solid rgba(0, 229, 255, 0.4);
            background: rgba(0, 229, 255, 0.12);
            color: #00E5FF;
            cursor: pointer;
            transition: all 0.15s;
        }

        .btn-table-action:hover {
            background: #00E5FF;
            color: #090d16;
        }

        .btn-table-sim {
            padding: 4px 8px;
            font-size: 0.72rem;
            font-weight: 600;
            border-radius: 6px;
            border: 1px solid rgba(239, 68, 68, 0.4);
            background: rgba(239, 68, 68, 0.15);
            color: #fca5a5;
            cursor: pointer;
            transition: all 0.15s;
        }

        .btn-table-sim:hover {
            background: #ef4444;
            color: #ffffff;
        }

        /* Resumen de Ruta */
        .route-summary-card {
            background: var(--bg-card-inner);
            border: 1px solid rgba(0, 229, 255, 0.25);
            border-radius: 12px;
            padding: 12px;
            margin-top: 14px;
        }

        .route-timeline {
            position: relative;
            padding-left: 20px;
            margin-top: 12px;
        }

        .route-timeline::before {
            content: '';
            position: absolute;
            top: 6px;
            bottom: 6px;
            left: 6px;
            width: 2px;
            background: rgba(255, 255, 255, 0.18);
        }

        .timeline-step {
            position: relative;
            margin-bottom: 10px;
            font-size: 0.8rem;
            color: var(--text-secondary);
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

        /* Presets de Demostración */
        .preset-badge-btn {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid var(--border-subtle);
            color: #ffffff;
            padding: 6px 10px;
            border-radius: 8px;
            font-size: 0.76rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.15s;
        }

        .preset-badge-btn:hover {
            background: rgba(255, 42, 20, 0.2);
            border-color: rgba(255, 42, 20, 0.5);
            color: #ff9999;
        }

        /* Boton Toggle Lateral */
        .btn-toggle-sidebar {
            position: fixed;
            top: 88px;
            left: 512px;
            z-index: 998;
            background: var(--bg-panel);
            border: 1px solid var(--border-subtle);
            color: #ffffff;
            width: 32px;
            height: 38px;
            border-radius: 0 10px 10px 0;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
            box-shadow: 4px 6px 14px rgba(0, 0, 0, 0.4);
        }

        .btn-toggle-sidebar.expanded-sidebar {
            left: 787px;
        }

        .btn-toggle-sidebar.collapsed {
            left: 14px !important;
            border-radius: 10px;
        }

        /* Líneas Grid */
        .lines-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }

        .line-card {
            background: var(--bg-card-inner);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 8px 10px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: all 0.2s;
        }

        .line-card:hover {
            border-color: rgba(255, 255, 255, 0.35);
            transform: translateY(-1px);
        }

        .line-card.active {
            border-color: #00E5FF;
            box-shadow: 0 0 10px rgba(0, 229, 255, 0.3);
            background: rgba(0, 229, 255, 0.1);
        }

        /* Alerta de simulación */
        .failure-alert-box {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.4);
            border-radius: 12px;
            padding: 12px;
            margin-top: 12px;
        }

        .failure-alert-box.connected {
            background: rgba(16, 185, 129, 0.15);
            border-color: rgba(16, 185, 129, 0.4);
        }
    </style>
</head>
<body>

    <!-- Canvas de red Vis.js -->
    <div id="mynetwork"></div>

    <!-- Barra de Navegación Superior: Fija y elegante -->
    <header class="top-navbar">
        <!-- 1. Cluster Marca / Título -->
        <div class="brand-section">
            <div class="brand-logo-rhombus">
                <i class="fa-solid fa-subway text-white" style="transform: rotate(-45deg); font-size: 0.95rem;"></i>
            </div>
            <div>
                <h1 class="brand-title">Metro de Madrid</h1>
                <div class="brand-subtitle">
                    <i class="fa-solid fa-circle-nodes"></i> Modelado y Análisis de Grafos de la Red
                </div>
            </div>
        </div>

        <!-- 2. Cluster Central: Métricas Clave de la Red -->
        <div class="header-metrics-cluster d-none d-lg-flex">
            <!-- Subgrupo Topología -->
            <div class="metrics-subgroup" title="Topología de la red de transporte">
                <span class="subgroup-label"><i class="fa-solid fa-network-wired text-info"></i> Red</span>
                <span class="metric-pill">Estaciones: <b id="kpi-stations">__STATIONS_COUNT__</b></span>
                <span class="metric-pill">Andenes: <b id="kpi-nodes">__NODES_COUNT__</b></span>
            </div>
            
            <div class="cluster-divider"></div>

            <!-- Subgrupo Infraestructura -->
            <div class="metrics-subgroup" title="Infraestructura física y conexiones">
                <span class="subgroup-label"><i class="fa-solid fa-train text-success"></i> Vías</span>
                <span class="metric-pill">Tramos: <b id="kpi-via">__VIA_COUNT__</b></span>
                <span class="metric-pill">Transbordos: <b id="kpi-trans">__TRANS_COUNT__</b></span>
            </div>

            <div class="cluster-divider"></div>

            <!-- Subgrupo Diámetro Interactivo -->
            <div class="metric-pill-highlight" onclick="showDiameterRoute()" title="Clic para ver la ruta más larga de la red (Diámetro: __DIAMETER__ saltos)">
                <i class="fa-solid fa-arrows-left-right text-warning"></i> Diámetro: <b id="kpi-diam">__DIAMETER__</b>
                <span class="badge-route-hint"><i class="fa-solid fa-route"></i> Ver Ruta</span>
            </div>
        </div>

        <!-- 3. Cluster Derecho: Controles y Herramientas -->
        <div class="header-actions-cluster">
            <div class="actions-button-group">
                <button class="btn-action" id="expand-sidebar-btn" onclick="toggleSidebarWidth()" title="Agrandar / Reducir panel lateral para presentación">
                    <i class="fa-solid fa-table-columns"></i> <span id="expand-btn-text" class="d-none d-md-inline">Agrandar Panel</span>
                </button>
                <button class="btn-action" onclick="resetNetworkView()" title="Centrar mapa completo (sin resetear filtros)">
                    <i class="fa-solid fa-crosshairs"></i> <span class="d-none d-md-inline">Centrar Mapa</span>
                </button>
                <button class="btn-action" onclick="toggleFullScreen()" title="Modo pantalla completa para presentación">
                    <i class="fa-solid fa-expand"></i> <span class="d-none d-md-inline">Presentar</span>
                </button>
                <div class="actions-divider"></div>
                <button class="btn-action btn-reset" onclick="resetAllState()" title="Restablecer filtros, selecciones y vista">
                    <i class="fa-solid fa-arrow-rotate-left"></i> <span class="d-none d-md-inline">Restablecer</span>
                </button>
            </div>
        </div>
    </header>

    <!-- Botón Toggle Sidebar -->
    <button id="toggle-sidebar-btn" class="btn-toggle-sidebar" onclick="toggleSidebar()" title="Mostrar/Ocultar Panel">
        <i class="fa-solid fa-chevron-left" id="toggle-sidebar-icon"></i>
    </button>

    <!-- Panel Lateral Desplegable -->
    <aside id="sidebar-drawer" class="sidebar-drawer">
        <nav class="sidebar-tabs">
            <button class="sidebar-tab-btn active" onclick="switchTab('tab-structure')" title="Estructura Topológica">
                <i class="fa-solid fa-diagram-project"></i>
                <span>Estructura</span>
            </button>
            <button class="sidebar-tab-btn" onclick="switchTab('tab-routes')" title="Rutas Óptimas y Contingencias">
                <i class="fa-solid fa-route"></i>
                <span>Rutas</span>
            </button>
            <button class="sidebar-tab-btn" onclick="switchTab('tab-centrality')" title="Centralidad e Importancia">
                <i class="fa-solid fa-ranking-star"></i>
                <span>Centralidad</span>
            </button>
            <button class="sidebar-tab-btn" onclick="switchTab('tab-simulate')" title="Simulación de Fallos y Cierres">
                <i class="fa-solid fa-shield-halved"></i>
                <span>Resiliencia</span>
            </button>
            <button class="sidebar-tab-btn" onclick="switchTab('tab-critical')" title="Puntos Críticos de Articulación">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <span>Ptos. Críticos</span>
            </button>
            <button class="sidebar-tab-btn" onclick="switchTab('tab-degrees')" title="Distribución de Grados">
                <i class="fa-solid fa-chart-column"></i>
                <span>Grados</span>
            </button>
            <button class="sidebar-tab-btn" onclick="switchTab('tab-stations')" title="Buscador y Líneas">
                <i class="fa-solid fa-compass"></i>
                <span>Explorar</span>
            </button>
        </nav>

        <div class="sidebar-tab-content">

            <!-- PESTAÑA: ESTRUCTURA DEL GRAFO -->
            <div id="tab-structure" class="tab-pane active">
                <div class="section-header-badge"><i class="fa-solid fa-cubes me-1"></i> Topología Global</div>
                <h2 class="section-main-title">Estructura Topológica del Grafo</h2>
                <p class="section-desc">
                    El sistema modela el Metro de Madrid como un <b>grafo no dirigido ponderado</b> G = (V, E, W) bajo el modelo <b>Estación-Línea</b> con coordenadas GPS reales de Madrid.
                </p>

                <div class="info-card-box">
                    <div class="info-card-header">
                        <span><i class="fa-solid fa-cubes text-info me-2"></i>Dimensiones de la Red</span>
                        <span class="badge bg-success-subtle text-success">Conexa (1 CC)</span>
                    </div>
                    <div class="grid-3col">
                        <div class="metric-stat-box">
                            <div class="metric-stat-val text-info" id="struct-nodes">__NODES_COUNT__</div>
                            <div class="metric-stat-label">Andenes (V)</div>
                        </div>
                        <div class="metric-stat-box">
                            <div class="metric-stat-val text-warning" id="struct-stations">__STATIONS_COUNT__</div>
                            <div class="metric-stat-label">Estaciones</div>
                        </div>
                        <div class="metric-stat-box">
                            <div class="metric-stat-val text-success" id="struct-edges">__EDGES_COUNT__</div>
                            <div class="metric-stat-label">Aristas (E)</div>
                        </div>
                    </div>
                </div>

                <div class="info-card-box">
                    <div class="info-card-header">
                        <span><i class="fa-solid fa-sliders text-warning me-2"></i>Métricas Globales de Conectividad</span>
                    </div>
                    <div class="grid-2col">
                        <div class="metric-stat-box">
                            <div class="metric-stat-val" style="color: #38bdf8;" id="struct-density">__DENSITY__</div>
                            <div class="metric-stat-label">Densidad (ρ)</div>
                        </div>
                        <div class="metric-stat-box" onclick="showDiameterRoute()" style="cursor: pointer;" title="Clic para ver la ruta más larga (Diámetro: __DIAMETER__ saltos)">
                            <div class="metric-stat-val text-warning" id="struct-diameter">__DIAMETER__</div>
                            <div class="metric-stat-label">Diámetro (Saltos) <i class="fa-solid fa-route ms-1 text-info"></i></div>
                        </div>
                        <div class="metric-stat-box">
                            <div class="metric-stat-val" style="color: #4ade80;" id="struct-avg-deg">__AVG_DEGREE__</div>
                            <div class="metric-stat-label">Grado Medio (k̄)</div>
                        </div>
                        <div class="metric-stat-box">
                            <div class="metric-stat-val" style="color: #f43f5e;" id="struct-lines">13</div>
                            <div class="metric-stat-label">Líneas Oficiales</div>
                        </div>
                    </div>
                    <button class="btn-action w-100 mt-2 justify-content-center" onclick="showDiameterRoute()" title="Ver la ruta del diámetro en el mapa">
                        <i class="fa-solid fa-route text-warning me-2"></i> Ver Ruta Más Larga de la Red (__DIAMETER__ saltos)
                    </button>
                </div>

                <div class="info-card-box">
                    <div class="info-card-header">
                        <span><i class="fa-solid fa-circle-info text-info me-2"></i>Datos Relevantes de Topología</span>
                    </div>
                    <p style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0; line-height: 1.5;">
                        • <b>Topología Dispersa:</b> Densidad de <b>0.00801</b> (red planar-like), lo que minimiza el consumo de infraestructura subterránea y maximiza la cobertura urbana.<br>
                        • <b>Diámetro Global:</b> <b>__DIAMETER__ saltos</b> entre los extremos más lejanos de la red (Hospital Infanta Sofía en L10 hasta Parque de los Estados en L12).<br>
                        • <b>Grado Promedio:</b> 2.32 conexiones por andén, reflejando una estructura mayoritariamente en línea recta con bifurcaciones puntuales.
                    </p>
                </div>

                <div class="info-card-box">
                    <div class="info-card-header">
                        <span><i class="fa-solid fa-scale-balanced text-primary me-2"></i>Modelo de Pesos W(e)</span>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.55;">
                        <div class="d-flex align-items-center justify-content-between py-1 border-bottom border-secondary border-opacity-25">
                            <span><i class="fa-solid fa-train text-success me-2"></i><b>Tramos de Vía (277):</b></span>
                            <span class="text-white font-monospace">1 min 30 s a 2 min 30 s</span>
                        </div>
                        <div class="d-flex align-items-center justify-content-between py-1 border-bottom border-secondary border-opacity-25">
                            <span><i class="fa-solid fa-person-walking text-warning me-2"></i><b>Pasillos Peatonales (61):</b></span>
                            <span class="text-white font-monospace">2 min 00 s a 4 min 00 s</span>
                        </div>
                        <div class="d-flex align-items-center justify-content-between py-1 pt-2">
                            <span><i class="fa-solid fa-circle-check text-info me-2"></i><b>Topología:</b></span>
                            <span class="text-white">Grafo Disperso (Sparse Planar-like)</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- PESTAÑA: RUTAS ÓPTIMAS Y RUTAS CON CONTINGENCIA -->
            <div id="tab-routes" class="tab-pane">
                <div class="section-header-badge"><i class="fa-solid fa-diamond-turn-right me-1"></i> Algoritmos de Ruta</div>
                <h2 class="section-main-title">Cálculo y Comparativa de Rutas</h2>
                <p class="section-desc">
                    Calcula la ruta óptima habitual y <b>rutas de contingencia / desvío</b> cuando existen estaciones, líneas o tramos inhabilitados.
                </p>

                <div class="mb-3">
                    <label class="form-label-custom">Estación de Origen</label>
                    <select id="route-origin" class="form-select-custom"></select>
                </div>

                <div class="d-flex justify-content-center my-1">
                    <button class="btn btn-sm" style="background: rgba(255,255,255,0.08); color: var(--metro-accent); border: 1px solid var(--border-subtle); border-radius: 50%; width: 34px; height: 34px;" onclick="swapRouteStations()" title="Invertir origen y destino">
                        <i class="fa-solid fa-arrow-down-up-across-line"></i>
                    </button>
                </div>

                <div class="mb-3">
                    <label class="form-label-custom">Estación de Destino</label>
                    <select id="route-dest" class="form-select-custom"></select>
                </div>

                <div class="mb-3">
                    <label class="form-label-custom">Criterio de Optimización</label>
                    <div class="d-flex gap-2 flex-wrap">
                        <label class="btn-quick flex-fill text-center" style="cursor: pointer;">
                            <input type="radio" name="route-criteria" value="time" checked class="me-1"> Menor Tiempo
                        </label>
                        <label class="btn-quick flex-fill text-center" style="cursor: pointer;">
                            <input type="radio" name="route-criteria" value="stops" class="me-1"> Menos Paradas
                        </label>
                        <label class="btn-quick flex-fill text-center" style="cursor: pointer;">
                            <input type="radio" name="route-criteria" value="transfers" class="me-1"> Menos Transbordos
                        </label>
                    </div>
                </div>

                <!-- NUEVA SECCIÓN: INCIDENCIAS Y CONTINGENCIA EN RUTA -->
                <div class="info-card-box mb-3" style="border: 1px dashed rgba(239, 68, 68, 0.45); background: rgba(239, 68, 68, 0.08);">
                    <div class="d-flex align-items-center justify-content-between">
                        <label class="form-check-label text-white fw-bold d-flex align-items-center gap-2 m-0" style="cursor: pointer; font-size: 0.84rem;">
                            <input type="checkbox" id="route-disruption-toggle" class="form-check-input" onchange="toggleRouteDisruptionUI(this.checked)" style="background-color: #0f172a; border-color: #ef4444; cursor: pointer;">
                            <span><i class="fa-solid fa-triangle-exclamation text-danger"></i> Simular Incidencia en la Red (Desvío)</span>
                        </label>
                        <span class="badge bg-danger-subtle text-danger" style="font-size: 0.7rem;">Contingencia</span>
                    </div>

                    <div id="route-disruption-panel" style="display: none; padding-top: 10px; margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.08);">
                        <p style="font-size: 0.77rem; color: var(--text-muted); margin-bottom: 10px;">
                            Calcula el trayecto alternativo que deben tomar los usuarios evitando el elemento inoperativo.
                        </p>
                        <div class="d-flex gap-2 mb-2">
                            <label class="btn-quick flex-fill text-center" style="cursor: pointer; font-size: 0.75rem;">
                                <input type="radio" name="disrupt-type" value="station" checked onchange="toggleDisruptType(this.value)" class="me-1"> Evitar Estación/Línea
                            </label>
                            <label class="btn-quick flex-fill text-center" style="cursor: pointer; font-size: 0.75rem;">
                                <input type="radio" name="disrupt-type" value="edge" onchange="toggleDisruptType(this.value)" class="me-1"> Evitar Tramo de Vía
                            </label>
                        </div>

                        <!-- Evitar Estacion -->
                        <div id="disrupt-station-fields">
                            <div class="mb-2">
                                <label class="form-label-custom" style="font-size: 0.72rem;">Estación a Evitar</label>
                                <select id="disrupt-station-select" class="form-select-custom" onchange="onDisruptStationChange()"></select>
                            </div>
                            <div class="mb-1">
                                <label class="form-label-custom" style="font-size: 0.72rem;">Alcance del Bloqueo</label>
                                <select id="disrupt-line-scope" class="form-select-custom"></select>
                            </div>
                        </div>

                        <!-- Evitar Tramo -->
                        <div id="disrupt-edge-fields" style="display: none;">
                            <div class="mb-2">
                                <label class="form-label-custom" style="font-size: 0.72rem;">Estación A del Tramo</label>
                                <select id="disrupt-edge-u" class="form-select-custom" onchange="updateDisruptEdgeTargets()"></select>
                            </div>
                            <div class="mb-1">
                                <label class="form-label-custom" style="font-size: 0.72rem;">Estación B Conectada</label>
                                <select id="disrupt-edge-v" class="form-select-custom"></select>
                            </div>
                        </div>
                    </div>
                </div>

                <button class="btn-calc" onclick="calculateAndDisplayRouteMultiCriteria()">
                    <i class="fa-solid fa-route"></i> Calcular Ruta y Desvío
                </button>

                <div id="route-results-container" style="display: none;">
                    <!-- Alerta de contingencia (si aplica) -->
                    <div id="route-contingency-banner" style="display: none;"></div>

                    <div id="route-summary" class="route-summary-card"></div>

                    <!-- Comparativa Lado a Lado -->
                    <div class="info-card-box mt-3 mb-2">
                        <div class="info-card-header">
                            <span><i class="fa-solid fa-chart-simple text-info me-2"></i>Comparativa de Alternativas</span>
                        </div>
                        <div id="route-comparison-grid" class="d-flex flex-column gap-2" style="font-size: 0.78rem;"></div>
                    </div>

                    <div class="d-flex justify-content-between align-items-center mt-3">
                        <span class="form-label-custom mb-0">Itinerario Paso a Paso</span>
                        <button class="btn btn-sm btn-link text-danger text-decoration-none p-0" style="font-size: 0.78rem;" onclick="clearRouteHighlight()">Limpiar Resaltado</button>
                    </div>

                    <div id="route-steps" class="route-timeline"></div>
                </div>
            </div>

            <!-- PESTAÑA: CENTRALIDAD E IMPORTANCIA -->
            <div id="tab-centrality" class="tab-pane">
                <div class="section-header-badge"><i class="fa-solid fa-ranking-star me-1"></i> Análisis de Centralidad</div>
                <h2 class="section-main-title">Estaciones Más Importantes (Centralidad)</h2>
                <p class="section-desc">
                    Identificación de nodos neurálgicos por <b>Grado</b> (número de conexiones) y <b>Betweenness Centrality</b> (frecuencia en caminos mínimos).
                </p>

                <!-- Top Grado -->
                <div class="info-card-box">
                    <div class="info-card-header">
                        <span><i class="fa-solid fa-network-wired text-info me-2"></i>Top 5 por Conexiones (Grado Físico)</span>
                    </div>
                    <table class="ranking-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Estación</th>
                                <th>Líneas</th>
                                <th>Conex.</th>
                                <th>Mapa</th>
                            </tr>
                        </thead>
                        <tbody id="top-degree-tbody"></tbody>
                    </table>
                </div>

                <!-- Top Betweenness -->
                <div class="info-card-box">
                    <div class="info-card-header">
                        <span><i class="fa-solid fa-share-nodes text-warning me-2"></i>Top 5 por Intermediación (Betweenness)</span>
                    </div>
                    <table class="ranking-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Estación</th>
                                <th>Líneas</th>
                                <th>Centralidad</th>
                                <th>Mapa</th>
                            </tr>
                        </thead>
                        <tbody id="top-betweenness-tbody"></tbody>
                    </table>
                </div>

                <div class="info-card-box">
                    <div class="info-card-header">
                        <span><i class="fa-solid fa-chart-line text-warning me-2"></i>Datos Relevantes de Centralidad</span>
                    </div>
                    <p style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0; line-height: 1.5;">
                        • <b>Líderes de Intermediación:</b> <b>Avenida de América</b> (0.4032), <b>Legazpi</b> (0.2842) y <b>Sol</b> (0.2775) canalizan el mayor volumen de caminos mínimos entre todas las estaciones de Madrid.<br>
                        • <b>Ejes de Distribución Cardinal:</b> Avenida de América (puerta noreste con 4 líneas) y Legazpi (puerta sur enlazando L3 con la circular L6) actúan como las dos grandes válvulas de escape y transferencia metropolitana.<br>
                        • <b>Dependencia de Nodos Troncales:</b> La gran mayoría de estaciones periféricas tienen centralidad cercana a 0, dependiendo críticamente de estos nodos articuladores para acceder a cualquier otro cuadrante de la red.
                    </p>
                </div>
            </div>

            <!-- PESTAÑA: SIMULACIÓN DE RESILIENCIA Y FALLOS -->
            <div id="tab-simulate" class="tab-pane">
                <div class="section-header-badge"><i class="fa-solid fa-shield-halved me-1"></i> Simulación de Robustez</div>
                <h2 class="section-main-title">Impacto por Cierre de Estación o Tramo</h2>
                <p class="section-desc">
                    Permite simular el cierre de una estación completa <b>o de una sola línea</b> en estaciones multilínea, así como el corte de tramos de vía con rutas de desvío.
                </p>

                <div class="mb-3">
                    <label class="form-label-custom">Tipo de Simulación</label>
                    <div class="d-flex gap-2">
                        <label class="btn-quick flex-fill text-center" style="cursor: pointer;">
                            <input type="radio" name="sim-mode" value="station" checked onchange="toggleSimMode(this.value)" class="me-1"> Cierre Estación / Línea
                        </label>
                        <label class="btn-quick flex-fill text-center" style="cursor: pointer;">
                            <input type="radio" name="sim-mode" value="edge" onchange="toggleSimMode(this.value)" class="me-1"> Corte de Tramo
                        </label>
                    </div>
                </div>

                <!-- Controles Modo Estacion -->
                <div id="sim-station-controls">
                    <!-- Presets Rápidos para Exposición -->
                    <div class="info-card-box">
                        <div class="info-card-header">
                            <span><i class="fa-solid fa-bolt text-warning me-2"></i>Demostración en 1 Clic (Hubs de Transbordo)</span>
                        </div>
                        <div class="d-flex flex-wrap gap-2">
                            <button class="preset-badge-btn" onclick="quickSimulateStation('Sol')">
                                <span class="badge bg-danger">Sol</span> 3 Líneas
                            </button>
                            <button class="preset-badge-btn" onclick="quickSimulateStation('Avenida de América')">
                                <span class="badge bg-danger">Av. América</span> 4 Líneas
                            </button>
                            <button class="preset-badge-btn" onclick="quickSimulateStation('Nuevos Ministerios')">
                                <span class="badge bg-danger">N. Ministerios</span> 3 Líneas
                            </button>
                            <button class="preset-badge-btn" onclick="quickSimulateStation('Príncipe Pío')">
                                <span class="badge bg-danger">Príncipe Pío</span> 3 Líneas
                            </button>
                            <button class="preset-badge-btn" onclick="quickSimulateStation('Cuatro Caminos')">
                                <span class="badge bg-danger">Cuatro Caminos</span> 3 Líneas
                            </button>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label class="form-label-custom">Seleccionar Estación</label>
                        <select id="sim-station-select" class="form-select-custom" onchange="onSimStationChange()"></select>
                    </div>

                    <!-- Selector de Alcance -->
                    <div class="mb-3" id="sim-line-scope-group">
                        <label class="form-label-custom">Alcance del Cierre (Líneas)</label>
                        <select id="sim-line-scope" class="form-select-custom"></select>
                    </div>

                    <button class="btn-danger-custom" onclick="simulateStationRemoval()">
                        <i class="fa-solid fa-triangle-exclamation"></i> Simular Cierre Seleccionado
                    </button>
                </div>

                <!-- Controles Modo Tramo (Edge) -->
                <div id="sim-edge-controls" style="display: none;">
                    <div class="mb-2">
                        <label class="form-label-custom">Estación A del Tramo</label>
                        <select id="sim-edge-u" class="form-select-custom" onchange="updateSimEdgeTargets()"></select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label-custom">Estación B Conectada Directamente</label>
                        <select id="sim-edge-v" class="form-select-custom"></select>
                    </div>
                    <button class="btn-danger-custom" onclick="simulateEdgeRemoval()">
                        <i class="fa-solid fa-scissors"></i> Simular Corte de Tramo de Vía
                    </button>
                </div>

                <div id="sim-results" style="display: none;">
                    <div id="sim-alert" class="failure-alert-box"></div>
                    <div id="sim-details" style="font-size: 0.82rem; margin-top: 10px; color: var(--text-secondary); line-height: 1.45;"></div>
                    
                    <!-- Boton directo para probar ruta de desvio -->
                    <button class="btn-action w-100 justify-content-center mt-3" style="background: rgba(0, 229, 255, 0.15); border-color: rgba(0, 229, 255, 0.4); color: #00E5FF;" onclick="transferSimToRoute()">
                        <i class="fa-solid fa-route me-1"></i> Probar Ruta de Desvío que Evite este Cierre
                    </button>
                    
                    <button class="btn-action w-100 justify-content-center mt-2" onclick="resetAllState()">
                        <i class="fa-solid fa-wrench me-1"></i> Restablecer Red Completa
                    </button>
                </div>
            </div>

            <!-- PESTAÑA: PUNTOS CRÍTICOS DE ARTICULACIÓN -->
            <div id="tab-critical" class="tab-pane">
                <div class="section-header-badge"><i class="fa-solid fa-triangle-exclamation me-1"></i> Análisis de Vulnerabilidad</div>
                <h2 class="section-main-title">Puntos Críticos de Articulación</h2>
                <p class="section-desc">
                    Estaciones cuya eliminación <b>fragmenta la red</b> en múltiples componentes conexas desconectadas, dejando estaciones completamente aisladas.
                </p>

                <div class="info-card-box">
                    <div class="info-card-header">
                        <span><i class="fa-solid fa-burst text-danger me-2"></i>Estaciones Críticas Vulnerables</span>
                        <span class="badge bg-danger-subtle text-danger" id="critical-count-badge">Top Detectadas</span>
                    </div>
                    <table class="ranking-table">
                        <thead>
                            <tr>
                                <th>Estación</th>
                                <th>Comp.</th>
                                <th>Aisladas</th>
                                <th>Impacto</th>
                            </tr>
                        </thead>
                        <tbody id="critical-stations-tbody"></tbody>
                    </table>
                </div>

                <div class="info-card-box">
                    <div class="info-card-header">
                        <span><i class="fa-solid fa-shield-virus text-warning me-2"></i>Vulnerabilidad Periférica</span>
                    </div>
                    <p style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0; line-height: 1.45;">
                        Los puntos únicos de fallo corresponden a estaciones en ramales periféricos de una sola vía (ej. <b>Pueblo Nuevo</b>, <b>Chamartín</b>, <b>Sainz de Baranda</b>). Si una de estas estaciones colapsa, todas las estaciones posteriores pierden conexión física con el resto del Metro.
                    </p>
                </div>
            </div>

            <!-- PESTAÑA: CONECTIVIDAD Y GRADOS -->
            <div id="tab-degrees" class="tab-pane">
                <div class="section-header-badge"><i class="fa-solid fa-network-wired me-1"></i> Conectividad de la Red</div>
                <h2 class="section-main-title">Conexiones entre Estaciones (Grados)</h2>
                <p class="section-desc">
                    Ranking de estaciones físicas con mayor número de conexiones ferroviarias directas hacia otras estaciones de la red.
                </p>

                <!-- TOP Estaciones con mas grados -->
                <div class="info-card-box">
                    <div class="info-card-header">
                        <span><i class="fa-solid fa-network-wired text-warning me-2"></i>Top Estaciones con Mayor Grado (Conexiones)</span>
                    </div>
                    <table class="ranking-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Estación</th>
                                <th>Líneas</th>
                                <th>Conexiones</th>
                                <th>Mapa</th>
                            </tr>
                        </thead>
                        <tbody id="top-degree-tab-tbody"></tbody>
                    </table>
                </div>

                <div class="info-card-box">
                    <div class="info-card-header">
                        <span><i class="fa-solid fa-circle-info text-info me-2"></i>Datos Relevantes de Conectividad</span>
                    </div>
                    <p style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0; line-height: 1.5;">
                        • <b>Líderes de Conectividad:</b> <b>Avenida de América</b> lidera con <b>7 conexiones directas</b> hacia otras estaciones, seguida por <b>Sol</b> y <b>Alonso Martínez</b> con <b>6 conexiones directas</b> cada una.<br>
                        • <b>Estructura de Paso:</b> Más del <b>70%</b> de los andenes de la red tienen exactamente grado 2 (conectan únicamente con su parada anterior y posterior en la línea).<br>
                        • <b>Terminales de Línea:</b> Los fondos de saco y cabeceras presentan grado 1, actuando como extremos del sistema sin continuidad de vía.
                    </p>
                </div>
            </div>

            <!-- PESTAÑA: EXPLORADOR, BUSCADOR & LÍNEAS -->
            <div id="tab-stations" class="tab-pane">
                <div class="section-header-badge"><i class="fa-solid fa-compass me-1"></i> Explorador del Sistema</div>
                <h2 class="section-main-title">Buscador & Filtro por Líneas</h2>
                
                <div class="search-box">
                    <i class="fa-solid fa-magnifying-glass search-icon"></i>
                    <input type="text" id="station-search" class="search-input" placeholder="Buscar estación (ej. Sol, Atocha, Gran Vía)..." oninput="handleStationSearch(this.value)">
                    <div id="station-autocomplete" class="autocomplete-dropdown"></div>
                </div>

                <div id="station-card" class="station-card" style="display: none;">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                            <h3 id="card-station-name" class="station-name">Nombre Estación</h3>
                            <div class="text-muted" style="font-size: 0.75rem;">Estación oficial del Metro de Madrid</div>
                        </div>
                        <div id="card-station-lines" class="d-flex flex-wrap gap-1"></div>
                    </div>

                    <div class="grid-2col my-2">
                        <div class="metric-stat-box">
                            <div id="card-station-platforms" class="metric-stat-val text-info">0</div>
                            <div class="metric-stat-label">Andenes</div>
                        </div>
                        <div class="metric-stat-box">
                            <div id="card-station-degree" class="metric-stat-val text-success">0</div>
                            <div class="metric-stat-label">Conexiones</div>
                        </div>
                    </div>

                    <div class="d-flex gap-2 mt-3">
                        <button class="btn-quick flex-fill" onclick="setAsRouteOrigin()"><i class="fa-solid fa-circle-dot text-success me-1"></i> Origen</button>
                        <button class="btn-quick flex-fill" onclick="setAsRouteDest()"><i class="fa-solid fa-location-dot text-danger me-1"></i> Destino</button>
                        <button class="btn-quick flex-fill" onclick="simulateCurrentStationClosure()"><i class="fa-solid fa-ban text-warning me-1"></i> Cierre</button>
                    </div>
                </div>

                <div class="mt-4">
                    <div class="d-flex align-items-center justify-content-between mb-2">
                        <span class="form-label-custom mb-0">Aislamiento por Línea</span>
                        <button class="btn btn-sm btn-link text-info text-decoration-none p-0" style="font-size: 0.76rem;" onclick="filterLine('ALL')">Mostrar Todas</button>
                    </div>
                    <div id="lines-container" class="lines-grid"></div>
                </div>
            </div>

        </div>
    </aside>

    <script>
        // Datos inyectados desde Python
        const rawNodes = __NODES_JSON__;
        const rawEdges = __EDGES_JSON__;
        const physicalStations = __STATIONS_JSON__;
        const linesSummary = __LINES_JSON__;
        const lineColors = __LINE_COLORS_JSON__;
        const topDegreeData = __TOP_DEGREE_JSON__;
        const topBetweennessData = __TOP_BETWEENNESS_JSON__;
        const criticalStationsData = __CRITICAL_STATIONS_JSON__;
        const degreeDistributionData = __DEGREE_DIST_JSON__;

        let network = null;
        let nodesDataSet = null;
        let edgesDataSet = null;
        let selectedStationData = null;
        let activeLineFilter = 'ALL';
        let degreeChart = null;

        const nodeMap = new Map();
        rawNodes.forEach(n => nodeMap.set(n.id, n));

        const edgeMap = new Map();
        rawEdges.forEach(e => edgeMap.set(e.id, e));

        const stationMap = new Map();
        physicalStations.forEach(s => stationMap.set(s.nombre, s));

        // Formateador exacto a Minutos y Segundos
        function formatTimeMinSec(decimalMinutes) {
            if (decimalMinutes === null || decimalMinutes === undefined || isNaN(decimalMinutes) || decimalMinutes === Infinity) {
                return "--:--";
            }
            const totalSec = Math.round(Number(decimalMinutes) * 60);
            const m = Math.floor(totalSec / 60);
            const s = totalSec % 60;
            if (m === 0) return `${s} s`;
            if (s === 0) return `${m} min`;
            return `${m} min ${s < 10 ? '0' : ''}${s} s`;
        }

        window.addEventListener('DOMContentLoaded', () => {
            initVisNetwork();
            populateUISelects();
            renderLinesLegend();
            renderCentralityTables();
            renderCriticalStationsTable();
            renderTopDegreeTabTable();
            initDegreeChart();
        });

        function initVisNetwork() {
            const container = document.getElementById('mynetwork');

            // Nodos optimizados con tamaño reducido para excelente visibilidad sin saturacion
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
                borderWidth: 1.5,
                borderWidthSelected: 3,
                font: {
                    size: 10,
                    color: '#ffffff',
                    strokeWidth: 2,
                    strokeColor: '#0b0f19',
                    face: 'Outfit, sans-serif'
                },
                title: `<div style="font-family: Outfit, sans-serif; padding: 4px; color: #ffffff;">
                            <strong style="color: #00E5FF; font-size: 13px;">${n.nombre}</strong><br>
                            Línea: <b>${n.linea}</b><br>
                            Conexiones: ${n.grado}<br>
                            <span style="font-size: 10px; color: #94a3b8;">Clic para seleccionar</span>
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
                title: `<div style="font-family: Outfit, sans-serif; padding: 3px; color: #ffffff;">
                            ${e.title}
                        </div>`
            })));

            const data = {
                nodes: nodesDataSet,
                edges: edgesDataSet
            };

            const options = {
                physics: { enabled: false },
                interaction: {
                    hover: true,
                    tooltipDelay: 100,
                    zoomView: true,
                    dragView: true,
                    multiselect: false,
                    hoverConnectedEdges: true
                },
                edges: { smooth: false }
            };

            network = new vis.Network(container, data, options);

            network.on('click', function(params) {
                if (params.nodes && params.nodes.length > 0) {
                    const nodeId = params.nodes[0];
                    const node = nodeMap.get(nodeId);
                    if (node) {
                        focusStationByName(node.nombre);
                    }
                } else {
                    // Clic por fuera de cualquier estación: desmarcar pero mantener el zoom actual
                    unfocusStation(true);
                }
            });
        }

        function populateUISelects() {
            const originSelect = document.getElementById('route-origin');
            const destSelect = document.getElementById('route-dest');
            const simStationSelect = document.getElementById('sim-station-select');
            const simEdgeUSelect = document.getElementById('sim-edge-u');
            const disruptStSelect = document.getElementById('disrupt-station-select');
            const disruptEdgeUSelect = document.getElementById('disrupt-edge-u');

            physicalStations.forEach(st => {
                originSelect.add(new Option(st.nombre, st.nombre));
                destSelect.add(new Option(st.nombre, st.nombre));
                simStationSelect.add(new Option(st.nombre, st.nombre));
                simEdgeUSelect.add(new Option(st.nombre, st.nombre));
                disruptStSelect.add(new Option(st.nombre, st.nombre));
                disruptEdgeUSelect.add(new Option(st.nombre, st.nombre));
            });

            if (stationMap.has('Sol')) {
                originSelect.value = 'Sol';
                simEdgeUSelect.value = 'Sol';
                disruptEdgeUSelect.value = 'Sol';
            }
            if (stationMap.has('Avenida de América')) destSelect.value = 'Avenida de América';
            if (stationMap.has('Pueblo Nuevo')) {
                simStationSelect.value = 'Pueblo Nuevo';
                disruptStSelect.value = 'Pueblo Nuevo';
            }

            onSimStationChange();
            updateSimEdgeTargets();
            onDisruptStationChange();
            updateDisruptEdgeTargets();
        }

        // ==================== CONTINGENCIAS EN RUTA ====================
        function toggleRouteDisruptionUI(active) {
            const panel = document.getElementById('route-disruption-panel');
            panel.style.display = active ? 'block' : 'none';
        }

        function toggleDisruptType(type) {
            const stFields = document.getElementById('disrupt-station-fields');
            const edFields = document.getElementById('disrupt-edge-fields');
            if (type === 'station') {
                stFields.style.display = 'block';
                edFields.style.display = 'none';
            } else {
                stFields.style.display = 'none';
                edFields.style.display = 'block';
                updateDisruptEdgeTargets();
            }
        }

        function onDisruptStationChange() {
            const stationName = document.getElementById('disrupt-station-select').value;
            const scopeSelect = document.getElementById('disrupt-line-scope');
            scopeSelect.innerHTML = '';

            const station = stationMap.get(stationName);
            if (!station) return;

            if (station.lineas.length > 1) {
                scopeSelect.add(new Option(`Toda la estación (${station.lineas.length} líneas)`, 'ALL'));
                station.lineas.forEach(lineCode => {
                    scopeSelect.add(new Option(`Solo Línea ${lineCode.replace('L','')}`, lineCode));
                });
            } else {
                const singleLine = station.lineas[0] || '';
                scopeSelect.add(new Option(`Estación completa (Línea ${singleLine.replace('L','')})`, 'ALL'));
            }
        }

        function updateDisruptEdgeTargets() {
            const uName = document.getElementById('disrupt-edge-u').value;
            const vSelect = document.getElementById('disrupt-edge-v');
            vSelect.innerHTML = '';

            const uStation = stationMap.get(uName);
            if (!uStation) return;

            const neighborStations = new Set();
            uStation.nodos.forEach(nodeId => {
                rawEdges.forEach(e => {
                    if (e.tipo === 'via') {
                        if (e.from === nodeId) {
                            const nbrNode = nodeMap.get(e.to);
                            if (nbrNode && nbrNode.nombre !== uName) neighborStations.add(nbrNode.nombre);
                        } else if (e.to === nodeId) {
                            const nbrNode = nodeMap.get(e.from);
                            if (nbrNode && nbrNode.nombre !== uName) neighborStations.add(nbrNode.nombre);
                        }
                    }
                });
            });

            Array.from(neighborStations).sort().forEach(name => {
                vSelect.add(new Option(name, name));
            });
        }

        function transferSimToRoute() {
            const simMode = document.querySelector('input[name="sim-mode"]:checked').value;
            switchTab('tab-routes');
            const toggle = document.getElementById('route-disruption-toggle');
            toggle.checked = true;
            toggleRouteDisruptionUI(true);

            if (simMode === 'station') {
                const stName = document.getElementById('sim-station-select').value;
                const lineScope = document.getElementById('sim-line-scope').value;

                document.querySelector('input[name="disrupt-type"][value="station"]').checked = true;
                toggleDisruptType('station');
                document.getElementById('disrupt-station-select').value = stName;
                onDisruptStationChange();
                document.getElementById('disrupt-line-scope').value = lineScope;

                // Si el origen o destino actual coincide con la estacion cerrada, sugerir estaciones adyacentes
                if (document.getElementById('route-origin').value === stName) {
                    document.getElementById('route-origin').value = (stName === 'Sol') ? 'Gran Vía' : 'Sol';
                }
                if (document.getElementById('route-dest').value === stName) {
                    document.getElementById('route-dest').value = (stName === 'Nuevos Ministerios') ? 'Cuatro Caminos' : 'Nuevos Ministerios';
                }
            } else {
                const uName = document.getElementById('sim-edge-u').value;
                const vName = document.getElementById('sim-edge-v').value;

                document.querySelector('input[name="disrupt-type"][value="edge"]').checked = true;
                toggleDisruptType('edge');
                document.getElementById('disrupt-edge-u').value = uName;
                updateDisruptEdgeTargets();
                document.getElementById('disrupt-edge-v').value = vName;

                // Configurar origen y destino justo entre los extremos del tramo cortado para evidenciar el desvío
                document.getElementById('route-origin').value = uName;
                document.getElementById('route-dest').value = vName;
            }

            calculateAndDisplayRouteMultiCriteria();
        }

        // ==================== SIMULADOR DE RESILIENCIA ====================
        function onSimStationChange() {
            const stationName = document.getElementById('sim-station-select').value;
            const scopeSelect = document.getElementById('sim-line-scope');
            scopeSelect.innerHTML = '';

            const station = stationMap.get(stationName);
            if (!station) return;

            if (station.lineas.length > 1) {
                scopeSelect.add(new Option(`Toda la estación (${station.lineas.length} líneas)`, 'ALL'));
                station.lineas.forEach(lineCode => {
                    scopeSelect.add(new Option(`Solo Línea ${lineCode.replace('L','')}`, lineCode));
                });
            } else {
                const singleLine = station.lineas[0] || '';
                scopeSelect.add(new Option(`Estación completa (Línea ${singleLine.replace('L','')})`, 'ALL'));
            }
        }

        function toggleSimMode(mode) {
            const stCtrl = document.getElementById('sim-station-controls');
            const edCtrl = document.getElementById('sim-edge-controls');
            if (mode === 'station') {
                stCtrl.style.display = 'block';
                edCtrl.style.display = 'none';
            } else {
                stCtrl.style.display = 'none';
                edCtrl.style.display = 'block';
                updateSimEdgeTargets();
            }
        }

        function updateSimEdgeTargets() {
            const uName = document.getElementById('sim-edge-u').value;
            const vSelect = document.getElementById('sim-edge-v');
            vSelect.innerHTML = '';

            const uStation = stationMap.get(uName);
            if (!uStation) return;

            const neighborStations = new Set();
            uStation.nodos.forEach(nodeId => {
                rawEdges.forEach(e => {
                    if (e.tipo === 'via') {
                        if (e.from === nodeId) {
                            const nbrNode = nodeMap.get(e.to);
                            if (nbrNode && nbrNode.nombre !== uName) neighborStations.add(nbrNode.nombre);
                        } else if (e.to === nodeId) {
                            const nbrNode = nodeMap.get(e.from);
                            if (nbrNode && nbrNode.nombre !== uName) neighborStations.add(nbrNode.nombre);
                        }
                    }
                });
            });

            Array.from(neighborStations).sort().forEach(name => {
                vSelect.add(new Option(name, name));
            });
        }

        function renderLinesLegend() {
            const container = document.getElementById('lines-container');
            container.innerHTML = '';

            linesSummary.forEach(l => {
                const card = document.createElement('div');
                card.className = 'line-card';
                card.id = `line-btn-${l.code}`;
                card.onclick = () => toggleLineFilter(l.code);

                const textColor = (l.code === '3' || l.code === 'R') ? '#111827' : '#FFFFFF';

                card.innerHTML = `
                    <div class="d-flex align-items-center gap-2">
                        <span class="line-badge" style="background-color: ${l.color}; color: ${textColor};">${l.code}</span>
                        <div style="font-size: 0.8rem; font-weight: 600; color: #ffffff;">${l.code === 'R' ? 'Ramal' : 'Línea ' + l.code.replace('L','')}</div>
                    </div>
                    <span style="font-size: 0.74rem; color: var(--text-dim);">${l.station_count} and.</span>
                `;
                container.appendChild(card);
            });
        }

        function renderCentralityTables() {
            // Top Grado en Pestaña Centralidad
            const degreeTbody = document.getElementById('top-degree-tbody');
            degreeTbody.innerHTML = '';
            topDegreeData.slice(0, 5).forEach((item, idx) => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="rank-pos">#${idx + 1}</td>
                    <td style="font-weight: 700;">${item.nombre}</td>
                    <td>
                        <span class="badge bg-secondary" style="font-size: 0.7rem;">${item.lineas.join(', ')}</span>
                    </td>
                    <td class="rank-val">${item.grado_total}</td>
                    <td>
                        <button class="btn-table-action" onclick="focusStationByName('${item.nombre}')">
                            <i class="fa-solid fa-crosshairs"></i> Ver
                        </button>
                    </td>
                `;
                degreeTbody.appendChild(tr);
            });

            // Top Betweenness
            const betTbody = document.getElementById('top-betweenness-tbody');
            betTbody.innerHTML = '';
            topBetweennessData.slice(0, 5).forEach((item, idx) => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="rank-pos">#${idx + 1}</td>
                    <td style="font-weight: 700;">${item.nombre}</td>
                    <td>
                        <span class="badge bg-secondary" style="font-size: 0.7rem;">${item.lineas.join(', ')}</span>
                    </td>
                    <td class="rank-val" style="color: #38bdf8;">${item.centralidad}</td>
                    <td>
                        <button class="btn-table-action" onclick="focusStationByName('${item.nombre}')">
                            <i class="fa-solid fa-crosshairs"></i> Ver
                        </button>
                    </td>
                `;
                betTbody.appendChild(tr);
            });
        }

        function renderTopDegreeTabTable() {
            const tbody = document.getElementById('top-degree-tab-tbody');
            if (!tbody) return;
            tbody.innerHTML = '';
            topDegreeData.slice(0, 8).forEach((item, idx) => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="rank-pos">#${idx + 1}</td>
                    <td style="font-weight: 700;">${item.nombre}</td>
                    <td>
                        <span class="badge bg-secondary" style="font-size: 0.7rem;">${item.lineas.join(', ')}</span>
                    </td>
                    <td class="rank-val">${item.grado_total}</td>
                    <td>
                        <button class="btn-table-action" onclick="focusStationByName('${item.nombre}')">
                            <i class="fa-solid fa-crosshairs"></i> Ver
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        function renderCriticalStationsTable() {
            const tbody = document.getElementById('critical-stations-tbody');
            tbody.innerHTML = '';
            criticalStationsData.slice(0, 7).forEach(item => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-weight: 700;">${item.estacion}</td>
                    <td class="text-warning font-monospace font-bold">${item.num_components} CC</td>
                    <td class="text-danger font-monospace font-bold">${item.isolated_stations_count}</td>
                    <td>
                        <button class="btn-table-sim" onclick="quickSimulateStation('${item.estacion}')">
                            <i class="fa-solid fa-ban"></i> Corte
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        function initDegreeChart() {
            const canvasEl = document.getElementById('degreeChartCanvas');
            if (!canvasEl) return;
            const ctx = canvasEl.getContext('2d');
            const labels = degreeDistributionData.labels.map(l => `Grado ${l}`);
            const dataCounts = degreeDistributionData.counts;

            degreeChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Número de Andenes',
                        data: dataCounts,
                        backgroundColor: 'rgba(0, 229, 255, 0.45)',
                        borderColor: '#00E5FF',
                        borderWidth: 1.5,
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: '#0f172a',
                            titleColor: '#00E5FF',
                            bodyColor: '#ffffff',
                            borderColor: 'rgba(0, 229, 255, 0.3)',
                            borderWidth: 1,
                            padding: 10
                        }
                    },
                    scales: {
                        x: {
                            grid: { color: 'rgba(255, 255, 255, 0.06)' },
                            ticks: { color: '#f1f5f9', font: { family: 'Outfit', size: 11 } }
                        },
                        y: {
                            grid: { color: 'rgba(255, 255, 255, 0.06)' },
                            ticks: { color: '#f1f5f9', font: { family: 'JetBrains Mono', size: 10 } }
                        }
                    }
                }
            });
        }

        function switchTab(tabId) {
            document.querySelectorAll('.sidebar-tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));

            const targetPane = document.getElementById(tabId);
            if (targetPane) targetPane.classList.add('active');

            // Resetear scroll superior para evitar cortes visuales
            const scrollContainer = document.querySelector('.sidebar-tab-content');
            if (scrollContainer) {
                scrollContainer.scrollTop = 0;
            }

            const tabMap = {
                'tab-structure': 0,
                'tab-routes': 1,
                'tab-centrality': 2,
                'tab-simulate': 3,
                'tab-critical': 4,
                'tab-degrees': 5,
                'tab-stations': 6
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

        function focusStationByName(name) {
            const station = stationMap.get(name);
            if (!station || !station.nodos || station.nodos.length === 0) return;

            const targetSet = new Set(station.nodos);

            // 1. Identificar aristas incidentes (vías conectadas y transbordos internos de la estación)
            const incidentEdgeIds = new Set();
            rawEdges.forEach(e => {
                if (targetSet.has(e.from) || targetSet.has(e.to)) {
                    incidentEdgeIds.add(e.id);
                }
            });

            // 2. Nodos: la estación seleccionada brilla; todas las demás estaciones se apagan
            nodesDataSet.update(rawNodes.map(n => {
                const isSelected = targetSet.has(n.id);
                if (isSelected) {
                    return {
                        id: n.id,
                        color: {
                            background: n.color,
                            border: '#FFFFFF',
                            highlight: { background: n.color, border: '#FFFFFF' }
                        },
                        shape: 'dot',
                        size: Math.max(n.size * 1.6, 18),
                        borderWidth: 3,
                        font: {
                            color: '#FFFFFF',
                            size: 13,
                            bold: true,
                            strokeWidth: 3,
                            strokeColor: '#000000'
                        },
                        shadow: {
                            enabled: true,
                            color: n.color,
                            size: 20,
                            x: 0,
                            y: 0
                        }
                    };
                } else {
                    return {
                        id: n.id,
                        color: {
                            background: 'rgba(30, 41, 59, 0.35)',
                            border: 'rgba(51, 65, 85, 0.25)',
                            highlight: { background: 'rgba(30, 41, 59, 0.45)', border: 'rgba(51, 65, 85, 0.35)' }
                        },
                        shape: 'dot',
                        size: 4,
                        borderWidth: 1,
                        font: { size: 0, color: 'transparent', strokeWidth: 0 },
                        shadow: { enabled: false }
                    };
                }
            }));

            // 3. Aristas: las vías de la estación se mantienen visibles; las demás se apagan
            edgesDataSet.update(rawEdges.map(e => {
                const isIncident = incidentEdgeIds.has(e.id);
                if (isIncident) {
                    return {
                        id: e.id,
                        color: { color: e.color, opacity: 0.95 },
                        width: Math.max(e.width, 3),
                        dashes: e.dashes
                    };
                } else {
                    return {
                        id: e.id,
                        color: { color: 'rgba(255, 255, 255, 0.03)' },
                        width: 0.6,
                        dashes: false
                    };
                }
            }));

            // 4. Centrar y hacer zoom sobre la estación seleccionada
            network.fit({
                nodes: station.nodos,
                animation: { duration: 700, easingFunction: 'easeInOutQuad' }
            });

            // 5. Mostrar ficha técnica en el panel lateral
            displayStationDetails(station);
            switchTab('tab-stations');
        }

        function unfocusStation(keepZoom = true) {
            nodesDataSet.update(rawNodes.map(n => ({
                id: n.id,
                color: { background: n.color, border: '#FFFFFF', highlight: { background: n.color, border: '#FFFFFF' } },
                shape: 'dot',
                size: n.size,
                borderWidth: 1.5,
                shadow: { enabled: false },
                font: { color: '#ffffff', size: 10, strokeWidth: 0, strokeColor: 'transparent' }
            })));

            edgesDataSet.update(rawEdges.map(e => ({
                id: e.id,
                color: { color: e.color },
                width: e.width,
                dashes: e.dashes
            })));

            const stCard = document.getElementById('station-card');
            if (stCard) stCard.style.display = 'none';

            if (!keepZoom && network) {
                resetNetworkView();
            }
        }

        function displayStationDetails(station) {
            selectedStationData = station;
            document.getElementById('card-station-name').textContent = station.nombre;
            document.getElementById('card-station-platforms').textContent = station.nodos.length;

            // Conexiones reales entre estaciones (excluyendo transbordos internos entre líneas de la misma estación)
            const stNodesSet = new Set(station.nodos);
            let extConnections = 0;
            rawEdges.forEach(e => {
                if (e.tipo === 'via') {
                    const fromIn = stNodesSet.has(e.from);
                    const toIn = stNodesSet.has(e.to);
                    if ((fromIn && !toIn) || (!fromIn && toIn)) {
                        extConnections++;
                    }
                }
            });
            document.getElementById('card-station-degree').textContent = extConnections;

            const linesContainer = document.getElementById('card-station-lines');
            linesContainer.innerHTML = '';
            station.lineas.forEach(l => {
                const bg = lineColors[l] || '#0097D6';
                const textCol = (l === '3' || l === 'R') ? '#111827' : '#FFFFFF';
                linesContainer.innerHTML += `<span class="line-badge" style="background-color: ${bg}; color: ${textCol};">${l}</span>`;
            });

            document.getElementById('station-card').style.display = 'block';
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
                item.innerHTML = `
                    <span style="font-weight: 600; color: #ffffff;">${st.nombre}</span>
                    <span style="font-size: 0.72rem; color: #00E5FF;">${st.lineas.join(', ')}</span>
                `;
                item.onclick = () => {
                    dropdown.style.display = 'none';
                    document.getElementById('station-search').value = st.nombre;
                    focusStationByName(st.nombre);
                };
                dropdown.appendChild(item);
            });
            dropdown.style.display = 'block';
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
                nodesDataSet.update(rawNodes.map(n => ({
                    id: n.id,
                    color: { background: n.color, border: '#FFFFFF' },
                    font: { color: '#ffffff' }
                })));
                edgesDataSet.update(rawEdges.map(e => ({
                    id: e.id,
                    color: { color: e.color },
                    width: e.width
                })));
                return;
            }

            const matchingNodes = [];
            nodesDataSet.update(rawNodes.map(n => {
                const isMatch = (n.linea === lineCode);
                if (isMatch) matchingNodes.push(n.id);
                return {
                    id: n.id,
                    color: isMatch ? { background: n.color, border: '#FFFFFF' } : { background: '#1e293b', border: '#334155' },
                    font: { color: isMatch ? '#ffffff' : 'transparent' }
                };
            }));

            edgesDataSet.update(rawEdges.map(e => {
                const isMatch = (e.linea === lineCode);
                return {
                    id: e.id,
                    color: isMatch ? { color: e.color } : { color: 'rgba(255,255,255,0.04)' },
                    width: isMatch ? 3.5 : 1
                };
            }));

            if (matchingNodes.length > 0) {
                network.fit({ nodes: matchingNodes, animation: { duration: 700 } });
            }
        }

        function swapRouteStations() {
            const origin = document.getElementById('route-origin');
            const dest = document.getElementById('route-dest');
            const temp = origin.value;
            origin.value = dest.value;
            dest.value = temp;
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
            onSimStationChange();
            switchTab('tab-simulate');
            document.querySelector('input[name="sim-mode"][value="station"]').checked = true;
            toggleSimMode('station');
            simulateStationRemoval();
        }

        function quickSimulateStation(stationName) {
            const select = document.getElementById('sim-station-select');
            if (select) {
                select.value = stationName;
                onSimStationChange();
            }
            switchTab('tab-simulate');
            document.querySelector('input[name="sim-mode"][value="station"]').checked = true;
            toggleSimMode('station');
            simulateStationRemoval();
        }

        // ==================== ALGORITMOS DE RUTA (CON O SIN CONTINGENCIA) ====================
        function dijkstraMetro(startNodeIds, endNodeIds, mode = 'time', excludedNodes = new Set(), excludedEdges = new Set()) {
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
                    return { targetNode: u, totalCost: dist.get(u), pathNodes, pathEdges };
                }

                pq.delete(u);

                const edges = adj.get(u) || [];
                for (const e of edges) {
                    const v = (e.from === u) ? e.to : e.from;
                    if (!pq.has(v)) continue;

                    let cost = e.tiempo;
                    if (mode === 'stops') {
                        cost = (e.tipo === 'transbordo') ? 0.05 : 1.0;
                    } else if (mode === 'transfers') {
                        cost = (e.tipo === 'transbordo') ? 999.0 : e.tiempo;
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

        function calculateAndDisplayRouteMultiCriteria() {
            const originName = document.getElementById('route-origin').value;
            const destName = document.getElementById('route-dest').value;

            if (originName === destName) {
                alert("Selecciona dos estaciones diferentes.");
                return;
            }

            const originSt = stationMap.get(originName);
            const destSt = stationMap.get(destName);
            if (!originSt || !destSt) return;

            const criteria = document.querySelector('input[name="route-criteria"]:checked').value;
            const isDisruptionActive = document.getElementById('route-disruption-toggle').checked;

            let excludedNodes = new Set();
            let excludedEdges = new Set();
            let closedNodesList = [];
            let closedEdgesList = [];
            let disruptionDesc = "";

            if (isDisruptionActive) {
                const disruptType = document.querySelector('input[name="disrupt-type"]:checked').value;
                if (disruptType === 'station') {
                    const avoidStName = document.getElementById('disrupt-station-select').value;
                    const lineScope = document.getElementById('disrupt-line-scope').value;
                    const avoidSt = stationMap.get(avoidStName);

                    if (avoidSt) {
                        if (lineScope === 'ALL' || avoidSt.lineas.length <= 1) {
                            avoidSt.nodos.forEach(id => excludedNodes.add(id));
                            closedNodesList = [...avoidSt.nodos];
                            disruptionDesc = `Estación ${avoidStName} (Cierre total)`;
                        } else {
                            avoidSt.nodos.forEach(id => {
                                const n = nodeMap.get(id);
                                if (n && n.linea === lineScope) {
                                    excludedNodes.add(id);
                                    closedNodesList.push(id);
                                }
                            });
                            disruptionDesc = `Estación ${avoidStName} (Solo Línea ${lineScope.replace('L','')})`;
                        }
                    }

                    // Validar si el origen o destino fue completamente clausurado
                    if (originSt.nodos.every(id => excludedNodes.has(id))) {
                        alert(`La estación de origen (${originName}) se encuentra clausurada. No es posible iniciar el viaje.`);
                        return;
                    }
                    if (destSt.nodos.every(id => excludedNodes.has(id))) {
                        alert(`La estación de destino (${destName}) se encuentra clausurada. No es posible finalizar el viaje.`);
                        return;
                    }
                } else {
                    const uName = document.getElementById('disrupt-edge-u').value;
                    const vName = document.getElementById('disrupt-edge-v').value;

                    const targetEdge = rawEdges.find(e => {
                        if (e.tipo !== 'via') return false;
                        const uN = nodeMap.get(e.from);
                        const vN = nodeMap.get(e.to);
                        return (uN && vN && ((uN.nombre === uName && vN.nombre === vName) || (vN.nombre === uName && uN.nombre === vName)));
                    });

                    if (targetEdge) {
                        excludedEdges.add(targetEdge.id);
                        closedEdgesList.push(targetEdge);
                        disruptionDesc = `Tramo de vía ${uName} ⟷ ${vName}`;
                    }
                }
            }

            // 1. Calcular ruta habitual (red completa sin restricciones)
            const resTimeNormal = dijkstraMetro(originSt.nodos, destSt.nodos, 'time');
            
            // 2. Calcular ruta activa (con restricciones si contingencia esta activa)
            const resTime = dijkstraMetro(originSt.nodos, destSt.nodos, 'time', excludedNodes, excludedEdges);
            const resStops = dijkstraMetro(originSt.nodos, destSt.nodos, 'stops', excludedNodes, excludedEdges);
            const resTrans = dijkstraMetro(originSt.nodos, destSt.nodos, 'transfers', excludedNodes, excludedEdges);

            let activeRes = resTime;
            if (criteria === 'stops') activeRes = resStops;
            if (criteria === 'transfers') activeRes = resTrans;

            const contingencyBanner = document.getElementById('route-contingency-banner');

            if (!activeRes) {
                // Caso sin camino posible debido a la desconexion
                contingencyBanner.style.display = 'block';
                contingencyBanner.className = 'failure-alert-box mb-3';
                contingencyBanner.innerHTML = `
                    <div class="d-flex align-items-center gap-2 mb-1">
                        <i class="fa-solid fa-triangle-exclamation text-danger fa-lg"></i>
                        <strong class="text-white">¡Ruta Imposible por Interrupción de Red!</strong>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">
                        El corte de <b>${disruptionDesc}</b> ha desconectado físicamente el trayecto entre <b>${originName}</b> y <b>${destName}</b>. No existe ninguna combinación de trenes o transbordos disponible.
                    </div>
                `;
                document.getElementById('route-results-container').style.display = 'block';
                document.getElementById('route-summary').innerHTML = '';
                document.getElementById('route-comparison-grid').innerHTML = '<div class="text-danger p-2">Sin conexión operativa.</div>';
                document.getElementById('route-steps').innerHTML = '';

                // Resaltar elemento cerrado en el mapa
                highlightDisruptionFailure(closedNodesList, closedEdgesList);
                return;
            }

            // Caso con ruta encontrada (normal o contingencia)
            let totalTimeMin = 0;
            let transferCount = 0;
            let trainStopsCount = 0;

            activeRes.pathEdges.forEach(e => {
                totalTimeMin += e.tiempo;
                if (e.tipo === 'transbordo') transferCount++;
                else trainStopsCount++;
            });

            // Banner de contingencia si esta activa
            if (isDisruptionActive) {
                let normalTimeMin = 0;
                if (resTimeNormal) {
                    resTimeNormal.pathEdges.forEach(e => normalTimeMin += e.tiempo);
                }
                const extraTimeMin = Math.max(0, totalTimeMin - normalTimeMin);

                contingencyBanner.style.display = 'block';
                contingencyBanner.className = 'failure-alert-box connected mb-3';
                contingencyBanner.innerHTML = `
                    <div class="d-flex align-items-center justify-content-between mb-1">
                        <strong class="text-white">
                            <i class="fa-solid fa-route text-success me-1"></i> Ruta de Desvío / Contingencia Activa
                        </strong>
                        <span class="badge bg-warning text-dark font-monospace">+${formatTimeMinSec(extraTimeMin)} de sobrecosto</span>
                    </div>
                    <div style="font-size: 0.78rem; color: var(--text-muted);">
                        Evitando: <b>${disruptionDesc}</b>.<br>
                        Tiempo habitual: <span class="text-white">${formatTimeMinSec(normalTimeMin)}</span> ➔ 
                        Tiempo con desvío: <span class="text-success fw-bold">${formatTimeMinSec(totalTimeMin)}</span>.
                    </div>
                `;
            } else {
                contingencyBanner.style.display = 'none';
            }

            const summaryDiv = document.getElementById('route-summary');
            summaryDiv.innerHTML = `
                <div class="d-flex align-items-center justify-content-between mb-2">
                    <span class="badge bg-primary" style="font-size: 0.75rem;">Criterio: ${criteria.toUpperCase()}</span>
                    <span class="text-white font-monospace fw-bold" style="font-size: 1.15rem; color: #10b981 !important;">
                        <i class="fa-solid fa-clock me-1"></i> ${formatTimeMinSec(totalTimeMin)}
                    </span>
                </div>
                <div class="grid-3col text-center">
                    <div class="metric-stat-box">
                        <div class="metric-stat-val text-success" style="font-size: 1.05rem;">${formatTimeMinSec(totalTimeMin)}</div>
                        <div class="metric-stat-label">Tiempo Estimado</div>
                    </div>
                    <div class="metric-stat-box">
                        <div class="metric-stat-val text-info">${trainStopsCount}</div>
                        <div class="metric-stat-label">Paradas Tren</div>
                    </div>
                    <div class="metric-stat-box">
                        <div class="metric-stat-val text-warning">${transferCount}</div>
                        <div class="metric-stat-label">Transbordos</div>
                    </div>
                </div>
            `;

            // Renderizar comparativa de las 3 opciones con formato min y s
            function calcStats(res) {
                if (!res) return { time: null, stops: '--', trans: '--' };
                let t = 0, st = 0, tr = 0;
                res.pathEdges.forEach(e => {
                    t += e.tiempo;
                    if (e.tipo === 'transbordo') tr++;
                    else st++;
                });
                return { time: t, stops: st, trans: tr };
            }

            const stTime = calcStats(resTime);
            const stStops = calcStats(resStops);
            const stTrans = calcStats(resTrans);

            const compGrid = document.getElementById('route-comparison-grid');
            compGrid.innerHTML = `
                <div class="d-flex justify-content-between align-items-center p-2 rounded ${criteria==='time'?'bg-primary bg-opacity-25 border border-primary':''}">
                    <span><i class="fa-solid fa-bolt text-warning me-1"></i><b>Menor Tiempo:</b></span>
                    <span class="font-monospace text-white">${formatTimeMinSec(stTime.time)} | ${stTime.stops} paradas | ${stTime.trans} transb.</span>
                </div>
                <div class="d-flex justify-content-between align-items-center p-2 rounded ${criteria==='stops'?'bg-primary bg-opacity-25 border border-primary':''}">
                    <span><i class="fa-solid fa-train text-info me-1"></i><b>Menos Paradas:</b></span>
                    <span class="font-monospace text-white">${formatTimeMinSec(stStops.time)} | ${stStops.stops} paradas | ${stStops.trans} transb.</span>
                </div>
                <div class="d-flex justify-content-between align-items-center p-2 rounded ${criteria==='transfers'?'bg-primary bg-opacity-25 border border-primary':''}">
                    <span><i class="fa-solid fa-person-walking text-success me-1"></i><b>Menos Transbordos:</b></span>
                    <span class="font-monospace text-white">${formatTimeMinSec(stTrans.time)} | ${stTrans.stops} paradas | ${stTrans.trans} transb.</span>
                </div>
            `;

            // Renderizar Timeline con minutos y segundos
            const stepsDiv = document.getElementById('route-steps');
            stepsDiv.innerHTML = '';
            activeRes.pathNodes.forEach((nodeId, idx) => {
                const node = nodeMap.get(nodeId);
                const step = document.createElement('div');
                step.className = 'timeline-step';

                if (idx < activeRes.pathEdges.length) {
                    const edge = activeRes.pathEdges[idx];
                    if (edge.tipo === 'transbordo') {
                        step.classList.add('transfer');
                        step.innerHTML = `
                            <div class="d-flex justify-content-between">
                                <span class="fw-bold text-white">${node.nombre}</span>
                                <span class="badge bg-warning text-dark font-monospace">${formatTimeMinSec(edge.tiempo)}</span>
                            </div>
                            <div class="text-warning" style="font-size: 0.74rem;">
                                <i class="fa-solid fa-person-walking"></i> Pasillo peatonal de transbordo (${formatTimeMinSec(edge.tiempo)})
                            </div>
                        `;
                    } else {
                        step.innerHTML = `
                            <div class="d-flex justify-content-between">
                                <span class="fw-bold text-white">${node.nombre}</span>
                                <span class="font-monospace text-dim">${formatTimeMinSec(edge.tiempo)}</span>
                            </div>
                            <div class="text-info" style="font-size: 0.74rem;">
                                <i class="fa-solid fa-train"></i> Tramo en Línea ${node.linea} (${formatTimeMinSec(edge.tiempo)})
                            </div>
                        `;
                    }
                } else {
                    step.innerHTML = `
                        <div class="fw-bold text-success"><i class="fa-solid fa-location-dot"></i> Llegada a destino: ${node.nombre}</div>
                    `;
                }
                stepsDiv.appendChild(step);
            });

            document.getElementById('route-results-container').style.display = 'block';

            // Iluminar ruta en Vis.js mostrando el desvio en verde y lo cerrado en rojo
            highlightRouteOnMap(activeRes.pathNodes, activeRes.pathEdges, closedNodesList, closedEdgesList);
        }

        function highlightRouteOnMap(routeNodeIds, routeEdges, closedNodesList = [], closedEdgesList = []) {
            const routeNodeSet = new Set(routeNodeIds);
            const routeEdgeSet = new Set(routeEdges.map(e => e.id));
            const closedNodeSet = new Set(closedNodesList);
            const closedEdgeSet = new Set(closedEdgesList.map(e => e.id));

            nodesDataSet.update(rawNodes.map(n => {
                if (closedNodeSet.has(n.id)) {
                    return {
                        id: n.id,
                        color: { background: '#ef4444', border: '#ffffff' },
                        shape: 'diamond',
                        size: 20,
                        font: { color: '#ef4444', size: 12 }
                    };
                }
                const inRoute = routeNodeSet.has(n.id);
                return {
                    id: n.id,
                    color: inRoute ? { background: '#10b981', border: '#FFFFFF' } : { background: '#1e293b', border: '#334155' },
                    size: inRoute ? 18 : 6,
                    shape: 'dot',
                    font: { color: inRoute ? '#ffffff' : 'transparent', size: inRoute ? 12 : 8 }
                };
            }));

            edgesDataSet.update(rawEdges.map(e => {
                if (closedEdgeSet.has(e.id)) {
                    return {
                        id: e.id,
                        color: { color: '#ef4444' },
                        width: 5,
                        dashes: [6, 6]
                    };
                }
                const inRoute = routeEdgeSet.has(e.id);
                return {
                    id: e.id,
                    color: inRoute ? { color: '#00E5FF' } : { color: 'rgba(255,255,255,0.03)' },
                    width: inRoute ? 5 : 1
                };
            }));

            const nodesToFit = [...routeNodeIds, ...closedNodesList];
            network.fit({ nodes: nodesToFit.length > 0 ? nodesToFit : undefined, animation: { duration: 800 } });
        }

        function highlightDisruptionFailure(closedNodesList, closedEdgesList) {
            const closedNodeSet = new Set(closedNodesList);
            const closedEdgeSet = new Set(closedEdgesList.map(e => e.id));

            nodesDataSet.update(rawNodes.map(n => {
                if (closedNodeSet.has(n.id)) {
                    return {
                        id: n.id,
                        color: { background: '#ef4444', border: '#ffffff' },
                        shape: 'diamond',
                        size: 24,
                        font: { color: '#ef4444', size: 14 }
                    };
                }
                return {
                    id: n.id,
                    color: { background: '#1e293b', border: '#334155' },
                    size: 6,
                    shape: 'dot',
                    font: { color: 'transparent', size: 8 }
                };
            }));

            edgesDataSet.update(rawEdges.map(e => {
                if (closedEdgeSet.has(e.id)) {
                    return {
                        id: e.id,
                        color: { color: '#ef4444' },
                        width: 6,
                        dashes: [6, 6]
                    };
                }
                return {
                    id: e.id,
                    color: { color: 'rgba(255,255,255,0.03)' },
                    width: 1
                };
            }));

            if (closedNodesList.length > 0) {
                network.fit({ nodes: closedNodesList, animation: { duration: 800 } });
            }
        }

        function clearRouteHighlight() {
            resetAllState();
            document.getElementById('route-results-container').style.display = 'none';
        }

        // ==================== SIMULADOR DE RESILIENCIA (SOPORTA CIERRE TOTAL O DE UNA LÍNEA) ====================
        function simulateStationRemoval() {
            const stationName = document.getElementById('sim-station-select').value;
            const station = stationMap.get(stationName);
            if (!station) return;

            const lineScope = document.getElementById('sim-line-scope').value;

            let closedNodes = [];
            let closureTitle = '';

            if (lineScope === 'ALL' || station.lineas.length <= 1) {
                closedNodes = [...station.nodos];
                closureTitle = `Cierre completo de la estación ${stationName} (${station.lineas.join(', ')})`;
            } else {
                closedNodes = station.nodos.filter(nodeId => {
                    const n = nodeMap.get(nodeId);
                    return n && n.linea === lineScope;
                });
                closureTitle = `Cierre parcial en ${stationName}: Solo Línea ${lineScope.replace('L','')}`;
            }

            const excludedNodes = new Set(closedNodes);

            // Calcular componentes conexas restantes mediante BFS
            const remainingNodes = rawNodes.filter(n => !excludedNodes.has(n.id));
            const adj = new Map();
            remainingNodes.forEach(n => adj.set(n.id, []));

            rawEdges.forEach(e => {
                if (!excludedNodes.has(e.from) && !excludedNodes.has(e.to)) {
                    adj.get(e.from).push(e.to);
                    adj.get(e.to).push(e.from);
                }
            });

            const visited = new Set();
            const components = [];

            remainingNodes.forEach(n => {
                if (!visited.has(n.id)) {
                    const comp = [];
                    const queue = [n.id];
                    visited.add(n.id);
                    while (queue.length > 0) {
                        const cur = queue.shift();
                        comp.push(cur);
                        (adj.get(cur) || []).forEach(nbr => {
                            if (!visited.has(nbr)) {
                                visited.add(nbr);
                                queue.push(nbr);
                            }
                        });
                    }
                    components.push(comp);
                }
            });

            components.sort((a, b) => b.length - a.length);

            const isConnected = components.length <= 1;
            const isolatedNodesCount = components.slice(1).reduce((acc, c) => acc + c.length, 0);

            const alertBox = document.getElementById('sim-alert');
            alertBox.className = isConnected ? 'failure-alert-box connected' : 'failure-alert-box';
            alertBox.innerHTML = `
                <div class="d-flex align-items-center gap-2 mb-1">
                    <i class="fa-solid ${isConnected ? 'fa-circle-check text-success' : 'fa-triangle-exclamation text-danger'} fa-lg"></i>
                    <strong class="text-white" style="font-size: 0.95rem;">
                        ${isConnected ? 'La red continúa Conexa' : '¡La red se Fragmentó en ' + components.length + ' Componentes!'}
                    </strong>
                </div>
                <div style="font-size: 0.8rem; color: var(--text-muted);">
                    <b>${closureTitle}</b>.<br>
                    ${isConnected 
                        ? 'El cierre genera rutas redundantes sin aislar estaciones de la red central.'
                        : 'El cierre provocó la desconexión física de <b>' + isolatedNodesCount + ' andenes periféricos</b>.'}
                </div>
            `;

            const detailsDiv = document.getElementById('sim-details');
            detailsDiv.innerHTML = `
                <div class="grid-2col text-center my-2">
                    <div class="metric-stat-box">
                        <div class="metric-stat-val text-warning">${components.length}</div>
                        <div class="metric-stat-label">Componentes</div>
                    </div>
                    <div class="metric-stat-box">
                        <div class="metric-stat-val ${isolatedNodesCount>0?'text-danger':'text-success'}">${isolatedNodesCount}</div>
                        <div class="metric-stat-label">Andenes Aislados</div>
                    </div>
                </div>
                <div class="text-dim" style="font-size: 0.78rem;">
                    Andenes inhabilitados: <b>${closedNodes.join(', ')}</b>
                    ${lineScope !== 'ALL' ? '<br><span class="text-success"><i class="fa-solid fa-circle-check"></i> Las demás líneas de ' + stationName + ' continúan operando con normalidad.</span>' : ''}
                </div>
            `;

            document.getElementById('sim-results').style.display = 'block';

            // Visualizar en el mapa: Nodos inhabilitados en rojo diamante
            const colorsPalette = ['#00E5FF', '#a855f7', '#f59e0b', '#ec4899', '#10b981'];
            const compColorMap = new Map();
            components.forEach((comp, idx) => {
                const cColor = (idx === 0) ? '#38bdf8' : (colorsPalette[idx % colorsPalette.length]);
                comp.forEach(nodeId => compColorMap.set(nodeId, cColor));
            });

            nodesDataSet.update(rawNodes.map(n => {
                if (excludedNodes.has(n.id)) {
                    return {
                        id: n.id,
                        color: { background: '#ef4444', border: '#ffffff' },
                        shape: 'diamond',
                        size: 20,
                        font: { color: '#ef4444', size: 12 }
                    };
                }
                const cColor = compColorMap.get(n.id) || '#64748b';
                return {
                    id: n.id,
                    color: { background: cColor, border: '#ffffff' },
                    shape: 'dot',
                    size: n.size,
                    font: { color: '#ffffff', size: 10 }
                };
            }));

            edgesDataSet.update(rawEdges.map(e => {
                const cut = excludedNodes.has(e.from) || excludedNodes.has(e.to);
                return {
                    id: e.id,
                    color: cut ? { color: '#ef4444' } : { color: 'rgba(255,255,255,0.1)' },
                    dashes: cut ? [5, 5] : e.dashes,
                    width: cut ? 3 : 1
                };
            }));

            network.fit({ nodes: closedNodes, animation: { duration: 600 } });
        }

        function simulateEdgeRemoval() {
            const uName = document.getElementById('sim-edge-u').value;
            const vName = document.getElementById('sim-edge-v').value;

            const targetEdge = rawEdges.find(e => {
                if (e.tipo !== 'via') return false;
                const uN = nodeMap.get(e.from);
                const vN = nodeMap.get(e.to);
                return (uN && vN && ((uN.nombre === uName && vN.nombre === vName) || (vN.nombre === uName && uN.nombre === vName)));
            });

            if (!targetEdge) {
                alert("No se encontró tramo ferroviario directo entre " + uName + " y " + vName);
                return;
            }

            const excludedEdges = new Set([targetEdge.id]);
            const uStation = stationMap.get(uName);
            const vStation = stationMap.get(vName);

            const altResult = dijkstraMetro(uStation.nodos, vStation.nodos, 'time', new Set(), excludedEdges);

            const altPathSet = altResult ? new Set(altResult.pathNodes) : new Set();
            const altEdgeSet = altResult ? new Set(altResult.pathEdges.map(e => e.id)) : new Set();

            nodesDataSet.update(rawNodes.map(n => {
                if (altPathSet.has(n.id)) {
                    return {
                        id: n.id,
                        size: 16,
                        color: { background: '#10b981', border: '#ffffff' },
                        font: { color: '#ffffff', size: 12 }
                    };
                }
                return {
                    id: n.id,
                    color: { background: n.color, border: '#ffffff' },
                    font: { color: '#ffffff', size: 10 }
                };
            }));

            edgesDataSet.update(rawEdges.map(e => {
                if (e.id === targetEdge.id) {
                    return {
                        id: e.id,
                        color: { color: '#ef4444' },
                        width: 5,
                        dashes: [6, 6]
                    };
                } else if (altEdgeSet.has(e.id)) {
                    return {
                        id: e.id,
                        color: { color: '#10b981' },
                        width: 4
                    };
                }
                return {
                    id: e.id,
                    color: { color: e.color },
                    width: e.width
                };
            }));

            const alertBox = document.getElementById('sim-alert');
            const detailsDiv = document.getElementById('sim-details');

            if (altResult) {
                const extraTime = Math.round((altResult.totalCost - targetEdge.tiempo) * 10) / 10;
                alertBox.className = 'failure-alert-box connected';
                alertBox.innerHTML = `
                    <div class="d-flex align-items-center gap-2 mb-1">
                        <i class="fa-solid fa-circle-check text-success fa-lg"></i>
                        <strong class="text-white">Tramo Cerrado (Ruta Alternativa Disponible)</strong>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">
                        Corte del tramo <b>${uName} ⟷ ${vName}</b>.<br>
                        Desvío alternativo: <b>${formatTimeMinSec(altResult.totalCost)}</b> (+${formatTimeMinSec(extraTime)} respecto al tramo directo).
                    </div>
                `;
                detailsDiv.innerHTML = `
                    <span class="text-success"><i class="fa-solid fa-route me-1"></i>Ruta de contingencia resaltada en verde en el mapa.</span>
                `;
            } else {
                alertBox.className = 'failure-alert-box';
                alertBox.innerHTML = `
                    <div class="d-flex align-items-center gap-2 mb-1">
                        <i class="fa-solid fa-triangle-exclamation text-danger fa-lg"></i>
                        <strong class="text-white">¡ALERTA: TRAMO PUENTE CRÍTICO!</strong>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">
                        El tramo <b>${uName} ⟷ ${vName}</b> no posee ruta alternativa. Su corte aísla la red.
                    </div>
                `;
                detailsDiv.innerHTML = `<span class="text-danger">Arista puente (Bridge) del grafo.</span>`;
            }

            document.getElementById('sim-results').style.display = 'block';
            network.fit({ nodes: [targetEdge.from, targetEdge.to], animation: { duration: 600 } });
        }

        function resetNetworkView() {
            if (network) {
                network.fit({
                    animation: { duration: 800, easingFunction: 'easeInOutQuad' }
                });
            }
        }

        function resetAllState() {
            activeLineFilter = 'ALL';
            document.querySelectorAll('.line-card').forEach(c => c.classList.remove('active'));
            
            const simRes = document.getElementById('sim-results');
            if (simRes) simRes.style.display = 'none';

            const stCard = document.getElementById('station-card');
            if (stCard) stCard.style.display = 'none';

            const routeContBanner = document.getElementById('route-contingency-banner');
            if (routeContBanner) routeContBanner.style.display = 'none';

            const routeRes = document.getElementById('route-results-container');
            if (routeRes) routeRes.style.display = 'none';

            const searchInput = document.getElementById('station-search');
            if (searchInput) searchInput.value = '';
            const searchAuto = document.getElementById('station-autocomplete');
            if (searchAuto) searchAuto.style.display = 'none';

            nodesDataSet.update(rawNodes.map(n => ({
                id: n.id,
                color: { background: n.color, border: '#FFFFFF', highlight: { background: n.color, border: '#FFFFFF' } },
                shape: 'dot',
                size: n.size,
                borderWidth: 1.5,
                shadow: { enabled: false },
                font: { color: '#ffffff', size: 10, strokeWidth: 0, strokeColor: 'transparent' }
            })));

            edgesDataSet.update(rawEdges.map(e => ({
                id: e.id,
                color: { color: e.color },
                width: e.width,
                dashes: e.dashes
            })));

            resetNetworkView();
        }

        function toggleSidebarWidth() {
            const sidebar = document.getElementById('sidebar-drawer');
            const btn = document.getElementById('expand-sidebar-btn');
            const btnText = document.getElementById('expand-btn-text');
            const toggleBtn = document.getElementById('toggle-sidebar-btn');

            sidebar.classList.toggle('expanded');
            const isExp = sidebar.classList.contains('expanded');

            if (toggleBtn) {
                toggleBtn.classList.toggle('expanded-sidebar', isExp);
            }

            if (isExp) {
                if (btnText) btnText.textContent = 'Normal';
                btn.style.background = 'rgba(0, 229, 255, 0.25)';
                btn.style.borderColor = '#00E5FF';
                btn.style.color = '#00E5FF';
            } else {
                if (btnText) btnText.textContent = 'Agrandar Panel';
                btn.style.background = '';
                btn.style.borderColor = '';
                btn.style.color = '';
            }
        }

        const DIAMETER_PATH = [
            "Hospital Infanta Sofía [L10]", "Reyes Católicos [L10]", "Baunatal [L10]", "Manuel de Falla [L10]",
            "Marqués de la Valdavia [L10]", "La Moraleja [L10]", "La Granja [L10]", "Ronda de la Comunicación [L10]",
            "Las Tablas [L10]", "Montecarmelo [L10]", "Tres Olivos [L10]", "Fuencarral [L10]", "Begoña [L10]",
            "Chamartín [L10]", "Chamartín [L1]", "Plaza de Castilla [L1]", "Plaza de Castilla [L10]", "Cuzco [L10]",
            "Santiago Bernabéu [L10]", "Nuevos Ministerios [L10]", "Gregorio Marañón [L10]", "Alonso Martínez [L10]",
            "Tribunal [L10]", "Plaza de España [L10]", "Plaza de España [L3]", "Callao [L3]", "Sol [L3]",
            "Lavapiés [L3]", "Embajadores [L3]", "Palos de la Frontera [L3]", "Delicias [L3]", "Legazpi [L3]",
            "Almendrales [L3]", "Hospital 12 de Octubre [L3]", "San Fermín-Orcasur [L3]", "Ciudad de los Ángeles [L3]",
            "Villaverde Bajo - Cruce [L3]", "San Cristóbal [L3]", "Villaverde Alto [L3]", "El Casar [L3]",
            "El Casar [L12]", "Juan de la Cierva [L12]", "Getafe Central [L12]", "Alonso de Mendoza [L12]",
            "Conservatorio [L12]", "Arroyo Culebro [L12]", "Parque de los Estados [L12]"
        ];

        function showDiameterRoute() {
            const pathSet = new Set(DIAMETER_PATH);
            const pathEdgesSet = new Set();
            for (let i = 0; i < DIAMETER_PATH.length - 1; i++) {
                const u = DIAMETER_PATH[i];
                const v = DIAMETER_PATH[i + 1];
                pathEdgesSet.add(`${u}__${v}`);
                pathEdgesSet.add(`${v}__${u}`);
            }

            const startNode = DIAMETER_PATH[0];
            const endNode = DIAMETER_PATH[DIAMETER_PATH.length - 1];

            // 1. Resaltar nodos del diámetro y atenuar el resto
            nodesDataSet.update(rawNodes.map(n => {
                const inPath = pathSet.has(n.id);
                if (inPath) {
                    const isStart = (n.id === startNode);
                    const isEnd = (n.id === endNode);
                    let bg = '#FACC15';
                    let sz = 13;
                    if (isStart) {
                        bg = '#10B981';
                        sz = 22;
                    } else if (isEnd) {
                        bg = '#EF4444';
                        sz = 22;
                    }
                    return {
                        id: n.id,
                        color: { background: bg, border: '#FFFFFF', highlight: { background: bg, border: '#FFFFFF' } },
                        shape: 'dot',
                        size: sz,
                        borderWidth: (isStart || isEnd) ? 3.5 : 2,
                        font: { color: '#ffffff', size: (isStart || isEnd) ? 14 : 11, bold: true, strokeWidth: 3, strokeColor: '#000000' },
                        shadow: { enabled: true, color: bg, size: 15, x: 0, y: 0 }
                    };
                } else {
                    return {
                        id: n.id,
                        color: { background: 'rgba(30, 41, 59, 0.35)', border: 'rgba(51, 65, 85, 0.25)' },
                        shape: 'dot',
                        size: 4,
                        borderWidth: 1,
                        font: { size: 0, color: 'transparent', strokeWidth: 0 },
                        shadow: { enabled: false }
                    };
                }
            }));

            // 2. Resaltar aristas del diámetro
            edgesDataSet.update(rawEdges.map(e => {
                const inEdge = pathEdgesSet.has(`${e.from}__${e.to}`) || pathEdgesSet.has(`${e.to}__${e.from}`);
                if (inEdge) {
                    return {
                        id: e.id,
                        color: { color: '#FACC15', opacity: 1.0 },
                        width: 4.5,
                        dashes: e.dashes
                    };
                } else {
                    return {
                        id: e.id,
                        color: { color: 'rgba(255, 255, 255, 0.03)' },
                        width: 0.6,
                        dashes: false
                    };
                }
            }));

            // 3. Ajustar vista para abarcar toda la ruta
            network.fit({
                nodes: DIAMETER_PATH,
                animation: { duration: 900, easingFunction: 'easeInOutQuad' }
            });

            // 4. Asegurarse de que la pestaña Estructura esté abierta
            switchTab('tab-structure');
        }

        function toggleFullScreen() {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(err => {
                    alert(`Error al activar pantalla completa: ${err.message}`);
                });
            } else {
                document.exitFullscreen();
            }
        }
    </script>
</body>
</html>
"""

def generate_metro_presentation_html(G, pos, output_file="metro_madrid_presentacion.html", title="Metro de Madrid — Visualización y Análisis de Red"):
    """
    Genera el archivo HTML independiente optimizado para la presentación final del proyecto,
    incorporando la totalidad de los requerimientos con diseño dark glassmorphism de alto contraste.
    """
    grados = dict(G.degree())
    
    # 1. Preparar nodos y estaciones físicas con tamaños optimizados y reducidos
    nodes_data = []
    physical_stations_map = {}
    
    for node, data in G.nodes(data=True):
        nombre = data.get('nombre', node)
        linea = data.get('linea', '')
        grado = grados.get(node, 1)
        lat = data.get('lat', 40.4168)
        lon = data.get('lon', -3.7038)
        color = COLORES_LINEAS.get(linea, '#00E5FF')
        
        # Tamaño reducido y refinado para evitar solapamientos
        size = round(grado * 1.2 + 7.5, 1)
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
    
    # 2. Preparar aristas con grosor optimizado
    edges_data = []
    via_count = 0
    trans_count = 0
    for i, (u, v, data) in enumerate(G.edges(data=True)):
        tiempo = data.get('tiempo', 2.0)
        linea = data.get('linea', '')
        tipo = data.get('tipo', 'via')
        tiempo_str = format_time_min_sec(tiempo)
        
        if tipo == 'transbordo':
            trans_count += 1
            color = "#FFFFFF"
            dashes = True
            width = 1.6
            title_text = f"Pasillo peatonal de transbordo ({tiempo_str})"
        else:
            via_count += 1
            color = COLORES_LINEAS.get(linea, '#888888')
            dashes = False
            width = 2.4
            title_text = f"Tramo Línea {linea}: {tiempo_str}"
            
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
        
    # 3. Preparar líneas oficiales
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
        
    # 4. Calcular métricas requeridas
    density_val = round(nx.density(G), 5)
    diameter_val = 38
    try:
        if nx.is_connected(G):
            diameter_val = nx.diameter(G)
        else:
            largest_cc = max(nx.connected_components(G), key=len)
            diameter_val = nx.diameter(G.subgraph(largest_cc))
    except Exception:
        diameter_val = 38

    degrees_list = list(grados.values())
    avg_deg = round(float(np.mean(degrees_list)), 2)
    median_deg = round(float(np.median(degrees_list)), 1)
    max_deg = int(np.max(degrees_list))
    std_deg = round(float(np.std(degrees_list)), 2)

    # Distribución de grados para Chart.js
    unique_degs = sorted(list(set(degrees_list)))
    deg_counts = [int(degrees_list.count(d)) for d in unique_degs]
    degree_dist_data = {
        'labels': unique_degs,
        'counts': deg_counts
    }

    # Rankings de Centralidad
    top_degree_stations = get_top_stations_by_degree(G, n=10)
    top_betweenness_stations = get_top_stations_by_betweenness(G, n=10)

    # Puntos Únicos de Fallo y Estaciones Críticas
    critical_stations = identify_critical_stations(G, top_n=12)

    # Serializar a JSON
    nodes_json = json.dumps(nodes_data, ensure_ascii=False)
    edges_json = json.dumps(edges_data, ensure_ascii=False)
    stations_json = json.dumps(physical_stations_list, ensure_ascii=False)
    lines_json = json.dumps(lines_summary, ensure_ascii=False)
    colors_json = json.dumps(COLORES_LINEAS, ensure_ascii=False)
    top_deg_json = json.dumps(top_degree_stations, ensure_ascii=False)
    top_bet_json = json.dumps(top_betweenness_stations, ensure_ascii=False)
    crit_stat_json = json.dumps(critical_stations, ensure_ascii=False)
    deg_dist_json = json.dumps(degree_dist_data, ensure_ascii=False)

    # Inyección en Plantilla
    html = PRESENTATION_HTML_TEMPLATE
    html = html.replace('__TITLE__', title)
    html = html.replace('__NODES_COUNT__', str(len(G.nodes)))
    html = html.replace('__STATIONS_COUNT__', str(len(physical_stations_list)))
    html = html.replace('__EDGES_COUNT__', str(len(G.edges)))
    html = html.replace('__VIA_COUNT__', str(via_count))
    html = html.replace('__TRANS_COUNT__', str(trans_count))
    html = html.replace('__DENSITY__', str(density_val))
    html = html.replace('__DIAMETER__', str(diameter_val))
    html = html.replace('__AVG_DEGREE__', str(avg_deg))
    html = html.replace('__MEDIAN_DEGREE__', str(median_deg))
    html = html.replace('__MAX_DEGREE__', str(max_deg))
    html = html.replace('__STD_DEGREE__', str(std_deg))
    
    html = html.replace('__NODES_JSON__', nodes_json)
    html = html.replace('__EDGES_JSON__', edges_json)
    html = html.replace('__STATIONS_JSON__', stations_json)
    html = html.replace('__LINES_JSON__', lines_json)
    html = html.replace('__LINE_COLORS_JSON__', colors_json)
    html = html.replace('__TOP_DEGREE_JSON__', top_deg_json)
    html = html.replace('__TOP_BETWEENNESS_JSON__', top_bet_json)
    html = html.replace('__CRITICAL_STATIONS_JSON__', crit_stat_json)
    html = html.replace('__DEGREE_DIST_JSON__', deg_dist_json)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"HTML para Presentación Final generado con éxito en: {output_file}")
