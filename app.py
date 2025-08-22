import streamlit as st
import pandas as pd
import json
from collections import defaultdict
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from io import BytesIO
from constants import MIN_PROJECT_RATIO, DAILY_HOURS, PROJECT_MAP_BT, PROJECT_MAP, DEFAULT_END_DATE, DEFAULT_END_DATE_with_timezone, DEFAULT_START_DATE,DEFAULT_START_DATE_with_timezone
from streamlit_javascript import st_javascript

st.page_link("planning/pages/alan.py", label="Alan")
st.page_link("planning/pages/martin.py", label="Martin")

