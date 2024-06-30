import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import re

class BayutSpider(CrawlSpider):
    name = 'bayut_spider'
    allowed_domains = ['bayut.com']
    start_urls = ['https://www.bayut.com/to-rent/property/dubai/']

    rules = (
        Rule(LinkExtractor(allow=r'/property/details-\d+\.html'), callback = 'parse_property'),
        Rule(LinkExtractor(restrict_css='a._95dd93c1[title="Next"]'), follow=True),
    )

    def parse_property(self, response):

        breadcrumb_elements = response.xpath('//div[@class="_3624d529"]//descendant-or-self::*')

        breadcrumb_text = []
        seen_elements = set()
        for element in breadcrumb_elements:
            if element.xpath('self::a'):
                text = element.xpath('span[@aria-label="Link name"]/text()').get()
                if text and text not in seen_elements:
                    breadcrumb_text.append(text.strip())
                    seen_elements.add(text)
            elif element.xpath('self::div[@aria-label="Link delimiter"]'):
                breadcrumb_text.append('>')
            elif element.xpath('self::span[@aria-label="Link name"]'):
                text = element.xpath('text()').get()
                if text and text not in seen_elements:
                    breadcrumb_text.append(text.strip())
                    seen_elements.add(text)

        # Join all extracted text into a single string
        breadcrumb_text = ' '.join(breadcrumb_text)

        temp_ameneties = response.xpath('//div[@class="_91c991df"]//span[@class="_7181e5ac"]/text()').getall()
        pattern = r": \d+"
        cleaned_ameneties = [elem for elem in temp_ameneties if not re.search(pattern, elem)]

        data = {
            'reference_no': response.css('span._2fdf7fc5[aria-label="Reference"]::text').get().strip(),
            'purpose': response.css('span._2fdf7fc5[aria-label="Purpose"]::text').get().strip(),
            'type': response.css('span._2fdf7fc5[aria-label="Type"]::text').get().strip(),
            'added_on': response.css('span._2fdf7fc5[aria-label="Reactivated date"]::text').get().strip(),
            'furnishing': response.css('span._2fdf7fc5[aria-label="Furnishing"]::text').get().strip(),
            'price': {
                'currency': response.css('div._2923a568 span[aria-label="Currency"]::text').get().strip(),
                'amount': response.css('div._2923a568 span[aria-label="Price"]::text').get().strip()
            },
            'location': response.css('div.e4fd45f0[aria-label="Property header"]::text').get().strip(),
            'bed_bath_size': {
                'bedrooms': response.css('span._140e6903::text').re_first(r'(\d+)'),
                'bathrooms': response.css('span._140e6903::text').re_first(r'(\d+)'),
                'size': response.css('span._140e6903 > span::text').get().strip()
            },
            # 'permit_number':  response.css('div._948d9e0a._1cc8fb85._95d4067f > ul._1deff3aa > li:nth-child(1) > span._2fdf7fc5[aria-label="Permit Number"]::text').get().strip(),
            'agent_name': response.css('span.d8185451[aria-label="Agent name"]::text').get().strip(),
            'image_url': response.css('link[rel="preload"][as="image"]::attr(href)').extract_first(),
            'breadcrumbs': breadcrumb_text,
            'amenities': cleaned_ameneties,
            'description': response.css('div[aria-label="Property description"] span._3547dac9::text').get().strip()
        }
        yield data
