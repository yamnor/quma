from bottle import Bottle, static_file, template, request, run
import json

from gms_parser import gparse

app = Bottle()

@app.route('/static/:path#.+#')
def static(path):
  return static_file(path, root='static')

@app.route('/favicon.ico')
def favcon():
    return static_file('favicon.ico', root='static')

@app.route('/data/:path#.+#')
def static(path):
  return static_file(path, root='data')

def load_molecules():
  with open('data/molecules.json', 'r') as file:
    data = json.load(file)
  return data['molecules']

molecules = load_molecules()

@app.route("/")
def index():
  return template("index.html", molecules = molecules, gms = gparse("Water", "HF", "STO-3G"))

@app.route("/", method="POST")
def view():
  molecule = request.forms.get("selected-molecule")
  method = request.forms.get("selected-method")
  basis = request.forms.get("selected-basis")
  return template("index.html", molecules = molecules, gms = gparse(molecule, method, basis))

if __name__ == "__main__":
  app.run(host='localhost', port=8080)
