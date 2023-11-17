import streamlit as st
from streamlit_modal import Modal
import streamlit.components.v1 as html
# https://github.com/okld/streamlit-elements
from streamlit_elements import dashboard as dash, nivo, elements, mui, html
import requests
import pandas as pd
import numpy as np
import random

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
    st.title("buscador de antibioticos da Lilica")

    st.session_state.bacteria = st.text_input(
        "Enter the name or code of the bacteria")

    st.button("Send to Flask", on_click=on_send_button_clicked,
              disabled=st.session_state.bacteria == "")


def results_page():

    st.button("Go back to Search", on_click=on_go_back_button_clicked)
    if 'response_data' in st.session_state and st.session_state.response_data:
        if st.session_state.response_data['results'] == []:
            st.error("No results found")
            return
        
        disease_to_antibiotics = {}
        for result in st.session_state.response_data['results']:
            antibiotic, micro_organism = result
            if micro_organism not in disease_to_antibiotics:
                disease_to_antibiotics[micro_organism] = [antibiotic]
            else:
                disease_to_antibiotics[micro_organism].append(antibiotic)
        st.balloons()
        with elements("nivo_charts"):
            diseases = meds['ds_micro_organismo'].value_counts()

            DATA = [
                {'id': disease, 'value': count}
                for disease, count in diseases.items()


            ]
    
            layout = [
                dash.Item('first_item',0,0,2,2),
                dash.Item('second_item',0,2,2,2),
                dash.Item('third_item',1,1,2,2),


            ]
            with dash.Grid(layout):
                with mui.Box(sx={"height": 500, 'border': '1px dashed grey'}, key="Second_Item"):
                    st.write(f"Results from Query with {st.session_state.bacteria}:")
                    tabs = mui.tabs(list(disease_to_antibiotics.keys()))
                    for tab, (disease, antibiotics) in zip(tabs, disease_to_antibiotics.items()):
                        with tab:
                            st.write(f"Antibiotics for {disease}:")
                            for antibiotic in antibiotics:
                                st.text(antibiotic)
                with mui.Box(sx={"height": 500}, key="first_item"):
                    nivo.Pie(
                        data=DATA,
                        margin={"top": 40, "right": 80, "bottom": 80, "left": 80},
                        innerRadius=0.5,
                        padAngle=0.7,
                        cornerRadius=3,
                        activeOuterRadiusOffset=8,
                        borderWidth=1,
                        borderColor={"from": "color", "modifiers": [["darker", 0.2]]},
                        arcLinkLabelsSkipAngle=10,
                        arcLinkLabelsTextColor="#333333",
                        arcLinkLabelsThickness=2,
                        arcLinkLabelsColor={"from": "color"},
                        arcLabelsSkipAngle=10,
                        arcLabelsTextColor={"from": "color",
                                            "modifiers": [["darker", 2]]},
                        defs=[
                            {
                                "id": "dots",
                                "type": "patternDots",
                                "background": "inherit",
                                "color": "rgba(255, 255, 255, 0.3)",
                                "size": 4,
                                "padding": 1,
                                "stagger": True
                            },
                            {
                                "id": "lines",
                                "type": "patternLines",
                                "background": "inherit",
                                "color": "rgba(255, 255, 255, 0.3)",
                                "rotation": -45,
                                "lineWidth": 6,
                                "spacing": 10
                            }
                        ],
                        fill=[

                            {'match': {'id': name}, 'id': random.choice(
                                ["dots", "lines", ''])}
                            for name in diseases.keys()
                        ],
                        legends=[
                            {
                                "anchor": "bottom",
                                "direction": "row",
                                "justify": False,
                                "translateX": 0,
                                "translateY": 56,
                                "itemsSpacing": 0,
                                "itemWidth": 100,
                                "itemHeight": 18,
                                "itemTextColor": "#999",
                                "itemDirection": "left-to-right",
                                "itemOpacity": 1,
                                "symbolSize": 18,
                                "symbolShape": "circle",
                                "effects": [
                                    {
                                        "on": "hover",
                                        "style": {
                                            "itemTextColor": "#000"
                                        }
                                    }
                                ]
                            }
                        ]
                    )

    
     
      
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
