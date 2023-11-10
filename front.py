import streamlit as st
import streamlit.components.v1 as sthtml
import requests

sthtml.html("<h1>Streamlit Frontend</h1>")
sthtml.html("<img src='https://www.streamlit.io/images/brand/streamlit-logo-primary-colormark-darktext.png' width='200px'>")

page = 'Search'


def send_data_to_flask(data):
    response = requests.post("http://localhost:5000/message", json=data)
    return response.json()


def ChangePage():
    match page:
        case 'Search':
            page = 'Results'
        case 'Results':
            page = 'Search'


def Search():
    global page, response_data
    st.title("Streamlit Frontend")

    bacteria = st.text_input("Enter the name of the bacteria")

    if st.button("Send to Flask"):
        page = 'Results'
        response_data = send_data_to_flask({"bacteria": bacteria})


def Results():
    st.button("Go back to Search")
    if response_data and 'results' in response_data:
        st.write("Results from Flask:")

        for result in response_data['results']:
            st.text(result)
    else:
        st.write("No results received or error in backend")


def main():
    if page == 'Search':
        Search()
    if page == 'Results':
        Results()


if __name__ == "__main__":
    main()
