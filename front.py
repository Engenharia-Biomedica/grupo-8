# Importar bibliotecas
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


st.set_page_config(page_title="Rastreador de dados para tratamento com antibióticos",
                   layout="wide", page_icon=':microscope:')

meds = pd.DataFrame(pd.read_csv('static\sample_data_clean.csv', sep=','))
try:
    print(st.session_state.time)
    if type(st.session_state.time) == datetime:
        pass
    else:
        st.session_state.time = datetime.now()
except AttributeError:
    st.session_state.time = datetime.now()

# modificações no excel (converter de csv para xlsx)


@st.cache_data
def load_data(type, path):
    match type:
        case 'csv':
            return pd.read_csv(path, sep=',')
        case 'xlsx':
            return pd.read_excel(path)
        case 'excel':
            return pd.read_excel(path)


meds = load_data('csv', 'static\sample_data_clean.csv')


@st.cache_data
def create_data(results, times, meds):

    raw_data = []
    disease_to_antibiotics = {}
    disease_to_times = {}
    antibiotics_to_times = {}
    sensitivity = {}

    # Process each result
    for antibiotic, micro_organism in results:
        # Update antibiotics mapping
        disease_to_antibiotics.setdefault(
            micro_organism, []).append(antibiotic)

        # Update times
        for time in times.get(micro_organism.lower(), []):
            disease_to_times.setdefault(micro_organism, []).append(time)

    unique_antibiotics = set(antibiotic for antibiotic, _ in results)
    for antibiotic in unique_antibiotics:
        matching_rows = meds[meds['ds_antibiotico_microorganismo'] == antibiotic]
        times_list = pd.to_datetime(
            matching_rows['dh_ultima_atualizacao'].dropna(), format='%Y-%m-%d %H:%M:%S.%f')

        if not times_list.empty:
            antibiotics_to_times[antibiotic] = (
                times_list.min().to_pydatetime(), times_list.max().to_pydatetime())
            oldest_time = times_list.min().to_pydatetime()
        else:
            print(f"No valid time data for antibiotic: {antibiotic}")

    # Relacionar doenças com seus antibióticos correspondentes:
    for disease, antibiotics in disease_to_antibiotics.items():
        for antibiotic in antibiotics:
            matching_rows = meds[meds['ds_antibiotico_microorganismo'] == antibiotic]
            # Calculate sensitivity data for each antibiotic
            sensitivity[antibiotic] = matching_rows['cd_interpretacao_antibiograma'].value_counts(
            ).to_dict()
            # Relacionar os antibioticos com as seus respectivos antibióticos
        for antibiotic in antibiotics:
            matching_rows = meds[meds['ds_antibiotico_microorganismo'] == antibiotic]
            for _, row in matching_rows.iterrows():
                local = row['ds_local_coleta'] if pd.notna(
                    row['ds_local_coleta']) else 'Nenhum'
                encontro = row['ds_tipo_encontro'] if pd.notna(
                    row['ds_tipo_encontro']) else 'Nenhum'
                exame = row['ds_exame_millennium'] if pd.notna(
                    row['ds_exame_millennium']) else 'Nenhum'

                update_time = datetime.strptime(
                    row['dh_ultima_atualizacao'], '%Y-%m-%d %H:%M:%S.%f')

                if raw_data != []:
                    if raw_data[-1][3] - update_time > timedelta(days=30):
                        print('deleted!')
                        continue
                raw_data.append(
                    [disease, antibiotic, row['ic_crescimento_microorganismo'], update_time, _, row['id_prontuario'], local, encontro, exame])

    return raw_data, disease_to_antibiotics, disease_to_times, antibiotics_to_times, oldest_time, sensitivity


def create_list_item(antibiotic, time_string):
    """Crie um item de lista com um botão que acionar o popover."""
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

# A função on_send_button_clicked() é uma função de retorno de chamada (callback) que é acionada quando o botão 'Send to Flask' é clicado


def on_send_button_clicked():
    """Chama a função do botão 'Send to Flask'."""
    if st.session_state.bacteria:
        # Envie dados para o Flask e atualize response_data no estado da sessão.
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


# A função search_page() está gerando e exibindo um código HTML. Esse código HTML inclui uma imagem que é posicionada no centro da página e gira continuamente.
def search_page():
    html.html('''
    <style>
    .image {
    position: absolute;
    top: 50%;
    left: 50%;
    height: 120px;
    height: auto;
    margin:-60px 0 0 -60px;
    margin-left: -110px;
    width: 235px;
 
}

              </style>

    <img class="image" src="https://dinizismo.s3.sa-east-1.amazonaws.com/Untitled.jpg" alt="">





'''



              )

    st.header("Rastreador de dados para tratamento com antibióticos")

    st.session_state.bacteria = st.text_input(
        "Digite o nome ou código da bactéria")

    st.button("Clique para pesquisar", on_click=on_send_button_clicked,
              disabled=st.session_state.bacteria == "")


def results_page():

    global bacteria
    bacteria = st.session_state.bacteria
    st.button("Volte para pesquisar ", on_click=on_go_back_button_clicked)
    if 'response_data' in st.session_state and st.session_state.response_data:
        if st.session_state.response_data['results'] == []:
            st.error("Nenhum resultado encontrado")
            return

        raw_data, disease_to_antibiotics, disease_to_times, antibiotics_to_times, oldest_time, sensitivity = create_data(
            st.session_state.response_data['results'], st.session_state.response_data['time_data'], meds)

      # Initialize the new dictionary
        @st.cache_data
        def check_occurrences(antibiotic, local, type_of_encounter, exam):
            for row in raw_data:
                if (antibiotic == 'todos' or row[1] == antibiotic) and \
                    (local == 'todos' or row[6] == local) and \
                    (type_of_encounter == 'todos' or row[7] == type_of_encounter) and \
                        (exam == 'todos' or row[8] == exam):
                    return True
            return False

        @st.cache_data
        def check_occurrences_disease(disease, local, type_of_encounter, exam):
            for row in raw_data:
                if (disease == 'todos' or row[0] == disease) and \
                    (local == 'todos' or row[6] == local) and \
                    (type_of_encounter == 'todos' or row[7] == type_of_encounter) and \
                        (exam == 'todos' or row[8] == exam):
                    return True
            return False

        st.balloons()

        sidebar, results = st.columns([1, 5])  # Adjust the ratio as needed

        with sidebar:
            st.header("Filtros")
            slider_value = st.slider(
                "Tempo desejado", oldest_time, st.session_state.time)
            unique_locals = set(row[6] for row in raw_data)
            unique_types = set(row[7] for row in raw_data)
            unique_exams = set(row[8] for row in raw_data)

            # Create filters using Streamlit's selectbox
            local_filter = st.selectbox(
                'Filtre o Local', ['todos'] + list(unique_locals))
            type_filter = st.selectbox(
                'Filtre o tipo de coleta', ['todos'] + list(unique_types))
            exam_filter = st.selectbox(
                'Filtre o tipo de exame', ['todos'] + list(unique_exams))

        with results:

            with elements("nivo_charts"):

                layout = [

                    dash.Item('results', 0, 0, 4, 2, isDraggable=False),
                    dash.Item('graphs', 0, 1, 5, 3, isDraggable=False),
                    dash.Item('res_graph', 0, 1, 4, 5, isDraggable=False),
                    dash.Item('sens_graph', 0, 1, 4, 4, isDraggable=False),

                    # Starts at column 0, spans 2 columns
                    dash.Item('results', 0, 0, 2, 2, isDraggable=False),
                    # Starts at column 2, spans 1 column
                    dash.Item('graphs', 2, 1, 2, 2, isDraggable=False),
                    # Starts at column 3, spans 1 column
                    dash.Item('res_graph', 4, 1, 2, 2, isDraggable=False),
                    # Starts at column 4, spans 1 column
                    dash.Item('sens_graph', 6, 0, 2, 2, isDraggable=False),


                ]

                with dash.Grid(layout):
                    with mui.Box(sx={"height": 500, 'border': '1px dashed grey', "overflow": "auto"}, key="results"):
                        st.write(f"Resultados da consulta para {bacteria}:")

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
                            if active_disease in disease_to_antibiotics:
                                for antibiotic in disease_to_antibiotics[active_disease]:
                                    # Check if the antibiotic has time data in antibiotics_to_times
                                    if antibiotic in antibiotics_to_times:

                                        if check_occurrences(antibiotic, local_filter, type_filter, exam_filter):

                                            # Extract oldest and latest times for this antibiotic
                                            oldest_time, latest_time = antibiotics_to_times[antibiotic]
                                            time_str = f" (Oldest Time: {oldest_time}, Latest Time: {latest_time})"

                                            # Compare with the slider value
                                            if oldest_time >= slider_value:
                                                list_item = create_list_item(
                                                    antibiotic, time_str)
                                                with list_item:
                                                    mui.ListItemText(
                                                        primary=antibiotic)
                                    else:
                                        print(
                                            f"Warning: No time data for {antibiotic}")

                    with mui.Box(sx={"height": 500}, key="graphs"):

                        mui.Typography('Porcentagem indivíduos com dada doença', sx={'textAlign': 'center'})

                        mui.Typography('Título do Gráfico', sx={
                                       'textAlign': 'center'})

                        mui.Typography('Porcentagem indivíduos com dada doença', sx={
                                       'textAlign': 'center', 'fontFamily': 'Raleway', 'fontSize': 50})

                        filtered_diseases = {}

                        for _, row in meds.iterrows():
                            disease = row['ds_micro_organismo']
                            update_time = datetime.strptime(
                                row['dh_ultima_atualizacao'], '%Y-%m-%d %H:%M:%S.%f')

                            if update_time >= slider_value:
                                filtered_diseases[disease] = filtered_diseases.get(
                                    disease, 0) + 1

    # Create Pie Data outside the loop
                        Pie_Data = [
                            {'id': disease, 'value': count}
                            for disease, count in filtered_diseases.items() if count > 0
                        ]

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
                                for name in filtered_diseases.items()
                            ],
                            legends=[
                                {
                                    "anchor": "bottom-left",  # You might try 'bottom-right' or 'bottom-left'
                                    "direction": "column",  # Change to 'column' for vertical alignment if needed
                                    "justify": False,
                                    "translateX": -70,
                                    "translateY": 56,  # Adjust if necessary to move the legend up or down
                                    "itemsSpacing": 5,  # Increase for more space between items
                                    "itemWidth": 120,  # Increase if items or text are too squeezed
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
                        mui.Typography('Gráfico de Resistência')

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
                                if check_occurrences_disease(active_disease, local_filter, type_filter, exam_filter):
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
                                for name in filtered_diseases.items()
                            ],
                            legends=[
                                {
                                    "anchor": "bottom-left",  # You might try 'bottom-right' or 'bottom-left'
                                    "direction": "column",  # Change to 'column' for vertical alignment if needed
                                    "justify": False,
                                    "translateX": -70,
                                    "translateY": 56,  # Adjust if necessary to move the legend up or down
                                    "itemsSpacing": 5,  # Increase for more space between items
                                    "itemWidth": 120,  # Increase if items or text are too squeezed
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

                    with mui.Box(sx={'height': 500}, key='sens_graph'):
                        mui.Typography('Gráfico de Sensibilidade')
                        if 'active_tab_antibiotic' not in st.session_state:
                            st.session_state['active_tab_antibiotic'] = 0

                    # Create Tabs dynamically
                        with mui.Tabs(
                            variant='scrollable',
                            value=st.session_state['active_tab_antibiotic'],
                            onChange=lambda _, value: setattr(
                                st.session_state, 'active_tab_antibiotic', int(value))
                        ):
                            for index, antibiotic in enumerate(disease_to_antibiotics[active_disease]):
                                mui.Tab(label=antibiotic, value=index)

                        # Determine the active antibiotic based on the selected tab
                        active_antibiotic = disease_to_antibiotics[active_disease][
                            st.session_state['active_tab_antibiotic']]

                        sens_data = [{'id': resistance, 'value': count}
                                     for resistance, count in sensitivity[antibiotic].items()]

                        nivo.Pie(
                            data=sens_data,
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
                                for name in filtered_diseases.items()
                            ],
                            legends=[
                                {
                                    "anchor": "bottom-left",  # You might try 'bottom-right' or 'bottom-left'
                                    "direction": "column",  # Change to 'column' for vertical alignment if needed
                                    "justify": False,
                                    "translateX": -70,
                                    "translateY": 56,  # Adjust if necessary to move the legend up or down
                                    "itemsSpacing": 5,  # Increase for more space between items
                                    "itemWidth": 120,  # Increase if items or text are too squeezed
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
