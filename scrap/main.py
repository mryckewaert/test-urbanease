import requests
import logging
import json
from bs4 import BeautifulSoup
import conf
import psycopg2


def main():

    conn = psycopg2.connect(
        "dbname=test_urbanease user=postgres password=postgres port=5433")
    cur = conn.cursor()

    logging.basicConfig(filename='scrap/logs/logfile.log', level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    for departement in conf.DEPARTEMENT_SEARCH:
        payload = {"region": "", "departement": ""}
        # loop to get the website departement information dynamically
        for info in conf.DEPARTEMENT_INFORMATION:
            if departement == info["departement"]:
                payload["region"] = info["websiteRegion"]
                payload["departement"] = info["websiteDepartement"]

                offerList = []
                # loop to get the right item to buy
                for item in conf.ITEM_TO_BUY:
                    if item == "Bureaux":  # add "bureaux" to the search
                        payload["rubrique_imo"] = "52"

                    # get the number max of page for each departement
                    r = requests.get(conf.URL_NEED, params=payload)
                    soup = BeautifulSoup(r.text, features="html.parser")
                    page_max = soup.find(class_="pagination__center__right")

                    if page_max is not None:
                        for i in range(1, int(page_max.text.strip()) + 1):
                            payload["page"] = i

                            r = requests.get(conf.URL_NEED, params=payload)
                            soup = BeautifulSoup(
                                r.text, features="html.parser")

                            # get all titles from the html of one page
                            titlesHtml = soup.find_all(
                                class_="offer-card__header__title")
                            titleList = []
                            for title in titlesHtml:
                                if title.text.strip() != "":
                                    titleList.append(title.text.strip())
                                else:
                                    titleList.append(None)

                            # get all urls from the html of one page
                            offerHref = soup.find_all(
                                'a', class_="offer-card-list")
                            hrefList = []
                            for offer in offerHref:
                                if offer.get('href') != "":
                                    hrefList.append(offer.get('href'))
                                else:
                                    hrefList.append(None)

                            # get all prices and surfaces from the html of one page
                            offerHighlights = soup.find_all(
                                class_="offer-highlights")
                            priceList = []
                            surfaceList = []
                            for highlight in offerHighlights:
                                badges = highlight.find_all(class_="badge")
                                for badge in badges:
                                    badgeSpans = badge.find_all('span')
                                    isPrice = False
                                    isSurface = False
                                    for span in badgeSpans:
                                        if span.string.strip() == "Prix de vente":
                                            isPrice = True
                                        elif span.string.strip() == "Surface":
                                            isSurface = True
                                    if badge.span.string.strip() == "Prix de vente" and isPrice:
                                        priceBadge = badge.find(
                                            class_="badge__content__inner").text.strip().replace("€", "").replace(" ", "")
                                        priceList.append(int(priceBadge))
                                    else:
                                        priceList.append(None)
                                    if badge.span.string.strip() == "Surface" and isSurface:
                                        surfaceBadge = badge.find(
                                            class_="badge__content__inner").text.strip().replace("m²", "").replace(" ", "")
                                        surfaceList.append(int(surfaceBadge))
                                    else:
                                        surfaceList.append(None)

                            for j in range(0, len(titleList)):
                                offerDisplay = {
                                    "title": "", "url": "https://www.cessionpme.com", "price": 0, "surface": 0}
                                offerDisplay["title"] = titleList[j]
                                offerDisplay["url"] += hrefList[j]
                                offerDisplay["price"] = priceList[j]
                                offerDisplay["surface"] = surfaceList[j]
                                offerList.append(offerDisplay)

                # insert information into the table offer from DB and get logs
                for i in range(0, len(offerList)):
                    try:
                        cur.execute(
                            """INSERT INTO offer (title, url, price, surface) VALUES (%(title)s, %(url)s, %(price)s, %(surface)s);""", {"title": offerList[i]["title"], "url": offerList[i]["url"], "price": offerList[i]["price"], "surface": offerList[i]["surface"]})
                        logging.info(
                            "L'ajout est un succès pour l'offre : %s", offerList[i]["title"])
                    except Exception as e:
                        logging.error("Erreur lors de l'ajout SQL pour l'offre %(offre)s : %(error)s", {
                                      "offre": offerList[i]["title"], "error": str(e)})

                # stock the result into json files
                if departement == "33":
                    with open("scrap/datas/resultats_33.json", "w") as result:
                        json.dump(offerList, result)
                elif departement == "64":
                    with open("scrap/datas/resultats_64.json", "w") as result:
                        json.dump(offerList, result)

                # try to get the table into the log
                try:
                    cur.execute("SELECT * FROM offer;")
                    tableOject = cur.fetchall()
                    logging.info("Ci suis la table offer : %s", tableOject)
                except:
                    conn.rollback()

    conn.commit()
    cur.close()
    conn.close()


main()
