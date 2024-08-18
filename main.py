from starlette.responses import HTMLResponse
from concurrent.futures import ThreadPoolExecutor, wait
from tls_client import Session
from threading import Lock, Thread
from datetime import date
from colorama import Fore
from fastapi import FastAPI
from uvicorn import run
from random import choice, randint
from typing import Optional
from string import *
from httpx import get
from time import time, sleep
from json import load, dump, dumps

stats = None
config = load(open('config.json', 'r'))
record = load(open('record.json', 'r'))
server = "https://publisher.linkvertise.com/"
proxy_num = 0
proxy_list = open("proxies.txt").read().splitlines()
thread_lock = Lock()
need_logging = config["need_logging"]
thread_count = config["thread_count"]
statistics, exceptions, downloads, impressions = {}, 0, 0, 0

class Db:
    def update_json():
        global config, record
        while True:
            with open("record.json", "w") as r:
                dump(record, r)
            with open("config.json", "w") as c:
                dump(config, c)
            config = load(open('config.json', 'r'))
            record = load(open('record.json', 'r'))
            sleep(1)
        
class Stats:
    def __init__(self, cookie: str) -> None:
        headers, version = Utils.spoof_fingerprint()
        self.session = Session(client_identifier = version, random_tls_extension_order = True)
        self.session.headers = headers
        self.session.headers["cookie"] = cookie
        self.utils = Utils(self.session)
    
    def check_statistics(self):
        while True:
            r = self.session.post(
                server + "statistics", 
                data = "interval=DAY7&t=FIXED&trafficOrigin=false&incomeOrigin=false&linkIsSeo=false",
                headers = {
                    "content-type": "application/x-www-form-urlencoded; charset=UTF-8"
                }
            )
            if "statistics" in r.text:
                r = r.json()["statistics"]
                break
        return {
            "amount": r["amount"]["converted"],
            "clicks": r["clicks"]["value"],
            "impressions": r["impressions"]["value"],
        }

    def create_link(self):
        while True:
            random_link = choice(['https://www.youtube.com/watch?v=7vQd7kqYL5I', 'https://www.youtube.com/watch?v=SyU1Qe7iY3A', 'https://www.youtube.com/watch?v=kuPYzNNsSdA', 'https://www.youtube.com/watch?v=zFPb7u80byM&t=3645s', 'https://www.youtube.com/watch?v=QwO0Ot5tT7o', 'https://www.youtube.com/watch?v=WsPaJdvBzhE'])
            random_game = choice(['krunker', 'pubg', 'teder', 'fornite'])

            r = self.utils.common_graphql({
                "operationName":"createLink",
                "variables":{
                    "input":{
                        "target":f"https://cheaters.game/id/{random_game}/{randint(10000, 99999)}/{int(time())}",
                        "btn_text":f"{random_game}:Cheat V{randint(1, 5)}.{1, 9}",
                        "title":f"Download THIS CHEAT | {choice(['Updated', 'NEW', 'HOT'])} | Works for most of the game mode",
                        "description":"The best cheat in the world you cannot find another one. Could you support us by going through this link?",
                        "video_url":choice(random_link),
                        "seo_faq_ids":[],"available_ads":"ALL","target_type":"URL","paywall_weight":0.5,"btn_prefix":"zu","seo_active":True,"images":[],"require_addon":True,"require_web":True,"require_installer":True,"require_og_ads":True,"require_custom_ad_step":True,

                }},
                "query":"mutation createLink($input: LinkInput!) {\n  createLink(input: $input) {\n    id\n    href\n    user_id\n    __typename\n  }\n}\n"
            })
            if "createLink" in r.text:
                return r.json()["data"]["createLink"]["href"]

class Utils:
    def __init__(self, session: Session, x_linkvertise_ut: Optional[str] = "") -> None:
        self.session = session
        self.x_linkvertise_ut = x_linkvertise_ut
    
    def common_graphql(self, json_payload: dict,  without_key: Optional[bool] = None) -> object:
        return self.session.post(
            server + "graphql" + ("" if without_key else "?X-Linkvertise-UT=" + self.x_linkvertise_ut),
            json = json_payload
        )
    @staticmethod
    def change_content(change_list: list, html_document: str) -> str:
        for _ in range(len(change_list)):
            if isinstance(change_list[_]["a"], int):
                change_list[_]["a"] = str(change_list[_]["a"])
            if isinstance(change_list[_]["b"], int):
                change_list[_]["b"] = str(change_list[_]["b"])
            html_document = html_document.replace("{{" + change_list[_]["a"] + "}}", change_list[_]["b"])
        return html_document

    @staticmethod
    def iterating_proxy() -> str:
        global proxy_num
        if proxy_num == len(proxy_list):
            proxy_num = 0
        random_proxy = proxy_list[proxy_num]
        proxy_num += 1
        return random_proxy

    @staticmethod
    def extract_link(link: str) -> dict:
        if "link-target.net" in link:
            link = str(get(link, follow_redirects = True).url)
        match_check = link.split("https://linkvertise.com/")[1].split("?")[0]

        return {
            "id": match_check.split("/")[0], 
            "link": link, 
            "value": match_check.split("/")[1]
        }
    
    @staticmethod
    def spoof_fingerprint():
        user_agent = [{"key": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36", "value": "chrome127"}, {"key": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36", "value": "chrome127"}, {"key": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36", "value": "chrome127"}, {"key": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/128.0.6613.34 Mobile/15E148 Safari/604.1", "value": "chrome127"}, {"key": "Mozilla/5.0 (iPad; CPU OS 17_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/128.0.6613.34 Mobile/15E148 Safari/604.1", "value": "chrome127"}, {"key": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.103 Mobile Safari/537.36", "value": "chrome127"}, {"key": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 OPR/112.0.0.0", "value": "opera112"}, {"key": "Mozilla/5.0 (Windows NT 10.0; WOW64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 OPR/112.0.0.0", "value": "opera112"}, {"key": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 OPR/112.0.0.0", "value": "opera112"}, {"key": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 OPR/112.0.0.0", "value": "opera112"}, {"key": "Mozilla/5.0 (Linux; Android 10; SM-G970F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.103 Mobile Safari/537.36 OPR/76.2.4027.73374", "value": "opera112"}, {"key": "Mozilla/5.0 (Linux; Android 10; SM-N975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.103 Mobile Safari/537.36 OPR/76.2.4027.73374", "value": "opera112"}, {"key": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0", "value": "firefox129"}, {"key": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.6; rv:129.0) Gecko/20100101 Firefox/129.0", "value": "firefox129"}, {"key": "Mozilla/5.0 (X11; Linux i686; rv:129.0) Gecko/20100101 Firefox/129.0", "value": "firefox129"}, {"key": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/129.0 Mobile/15E148 Safari/605.1.15", "value": "firefox129"}, {"key": "Mozilla/5.0 (iPad; CPU OS 14_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/129.0 Mobile/15E148 Safari/605.1.15", "value": "firefox129"}, {"key": "Mozilla/5.0 (Android 14; Mobile; rv:129.0) Gecko/129.0 Firefox/129.0", "value": "firefox129"}, {"key": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15", "value": "safari_17_5"}, {"key": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1", "value": "safari_17_5"}, {"key": "Mozilla/5.0 (iPad; CPU OS 17_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1", "value": "safari_17_5"}]
        user_agent_data = choice(user_agent)
        user_agent, client_identifier = user_agent_data["key"], user_agent_data["value"]

        headers = {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-GB,en;q=0.9",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://linkvertise.com",
            "priority": "u=1, i",
            "referer": "https://linkvertise.com/",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": user_agent
        }
        return headers, client_identifier

class Logger:
    @staticmethod
    def ERROR(text: str):
        print(f"{Fore.LIGHTRED_EX}- ERR{Fore.RESET} {text}")

    @staticmethod
    def SUCCESS(text: str):
        print(f"{Fore.LIGHTGREEN_EX}+ SUC{Fore.RESET} {text}")

    @staticmethod
    def NORMAL(text: str):
        if need_logging:
            print(f"{Fore.LIGHTCYAN_EX}* NOR{Fore.RESET} {text}")

    @staticmethod
    def FAILED(text: str):
        if need_logging:
            print(f"{Fore.LIGHTMAGENTA_EX}! EXC{Fore.RESET} {text}")

class Generator:
    def __init__(self, data: dict = {"id": "1217874", "link": "https://linkvertise.com/1217874/the-lateral-cranial?o=sharing", "value": "the-lateral-cranial"}) -> None:
        self.link_data = data["link"]
        self.link_payload = {"user_id":data["id"], "url":data["value"]}

    def run_proccess(self):
        global exceptions, downloads, impressions
        self.sent, self.exceptions, self.downloads, self.impressions = False, 0, 0, 0

        def inner_function():
            while True:
                try:
                    self.start_time = time()
                    proxy = Utils.iterating_proxy()
                    headers, version = Utils.spoof_fingerprint()
                    self.session = Session(client_identifier = version, random_tls_extension_order = True)
                    self.session.headers = headers
                    self.session.proxies = {
                        "http": "http://" + proxy,
                        "https": "http://" + proxy
                    }
                    if self.fetch_account() != True:
                        Logger.FAILED("cloudfare: retry")
                        self.exceptions += 1
                        continue

                    self.utils = Utils(self.session, self.x_linkvertise_ut)
                    tasks_to_complete = [
                        self.fetch_taboola_info, 
                        self.get_detail_page_content, 
                        self.get_taboola_ads, 
                        self.complete_detail_page_content
                    ]                
                    for _ in range(len(tasks_to_complete)):
                        tasks_to_complete[_]()

                    if self.complete_custom_ad_offer():
                        Logger.SUCCESS(f"increased: impression [Took {round(time() - self.start_time)} sec]")
                        continue

                    self.get_detail_page_target()
                    if self.sent: 
                        Logger.SUCCESS(f"increased: download/impression [Took {round(time() - self.start_time)} sec]")
                        break
                except Exception as e:
                    self.exceptions += 1
                    Logger.ERROR(f"{e}")

        inner_function()
        exceptions += self.exceptions
        downloads += self.downloads
        impressions += self.impressions

    def fetch_account(self) -> bool:
        r = self.session.get(
            server + "api/v1/account",
        )
        if "user_token" in r.text:
            self.x_linkvertise_ut = r.json()["user_token"]
            return True

    def fetch_taboola_info(self) -> None:
        self.user_id = self.session.get(
            "https://api.taboola.com/2.0/json/linkvertise-linkvertiseapikey/user.sync?app.type=desktop&app.apikey=5f560f57763908a1256447e08a287e0aaa466fb6&X-Linkvertise-UT=" + self.x_linkvertise_ut
        ).json()["user"]["id"]
        Logger.NORMAL(f"fetch_taboola_info: {self.user_id}")

    def get_detail_page_content(self) -> None:
        r = self.utils.common_graphql({
            "operationName":"getDetailPageContent",
            "variables":{"linkIdentificationInput":{"userIdAndUrl":self.link_payload},"origin":"sharing","additional_data":{"taboola":{"external_referrer":"","user_id":self.user_id,"url":self.link_data,"test_group":"old","session_id":None}}},"query":"mutation getDetailPageContent($linkIdentificationInput: PublicLinkIdentificationInput!, $origin: String, $additional_data: CustomAdOfferProviderAdditionalData!) {\n  getDetailPageContent(\n    linkIdentificationInput: $linkIdentificationInput\n    origin: $origin\n    additional_data: $additional_data\n  ) {\n    access_token\n    payload_bag {\n      taboola {\n        session_id\n        __typename\n      }\n      __typename\n    }\n    premium_subscription_active\n    link {\n      id\n      video_url\n      short_link_title\n      recently_edited\n      short_link_title\n      description\n      url\n      seo_faqs {\n        body\n        title\n        __typename\n      }\n      target_host\n      last_edit_at\n      link_images {\n        url\n        __typename\n      }\n      title\n      thumbnail_url\n      view_count\n      is_trending\n      recently_edited\n      seo_faqs {\n        title\n        body\n        __typename\n      }\n      percentage_rating\n      is_premium_only_link\n      publisher {\n        id\n        name\n        subscriber_count\n        __typename\n      }\n      positive_rating\n      negative_rating\n      already_rated_by_user\n      user_rating\n      __typename\n    }\n    linkCustomAdOffers {\n      title\n      call_to_action\n      description\n      countdown\n      completion_token\n      provider\n      provider_additional_payload {\n        taboola {\n          available_event_url\n          visible_event_url\n          __typename\n        }\n        __typename\n      }\n      media {\n        type\n        ... on UrlMediaResource {\n          content_type\n          resource_url\n          __typename\n        }\n        __typename\n      }\n      clickout_action {\n        type\n        ... on CustomAdOfferClickoutUrlAction {\n          type\n          clickout_url\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    link_recommendations {\n      short_link_title\n      target_host\n      id\n      url\n      publisher {\n        id\n        name\n        __typename\n      }\n      last_edit_at\n      link_images {\n        url\n        __typename\n      }\n      title\n      thumbnail_url\n      view_count\n      is_trending\n      recently_edited\n      percentage_rating\n      publisher {\n        name\n        __typename\n      }\n      __typename\n    }\n    target_access_information {\n      remaining_accesses\n      daily_access_limit\n      remaining_waiting_time\n      __typename\n    }\n    __typename\n  }\n}"
        }).json()["data"]["getDetailPageContent"]
        view_count, self.access_token = r["link"]["view_count"], r["access_token"]

        if len(r["linkCustomAdOffers"]) == 0:
            raise Exception("get_detail_page_content: error no list in")

        self.custom_ad_dict = r["linkCustomAdOffers"][randint(0, len(r["linkCustomAdOffers"])-1)]
        Logger.NORMAL(f"get_detail_page_content: {view_count, self.access_token}")
    
    def get_taboola_ads(self) -> None:
        r = self.utils.common_graphql({
            "operationName":"getTaboolaAds",
            "variables":{"linkIdentificationInput":{"userIdAndUrl":self.link_payload},"additional_data":{"taboola":{"consent_string":"","url":self.link_data,"user_id":self.user_id}}},
            "query":"query getTaboolaAds($linkIdentificationInput: PublicLinkIdentificationInput!, $additional_data: CustomAdOfferProviderAdditionalData!) {\n  getTaboolaAds(\n    linkIdentificationInput: $linkIdentificationInput\n    additional_data: $additional_data\n  ) {\n    title\n    call_to_action\n    description\n    media {\n      type\n      resource_url\n      __typename\n    }\n    clickout_action {\n      type\n      clickout_url\n      __typename\n    }\n    provider_additional_payload {\n      visible_event_url\n      available_event_url\n      __typename\n    }\n    __typename\n  }\n}",
        }).json()["data"]["getTaboolaAds"]

    def complete_detail_page_content(self) -> None:
        r = self.utils.common_graphql({
            "operationName":"completeDetailPageContent",
            "variables":{"linkIdentificationInput":{"userIdAndUrl":self.link_payload},"completeDetailPageContentInput":{"access_token":self.access_token}},
            "query":"mutation completeDetailPageContent($linkIdentificationInput: PublicLinkIdentificationInput!, $completeDetailPageContentInput: CompleteDetailPageContentInput!) {\n  completeDetailPageContent(\n    linkIdentificationInput: $linkIdentificationInput\n    completeDetailPageContentInput: $completeDetailPageContentInput\n  ) {\n    CUSTOM_AD_STEP\n    TARGET\n    additional_target_access_information {\n      remaining_waiting_time\n      can_not_access\n      should_show_ads\n      has_long_paywall_duration\n      __typename\n    }\n    __typename\n  }\n}",
        }).json()["data"]["completeDetailPageContent"]
        self.target_token, self.custom_ad_token = r["TARGET"], r["CUSTOM_AD_STEP"]
        Logger.NORMAL(f"complete_detail_page_content: {self.target_token} {self.custom_ad_token}")
    
    def complete_custom_ad_offer(self) -> bool:
        r = self.utils.common_graphql({
            "operationName":"completeCustomAdOffer",
            "variables":{"completion_token":self.custom_ad_dict["completion_token"],"traffic_validation_token":self.custom_ad_token},
            "query":"mutation completeCustomAdOffer($completion_token: String!, $traffic_validation_token: String!) {\n  completeCustomAdOffer(\n    completion_token: $completion_token\n    traffic_validation_token: $traffic_validation_token\n  )\n}"
        }).json()["data"]["completeCustomAdOffer"]

        if r != True:
            self.impressions += 1
            return True

        self.sent = r
        self.downloads += 1
        self.impressions += 1
        
        Logger.NORMAL(f"complete_custom_ad_offer: {r}")

    def get_detail_page_target(self) -> str:
        r = self.utils.common_graphql({
            "operationName":"getDetailPageTarget",
            "variables":{"linkIdentificationInput":{"userIdAndUrl":self.link_payload},"token":self.target_token},
            "query":"mutation getDetailPageTarget($linkIdentificationInput: PublicLinkIdentificationInput!, $token: String!) {\n  getDetailPageTarget(\n    linkIdentificationInput: $linkIdentificationInput\n    token: $token\n  ) {\n    type\n    url\n    paste\n    short_link_title\n    __typename\n  }\n}",
        }).json()["data"]["getDetailPageTarget"]["url"]

def run_server():
    global exceptions, downloads, impressions, statistics
    fast_app = FastAPI()
    @fast_app.get('/')
    def fast_api():
        with thread_lock:
            website_html = Utils.change_content([
                {"a": "impressions", "b": impressions},
                {"a": "exceptions", "b": exceptions},
                {"a": "downloads", "b": downloads},
                {"a": "revenue", "b": statistics["amount"] if statistics.get("amount") != None else ""},
                # {"a": "", "b": ""},
            ], open("index.html", "r").read())
            return HTMLResponse(content=website_html, status_code=200)
    run(fast_app, host="0.0.0.0", port=config["server_port"]) # , log_level="critical"


def check_stats():
    global statistics
    while True:
        try:
            statistics = stats.check_statistics()
            sleep(10)
        except Exception as e:
            print(e)

def cyber_earner(data: dict):
    while True:
        try:
            Generator(data).run_proccess()
        except:
            continue

def main_process():
    data_list = []
    for _ in range(len(config["link"])):
        data_list.append(Utils.extract_link(config["link"][_]))

    with ThreadPoolExecutor(max_workers = thread_count) as executor:
        while True:
            for _ in range(thread_count):
                executor.submit(cyber_earner, choice(data_list))

def stats_recorder():
    def create_link():
        data = {
            "link": stats.create_link(),
            "alive": 0,
            "req_range": [3, 4]
        }
        data["data"] = Utils.extract_link(data["link"])
        record["links"].append(data)

    def load_in():
        record["amount"].append(stats.check_statistics() | {"day": 0})

    def control_moment():
        startup_date = date.today().strftime('%d')
        record["day"] += 1
        record["date"] = startup_date
        for _ in range(len(record["link"])):
            temp_var = record["links"][_]
            temp_var["alive"] += 1
            temp_var["req_range"][0] += 1
            temp_var["req_range"][1] += 1
            record["links"][_] = temp_var
        
        if (len(record["links"]) < 20 and record["day"] != 0) and (record["day"] % 2 == 0):
            create_link()
        
    if len(record["links"]) == 0:
        create_link()
    if len(record["amount"]) == 0:
        load_in()
    
    while True:
        while date.today().strftime('%d') == startup_date:
            link_list = []
            start_time = int(time())
            thread_list = []

            for _ in range(len(record["links"])):
                data = record["links"][_]
                link_list.append([data["link"], data[""]])
            with ThreadPoolExecutor(max_workers = len(record["link"])) as executor:
                for _ in range(amount):
                    thread_list.append(executor.submit())
                wait(thread_list)
                  
        control_moment()

if __name__ == '__main__':
    stats = Stats(config["account_info"])
    startup_time = date.today()
    startup_date = startup_time.strftime('%d')
    
    stats_recorder()
    Thread(target=check_stats).start()
    main_thread = Thread(target=run_server)
    main_thread.start(); main_thread.join()
    # main_process()

