# categorize_input_pairs.r
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
# Load libraries
# ***
library(gbm)
library(caret)
library(dplyr)
library(tidyr)




# ***
# Specify the focus commodity and the associated year range(s)
# ***

# This is the commodity for which pairwise input patterns
# (vis-a-vis all other commodities) will be categorized;
# see the input-output tables in /raw_data/ for the full
# list of commodity codes and their descriptions
focus_commodity <- "324"  # petroleum and coal products

# Specify the year ranges for which to categorize input
# patterns; the years in each of the vectors within this
# list will be processed together under the assumption
# that input substitution patterns are stable over each
# of the associated time periods
year_ranges <- list(c(1964:2016))  # use a single 1964-2016 year range




# ***
# Specify parameters for categorizing input pairs as substitutes/complements
# ***

# These are the values to use when predicting how the
# usage of the focus commodity changes when usage of
# the other commodities (and the output) change
test_values <- seq(-0.5, 0.5, 0.02)  # use test values ranging from -50% to +50%

# This value determines how conservative the approach
# will be in categorizing input pairs as substitutes
# or complements; lower values are more conservative
# and will lead to fewer input pairs being classified
# one way or the other
rmse_divisor <- 4

# Specify the values to represent the categorization
# of each input pair in the results (pairs that have
# not been classified are signified by an empty string)
complements_value <- "C"
substitutes_value <- "S"




# ***
# Load the input and output quantity change data
# ***

# Load the input quantity change data calculated in import_io_data.py;
# see the notes at the top of that file for some important information
# about these results
input_quantity_data <- read.csv("./processed_data/input_quantity_changes.csv")

# The Python code constructs the values as ratios centered
# around one; subtract one to center the values around zero
input_quantity_data$value = input_quantity_data$value - 1

# Load the output quantity change data calculated
# in import_io_data.py
output_quantity_data <- read.csv("./processed_data/output_quantity_changes.csv")

# The Python code constructs the values as ratios centered
# around one; subtract one to center the values around zero
output_quantity_data$quantity_change = output_quantity_data$quantity_change - 1




# ***
# Prepare the training data and specify the industries to process
# ***

# Reshape the data into wide format so that each year-industry combination
# is a single row and the commodities are the columns
data_reshape <- spread(input_quantity_data,
                       key = commodity,
                       value = value)

# Delete all columns where a single commodity in the 1963-1996 IO data
# was expanded into multiple commodities in the 1997-2016 IO data; this
# allows for a consistent set of predictors over the whole time period
data_reshape[,c("44RT", "441", "445", "452", "4A0", "531", "HS", "ORE",
                "622HO", "622", "623", "GFG", "GFGD", "GFGN")] <- NULL

# Merge the output quantity data into the input quantity data
data_reshape <- data_reshape %>%
  left_join(output_quantity_data, by=c("industry", "year"))

# Create an empty data frame to hold the results by extracting the
# commodity column headers and the output quantity change header
# from the reshaped data
coefficient_results <- data_reshape %>%
  select("111CA":"quantity_change")
coefficient_results <- coefficient_results[0,]

# Generate a list of the commodities by extracting the
# column names of the results data frame after dropping
# the quantity change column
commodity_list <- names(coefficient_results %>% select(-quantity_change))

# Initialize an empty list to hold the name of the
# processed industries
industry_list <- list()

# Initialize an empty list to hold the years in
# each of the processed year groups
year_range_list <- list()

# Initialize an empty list to hold the average RMSE across
# the folds for each trained model
rmse_list <- c()

# Specify the industries to process by taking the
# commodity list and removing the "Other" and "Used"
# commodities
industries <- commodity_list
industries <- industries[industries != "Other"]
industries <- industries[industries != "Used"]




# ***
# Specify parameters for model training
# ***

# Set the training control to four-fold cross validation
# with two repeats
fitControl <- trainControl(method = "repeatedcv",
                           number = 4,
                           repeats = 2)

# Set the hyperparameter grid over which to search; the
# grid has been limited in this example to reduce the
# computational burden, but some additional values that
# may improve the RMSE are:
#   nrounds = c(c(1:40)*50)
#   eta = c(0.01, 0.05)
#   gamma = c(0, 0.01)
grid <- expand.grid(nrounds = c(c(1:30)*50),
                    max_depth = c(2),
                    eta = c(0.01),
                    gamma = c(0),
                    colsample_bytree = c(1),
                    min_child_weight = c(1),
                    subsample = c(1))




# ***
# Train models on the input patterns for the focus commodity
# ***

# Loop through the specified industries
for(current_industry in industries) {

  # Skip any industry that matches the focus commodity
  if(current_industry == focus_commodity) {
    print(paste0("Skipping industry ", current_industry, " because it matches the focus commodity."))
    next
  }
  
  # Print a message to the console
  print(paste0("Processing industry ", current_industry, "."))

  # Loop through each of the specified year ranges
  for(current_years in year_ranges) {
  
    # Print a message to the console
    print(paste0("Processing year range ", list(current_years), "."))
    
    # Extract the data for the current industry and year range
    data_extract <- data_reshape[(data_reshape$industry == current_industry) &
                                 (data_reshape$year %in% current_years),]
    
    # If there are no observations, skip to the next year range
    if(nrow(data_extract) == 0) {
      print(paste0("Skipping industry ",
                   current_industry,
                   " in year(s) ",
                   list(current_years),
                   " because the industry is not present in that/those year(s)."))
      next
    }
    
    # If an industry does not use a particular commodity in some years,
    # that commodity will have a value of -1 in the dataset for those
    # years; ensure that the focus commodity is used in every year of
    # the current year range
    if(sum(data_extract[,focus_commodity] == -1) > 0) {
      print(paste0("Skipping industry ",
                   current_industry,
                   " in year(s) ",
                   list(current_years),
                   " because of incomplete usage of the focus commodity in that/those year(s)."))
      next
    }
    
    # Create the training dataset by taking the data extract and
    # subtracting the output quantity changes from each column
    # of input quantity changes
    data_train <- data_extract
    data_train <- data_train %>%
      mutate(across("111CA":"Used", ~ .x - quantity_change))
    
    # Count how many -1 values appear in each column of the
    # data extract; these -1 values represent years in which
    # the associated input was not used
    neg_one_counts <- data_extract %>%
      select("111CA":"Used") %>%
      mutate(across(everything(), ~ .x == -1)) %>%
      summarize(across(everything(), sum))
    
    # Create a vector of commodities to use in the prediction by
    # (1) keeping only those without any values of -1; (2) ensuring
    # the focus commodity does not appear; and (3) adding the output
    # quantity change as a predictor column
    cols_for_prediction <- names(neg_one_counts)[as.logical(neg_one_counts == 0)]
    cols_for_prediction <- cols_for_prediction[cols_for_prediction != focus_commodity]
    cols_for_prediction <- c(cols_for_prediction, "quantity_change")
    
    # Train the model, where the dependent variable is the input
    # quantity change for the focus commodity and the predictors
    # are the input quantity changes for the remainder of the
    # commodities (as selected above) as well as the output
    # quantity change; by default, this training will use an
    # objective of 'reg:squarederror'
    model <- train(data_train[,cols_for_prediction],
                   data_train[,focus_commodity],
                   method = 'xgbTree',
                   trControl = fitControl,
                   tuneGrid = grid)
    
    # Add the RMSE for the trained model to the list
    trainPerf <- getTrainPerf(model)
    rmse_list <- c(rmse_list, trainPerf$TrainRMSE)
    
    # Initialize a data frame with (1) the commodities as
    # columns and (2) a single row of zeros
    new_row <- data_extract %>%
      select("111CA":"quantity_change") %>%
      slice_head() %>%
      mutate(across(everything(), ~ 0))
    
    # Using the fitted model, repeatedly predict the difference in
    # quantity change for the focus commodity given a difference in
    # quantity change for each other predictor commodity (as well
    # as a difference in quantity change for the industry-level
    # output quantity index)
    for(test_commodity in cols_for_prediction) {
      
      # Initialize vectors that will hold pairs of test quantity
      # changes (for the current test commodity) and the associated
      # predicted change in the focus commodity
      replaced_val <- c()
      predicted_val <- c()
      
      # Create a row of zeros that represents no input quantity
      # change across all commodities (as well as no output quantity
      # change for the current industry)
      sub_test <- data_extract %>%
        select(all_of(cols_for_prediction)) %>%
        slice_head() %>%
        mutate(across(everything(), ~ 0))
      
      # Loop through the test values
      for(test_value in test_values) {
        
        # Replace the current test commodity's quantity change value
        # with the current test value
        sub_test[1,test_commodity] <- test_value
        
        # Store the test value
        replaced_val <- c(replaced_val, test_value)
        
        # Predict the quantity change for the focus commodity given
        # this test value
        sub_predict <- predict(model, newdata = sub_test)
        
        # Store the predicted value
        predicted_val <- c(predicted_val, sub_predict)
        
      }
        
      # Create a data frame with two columns: the test values for the
      # current test commodity and the associated predicted values for
      # the focus commodity
      plot_vals <- data.frame(replaced_val = replaced_val, predicted_val = predicted_val)
      
      # Regress the predicted values on the test values
      linear_reg <- lm(predicted_val ~ replaced_val, data = plot_vals)
      
      # If the slope coefficient on the replaced values variable
      # is larger than a very small epsilon, use it as the estimate
      # for the current commodity; otherwise, set the estimate to zero,
      # which avoids the presence of very small (non-meaningful) slope
      # values in the results
      if(abs(linear_reg$coefficients[2]) > .Machine$double.eps) {
        coeff <- linear_reg$coefficients[2]
      } else {
        coeff <- 0
      }
      
      # Add the coefficient (or zero) as the entry
      # in the column for the current test commodity
      new_row[1,test_commodity] <- coeff
      
      # Plot the pairs of values for this commodity if the
      # absolute value of the slope is greater than the
      # training RMSE divided by the given value
      # if(abs(linear_reg$coefficients[2]) >= (trainPerf$TrainRMSE / rmse_divisor)) {
      #   plot(plot_vals,
      #        main = paste0("Industry ", current_industry, " and Commodity ", test_commodity))
      # }
      
    }
    
    # Add the completed new row, which has the coefficient values for
    # all of the test commodities (and for the output quantity change)
    # to the results data frame
    coefficient_results <- rbind(coefficient_results, new_row)
    
    # Add the current industry name to the list of industries
    industry_list <- append(industry_list, current_industry)
    
    # Add the current year range to the list of year ranges
    year_range_list <- append(year_range_list, list(current_years))
  
  }
  
}

# Add the industry list as a column in the data frame
coefficient_results$industry <- as.character(industry_list)

# Add the year range list as a column in the data frame
coefficient_results$year_range <- as.character(year_range_list)

# Add the RMSE list as a column in the data frame
coefficient_results$rmse <- rmse_list

# Reorder the columns in the data frame
coefficient_results <- coefficient_results %>%
  select("industry", "year_range", "rmse", everything())




# ***
# Create the categorization results from the coefficient results
# ***

# Create a new data frame to hold the categorization results by
# copying the coefficient results and converting the commodity
# and quantity change columns to string (so that the values for
# complements and substitutes specified above can be accommodated
# whether they are numeric or string)
categorization_results <- coefficient_results
categorization_results <- categorization_results %>%
  mutate(across("111CA":"quantity_change", as.character))

# Replace the values in the categorization results data frame
# with the complements value, the substitutes value, or an
# empty string depending on the whether (1) the slope is positive
# or negative and (2) how large it is (in absolute value)
# compared to the RMSE
for(commodity in c(commodity_list, "quantity_change")) {
  
  # Categorize input pairs as complements if the estimated slope
  # is greater than the RMSE / rmse_divisor
  categorization_results[coefficient_results[,commodity] >=
                           (coefficient_results$rmse / rmse_divisor), commodity] <- complements_value
  
  # Categorize input pairs as substitutes if the estimate slope
  # is less than the - RMSE / rmse_divisor
  categorization_results[coefficient_results[,commodity] <=
                           (-coefficient_results$rmse/ rmse_divisor), commodity] <- substitutes_value
  
  # Categorize input pairs as neither complements nor substitutes
  # if the estimate slope's absolute value is less than the
  # RMSE / rmse_divisor
  categorization_results[abs(coefficient_results[,commodity]) <
                           (coefficient_results$rmse / rmse_divisor), commodity] <- ""
  
}




# ***
# Save the coefficient and categorization results in .csv format
# ***

# Save the coefficient results
write.csv(coefficient_results,
          paste0("./results_data/coefficient_results_r_focus", focus_commodity, ".csv"),
          quote = FALSE,
          row.names = FALSE)

# Save the categorization results
write.csv(categorization_results,
          paste0("./results_data/categorization_results_r_focus", focus_commodity, ".csv"),
          quote = FALSE,
          row.names = FALSE)
