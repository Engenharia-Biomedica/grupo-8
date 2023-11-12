from flask import Flask, render_template, jsonify, request
from autofill import autofill
from flask_cors import CORS
import pandas as pd
import numpy as np

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:8501"}})


meds = pd.DataFrame(pd.read_csv('static\sample_data_clean.csv', sep=','))


def find_matches(df, search_string):
    # Convert all words to lowercase for case-insensitive comparison
    autofill_words = df['ds_micro_organismo'].str.lower().tolist()

    # Register words with autofill (assuming autofill expects lowercase words)
    autofill.register_words(autofill_words)
    lower_search_string = search_string.lower()

    # Perform the search
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
        matches = find_matches(meds, bacteria)

        for i in range(len(matches)):
            # Extracting antibiotic and micro_organism for each match
            antibiotic = meds['ds_antibiotico_microorganismo'].iloc[matches[i][1]]
            micro_organism = meds['ds_micro_organismo'].iloc[matches[i][1]]

            # Check for non-null values and append to results
            if pd.notna(antibiotic) and pd.notna(micro_organism):
                result = (antibiotic, micro_organism)
                results.append(result)

        # Remove duplicates from results
        results = list(set(results))

        return jsonify({'results': results}), 200

    else:
        return 'Request was not JSON', 415


if __name__ == '__main__':
    app.run(debug=True, port=5000)
