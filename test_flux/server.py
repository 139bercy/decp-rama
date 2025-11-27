# This example sets up an endpoint using the Flask framework.
# Watch this video to get started: https://youtu.be/7Ul1vfmsDck.
#pip install --upgrade flask
#pip install --upgrade stripe

import os
#import stripe

from flask import Flask, jsonify, send_file

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
  #os.path.join(app.config['UPLOAD_FOLDER'], 'resp.xml')
  #return send_file('flux_exemple_estOCSProgramme.xml')
  #return send_file('null.xml')
  #return send_file('agrf2_cdm_exemple_seconde.xml')
  #return send_file('agrf2_cdm_exemple_minute.xml')
  #return send_file('agrf3_cdm_exemple_seconde.xml')
  #return send_file('multi-full.xml')
  #return send_file('multi-error.xml')
  #return send_file('multi-empty.xml')
  #return send_file('response_1678803776901_new_entreprises_participantes.xml')
  #return send_file('_exemple_agr_f2_ent_participantes.xml')
  #return send_file('_flux_agr_f2-entreprises_participantes_operations.xml')
  #return send_file('flux_agrf\\agrf3_cdm_exemple_seconde.xml')
  #return send_file('20240704\\AGR_F2_ALPC_3446_2024-06-26T10_27_36.322+00_00.xml')

  #return send_file('source_test/index.json')
  return send_file('json/batch_sortie_avec_balise_source_ok.json')

@app.route('/json/sample.json', methods=['GET'])
def source_test():
  return send_file('json/batch_sortie_avec_balise_source_ok.json')

@app.route('/f2', methods=['GET'])
def dataf2():
  return send_file('20240704\\AGR_F2_CDM_21_27.xml')
  #return send_file('20240704\\AGR_F2_ALPC_3446_2024-06-26T10_27_36.322+00_00.xml')
  #return send_file('20240704\\AGR_F2_ALPC_3475_2024-07-03T09_26_23.972+00_00.xml')

@app.route('/f3', methods=['GET'])
def dataf3():
  return send_file('20240704\\AGR_F3_CDM_21_27.xml')

@app.route('/data-2022-decp-json', methods=['GET'])
def data2022decpjson():
  #return send_file('decp2022\\DAJ_Json_test_DECP_2022.json')
  return send_file('decp_2022_tests\\JSONFORMAT2022_marche_second_envoi.json')

@app.route('/data-2022-decp-xml', methods=['GET'])
def data2022decpxml():
  #return send_file('decp2022\\DAJ_Json_test_DECP_2022.xml')
  #return send_file('decp_2022_tests\\JSONFORMAT2022_concession_second_envoi.json')
  return send_file('decp_2022_tests\\decp_v2.0.1.xml')

@app.route('/vlad-xml', methods=['GET'])
def data2022vladxml():
  #return send_file('vlad\\VLAD_Json_test_DECP_2022_AXYUS.xml')
  #return send_file('vlad\\decp_v2.0.1.xml')
  #return send_file('vlad\\decp_v2.0.1_20240129.xml')
  #return send_file('demo\\Contrat-concession.xml')
  #return send_file('demo\\Contrat-concession-modification.xml')
  #return send_file('demo\\Marche.xml')
  #return send_file('demo\\Marche-modification.xml')
  #return send_file('20240423\\DGFIP_ADRIEN_v1.xml')
  #return send_file('20240423\\DGFIP_ADRIEN_v2.xml')
  #return send_file('20240423\\DGFIP_ADRIEN_v3.xml')
  #return send_file('20240423\\dgfip_v1.xml')
  #return send_file('20240423\\dgfip_v2.xml')
  #return send_file('20240423\\dgfip_v3.xml')
  return send_file('20240424\\dgfip_v2.xml')
  
  #return send_file('demo\\paquet.xml')


@app.route('/vlad-json', methods=['GET'])
def data2022vladjson():
  #return send_file('demo\\decp_concession.json')
  #return send_file('demo\\decp_concession_avec_modifications.json')
  #return send_file('demo\\decp_concession_moitie_sans_modifications.json')
  #return send_file('demo\\decp_marche.json')
  #return send_file('demo\\decp_marche_avec_modifications.json')
  #return send_file('demo\\decp_marche_moitie_sans_modifications.json')
  #return send_file('demo\\decp_sample.json')
  #return send_file('demo\\decp_sample_moitie_sans_modifications.json')
  return send_file('demo\\decp_sample_sans_modifications.json')


@app.route('/decp-json', methods=['GET'])
def datadecpjson():
  return send_file('decp_tests\\decp_v2.json')

@app.route('/decp-xml', methods=['GET'])
def datadecpxml():
  #return send_file('xml\\donnees-essentielles-marches26.03.2025.01-30.xml')
  return send_file('xml\\Donnees-Essentielles-Marches09.04.2025.10-58.xml')

if __name__== '__main__':
    #app.run(port=4242,ssl_context='adhoc')
    app.run(port=4242)
