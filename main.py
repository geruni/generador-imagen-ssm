import os
import json
import tempfile
import subprocess
import base64
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET'])
def root():
    return jsonify({"status": "ok"})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/generar', methods=['POST'])
def generar():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Body JSON vacío"}), 400
        for clave in ('input', 'output', 'actividades', 'flechas'):
            if clave not in data:
                return jsonify({"error": f"Falta clave: {clave}"}), 400

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, encoding='utf-8'
        ) as f:
            json.dump(data, f, ensure_ascii=False)
            json_path = f.name

        out_base = json_path.replace('.json', '_out')
        script_path = os.path.join(os.path.dirname(__file__), 'build_estilo_ssm.py')

        resultado = subprocess.run(
            ['python3', script_path, json_path, out_base],
            capture_output=True, text=True, timeout=90
        )

        if resultado.returncode != 0:
            return jsonify({
                "error": "Error en script de dibujo",
                "detalle": resultado.stderr
            }), 500

        # Intentar PNG primero, luego SVG como fallback
        png_path = out_base + '.png'
        svg_path = out_base + '.svg'

        if os.path.exists(png_path):
            with open(png_path, 'rb') as f:
                contenido_b64 = base64.b64encode(f.read()).decode('utf-8')
            tipo = 'png'
        elif os.path.exists(svg_path):
            with open(svg_path, 'rb') as f:
                contenido_b64 = base64.b64encode(f.read()).decode('utf-8')
            tipo = 'svg'
        else:
            return jsonify({"error": "No se generó ningún archivo de imagen"}), 500

        # Limpiar temporales
        for p in [json_path, png_path, svg_path]:
            try:
                os.remove(p)
            except Exception:
                pass

        return jsonify({
            "data": contenido_b64,
            "tipo": tipo,
            "actividades": len(data.get('actividades', [])),
            "flechas": len(data.get('flechas', []))
        })

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timeout: el script tardó más de 90s"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
