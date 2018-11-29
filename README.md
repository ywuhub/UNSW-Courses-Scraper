# [PYTHON + SAS] UNSW Courses Scraper

# Python
## Scrape all UNSW undergraduate and postgraduate courses that are available in all campuses and display in a csv file with all important variables.

## The program is split into different functions such that each function produces a CSV files and each subsequent function adds onto the CSV files such as adding course details and grouping courses. 

### NOTE: The addtional_data() section will need to be split into several parts for the courses as there are over 4000 courses and thus it will have to be doing something like 500 courses at a time which means we need to split the 'sorted_course_offerings.csv' into several parts and run one at a time. At the end we can join them using SAS 9.4 and clease each dataset as planned.

# SAS 9.4
## The CSV files generated will be cleansed using SAS 9.4 and will be merged together into one CSV files that contains all the course information.
