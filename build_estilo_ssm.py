import json
import sys
import math
import textwrap
import base64
import os

def envolver_texto(texto, ancho_max=16):
    lineas = textwrap.wrap(texto, width=ancho_max, break_long_words=False)
    return lineas

def construir_modelo(json_path, salida='modelo_estilo_ssm'):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    n = len(data['actividades'])
    W, H = 1400, 820
    cx, cy = W / 2, H / 2 - 20
    rx_anillo = 310
    ry_anillo = 230

    # Posiciones en anillo elíptico
    pos = {}
    for i, act in enumerate(data['actividades']):
        angulo = math.pi / 2 - 2 * math.pi * i / n
        x = cx + rx_anillo * math.cos(angulo)
        y = cy + ry_anillo * math.sin(angulo)
        pos[act['id']] = (x, y)

    # Frontera del sistema
    frx = rx_anillo + 60
    fry = ry_anillo + 55

    # Dimensiones de las cajas input/output
    box_w, box_h = 190, 110
    input_x = cx - frx - box_w - 30
    output_x = cx + frx + 30
    box_y = cy - box_h / 2

    svg_parts = []
    svg_parts.append(f'<svg width="{W+200}" height="{H}" viewBox="-100 0 {W+200} {H}" xmlns="http://www.w3.org/2000/svg">')
    svg_parts.append('<defs>')
    svg_parts.append('<marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M1 1 L9 5 L1 9 Z" fill="#555"/></marker>')
    svg_parts.append('<marker id="arr_io" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M1 1 L9 5 L1 9 Z" fill="#aaa"/></marker>')
    svg_parts.append('</defs>')

    # Fondo blanco
    svg_parts.append(f'<rect width="100%" height="100%" fill="white"/>')

    # Frontera punteada
    svg_parts.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{frx}" ry="{fry}" fill="none" stroke="#888" stroke-width="1.2" stroke-dasharray="4,4"/>')

    # Flechas input/output rectas
    arrow_y = cy
    # INPUT → frontera
    ix0 = input_x + box_w
    ix1 = cx - frx
    svg_parts.append(f'<line x1="{ix0}" y1="{arrow_y}" x2="{ix1}" y2="{arrow_y}" stroke="#bbb" stroke-width="8" marker-end="url(#arr_io)"/>')
    # frontera → OUTPUT
    ox0 = cx + frx
    ox1 = output_x
    svg_parts.append(f'<line x1="{ox0}" y1="{arrow_y}" x2="{ox1}" y2="{arrow_y}" stroke="#bbb" stroke-width="8" marker-end="url(#arr_io)"/>')

    # Caja INPUT
    svg_parts.append(f'<rect x="{input_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="8" fill="#d9ead3" stroke="#999" stroke-width="1"/>')
    lineas_in = envolver_texto(data['input'], ancho_max=22)
    total_in = len(lineas_in)
    for i, linea in enumerate(lineas_in):
        ly = box_y + box_h/2 - (total_in-1)*9 + i*18
        svg_parts.append(f'<text x="{input_x + box_w/2}" y="{ly}" text-anchor="middle" font-family="Arial" font-size="11" fill="#333">{_esc(linea)}</text>')

    # Caja OUTPUT
    svg_parts.append(f'<rect x="{output_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="8" fill="#d9ead3" stroke="#999" stroke-width="1"/>')
    lineas_out = envolver_texto(data['output'], ancho_max=22)
    total_out = len(lineas_out)
    for i, linea in enumerate(lineas_out):
        ly = box_y + box_h/2 - (total_out-1)*9 + i*18
        svg_parts.append(f'<text x="{output_x + box_w/2}" y="{ly}" text-anchor="middle" font-family="Arial" font-size="11" fill="#333">{_esc(linea)}</text>')

    # Flechas internas curvas entre actividades
    id_to_pos = pos
    for origen, destino in data['flechas']:
        if origen not in id_to_pos or destino not in id_to_pos:
            continue
        x1, y1 = id_to_pos[origen]
        x2, y2 = id_to_pos[destino]
        # Punto de control curvado hacia el centro
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        # Curvar hacia el centro del anillo
        dx = cx - mx
        dy = cy - my
        dist = math.sqrt(dx*dx + dy*dy) or 1
        factor = 0.25
        cpx = mx + dx * factor
        cpy = my + dy * factor
        svg_parts.append(f'<path d="M {x1:.1f} {y1:.1f} Q {cpx:.1f} {cpy:.1f} {x2:.1f} {y2:.1f}" fill="none" stroke="#555" stroke-width="1.2" marker-end="url(#arr)"/>')

    # Óvalos de actividades
    ow, oh = 130, 68
    for act in data['actividades']:
        x, y = pos[act['id']]
        num = act['id'][1:] if len(act['id']) > 1 else act['id']
        lineas = envolver_texto(act['texto'], ancho_max=14)
        svg_parts.append(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{ow//2}" ry="{oh//2}" fill="#c5e0a5" stroke="#a9c97a" stroke-width="1.2"/>')
        # Número arriba
        total_l = len(lineas)
        start_y = y - (total_l * 10) / 2 + 5
        svg_parts.append(f'<text x="{x:.1f}" y="{start_y - 6:.1f}" text-anchor="middle" font-family="Arial" font-size="9" font-style="italic" fill="#2c3a08">{num}.</text>')
        for i, linea in enumerate(lineas):
            ty = start_y + i * 13
            svg_parts.append(f'<text x="{x:.1f}" y="{ty:.1f}" text-anchor="middle" font-family="Arial" font-size="10" font-style="italic" fill="#2c3a08">{_esc(linea)}</text>')

    svg_parts.append('</svg>')
    svg_content = '\n'.join(svg_parts)

    # Guardar SVG
    out_base = salida if salida.startswith('/') else f'/tmp/{salida}'
    svg_path = out_base + '.svg'
    png_path = out_base + '.png'

    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)

    # Convertir SVG a PNG con svglib si está disponible, sino devolver SVG como PNG fake
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM
        drawing = svg2rlg(svg_path)
        renderPM.drawToFile(drawing, png_path, fmt='PNG', dpi=150)
    except Exception:
        # Fallback: devolver el SVG directamente (el cliente lo decodifica igual)
        png_path = svg_path

    print(f"Generado: {svg_path}")
    print(f"Generado: {png_path}")
    return svg_path, png_path

def _esc(texto):
    return texto.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

if __name__ == '__main__':
    json_path = sys.argv[1] if len(sys.argv) > 1 else 'modelo.json'
    salida = sys.argv[2] if len(sys.argv) > 2 else '/tmp/modelo_estilo_ssm'
    construir_modelo(json_path, salida)
