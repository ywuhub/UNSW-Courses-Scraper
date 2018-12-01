### UNSW Courses Scraper
### by Yuxing Wu
### Scrape all UNSW courses, term it is offered and campus it is held on and store as CSV format 

# import statements
from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.error import HTTPError
import numpy as np
import pandas as pd
import random
import re
import time

def scrape_courses():
    # class utils page to scrape all UNSW courses
    url = "http://classutil.unsw.edu.au/"
    content = urlopen(url).read()
    soup = BeautifulSoup(content, "html.parser")
    
    table_content = soup.find_all('table')[1]
    row_content = table_content.findChildren(['tr','td'])
    
    # Store the prefix and the corresponding campus of the courses offered there
    href_list = [] # list of links to all course offerings (for all three terms)
    campus = "Unknown Campus" # campus where the courses (prefix) are held
    course_campus = {} # pair campus with the course prefixes 
                       # (i.e. ACCT -> Main Campus, Kensington)
                       # this means that ACCTXXXX courses are held on the main campus
    for row in row_content:
        cells = row.findChildren('td')
        
        for cell in cells:
            cell = str(cell)
            
            if re.search('<td class="cutabhead" colspan="6">(.*)</td>', cell):
                campus = re.search('<td class="cutabhead" colspan="6">(.*)</td>', cell).group(1)
                campus = campus.replace('amp;', '')
            elif re.search('href=\"(.*)\"', cell):
                href = re.search('href=\"(.*)\"', cell).group(1)
                href_list.append(href)
            elif re.search('<td class="data">[A-Z]{4}</td>', cell):
                course_prefix = re.search('<td class="data">([A-Z]{4})</td>', cell).group(1)
                course_campus[course_prefix] = campus
    
    # use the hrefs that links to all course offerings (i.e. offered in summer, term 1, term 2 and/or term 3)
    # create a csv file that stores the subject, subject description, campus, term_offered, times
    course_list = []
    term_offered = []
    on_campus = []
    n_items = len(href_list) # for debuggin purposes only
    for href in href_list:
        href = href.strip()
 
        n_items += -1
        
        # go to next href link if this one is invalid
        if re.search('[A-Z]{4}_S[\d]\.html',href): 
            continue
        
        url = 'http://classutil.unsw.edu.au/' + href
        content = urlopen(url).read()
        soup = BeautifulSoup(content, "html.parser")
    
        title = soup.find_all('p', class_="classSearchMinorHeading")[0].encode_contents(formatter="html")
        title = title.decode('ascii')
        title = title.replace('&nbsp;&nbsp;', ' ')
        term = re.search("Subject Area - .* - (.*)", title).group(1)
        
        table_content = soup.find_all('table')[1]
        row_content = table_content.findChildren(['tr','td'])
        for row in row_content:
            cells = row.findChildren('td')
            
            for cell in cells:
                cell = str(cell.string)
                course = cell.split()[0]
                prefix_code = re.search('^([A-Z]{4})', course).group(1)
                campus = course_campus[prefix_code]
    
                # add to lists for the dataframe
                course_list.append(course)
                term_offered.append(term)
                on_campus.append(campus)
                
        # pause the scraping every 25-35 seconds to stop excessive requests
        timer = random.randint(25,35)
        print('Href: ' + href + ' -> Timer set to:', timer, '-> Items Remaining:', n_items)
        time.sleep(timer) 
    
    # create the course_term_offerings csv file
    raw_data = { 'Course': course_list,
                 'Term_Offered': term_offered,
                 'Campus': on_campus
               }        
    df = pd.DataFrame(raw_data, columns = ['Course', 'Term_Offered', 'Campus'])
    df.to_csv('course_offerings.csv')

def group_data():
    # read the csv file and set the courses as the index
    # group up the index columns and sort in order of the terms (i.e. Summer, Term 1, Term 2 and Term 3 <- Ordered)
    df = pd.read_csv('course_offerings.csv', index_col = 0)
    df = df.sort_values(['Course', 'Term_Offered'], ascending = [True, True])

    # get all unique values of the index in the dataframe
    courses = list(df.index.unique())
    
    # create new sorted file by course and sorted by term the subject is offered in
    term_offerings = []
    on_campus = []
    for course in courses:
        temp_df = df.loc[df.index == course]
        list_offering = ', '.join(temp_df['Term_Offered'])
        list_offering = list_offering.strip()
        campus = temp_df['Campus'].tolist()[0]
        term_offerings.append(list_offering)
        on_campus.append(campus)

    # create the sorted_course_term_offerings csv file
    raw_data = { 'Course': courses,
                 'Term_Offerings': term_offerings,
                 'Campus': on_campus
               }        
    
    df = pd.DataFrame(raw_data, columns = ['Course', 'Term_Offerings', 'Campus'])
    df.to_csv('sorted_course_offerings.csv', index = False)
    
def additional_data():
    # use the sorted course offerings file and add on additional information of columns
    df = pd.read_csv('sorted_course_offerings.csv', index_col = 0)        
    
    # split dataframe into smaller dataframes in order to output smaller CSV files (chunks of the main CSV files)
    dfs = np.array_split(df, 9)
    part = 1
    for df in dfs:
        courses = df.index.tolist()
    
        # fetch the year for the handbook
        handbook_url = 'https://www.handbook.unsw.edu.au'
        content = urlopen(handbook_url).read()
        soup = BeautifulSoup(content, "html.parser")
        year = soup.find_all('h1', class_='t-header__heading h3')[0].text
        year = re.search('Handbook ([\d]{4})', year).group(1)
        
        # debugging purposes only
        n_items = len(courses)
        
        # search for each course and retreive the additional information (i.e course description)
        undergrad_offered = dict.fromkeys(courses, 0) # True(1)/False(0) if the course is offered in undergraduate
        postgrad_offered = dict.fromkeys(courses, 0) # True(1)/False(0) if the course is offered in postgraduate
        prereqs = {}
        course_descr = {}
        uocs = {}
        for course in courses:
            # check if these links exists in the url above and that decides if what career they are offered under
            # career choices: undergraduate course or postgraduate course or course offered in both careers
            undergrad_url = 'http://www.handbook.unsw.edu.au/undergraduate/courses/'+ year + '/' + course + '.html'
            postgrad_url = 'http://www.handbook.unsw.edu.au/postgraduate/courses/'+ year + '/' + course + '.html'
            
            # course url
            url = 'http://timetable.unsw.edu.au/' + year + '/' + course + '.html'
                    
            # debugging purposes only
            n_items += -1
            print ('Current course being processed: ' + course + ' Courses left to process:', n_items)
            
            # try to open the url to check for validity
            try:
                content = urlopen(url).read()
            except HTTPError as error:
                undergrad_offered[course] = 0
                postgrad_offered[course] = 0
                prereqs[course] = "N\A"
                course_descr[course] = "N\A"
                uocs[course] = "N\A"
                continue
                    
            soup = BeautifulSoup(content, "html.parser")
            
            # check if course is offered under the undergraduate and/or postgraduate career
            href_tags = soup.find_all('a', href = True)
            for tag in href_tags:
                if (tag['href'] == undergrad_url):
                    undergrad_offered[course] = 1
                elif (tag['href'] == postgrad_url):
                    postgrad_offered[course] = 1
                    
            # fetch other details (i.e. course description)
            if (undergrad_offered[course] == 1):
                try:
                    content = urlopen(undergrad_url).read()
                except HTTPError as error:
                    prereqs[course] = "N\A"
                    course_descr[course] = "N\A"
                    uocs[course] = "N\A"
                    continue
            elif (postgrad_offered[course] == 1):
                try:
                    content = urlopen(postgrad_url).read()
                except HTTPError as error:
                    prereqs[course] = "N\A"
                    course_descr[course] = "N\A"
                    uocs[course] = "N\A"
                    continue
            else:
                prereqs[course] = "N\A"
                course_descr[course] = "N\A"
                uocs[course] = "N\A"
                continue
                
            soup = BeautifulSoup(content, "html.parser")
            prereq_descr = list(soup.find_all('div', class_ = 'a-card-text m-toggle-text has-focus'))
            course_uoc = list(soup.find_all('h4', class_ = 'no-margin units'))
            
            if (len(course_uoc) > 0):
                uoc = str(course_uoc[0].text).strip()
                uocs[course] = uoc
            else:
                prereqs[course] = "N\A"
                course_descr[course] = "N\A"
                uocs[course] = "N\A"
                continue
                
            # check if they have pre requisites 
            if (len(prereq_descr) == 2):
                description = str(prereq_descr[0].text).strip()
                prereq = str(prereq_descr[1].text).strip()
                
                course_descr[course] = description
                prereqs[course] = prereq
            elif (len(prereq_descr) == 1):
                description = str(prereq_descr[0].text).strip()
                
                course_descr[course] = description
                prereqs[course] = 'No Prerequisites'
     
            # take 10-20 seconds break before next link to reduce load on server
            timer = random.randint(10,20)
            time.sleep(timer)
        
        # create dataframes using the dictionaries create above
        undergrad_df = pd.DataFrame.from_dict(undergrad_offered, orient = 'index', columns = ['undergraduate_offered'])
        postgrad_df = pd.DataFrame.from_dict(postgrad_offered, orient = 'index', columns = ['postgraduate_offered'])  
        descr_df = pd.DataFrame.from_dict(course_descr, orient = 'index', columns = ['course_description'])
        prereqs_df = pd.DataFrame.from_dict(prereqs, orient = 'index', columns = ['pre_requisites'])
        uocs_df = pd.DataFrame.from_dict(uocs, orient = 'index', columns = ['course_uoc'])
        
        # join the dataframes with the main sorted_course_offerings csv with the new data
        temp_df = undergrad_df.join(postgrad_df).join(descr_df).join(prereqs_df).join(uocs_df)
        combined_df = df.merge(temp_df, how = 'inner', left_index = True, right_index = True)
        
        # output as detailed_course_offerings_part.csv
        output_file = 'detailed_course_offerings_' + str(part) + '.csv'
        combined_df.to_csv(output_file, index = True)
        part += 1

def join_data():
    # retrieve the 9 csv files and store into pandas dataframe
    dfs = []
    for part in range(1,10):
        file = 'detailed_course_offerings_' + str(part) + '.csv'
        df = pd.read_csv(file, index_col = 0)
        dfs.append(df)
        
    # concatonate all 9 csv files with partial courses into a complate file with all courses
    df = pd.concat(dfs)
    
    # output as total_course_offerings_part.csv
    output_file = 'total_course_offerings.csv'
    df.to_csv(output_file, index = True)
        
def cleanse_data():
    # fetch the complete course offerings csv file
    df = pd.read_csv('total_course_offerings.csv', index_col = 0)
    
    # clean up the cell values
    df.loc[df.course_description == 'N\A', 'course_description'] = "Description not available"
    df.loc[df.pre_requisites == 'N\A', 'pre_requisites'] = "Prerequisites not available"
    df.loc[df.course_uoc == 'N\A', 'course_uoc'] = "Units of credit not available"

    df.loc[df.undergraduate_offered == 1, 'undergraduate_offered'] = "Yes"
    df.loc[df.undergraduate_offered == 0, 'undergraduate_offered'] = "No"
    
    df.loc[df.postgraduate_offered == 1, 'postgraduate_offered'] = "Yes"
    df.loc[df.postgraduate_offered == 0, 'postgraduate_offered'] = "No"
    
    # clean up column names
    df.columns = ['Offering Terms', 'Campus', 'Undergraduate Course', 'Postgraduate Course', 'Course Description', 'Prerequisites', 'Units of Credit']
    
    # output as clean_total_course_offerings_part.csv
    output_file = 'clean_total_course_offerings.csv'
    df.to_csv(output_file, index = True)
    
if __name__ == "__main__":
    # get information on each individual course and any aditional information if needed
    # retrieve all UNSW courses with minimal information (i.e. Course Name, Term offered in and Campus its held at)
    scrape_courses()
    
    # group up the data (i.e. group up same course names and order by term offerings)
    group_data()
    
    # add additional information to each courses (i.e. units of credit, description of course, prerequisites...)
    additional_data()
    
    # join csv files into one file which will store all the UNSW courses
    join_data()
    
    # cleanse the complete dataset
    cleanse_data()