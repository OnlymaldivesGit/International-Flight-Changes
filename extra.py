# invalid_date_highlight = JsCode("""
# function(params) {
#     if (params.value === true) {
#         return {
#             'color': '#ffffff',
#             'backgroundColor': '#f7a492',
#             'textAlign': 'center'
#         }
#     } else {
#         return {
#             'textAlign': 'center'
#         }
#     }
# }
# """)

# column_styles = {
#     "Missing Value": invalid_date_highlight,
#     "Unmatched Flight Counts": invalid_date_highlight
# }



# def show_aggrid(df, column_styles=None):
#     gb = GridOptionsBuilder.from_dataframe(df)
#     gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum')
#     gb.configure_pagination(enabled=True, paginationPageSize=10)
#     gb.configure_selection(selection_mode="multiple", use_checkbox=True)
#     gb.configure_side_bar(filters_panel=True)

#     # Apply custom styles if provided
#     if column_styles:
#         for col, style in column_styles.items():
#             if col in df.columns:
#                 gb.configure_column(col, cellStyle=style,autoWidth=True)

#     grid_options = gb.build()

#     AgGrid(
#         df,
#         gridOptions=grid_options,
#         update_mode=GridUpdateMode.NO_UPDATE,
#         height=400,
#         width='100%',
#         allow_unsafe_jscode=True
#     )


