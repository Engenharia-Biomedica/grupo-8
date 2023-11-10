from flask import Flask, render_template, jsonify, request, redirect, url_for
import pandas as pd
import numpy as np
import math


app = Flask(__name__)

meds = pd.DataFrame(pd.read_csv('static/sample_data_clean.csv'))


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


@app.route('/')
def home():
    print('lets do this!!!')
    return render_template('index.html')


@app.route('/results/<bacteria>')
def results(bacteria):
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
    return render_template('results.html', results=results)


@app.route('/message', methods=['GET', 'POST'])
def predict():
    if request.is_json:
        data = request.get_json()
        bacteria = data.get("form")
        return jsonify({'results': bacteria}), 200

    else:
        return 'Request was not JSON', 415


if __name__ == '__main__':
    app.run(debug=True)
