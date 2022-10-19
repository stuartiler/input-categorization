# categorize_input_pairs.py
# This script takes the data files in /processed_data/
# and, for a specified "focus" commodity, categorizes
# the usage of that commodity as a substitute or
# complement (or neither) vis-a-vis every other
# commodity within each industry's production process.
# The script does this by training a model to predict,
# for each industry, how the industry's use of the
# focus commodity changes given the simultaneous
# changes in its usage of the other commodities and
# the changes in its output; the predictions from
# this model are then used to categorize each pair of
# inputs (that involve the focus commodity) as
# substitutes, complements, or neither.


# ***
# Load packages
# ***
from numpy import linspace, round, array
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import GridSearchCV, RepeatedKFold
from sklearn.linear_model import LinearRegression


# ***
# Specify the focus commodity and the associated year range(s)
# ***

# This is the commodity for which pairwise input patterns
# (vis-a-vis all other commodities) will be categorized;
# see the input-output tables in /raw_data/ for the full
# list of commodity codes and their descriptions
focus_commodity = "324"  # petroleum and coal products

# Specify the year ranges for which to categorize input
# patterns; the years in each of the vectors within this
# list will be processed together under the assumption
# that input substitution patterns are stable over each
# of the associated time periods
year_ranges = [range(1964, 2017)]  # use a single 1964-2016 year range


# ***
# Specify parameters for categorizing input pairs as substitutes/complements
# ***

# These are the values to use when predicting how the
# usage of the focus commodity changes when usage of
# the other commodities (and the output) change
test_values = linspace(-0.5, 0.5, 51)  # use test values ranging from -50% to +50%

# This value determines how conservative the approach
# will be in categorizing input pairs as substitutes
# or complements; lower values are more conservative
# and will lead to fewer input pairs being classified
# one way or the other
rmse_divisor = 4

# Specify the values to represent the categorization
# of each input pair in the results (pairs that have
# not been classified are signified by an empty string)
complements_value = 'C'
substitutes_value = 'S'


# ***
# Load the input and output quantity change data
# ***

# Load the input quantity change data calculated in import_io_data.py;
# see the notes at the top of that file for some important information
# about these results
input_changes = pd.read_csv('./processed_data/input_quantity_changes.csv',
                            index_col=False)

# The Python code constructs the values as ratios centered
# around one; subtract one to center the values around zero
input_changes.loc[:, 'value'] -= 1

# Load the output quantity change data calculated
# in import_io_data.py
output_changes = pd.read_csv('./processed_data/output_quantity_changes.csv',
                             index_col=0).reset_index()

# The Python code constructs the values as ratios centered
# around one; subtract one to center the values around zero
output_changes.loc[:, 'quantity_change'] -= 1


# ***
# Prepare the training data and specify the industries to process
# ***

# Reshape the data into wide format so that each year-industry combination
# is a single row and the commodities are the columns
input_changes = input_changes \
    .pivot(index=['year', 'industry'], columns="commodity", values="value"). \
    reset_index()

# Delete all columns where a single commodity in the 1963-1996 IO data
# was expanded into multiple commodities in the 1997-2016 IO data; this
# allows for a consistent set of predictors over the whole time period
input_changes.drop(columns=['44RT', '441', '445', '452', '4A0', '531', 'HS', 'ORE',
                            '622HO', '622', '623', 'GFG', 'GFGD', 'GFGN'],
                   inplace=True)

# Merge the output quantity data into the input quantity data
input_changes = pd.merge(input_changes,
                         output_changes,
                         how='left',
                         on=['industry', 'year'])

# Create an empty data frame to hold the results by copying the
# reshaped data, deleting all rows, and adding an "rmse" column
coefficient_results = input_changes \
                          .copy(deep=True) \
                          .iloc[0:0] \
                          .assign(rmse=None)

# Bring the 'industry', 'year', and 'rmse' columns to the front
coefficient_results = coefficient_results[['industry', 'year', 'rmse'] +
                                          [x for x in coefficient_results if x not in ['industry', 'year', 'rmse']]]

# Generate a list of the commodities by extracting the
# column names of the results data frame after dropping
# the year and industry columns
commodity_list = coefficient_results \
    .drop(columns=['industry', 'year', 'rmse']) \
    .columns \
    .to_list()

# Specify the industries to process by taking the
# commodity list and removing the "Other" and "Used"
# commodities and the output quantity change
industries = [x for x in commodity_list if x != 'Other' and x != 'Used' and x != 'quantity_change']


# ***
# Specify parameters for model training
# ***

# Create the XGBRegressor object, which by default
# uses the objective of 'reg:squarederror'
estimator = XGBRegressor()

# Set the hyperparameter grid over which to search; the
# grid has been limited in this example to reduce the
# computational burden, but some additional values that
# may improve the RMSE are:
#   'n_estimators': range(50, 2050, 50)
#   'eta': [0.01, 0.05]
#   'gamma': [0, 0.01]
parameters = {
    'n_estimators': range(50, 1550, 50),
    'max_depth': [2],
    'eta': [0.01],
    'gamma': [0],
    'colsample_bytree': [1],
    'min_child_weight': [1],
    'subsample': [1],
}

# Set the training control to four-fold cross validation
# with two repeats
cv = RepeatedKFold(n_splits=4, n_repeats=2)

# Create a GridSearchCV object with the estimator,
# parameters, and cross-validation initialized
# above; set scoring to be RMSE
grid_search = GridSearchCV(
    estimator=estimator,
    param_grid=parameters,
    scoring='neg_root_mean_squared_error',
    n_jobs=10,
    cv=cv,
    verbose=False
)


# ***
# Train models on the input patterns for the focus commodity
# ***

# Loop through the specified industries
for current_industry in industries:

    # Skip any industry that matches the focus commodity
    if current_industry == focus_commodity:
        print("Skipping industry ", current_industry, " because it matches the focus commodity.", sep='')
        continue

    # Print a message to the console
    print("Processing industry ", current_industry, ".", sep='')

    # Loop through each of the specified year ranges
    for current_years in year_ranges:

        # Print a message to the console
        print("Processing year range ", str(current_years[0]), ":", str(current_years[-1]), ".", sep='')

        # Extract the data for the current industry and year range
        data_extract = input_changes.loc[(input_changes['industry'] == current_industry) &
                                         (input_changes['year'].between(current_years[0], current_years[-1]))]

        # If there are no observations, skip to the next year range
        if data_extract.shape[0] == 0:
            print("Skipping industry ",
                  current_industry,
                  " in year(s) ",
                  str(current_years[0]), ":", str(current_years[-1]),
                  " because the industry is not present in that/those year(s).",
                  sep='')
            continue

        # If an industry does not use a particular commodity in some years,
        # that commodity will have a value of -1 in the dataset for those
        # years; ensure that the focus commodity is used in every year of
        # the current year range
        if sum(data_extract[focus_commodity] == -1) > 0:
            print("Skipping industry ",
                  current_industry,
                  " in year(s) ",
                  str(current_years[0]), ":", str(current_years[-1]),
                  " because of incomplete usage of the focus commodity in that/those year(s).",
                  sep='')
            continue

        # Create the training dataset by taking the data extract and
        # subtracting the output quantity changes from each column
        # of input quantity changes
        data_train = data_extract.copy(deep=True)
        commodity_list_without_qc = [x for x in commodity_list if x != 'quantity_change']
        data_train.loc[:, commodity_list_without_qc] = data_extract.loc[:, commodity_list_without_qc] \
            .sub(data_extract['quantity_change'],
                 axis='rows')

        # Count how many -1 values appear in each column of the
        # data extract; these -1 values represent years in which
        # the associated input was not used
        neg_one_counts = (data_extract.loc[:, commodity_list] == -1).sum(axis=0)

        # Create a vector of commodities to use in the prediction
        # by (1) keeping only those without any values of -1; and
        # (2) ensuring the focus commodity does not appear
        cols_for_prediction = neg_one_counts.loc[neg_one_counts == 0].index.to_list()
        cols_for_prediction = [x for x in cols_for_prediction if x != focus_commodity]

        # Extract the columns to use in prediction and the column to
        # be predicted (i.e., the change in use of the focus commodity)
        data_train_x = data_train.loc[:, cols_for_prediction]
        data_train_y = data_train.loc[:, focus_commodity]

        # Train the model, where the dependent variable is the input
        # quantity change for the focus commodity and the predictors
        # are the input quantity changes for the remainder of the
        # commodities (as selected above) as well as the output
        # quantity change; by default, this training will use an
        # objective of 'reg:squarederror'
        grid_search.fit(data_train_x, data_train_y)

        # print(grid_search.best_estimator_)
        # print("best index: ", grid_search.best_index_)
        # print("neg rmse: ", grid_search.best_score_)

        # Add a new row of zeros to the coefficient results
        coefficient_results.loc[len(coefficient_results.index)] = 0

        # Store the current industry, current year range, and the
        # RMSE from the training
        coefficient_results.loc[len(coefficient_results.index) - 1, 'industry'] = current_industry
        coefficient_results.loc[len(coefficient_results.index) - 1, 'year'] = \
            str(current_years[0]) + ":" + str(current_years[-1])
        coefficient_results.loc[len(coefficient_results.index) - 1, 'rmse'] = -grid_search.best_score_

        # Using the fitted model, repeatedly predict the difference in
        # quantity change for the focus commodity given a difference in
        # quantity change for each other predictor commodity (as well
        # as a difference in quantity change for the industry-level
        # output quantity index)
        for test_commodity in cols_for_prediction:

            # Initialize lists that will hold pairs of test quantity
            # changes (for the current test commodity) and the associated
            # predicted change in the focus commodity
            replaced_val = []
            predicted_val = []

            # Create a row of zeros that represents no input quantity
            # change across all commodities (as well as no output quantity
            # change for the current industry)
            sub_test = data_train_x \
                .copy(deep=True) \
                .iloc[0:1]
            sub_test.iloc[0, :] = 0

            # Loop through the test values
            for test_value in test_values:

                # Replace the current test commodity's quantity change value
                # with the current test value
                sub_test[test_commodity] = round(test_value, 2)

                # Store the test value
                replaced_val.append(round(test_value, 2))

                # Predict the quantity change for the focus commodity given
                # this test value
                sub_predict = grid_search.predict(sub_test)

                # Store the predicted value
                predicted_val.append(sub_predict[0])

            # Regress the predicted values on the test values
            reg = LinearRegression(fit_intercept=True) \
                .fit(array(replaced_val).reshape((len(replaced_val), 1)),
                     array(predicted_val).reshape((len(predicted_val), 1)))

            # Add the coefficient on the replaced values variable as
            # the entry in the column for the current test commodity
            coefficient_results.loc[len(coefficient_results.index) - 1, test_commodity] = reg.coef_.tolist()[0]


# ***
# Create the categorization results from the coefficient results
# ***

# Create a new data frame to hold the categorization results by
# copying the coefficient results
categorization_results = coefficient_results.copy(deep=True)

# Replace the values in the categorization results data frame
# with the complements value, the substitutes value, or an
# empty string depending on the whether (1) the slope is positive
# or negative and (2) how large it is (in absolute value)
# compared to the RMSE
for commodity in commodity_list:
    categorization_results.loc[coefficient_results.loc[:, commodity] >=
                               (coefficient_results.loc[:, 'rmse'] / rmse_divisor),
                               commodity] = 'C'

    categorization_results.loc[coefficient_results.loc[:, commodity] <=
                               (-coefficient_results.loc[:, 'rmse'] / rmse_divisor),
                               commodity] = 'S'

    categorization_results.loc[abs(coefficient_results.loc[:, commodity]) <
                               (coefficient_results.loc[:, 'rmse'] / rmse_divisor),
                               commodity] = ''


# ***
# Save the coefficient and categorization results in .csv format
# ***

# Save the coefficient results
coefficient_results.to_csv('./results_data/coefficient_results_python_focus' + focus_commodity + '.csv',
                           index=False)

# Save the categorization results
categorization_results.to_csv('./results_data/categorization_results_python_focus' + focus_commodity + '.csv',
                              index=False)
