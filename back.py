from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:8501"}})


meds = pd.DataFrame(pd.read_csv('static\sample_data_clean.csv', sep=','))


def find_matches(df, search_string):
    matches = []

    # Finding the location
    result = np.where(df == search_string)

    # The result is a tuple with row indices and column indices
    row_indices = result[0]
    col_indices = result[1]

    # Print the locations
    for row, col in zip(row_indices, col_indices):
        matches.append((row))
        # print(f"String found at row {row}, column {col} (Column name: {df.columns[col]})")
    return matches


@app.route('/message', methods=['POST'])
def predict():
    data = request.get_json()
    bacteria = data['bacteria']
    if request.is_json:
        print(bacteria)
        results = []
        matches = find_matches(meds, bacteria)
        for i in range(len(matches)):
            result = meds['ds_antibiotico_microorganismo'].iloc[matches[i]]
            if pd.notna(result):
                results.append(result)
        results = list(set(results))
        if None in results:
            results.remove(None)
        print(results)

        return jsonify({'results': results}), 200

    else:
        return 'Request was not JSON', 415


if __name__ == '__main__':
    app.run(debug=True, port=5000)
