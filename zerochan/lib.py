import json
import re
import os
from typing import List
import urllib.request
import shutil

import requests
from bs4 import BeautifulSoup

from .c_exceptions import NoPicturesFound
from .dtypes import (
    PictureSize, ZeroChanCategory,
    ZeroChanImage, ZeroChanPage, SortBy
)


class ZeroChan:
  WEBSITE_URL = "https://www.zerochan.net"

  # TODO: filter by image size by pixel, alt and other

  def __init__(self, dir):
    self._search = ""
    self._page = 1  # Should equal to start_page
    self._end_page = 1
    self._sort_by = SortBy.LAST
    self._size = PictureSize.ALL_SIZES
    self._force_overwrite = True
    self._filled_link = False
    self._session = requests.Session()
    self._session.cookies.set("z_lang", "en")
    self._session.headers = {
        "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"
    }
    self._req_args = {}
    self._links = []
    self._max_page = -1
    self._root_dir = dir or './output'
    self._dir = self._root_dir + '/' + self._search

    if not os.path.exists(self._dir):
      print("Creating folder", self._dir)
      os.makedirs(self._dir)
    print("Output folder", self._dir)

  def size(self, size: PictureSize) -> 'ZeroChan':
    self._size = size
    return self

  def set_filled_links(self, val):
    self._filled_link = val
    return self

  def set_force_overwrite(self, val):
    self._force_overwrite = val
    return self

  def sort(self, sort_by: SortBy) -> 'ZeroChan':
    self._sort_by = sort_by
    return self

  def page(self, page_num: int) -> 'ZeroChan':
    self._page = page_num
    return self

  def end_page(self, page_num: int) -> 'ZeroChan':
    self._end_page = page_num
    return self

  def search(self, title: str) -> 'ZeroChan':
    self._search = title
    return self

  def add_links(self, links):
    self._links.extend(links)
    return self

  def add_link(self, link):
    self._links.append(link)
    return self

  def authorize(self, z_hash: str, z_id: str):
    self._session.cookies.update(dict(
        z_hash=z_hash,
        z_id=z_id
    ))
    return self

  def request_params(self, req_params):
    self._req_args.update(req_params)
    return self

  def get_links(self):
    return self._links

  def _get_soup(self, page, imgUrl) -> BeautifulSoup:
    self._req_args.update(dict(
        p=self._page if page is None or page < 0 else page,
        s=self._sort_by,
        d=int(self._size)
    ))
    res = self._session.get(
        imgUrl or f"{self.WEBSITE_URL}/{self._search}",
        params=self._req_args,
    )
    # print("Get from", res.request.url, res.request.path_url)

    if (res.status_code >= 400):
      raise Exception(
          f"Error with status: {res.status_code}. Message: {res.text}")
    return BeautifulSoup(res.content, "html.parser")

  def category(self) -> ZeroChanCategory:
    soup = self._get_soup()
    content_el = soup.find("script", {"type": "application/ld+json"})
    if content_el is None:
      raise NoPicturesFound
    page_data = json.loads("".join(content_el.contents))
    menu = soup.find("div", dict(id="menu"))
    # parsing description
    p_tags = menu.find_all("p")
    description = p_tags[1].text.replace("\r\n", "")
    return ZeroChanCategory(
        name=page_data.get("name"),
        image=page_data.get("image"),
        type=page_data.get("@type"),
        description=description
    )

  def _parse_pics(self, pics_soup: BeautifulSoup) -> List[ZeroChanImage]:
    images = []
    for pic in pics_soup.find_all("li"):
      title = pic.a.img.get("title")
      splitted_title = title.split(" ")
      size = int(splitted_title[1][:-2])  # remove "kb" chars
      # split by x and convert to int
      height, width = map(int, list(splitted_title[0].split("x")))

      if "multiple" in pic.get("class"):
        links = self.process_image_page_link(
            self.WEBSITE_URL + pic.a.get("href"))
        for link in links:
          images.append(
              ZeroChanImage(title=title, url=link,
                            height=height, width=width, kbsize=size, multi=True)
          )

        continue

      pic_download_el = pic.p.a
      if pic_download_el.img:
        download_url = pic.p.a.get("href")
        if not download_url.startswith("https"):
          continue
        images.append(
            ZeroChanImage(title=title, url=download_url,
                          height=height, width=width, kbsize=size)
        )
      else:
        elms = pic_download_el.parent.find_all("a")
        for elm in elms:
          download_url = elm.get("href")
          if not download_url.startswith("https"):
            continue

          images.append(
              ZeroChanImage(title=title, url=download_url,
                            height=height, width=width, kbsize=size)
          )
    return images

  def pics(self):
    return self.pics_in_page(self._page)

  def pics_in_page(self, page) -> ZeroChanPage:
    current_page = page or self._page

    soup = self._get_soup(current_page, None)
    pics_soup = soup.find("ul", dict(id="thumbs2"))

    if pics_soup is None:
      raise NoPicturesFound
    imgs = self._parse_pics(pics_soup)

    # Setting page and maxpage to 1 if random mode chosen
    if self._sort_by == SortBy.RANDOM:
      page = 1
      max_page = 1
    else:
      paginator_el = soup.find("nav", {"class": "pagination"})
      str_list = paginator_el.text.strip().replace("\t", " ").split(" ")
      if current_page == 1:
        page = int(str_list[1])
        # max_page = int(str_list[3])
        max_page = int(re.search(r'\d+', str_list[3]).group())
      else:
        page = int(str_list[2])
        max_page = int(re.search(r'\d+', str_list[4]).group())
    return ZeroChanPage(
        images=imgs,
        page=page,
        max_page=max_page
    )

  def collect_links(self):
    cur_page = self._page
    end_page = self._end_page or self._max_page or -1

    sync_max_page_end_page = True
    if self._end_page > self._page:
      sync_max_page_end_page = False

    print(f"Start collecting links from page {cur_page}")

    while cur_page <= end_page or end_page == -1:
      data = self.pics_in_page(cur_page)

      for img in data.images:
        self.add_link(img.url)

      if self._max_page == -1 or self._max_page < data.max_page:
        print(f"Set max_page of search {self._search} to {data.max_page}")
        self._max_page = data.max_page
        if sync_max_page_end_page:
          print(f"Synching end page to {data.max_page}")
          end_page = data.max_page

      print(
          f"Added {len(data.images)} to urls. Page {cur_page}/{end_page}")

      cur_page += 1

    print(
        f"Total Images: {len(self.get_links())}. Start Page: {self._page}. Page: {end_page}. Max Page: {self._max_page}")

    self.set_filled_links(True)

    return self.get_links()

  def verify_response(self, r, raiseException=False):
    if not r.ok:
      print(f"Error downloading {r.url}. Error: {r}")
      if raiseException:
        raise f"Error downloading {r.url}. Error: {r}"

  def download_image_with_urllib(self, filepath, link):
    urllib.request.urlretrieve(link, filepath)

  def download_file_with_shutil(self, filepath, link):
    with requests.get(link, stream=True) as r:
      # r.raise_for_status()
      with open(filepath, mode='wb') as f:
        shutil.copyfileobj(r.raw, f)

  def download_image(self, filepath, link):
    with self.session.get(link, stream=True) as r:
      # r.raise_for_status()
      self.verify_response(r)
      with open(filepath, 'wb') as f:
        for chunk in r.iter_content(8192):
          if not chunk:
            break
          f.write(chunk)

  def download_images(self):
    if (self._filled_link == False):
      self.collect_links()

    p = re.compile(
        r'(?<=https:\/\/static\.zerochan\.net\/)[\s\S]*\.full\.[\d]*?\.(?:jpg|png|gif)')

    downloaded = 0
    skip = 0
    for idx, link in enumerate(self.get_links()):
      name = p.search(str(link)).group(0)
      filepath = self._dir + '/' + name

      if (self._force_overwrite == False and os.path.exists(self._dir + '/' + name)):
        skip += 1
        continue

      if idx % 10 == 0:
        print(f"Downloaded: {downloaded}/{len(self.get_links())}")
        print(f"Skipped: {skip}/{len(self.get_links())}")
        print(f"Remaining: {len(self.get_links()) - skip - downloaded}")
        print(f"Current downloading index {idx}. Name: {name}")

      # self.download_image(self.dir + '/' + name, link)
      self.download_image_with_urllib(filepath, link)
      # self.download_image_with_urllib(self.dir + '/' + name, link)

      downloaded += 1

    print("Finished!")

  def collect_from_id(self, ids):
    for id in ids:
      page_link = f"{self.WEBSITE_URL}/{id}"
      # print(page_link)
      self.add_links(self.process_image_page_link(page_link))
    self.set_filled_links(True)
    return self.get_links()

  def process_image_page_link(self, page_link):
    soup = self._get_soup(1, page_link)

    link_images = []
    # Get all small thumbs
    thumbs = soup.find_all("ul", {"class": "smallthumbs"})

    if len(thumbs) == 0:
      # If no thumbs (no other image for image page)
      link_images.append(self.get_link_full(soup))
    else:
      for thumb in thumbs[0].find_all("li"):
        href = thumb.a.get("href")
        thumb_soup = self._get_soup(1, f"{self.WEBSITE_URL}{href}")
        link_images.append(self.get_link_full(thumb_soup))

    return filter(lambda item: item is not None, link_images)

  def get_link_full(self, soup):
    image_link = soup.find_all("a", {"class": "preview"})
    image_link2 = image_link[0].img

    link = image_link[0].get("href") or image_link2.get("src")
    return link if link.startswith("https") else None
