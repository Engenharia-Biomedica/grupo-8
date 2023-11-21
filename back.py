from flask import Flask, render_template, jsonify, request
from autofill import autofill
from flask_cors import CORS
import pandas as pd
import numpy as np
from thefuzz import fuzz, process
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:8501"}})


meds = pd.DataFrame(pd.read_csv('static\sample_data_clean.csv', sep=','))


def find_matches(df, search_string):
    # Convert all words to lowercase for case-insensitive comparison
    autofill_words = df['ds_micro_organismo'].str.lower().tolist()
    raw_probable_words = process.extract(
        search_string, autofill_words, limit=5)
    query = []
    for i in range(len(raw_probable_words)):
        if raw_probable_words[i][1] >= 75:
            if raw_probable_words[i][1] == 100:
                print('jackpot bitches!')
            query.append(raw_probable_words[i][0])

    # Register words with autofill (assuming autofill expects lowercase words)
    autofill.register_words(autofill_words)
    lower_search_string = search_string.lower()

    # Perform the search
    if query == []:
        query = autofill.search(lower_search_string) if lower_search_string not in autofill_words else [
            lower_search_string]

    # Convert the DataFrame to lowercase once
    lower_df = df.apply(lambda x: x.astype(str).str.lower())

    matches = []
    for word in query:
        # Finding the location
        result = np.where(lower_df['ds_micro_organismo'] == word)
        row_indices = result[0]

        # Append matches
        for row in row_indices:
            matches.append((word, row))

    return matches


@app.route('/message', methods=['POST'])
def predict():
    data = request.get_json()

    if request.is_json and 'bacteria' in data:
        bacteria = data['bacteria']

        results = []
        time_data = {}
        resistence = {}
        matches = find_matches(meds, bacteria)

        for match in matches:
            disease, row_index = match
            antibiotic = meds['ds_antibiotico_microorganismo'].iloc[row_index]
            micro_organism = meds['ds_micro_organismo'].iloc[row_index]
            Res1 = meds['ic_crescimento_microorganismo'].iloc[row_index]

            # Check for non-null values and append to results (for disease, not time nor resistence)
            if pd.notna(antibiotic) and pd.notna(micro_organism):
                result = (antibiotic, micro_organism)
                results.append(result)

                # Collect time data for each disease ( for time)
                time_str = meds['dh_ultima_atualizacao'].iloc[row_index]
                time_data.setdefault(disease, []).append(
                    datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S.%f'))

                # Resistence tiem
                if pd.notna(Res1):
                    resistence.setdefault(disease, []).append(Res1)

        # Remove duplicates from results
        results = list(set(results))
        oldest_latest_times = {disease: (min(times), max(
            times)) for disease, times in time_data.items()}
        print(oldest_latest_times)
        return jsonify({'results': results, 'time_data': oldest_latest_times, 'resistence': resistence}), 200
    else:
        return 'Request was not JSON', 415


if __name__ == '__main__':
    app.run(debug=True, port=5000)
