import hashlib
import logging
import re
import smtplib
import datetime
import time
import urllib.parse
from collections import OrderedDict
from pprint import pprint
from urllib import error
from lxml import html

import bcrypt
import requests
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _
from django.contrib.auth.password_validation import validate_password, UserAttributeSimilarityValidator
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.core.mail import EmailMessage   # this could be changed to old style which is used in register_view
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_text
from django.core.paginator import Paginator
from datetime import date
# from thefuzz import fuzz     ## also include the fuzz in the requirements.txt if fuzz is needed in WMC search
from django.core.cache import cache
from functools import wraps

from Geoportal.decorator import check_browser
from Geoportal.geoportalObjects import GeoportalJsonResponse, GeoportalContext
from Geoportal.settings import DEFAULT_GUI, HOSTNAME, HTTP_OR_SSL, INTERNAL_SSL, \
    SESSION_NAME, PROJECT_DIR, MULTILINGUAL, LANGUAGE_CODE, DEFAULT_FROM_EMAIL, GOOGLE_RECAPTCHA_SECRET_KEY, \
    USE_RECAPTCHA, GOOGLE_RECAPTCHA_PUBLIC_KEY, DEFAULT_TO_EMAIL, MOBILE_WMC_ID, SHOW_SEARCH_CONTAINER, SHOW_PAGING, MAX_RESULTS, NO_OF_DAYS
from Geoportal.utils import utils, php_session_data, mbConfReader
from searchCatalogue.utils.url_conf import URL_INSPIRE_DOC
from searchCatalogue.settings import PROXIES
from useroperations.settings import LISTED_VIEW_AS_DEFAULT, ORDER_BY_DEFAULT, INSPIRE_CATEGORIES, ISO_CATEGORIES
from useroperations.utils import useroperations_helper
from .forms import RegistrationForm, LoginForm, PasswordResetForm, ChangeProfileForm, DeleteProfileForm, FeedbackForm, PasswordResetConfirmForm
from .models import MbUser, MbGroup, MbUserMbGroup, MbRole, GuiMbUser, MbProxyLog, Wfs, Wms

logger = logging.getLogger(__name__)

def prioritize_top_news(parsed_data):
    """
    Prioritizes "topNews" items based on their repair start dates and durations.

    This function calculates the repair start date for each "topNews" item by adding
    its duration to the specified date. It then sorts the items based on the number
    of days until the repair start date, in ascending order. Items with repair dates
    that have already passed are filtered out.

    Additionally, if multiple "topNews" items have the same title and date, the latest entry
    will be prioritized at the top of the list.

    Args:
        parsed_data (list of dict): A list of "topNews" items, each represented as a dictionary
            with keys "title," "date," "duration," "teaser," and "article_body."

    Returns:
        list of dict: A sorted and filtered list of "topNews" items, prioritized by their repair dates.

    """
    
    # Get today's date
    today = datetime.date.today()

    # Define a custom sorting function
    def custom_sort(item):
        # Parse the date into a format that can be compared
        date_parts = item["date"].split(".")
        parsed_date = datetime.date(int(date_parts[2]), int(date_parts[1]), int(date_parts[0]))

        # Calculate the repair start date based on duration
        if item["duration"]:
            repair_start_date = parsed_date + datetime.timedelta(days=int(item["duration"]))
        else:
            repair_start_date = parsed_date

        # Calculate the difference in days between today and the repair start date
        days_until_repair = (repair_start_date - today).days

        # Sort by days until repair (ascending)
        return days_until_repair

    # Sort the parsed data using the custom sorting function
    try:
        sorted_data = sorted(parsed_data, key=custom_sort)

        # Filter out "topNews" items with repair dates that have already passed
        sorted_data = [item for item in sorted_data if custom_sort(item) >= 0]
        return sorted_data
    except:
        pass

def extract_element(parent, selector):
    try:
        return parent.cssselect(selector)[0]
    except IndexError:
        return None
    
def extract_text_content(element):
    try:
        return element.text_content().strip()
    except AttributeError:
        return ""

def extract_text(element):
    try:
        return element.text.strip()
    except AttributeError:
        return None    

def parse_wiki_data():
    """
    Parse the "Meldungen" page on the wiki and return the prioritized top news, along with a URL
    to see more details if available.

    Args:
        request: The HTTP request object (not explicitly used in this function).

    Returns:
        tuple: A tuple containing two elements:
            - A list of prioritized top news items, each represented as a dictionary with keys
              "title," "date," "duration," "teaser," and "article_body."
            - A URL to see more details about the top news on the wiki page, or an empty string if
              there are no top news items.

    This function performs the following steps:
    1. Constructs the URL for the Wikimedia API endpoint.
    2. Sends a request to the API to parse the "Meldungen" page.
       A t t e n t i o n !: prerequisites in Mediawiki - special template is needed!
                            The documentation can be found in Geoportal.rlp/documentation/requirement_topnews_parser.md
    3. Parses the JSON response to extract the HTML content.
    4. Extracts information from HTML elements within "topNews" divs, including title, date,
       duration, teaser, and article body.
    5. Prioritizes the top news items based on repair start dates and durations.
    6. Generates a URL to see more details about the top news item, adapted for MediaWiki encoding.
    7. Returns the prioritized top news and the see more URL.
    """
    # Define the URL of your Wikimedia API endpoint
    api_url = "http://localhost/mediawiki/api.php"

    # Define parameters for the API request to parse the "Meldungen" page
    params = {
        "action": "parse",
        "format": "json",
        "page": "Meldungen",  
        "formatversion": 2
    }

    response = requests.get(api_url, params=params)
    parsed_data = []

    # Check if the API request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        parsed_content = data["parse"]["text"]

        # Parse the HTML content (in 'parsed_content') and create an HTML tree structure for further processing.
        html_tree = html.fromstring(parsed_content)
        
        # Find all div elements with class="topNews" 
        top_news_elements = html_tree.cssselect("div.topNews")
        
        for top_news in top_news_elements:
            title_element = extract_element(top_news, "h2.topNewsTitle")
            date_element = extract_element(top_news, "span.topNewsDate strong")
            duration_element = extract_element(top_news, "span.hiddenDuration")
            teaser_element = extract_element(top_news, "p.teaser")
            article_body_element = extract_element(top_news, "p.articleBody")


            title = extract_text_content(title_element)
            date = extract_text(date_element)
            if date is None:
                continue
            duration = extract_text(duration_element)
            teaser = extract_text_content(teaser_element)
            article_body = extract_text_content(article_body_element)

            # Append the parsed data to the list
            parsed_data.append({
                "title": title,
                "date": date,
                "duration": duration,
                "teaser": teaser,
                "article_body": article_body
            })

    # Call the function to prioritize the "topNews" elements based on repair start date
    prioritized_top_news = prioritize_top_news(parsed_data)
    # If there are prioritized top news items, select the first item
    if prioritized_top_news:
        top_news =[prioritized_top_news[0]] 
        one_news = prioritized_top_news[0]
        #remove all white spaces (if there is whitespaces we cannot see it in mediawiki id and in the page, but the parsed_content will have white spaces)
        cleaned_top_news = re.sub(r'\s+', ' ', one_news["title"])  
        encoded_title = urllib.parse.quote(cleaned_top_news, safe='')
        # Adapt the encoded_title for compatibility with MediaWiki encoding:
        # - Replace '%20' with underscores ('_')
        # - Replace '%' with periods ('.')
        encoded_title = encoded_title.replace("%20", "_")
        encoded_title = encoded_title.replace("%", ".")  
        see_more_url = f'{HTTP_OR_SSL}{HOSTNAME}/article/Meldungen/#{encoded_title}' #see_more_url for the link to the wiki page
    else:
        top_news = []
        see_more_url = ""
    return top_news, see_more_url


# might be good to move this to a separate file
class CustomTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        login_timestamp = '' if user.mb_user_password_ticket == '' else datetime.datetime.fromtimestamp(int(user.mb_user_password_ticket)).strftime('%Y%m%d%H%M%S')
        return (
            str(user.pk) + str(timestamp) +
            str(user.password) + login_timestamp
        )

custom_token_generator = CustomTokenGenerator()

@check_browser
def index_view(request, wiki_keyword=""):
    """ Prepares the index view, and renders the page.

    This view is the main view and landing page of the project.
    It includes checking if a mediawiki page should be rendered or not.
    The default page, if no keyword was given, is landing_page.html,
     which shows an overview of the most popular wmc services.


    Args:
        request: HTTP request coming from djangos URLconf.
        wiki_keyword: If a string is present it will be used to render
         a mediawiki page transparently to the user.
        HTTPGet('status'): Checks if the login was successful or not.
         'status' comes from a mapbender php script(authentication.php)

    Returns:
        view: returns the rendered view, which can be:
         (default): landing_page.html
         (wiki): a mediawiki page
         (viewer): geoportal.html
         (error): 404.html
    """

    request.session["current_page"] = "index"
    if MULTILINGUAL:
        lang = request.LANGUAGE_CODE
    else:
        lang = LANGUAGE_CODE
    get_params = request.GET.dict()
    dsgvo_list = ["Datenschutz", "Kontakt", "Impressum", "Rechtshinweis", "Transparenzgesetz"]

    output = ""
    results = []

    # In a first run, we check if the mapbender login has worked, which is indicated by a 'status' GET parameter.
    # Since this is not nice to have in your address bar, we exchange the GET parameter with a pretty message for the user
    # and reload the same route simply again to get rid of the GET parameter.
    if request.method == 'GET' and 'status' in request.GET:
        if request.GET['status'] == "fail":
            messages.error(request, _("Login failed"))
            return redirect('useroperations:login')
        elif request.GET['status'] == "success":
            messages.success(request, _("Successfully logged in"))
            return redirect('useroperations:index')
        elif request.GET['status'] == "notactive":
            messages.error(request, _("Account not active, please check your emails to reactivate!"))
            return redirect('useroperations:index')
        elif request.GET['status'] == "fail3":
            user = MbUser.objects.get(mb_user_name=request.GET['name'])
            messages.error(request, _("Password failed too many times! Account is deactivated! Activation mail was sent to you!"))
            try:

                send_mail(
                    _("Activation Mail"),
                    _("Hello ") + request.GET['name'] +
                    ", \n \n" +
                    _("Your account has been deactivated because of too many failed password inputs! You can reactivate with the following link.")
                    + "\n Link: " + HTTP_OR_SSL + HOSTNAME + "/activate/" + user.activation_key,
                    DEFAULT_FROM_EMAIL,
                    [user.mb_user_email],
                    fail_silently=False,
                )
            except smtplib.SMTPException:
                logger.error("Could not send activation mail!")
                messages.error(request, _("An error occured during sending. Please inform an administrator."))

            return redirect('useroperations:index')


    geoportal_context = GeoportalContext(request)
    top_news, see_more_url = parse_wiki_data()
    context_data = geoportal_context.get_context()
    if context_data['dsgvo'] == 'no' and context_data['loggedin'] == True and wiki_keyword not in dsgvo_list:
        return redirect('useroperations:change_profile')

    if wiki_keyword == "viewer":
        template = "geoportal.html"
    elif wiki_keyword != "":
        # display the wiki article in the template
        template = "wiki.html"
        try:
            output = useroperations_helper.get_wiki_body_content(wiki_keyword, lang)
            request.session["current_page"] = wiki_keyword
        except (error.HTTPError, FileNotFoundError) as e:
            template = "404.html"
            output = ""
    else:
        # display the favourite WMCs in the template
        template = "landing_page.html"
        # Default to '1' if no page number is provided also it is not necessary here. Just used not to get error
        # if the page number is not provided, since get_landing_page function needs it.
        page_num = request.session.get("page_num", 1) 
        results = useroperations_helper.get_landing_page(lang, page_num)

    context = {
               "wiki_keyword": wiki_keyword,
               "content": output,
               "results": results,
               "mobile_wmc_id": MOBILE_WMC_ID,
               "see_more_url": see_more_url,
               "top_news": top_news,
               "show_search_container": SHOW_SEARCH_CONTAINER,
               "show_paging": SHOW_PAGING,
               "max_results": MAX_RESULTS
               }
    geoportal_context.add_context(context=context)

    # check if this is an ajax call from info search
    if get_params.get("info_search", "") == 'true':
        category = get_params.get("category", "")
        output = useroperations_helper.get_wiki_body_content(wiki_keyword, lang, category)
        return GeoportalJsonResponse(html=output).get_response()
    else:
        return render(request, template, geoportal_context.get_context())
    
def rate_limit(limit=5, period=10):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            client_ip = request.META.get('REMOTE_ADDR')
            cache_key = f"rate_limit_{client_ip}"
            requests = cache.get(cache_key, [])
            
            # Filter out requests outside the current period
            current_time = time.time()
            requests = [req for req in requests if current_time - req < period]
            
            if len(requests) >= limit:
                return JsonResponse({"error": "Rate limit exceeded"}, status=429)
            
            requests.append(current_time)
            cache.set(cache_key, requests, timeout=period)
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

def parse_date(date_str):
    # Cache parsed dates to avoid re-parsing
    if date_str in parse_date.cache:
        return parse_date.cache[date_str]
    parsed_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
    parse_date.cache[date_str] = parsed_date
    return parsed_date
parse_date.cache = {}

@rate_limit(limit=5, period=10)  # Allow 5 requests per 10 seconds  
def landing_page_view(request):
    """ It render the WMC (according to the number given in MAX_RESULTS in settings.py) on the landing page according to the request from the user in the landing page.
    The user can choose the WMC rankwise and datewise. The num_wmc helps to create a pagination and new_wmcs helps to 
    mark the top 3 new WMCs which are not older than 15 days as new. """
    lang = request.GET.get('lang', 'en')  # Default to 'en' if no language is provided
    page_num = request.GET.get('page_num', '1')  # Default to '1' if no page number is provided
    sort_by = request.GET.get('sort_by', 'rank')
    # Check if all_data is cached
    all_data_cache_key = f"all_data_{lang}"
    all_data = cache.get(all_data_cache_key)
    if not all_data:
        all_data = useroperations_helper.get_all_data(lang)
        cache.set(all_data_cache_key, all_data, 600)  # since the number of viewers will not be updated if cached for 12 hours, the timeout is reduced to 10 minutes

    # Check if latest_wmc_date is cached
    latest_wmc_date_cache_key = f"latest_wmc_date_{lang}"
    latest_wmc_date = cache.get(latest_wmc_date_cache_key)
    if not latest_wmc_date:
        wmcs = all_data.get('wmc', [])
        if wmcs:
            latest_wmc_date = max(wmcs, key=lambda w: parse_date(w.get('date', '01.01.1990'))).get('date', '01.01.1990')
        else:
            latest_wmc_date = "01.01.1990"
        cache.set(latest_wmc_date_cache_key, latest_wmc_date, 600)  # Cache for 10 minutes
        
    cache_key = f"landing_page_{lang}_{page_num}_{sort_by}_{latest_wmc_date}"
    cached_response = cache.get(cache_key)
    if cached_response:
        return JsonResponse(cached_response)

    # If not cached, proceed with generating the response
    request.session["page_num"] = int(page_num)
    page_num = int(page_num)
    results = useroperations_helper.get_landing_page(lang, page_num, sort_by)
    all_data = useroperations_helper.get_all_data(lang)
    wmcs = all_data.get('wmc', [])
    results_num = results.get("num_wmc", 0)
    new_wmcs = [wmc for wmc in wmcs if sort_wmc(wmc) <= NO_OF_DAYS]
    new_wmcs = sorted(new_wmcs, key=sort_wmc)[:3]
    html = render_to_string('tile_wmc.html', {'results': results, 'num_wmc': results_num, 'new_wmcs': new_wmcs, 'show_search_container': SHOW_SEARCH_CONTAINER, 'max_results': MAX_RESULTS})

    # Cache the generated response
    response_data = {"html": html, "num_wmc": results_num, 'new_wmcs': new_wmcs, 'max_results': MAX_RESULTS}
    # store the cache until the latest wmc date changes, default is 5 minutes
    cache.set(cache_key, response_data, None)  

    return JsonResponse(response_data)


# Sorting function for getting the new wmcs
def sort_wmc(wmc):
    date_parts = wmc.get('date', '01.01.1990').split(".")
    parsed_date = date(int(date_parts[2]), int(date_parts[1]), int(date_parts[0]))
    today = date.today()
    days_since_wmc = (today - parsed_date).days
    return days_since_wmc

def get_titles(request):
    """This is only used for the search function in the landing page with query now and return the matching wmcs."""
    lang = request.GET.get('lang', 'en')
    page_num = request.GET.get('page_num', 1)
    query = request.GET.get('query', '')

    # Proceed if no cached response
    results = useroperations_helper.get_wmc_title(lang)
    wmcs = results.get('wmc', [])
    matching_wmcs = [wmc for wmc in wmcs if query.lower() in wmc.get('title', '').lower() or query.lower() in wmc.get('abstract', '').lower()]
    # remove the comment if fuzz needs to be used and pip install thefuzz
    # matching_wmcs = [wmc for wmc in wmcs if fuzz.partial_ratio(query.lower(), wmc.get('title', '').lower()) > 70 or fuzz.partial_ratio(query.lower(), wmc.get('abstract', '').lower()) > 70]
    # Create a Django Paginator
    paginator = Paginator(matching_wmcs, 5)  # Show 5 results per page
    # Get the requested page of results
    page = paginator.get_page(page_num)
    results_num = results.get('num_wmc', 0)
    new_wmcs = [wmc for wmc in wmcs if sort_wmc(wmc) <= NO_OF_DAYS]
    new_wmcs = sorted(new_wmcs, key=sort_wmc)[:3]

    context = {
        'results': {
            'wmc': page,
            
        },
        'num_wmc': results_num,
        'new_wmcs': new_wmcs,
        'max_results': MAX_RESULTS,
        }
    html = render_to_string('tile_wmc.html', context)
    titles = [wmc.get('title') for wmc in page]

    response_data = {
        "html": html,
        "titles": titles,
        "has_previous": page.has_previous(),
        "previous_page_number": page.previous_page_number() if page.has_previous() else None,
        "has_next": page.has_next(),
        "next_page_number": page.next_page_number() if page.has_next() else None,
        "new_wmcs": [wmc.get('title') for wmc in new_wmcs],
        "max_results": MAX_RESULTS
    }

    return JsonResponse(response_data)

@check_browser
def applications_view(request: HttpRequest):
    """ Renders the view for showing all available applications

    Args:
        request: The incoming request
    Returns:
         A rendered view
    """
    request.session["current_page"] = "apps"

    geoportal_context = GeoportalContext(request)
    
    order_by_options = OrderedDict()
    order_by_options["rank"] = _("Relevance")
    order_by_options["title"] = _("Alphabetically")

    apps = useroperations_helper.get_all_applications()
    params = {
        "apps": apps,
        "order_by_options": order_by_options,
        "ORDER_BY_DEFAULT": ORDER_BY_DEFAULT,
        "LISTED_VIEW_AS_DEFAULT": LISTED_VIEW_AS_DEFAULT,
    }
    template = "applications.html"
    geoportal_context.add_context(params)
    return render(request, template, geoportal_context.get_context())


@check_browser
def organizations_view(request: HttpRequest):
    """ Renders the view for showing all participating organizations

    Args:
        request: The incoming request
    Returns:
         A rendered view
    """

    geoportal_context = GeoportalContext(request)
    context_data = geoportal_context.get_context()
    if context_data['dsgvo'] == 'no' and context_data['loggedin'] == True:
        return redirect('useroperations:change_profile')

    template = "publishing_organizations.html"
    geoportal_context = GeoportalContext(request)
    order_by_options = OrderedDict()
    order_by_options["rank"] = _("Relevance")
    order_by_options["title"] = _("Alphabetically")

    context = {
        "organizations": useroperations_helper.get_all_organizations(),
        "order_by_options": order_by_options,
        "ORDER_BY_DEFAULT": ORDER_BY_DEFAULT,
        "LISTED_VIEW_AS_DEFAULT": LISTED_VIEW_AS_DEFAULT,
    }
    geoportal_context.add_context(context)
    return render(request, template, geoportal_context.get_context())


@check_browser
def categories_view(request: HttpRequest):
    """ Renders the view for showing all available categories

    Args:
        request: The incoming request
    Returns:
         A rendered view
    """

    geoportal_context = GeoportalContext(request)
    context_data = geoportal_context.get_context()
    if context_data['dsgvo'] == 'no' and context_data['loggedin'] == True:
        return redirect('useroperations:change_profile')

    order_by_options = OrderedDict()
    order_by_options["rank"] = _("Relevance")
    order_by_options["title"] = _("Alphabetically")

    template = "topics.html"

    topics = []
    inspire_topics = useroperations_helper.get_topics(request.LANGUAGE_CODE, INSPIRE_CATEGORIES)
    iso_topics = useroperations_helper.get_topics(request.LANGUAGE_CODE, ISO_CATEGORIES)
    topics += inspire_topics.get("tags", []) + iso_topics.get("tags", [])

    context = {
        "topics": topics,
        "inspire_doc_uri": URL_INSPIRE_DOC,
        "order_by_options": order_by_options,
        "ORDER_BY_DEFAULT": ORDER_BY_DEFAULT,
        "LISTED_VIEW_AS_DEFAULT": LISTED_VIEW_AS_DEFAULT,
    }
    geoportal_context.add_context(context)
    return render(request, template, geoportal_context.get_context())


@check_browser
def login_view(request):
    """ View that handles the login

    Login is handled by a mapbender php script(authentication.php),
    this view just takes credentials and forwards it to the script.
    The script returns a status message to the index view.

    Args:
        request: HTTPRequest

    Returns:
        The login page
    """
    request.session["current_page"] = "login"
    form = LoginForm()
    btn_label_pw = _("Forgot Password?")
    btn_label_login = _("Login")
    geoportal_context = GeoportalContext(request=request)
    context = {
        'form': form,
        "btn_label_pw": btn_label_pw,
        "btn_label_login": btn_label_login,
        'headline': _("Login"),
    }
    geoportal_context.add_context(context)
    # The mb_user_password_ticket is set to null or empty string, if the user login successful,
    # in order to make the password forgot token link invalid. Since the user has logged in, he doesn't need it anymore.
    # If the user is blocked from the Forgot password (after 1 attempt), after login he can again use forget password to reset his password.
    # But if not logged in, he has to wait 24 hours to use the forget password. Or he has to change the password, and the mb_user_password_ticket will again set to current time - 86400 allowing him to use the forget password.
    # Since the authenication is done in php (authentication.php:61), change the code in the php script to set the mb_user_password_ticket to null or empty string after successful login.

    return render(request, "crispy_form_auth.html", geoportal_context.get_context())


@check_browser
def register_view(request):
    """ View for user registration.

    On HTTPGet it renders the registration Form in forms.py.
    On HTTPPost it checks if the username is taken and validates password specification.
    It uses pythons hashlib.pbkdf2_hmac for password storage.
    Further it tries to read the mapbender.conf to get the id of the admin user.

    Args:
        request: HTTPRequest

    Returns:
        RegistrationForm

    """
    request.session["current_page"] = "register"
    btn_label = _("Registration")
    small_labels = [
        "id_newsletter",
        "id_survey",
        "id_dsgvo",
    ]
    form = RegistrationForm()
    geoportal_context = GeoportalContext(request=request)
    disclaimer = _("Personal data will not be transmitted to other parties or services. "
                   "Further information can be found in our ")
    context = {
        'form': form,
        'headline': _("Registration"),
        "btn_label1": btn_label,
        "small_labels": small_labels,
        "disclaimer": disclaimer,
        "use_recaptcha": USE_RECAPTCHA,
        "recaptcha_public_key": GOOGLE_RECAPTCHA_PUBLIC_KEY,
        "register": 1,
    }

    geoportal_context.add_context(context)

    context_data = geoportal_context.get_context()
    if context_data['loggedin'] == True:
        messages.error(request, _("Log out to register a new user"))
        return redirect('useroperations:index')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():

            if USE_RECAPTCHA == 1:
                recaptcha_response = request.POST.get('g-recaptcha-response')
                data = {
                    'secret': GOOGLE_RECAPTCHA_SECRET_KEY,
                    'response': recaptcha_response
                }
                r = requests.post('https://www.google.com/recaptcha/api/siteverify', proxies=PROXIES, data=data)
                result = r.json()

                if not result['success']:
                    messages.error(request, _("Invalid reCAPTCHA. Please try again."))
                    return redirect('useroperations:register')

            #bot honeypot field
            if form.cleaned_data['identity'] != "":
                form.cleaned_data['identity'] = ''
                return render(request, 'crispy_form_no_action.html', {'form': form})

            if MbUser.objects.filter(mb_user_name=form.cleaned_data['name']).exists():
                messages.error(request, _("The Username") + " {str_name} ".format(str_name=form.cleaned_data['name']) + _("is already taken"))
                context = geoportal_context.get_context()
                context['form'] = form  # Add form to context
                context['focus_username'] = True
                return render(request, 'crispy_form_no_action.html', context)

            try:
                validate_password(form.cleaned_data['password'])
            except ValidationError as e:
                error_messages = ', '.join(e.messages)
                messages.error(request, error_messages)
                context = geoportal_context.get_context()
                context['form'] = form
                context['focus_password'] = True 
                return render(request, 'crispy_form_no_action.html', context)
            
            validator = UserAttributeSimilarityValidator(user_attributes=['mb_user_name'])
            user = MbUser(mb_user_name=form.cleaned_data['name'], mb_user_email=form.cleaned_data['email'])  # temporary user instance
            try:
                validator.validate(form.cleaned_data['password'], user)
            except ValidationError:
                messages.error(request, _("Your password can't be too similar to your username."))
                context = geoportal_context.get_context()
                context['form'] = form
                context['focus_password'] = True 
                return render(request, 'crispy_form_no_action.html', context)
            

            user = MbUser()
            user.mb_user_name = form.cleaned_data['name']
            user.mb_user_email = form.cleaned_data['email']
            user.mb_user_department = form.cleaned_data['department']
            user.mb_user_description = form.cleaned_data['description']
            user.mb_user_phone = form.cleaned_data['phone']
            user.mb_user_organisation_name = form.cleaned_data['organization']
            user.mb_user_newsletter = form.cleaned_data['newsletter']
            user.mb_user_allow_survey = form.cleaned_data['survey']
            user.timestamp_dsgvo_accepted = time.time()

            # check if passwords match
            if form.cleaned_data['password'] == form.cleaned_data['passwordconfirm']:
                user.password = (str(bcrypt.hashpw(form.cleaned_data['password'].encode('utf-8'), bcrypt.gensalt(12)),'utf-8'))
            else:
                form = RegistrationForm(request.POST)
                context = {
                    'form': form,
                    'headline': _("Registration"),
                    "btn_label1": btn_label,
                    "small_labels": small_labels,
                    "disclaimer": disclaimer,
                    "use_recaptcha": USE_RECAPTCHA,
                    "register": 1,
                }
                geoportal_context.add_context(context)
                messages.error(request, _("Passwords do not match"))
                geoportal_context.get_context()['focus_password'] = True
                return render(request, 'crispy_form_no_action.html', geoportal_context.get_context())

            try:
                realm = mbConfReader.get_mapbender_config_value(PROJECT_DIR,'REALM')
                portaladmin = mbConfReader.get_mapbender_config_value(PROJECT_DIR,'PORTAL_ADMIN_USER_ID')
                byte_aldigest = (form.cleaned_data['name'] + ":" + realm + ":" + form.cleaned_data['password']).encode('utf-8')
                user.mb_user_aldigest = hashlib.md5(byte_aldigest).hexdigest()
                user.mb_user_owner = portaladmin
            except KeyError:
                user.mb_user_owner = 1
                user.mb_user_aldigest = "Could not find realm"
                print("Could not read from Mapbender Config")


            user.mb_user_login_count = 0
            user.mb_user_resolution = 72
            user.is_active = False

            user.activation_key = useroperations_helper.random_string(50)

            send_mail(
                 _("Activation Mail"),
                _("Hello ") + user.mb_user_name +
                ", \n \n" +
                _("This is your activation link. It will be valid until the end of the day, please copy and paste the link in your browser to activate it.")
              	+ "\n Link: "  + HTTP_OR_SSL + HOSTNAME + "/activate/" + user.activation_key,
                DEFAULT_FROM_EMAIL,
                [user.mb_user_email],
                fail_silently=False,
            )


            user.save()

            user = MbUser.objects.get(mb_user_name=user.mb_user_name)
            UserGroupRel = MbUserMbGroup()
            UserGroupRel.fkey_mb_user = user

            group = MbGroup.objects.get(mb_group_name='guest')
            UserGroupRel.fkey_mb_group = group

            role = MbRole.objects.get(role_id=1)
            UserGroupRel.mb_user_mb_group_type = role
            UserGroupRel.save()

            messages.success(request, _("Account creation was successful. "
                "You have to activate your account via email before you can login!"))

            return redirect('useroperations:login')
        else:
            form = RegistrationForm(request.POST)
            context = {
                'form': form,
                'headline': _("Registration"),
                "btn_label1": btn_label,
                "small_labels": small_labels,
                "disclaimer": disclaimer,
            }
            context['focus_phone'] = True
            geoportal_context.add_context(context)
            # give only one error message
            for field, errors in form.errors.items():
                for error in errors:
                    if field == 'captcha':
                        messages.error(request, _("Captcha was wrong! Please try again"))
                    else:
                        messages.error(request, error)
                    break
                break
            
    return render(request, 'crispy_form_no_action.html', geoportal_context.get_context())

@check_browser
def pw_reset_view(request):
    """ View to reset password

    This view has the purpose to regain access if a password is lost.
    To achieve this the user has to enter the correct username and email combination.
    After doing so he gets an email with a password reset link.

    Args:
        request: HTTPRequest
    Returns:
        PasswordResetForm
        Email confirmation
    """

    request.session["current_page"] = "password_reset"
    geoportal_context = GeoportalContext(request=request)

    form = PasswordResetForm()
    btn_label = _("Submit")
    context = {
        'form': form,
        'headline': _("Reset Password"),
        "btn_label2": btn_label,
    }
    geoportal_context.add_context(context)

    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():

            username = form.cleaned_data['name']
            email = form.cleaned_data['email']

            if not MbUser.objects.filter(mb_user_name=username, mb_user_email=email).exists():
                messages.error(request, _("No Account with this Username or Email found"))
            else:
                user = MbUser.objects.get(mb_user_name=username, mb_user_email=email)
                email = user.mb_user_email

                if not user.is_active:  # Check if the user profile is active
                    messages.error(request, _("No Account with this Username or Email found"))
                    return redirect('useroperations:login')
                
                # get the mb_user_password_ticket from the user and if it is true, the user has to wait 24 hours
                if user.mb_user_password_ticket is not None and user.mb_user_password_ticket != "":
                    time_difference = int(time.time()) - int(user.mb_user_password_ticket)
                    if time_difference < 86400:  # 1 day = 86400 seconds
                        messages.error(request, _("You have to wait 24 hours to reset your password again!")) #change it later
                        return redirect('useroperations:login')
                    else:
                        user.mb_user_password_ticket = str(int(time.time()))
                        user.save()
                else:
                    # use the current time as the mb_user_password_ticket and write it to the user
                    user.mb_user_password_ticket = str(int(time.time()))
                    user.save()

                token = custom_token_generator.make_token(user) 
                uid = urlsafe_base64_encode(force_bytes(user.pk)) # encode the user id to base64
                mail_subject = 'Reset your password.'
                message = render_to_string('password_reset_email.html', {
                    'user': user,
                    'domain': HTTP_OR_SSL + HOSTNAME,
                    'uid': uid,
                    'token': token,
                })

                email = EmailMessage(
                    mail_subject, message, to=[email]
                ) 
                email.send()
                messages.success(request, _("We have emailed you instructions for setting your password. You should receive them shortly."))
                return redirect('useroperations:login')

    return render(request, "crispy_form_no_action.html", geoportal_context.get_context())


def password_reset_confirm_view(request, uidb64=None, token=None):
    """ View to confirm password reset

    This view checks if the token is valid and if it is, it allows the user to set a new password.
    After the new password is set, the user is redirected to a page indicating that the password reset was successful.

    Args:
        request: HTTPRequest
        uidb64: User ID encoded in base 64
        token: Token to check if the password reset request is valid
    Returns:
        PasswordResetConfirmForm or redirect to password reset complete view
    """

    try:
        uid = force_text(urlsafe_base64_decode(uidb64)) # decode the user id from base64
        user = MbUser._default_manager.get(pk=uid) # get the user by the user id
    except(TypeError, ValueError, OverflowError, MbUser.DoesNotExist):
        user = None

    if user is not None and user.is_active and custom_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = PasswordResetConfirmForm(request.POST)
            try:
                if form.is_valid():
                    if form.cleaned_data['new_password'] != form.cleaned_data['confirm_password']:
                        messages.error(request, _("The two password fields didn’t match."))
                        return redirect('useroperations:password_reset_confirm', uidb64=uidb64, token=token)
                    else:
                        try:
                            validate_password(form.cleaned_data['new_password'])
                        except ValidationError as e:
                            messages.error(request, e.messages)
                            return redirect('useroperations:password_reset_confirm', uidb64=uidb64, token=token)
                        validator = UserAttributeSimilarityValidator(user_attributes=['mb_user_name'])

                        try:
                            validator.validate(form.cleaned_data['new_password'], user)
                        except ValidationError:
                            messages.error(request, _("Your password can't be too similar to your username."))
                            return redirect('useroperations:password_reset_confirm', uidb64=uidb64, token=token)    
                        user.password = (str(bcrypt.hashpw(form.cleaned_data.get('new_password').encode('utf-8'), bcrypt.gensalt(12)),'utf-8'))
                        # when the password is changed, the mb_user_password_ticket is set to now-86400 so that he can again use the forget password
                        user.mb_user_password_ticket = str(int(time.time()) - 86400)
                        user.save()
                        messages.success(request, _("Your password has been reset. You can now log in with your new password."))
                        return redirect('useroperations:login')
                else:
                    messages.error(request, _("The form is not valid."))
                    return redirect('useroperations:password_reset')
            except ValidationError as e:
                messages.error(request, e.messages)
                return redirect('useroperations:password_reset_confirm', uidb64=uidb64, token=token)
              
        else:
            form = PasswordResetConfirmForm()
        # Get the geoportal context
        if request.method == 'GET':
            geoportal_context = GeoportalContext(request)
            context = {
                'form': form,
                'headline': _("Password reset"),
                "btn_label2": _("Submit"),
            }
            geoportal_context.add_context(context)
            return render(request, 'password_reset_confirm.html', geoportal_context.get_context())
    else:
        messages.error(request, _("The password reset link is invalid or has expired."))
        return redirect('useroperations:password_reset')


@check_browser
def change_profile_view(request):
    """ View to change or delete profile data

    This view is needed if a user wants to change his personal data.
    To achieve this he has to enter his valid password.
    Further the user has the option to delete his account.

    Args:
        request: HTTPRequest
    Returns:
        On HTTPGet it renders the ChangeProfileForm in forms.py.
        On HTTPPost it checks whether the user wants to delete or change his profile.
         Afterwards password is checked for both options and action is takes on.

    """
    dsgvo_flag = True # guest
    
    request.session["can_access_delete"] = True
    request.session["current_page"] = "useroperations:change_profile"
    
    # Retrieve data from session
    #current_page = request.session.get("current_page", None)
    form = ChangeProfileForm()
    user = None
    if request.COOKIES.get(SESSION_NAME) is not None:
        session_data = php_session_data.get_mapbender_session_by_memcache(request.COOKIES.get(SESSION_NAME))
        if session_data != None:
            if b'mb_user_id' in session_data and session_data[b'mb_user_name'] != b'guest':
                userid = session_data[b'mb_user_id']
                user = MbUser.objects.get(mb_user_id=userid)
            else:
                return redirect('useroperations:index')

    else:
        return redirect('useroperations:index')
    if user is None:
        # we expect it to be read out of the session data until this point!!
        messages.add_message(request, messages.ERROR, _("The user could not be found. Please contact an administrator!"))
        return redirect('useroperations:index')

    if request.method == 'GET':
        geoportal_context = GeoportalContext(request)
        context_data = geoportal_context.get_context()
        userdata = {'name': user.mb_user_name,
                    'email': user.mb_user_email,
                    'department': user.mb_user_department,
                    'description': user.mb_user_description,
                    'phone': user.mb_user_phone,
                    'organization': user.mb_user_organisation_name,
                    'newsletter': user.mb_user_newsletter,
                    'survey': user.mb_user_allow_survey,
                    'create_digest' : user.create_digest,
                    'preferred_gui' : user.fkey_preferred_gui_id,
                    }
        if user.timestamp_dsgvo_accepted:
            userdata["dsgvo"] = True

        form = ChangeProfileForm(userdata)

        if context_data['dsgvo'] == 'no' and context_data['loggedin'] == True:
            dsgvo_flag = False
            messages.error(request, _("Please accept the General Data Protection Regulation or delete your account!"))

    if request.method == 'POST':
        form = ChangeProfileForm(request.POST)
        if form.is_valid():

            # Delete profile process
            if request.POST['submit'] == 'Delete Profile' or request.POST['submit'] == 'Profil entfernen':
                if form.cleaned_data['oldpassword']:
                    password = useroperations_helper.bcrypt_password(form.cleaned_data["oldpassword"], user)
                    if password != user.password:
                        messages.error(request, _("Your old Password was wrong"))
                        return redirect('useroperations:change_profile')
                    else:
                        request.session["can_access_delete"] = True
                        return redirect('useroperations:delete_profile')
                else:
                    messages.error(request, _("For deleting your profile, you have to enter your current password."))
                    return redirect("useroperations:change_profile")

            # Save profile process
            elif request.POST['submit'] == 'Save' or request.POST['submit'] == 'Speichern':
                if form.is_valid():
                    # Check old password if any field has been changed
                    if form.has_changed():
                        if form.cleaned_data['oldpassword']:
                            password = useroperations_helper.bcrypt_password(form.cleaned_data["oldpassword"], user)
                            # if the old password didn't match with the one associated to the user, we can abort here!
                            if password != user.password:
                                messages.error(request, _("Your current password was wrong"))
                                return redirect('useroperations:change_profile')
                        else:
                            # user didn't provide the old password!
                            messages.error(request, _("For changing your profile, you have to enter your current password."))
                            return redirect("useroperations:change_profile#change_profile_oldpassword")

                    # user wants to change the password
                    if form.cleaned_data['password'] and form.cleaned_data['passwordconfirm']:
                        # if the old password is fine, we can continue with checking the new provided one
                        if form.cleaned_data['password'] == form.cleaned_data['passwordconfirm']:
                            try: 
                                validate_password(form.cleaned_data['password'])
                            except ValidationError as e:
                                messages.error(request, e.messages)
                                return redirect('useroperations:change_profile')
                            user.password = (str(bcrypt.hashpw(form.cleaned_data['password'].encode('utf-8'), bcrypt.gensalt(12)), 'utf-8'))
                        else:
                            messages.error(request, _("Passwords do not match"))
                            return redirect('useroperations:change_profile')
                    elif form.cleaned_data['password'] or form.cleaned_data['passwordconfirm']:
                        messages.error(request, _("For changing your password, all password fields must be filled."))
                        return redirect('useroperations:change_profile')
                
                user.mb_user_email = form.cleaned_data['email']
                user.mb_user_department = form.cleaned_data['department']
                user.mb_user_description = form.cleaned_data['description']
                user.mb_user_phone = form.cleaned_data['phone']
                user.mb_user_organisation_name = form.cleaned_data['organization']
                user.mb_user_newsletter = form.cleaned_data['newsletter']
                user.mb_user_allow_survey = form.cleaned_data['survey']
                user.create_digest = form.cleaned_data['create_digest']
                user.fkey_preferred_gui_id = form.cleaned_data['preferred_gui']

                if form.cleaned_data['dsgvo'] == True:
                    user.timestamp_dsgvo_accepted = time.time()
                    # set session variable dsgvo via session wrapper php script
                    response = requests.get(HTTP_OR_SSL + '127.0.0.1/mapbender/php/mod_sessionWrapper.php?sessionId='+request.COOKIES.get(SESSION_NAME)+'&operation=set&key=dsgvo&value=true', verify=INTERNAL_SSL)
                else:
                    response = requests.get(HTTP_OR_SSL + '127.0.0.1/mapbender/php/mod_sessionWrapper.php?sessionId='+request.COOKIES.get(SESSION_NAME) +'&operation=set&key=dsgvo&value=false', verify=INTERNAL_SSL)
                    user.timestamp_dsgvo_accepted = None

                if form.cleaned_data['preferred_gui'] == 'Geoportal-RLP_2019':
                    # set session variable preferred_gui via session wrapper php script
                    response = requests.get(HTTP_OR_SSL + '127.0.0.1/mapbender/php/mod_sessionWrapper.php?sessionId='+request.COOKIES.get(SESSION_NAME)+'&operation=set&key=preferred_gui&value=Geoportal-RLP_2019', verify=INTERNAL_SSL)
                else:
                    response = requests.get(HTTP_OR_SSL + '127.0.0.1/mapbender/php/mod_sessionWrapper.php?sessionId='+request.COOKIES.get(SESSION_NAME)+'&operation=set&key=preferred_gui&value='+DEFAULT_GUI, verify=INTERNAL_SSL)
                
                user.save()
                messages.success(request, _("Successfully changed data"))
                return redirect('useroperations:index')
        else:
            if form.errors.get('phone'): 
                messages.error(request, _("Invalid phone number."))
            else:
                messages.error(request, _("For changing your profile, you have to enter your current password."))
            return HttpResponseRedirect(reverse('useroperations:change_profile') + '#change_profile_oldpassword')

    small_labels = [
        "id_newsletter",
        "id_survey",
        "id_create_digest",
        "id_dsgvo"
    ]
    btn_label_change = _("Save")
    btn_label_delete = _("Delete Profile")

    geoportal_context = GeoportalContext(request=request)
    context = {
        'btn_label1': btn_label_change,
        'btn_label2': btn_label_delete,
        'form': form,
        'headline': _("Change data"),
        'small_labels': small_labels,
        'dsgvo_flag': dsgvo_flag,
        #'is_change_page': True,
    }
    geoportal_context.add_context(context)
    return render(request, 'crispy_form_no_action.html', geoportal_context.get_context())


@check_browser
def delete_profile_view(request):
    """ View for profile deletion

    This view handles the deletion of profiles.
    Users get redirected to this view if they click on "delete profile"
     in the change profile form and provided a valid password.

    Args
        request: HTTPRequest
    Returns:
        DeleteProfileForm
    """

    geoportal_context = GeoportalContext(request=request)
    # check if the user has access to this page and donot allow direct access
    # to this delete the page directly from the url
    referer = request.META.get('HTTP_REFERER', '')

    if 'change-profile' not in referer.lower() and 'delete-profile' not in referer.lower():
        return redirect('useroperations:change_profile')
    
    if not request.session.get("can_access_delete", False):
        return redirect('useroperations:change_profile')
    
    # TODO:
    # check if the mapbender connection with delete profile is still working!
    

    if request.COOKIES.get(SESSION_NAME) is not None:
        session_data = php_session_data.get_mapbender_session_by_memcache(request.COOKIES.get(SESSION_NAME))
        if session_data != None:
            if b'mb_user_id' in session_data and session_data[b'mb_user_name'] != b'guest':

                session_data = php_session_data.get_mb_user_session_data(request)

                request.session["current_page"] = "delete_profile"

                form = DeleteProfileForm(request.POST)
                btn_label = _("Delete Profile!")
                geoportal_context = GeoportalContext(request=request)
                context = {
                    'form': form,
                    'headline': _("Delete Profile?"),
                    "btn_label2": btn_label,
                    'is_delete_page': True,
                }
                geoportal_context.add_context(context)

                if request.method == 'POST':
                    if form.is_valid():
                        # get user
                        session_id = request.COOKIES.get(SESSION_NAME)
                        session_data = php_session_data.get_mapbender_session_by_memcache(session_id)
                        try:
                            userid = session_data[b'mb_user_id']
                        except KeyError:
                            messages.error(request, _("You are not logged in"))
                            return redirect('useroperations:index')
                        userid = session_data[b'mb_user_id']
                        user = MbUser.objects.get(mb_user_id=userid)

                        error = False
                        if Wms.objects.filter(wms_owner=userid).exists() or Wfs.objects.filter(wfs_owner=userid).exists():
                            messages.error(request, _("You are owner of registrated services - please delete them or give the ownership to another user."))
                            error = True
                        if GuiMbUser.objects.filter(fkey_mb_user_id=userid).exists() and GuiMbUser.objects.filter(mb_user_type='owner'):
                            messages.error(request, _("You are owner of guis/applications - please delete them or give the ownership to another user."))
                            error = True
                        if MbProxyLog.objects.filter(fkey_mb_user_id=userid).exists():
                            messages.error(request, _("There are logged service accesses for this user profile. Please connect the service administrators for the billing first."))
                            error = True

                        if not error:
                            user.is_active = False
                            user.activation_key = useroperations_helper.random_string(50)
                            user.timestamp_delete = time.time()
                            user.save()
                            
                            try:
                                send_mail(
                                    _("Reactivation Mail"),
                                    _("Hello ") + user.mb_user_name +
                                    ", \n \n" +
                                    _("In case the deletion of your account was a mistake, you can reactivate it by clicking this link!")
                                    + "\n Link: " + HTTP_OR_SSL + HOSTNAME + "/activate/" + user.activation_key,
                                    DEFAULT_FROM_EMAIL,
                                    [user.mb_user_email],
                                    fail_silently=False,
                                )
                            except smtplib.SMTPException:
                                logger.error(_("Could not send activation mail!"))
                                messages.error(request, _("An error occured during sending. Please inform an administrator."))
                                return redirect('useroperations:change_profile')

                            php_session_data.delete_mapbender_session_by_memcache(session_id)
                            messages.success(request, _("Successfully deleted the user:")
                                             + " {str_name} ".format(str_name=user.mb_user_name)
                                             + _(". In case this was an accident, we sent you a link where you can reactivate "
                                                 "your account for 24 hours!"))

                            return redirect('useroperations:logout')
            else:
                return redirect('useroperations:index')
    else:
        return redirect('useroperations:index')

    return render(request, "crispy_form_no_action.html", geoportal_context.get_context())


@check_browser
def logout_view(request):
    """ View for logging out users

    This view deletes the session if a user logs out.

    Args:
        request: HTTPRequest

    Returns:
        LogoutForm
    """

    request.session["current_page"] = "logout"
    geoportal_context = GeoportalContext(request=request)

    if request.COOKIES.get(SESSION_NAME) is not None:
        session_id = request.COOKIES.get(SESSION_NAME)
        php_session_data.delete_mapbender_session_by_memcache(session_id)
        messages.success(request, _("Successfully logged out"))
        return redirect('useroperations:index')
    else:
        messages.error(request, _("You are not logged in"))
    return render(request, "crispy_form_no_action.html", geoportal_context.get_context())


@check_browser
def map_viewer_view(request):
    """ Parse all important data for the map rendering from the session

    This view is used to hand over all the data that is needed
     by the mapviewer.
    The parameters come from the search interface are therefore
     included in the URL.



    Args:
        request: HTTPReqeust , this in includes all mapviewer
                  parameters coming from the search module
    Returns:
            response: a json object containing all the
             mapviewer parameters
    """

    geoportal_context = GeoportalContext(request)
    context_data = geoportal_context.get_context()
    if context_data['dsgvo'] == 'no' and context_data['loggedin'] == True:
        return redirect('useroperations:change_profile')

    lang = request.LANGUAGE_CODE
    geoportal_context = GeoportalContext(request=request)

    is_external_search = "external" in request.META.get("HTTP_REFERER", "")
    request_get_params_dict = request.GET.dict()

    # is regular call means the request comes directly from the navigation menu in the page, without selecting a search result
    is_regular_call = len(request_get_params_dict) == 0 or request_get_params_dict.get("searchResultParam", None) is None
    request_get_params = dict(urllib.parse.parse_qsl(request_get_params_dict.get("searchResultParam"), keep_blank_values=True))
    template = "geoportal_external.html"
    gui_id = context_data.get("preferred_gui", DEFAULT_GUI)  # get selected gui from params, use default gui otherwise!

    wmc_id = request_get_params.get("WMC", "") or request_get_params.get("wmc", "")
    wms_id = request_get_params.get("WMS", "") or request_get_params.get("wms", "")

    # resolve wms_id to LAYER[id] if the given parameter is not an uri but rather an integer
    try:
        wms_id = int(wms_id)
        request_get_params["LAYER[id]"] = wms_id
        wms_id = ""
    except ValueError:
        # If this failed, the wms_id is not an integer, so we assume it must be some kind of link
        pass

    # MOBILE DETECTION IS NOW IN JAVASCRIPT all.js and frontpage.js, NOT SURE IF THIS MIGHT BE NEEDED LATER
    # check if the request comes from a mobile device
    #is_mobile = request.user_agent.is_mobile
    #if is_mobile:
        # if so, just call the mobile map viewer in a new window
    #    mobile_viewer_url = "{}{}/mapbender/extensions/mobilemap2/index.html?".format(HTTP_OR_SSL, HOSTNAME)
    #    if wmc_id != "":
    #        mobile_viewer_url += "&wmc_id={}".format(wmc_id)
    #    if wms_id != "":
    #        mobile_viewer_url += "&wms_id={}".format(wms_id)
    #    return GeoportalJsonResponse(url=mobile_viewer_url).get_response()

    mapviewer_params_dict = {
        "LAYER[id]": request_get_params.get("LAYER[id]", ""),
        "LAYER[zoom]": request_get_params.get("LAYER[zoom]", ""),
        "LAYER[visible]": request_get_params.get("LAYER[visible]", 1),
        "LAYER[querylayer]": request_get_params.get("LAYER[querylayer]", 1),
        "WMS": wms_id,
        "WMC": wmc_id,
        "GEORSS": urllib.parse.urlencode(request_get_params.get("GEORSS", "")),
        "KML": urllib.parse.urlencode(request_get_params.get("KML", "")),
        "FEATURETYPE": request_get_params.get("FEATURETYPE[id]", ""),
        "ZOOM": request_get_params.get("ZOOM", ""),
        "GEOJSON": request_get_params.get("GEOJSON", ""),
        "GEOJSONZOOM": request_get_params.get("GEOJSONZOOM", ""),
        "GEOJSONZOOMOFFSET": request_get_params.get("GEOJSONZOOMOFFSET", ""),
        "gui_id": request_get_params.get("gui_id", gui_id),
        "DATASETID": request_get_params.get("DATASETID", ""),
    }

    mapviewer_params = "&" + urllib.parse.urlencode(mapviewer_params_dict)

    if is_regular_call:
        # an internal call from our geoportal should lead to the map viewer page without problems
        params = {
            "mapviewer_params": mapviewer_params,
            "mapviewer_src":  HTTP_OR_SSL + HOSTNAME + "/mapbender/frames/index.php?lang=" + lang + "&" + mapviewer_params,
        }
        geoportal_context.add_context(context=params)
        return render(request, template, geoportal_context.get_context())

    elif is_external_search:
        # for an external ajax call we need to deliver a url which can be used to open a new tab which leads to the geoportal
        return GeoportalJsonResponse(url=HTTP_OR_SSL + HOSTNAME, mapviewer_params=gui_id + "&" + request_get_params_dict.get("searchResultParam")).get_response()

    else:
        # for an internal search result selection, where the dynamic map viewer overlay shall be used
        return GeoportalJsonResponse(mapviewer_params=mapviewer_params).get_response()


@check_browser
def get_map_view(request):
    """ Calls a service directly using GET parameters

    There is no logic inside this function. Since all the service loading is on javascript controlled client side
    we only call the usual index page and keep the GET parameters which will be processed by the javascript.

    Args:
        request (HttpRequest):  The incoming HttpRequest
    Returns:
         the index view
    """
    return index_view(request)


@check_browser
def activation_view(request, activation_key=""):
    """
    View for activating user account after creation or deletion

    After creating an account, a user has to verify his email by clicking a link that was send to him.
    After deleting an account, a user can reactivate his account by clicking a link in the email.

    Args:
        request: HTTPRequest
        activation_key (slug): Key to activate the user, stored in database
    Returns:
        Template:
         (activation.html) in case activation was successful
         (404.html) in case activation failed for some reason

    """
    geoportal_context = GeoportalContext(request=request)
    reactivated = False

    if MbUser.objects.filter(activation_key=activation_key, is_active=True):
        messages.error(request, _("Account already active"))
        activated = True
        template = '404.html'

    elif not MbUser.objects.filter(activation_key=activation_key, is_active=False):
        messages.error(request, _("Invalid data"))
        activated = False
        template = '404.html'

    else:
        user = MbUser.objects.get(activation_key=activation_key, is_active=False)
        user.is_active = True
        reactivated = user.timestamp_delete is not None
        user.mb_user_login_count = 0
        activated = True
        user.save()
        template = 'activation.html'

    context = {
        "headline": _('Account activation'),
        "activated": activated,
        "reactivated": reactivated,
        "navigation": utils.get_navigation_items(),
    }
    geoportal_context.add_context(context=context)

    return render(request, template, context=geoportal_context.get_context())


@check_browser
def feedback_view(request: HttpRequest):

    """ Renders a feedback form for the user

    Args:
        request:
    Returns:

    """
    request.session["current_page"] = "feedback"

    geoportal_context = GeoportalContext(request)
    context_data = geoportal_context.get_context()
    if context_data['dsgvo'] == 'no' and context_data['loggedin'] == True:
        return redirect('useroperations:change_profile')

    disclaimer = _("Personal data will not be transmitted to other parties or services. "
                   "The data, you provided during the feedback process, will only be used to stay in contact regarding your feedback.\n"
                   "Further information can be found in our ")
    if request.method == 'POST':
        # form is returning
        form = FeedbackForm(request.POST)
        if form.is_valid():

            if USE_RECAPTCHA == 1:
                recaptcha_response = request.POST.get('g-recaptcha-response')
                data = {
                    'secret': GOOGLE_RECAPTCHA_SECRET_KEY,
                    'response': recaptcha_response
                }
                r = requests.post('https://www.google.com/recaptcha/api/siteverify', proxies=PROXIES, data=data)
                result = r.json()

                if not result['success']:
                    messages.error(request, _("Invalid reCAPTCHA. Please try again."))
                    return redirect('useroperations:feedback')


            messages.success(request, _("Feedback sent. Thank you!"))
            msg = {
                "sender": form.cleaned_data["first_name"] + " " + form.cleaned_data["family_name"],
                "address": form.cleaned_data["email"],
                "message": form.cleaned_data["message"],
            }
            try:

                send_mail(
                    _("Geoportal Feedback"),
                    _("Feedback from ") + form.cleaned_data["first_name"] + " " + form.cleaned_data["family_name"]
                    + ", \n \n" +
                    form.cleaned_data["message"],
                    form.cleaned_data["email"],
                    [DEFAULT_TO_EMAIL],
                    fail_silently=False,
                )
            except smtplib.SMTPException:
                logger.error("Could not send feedback mail!")
                messages.error(request, _("An error occured during sending. Please inform an administrator."))
            return index_view(request=request)
        else:
            messages.error(request, _("Captcha was wrong! Please try again"))
            template = "feedback_form.html"
            params = {
                "form": form,
                "btn_send": _("Send"),
                "disclaimer": disclaimer,
            }
            geoportal_context.add_context(params)
            return render(request=request, context=geoportal_context.get_context(), template_name=template)
    else:
        # create the form
        template = "feedback_form.html"
        feedback_form = FeedbackForm()
        params = {
            "form": feedback_form,
            "btn_send": _("Send"),
            "disclaimer": disclaimer,
            "use_recaptcha": USE_RECAPTCHA,
            "recaptcha_public_key" : GOOGLE_RECAPTCHA_PUBLIC_KEY,
        }
        geoportal_context = GeoportalContext(request=request)
        geoportal_context.add_context(params)
        return render(request=request, context=geoportal_context.get_context(), template_name=template)


@check_browser
def service_abo(request: HttpRequest):

    """ Displays the serice abos of a user

    Args:
        request:
    Returns:

    """
    request.session["current_page"] = "show_abo"

    geoportal_context = GeoportalContext(request)
    context_data = geoportal_context.get_context()
    if context_data['dsgvo'] == 'no' and context_data['loggedin'] == True:
        return redirect('useroperations:change_profile')

    template = "show_abo.html"

    geoportal_context = GeoportalContext(request=request)
    return render(request=request, context=geoportal_context.get_context(), template_name=template)

@check_browser
def open_linked_data(request: HttpRequest):

    """ Open Linked Data Page

    Args:
        request:
    Returns:

    """
    request.session["current_page"] = "linked_open_data"

    geoportal_context = GeoportalContext(request)
    context_data = geoportal_context.get_context()
    if context_data['dsgvo'] == 'no' and context_data['loggedin'] == True:
        return redirect('useroperations:change_profile')

    template = "open_linked_data.html"

    geoportal_context = GeoportalContext(request=request)
    return render(request=request, context=geoportal_context.get_context(), template_name=template)


def incompatible_browser(request: HttpRequest):
    """ Renders a template about how the user's browser is a filthy peasants tool.

    Args:
        request: The incoming request
    Returns:
         A rendered view
    """
    request.session["current_page"] = "incompatible"
    template = "unsupported_browser.html"
    params = {

    }
    return render(request, template_name=template, context=params)


def handle500(request: HttpRequest, template_name="500.html"):
    """ Handles a 404 page not found error using a custom template

    Args:
        request:
        exception:
        template_name:
    Returns:
    """
    return render(request, template_name, GeoportalContext(request).get_context())