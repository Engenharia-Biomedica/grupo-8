#importar bibliotecas para funcionar o programa
from flask import Flask, render_template, jsonify, request
from autofill import autofill
from flask_cors import CORS
import pandas as pd
import numpy as np
from thefuzz import fuzz, process
from datetime import datetime

# Cria um flask para permitir comunicacao com o site
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:8501"}})

#Carrega dados de um CSV para um DataFrame do pandas
meds = pd.DataFrame(pd.read_csv('static\sample_data_clean.csv', sep=','))

#Função para encontrar as palavras mais parecidas com a palavra digitada# Encontra correspondencia para um string de busca
def find_matches(df, search_string):
    # Converter todas as palavras em minusculo para não ter problema na ocmparação de maiuscula com minuscula
    autofill_words = df['ds_micro_organismo'].str.lower().tolist()
    raw_probable_words = process.extract(
        search_string, autofill_words, limit=5)
    query = []
    #Palavras com maior ou igual a 75% de certeza da palavra digitada
    for i in range(len(raw_probable_words)):
        if raw_probable_words[i][1] >= 75:
            query.append(raw_probable_words[i][0])

    # Register words with autofill (assuming autofill expects lowercase words)
    autofill.register_words(autofill_words)
    lower_search_string = search_string.lower()

    # Pesquisar palavras com a palavra digitada
    if query == []:
        query = autofill.search(lower_search_string) if lower_search_string not in autofill_words else [
            lower_search_string]

    # Converter o Dataframe para minusculo
    lower_df = df.apply(lambda x: x.astype(str).str.lower())

    matches = []
    for word in query:
        # Achar a localização
        result = np.where(lower_df['ds_micro_organismo'] == word)
        row_indices = result[0]

        # Combina bacteria com linha
        for row in row_indices:
            matches.append((word, row))

    return matches

#Funcionamento do site: quando o site recebe uma mensagem, ele chama a função predict
@app.route('/message', methods=['POST'])
def predict():
    data = request.get_json()

    if request.is_json and 'bacteria' in data:
        bacteria = data['bacteria']

        results = []
        time_data = {}
        resistence = {}
        matches = find_matches(meds, bacteria)
        print(matches)

        for match in matches:
            disease, row_index = match
            antibiotic = meds['ds_antibiotico_microorganismo'].iloc[row_index]
            micro_organism = meds['ds_micro_organismo'].iloc[row_index]

            # Checar se não tem valores nulos e adcicionar em resultados 
            if pd.notna(antibiotic) and pd.notna(micro_organism):
                result = (antibiotic, micro_organism)
                results.append(result)

                # Collect time data for each disease ( for time)
                time_str = meds['dh_ultima_atualizacao'].iloc[row_index]
                time_data.setdefault(disease, []).append(
                    datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S.%f'))

        

        # Remove duplicações para o resultado
        results = list(set(results))
        oldest_latest_times = {disease: (min(times), max(
            times)) for disease, times in time_data.items()}
        print(oldest_latest_times)
        return jsonify({'results': results, 'time_data': oldest_latest_times}), 200
    else:
        return 'Request was not JSON', 415


if __name__ == '__main__':
    app.run(debug=True, port=5000)
