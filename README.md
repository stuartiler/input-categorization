# Industry Input Categorization and Visualization

This repository contains code to:

1. Import U.S. input-ouput, price index, and quantity index data,
2. Use those data to categorize industries' input pairs as complements or substitutes (or neither),
3. Combine those categorizations with the original input-output data to determine the percentage of industries' inputs categorized as complements, substitutes, or neither, and
4. Visualize those categorization percentages in an interactive data visualization built with [D3.js v7](https://d3js.org/).

A live version of the visualization is available online at [stuartiler.com](https://stuartiler.com/input_categorization).

The first step is accomplished by import_io_data.py, which takes the raw data files in /raw_data/ and processes them into the data files in /processed_data/. All of the raw data files were retrieved from the website of the [U.S. Bureau of Economic Analysis](https://www.bea.gov/).

The second step is performed by categorize_input_pairs.py and categorize_input_pairs.r, which take the processed data files in /processed_data/ and produce the coefficient_results_* and categorization_results_* files in /results_data/. The Python script and the R script implement the same categorization approach.

The third step is performed by combine_categorizations_with_weights.py, which takes the results from the second step and, combined with some of the input-output data from the first step, produces the complement_and_substitute_values_* files in /results_data/.

Lastly, the visualization is composed of three core files:

* input_categorization.html,
* input_categorization.css, and
* input_categorization.js.

The visualization depends on the wide version of the data produced by the third step.