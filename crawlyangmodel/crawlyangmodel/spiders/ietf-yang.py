import scrapy
import sys, os
from crwalyangmodel.items import YangModelItem

root_url = "https://datatracker.ietf.org"

class IetfMainPageSpider(scrapy.Spider):
    name = "ietf-yang"
    allowed_domains = ["ietf.org"]
    start_urls = [
        "https://datatracker.ietf.org/wg/"
    ]

    def parse(self, response):
        area_names = response.css("h2").xpath("text()").extract()
        areas = response.css(".table-condensed")
        for index,value in enumerate(areas):
            for index2, wg_item in enumerate(value.xpath("tbody/tr")):
                wg_name = wg_item.xpath("td[3]/text()").extract()[0]
                wg_relative_link = wg_item.xpath("./td[1]/a/@href").extract()[0]
                args = {
                        "url"       : root_url + wg_relative_link,
                        "callback"  : self.parse_wg_page,
                        "meta"      : {"area":area_names[index], "wg":wg_name}
                }
                yield scrapy.Request(**args)

    def parse_wg_page(self, response):
        tables = response.css(".table-condensed")
        for index, table in enumerate(tables):
            artifacts = table.xpath("tbody/tr")
            for index, artifact in enumerate(artifacts):
                condition = artifact.xpath("td[3]/span[2]/span/text()").extract()
                if ( len(condition) > 0 and condition[0] == u"\u262f"):
                    short_url = artifact.xpath("td[2]/div/a/@href").extract()[0]
                    name = artifact.xpath("td[2]/div/b/text()").extract()[0]
                    self.artifact_name = name
                    args = {
                            "url"       : root_url+short_url,
                            "callback"  : self.parse_artifact_page,
                            "meta"      : {"area": response.meta["area"], "wg":response.meta["wg"], "model_name": name}
                    }
                    yield scrapy.Request(**args)

    def parse_artifact_page(self, response):
        url = None
        for i in [4,5,6]:
            text = response.css("table").xpath("tbody/tr[%d]/td[2]/a[1]/text()" %(i)).extract()
            if (len(text) == 0 or "".join(text).strip().find("plain text") == -1):
                continue
            links = response.css("table").xpath("tbody/tr[%d]/td[2]/a[1]/@href" %(i)).extract()
            if (len(links) != 0):
                url = links[0]
                break

        args = {
                "area"      : response.meta["area"],
                "wg"        : response.meta["wg"],
                "title"      : response.meta["model_name"],
                "url"       : url
        }
        yield scrapy.Request(url, self.parse_artifact)
        #return YangModelItem(**args)

    def parse_artifact(self, response):
        #import pdb;pdb.set_trace()
        with open("tmp.txt","wb") as file:
            file.write(response.body)
            file.close()


        from crwalyangmodel.xym import xym
        #print(xym)

        extracted_models = xym("tmp.txt","./","./", False, False, 0)
        os.remove("tmp.txt")
        print(extracted_models)






