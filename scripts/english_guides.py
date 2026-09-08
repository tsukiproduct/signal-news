"""English counterparts for SIGNAL's original buying guides."""
from urllib.parse import quote
from html import escape

def build(docs, frame, origin):
    def ad(title, text, query):
        url = 'https://www.amazon.co.jp/s?k=' + quote(query) + '&tag=tsukiproduct-22'
        return f'<section class="rail-block"><p class="translation">Advertisement / Amazon Associate</p><h2>{title}</h2><p>{text}</p><a data-signal-event="affiliate_click" data-offer="amazon" href="{escape(url)}" target="_blank" rel="sponsored noopener noreferrer">Browse Amazon Japan</a><p class="translation">Product search, not a tested recommendation or ranking. Check prices, stock, language and compatibility at the retailer.</p></section>'
    video = '''<p class="answer">Estimate the cost of usable shots, not just the number of generations in a subscription. Rejected outputs are part of production cost.</p>
<h2>Cost per usable shot</h2><p>Enter the plan’s cost and your own trial results. Defaults are illustrative, not performance estimates.</p>
<form id="budget-form"><label>Total spend, including top-ups (JPY)<input name="cost" type="number" min="0" max="10000000" value="3000" required></label><label>Generations covered by that spend<input name="runs" type="number" min="1" max="1000000" step="1" value="100" required></label><label>Usable outputs in your trial (%)<input name="yield" type="number" min="0.1" max="100" step="0.1" value="20" required></label><label>Shots needed for one finished video<input name="cuts" type="number" min="1" max="100000" step="1" value="12" required></label><output id="budget-result" aria-live="polite"></output><p id="budget-detail"></p></form>
<p>This estimate assumes comparable generation settings. Editing, music and upscaling are excluded. Include unused credits in total spend. Inputs stay on this device.</p>
<h2>Test the same short scene before subscribing</h2><ol><li>Choose a scene you actually need: a person moving, a camera move or a product shot.</li><li>Set acceptance criteria first. Check hands, text and character consistency.</li><li>Record usable shots and enter the results above. Small samples can produce unstable estimates.</li></ol>
<h2>Check the official plan</h2><p>Check credit use by duration and resolution, retries, watermarks, exports, expiration and upfront annual charges. For public or commercial work, check the plan’s usage terms.</p><p><a href="https://runwayml.com/pricing">Runway pricing</a> · <a href="https://www.adobe.com/products/firefly/plans.html">Adobe Firefly plans</a></p>
<h2>If generation is not the problem</h2><p>More credits will not fix unclear composition or shots that run too long. Review your storyboard and editing first.</p>'''
    video += ad('Learn composition and shot sequencing','Check sample pages for practical storyboarding and editing examples. This search is on Amazon Japan.','映像制作 絵コンテ カット割り')
    local = '''<p class="answer">Start with the model you need, then check its requirements. An “AI PC” label alone does not establish suitability for text, image or video work.</p>
<h2>Before buying hardware</h2><ol><li>Choose one model. Write down its name, size, task and software.</li><li>Check the publisher’s OS, GPU, memory and storage requirements. GPU memory and system memory are different.</li><li>Try a smaller model on your current machine. Being able to launch it differs from getting acceptable response times.</li><li>Identify the bottleneck. Storage capacity and computation memory require different remedies.</li></ol><p>Requirements vary by model and software. Start with the <a href="https://lmstudio.ai/docs/app/system-requirements">official LM Studio requirements</a> if that is your intended software.</p>
<h2>Match the problem to a test</h2><dl><dt>Will not launch</dt><dd>Check OS, model format and memory requirements.</dd><dt>Slow responses</dt><dd>Test a smaller model or different settings on your actual task.</dd><dt>No storage space</dt><dd>Review unused files and available capacity.</dd><dt>Unsure about buying</dt><dd>Compare monthly use, cloud costs and hardware replacement costs.</dd></dl>'''
    local += ad('Only if you need more storage','Check ports, real transfer speeds and capacity. An external SSD does not add GPU memory; do not buy one to solve insufficient compute memory.','外付け SSD USB')
    learning = '''<p class="answer">Decide what you want to do after reading. A narrow learning goal makes a book easier to evaluate than trying to learn all of AI at once.</p>
<h2>Match contents to your goal</h2><dl><dt>AI at work</dt><dd>Look for problems close to your job, failure examples and output verification. A single operation may be better answered by official documentation.</dd><dt>Machine learning</dt><dd>Check prerequisite mathematics, code environment, exercises and solutions. Confirm your Python and mathematics foundations first.</dd><dt>Images and video</dt><dd>Look for composition, lighting, editing and production process. Avoid rushing into a tool-specific manual before choosing a tool.</dd></dl>
<h2>Three checks before buying</h2><ol><li>Read sample pages to assess difficulty and writing style.</li><li>Check product version and publication date. Even a recent book may show an outdated interface.</li><li>Review the publisher’s errata and sample code. Libraries and official tutorials are alternatives.</li></ol>'''
    learning += ad('Find examples close to your work','Look for relevant chapters and exercises instead of rankings. Check the book language.','生成AI ビジネス 活用 書籍')
    learning += ad('Learn by running code','Check prerequisites and the execution environment before choosing an exercise-based book.','Python 機械学習 入門 演習')
    guides = [('video-budget','Estimate the cost of a finished AI video',video),('local-ai','Before buying a PC for local AI',local),('ai-learning','Choose an AI book by goal and contents',learning)]
    for slug,title,body in guides:
        rel = f'guides/{slug}.html'
        target = docs/'en'/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(frame('en',rel,title,title,f'<main id="main" class="wrap article"><p class="kicker">SIGNAL / FIELD GUIDE</p><h1>{title}</h1>{body}<p><a href="/en/guides.html">All buying guides</a></p></main>'))
    cards = ''.join(f'<section class="rail-block"><h2><a data-signal-event="guide_open" href="/en/guides/{slug}.html">{title}</a></h2></section>' for slug,title,_ in guides)
    (docs/'en/guides.html').write_text(frame('en','guides.html','Before you buy','Practical checks before paying for AI tools, hardware or books.',f'<main id="main" class="wrap article"><h1>Before you buy.</h1><p>Start with your task, check constraints and try the no-purchase option.</p>{cards}</main>'))
    for rel in ['guides.html'] + [f'guides/{slug}.html' for slug,_,_ in guides]:
        target = docs/rel
        original = target.read_text()
        if 'hreflang="en"' not in original:
            original = original.replace('</head>',f'<link rel="alternate" hreflang="ja" href="{origin}/{rel}"><link rel="alternate" hreflang="en" href="{origin}/en/{rel}"></head>')
            original = original.replace('</header>',f'<a href="/en/{rel}" lang="en" hreflang="en">English</a></header>')
            target.write_text(original)
