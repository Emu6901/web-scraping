import time
import pandas as pd
import csv
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains


class CFG:
    url = r"https://www.goodreads.com/search?q=Higashino+Keigo&qid=SvDlDs0jLd"
    book_file = "data/book.csv"
    comment_file = "data/comment.csv"
    reply_file = "data/reply.csv"
    book_headers = [
        "ID sách",
        "Tên sách",
        "Số sao đánh giá",
        "Số người đánh giá",
        "Số người review",
        "Tóm tắt",
        "Ảnh bìa",
        "Tác giả",
    ]
    comment_headers = [
        "ID bình luận",
        "Tên người bình luận",
        "Ngày bình luận",
        "Nội dung",
        "Số sao",
        "Số like",
        "ID sách",
    ]
    reply_headers = [
        "ID bình luận",
        "Tên người bình luận",
        "Ngày bình luận",
        "Nội dung",
    ]
    book_id = 0
    MAX_COMMENT_NUMBER = 35
    MAX_REPLY_NUMBER = 10


class Utilily:
    @staticmethod
    def try_except_find_elements(container, by, value, default_return=""):
        try:
            element = container.find_elements(by=by, value=value)
            return element
        except Exception as e:
            return default_return

    @staticmethod
    def try_except_find_element(
        container, by, value, default_return="", get_text=False, attribute = None
    ):
        try:
            element = container.find_element(by=by, value=value)
            if get_text:
                return element.text
            elif attribute != None:
                return element.get_attribute(attribute)
            return element
        except Exception as e:
            return default_return


class Setup:
    def setup_driver():
        chrome_options = Options()
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--start-maximized")
        # chrome_options.add_argument("--headless")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        return webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=chrome_options
        )

    def setup_writer(filename, headers):
        file = open(filename, "w", newline="", encoding="utf-8")
        writer = csv.DictWriter(
            file, delimiter=",", lineterminator="\n", fieldnames=headers
        )
        writer.writeheader()
        return writer


class Find:
    def find_next_page(driver):
        next_page = driver.find_element(by=By.CLASS_NAME, value="next_page")
        if next_page.tag_name == "a":
            return next_page
        else:
            return False

    def find_books(driver):
        rows = driver.find_elements(by=By.TAG_NAME, value="tr")
        elements = [row.find_element(by=By.TAG_NAME, value="a") for row in rows]
        if elements:
            return elements
        else:
            return False

    def find_comment_ids():
        comments = CFG.driver.find_elements(by=By.CLASS_NAME, value="review")
        elements = [comment.get_attribute("id") for comment in comments]
        return elements

    def find_reply_ids():
        replies = CFG.driver.find_elements(by=By.CLASS_NAME, value="comment")
        elements = [reply.get_attribute("id") for reply in replies]
        return elements


class GetInformation:
    def extract_book(book_container):
        # ['ID sách','Tên sách', 'Số sao đánh giá', 'Số người đánh giá', 'Số người review', 'Tóm tắt', 'Ảnh bìa', 'Tác giả']
        bookTitle = book_container.find_element(by=By.ID, value="bookTitle").text
        ratingValue = book_container.find_element(
            by=By.XPATH, value='//*[@id="bookMeta"]/span[2]'
        ).text
        ratingCount = book_container.find_element(
            by=By.XPATH, value='//*[@id="bookMeta"]/a[2]'
        ).text
        reviewCount = book_container.find_element(
            by=By.XPATH, value='//*[@id="bookMeta"]/a[3]'
        ).text
        description = book_container.find_element(
            by=By.ID, value="descriptionContainer"
        ).text.replace("\n", " ")
        # coverImage = book_container.find_element(
        #     by=By.ID, value="coverImage"
        # ).get_attribute("src")
        coverImage = Utilily.try_except_find_element(
            container=book_container,
            by=By.ID,
            value="coverImage",
            default_return="",
            attribute= 'src'
        )
        author = book_container.find_element(
            by=By.XPATH, value='//*[@id="bookAuthors"]/span[2]'
        ).text
        print(
            "Book",
            bookTitle,
            ratingValue,
            ratingCount,
            reviewCount,
            description,
            coverImage,
            author,
            sep="\n",
        )
        CFG.book_writer.writerow(
            {
                CFG.book_headers[0]: CFG.book_id,
                CFG.book_headers[1]: bookTitle,
                CFG.book_headers[2]: ratingValue,
                CFG.book_headers[3]: ratingCount,
                CFG.book_headers[4]: reviewCount,
                CFG.book_headers[5]: description,
                CFG.book_headers[6]: coverImage,
                CFG.book_headers[7]: author,
            }
        )

    def extract_comment(comment_container, comment_id):
        # ['ID bình luận' ,'Tên người bình luận', 'Ngày bình luận', 'Nội dung', 'Số sao', 'Số like', 'ID sách']
        author = comment_container.find_element(
            by=By.CLASS_NAME, value="userReview"
        ).text
        reviewDate = comment_container.find_element(
            by=By.CLASS_NAME, value="dtreviewed"
        ).text
        reviewText = Utilily.try_except_find_element(
            container=comment_container,
            by=By.CLASS_NAME,
            value="reviewText",
            get_text=True,
        )
        staticStar = len(comment_container.find_elements(by=By.CLASS_NAME, value="p10"))
        likesCount = Utilily.try_except_find_element(
            container=comment_container,
            by=By.ID,
            value="like_count_{0}".format(comment_id),
            default_return="0 likes",
            get_text=True,
        )
        print(
            "Comment", author, reviewDate, reviewText, staticStar, likesCount, sep="\n"
        )
        CFG.comment_writer.writerow(
            {
                CFG.comment_headers[0]: comment_id,
                CFG.comment_headers[1]: author,
                CFG.comment_headers[2]: reviewDate,
                CFG.comment_headers[3]: reviewText,
                CFG.comment_headers[4]: staticStar,
                CFG.comment_headers[5]: likesCount,
                CFG.comment_headers[6]: CFG.book_id,
            }
        )

    def extract_reply(reply_id, comment_id):
        # ["ID bình luận","Tên người bình luận","Ngày bình luận","Nội dung"]
        reply = CFG.driver.find_element(by=By.ID, value=reply_id)
        replyAuthor = reply.find_element(by=By.CLASS_NAME, value="commentAuthor").text
        replyTime = reply.find_element(by=By.CLASS_NAME, value="right").text
        replyText = reply.find_element(by=By.CLASS_NAME, value="reviewText").text
        print("Reply", comment_id, replyAuthor, replyTime, replyText, sep="\n")
        CFG.reply_writer.writerow(
            {
                CFG.reply_headers[0]: comment_id,
                CFG.reply_headers[1]: replyAuthor,
                CFG.reply_headers[2]: replyTime,
                CFG.reply_headers[3]: replyText,
            }
        )


def crawl():
    CFG.driver = Setup.setup_driver()
    CFG.driver.delete_network_conditions()
    CFG.driver.set_network_conditions(
        offline=False,
        latency=5,  # additional latency (ms)
        download_throughput=500 * 1024,  # maximal throughput
        upload_throughput=500 * 1024,  # maximal throughput
    )
    CFG.driver.delete_all_cookies()
    CFG.driver.get(CFG.url)
    CFG.wait = WebDriverWait(CFG.driver, 20)
    CFG.action = ActionChains(CFG.driver)
    CFG.book_writer = Setup.setup_writer(CFG.book_file, CFG.book_headers)
    CFG.comment_writer = Setup.setup_writer(CFG.comment_file, CFG.comment_headers)
    CFG.reply_writer = Setup.setup_writer(CFG.reply_file, CFG.reply_headers)

    while True:
        books = CFG.wait.until(Find.find_books)
        book_index = 0
        while book_index < len(books):
            book = books[book_index]
            book_index += 1
            CFG.book_id += 1
            CFG.action.move_to_element(book).move_by_offset(-40, 0).click().perform()
            book.click()
            time.sleep(2)
            book_container = CFG.driver.find_element(
                by=By.CLASS_NAME, value="leftContainer"
            )
            GetInformation.extract_book(book_container)

            comment_ids = Find.find_comment_ids()
            comment_index = 0
            while comment_index < min(len(comment_ids), CFG.MAX_COMMENT_NUMBER):
                comment_id = comment_ids[comment_index]
                comment_index += 1
                see_review = CFG.driver.find_element(
                    by=By.XPATH,
                    value='//*[@id="{0}"]/div[1]/div[1]/a'.format(comment_id),
                )
                CFG.action.move_to_element(see_review).move_by_offset(
                    -see_review.location["x"] + 1, 0
                ).click().perform()
                CFG.action.move_to_element(see_review).click(see_review).perform()
                time.sleep(2)
                comment_container = CFG.driver.find_element(
                    by=By.CLASS_NAME, value="leftContainer"
                )
                GetInformation.extract_comment(comment_container, comment_id)

                reply_ids = Find.find_reply_ids()
                reply_index = 0
                while reply_index < min(len(reply_ids), CFG.MAX_REPLY_NUMBER):
                    reply_id = reply_ids[reply_index]
                    reply_index += 1
                    GetInformation.extract_reply(reply_id, comment_id)

                CFG.driver.back()
                time.sleep(2)

            CFG.driver.back()
            time.sleep(1)
            books = CFG.wait.until(Find.find_books)
            time.sleep(1)

        next_page = Find.find_next_page(CFG.driver)
        if next_page:
            try:
                next_page.click()
            except:
                print(next_page.location)
                CFG.action.move_to_element(next_page).move_by_offset(
                    -40, 0
                ).click().perform()
                next_page.click()
                time.sleep(2)
        else:
            break


if __name__ == "__main__":
    crawl()
