import json
import sys
import math
import re
import textwrap
import graphviz
import tempfile
import os

def envolver_texto(texto, ancho_max=18):
    lineas = textwrap.wrap(texto, width=ancho_max, break_long_words=False)
    return '\n'.join(lineas)

def construir_modelo(json_path, salida='modelo_estilo_ssm'):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    n = len(data['actividades'])

    g = graphviz.Graph('modelo', format='svg', engine='neato')
    g.attr(bgcolor='white', fontname='DejaVu Sans', overlap='false',
           splines='curved', size='15,10', pad='0.6')

    cx, cy, r = 6.4, 4.3, 3.3
    pos = {}
    for i, act in enumerate(data['actividades']):
        angulo = math.pi/2 - 2*math.pi*i/n
        x = cx + r * math.cos(angulo)
        y = cy + r * math.sin(angulo) * 0.78
        pos[act['id']] = (x, y)

    input_txt = envolver_texto(data['input'], ancho_max=26)
    output_txt = envolver_texto(data['output'], ancho_max=26)

    g.node('INPUT', input_txt, shape='box', style='filled,rounded',
           fillcolor='#d9ead3', color='#999999', fontsize='13',
           fontname='DejaVu Sans', margin='0.35,0.3', width='2.3',
           pos=f"{cx-r-3.3},{cy}!")
    g.node('OUTPUT', output_txt, shape='box', style='filled,rounded',
           fillcolor='#d9ead3', color='#999999', fontsize='13',
           fontname='DejaVu Sans', margin='0.35,0.3', width='2.3',
           pos=f"{cx+r+3.3},{cy}!")

    for act in data['actividades']:
        x, y = pos[act['id']]
        etiqueta = f"{act['id'][1:]}. " + envolver_texto(act['texto'], ancho_max=16)
        g.node(act['id'], etiqueta,
               shape='ellipse', style='filled', fillcolor='#c5e0a5',
               color='#a9c97a', fontname='DejaVu Sans Condensed Oblique',
               fontsize='12.5', fontcolor='#2c3a08', width='2.0', height='1.15',
               margin='0.18,0.12', pos=f"{x},{y}!")

    for origen, destino in data['flechas']:
        g.edge(origen, destino, color='#444444', penwidth='0.9',
               arrowsize='0.6', dir='forward')

    # Usar /tmp para Railway (no /home/claude/render/)
    out_path = salida if salida.startswith('/') else f'/tmp/{salida}'
    svg_path = g.render(out_path, cleanup=True)

    insertar_frontera_y_flechas(svg_path, cx, cy, r)

    png_path = svg_path.replace('.svg', '.png')

    # Convertir SVG a PNG sin cairosvg — usando svglib + reportlab
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM
        drawing = svg2rlg(svg_path)
        if drawing is None:
            raise ValueError("svg2rlg devolvio None")
        renderPM.drawToFile(drawing, png_path, fmt='PNG', dpi=150)
    except Exception as e:
        # Fallback: devolver el SVG como PNG usando Pillow si está disponible
        try:
            from PIL import Image
            import io
            # Si no hay conversor, guardar el SVG renombrado como indicador
            raise RuntimeError(f"No se pudo convertir SVG a PNG: {e}")
        except Exception as e2:
            raise RuntimeError(f"Conversion fallida: {e} / {e2}")

    print(f"Generado: {svg_path}")
    print(f"Generado: {png_path}")
    return svg_path, png_path

def insertar_frontera_y_flechas(svg_path, cx, cy, r):
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg = f.read()

    ellipses = re.findall(
        r'<ellipse[^>]*cx="([\-\d.]+)"[^>]*cy="([\-\d.]+)"[^>]*rx="([\-\d.]+)"[^>]*ry="([\-\d.]+)"',
        svg)
    if not ellipses:
        return
    xs_min = min(float(e[0]) - float(e[2]) for e in ellipses)
    xs_max = max(float(e[0]) + float(e[2]) for e in ellipses)
    ys_min = min(float(e[1]) - float(e[3]) for e in ellipses)
    ys_max = max(float(e[1]) + float(e[3]) for e in ellipses)

    margen = 42
    fx = (xs_min + xs_max) / 2
    fy = (ys_min + ys_max) / 2
    frx = (xs_max - xs_min) / 2 + margen
    fry = (ys_max - ys_min) / 2 + margen * 0.7

    frontera_svg = (f'<ellipse cx="{fx:.1f}" cy="{fy:.1f}" rx="{frx:.1f}" ry="{fry:.1f}" '
                     f'fill="none" stroke="#777777" stroke-width="1" stroke-dasharray="2,3"/>\n')

    entrada_x = fx - frx
    salida_x = fx + frx

    def bbox_desde_path(titulo):
        m = re.search(rf'<title>{titulo}</title>\s*<path[^>]*d="([^"]+)"', svg)
        if not m:
            return None
        coords = re.findall(r'(-?\d+\.?\d*),(-?\d+\.?\d*)', m.group(1))
        xs = [float(c[0]) for c in coords]
        ys = [float(c[1]) for c in coords]
        return min(xs), max(xs), min(ys), max(ys)

    input_bb = bbox_desde_path('INPUT')
    output_bb = bbox_desde_path('OUTPUT')

    flechas_svg = ''
    if input_bb:
        x_min, x_max, y_min, y_max = input_bb
        cy_in = (y_min + y_max) / 2
        x0, y0 = x_max + 8, cy_in
        x1, y1 = entrada_x, cy_in
        flechas_svg += (
            f'<path d="M {x0:.1f} {y0:.1f} L {x1:.1f} {y1:.1f}" '
            f'fill="none" stroke="#bbbbbb" stroke-width="9" '
            f'marker-end="url(#flecha_io)"/>\n'
        )
    if output_bb:
        x_min, x_max, y_min, y_max = output_bb
        cy_out = (y_min + y_max) / 2
        x0, y0 = salida_x, cy_out
        x1, y1 = x_min - 8, cy_out
        flechas_svg += (
            f'<path d="M {x0:.1f} {y0:.1f} L {x1:.1f} {y1:.1f}" '
            f'fill="none" stroke="#bbbbbb" stroke-width="9" '
            f'marker-end="url(#flecha_io)"/>\n'
        )

    defs_marker = (
        '<defs><marker id="flecha_io" viewBox="0 0 10 10" refX="8" refY="5" '
        'markerWidth="5" markerHeight="5" orient="auto-start-reverse">'
        '<path d="M1 1 L9 5 L1 9 Z" fill="#bbbbbb"/></marker></defs>\n'
    )

    inserto = defs_marker + frontera_svg + flechas_svg

    marker = '<polygon fill="white"'
    idx = svg.find(marker)
    if idx == -1:
        svg = svg.replace('</svg>', inserto + '</svg>')
    else:
        fin_polygon = svg.find('/>', idx) + 2
        svg = svg[:fin_polygon] + '\n' + inserto + svg[fin_polygon:]

    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(svg)

if __name__ == '__main__':
    json_path = sys.argv[1] if len(sys.argv) > 1 else 'modelo_loreto_total.json'
    salida = sys.argv[2] if len(sys.argv) > 2 else '/tmp/modelo_estilo_ssm'
    construir_modelo(json_path, salida)
