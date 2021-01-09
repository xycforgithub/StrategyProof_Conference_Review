import pdb

import scrapy


class QuotesSpider(scrapy.Spider):
    name = "gs"

    def start_requests(self):
        fin = open('raw_authorlist.txt')
        all_authors = []
        urls = []
        for line in fin:
            all_authors.append(line.strip())
            author_string = all_authors[-1].replace(' ', '+')
            urls.append('https://scholar.google.com/citations?hl=en&view_op=search_authors&mauthors={}&btnG='.format(
                author_string))
        # print('author names:', all_authors[:10])
        for url, author_name in zip(urls, all_authors):
            print('yeild results for', author_name)
            # time.sleep(random.randint(0,1))
            yield scrapy.Request(url=url, callback=self.parse, meta={'name': author_name})

    def parse(self, response):
        links = response.xpath('//a[contains(@href,"user=")]').getall()
        output_file_name = 'results.txt'
        try:
            author_name = response.meta['name']
        except:
            pdb.set_trace()
        res = 0
        with open(output_file_name, 'a+') as f:
            if len(links) == 0:
                f.write('{},None,None\n'.format(author_name))
                res = 'None'
            elif len(links) > 2:
                f.write('{},Multiple,Multiple\n'.format(author_name))
                res = 'Multiple'

            else:
                thestr = links[0]
                start_pos = thestr.find('user=') + 5
                end_pos = thestr.find('class=') - 2
                sid = thestr[start_pos:end_pos]
                link_start_pos = thestr.find('href=') + 6
                gs_link = 'https://scholar.google.com{}'.format(links[0][link_start_pos:end_pos])
                f.write('{},{},{}\n'.format(author_name, sid, gs_link))
                res = 'found'

        self.log('Finished Author {}; result={}'.format(author_name, res))
