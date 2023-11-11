import streamlit as st
import requests


def send_data_to_flask(data):
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
    response_data = send_data_to_flask({"bacteria": st.session_state.bacteria})
    st.session_state.response_data = response_data
    st.session_state.page = 'results'


def on_go_back_button_clicked():
    st.session_state.page = 'search'


def search_page():
    st.title("Streamlit Frontend")
    st.session_state.bacteria = st.text_input("Enter the name of the bacteria")

    st.button("Send to Flask", on_click=on_send_button_clicked)


def results_page():
    st.button("Go back to Search", on_click=on_go_back_button_clicked)

    response_data = st.session_state.get('response_data', {})
    if 'results' in response_data:
        st.write("Results from Flask:")
        for result in response_data['results']:
            st.text(result)
    else:
        st.write("No results received or error in backend")


def main():
    st.image('https://www.streamlit.io/images/brand/streamlit-logo-primary-colormark-darktext.png', width=200)

    if 'page' not in st.session_state:
        st.session_state['page'] = 'search'

    if st.session_state['page'] == 'search':
        st.write("Displaying Search Page")
        search_page()
    elif st.session_state['page'] == 'results':
        st.write("Displaying Results Page")
        results_page()


if __name__ == "__main__":
    main()
