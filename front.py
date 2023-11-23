import streamlit as st
from streamlit_modal import Modal
import streamlit.components.v1 as html
# https://github.com/okld/streamlit-elements
from streamlit_elements import dashboard as dash, nivo, elements, mui, editor
import requests
import pandas as pd
import numpy as np
import random
from datetime import datetime

meds = pd.DataFrame(pd.read_csv('static\sample_data_clean.csv', sep=','))
try:
    st.session_state.time
    if type(st.session_state.time) == datetime:
        print('fuck yeah')
    else:
        st.session_state.time = datetime.now()
except AttributeError:
    print('fuck no')
    st.session_state.time = datetime.now()


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


def search_page():
    # Inject custom CSS
    st.markdown("""
        <style>
        .my-custom-style {
            color: red;
            font-size: 20px;
            /* other CSS properties */
        }
        </style>
    """, unsafe_allow_html=True)

    # Use the custom style in a markdown
    st.markdown('<img class="my-custom-style" src="/static/imgs/jpg2png.png"></img>',
                unsafe_allow_html=True)
    st.title("buscador de antibioticos da Lilica")

    st.session_state.bacteria = st.text_input(
        "Enter the name or code of the bacteria")

    st.button("Send to Flask", on_click=on_send_button_clicked,
              disabled=st.session_state.bacteria == "")


def results_page():
    global bacteria
    bacteria = st.session_state.bacteria
    st.session_state.bacteria = None
    st.button("Go back to Search", on_click=on_go_back_button_clicked)
    if 'response_data' in st.session_state and st.session_state.response_data:
        if st.session_state.response_data['results'] == []:
            st.error("No results found")
            return

        diseases = meds['ds_micro_organismo'].value_counts()
        Pie_Data = [
            {'id': disease, 'value': count}
            for disease, count in diseases.items()
        ]
        disease_to_antibiotics = {}
        disease_to_times = {}
        disease_to_resistence = {}
        for result in st.session_state.response_data['results']:
            antibiotic, micro_organism = result

            # Update antibiotics
            disease_to_antibiotics.setdefault(
                micro_organism, []).append(antibiotic)

            # Update times
            for time in st.session_state.response_data['time_data'][micro_organism.lower()]:

                disease_to_times.setdefault(
                    micro_organism, []).append(time)

            # Update resistence
            for resistence in st.session_state.response_data['resistence'][micro_organism.lower()]:

                disease_to_resistence.setdefault(
                    micro_organism, []).append(resistence)

        oldest_time = datetime.strptime(
            min([min(times) for times in disease_to_times.values()]), '%a, %d %b %Y %H:%M:%S GMT')
        latest_time = datetime.strptime(
            max([max(times) for times in disease_to_times.values()]), '%a, %d %b %Y %H:%M:%S GMT')

        st.balloons()

        sidebar, results = st.columns([1, 5])  # Adjust the ratio as needed

        with sidebar:
            st.header("Filters")
            slider_value = st.slider(
                "Select a value", oldest_time, st.session_state.time)

        with results:
            with elements("nivo_charts"):

                layout = [
                    dash.Item('first_item', 0, 0, 2, 2),
                    dash.Item('second_item', 0, 2, 2, 2),
                    dash.Item('third_item', 1, 1, 2, 2),
                ]

                with dash.Grid(layout):
                    with mui.Box(sx={"height": 500, 'border': '1px dashed grey', "overflow": "auto"}, key="first_item"):
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
                        with mui.Box(sx={"maxHeight": 300, "overflow": "auto"}):
                            if active_disease in disease_to_times:
                                oldest_time = disease_to_times[active_disease][0]
                                latest_time = disease_to_times[active_disease][1]
                                time_str = f" (Oldest Time: {oldest_time}, Latest Time: {latest_time})"
                            else:
                                time_str = ""
                                print(
                                    f"Warning: {active_disease} not in disease_to_times")

                            for antibiotic in disease_to_antibiotics[active_disease]:
                                if datetime.strptime(disease_to_times[active_disease][1], '%a, %d %b %Y %H:%M:%S GMT') < slider_value:
                                    continue
                                mui.Typography(antibiotic + time_str)

                        # Display the oldest and latest times

                    with mui.Box(sx={"height": 500}, key="second_item"):
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

                    with mui.Box(sx={"height": 500, 'border': '1px dashed grey', "overflow": "auto"}, key="third_item"):
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
                        for item in disease_to_resistence.get(active_disease, []):
                            if item == 'POSITIVO':
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
    html.html("""
<canvas id="fireworksCanvas"></canvas>

<script>
// Get canvas and context
var canvas = document.getElementById('fireworksCanvas');
var ctx = canvas.getContext('2d');

// Set the canvas size to the window size
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

// Function to create a random color
function randomColor() {
    var letters = '0123456789ABCDEF';
    var color = '#';
    for (var i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

// Function to create a single particle
function Particle(x, y) {
    this.x = x;
    this.y = y;
    this.radius = Math.random() * 5 + 1;
    this.color = randomColor();
    this.lifeSpan = Math.random() * 50 + 80;
    this.vx = Math.random() * 2 - 1;
    this.vy = Math.random() * 2 - 1;

    this.draw = function() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, 2 * Math.PI);
        ctx.fillStyle = this.color;
        ctx.fill();
    }
}

// Array to hold particles
var particles = [];

// Function to create a group of particles (a single firework)
function createFirework() {
    var x = Math.random() * canvas.width;
    var y = Math.random() * canvas.height;

    for (var i = 0; i < 100; i++) {
        particles.push(new Particle(x, y));
    }
}

// Animation loop
function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    particles.forEach(function(particle, index) {
        particle.lifeSpan--;
        particle.x += particle.vx;
        particle.y += particle.vy;
        particle.draw();

        // Remove particles that are dead (lifeSpan <= 0)
        if (particle.lifeSpan <= 0) {
            particles.splice(index, 1);
        }
    });

    // Generate a new firework periodically
    if (Math.random() < 0.02) {
        createFirework();
    }

    requestAnimationFrame(draw);
}

// Start the animation
draw();

</script>


""")

    if 'page' not in st.session_state:
        st.session_state['page'] = 'search'

    if st.session_state['page'] == 'search':
        search_page()
    elif st.session_state['page'] == 'results':
        results_page()


if __name__ == "__main__":
    main()


'''
    -> All the tabs have the same pointer, so when you click on one, the others change as well
              -> To change this: create a new variable as the pointer for each box

Para tempo, filtrar resultados para somente aqueles dentro do tempo selecionado

Graficos de dentro do Einstein cm mais csa
         -> Pega so os dados que aconteceram dentro do Einstein
antibioticos prescritos com base no prontuario

'''
