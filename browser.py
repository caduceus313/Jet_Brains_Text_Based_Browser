from os import mkdir, makedirs, path
from collections import deque
from bs4 import BeautifulSoup
from colorama import init, Fore
import argparse
import requests

init()

# handles command line argument parsing
parser = argparse.ArgumentParser(description='Text based web browser')
parser.add_argument('dirname', nargs='?', default='temp')
args = parser.parse_args()


class Browser:
    def __init__(self, dir_name):
        self.dir_name = dir_name
        self.state = 'begin'
        self.url_stack = deque()

    # create directory from command line if it doesn't exist
    def make_dir(self):
        if not path.exists(self.dir_name):
            makedirs(self.dir_name)
        self.state = 'run'

    def cache_page(self, page, url):
        url = url.replace('http://', '').replace('https://', '').rsplit('.', 1)[0]  # removes prefix and .com suffix
        with open(self.dir_name + '/' + url + '.txt', 'w') as file_out:
            file_out.write(page)
        self.url_stack.append(url)

    def tag_handler(self, r_object):
        # tags = ('title', 'p', 'a', 'strong', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'dt', 'ul', 'ol', 'li')
        parents = ('p', 'ul', 'ol', 'li')
        soup = BeautifulSoup(r_object.content, 'html.parser')
        line_break = ' '
        for br in soup.select('br'):
            br.replace_with(line_break)
        # use ``unwrap`` to retrieve text from `span`-tag inside other tags
        for span_tag in soup.select('span'):
            span_tag.unwrap()
        for a_tag in soup.select('a'):
            if a_tag.get('href'):
                a_tag.insert(0, Fore.BLUE)
                a_tag.append(Fore.RESET)
            if a_tag.parent and a_tag.parent.name in parents:
                a_tag.unwrap()
        # use ``smooth`` to clean up the parse tree
        # by consolidating adjacent strings
        soup.smooth()
        text_of_page = []
        # don't need find `ul` and `ol` tags,
        # because they don't have text inside
        for tag in soup.select('p, li'):
            text: str = tag.string
            if text:
                text_of_page.append(
                    str(text).replace('\n', ' ').replace('  ', ' ').strip()
                )
        return '\n'.join(text_of_page)

    # main method to deal with user input
    def address_bar(self, url):
        if self.state == 'begin':
            self.make_dir()
        if self.state == 'run':
            if url == "exit":
                self.state = 'exit'
                return
            elif url == "back":
                if len(self.url_stack) > 1:
                    self.url_stack.pop()
                    return self.address_bar(self.url_stack.pop())
            elif path.isfile(self.dir_name + '/' + url + '.txt'):  # check if url has been cached
                with open(self.dir_name + '/' + url + '.txt', 'r') as file_in:
                    self.url_stack.append(url)
                    return file_in.read()
            elif "." not in url:
                return 'error'
            else:
                url = f"https://{url}" if not url.startswith(('https://', 'http://')) else url
                # print(url)
                r = requests.get(url)
                if r:
                    page = self.tag_handler(r)
                    self.cache_page(page, url)
                else:
                    page = f'Request failed with code: {r.status_code}'
                return page

        return 'error'


if __name__ == "__main__":
    myBrowser = Browser(args.dirname)
    while myBrowser.state != 'exit':
        print(myBrowser.address_bar(input('> ')))
