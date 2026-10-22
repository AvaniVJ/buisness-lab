from app.knowledge import chunk_sections, content_hash, parse_article, sitemap_urls

def test_content_hash_is_stable():
    assert content_hash("abc") == content_hash("abc")
    assert content_hash("abc") != content_hash("abcd")

def test_parse_article_extracts_title_text_and_image():
    html = """
    <html><head><title>Example</title></head><body>
      <nav>Navigation noise</nav><main><h1>Logo setup</h1><p>Open settings.</p>
      <img src="/images/logo.png" alt="Logo button"><h2>Save</h2><p>Click save.</p></main>
    </body></html>
    """
    result = parse_article(html, "https://example.com/article")
    assert result["title"] == "Logo setup"
    assert "Open settings." in result["content"]
    assert "https://example.com/images/logo.png" in result["content"]
    assert "Navigation noise" not in result["content"]

def test_chunk_sections_splits_long_text():
    chunks = chunk_sections([{"heading":"H","text":"Sentence. " * 300}], max_chars=100, overlap_chars=10)
    assert len(chunks) > 1
    assert all(c["heading"] == "H" for c in chunks)

def test_sitemap_filters_untrusted_hosts_and_deduplicates():
    xml = """<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://support.brilliantdirectories.com/a</loc><lastmod>2026-01-01</lastmod></url>
    <url><loc>https://evil.example/b</loc></url>
    <url><loc>https://support.brilliantdirectories.com/a</loc></url>
    </urlset>"""
    pages=sitemap_urls(xml)
    assert len(pages)==1
    assert pages[0]["url"].endswith("/a")
