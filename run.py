from zerochan import ZeroChan, PictureSize, SortBy


def init_zerochan_instance(tag, z_hash, z_id, output_dir):
  zerochan = ZeroChan(output_dir)

  zerochan.search(tag)
  zerochan.size(PictureSize.BIGGER_AND_BETTER)  # Set quality and pic size
  zerochan.sort(SortBy.POPULAR)  # Set sorting (now only popular)
  zerochan.authorize(z_hash, z_id)

  return zerochan

# Currently, if image has more than 1 children, it only download parent

if __name__ == "__main__":
  zerochan_instance = init_zerochan_instance(
      # "Tokisaki+Kurumi",
      "Fate+Testarossa",
      "2b7d878080d709aaeb171d3281354518",
      "1901546",
      './output')

  # Download
  zerochan_instance.set_force_overwrite(False)
  zerochan_instance.download_images()

  # zerochan_instance.collect_from_id([
  #     1873092,
  #     1925283,
  #     1817158,
  #     1732045,
  #     1705082,
  #     1723714,
  #     1739233,
  #     1746653,
  #     1536439,
  #     1536476,
  #     1532287,
  #     1542570,
  #     1548232,
  #     1526543,
  #     1515800,
  #     1516331,
  #     1454860,
  #     4060639,
  #     1383525,
  #     2705400,
  #     2705431,
  #     2705439,
  #     3737194,
  #     4043572,
  #     1843486,
  #     2678717,
  #     2690735,
  #     2690736,
  #     1842557,
  #     1875756,
  #     1876298,
  #     1613293,
  #     1606123,
  #     1730058,
  #     1755993,
  #     1809693,
  #     1599902,
  #     1542159,
  #     1529366,
  #     1513071,
  #     1515059,
  #     1494192,
  #     1495805,
  #     1496576,
  #     1499255,
  #     1509116,
  #     2705424,
  #     2705453,
  #     3095631,
  #     1490556,
  #     1685025,
  #     1730910,
  #     1746304,
  #     1589214,
  #     1589814,
  #     1598802,
  #     1612691,
  #     1683208,
  #     1522959,
  #     1544552,
  #     1548240,
  #     2705422,
  #     1522158,
  #     1515543,
  #     1509269,
  #     1516374,
  #     2705420,
  #     1507554,
  #     1523827,
  #     1618808
  # ])

  # zerochan_instance.download_images()

  # zerochan_instance.page(17)
  # zerochan_instance.sort(SortBy.LAST)
  # data = zerochan_instance.pics()
  # for image in data.images:
  #   print(image.url, image.multi)
    
  # print(len(data.images))