import streamlit as st
from streamlit_modal import Modal
import streamlit.components.v1 as html
# https://github.com/okld/streamlit-elements
from streamlit_elements import dashboard as dash, nivo, elements, mui, html
import requests
import pandas as pd
import numpy as np

meds = pd.DataFrame(pd.read_csv('static\sample_data_clean.csv', sep=','))


def send_data_to_flask(data):
    with st.spinner('Processing...'):
        try:
            response = requests.post(
                "http://localhost:5000/message", json=data)
            if response.status_code == 200:
                return response.json()
            else:
                st.error("Error from Flask: " + response.text)
                return None
        except requests.exceptions.RequestException as e:
            st.error("Request failed: " + str(e))
            return None


def on_send_button_clicked():
    """Callback function for 'Send to Flask' button."""
    if st.session_state.bacteria:
        # Send data to Flask and update response_data in session state
        st.session_state.response_data = send_data_to_flask(
            {"bacteria": st.session_state.bacteria})
        st.session_state.page = 'results' if st.session_state.response_data else 'search'

        response_data = send_data_to_flask(
            {"bacteria": st.session_state.bacteria})

        st.session_state.response_data = response_data
        st.session_state.page = 'results'


def on_go_back_button_clicked():
    st.session_state.page = 'search'


def search_page():
    st.title("We doin this")

    st.session_state.bacteria = st.text_input(
        "Enter the name or code of the bacteria")

    st.button("Send to Flask", on_click=on_send_button_clicked,
              disabled=st.session_state.bacteria == "")


def results_page():
    with elements('Grid'):
        layout = [
            dash.Item('first_item', 0, 0, 2, 2,
                      isDraggable=False, isResizable=False),
            dash.Item('second_item', 2, 0, 2, 2,
                      isDraggable=False, isResizable=False),
            dash.Item('third_item', 0, 2, 1, 1,
                      isDraggable=False, isResizable=False),

        ]
        with dash.Grid(layout):
            mui.Paper('first_item', key='first_item')
            mui.Paper('second_item', key='second_item')
            mui.Paper('third_item', key='third_item')
    st.button("Go back to Search", on_click=on_go_back_button_clicked)

    if 'response_data' in st.session_state and st.session_state.response_data:
        st.balloons()
        st.write("Results from Flask:")

        # Organize the results by disease
        disease_to_antibiotics = {}
        for result in st.session_state.response_data['results']:
            antibiotic, micro_organism = result
            if micro_organism not in disease_to_antibiotics:
                disease_to_antibiotics[micro_organism] = [antibiotic]
            else:
                disease_to_antibiotics[micro_organism].append(antibiotic)

        # Create tabs for each disease
        tabs = st.tabs(list(disease_to_antibiotics.keys()))
        for tab, (disease, antibiotics) in zip(tabs, disease_to_antibiotics.items()):
            with tab:
                st.write(f"Antibiotics for {disease}:")
                for antibiotic in antibiotics:
                    st.text(antibiotic)
    else:
        st.error("No results received or error in backend")


def main():

    if 'page' not in st.session_state:
        st.session_state['page'] = 'search'

    if st.session_state['page'] == 'search':
        search_page()
    elif st.session_state['page'] == 'results':
        results_page()


if __name__ == "__main__":
    main()
