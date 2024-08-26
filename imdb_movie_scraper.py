import csv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from concurrent.futures import ThreadPoolExecutor
import time
import random


def scroll_to_end(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def get_movie_links(url):
    driver = webdriver.Chrome(
        options=webdriver.ChromeOptions().add_argument("--headless")
    )
    driver.get(url)

    scroll_to_end(driver)

    movie_elements = driver.find_elements(
        By.CSS_SELECTOR, "div.cli-title a.ipc-title-link-wrapper"
    )
    movie_links = [elem.get_attribute("href") for elem in movie_elements]

    driver.quit()
    return movie_links


def get_cast_and_crew(driver):
    actors = []
    try:
        cast_crew_link = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Cast & crew"))
        )
        cast_crew_link.click()

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.cast_list"))
        )

        rows = driver.find_elements(By.CSS_SELECTOR, "table.cast_list tr")
        collecting = True

        for row in rows:
            row_text = row.text.strip()
            if "Rest of cast listed alphabetically" in row_text:
                collecting = False
                continue

            if collecting:
                try:
                    name_element = row.find_element(
                        By.CSS_SELECTOR, "td:nth-of-type(2) a"
                    )
                    actor_name = name_element.text.strip()
                    if actor_name:
                        actors.append(actor_name)
                except:
                    continue

    except Exception as e:
        print(f"Error processing the page {driver.current_url}: {e}")

    return actors


def get_movie_title_cast_and_rating(url):
    driver = webdriver.Chrome(
        options=webdriver.ChromeOptions().add_argument("--headless")
    )
    driver.get(url)

    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'h1[data-testid="hero__pageTitle"]')
            )
        )

        movie_title = driver.find_element(
            By.CSS_SELECTOR, 'h1[data-testid="hero__pageTitle"] span.hero__primary-text'
        ).text

        # Extract rating
        rating_element = driver.find_element(
            By.CSS_SELECTOR, "span.sc-eb51e184-1.ljxVSS"
        )
        movie_rating = float(rating_element.text)

        actors = get_cast_and_crew(driver)
    except Exception as e:
        print(f"Error processing the page {url}: {e}")
        movie_title = "Error"
        movie_rating = None
        actors = []
    finally:
        driver.quit()

    return {"title": movie_title, "rating": movie_rating, "actors": actors}


def write_headers(filename):
    with open(filename, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["Movie Title", "Rating", "Actors"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()


def write_to_csv(data, filename, mode="w"):
    with open(filename, mode, newline="", encoding="utf-8") as csvfile:
        fieldnames = ["Movie Title", "Rating", "Actors"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if mode == "w":
            writer.writeheader()  # Write header only if we're opening the file in write mode

        writer.writerow(
            {
                "Movie Title": data["title"],
                "Rating": data["rating"],
                "Actors": ", ".join(data["actors"]),
            }
        )


def main():
    main_url = "https://www.imdb.com/chart/top/"

    start_time = time.time()
    movie_links = get_movie_links(main_url)

    print(f"{len(movie_links)} links found.")

    write_headers("movies_and_actors_with_rating.csv")

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(get_movie_title_cast_and_rating, link): link
            for link in movie_links
        }
        for future in futures:
            link = futures[future]
            try:
                data = future.result()
                print(f"{link} {data['title']}")
                print(f"Rating: {data['rating']}")
                print(f"Actors: {', '.join(data['actors'])}")
                print("=======================")
                # Save each movie's data to CSV immediately
                write_to_csv(data, "movies_and_actors_with_rating.csv", mode="a")
                time.sleep(random.uniform(5, 7))
            except Exception as e:
                print(f"Error processing the page {link}: {e}")

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.2f} sec.")


if __name__ == "__main__":
    main()
