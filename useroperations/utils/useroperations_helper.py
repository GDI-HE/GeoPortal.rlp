import threading
import random
import string

import bcrypt
import requests
from lxml import html
from Geoportal.settings import HOSTNAME, HTTP_OR_SSL, INTERNAL_SSL, MULTILINGUAL, MAX_RESULTS, MAX_API_RESULTS
from Geoportal.utils import utils
from searchCatalogue.utils.searcher import Searcher
from useroperations.models import MbUser
from useroperations.settings import INSPIRE_CATEGORIES, ISO_CATEGORIES
from concurrent.futures import ThreadPoolExecutor, as_completed


def random_string(stringLength=15):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


def __set_tag(dom, tag, attribute, prefix):
    """ Checks the DOM for a special tag and changes the attribute according to the provided value

    Args:
        dom: The document object model
        tag: The tag which we are looking for (e.g. <a>)
        attribute: The attribute that has to be changed
        prefix: The 'https://xyz' prefix of a route
    Returns:
        Nothing, dom is mutable
    """
    protocol = "http"
    searcher = Searcher()
    _list = dom.cssselect(tag)
    for elem in _list:
        attrib = elem.get(attribute)
        if tag == 'a':
            # check if the page we want to go to is an internal or external page
            title = elem.get("title", "").replace(" ", "_")
            if searcher.is_article_internal(title):
                attrib = "/article/" + title
        if protocol not in attrib:
            elem.set(attribute, prefix + attrib)


def set_links_in_dom(dom):
    """ Since the wiki (where the DOM comes from) is currently(!!!) not on the same machine as the Geoportal,
    we need to change all links to the machine where the wiki lives

    Args:
        dom:
    Returns:
    """
    prefix = HTTP_OR_SSL + HOSTNAME

    # handle links
    thread_list = []
    thread_list.append(threading.Thread(target=__set_tag, args=(dom, "a", "href", prefix)))
    thread_list.append(threading.Thread(target=__set_tag, args=(dom, "img", "src", prefix)))
    utils.execute_threads(thread_list)


def get_wiki_body_content(wiki_keyword, lang, category=None):
    """ Returns the HTML body content of the corresponding mediawiki page

    Args:
        wiki_keyword (str): A keyword that matches a mediawiki article title
        lang (str): The currently selected language
        category (str): A filter for internal or external categories
    Returns:
        str: The html content of the wiki article
    """
    # get mediawiki html

    url = HTTP_OR_SSL + '127.0.0.1' + "/mediawiki/index.php/" + wiki_keyword + "#bodyContent"
    html_raw = requests.get(url, verify=INTERNAL_SSL)
    if html_raw.status_code != 200:
        raise FileNotFoundError

    html_con = html.fromstring(html_raw.content)

    # get body html div - due to translation module on mediawiki, we need to fetch the parser output
    try:
        body_con = html_con.cssselect(".mw-parser-output")
        if len(body_con) == 1:
            body_con = body_con[0]
    except KeyError:
        return "Error: Check if mediawiki translation package is installed!"
    except TypeError:
        return "Error: mw-parser-output ist not unique"

    # set correct src/link for all <img> and <a> tags
    set_links_in_dom(body_con)

    # render back to html
    return html.tostring(doc=body_con, method='html', encoding='unicode')

def get_all_data(lang: str):
    """ Returns the landing page content (favourite wmcs)

    Args:
        lang (str): The language for which the data shall be fetched
    Returns:
        A dict containing an overview of how many organizations, topics, wmcs, services and so on are available
    """
    ret_dict = {}
    # get favourite wmcs
    searcher = Searcher(keywords="", result_target="", resource_set=["wmc"], page=1, order_by="date", host=HOSTNAME, max_results=MAX_RESULTS)
    search_results = searcher.search_primary_catalogue_data()
    ret_dict["wmc"] = search_results.get("wmc", {}).get("wmc", {}).get("srv", [])

    # get number of wmc's
    ret_dict["num_wmc"] = search_results.get("wmc", {}).get("wmc", {}).get("md", {}).get("nresults")

    # get number of organizations
    ret_dict["num_orgs"] = len(get_all_organizations())

    # get number of applications
    ret_dict["num_apps"] = len(get_all_applications())

    # get number of topics
    len_inspire = len(get_topics(lang, INSPIRE_CATEGORIES).get("tags", []))
    len_iso = len(get_topics(lang, ISO_CATEGORIES).get("tags", []))
    ret_dict["num_topics"] = len_inspire + len_iso

    # get number of datasets and layers
    tmp = {
        "dataset": "num_dataset",
        "wms": "num_wms",
    }
    for key, val in tmp.items():
        searcher = Searcher(keywords="", result_target="", resource_set=[key], host=HOSTNAME)
        search_results = searcher.search_primary_catalogue_data()
        ret_dict[val] = search_results.get(key, {}).get(key, {}).get("md", {}).get("nresults")

    return ret_dict

def get_landing_page(lang: str, page_num: str, order_by: str = "rank"):
    """ Returns the landing page content (favourite wmcs)

    Args:
        lang (str): The language for which the data shall be fetched
    Returns:
        A dict containing an overview of how many organizations, topics, wmcs, services and so on are available
    """
    # get number of wmc's
    ret_dict = {}
    # get favourite wmcs
    searcher = Searcher(keywords="", result_target="", resource_set=["wmc"], page=page_num, page_res="wmc", order_by=order_by, host=HOSTNAME, max_results=MAX_RESULTS)
    search_results = searcher.search_primary_catalogue_data()
    ret_dict["wmc"] = search_results.get("wmc", {}).get("wmc", {}).get("srv", [])

    # get number of wmc's
    ret_dict["num_wmc"] = search_results.get("wmc", {}).get("wmc", {}).get("md", {}).get("nresults")

    # get number of organizations
    ret_dict["num_orgs"] = len(get_all_organizations())

    # get number of applications
    ret_dict["num_apps"] = len(get_all_applications())

    # get number of topics
    len_inspire = len(get_topics(lang, INSPIRE_CATEGORIES).get("tags", []))
    len_iso = len(get_topics(lang, ISO_CATEGORIES).get("tags", []))
    ret_dict["num_topics"] = len_inspire + len_iso

    # get number of datasets and layers
    tmp = {
        "dataset": "num_dataset",
        "wms": "num_wms",
    }
    for key, val in tmp.items():
        searcher = Searcher(keywords="", result_target="", resource_set=[key], host=HOSTNAME)
        search_results = searcher.search_primary_catalogue_data()
        ret_dict[val] = search_results.get(key, {}).get(key, {}).get("md", {}).get("nresults")

    return ret_dict

def get_all_results(max_results, keywords="", result_target="", resource_set=["wmc"], page_res="wmc", order_by="rank", host=HOSTNAME):
    results = []
    page = 1
    while len(results) < max_results:
        searcher = Searcher(keywords=keywords, result_target=result_target, resource_set=resource_set, page=page, page_res=page_res, order_by=order_by, host=host, max_results=50)
        search_results = searcher.search_primary_catalogue_data()
        new_results = search_results.get("wmc", {}).get("wmc", {}).get("srv", [])
        results.extend(new_results)
        if not new_results:
            # If the new_results is empty, break the loop
            break
        page += 1
    return results[:max_results]

def get_wmc_title(lang: str):
    """ get_titles from views.py calls this function to get the data for searching WMCs in the landing page"""
    # get number of wmc's
    ret_dict = {}
    # get favourite wmcs
    # max_result set to 3000 to get all the results in while searching WMCs. It could be changed to lower value if needed.
    # If set to lower value, the search will show less or no results. Since the maximum 99 results is possible from 
    # API, the results are added to the list until the max_results is reached.
    def fetch_wmc():
        return get_all_results(max_results=MAX_API_RESULTS, keywords="", result_target="", resource_set=["wmc"], page_res="wmc", order_by="rank", host=HOSTNAME)

    def fetch_datasets_and_layers(key, val):
        searcher = Searcher(keywords="", result_target="", resource_set=[key], host=HOSTNAME)
        search_results = searcher.search_primary_catalogue_data()
        return val, search_results.get(key, {}).get(key, {}).get("md", {}).get("nresults")

    tasks = {
        "wmc": fetch_wmc,
        "dataset": lambda: fetch_datasets_and_layers("dataset", "num_dataset"),
        "wms": lambda: fetch_datasets_and_layers("wms", "num_wms"),
    }

    with ThreadPoolExecutor() as executor:
        future_map = {executor.submit(task): name for name, task in tasks.items()}
        for future in as_completed(future_map):
            task_name = future_map[future]
            if task_name in ["dataset", "wms"]:
                key, result = future.result()
                ret_dict[key] = result
            else:
                ret_dict[task_name] = future.result()

    return ret_dict

def get_all_organizations():
    """ Returns a list of all data publishing organizations

    Returns:
         A list of all organizations which publish data
    """
    searcher = Searcher(keywords="", resource_set=["wmc"], page=1, order_by="rank", host=HOSTNAME)

    return searcher.search_all_organizations()


def get_all_applications():
    """ Returns a list of all available applications

    Returns:
         A list of all applications
    """
    searcher = Searcher(keywords="", resource_set=["application"], host=HOSTNAME, max_results=50)
    return searcher.search_primary_catalogue_data().get("application", {}).get("application", {}).get("application", {}).get("srv", [])


def get_topics(language, topic_type: str):
    """ Returns a list of all inspire topics available

    Returns:
         A list of all organizations which publish data
    """
    searcher = Searcher(
        keywords="",
        resource_set=["wmc"],
        page=1,
        order_by="rank",
        host=HOSTNAME
    )

    return searcher.search_topics(language, topic_type)


def bcrypt_password(pw: str, user: MbUser):
    """ Encrypts the given password using a user salt.

    Needed for checking if a given password matches a user's password

    Args:
        pw (str): The given password
        user (MbUser): The MbUser object
    Returns:
         The encrypted password string
    """
    return (str(bcrypt.hashpw(pw.encode('utf-8'), user.password.encode('utf-8')), 'utf-8'))
