import scrapy


class ForumSpider(scrapy.Spider):
    name = "forum"
    allowed_domains = ["dgcoursereview.com"]

    start_urls = [
        "https://dgcoursereview.com/forums/technique-strategy.52/"
    ]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": "Mozilla/5.0 (compatible; ResearchBot/1.0)",
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 1,
    }

    def parse(self, response):

        # Find every thread on the current forum page
        """
        for thread in response.css("div.structItem--thread"):

            link = thread.css(".structItem-title a::attr(href)").get()

            title = thread.css(".structItem-title a::text").get()
            title = title.strip() if title else None

            yield response.follow(
                link,
                callback=self.parse_thread,
                meta={
                    "thread_title": title,
                    "thread_url": response.urljoin(link),
                }
            )
        """
        thread = response.css("div.structItem--thread")[9]
        link = thread.css(".structItem-title a::attr(href)").get()
        
        title = thread.css(".structItem-title a::text").get()
        title = title.strip() if title else None
        
        yield response.follow(
            link,
            callback=self.parse_thread,
            meta={
                "thread_title": title,
                "thread_url": response.urljoin(link),
            }
        )

    def parse_thread(self, response):

        for post in response.css("article.message--post"):

            author = post.css(".message-name .username")

            timestamp = post.css(
                ".message-attribution-main time::attr(datetime)"
            ).get()

            post_url = post.css(
                ".message-attribution-main a::attr(href)"
            ).get()

            content = post.css(
                ".bbWrapper"
            ).xpath(
                "string(.)"
            ).get()

            yield {
                "thread_title": response.meta["thread_title"],
                "thread_url": response.url,

                "post_url": response.urljoin(post_url)
                    if post_url else None,

                "post_id": post.attrib.get("data-content", "").replace(
                "post-", ""
                ),

                "author": post.css(
                ".message-name .c_name::text"
                ).get(),

                "author_id": post.css(
                ".message-name .username::attr(data-user-id)"
                ).get(),

                "timestamp":timestamp,

                "content": content.strip()
                    if content else None,
            }