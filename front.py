import streamlit as st
from streamlit_modal import Modal
import streamlit.components.v1 as html
import requests


def send_data_to_flask(data):
    print(data)
    try:
        response = requests.post("http://localhost:5000/message", json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Error from Flask: " + response.text)
            return {}
    except requests.exceptions.RequestException as e:
        st.error("Request failed: " + str(e))
        return {}


def on_send_button_clicked():
    """Callback function for 'Send to Flask' button."""
    youfailed = Modal(key="youfailed", title="You failed",
                      max_width=500)
    if st.session_state.bacteria == "" and st.session_state.bac_code == "":
        with youfailed.container():

            st.write("You failed")
    else:
        if st.session_state.bacteria:
            response_data = send_data_to_flask(
                {"bacteria": st.session_state.bacteria})
        elif st.session_state.bac_code:
            response_data = send_data_to_flask(
                {"code": st.session_state.bac_code})
        st.session_state.response_data = response_data
        st.session_state.page = 'results'


def on_go_back_button_clicked():
    st.session_state.page = 'search'


def search_page():
    st.title("We doin this")

    st.session_state.bacteria = st.text_input(
        "Enter the name or code of the bacteria")

    st.button("Send to Flask", on_click=on_send_button_clicked)


def results_page():
    st.button("Go back to Search", on_click=on_go_back_button_clicked)

    response_data = st.session_state.get('response_data', {})
    if 'results' in response_data and response_data['results'] != []:
        st.write("Results from Flask:")

        # Organize the results by disease
        disease_to_antibiotics = {}
        for result in response_data['results']:
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
        st.write("No results received or error in backend")


def main():

    if 'page' not in st.session_state:
        st.session_state['page'] = 'search'

    if st.session_state['page'] == 'search':
        search_page()
    elif st.session_state['page'] == 'results':
        results_page()


if __name__ == "__main__":
    main()
