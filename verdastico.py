import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

meds = pd.DataFrame(pd.read_csv('static\sample_data_clean.csv', sep=','))



def main():
    st.bar_chart(data = meds['ds_exame_millennium'].value_counts())
    


if __name__ == "__main__":
    main()
