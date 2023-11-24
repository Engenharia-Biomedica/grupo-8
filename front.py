import streamlit as st
from streamlit_modal import Modal
import streamlit.components.v1 as html
# https://github.com/okld/streamlit-elements
from streamlit_elements import dashboard as dash, nivo, elements, mui, editor
import requests
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

meds = pd.DataFrame(pd.read_csv('static\sample_data_clean.csv', sep=','))
try:
    print(st.session_state.time)
    if type(st.session_state.time) == datetime:
        pass
    else:
        st.session_state.time = datetime.now()
except AttributeError:
    st.session_state.time = datetime.now()


@st.cache_data
def create_data(results, times):

    raw_data = []
    disease_to_antibiotics = {}
    disease_to_times = {}

    for result in results:
        antibiotic, micro_organism = result

        # Update antibiotics
        disease_to_antibiotics.setdefault(
            micro_organism, []).append(antibiotic)

        # Update times
        for time in times[micro_organism.lower()]:

            disease_to_times.setdefault(
                micro_organism, []).append(time)

    # Iterate over diseases and their corresponding antibiotics
    for disease, antibiotics in disease_to_antibiotics.items():
        # Iterate over the antibiotics for the current disease
        for antibiotic in antibiotics:
            for row, index in meds.iterrows():
                if meds['ds_antibiotico_microorganismo'].iloc[row] == antibiotic:
                    raw_data.append([disease, antibiotic, meds['ic_crescimento_microorganismo'].iloc[row],
                                     datetime.strptime(
                        meds['dh_ultima_atualizacao'].iloc[row], '%Y-%m-%d %H:%M:%S.%f'),
                        row, meds['id_prontuario'].iloc[row]])
            for i, item in enumerate(raw_data):
                if i + 1 < len(raw_data):
                    if raw_data[i][3] - raw_data[i + 1][3] > timedelta(days=7) and raw_data[i][5] == raw_data[i + 1][5]:
                        raw_data.remove(item)

    oldest_time = datetime.strptime(
        min([min(times) for times in disease_to_times.values()]), '%a, %d %b %Y %H:%M:%S GMT')
    latest_time = datetime.strptime(
        max([max(times) for times in disease_to_times.values()]), '%a, %d %b %Y %H:%M:%S GMT')
    return raw_data, disease_to_antibiotics, disease_to_times, oldest_time, latest_time


def create_list_item(antibiotic, time_string):
    """Create a list item with a button that triggers the popover."""
    def handle_click():
        on_antibiotic_click(antibiotic, time_string)

    return mui.ListItemButton(onClick=handle_click)


def on_antibiotic_click(antibiotic, time_string):
    print(f"Antibiotic clicked: {antibiotic}, Time: {time_string}")
    modal = Modal(f'Details for {antibiotic}',
                  key=antibiotic, max_width=800)
    with modal.container():
        st.write(f"Details for {antibiotic}:")
        st.write(f"Time: {time_string}")


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
    st.session_state['active_tab'] = 0
    st.session_state.bacteria = None


def search_page():
    html.html('''
    <style>
    .image {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 120px;
    height: 120px;
    margin:-60px 0 0 -60px;
    -webkit-animation:spin 4s linear infinite;
    -moz-animation:spin 4s linear infinite;
    animation:spin 4s linear infinite;
}
@-moz-keyframes spin { 100% { -moz-transform: rotate(360deg); } }
@-webkit-keyframes spin { 100% { -webkit-transform: rotate(360deg); } }
@keyframes spin { 100% { -webkit-transform: rotate(360deg); transform:rotate(360deg); } }
              </style>

    <img class="image" src="https://dinizismo.s3.sa-east-1.amazonaws.com/img.jpg" alt="" width="120" height="120">





'''



              )

    st.title("buscador de antibioticos da Lilica")

    st.session_state.bacteria = st.text_input(
        "Enter the name or code of the bacteria")

    st.button("Send to Flask", on_click=on_send_button_clicked,
              disabled=st.session_state.bacteria == "")


def results_page():
    global bacteria
    bacteria = st.session_state.bacteria
    st.button("Go back to Search", on_click=on_go_back_button_clicked)
    if 'response_data' in st.session_state and st.session_state.response_data:
        if st.session_state.response_data['results'] == []:
            st.error("No results found")
            return

        raw_data, disease_to_antibiotics, disease_to_times, oldest_time, latest_time = create_data(
            st.session_state.response_data['results'], st.session_state.response_data['time_data'])

      # Initialize the new dictionary

        st.balloons()

        sidebar, results = st.columns([1, 5])  # Adjust the ratio as needed

        with sidebar:
            st.header("Filters")
            slider_value = st.slider(
                "Select a value", oldest_time, st.session_state.time)

        with results:

            with elements("nivo_charts"):

                layout = [
                    dash.Item('results', 0, 0, 2, 2),
                    dash.Item('graphs', 0, 2, 2, 2),
                    dash.Item('res_graph', 1, 1, 2, 2),
                ]

                with dash.Grid(layout):
                    with mui.Box(sx={"height": 500, 'border': '1px dashed grey', "overflow": "auto"}, key="results"):
                        st.write(f"Results from Query with {bacteria}:")

                        # Create Tabs dynamically
                        if 'active_tab' not in st.session_state:
                            st.session_state['active_tab'] = 0

                        # Create Tabs dynamically
                        with mui.Tabs(variant='scrollable', value=st.session_state['active_tab'], onChange=lambda _, value: setattr(st.session_state, 'active_tab', int(value))):
                            for index, disease in enumerate(disease_to_antibiotics.keys()):
                                mui.Tab(label=disease, value=index)

                                # Display content for the active tab
                        active_disease = list(disease_to_antibiotics.keys())[
                            st.session_state['active_tab']]
                        # Scrollable container for antibiotics
                        with mui.Box(sx={"overflow": "auto"}):
                            if active_disease in disease_to_times:
                                oldest_time = disease_to_times[active_disease][0]
                                latest_time = disease_to_times[active_disease][1]
                                time_str = f" (Oldest Time: {oldest_time}, Latest Time: {latest_time})"
                            else:
                                time_str = ""
                                print(
                                    f"Warning: {active_disease} not in disease_to_times")

                            with mui.List():
                                for antibiotic in disease_to_antibiotics[active_disease]:
                                    list_item = create_list_item(
                                        antibiotic, time_str)
                                    with list_item:
                                        mui.ListItemText(primary=antibiotic)

                    with mui.Box(sx={"height": 500}, key="graphs"):

                        diseases = meds['ds_micro_organismo'].value_counts()

                        Pie_Data = [
                            {'id': disease, 'value': count}
                            for disease, count in diseases.items()
                        ]
                        for values in Pie_Data:
                            if values['value'] == 0:
                                Pie_Data.remove(values)
                        if len(Pie_Data) == 0:
                            Pie_Data = [{'id': 'Nenhum', 'value': 1}]

                        nivo.Pie(
                            data=Pie_Data,
                            margin={"top": 40, "right": 80,
                                    "bottom": 80, "left": 80},
                            innerRadius=0.5,
                            padAngle=0.7,
                            cornerRadius=3,
                            activeOuterRadiusOffset=8,
                            borderWidth=1,
                            borderColor={"from": "color",
                                         "modifiers": [["darker", 0.2]]},
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

                    with mui.Box(sx={"height": 500, 'border': '1px dashed grey', "overflow": "auto"}, key="res_graph"):

                        # Create Tabs dynamically
                        if 'active_tab' not in st.session_state:
                            st.session_state['active_tab'] = 0

                        # Create Tabs dynamically
                        with mui.Tabs(variant='scrollable', value=st.session_state['active_tab'], onChange=lambda _, value: setattr(st.session_state, 'active_tab', int(value))):
                            for index, disease in enumerate(disease_to_antibiotics.keys()):
                                mui.Tab(label=disease, value=index)

                                # Display content for the active tab
                        active_disease = list(disease_to_antibiotics.keys())[
                            st.session_state['active_tab']]
                        positive_resistence = 0
                        negative_resistence = 0

                        if active_disease in disease_to_times:
                            oldest_time = disease_to_times[active_disease][0]
                            latest_time = disease_to_times[active_disease][1]
                            time_str = f" (Oldest Time: {oldest_time}, Latest Time: {latest_time})"
                        else:
                            time_str = ""
                            print(
                                f"Warning: {active_disease} not in disease_to_times")

                        # Calculate resistance data
                        for i, item in enumerate(raw_data):
                            if raw_data[i][3] > slider_value:
                                if raw_data[i][2] == 'POSITIVO':
                                    positive_resistence += 1
                                else:
                                    negative_resistence += 1

                        res_data = [
                            {'id': 'POSITIVO', 'value': positive_resistence}]
                        if negative_resistence > 0:
                            res_data.append(
                                {'id': 'NEGATIVO', 'value': negative_resistence})
                        nivo.Pie(
                            data=res_data,
                            margin={"top": 40, "right": 80,
                                    "bottom": 80, "left": 80},
                            innerRadius=0.5,
                            padAngle=0.7,
                            cornerRadius=3,
                            activeOuterRadiusOffset=8,
                            borderWidth=1,
                            borderColor={"from": "color",
                                         "modifiers": [["darker", 0.2]]},
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

                        # Display the oldest and latest times

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


'''


New page for when you click on a result( maybe?)
    -> All the tabs have the same pointer, so when you click on one, the others change as well
              -> To change this: create a new variable as the pointer for each box

Para tempo, filtrar resultados para somente aqueles dentro do tempo selecionado

Graficos de dentro do Einstein cm mais csa
         -> Pega so os dados que aconteceram dentro do Einstein
antibioticos prescritos com base no prontuario


sensiel resistente para monitorar resistencia
       -> Ta na tabela?
       

'''
