/* input_categorization.js
   This file creates a stacked, horizontal bar chart showing
   the complement, substitute, and "other" (uncategorized)
   values produced by combine_categorizations_with_weights.py.
   It requires a .csv file with the values to display and
   assumes the presence of (1) an HTML SVG element to contain
   the visualization and (2) a simple CSS file that specifies
   the text style, the :hover pseudo-classes for the
   buttons and rectangles, and the font weight for the
   industry name in the hover box. */


/* Store a reference to the svg element, set the
   visualization margins, and calculate the width
   and height of the visualization taking account
   of the margins */
var svg = d3.select("svg"),
    margin = {top: 55, right: 20, bottom: 25, left: 100},
    width = +svg.attr("width") - margin.left - margin.right,
    height = +svg.attr("height") - margin.top - margin.bottom;

/* Store the x and y coordinates of the svg element,
   which allows the position of the hover box to be
   adjusted accordingly */
var svgEl = document.querySelector("svg");
var svgRect = svgEl.getBoundingClientRect();
var hover_adjustX = svgRect.x + window.scrollX;
var hover_adjustY = svgRect.y + window.scrollY;

/* Create a group for the buttons and position it
   above the chart area to be created below */
var button_area = svg.append("g")
  .attr("class", "button_area")
  .attr("transform", "translate(" + margin.left + "," + (3/4*margin.top) + ")");

/* Add three rectangles with text to represent the
   buttons; set the click events to re-sort the
   chart depending on which button was pressed */
button_area.append("rect")
  .attr("class", "complements")
  .attr("width", 100)
  .attr("height", 40)
  .attr("transform", "translate(" + (width/4-50) +",-23)")
  .attr("rx", 5)
  .attr("fill", "#e07a5f")
  .attr("opacity", 0.8)
  .on("click", (e,d) => {
    if(sort_by != 'complements') {
      sort_by = 'complements';
      draw_chart();
      button_area.select("rect.complements").attr("fill", "#e07a5f");
      button_area.select("rect.substitutes").attr("fill", "#fff");
      button_area.select("rect.other").attr("fill", "#fff");
    }
  });
button_area.append("text")
  .attr("transform", "translate(" + (width/4) +",0)")
  .attr("text-anchor", "middle")
  .text("Complements");
button_area.append("rect")
  .attr("class", "substitutes")
  .attr("width", 100)
  .attr("height", 40)
  .attr("transform", "translate(" + (width/2-50) +",-23)")
  .attr("rx", 5)
  .attr("fill", "#fff")
  .attr("opacity", 0.8)
  .on("click", (e,d) => {
    if(sort_by != 'substitutes') {
      sort_by = 'substitutes';
      draw_chart();
      button_area.select("rect.complements").attr("fill", "#fff");
      button_area.select("rect.substitutes").attr("fill", "#81b29a");
      button_area.select("rect.other").attr("fill", "#fff");
    }
  });
button_area.append("text")
  .attr("transform", "translate(" + (width/2) +",0)")
  .attr("text-anchor", "middle")
  .text("Substitutes");
button_area.append("rect")
  .attr("class", "other")
  .attr("width", 100)
  .attr("height", 40)
  .attr("transform", "translate(" + (3/4*width-50) +",-23)")
  .attr("rx", 5)
  .attr("fill", "#fff")
  .attr("opacity", 0.8)
  .on("click", (e,d) => {
    if(sort_by != 'other') {
      sort_by = 'other';
      draw_chart();
      button_area.select("rect.complements").attr("fill", "#fff");
      button_area.select("rect.substitutes").attr("fill", "#fff");
      button_area.select("rect.other").attr("fill", "#f4f1de");
    }
  });
button_area.append("text")
  .attr("transform", "translate(" + (3/4*width) +",0)")
  .attr("text-anchor", "middle")
  .text("Uncategorized");

/* Create a group for the visualization and
   set its width and height */
var chart_area = svg.append("g")
  .attr("class", "chart_area")
  .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
  .attr("width", width)
  .attr("height", height);

// Create a group for the vertical axis
var axis_area = svg.append("g")
  .attr("class", "axis")
  .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

/* Create a hover box with a line for the industry
   name and a line for additional detail */
var hover = svg.append("g")
  .attr("class", "hover_area")
  .attr("transform", "translate(50,50)")
  .attr("opacity", 0)
  .style("pointer-events", "none");
hover.append("rect")
  .attr("width", 300)
  .attr("height", 50)
  .attr("fill", "#eee")
  .attr("stroke", "black")
  .attr("rx", 10)
  .attr("ry", 10);
hover.append("text")
  .attr("class", "hover_indname")
  .attr("x", 10)
  .attr("y", 20)
  .text("");
hover.append("text")
  .attr("class", "hover_detail")
  .attr("x", 10)
  .attr("y", 40)
  .text("");

// Create the vertical scale
var y_scale = d3.scaleBand()
    .rangeRound([0, height])
    .paddingInner(0.2);

// Create the horizontal scale
var x_scale = d3.scaleLinear()
    .domain([0, 1])
    .rangeRound([0, width]);

// Create the color scale
var color_scale = d3.scaleOrdinal()
    .domain(['complements', 'substitutes', 'other'])
    .range(["#e07a5f", "#81b29a", "#f4f1de"]);

/* Create a variable that will store which
   key group the mouse pointer is over */
var hover_key = "";

/* Create a variable that will specify which key
   group the bars are being sorted on; initialize
   to sort on the complements values */
var sort_by = "complements";

/* Specify whether the visualization will display
   the upstream or downstream values */
var up_or_down = "upstream";

// Load the data and draw the visualization
var category_data;
d3.csv("./results_data/complement_and_substitute_values_324_wide.csv")
  .then(function(loaded_data) {

    /* Extract either the upstream or downtsream values
       from the dataset */
    category_data = loaded_data.filter(d => d.direction == up_or_down);

    // Draw the visualization
    draw_chart();

});

/* FUNCTION: draw_chart()
   This function uses the upstream or downstream
   complement/substitute values to draw/update
   a sorted, horizontal bar chart */
function draw_chart() {

  /* Create the transition for rearranging the bars
     and the labels when the chart is re-sorted */
  const t = svg.transition().duration(750);

  /* Create the transition for fading back in the
     "other" group, which is made partially transparent
     during the animation so that the other groups
     are easier to see */
  const t2 = svg.transition().duration(1250);

  /* Depending on value of the sort_by variable, set the
     stack order (where 0 is the complements group, 1 is
     the substitutes group, and 2 is the "other" group)
     and re-sort the data */
  var stack_order = [];
  switch(sort_by) {

    case "complements":
      stack_order = [0, 1, 2];
      category_data.sort(function(a, b) { return b.complements - a.complements; });
      break;

    case "substitutes":
      stack_order = [1, 0, 2];
      category_data.sort(function(a, b) { return b.substitutes - a.substitutes; });
      break;

    case "other":
      stack_order = [2, 0, 1];
      category_data.sort(function(a, b) { return b.other - a.other; });
      break;

  }

  /* Set the domain for the vertical scale to be
     the list of industry codes */
  y_scale.domain(category_data.map(function(d) { return d.industry; }));

  /* Create the stack generator using the order
     specified above */
  let stack = d3.stack()
    .keys(['complements', 'substitutes', 'other'])
    .order(stack_order);

  // Generate the stacked data
  let stacked_data = stack(category_data);

  /* Create a group for each of the keys by binding
     the stacked data; reverse the order of the arrays
     in the stacked data because, initially, the sort
     order is complements, substitutes, "other" but the
     animation is easier to see if the "other" group is
     drawn behind the complements and substitutes groups */
  let chart_groups = chart_area.selectAll("g")
    .data([stacked_data[2], stacked_data[1], stacked_data[0]])
    .join(enter => {

        // Create the groups and set their fill colors
        return enter.append("g")
          .attr("fill", function(d) { return color_scale(d.key); })
          .on("mouseover", (e,d) => {

            /* When the mouse is brought over a group, store
               the group name for use below */
            hover_key = d.key;

          });

      },
      update => {

        /* When the bars are animating to their new positions,
           temporarily set the opacity of the "other" group
           to 0.3 to make the complements and substitutes
           groups easier to see */
        return update.attr("opacity", function(d) {
          if (d.key == "other") {
            return 0.3;
          }
          else {
            return 1;
          }
        });

      },
      exit => exit.remove());

  /* Create the bar chart rectangles within each key group;
     identify each rectangle by its associated industry, which
     results in an animation where bars are re-positioned
     (retaining their original size) rather than being re-sized
     in their original position */
  chart_groups.selectAll("rect")
    .data(function(d) { return d; }, d => d.data.industry)
    .join(enter => {

        /* Create the rectangles and set their positions,
           widths, and heights */
        return enter.append("rect")
          .attr("y", function(d) { return y_scale(d.data.industry); })
          .attr("x", function(d) { return x_scale(d[0]); })
          .attr("width", function(d) { return x_scale(d[1]) - x_scale(d[0]); })
          .attr("height", y_scale.bandwidth())
          .on("mousemove", (e,d) => {

            // Update the industry name/code in the hover box
            hover.select(".hover_indname")
              .text(d.data.description + " (" + d.data.industry + ")");

            /* Update the detail line in the hover box, which
               will be set to the complements value, the
               substitutes value, or the "other" value depending
               on the key group the mouse is over (as recorded
               above in the groups' "mouseover" event) */
            switch(hover_key) {

              case "complements":
                hover.select(".hover_detail")
                  .text("% " + up_or_down + " complements: " +
                    Math.round(d.data.complements * 10000)/100 + "%");
                break;

              case "substitutes":
                hover.select(".hover_detail")
                  .text("% " + up_or_down + " substitutes: " +
                    Math.round(d.data.substitutes * 10000)/100 + "%");
                break;

              case "other":
                hover.select(".hover_detail")
                  .text("% " + up_or_down + " uncategorized: " +
                    Math.round(d.data.other * 10000)/100 + "%");
                break;

            }

            /* Set the hover box's width depending on which of
               the two lines in the box is longest */
            hover.select("rect").attr("width",
              Math.max(calculate_text_width(hover.select(".hover_indname").text()),
                       calculate_text_width(hover.select(".hover_detail").text()))
              + 20);

            /* Retrieve the mouse coordinates and calculate the
               hover box's x and y coordinates so that the box
               does not go outside of the svg container */
            var coords = d3.pointer(e, svg);
            var box_x = Math.min(coords[0] - hover_adjustX + 10,
              svg.attr("width") - hover.select("rect").attr("width") - 10);
            var box_y = Math.min(coords[1] - hover_adjustY + 10,
              svg.attr("height") - hover.select("rect").attr("height") - 10);

            /* Set the new position of the hover box and make
               it visible */
            hover.attr("transform", "translate(" + box_x + "," + box_y + ")")
              .attr("opacity", 0.9);

          })
          .on("mouseout", (e,d) => {

            /* If the mouse goes outside of the rectangle,
               make the hover box invisible */
            hover.attr("opacity", 0);

          });

      },
      update => {

        // Update the positions and widths of the rectangles
        return update.transition(t)
          .attr("y", function(d) { return y_scale(d.data.industry); })
          .attr("x", function(d) { return x_scale(d[0]); })
          .attr("width", function(d) { return x_scale(d[1]) - x_scale(d[0]); });

      },
      exit => exit.remove());

  // Create/update the vertical axis using the vertical scale
  axis_area
    .transition(t)
    .call(d3.axisLeft(y_scale));

  // Make the domain invisible by setting its color to white
  axis_area.select(".domain")
    .style("stroke", "white");

  /* Fade the key groups' opacity back to 1, which will
     only impact the "other" group as the complements
     and substitutes groups will already have opacity
     of 1 (see above) */
  chart_area.selectAll("g").transition(t2)
    .attr("opacity", 1);

}

/* FUNCTION: calculate_text_width(text)
   This function takes a string and returns the width of
   the rendered text in pixels; note that the function
   assumes the relevant font is whatever the font of the
   hover box's industry name text element is; thanks to
   poster Domi on Stack Overflow for outlining this method
*/
function calculate_text_width(text) {

  // Create a canvas element if one does not already exist
  const canvas = calculate_text_width.canvas ||
    (calculate_text_width.canvas = document.createElement("canvas"));

  // Get the context
  const context = canvas.getContext("2d");

  /* Set the font to the current font of the hover box's
     industry name text element */
  context.font = window
    .getComputedStyle(document.querySelector(".hover_indname"), null)
    .getPropertyValue("font");

  // Use the context's measureText function on the given text
  const metrics = context.measureText(text);

  // Return the width
  return metrics.width;

}
