import os
import streamlit as st
import pandas as pd
from supabase import create_client, Client
import ftplib
import tempfile
from pathlib import Path
import numpy as np
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


############# ############## PAGE 2 INSERT TO DATABASE USER+TRIAL ############## ############ #############################
st.set_page_config(
    page_title="Balance App | SPESS",
    page_icon="random",
    layout="wide",
    initial_sidebar_state="expanded",
    
)

# Create a connection with database
def init_connection():
    url = st.secrets["supabase_url"]
    key = st.secrets["supabase_key"]
    #client = create_client(url, key)
    return create_client(url, key)
con = init_connection()



# Button to download a sample proper file:
df = pd.read_csv('https://sportsmetrics.geth.gr/storage/BAL_LOAD-0_2ND_2022-11-04_12-32-00.csv')

with st.sidebar.expander("Download a sample file:"):
    st.download_button(
        label="Sample",
        data=df.to_csv(),
        file_name='sample.csv',
        mime='text/csv',
    )
#-----Method to delete a entry from den database:-----#
with st.sidebar.expander("DELETE USER", expanded=False):
    st.error("Warning this is pernament")
    with st.form("delete user"):
        id_to_delete = st.number_input("Type ID of user to delete", value=0, step=1)
        verify_delete_text_input = st.text_input("Type 'Delete' in the field above to proceed")
        id_to_delete_button = st.form_submit_button("Delete User")

    if id_to_delete_button and verify_delete_text_input=="Delete":
        def delete_entry_from_balance_table(supabase):
            query=con.table("balance_table").delete().eq("id", id_to_delete).execute()
            return query
        query = delete_entry_from_balance_table(con)
        # Check if list query.data is empty or not
        if query.data:
            def main():
                delete_entry = delete_entry_from_balance_table(con)
            main()
            st.success('Thank you! This entry has been deleted from database!')
        else:
            st.warning("There is no entry with this id to delete!")
#-----End of Method to delete a entry from den database:-----#


# Main title of the page:
st.title("Calculate Results")

#--------Fetch and display the whole table with entries:--------#
url_list=[]
with st.expander("List of all entries from the database.", expanded=True):
    st.caption("Use the below search fields to filter the datatable!")
    #@st.experimental_memo(ttl=300)
    def select_all_from_balance_table():
        query=con.table("balance_table").select("*").execute()
        return query
    query = select_all_from_balance_table()

    df_balance_table = pd.DataFrame(query.data)
    if not df_balance_table.empty:
        df_balance_table.columns = ['ID', 'Created At', 'Fullname', 'Age', 'Height', 'Weight', 'Email', 'Occupy', 'Filepath', 'Filename', 'Type of trial', 'Description', 'Instructor']
        col1, col2 = st.columns(2)
        with col2:
            instructor_search = st.text_input("Instructor:")
        with col1:
            fullname_search = st.text_input("Fullname:")

        if not instructor_search and not fullname_search :
            df_balance_table.sort_values(by=['Created At'], inplace=True, ascending=True)
            df_balance_table = df_balance_table.iloc[1:]
            df_balance_table[['ID', 'Created At', 'Fullname', 'Age', 'Height', 'Weight', 'Email', 'Occupy', 'Filepath', 'Filename', 'Type of trial', 'Description', 'Instructor']]
        
        elif fullname_search and not instructor_search :
            st.dataframe(df_balance_table[df_balance_table['Fullname']== fullname_search])

        elif instructor_search and not fullname_search :
            st.dataframe(df_balance_table[df_balance_table['Instructor']== instructor_search])

        elif fullname_search and instructor_search :
            df_balance_table[(df_balance_table['Fullname'] == fullname_search) & (df_balance_table['Instructor'] == instructor_search)]
        
        elif instructor_search :
            df_balance_table[(df_balance_table['Instructor'] == instructor_search) ]
        
        elif fullname_search and instructor_search :
            df_balance_table[(df_balance_table['Instructor'] == instructor_search) & (df_balance_table['Fullname'] == fullname_search)]

        #url_id_number_input = st.number_input("Type the ID of the person you want to calculate results of the current trial.",value=0,step=1)


        # In this form, you type the id of the person to calculate speicific trial.
        
    else:
        st.write("There are no entries in the database! Please insert first!")
#--------End of Fetch and display the whole table with entries:---------#

# Method to run results:
with st.sidebar.form("Type the ID of your link:", clear_on_submit=False):   
    url_id_number_input = st.number_input("Type the ID of the trial and Press 'Calculate Results' :",value = 0,step= 1)
    id_submitted = st.form_submit_button("Calculate Results")
    # Querry to find the data row of specific ID
    if url_id_number_input:
        def select_filepath_from_specific_id():
            query=con.table("balance_table").select("*").eq("id", url_id_number_input).execute()
            return query
        query = select_filepath_from_specific_id()  
        # Make a list with all values from database depending on the condition. 
        url_list =  query.data
        # List with values depending on the querry
        if url_list:
            url = url_list[0]['filepath'].replace(" ", "%20")
            st.write("Person ID:", url_list[0]['id'])
            st.write("Person Filepath:",url_list[0]['filepath'])
        else:
            st.write("There is no entry with this ID")

def get_data():
    if url_list:
        storage_options = {'User-Agent': 'Mozilla/5.0'}
        df = pd.read_csv(url_list[0]['filepath'].replace(" ", "%20"), storage_options=storage_options)
        df['Rows_Count'] = df.index
    return df

if url_list:
    
    df = get_data()
    min_time = int(df.index.min())
    max_time = int(df.index.max())
    #min_ML = min(df['ML'])
    #max_ML = max(df['ML'])
    selected_time_range = st.sidebar.slider('Select the time range, per 100', min_time, max_time, (min_time, max_time), 100)
    df_selected_model = (df.Rows_Count.between(selected_time_range[0], selected_time_range[1]) )
    df = pd.DataFrame(df[df_selected_model])

    df['Rn'] = ( (df['Xn'] ** 2) + (df['Yn'] ** 2) ) ** (1/2)
   
    def make_charts():       
        fig1 = px.scatter(df, x="ML", y="AP", opacity= 0.4)
        fig1.update_traces(marker={'size': 1})
        #Create marker point
        fig1.add_trace(go.Scatter(x=[round(df['ML'].mean(),3)], y=[round(df['AP'].mean(),3)], mode = 'markers',
                        marker_symbol = 'circle', name="ML/AP Point", marker_color='blue',
                        marker_size = 5))
        #Create marker point
        fig1.add_trace(go.Scatter(x=[round(df['Xn'].mean(),3)], y=[round(df['Yn'].mean(),3)], mode = 'markers',
                        marker_symbol = 'circle', name="Zero Point", marker_color='red',
                        marker_size = 5))
        fig1.update_layout(
             margin=dict(l=10, r=10, t=10, b=60),
        )        
        return fig1

    fig1 = make_charts()
    st.write("#")
    st.info("**Details about this trial:**", icon="ℹ️")
    col1,col2,col3 = st.columns(3, gap='medium')
    with col1:
        st.caption("X & Y Columns have been created by CoPx & CoPy Plux equations, in whole time range.")
    with col2:
        st.caption("ML & AP Columns have been created by X & Y Columns minus the means values of X, Y (Xp, Yp) between two triggers.")
    with col3:
        st.caption("Xn & Yn Columns have been created by ML & AP Columns minus the means values of ML, AP between two triggers.")

    col1,col2,col3,col4 = st.columns(4, gap="small")
    with col1:
        st.write("**Instructor:**", url_list[0]['instructor'])
    with col2:
        st.write("**Fullname:**", url_list[0]['fullname'])
    with col3:
        st.write("**Type of the trial:**", url_list[0]['kind_of_trial'])
    with col4:
        st.write("**Date:**", url_list[0]['created_at'])
                
    st.write("---")

    col1,col2 = st.columns([3,1],gap='large')
    with col1:
        st.write("**ML | AP Chart** (in cm)")
        st.plotly_chart(fig1,use_container_width=True)
    with col2:
        st.write("#")
        st.write("#")
        st.write('**Results** (in cm) ')
        #st.write("#")
        #st.write('Min & Max ML:', round(min(df['ML']),3),'&', round(max(df['ML']),3))
        #st.write('Min & Max AP:', round(min(df['AP']),3),'&', round(max(df['AP']),3))
        st.write('ML Mean distance |ML|:', round(df['ML'].abs().mean(),3))
        st.write('Mean distance |Rn|:', round(df['Rn'].abs().mean(),3))
        st.write('Maximal distance |ML|:', round(max(df['ML'].abs()),3))
        st.write('Maximal distance |Rn|:',  round(max(df['Rn'].abs()),3))
        st.write('Root mean square ML:', round(((df['Xn'] ** 2).mean()) ** (1/2),3))
        st.write('Root mean square radius:', round(((df['Rn'] ** 2).mean()) ** (1/2),3))
        st.write('RANGE ML |Xn - Xm|:',  round(np.fabs(df['Xn'].max() - df['Xn'].min()),3))
        st.write('RANGE AP |Yn - Ym|:',  round(np.fabs(df['Yn'].max() - df['Yn'].min()),3))
        st.write('RANGE ML-AP:', round(((df['Xn'].max() - df['Xn'].min()) ** (1/2) + (df['Yn'].max() - df['Yn'].min()) ** (1/2)) ** (1/2),3))
        st.write('RANGE RATIO:', round(np.fabs(df['Xn'].max() - df['Xn'].min()) / np.fabs(df['Yn'].max() - df['Yn'].min()),3))
        
        N = len(df)
        rms_ml = ((1/N) * ((df['Xn']) ** 2).sum()) ** (1/2)
        rms_ap = ((1/N) * ((df['Yn']) ** 2).sum()) ** (1/2)
        cov = ( 1 / N ) * (df['Xn'] * df['Yn']).sum()
        
        p = 3.14
        conf_area = 2 * p * ( len(df) - 1 ) / ( len(df) - 2 ) * (((rms_ml) ** (2) * (rms_ap) ** 2) - (cov) ** 2) ** (1/2)
        st.write('Mean ML & AP:', round(df['ML'].mean(),3),'&', round(df['AP'].mean(),3))
        
        st.write('Mean Xn & Yn:', round(df['Xn'].mean(),3),'&', round(df['Yn'].mean(),3))
        
        
        #st.write('Min Rn',  round(min(df['Rn']),3))

        #MEAN DIST. ML Mean distance ML 1

    st.write("#")
    df['MLabs'] = df['ML'].abs()

    st.write(df['MLabs'].mean())
    
    st.write('Mean ML & AP:', round(df['ML'].mean(),3),'&', round(df['AP'].mean(),3))
    st.write('Mean Xn & Yn:', round(df['Xn'].mean(),3),'&', round(df['Yn'].mean(),3))
    selected_clear_columns = st.multiselect(
    label='Choose columns to be displayed', default=('Time', 'X', 'Y', 'ML', 'AP', 'Xn', 'Yn','Rn'), help='Click to select', options=df.columns)
    st.dataframe(df[selected_clear_columns], use_container_width=True)
    st.download_button(
        label="Export Table",
        data=df[selected_clear_columns].to_csv(),
        file_name='df.csv',
        mime='text/csv',
    )

