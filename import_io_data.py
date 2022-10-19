# import_io_data.py
# This script imports and processes the 3-digit IO data and
# 3-digit price/quantity index data in /raw_data/; it
# produces several outputs in /processed_data/, including:
# supplier-customer percentages for the years 1963-2016;
# customer-supplier percentages for the years 1963-2016;
# price and output quantity changes for every industry
# between 1948 and 2016 (excluding 1997; see the notes in
# the relevant section below); and input quantity changes
# for each industry between 1964 and 2016 (again excluding
# 1997; see the notes in the section below).

# Note: to accomplish the above, this file uses two sets of
# IO data: one set spanning 1963-1996 and another set that
# covers 1997-2016; there are four codes in the first set
# that become multiple codes in the second set (these are
# '44RT', '531', '622HO', and 'GFG'; see more below); for
# this reason, the final estimated input quantity changes
# will show non-one ratios for these categories for 1996
# and before and will show ratios of one for these codes
# for 1998 and after; similarly, the codes into which these
# codes are split show non-one ratios for 1998 and after
# but have ratios of one for 1996 and before; lastly, note
# that although HS, GFG, GFGD, GFGN, and GSLG are accounted
# for in the price/quantity index data (see notes below),
# the associated input ratios all end up being one because
# these commodities are all final-use (so are not used
# as inputs to other industries).


# Import pandas
import pandas as pd


###########################################
# Import and process the 1997-2016 IO data
###########################################

# Specify the Excel file containing the 3-digit-NAICS IO data for 1997-2016
xlsx_9716 = pd.ExcelFile('./raw_data/IOUse_Before_Redefinitions_PRO_1997-2016_Summary.xlsx')

# Specify the Excel sheets to read by creating a
# list of strings from '1997' to '2016'
sheets_9716 = []
for year in list(range(1997, 2017)):
    sheets_9716.append(str(year))

# Read in the 1997-2016 IO tables, skipping the header rows (0-4) and the industry
# description row (6); for each table, read 83 data rows and the columns A to CV
data_9716 = pd.read_excel(xlsx_9716, sheets_9716, skiprows=[0, 1, 2, 3, 4, 6], nrows=83, usecols='A:CV')

# Loop through each year (sheet) in the data, fixing the column and
# row names and replacing the character string '...' with zeroes
for i in sheets_9716:
    # Rename a number of columns (all columns beginning with
    # 'Unnamed: #' as well as the commodity description column
    # and the personal consumption column)
    data_9716[i] = data_9716[i].rename(index=str, columns={"Unnamed: 0": "Commodity",
                                                           "Commodities/Industries": "Commodity_Desc",
                                                           "Unnamed: 73": "SumIntermediateSelected",
                                                           "Unnamed: 74": "SumIntermediateNotSelected",
                                                           "Unnamed: 75": "TotalIntermediate",
                                                           "F010": "PersonalConsumption",
                                                           "Unnamed: 96": "SumFinalUseSelected",
                                                           "Unnamed: 97": "SumFinalUseNotSelected",
                                                           "Unnamed: 98": "TotalFinalUse",
                                                           "Unnamed: 99": "TotalCommodityOutput"})

    # Rename rows where the value is 'nan'
    data_9716[i].iloc[73, 0] = 'SumIntermediateSelected'
    data_9716[i].iloc[74, 0] = 'SumIntermediateNotSelected'
    data_9716[i].iloc[75, 0] = 'TotalIntermediate'
    data_9716[i].iloc[79, 0] = 'SumValueAddedSelected'
    data_9716[i].iloc[80, 0] = 'SumValueAddedNotSelected'
    data_9716[i].iloc[81, 0] = 'TotalValueAdded'
    data_9716[i].iloc[82, 0] = 'TotalIndustryOutput'

    # Strip any whitespace from the 'Commodity' column (there is leading
    # whitespace in the Excel file for the 1997-2016 data)
    data_9716[i]['Commodity'] = data_9716[i]['Commodity'].str.strip()

    # Set the 'Commodity' column to be the data frame index
    data_9716[i].set_index('Commodity', inplace=True)

    # Replace all instances of '...' with zeroes
    data_9716[i].replace(to_replace='...', value=0, inplace=True)


###########################################
# Import and process the 1963-1996 IO data
###########################################

# Specify the Excel file containing the 3-digit-NAICS IO data for 1963-1996
xlsx_6396 = pd.ExcelFile('./raw_data/IOUse_Before_Redefinitions_PRO_1963-1996_Summary.xlsx')

# Specify the Excel sheets to read by creating a
# list of strings from '1963' to '1996'
sheets_6396 = []
for year in list(range(1963, 1997)):
    sheets_6396.append(str(year))

# Read in the 1963-1996 IO tables, skipping the header rows (0-4) and the industry
# description row (6); for each table, read 70 data rows and the columns A to CH
data_6396 = pd.read_excel(xlsx_6396, sheets_6396, skiprows=[0, 1, 2, 3, 4, 6], nrows=70, usecols='A:CH')

# Loop through each year (sheet) in the data, fixing the column and
# row names and replacing the character string '...' with zeroes
for i in sheets_6396:
    # Rename a number of columns (all columns beginning with
    # 'Unnamed: #' as well as the commodity description column
    # and the personal consumption column)
    data_6396[i] = data_6396[i].rename(index=str, columns={"Unnamed: 0": "Commodity",
                                                           "Commodities/Industries": "Commodity_Desc",
                                                           "T001": "TotalIntermediate",
                                                           "F010": "PersonalConsumption",
                                                           "Unnamed: 84": "TotalFinalUse",
                                                           "Unnamed: 85": "TotalCommodityOutput"})

    # Ensure that all column names are strings (the numeric industries
    # were being treated as numbers for the 1963-1996 data)
    data_6396[i] = data_6396[i].rename(columns=str)

    # Rename rows where the value is 'nan'
    data_6396[i].iloc[67, 0] = 'TotalIntermediate'
    data_6396[i].iloc[68, 0] = 'TotalValueAdded'
    data_6396[i].iloc[69, 0] = 'TotalIndustryOutput'

    # Set the 'Commodity' column to be the data frame index
    data_6396[i].set_index('Commodity', inplace=True)

    # Ensure that all row names are strings (the numeric commodities
    # were being treated as numbers for the 1963-1996 data)
    data_6396[i] = data_6396[i].rename(index=str)

    # Replace all instances of '...' with zeroes
    data_6396[i].replace(to_replace='...', value=0, inplace=True)


########################################################
# Extract and save the commodity names and descriptions
########################################################

# Extract the commodity names and descriptions from the
# 1997 data tab; rename the columns to "industry" and
# "description" (which treats commodities and industries
# as interchangeable)
descriptions = data_9716['1997']['Commodity_Desc'] \
    .reset_index() \
    .rename(columns={"Commodity": "industry",
                     "Commodity_Desc": "description"})

# Save the descriptions to a .csv file
descriptions.to_csv('./processed_data/industry_descriptions.csv', index=False)


########################################################
# Calculate supplier-customer percentages for all years
########################################################

# Create an empty data frame to hold the fraction of a commodity's total
# intermediate output purchased by each industry
commodity_buyers = pd.DataFrame(columns=['year', 'commodity', 'industry', 'value'])
year_list = []
commodity_list = []
industry_list = []
value_list = []

# Loop through the years
for demand_year in range(1963, 2017):

    # Convert the year to a string
    demand_year_str = str(demand_year)

    # Extract the commodity names
    if demand_year >= 1997:
        ind_names = data_9716[demand_year_str].index.tolist()[0:71]
    else:
        ind_names = data_6396[demand_year_str].index.tolist()[0:65]

    # Loop through the commodities
    for commodity in ind_names:

        # Extract the total intermediate demand for the
        # current commodity in the specified year
        if demand_year >= 1997:
            commodity_demand = data_9716[demand_year_str]['TotalIntermediate'][commodity]
        else:
            commodity_demand = data_6396[demand_year_str]['TotalIntermediate'][commodity]

        # Determine each industry's use of the commodity
        # in the specified year
        for industry in ind_names:
            if demand_year >= 1997:
                industry_demand = data_9716[demand_year_str][industry][commodity]
            else:
                industry_demand = data_6396[demand_year_str][industry][commodity]

            year_list.append(demand_year)
            commodity_list.append(commodity)
            industry_list.append(industry)

            if commodity_demand != 0:
                value_list.append(industry_demand / commodity_demand)
            else:
                value_list.append(0)

# Fill out the data frame with the calculated values
commodity_buyers['year'] = year_list
commodity_buyers['commodity'] = commodity_list
commodity_buyers['industry'] = industry_list
commodity_buyers['value'] = value_list

# Export the data frame to a .csv file
commodity_buyers.to_csv('./processed_data/commodity_buyers.csv', index=False)


########################################################
# Calculate customer-supplier percentages for all years
########################################################

# Create an empty data frame to hold the fraction of an industry's total
# intermediate inputs supplied by each commodity
industry_suppliers = pd.DataFrame(columns=['year', 'industry', 'commodity', 'value'])
year_list = []
industry_list = []
commodity_list = []
value_list = []

# Loop through the years
for demand_year in range(1963, 2017):

    # Convert the current year to a string
    demand_year_str = str(demand_year)

    # Extract the industry names
    if demand_year >= 1997:
        ind_names = data_9716[demand_year_str].index.tolist()[0:71]
    else:
        ind_names = data_6396[demand_year_str].index.tolist()[0:65]

    # Loop through the industries
    for industry in ind_names:

        # Extract the total intermediate input use for the
        # current industry in the specified year
        if demand_year >= 1997:
            industry_demand = data_9716[demand_year_str][industry]['TotalIntermediate']
        else:
            industry_demand = data_6396[demand_year_str][industry]['TotalIntermediate']

        # Determine the industry's use of each of the commodities
        # in the specified year
        for commodity in ind_names:
            if demand_year >= 1997:
                commodity_demand = data_9716[demand_year_str][industry][commodity]
            else:
                commodity_demand = data_6396[demand_year_str][industry][commodity]

            year_list.append(demand_year)
            industry_list.append(industry)
            commodity_list.append(commodity)

            if industry_demand != 0:
                value_list.append(commodity_demand / industry_demand)
            else:
                value_list.append(0)

# Fill out the data frame with the calculated values
industry_suppliers['year'] = year_list
industry_suppliers['industry'] = industry_list
industry_suppliers['commodity'] = commodity_list
industry_suppliers['value'] = value_list

# Export the data frame to a .csv file
industry_suppliers.to_csv('./processed_data/industry_suppliers.csv', index=False)


#########################################################
# Import the price and quantity index data for 1947-2016
#########################################################

# Import the price indexes .csv file for 1997-2017
prices_9717 = pd.read_csv('./raw_data/Price_Index_1997-2017.csv',
                          index_col=0, skiprows=[0, 1, 2, 3, 102], nrows=100)

# Import the price indexes .csv file for 1947-1997
prices_4797 = pd.read_csv('./raw_data/Price_Index_1947-1997.csv',
                          index_col=0, skiprows=[0, 1, 2, 3, 102], nrows=100)

# Import the quantity indexes .csv file for 1997-2017
quantities_9717 = pd.read_csv('./raw_data/Quantity_Index_1997-2017.csv',
                              index_col=0, skiprows=[0, 1, 2, 3, 102], nrows=100)

# Import the quantity indexes .csv file for 1947-1997
quantities_4797 = pd.read_csv('./raw_data/Quantity_Index_1947-1997.csv',
                              index_col=0, skiprows=[0, 1, 2, 3, 102], nrows=100)

# Rename the industry description column
prices_9717 = prices_9717.rename(index=str, columns={"Unnamed: 1": "Industry_Desc"})
prices_4797 = prices_4797.rename(index=str, columns={"Unnamed: 1": "Industry_Desc"})
quantities_9717 = quantities_9717.rename(index=str, columns={"Unnamed: 1": "Industry_Desc"})
quantities_4797 = quantities_4797.rename(index=str, columns={"Unnamed: 1": "Industry_Desc"})

# Replace all instances of '...' with zeroes (for the 1997-2017 data,
# this only occurs in the year 2017; the year 2017 is excluded in the
# processing below because its values are preliminary)
prices_9717.replace(to_replace='...', value=0, inplace=True)
prices_4797.replace(to_replace='...', value=0, inplace=True)
quantities_9717.replace(to_replace='...', value=0, inplace=True)
quantities_4797.replace(to_replace='...', value=0, inplace=True)

# Convert the price and quantity values in the 1947-1997 data
# from strings to floats
for col in list(range(1, 52)):
    prices_4797.iloc[:, col] = prices_4797.iloc[:, col].astype(float)
    quantities_4797.iloc[:, col] = quantities_4797.iloc[:, col].astype(float)

# Create a list of row names that match the price/quantity index data to
# the input-output data; these rows match one-to-one except in these cases:
# '44RT', '531', '622HO', and 'GFG'; these are all in the 1963-1996 IO data
# and then are broken into multiple categories in the 1997-2016 IO data (441,
# 445, 452, and 4A0 for 44RT; HS and ORE for 531; 622 and 623 for 622HO; and
# GFGD and GFGN for GFG); therefore, 44RT, 531, 622HO, and GFG are inserted
# in this list to correspond to the appropriate higher-level categories in
# the price/quantity index data ("retail trade" for 44RT, "real estate" for
# 531, "health care and social assistance" for 622HO, and "general government"
# for GFG); this allows for non-zero price/quantity indexes to be used for
# these four categories during the years 1996 and before, and then the
# one-to-one mappings are used for the years 1997 and after; finally, note
# that although HS, GFG, GFGD, GFGN, and GSLG are included here, these
# commodities are never used as inputs in the IO data, and so the final
# calculated input changes for these suppliers are zeros for all industries
row_names = ['All_Industries', 'Private_Industries', 'Agriculture_Forestry_Fishing_Hunting', '111CA', '113FF',
             'Mining', '211', '212', '213', '22', '23', 'Manufacturing', 'Durable_Goods', '321', '327', '331', '332',
             '333', '334', '335', '3361MV', '3364OT', '337', '339', 'Nondurable_Goods', '311FT', '313TT', '315AL',
             '322', '323', '324', '325', '326', '42', '44RT', '441', '445', '452', '4A0', 'Transportation_Warehousing',
             '481', '482', '483', '484', '485', '486', '487OS', '493', 'Information', '511', '512', '513', '514',
             'Finance_Insurance_RealEstate_Rental_Leasing', 'Finance_Insurance', '521CI', '523', '524', '525',
             'RealEstate_Rental_Leasing', '531', 'HS', 'ORE', '532RL', 'Professional_BusinessServices',
             'Professional_Scientific_TechnicalServices', '5411', '5415', '5412OP', '55',
             'Administrative_WasteManagementServices', '561', '562', 'EducationalServices_HealthCare_SocialAssistance',
             '61', '622HO', '621', '622', '623', '624', 'Arts_Entertainment_Recreation_Accommodation_FoodServices',
             'Arts_Entertainment_Recreation', '711AS', '713', 'Accommodation_FoodServices', '721', '722', '81',
             'Government', 'Federal', 'GFG', 'GFGD', 'GFGN', 'GFE', 'State_Local', 'GSLG', 'GSLE',
             'Private_Goods_Industries', 'Private_Services_Industries',
             'Information_Communications_Technology_Industries']

# Update the row names
prices_9717['temp_names'] = row_names
prices_9717.set_index('temp_names', inplace=True)
prices_4797['temp_names'] = row_names
prices_4797.set_index('temp_names', inplace=True)
quantities_9717['temp_names'] = row_names
quantities_9717.set_index('temp_names', inplace=True)
quantities_4797['temp_names'] = row_names
quantities_4797.set_index('temp_names', inplace=True)

# Extract the commodity description column and the price
# indexes for 1947-1996 from the 1947-1997 data
prices_4796 = prices_4797.iloc[:, 0:51]

# Extract the price indexes for 1997-2016 from the
# 1997-2017 data (the 2017 column appears in both the
# 1947-1997 data and the 1997-2017 data; however, it
# only contains values for the "new" commodities (like
# IT) in the latter; in addition, only take values up
# to 2016 because the 2017 values are preliminary)
prices_9716 = prices_9717.iloc[:, 1:21]

# Join the two data frames together to form a full set
# of price indexes spanning 1947-2016; note that for
# the "new" commodities (like IT), these values are
# zeroes until 1997 and then jump up
prices_4716 = prices_4796.join(prices_9716)

# Repeat this process with the quantities data to
# construct a full set of quantity indexes spanning
# 1947-2016; as with the prices, note that for the
# "new" commodities (like IT), these values are zeros
# until 1997 and then jump up
quantities_4796 = quantities_4797.iloc[:, 0:51]
quantities_9716 = quantities_9717.iloc[:, 1:21]
quantities_4716 = quantities_4796.join(quantities_9716)


#########################################################################
# Calculate price and output quantity changes for 1948-2016 (excl. 1997)
#########################################################################

# Generate a list of strings from '1948' to '2016',
# excluding '1997'; this will calculate price and
# quantity changes from 1948-1996 using the 1947-
# 1996 price/quantity index data and from 1998-
# 2016 using the 1997-2016 price/quantity index data
col_names = []
for year in list(range(1948, 2017)):
    col_names.append(str(year))
col_names.remove('1997')

# Create empty data frames to hold the results
price_change = pd.DataFrame(columns=col_names)
quantity_change = pd.DataFrame(columns=col_names)

# Iterate over the columns (years)
for col in col_names:

    # Create an empty list to hold the results for this column (year)
    val_list_p = []
    val_list_q = []

    # Iterate over the rows (industries)
    for row in row_names:

        # Extract the value for this industry/year combination
        val_curr_p = prices_4716[col][row]
        val_curr_q = quantities_4716[col][row]

        # Extract the value for this industry/commodity combination in
        # the previous year
        val_prev_p = prices_4716[str(int(col) - 1)][row]
        val_prev_q = quantities_4716[str(int(col) - 1)][row]

        # Add the ratio of these two values to the list
        if val_prev_p != 0:
            val_list_p.append(val_curr_p / val_prev_p)
        else:
            val_list_p.append(0)
        if val_prev_q != 0:
            val_list_q.append(val_curr_q / val_prev_q)
        else:
            val_list_q.append(0)

    # Add the list to the data frame as a new column
    price_change[col] = val_list_p
    quantity_change[col] = val_list_q

# Add a column with the row names
price_change['temp_names'] = row_names
quantity_change['temp_names'] = row_names

# Reshape the price change data from wide to long format; each industry-year
# combination will now be on its own row
price_change_out = pd.melt(price_change, id_vars=['temp_names'])

# Rename the columns
price_change_out.columns = ['industry', 'year', 'price_change']

# Write the price change data to a .csv file for later use
price_change_out.to_csv('./processed_data/price_changes.csv', index=False)

# Reshape the quantity change data from wide to long format; each industry-year
# combination will now be on its own row
quantity_change_out = pd.melt(quantity_change, id_vars=['temp_names'])

# Rename the columns
quantity_change_out.columns = ['industry', 'year', 'quantity_change']

# Write the quantity change data to a .csv file for later use
quantity_change_out.to_csv('./processed_data/output_quantity_changes.csv', index=False)

# Set the temp_names column to be the index for both the
# price change and quantity change data
price_change.set_index('temp_names', inplace=True)
quantity_change.set_index('temp_names', inplace=True)


##############################################################
# Calculate input quantity changes for 1964-2016 (excl. 1997)
##############################################################

# Extract the column names for all industries up to and
# including "personal consumption" for the 1997-2016 IO
# data (arbitrarily using the 1997 columns)
col_names_9716 = data_9716['1997'].columns.tolist()[1:76]

# Extract the column names for all industries up to and
# including "personal consumption" for the 1963-1996 IO
# data (arbitrarily using the 1963 columns)
col_names_6396 = data_6396['1963'].columns.tolist()[1:68]

# Extract the row names for all commodities up to
# 'Other' for the 1997-2016 IO data (arbitrarily
# using the 1997 rows)
row_names_9716 = data_9716['1997'].index.tolist()[0:73]

# Extract the row names for all commodities up to
# 'Other' for the 1963-1996 IO data (arbitrarily
# using the 1963 rows)
row_names_6396 = data_6396['1963'].index.tolist()[0:67]

# Set the years to iterate over by creating a list of
# strings from '1964' to '2016', excluding '1997'; input
# changes will be calculated from 1964 to 1996 using
# the 1963-1996 IO data and from 1998 to 2016 using the
# 1997-2016 IO data
years = []
for year_val in list(range(1964, 2017)):
    years.append(str(year_val))
years.remove('1997')

# Create an empty dictionary to hold the input quantity
# change results; each element of this dictionary is a
# data frame with the quantity changes values for a
# particular year
input_change = {}

# Create an empty data frame to hold the personal
# consumption change results
PC_change = pd.DataFrame(columns=['year', 'industry', 'change'])
PC_ind_list = []
PC_val_list = []

# Iterate over the years
for year in years:

    if int(year) >= 1998:
        col_names = col_names_9716
        row_names = row_names_9716
        data_io = data_9716
    else:
        col_names = col_names_6396
        row_names = row_names_6396
        data_io = data_6396

    # Create an empty data frame to hold the results
    # for the current year
    diff = pd.DataFrame(columns=col_names)

    # Iterate over the columns (industries) in the current year
    for col in col_names:

        # Create an empty list to hold the results
        # for this column (industry)
        val_list = []

        # Iterate over the rows (commodities) in the current year
        for row in row_names:

            # Extract the value for this industry/commodity combination in
            # the current year
            val_curr = data_io[year][col][row]

            # Extract the value for this industry/commodity combination in
            # the previous year
            val_prev = data_io[str(int(year)-1)][col][row]

            if val_prev != 0:
                # Extract the price change factor for the current commodity
                # in the current year; for the 'Used' and 'Other' commodities,
                # use a factor of one
                if (row == 'Used') or (row == 'Other'):
                    price_factor = 1
                else:
                    price_factor = price_change[year][row]

                # Add the ratio of these two values to the list
                if price_factor != 0:
                    val_list.append((val_curr / val_prev) / price_factor)
                else:
                    val_list.append(0)
            else:
                val_list.append(0)

        # Replace the appropriate column in the data frame with the list
        diff[col] = val_list

    # Add a column with the row names
    diff['temp_names'] = row_names

    # Store the completed data frame in the dictionary
    input_change[year] = diff

    # Calculate the percentage change in personal consumption
    PC_val_curr = data_io[year]['TotalIntermediate']['TotalIntermediate']
    PC_val_prev = data_io[str(int(year)-1)]['TotalIntermediate']['TotalIntermediate']
    PC_ind_list.append("PersonalConsumption")
    PC_val_list.append(PC_val_curr / PC_val_prev)

# Add the years and the change ratios to the PC_change
# data frame; save the data to a .csv file
PC_change['year'] = years
PC_change['industry'] = PC_ind_list
PC_change['change'] = PC_val_list
PC_change.to_csv('./processed_data/personal_consumption_changes.csv', index=False)

# Create an empty data frame to store the final output; this
# "flattens" the values in the input_change dictionary so that
# all years are contained in one spreadsheet
final_data = pd.DataFrame(columns=['year', 'industry', 'commodity', 'value'])

# Iterate over the years
for year in years:
    # Reshape the data from wide into long format; the first column will be
    # 'temp_names' (the commodities) and the second column will have the
    # values that were originally the column names (the industries)
    new_rows = pd.melt(input_change[year], id_vars=['temp_names'])

    # Add a column with the current year
    new_rows['year'] = year

    # Rename and reorder the columns
    new_rows.columns = ['commodity', 'industry', 'value', 'year']
    new_rows = new_rows[['year', 'industry', 'commodity', 'value']]

    # Add the data for this year to the final data frame
    final_data = pd.concat([final_data, new_rows], ignore_index=True)

# Write the final data to a .csv file
final_data.to_csv('./processed_data/input_quantity_changes.csv', index=False)
