"""
UI utilities for the Streamlit interface.
"""

import streamlit as st
from typing import List, Dict, Any, Callable, Optional, Union
import pandas as pd

def display_in_area(element_function: Callable, *args, **kwargs) -> Any:
    """Displays a UI element in the appropriate area (sidebar or main) based on pinning mode"""
    area = st.sidebar if st.session_state.get('pin_selections', True) else st
    return getattr(area, element_function.__name__)(*args, **kwargs)

def create_metric_row(metrics_data: List[Dict[str, Any]], n_columns: int = 4) -> None:
    """Creates a row of metrics in the dashboard"""
    columns = st.columns(n_columns)
    
    for i, metric in enumerate(metrics_data):
        with columns[i % n_columns]:
            if 'delta' in metric:
                st.metric(
                    label=metric['label'], 
                    value=metric['value'], 
                    delta=metric['delta'],
                    delta_color=metric.get('delta_color', 'normal')
                )
            else:
                st.metric(label=metric['label'], value=metric['value'])

def display_warning_if_empty(data: Union[pd.DataFrame, List], message: str) -> bool:
    """Displays a warning if data is empty"""
    if (isinstance(data, pd.DataFrame) and data.empty) or (isinstance(data, list) and not data):
        st.warning(message)
        return True
    return False

def create_expander_section(title: str, content_function: Callable, expanded: bool = False) -> Any:
    """Creates an expandable section with a title and content"""
    with st.expander(title, expanded=expanded):
        return content_function()

def display_table_with_title(title: str, data: pd.DataFrame, use_container_width: bool = True)  -> None:
    """Displays a table with a title"""
    st.subheader(title)
    if not data.empty:
        st.dataframe(data, use_container_width=use_container_width)
    else:
        st.info("No data available for this table.")

def create_tab_section(tabs_data: Dict[str, Callable]) -> None:
    """Creates a tabbed section"""
    tabs = st.tabs(list(tabs_data.keys()))
    
    for i, (tab_name, content_function) in enumerate(tabs_data.items()):
        with tabs[i]:
            content_function()