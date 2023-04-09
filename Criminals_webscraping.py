import requests
from bs4 import BeautifulSoup
import csv

base_url = "https://www.police.hu"
response = requests.get(f"{base_url}""/hu/koral/toplistas-korozesek")
soup = BeautifulSoup(response.text, "html.parser")
wanted = soup.find_all("div", class_="image-container")  # wanted persons on Körözési Toplista page

profiles = []
result = []
res_wanted_list = []


for w in wanted:
    wanted_profile = w.find("a")["href"]  # each person has a linked profile for detailed information
    profiles.append(wanted_profile)  # collecting sub-path of individual profiles


def profiles_info(data):

    for profile in profiles:
        sub_url = base_url + profile  # creating a callable URL path for a profile
        sub_response = requests.get(sub_url)
        sub_soup = BeautifulSoup(sub_response.text, "html.parser")
        persons = sub_soup.find_all("div", class_="line left float-none")
        crime_section = sub_soup.find_all("div", class_="line float-none left")
        content = sub_soup.select("div[class = 'line']")  # parent section which also includes reward information
        properties = sub_soup.find_all("div", class_="properties")  # dangerous, gunman

        res = personal_info(persons, crime_section, content, properties)
        res_wanted_list.append(res)

    return res_wanted_list


def personal_info(persons, crime_section, content, properties):
    persons_list = []
    wanted_list = []
    unique_crimes = []
    properties_list = []

    for p in persons:
        p_label = p.find("label")
        p_label.extract()

        person = p.get_text()    # getting name, gender, nationality, dob, birth place
        persons_list.append(person)

    for c in crime_section:
        try:
            anchor = c.find("a", recursive=False)
            crimes = anchor.text
            unique_crimes.append(crimes) if crimes not in unique_crimes else None   # the list of crime(s) is linked to other criminals who committed the same crimes, so there are duplicates.

        except AttributeError:   # the criminal has been caught, his profile already exists, but personal information is no longer available
            continue

    reward = content[0].text.replace("\t", "").replace("\n", "").replace("Ft", "").replace(".", "") if content != [] else 0   # not all criminals are affected



    for property in properties:
        try:
            dangerous = property.find("div", class_="dangerous").get("title")
            gunman = property.find("div", class_="gunman").get("title")

        except AttributeError:   # not all criminals are classified
                                 # the criminal has been caught, his profile already exists, but personal information is no longer available
            continue

        properties_list.append(dangerous)
        properties_list.append(gunman)

    persons_list.append(unique_crimes)
    persons_list.append(reward)
    persons_list.append(properties_list)
    wanted_list.append(persons_list)

    return persons_list


result = profiles_info(profiles)


columns = ["Nev", "Nem", "Szuletesi hely", "Szuletesi datum", "Allampolgarsag", "Korozes", "Nyomravezetoi dij", "Jelzo"]

with open("Korozesi_toplista.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file, delimiter=";")
    writer.writerow(columns)
    for entity in result:
        try:
            name, gender, place, dob, nationality, crimes, reward, properties = entity
            for crime in crimes:  ## some criminals committed multiple crimes
                row = [name, gender, place, dob, nationality, crime, reward]
                writer.writerow(row)

            if properties:
                for prop in properties:   ## some criminals have multiple classifiers
                    row = [name, gender, place, dob, nationality, "", reward, prop]
                    writer.writerow(row)
        except ValueError:
            continue
