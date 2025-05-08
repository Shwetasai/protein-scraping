import requests
from bs4 import BeautifulSoup
import json
import time
import string

BASE_URL = "https://currentops.com/"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

def extract_unit_details(unit_url):

    response = requests.get(unit_url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    unit_data = {
        'unit_patch': None,
        'full_unit_name': None,
        'unit_type': None,
        'unit_number': None,
        'location': None,
        'city': None,
        'state': None,
        'country': None,
        'name': None,
        'url': unit_url
    }

    img_tag = soup.select_one('div > img.margin-right-5px')
    if img_tag and img_tag.get('src'):
        unit_data['unit_patch'] = requests.compat.urljoin(BASE_URL, img_tag['src'])

    name_tag = soup.select_one('div > a[title]')
    if name_tag:
        full_name = name_tag.get_text(strip=True)
        unit_data['full_unit_name'] = full_name

        if ' ' in full_name:
            first_space = full_name.find(' ')
            unit_data['unit_number'] = full_name[:first_space]
            unit_data['unit_type'] = full_name[first_space+1:]
        else:
            unit_data['unit_type'] = full_name

    location_tag = soup.select_one('div > i')
    if location_tag:
        loc_text = location_tag.get_text(strip=True)
        unit_data['location'] = loc_text

        parts = [x.strip() for x in loc_text.split(',')]
        if len(parts) == 3:
            unit_data['city'], unit_data['state'], unit_data['country'] = parts
        elif len(parts) == 2:
            unit_data['city'], unit_data['state'] = parts
        elif len(parts) == 1:
            unit_data['state'] = parts[0]

    loc_name_tag = soup.select_one('div > a[title]')
    if loc_name_tag:
        loc_name = loc_name_tag.get_text(strip=True)
        unit_data['name'] = loc_name

    return unit_data


def scrape_components(page_url, parent_id):

    response = requests.get(page_url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    h4_tags = soup.find_all('h4')
    components = []

    for index, h4 in enumerate(h4_tags, start=1):
        name = h4.get_text(strip=True)

        if parent_id:
            comp_id = f"{parent_id}.{index}"
        else:
            comp_id = f"{index}"

        parent_a = h4.find_parent('a')
        link = parent_a['href'] if parent_a and 'href' in parent_a.attrs else None

        if link and not link.startswith('http'):
            link = requests.compat.urljoin(BASE_URL, link)

        component_data = {
            'id': comp_id,
            'name': name,
            'url': link
        }

        if link:
            time.sleep(1)  # be polite
            unit_details = extract_unit_details(link)
            component_data.update(unit_details)

            sub_components = scrape_components(link, comp_id)
            if sub_components:
                component_data['sub_components'] = sub_components

        components.append(component_data)

    return components


def main():
    response = requests.get(BASE_URL, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    units_link = soup.find('a', href="https://currentops.com/units")
    result = []

    if units_link:
        units_li = units_link.find_parent('li')
        dropdown_menu = units_li.find('ul')

        if dropdown_menu:
            country_links = dropdown_menu.find_all('a', href=True)

            for i, a_tag in enumerate(country_links):
                country_letter = string.ascii_uppercase[i] 
                country_name = a_tag.get_text(strip=True)
                country_url = a_tag['href']

                components = scrape_components(country_url, country_letter)

                result.append({
                    'id': country_letter,
                    'country': country_name,
                    'url': country_url,
                    'components': components
                })

                time.sleep(1)
        else:
            print("Dropdown menu not found under Units")
    else:
        print("Units link not found")

    with open('All_data.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print("Saved all components to components.json")


if __name__ == "__main__":
    main()
