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
        out_path = json_path.replace('.json', '_out')
        script_path = os.path.join(os.path.dirname(__file__), 'build_estilo_ssm.py')
        resultado = subprocess.run(
            ['python3', script_path, json_path, out_path],
            capture_output=True, text=True, timeout=90
        )
        if resultado.returncode != 0:
            return jsonify({"error": "Error en script de dibujo", "detalle": resultado.stderr}), 500
        png_path = out_path + '.png'
        if not os.path.exists(png_path):
            return jsonify({"error": "El script no generó el PNG"}), 500
        with open(png_path, 'rb') as f:
            png_b64 = base64.b64encode(f.read()).decode('utf-8')
        for p in [json_path, png_path, out_path + '.svg']:
            try:
                os.remove(p)
            except:
                pass
        return jsonify({"data": png_b64})
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timeout"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
