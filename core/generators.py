"""
Spidey Core — Generators (100% same as Telegram bot)
Keywords + Dorks (Normal / HQ / Country / CMS / Exposed)
Kuch nahi skip. Kuch nahi change.
"""
import itertools
import random

# ═══════════════════════════════════════════════════════════════════════════
#  PHP PARAMS — 100% same as bot
# ═══════════════════════════════════════════════════════════════════════════
PHP_PARAMS = [
    "id","pid","cid","oid","nid","sid","tid","fid","uid","cat","category","type",
    "sub","page","item","product","article","news","post","entry","record","row",
    "order","orderid","order_id","cart","item_id","product_id","invoice","invoice_id",
    "transaction","ref","user","username","userid","user_id","email","account",
    "login","token","key","hash","session","view","show","display","action","method",
    "step","tab","mode","lang","language","locale","region","sort","offset","start",
    "limit","per_page","pager","page_num","q","search","query","keyword","term","s",
    "find","filter","tag","topic","subject","file","filename","path","folder","dir",
    "name","album","gallery","image","img","photo","video","redirect","return","next",
    "url","link","back","from","callback","format","output","download","report","date",
    "year","month","day","district","country","source","src","origin","parent","child",
    "module","plugin","template","theme","skin","layout","config","settings","option",
    "flag","debug","env","code","status","level","grade","rank","score","group",
    "class","section","version","build",
]

# ═══════════════════════════════════════════════════════════════════════════
#  COUNTRY SITES — 100% same
# ═══════════════════════════════════════════════════════════════════════════
COUNTRY_SITES = [
    "site:.br","site:.in","site:.tr","site:.ro","site:.it","site:.pl",
    "site:.ru","site:.ua","site:.gr","site:.mx","site:.ar","site:.co",
    "site:.pe","site:.id","site:.ph","site:.vn","site:.th","site:.my",
    "site:.pk","site:.bd","site:.bg","site:.hu","site:.rs","site:.sk",
    "site:.cz","site:.pt","site:.es","site:.de","site:.fr","site:.nl",
]

# ═══════════════════════════════════════════════════════════════════════════
#  CMS DORKS — 100% same
# ═══════════════════════════════════════════════════════════════════════════
CMS_DORKS = {
    "wordpress": [
        'inurl:"/wp-login.php" inurl:.php?id=', 'inurl:"wp-content" inurl:.php?{param}=',
        'inurl:"wp-admin" inurl:.php?{param}=', 'site:*.wordpress.com inurl:.php?{param}=',
        'inurl:"/?p=" inurl:.php ext:php', 'inurl:"/wp-includes/" ext:php inurl:?id=',
        '"Powered by WordPress" inurl:.php?{param}=', 'inurl:"page_id=" ext:php',
        'inurl:"cat=" inurl:"/wordpress/" ext:php',
    ],
    "joomla": [
        'inurl:"option=com_" inurl:.php?{param}=', 'inurl:"index.php?option=com_content"',
        'inurl:"index.php?option=com_users"', '"Powered by Joomla" inurl:.php?id=',
        '"Joomla!" inurl:index.php?{param}=', 'inurl:"com_k2" ext:php',
        'inurl:"/administrator/" inurl:index.php "{kw}"',
        'inurl:"option=com_" inurl:"view=article" inurl:"id="',
        'inurl:"option=com_virtuemart" inurl:"product_id="',
    ],
    "opencart": [
        'inurl:"index.php?route=product" "{kw}"', 'inurl:"index.php?route=checkout" "{kw}"',
        'inurl:"route=account/login" "{kw}"', '"Powered by OpenCart" inurl:.php?product_id=',
        'inurl:"index.php?route=product/product&product_id="',
        'inurl:"/index.php?route=common/home" "{kw}"', '"OpenCart" inurl:"&category_id=" ext:php',
    ],
    "prestashop": [
        '"PrestaShop" inurl:index.php?id_product= "{kw}"', 'inurl:"index.php?id_category=" site:com "{kw}"',
        '"PrestaShop" inurl:checkout "{kw}"', 'inurl:"/index.php?controller=" inurl:"prestashop"',
        '"Powered by PrestaShop" inurl:.php?{param}=', 'inurl:"index.php?id_product=" "{kw}"',
        'inurl:"index.php?id_order=" "{kw}"', 'inurl:"index.php?controller=order&step=" "{kw}"',
    ],
    "magento": [
        'inurl:"/checkout/cart/" "{kw}"', 'inurl:"/checkout/onepage/" "{kw}"',
        '"Magento" inurl:.php?id= "{kw}"', '"Powered by Magento" inurl:checkout',
        'inurl:"/catalog/product/view/id/"', 'inurl:"/index.php/checkout/" "{kw}"',
        '"Magento Commerce" inurl:.php?{param}=', 'inurl:"/customer/account/login/" "{kw}"',
        'inurl:"/sales/order/view/order_id/" "{kw}"',
    ],
    "drupal": [
        'inurl:"?q=node/" "{kw}"', 'inurl:"?q=user/login" "{kw}"',
        '"Powered by Drupal" inurl:.php?{param}=', 'inurl:"/node/" inurl:"?{param}=" site:com',
        '"X-Generator: Drupal" inurl:.php?id=', 'inurl:"?q=content/" "{kw}" ext:php',
    ],
    "laravel": [
        'inurl:"/api/" inurl:".php?id=" "{kw}"', 'intext:"Laravel" inurl:.php?{param}= "{kw}"',
        'inurl:"/public/" inurl:.php?{param}=', '"laravel" inurl:?{param}= site:com',
    ],
    "codeigniter": [
        'inurl:"/index.php/{param}/" "{kw}"', '"CodeIgniter" inurl:.php?{param}=',
        'inurl:"/index.php/user/login" "{kw}"', '"CodeIgniter" inurl:checkout "{kw}"',
    ],
}

# ═══════════════════════════════════════════════════════════════════════════
#  DORK TEMPLATES — 100% same (saare ~130 templates)
# ═══════════════════════════════════════════════════════════════════════════
DORK_TEMPLATES = [
    # ── SQLi injectable PHP pages ──
    '{kw} *login inurl:.php?{param}=','{kw} login inurl:.php?{param}=',
    '{kw} login inurl:index.php?{param}=','{kw} login inurl:page.php?{param}=',
    '{kw} login inurl:view.php?{param}=','"{kw}" ext:php inurl:?{param}=',
    '"{kw}" ext:php inurl:.php?{param}=','ext:php inurl:?{param}= "{kw}"',
    '{kw} ext:php inurl:{param}=','{kw} ext:php inurl:id=',
    '{kw} ext:php inurl:page=','{kw} ext:php inurl:view=',
    '{kw} ext:php inurl:cat=','{kw} ext:php inurl:type=',
    'inurl:.php?{param}= "{kw}"','inurl:.php?{param}= {kw}',
    'inurl:.php?id= "{kw}"','inurl:.php?id= {kw} site:com',
    '"{kw}" inurl:.php?{param}= site:.com','{kw} inurl:.php?{param}= ext:php',
    '"{kw}" inurl:?{param}=','{kw} site:com inurl:.php?{param}=',
    # ── Specific PHP pages ──
    '"{kw}" inurl:view.php?id=','"{kw}" inurl:index.php?id=',
    '"{kw}" inurl:page.php?id=','"{kw}" inurl:item.php?id=',
    '"{kw}" inurl:news.php?id=','"{kw}" inurl:article.php?id=',
    '"{kw}" inurl:post.php?id=','"{kw}" inurl:read.php?id=',
    '"{kw}" inurl:detail.php?id=','"{kw}" inurl:show.php?id=',
    '"{kw}" inurl:category.php?id=','"{kw}" inurl:product.php?id=',
    '"{kw}" inurl:products.php?id=','"{kw}" inurl:search.php?{param}=',
    '"{kw}" inurl:gallery.php?id=','"{kw}" inurl:download.php?id=',
    # ── E-commerce / CC ──
    '"{kw}" inurl:checkout.php?id=','"{kw}" inurl:payment.php?id=',
    '"{kw}" inurl:billing.php?id=','"{kw}" inurl:invoice.php?id=',
    '"{kw}" inurl:order.php?id=','"{kw}" inurl:cart.php?id=',
    'inurl:checkout.php intext:"card number" "{kw}"',
    'inurl:payment.php intext:"credit card" "{kw}"',
    'intext:"card number" intext:"expiry" inurl:.php?{param}=',
    'intext:"credit card number" inurl:checkout ext:php',
    'intext:"cvv" intext:"card number" inurl:.php?{param}=',
    'intext:"visa" intext:"mastercard" inurl:checkout.php',
    'intext:"stripe" inurl:checkout.php ext:php',
    'intext:"paypal" intext:"card" inurl:checkout.php',
    'inurl:checkout.aspx intext:"card number"',
    'inurl:payment.aspx intext:"credit card" "{kw}"',
    # ── Login/admin ──
    '"{kw}" inurl:login.php?{param}=','"{kw}" inurl:admin.php?{param}=',
    '"{kw}" inurl:user.php?{param}=','"{kw}" inurl:member.php?{param}=',
    '"{kw}" inurl:profile.php?{param}=','"{kw}" inurl:dashboard.php?{param}=',
    'intitle:"admin login" inurl:.php?{param}=','intitle:"login" inurl:admin.php "{kw}"',
    'intitle:"administrator" inurl:.php?{param}= "{kw}"',
    'inurl:"/admin/" inurl:.php?{param}= "{kw}"',
    'inurl:"/administrator/" inurl:.php?id=','inurl:"/manage/" inurl:.php?id= "{kw}"',
    'intext:"username" intext:"password" inurl:login.php?{param}=',
    # ── ASPX / ASP / JSP / CFM ──
    '"{kw}" inurl:.aspx?{param}=','{kw} inurl:.aspx?id=',
    '{kw} ext:aspx inurl:?{param}=','"{kw}" inurl:checkout.aspx',
    '"{kw}" inurl:payment.aspx?{param}=','"{kw}" inurl:product.aspx?id=',
    '"{kw}" inurl:default.aspx?{param}=','{kw} inurl:.asp?{param}=',
    '{kw} inurl:.asp?id=','"{kw}" inurl:.jsp?{param}=',
    '{kw} inurl:.jsp?id=','{kw} inurl:.cfm?{param}=',
    # ── SQL error dorks ──
    'intext:"mysql_fetch_array()" inurl:.php?{param}=',
    'intext:"mysql_num_rows()" inurl:.php?{param}=',
    'intext:"You have an error in your SQL syntax" inurl:.php',
    'intext:"Warning: mysql_" inurl:.php?{param}=',
    'intext:"supplied argument is not a valid MySQL" inurl:.php',
    'intext:"ORA-01756:" inurl:.php','intext:"ORA-00933:" inurl:.php',
    'intext:"Microsoft OLE DB Provider for SQL Server" inurl:.asp',
    'intext:"ODBC SQL Server Driver" inurl:.asp','intext:"Incorrect syntax near" inurl:.asp',
    'intext:"Unclosed quotation mark before the character string" inurl:.asp',
    'intext:"mysqli_fetch_" inurl:.php?{param}=',
    'intext:"pg_query()" inurl:.php?{param}=',
    'intext:"PDOException:" inurl:.php?{param}=',
    'intext:"SQLSTATE[" inurl:.php?{param}=',
    'intext:"SQL command not properly ended" inurl:.php',
    # ── Exposed files ──
    'filetype:sql intext:"INSERT INTO" "{kw}"',
    'filetype:sql intext:"CREATE TABLE" intext:"password"',
    'filetype:log intext:"password" intext:"username" "{kw}"',
    'filetype:env intext:"DB_PASSWORD" "{kw}"',
    'filetype:yml intext:"password" "{kw}"','filetype:xml intext:"password" "{kw}"',
    'filetype:ini intext:"passwd" "{kw}"','filetype:conf intext:"password" "{kw}"',
    'filetype:bak inurl:backup "{kw}"','filetype:json intext:"api_key" "{kw}"',
    'filetype:txt intext:"username" intext:"password" "{kw}"',
    'filetype:csv intext:"credit card" "{kw}"','filetype:xls intext:"password" intext:"email" "{kw}"',
    'filetype:pem intext:"PRIVATE KEY"','inurl:"/.env" intext:"DB_PASSWORD"',
    'inurl:"/config.php" intext:"$db_pass"','inurl:"/database.yml" intext:"password"',
    'inurl:"/phpMyAdmin" intitle:"phpMyAdmin"','inurl:"/phpmyadmin/" intitle:"phpMyAdmin"',
    'inurl:"db.php" intext:"mysql_connect"','inurl:"wp-config.php" intext:"DB_PASSWORD"',
    'inurl:"settings.php" intext:"database_password"',
    # ── Directory listing ──
    'intitle:"Index of" intext:"backup" "{kw}"',
    'intitle:"Index of" intext:".sql" "{kw}"',
    'intitle:"Index of" intext:"password" "{kw}"',
    'intitle:"Index of" "/admin" "{kw}"',
    'intitle:"Index of" "/database" "{kw}"',
    'intitle:"Index of" intext:"dump.sql"',
    # ── Country ──
    '{kw} inurl:.php?id= site:.br','{kw} inurl:.php?id= site:.in',
    '{kw} inurl:.php?id= site:.tr','{kw} inurl:.php?id= site:.ro',
    '{kw} inurl:.php?id= site:.it','{kw} inurl:.php?id= site:.pl',
    '{kw} inurl:.php?{param}= site:.ru','{kw} inurl:.php?{param}= site:.ua',
    '{kw} inurl:.php?{param}= site:.gr','{kw} inurl:.php?{param}= site:.mx',
    '{kw} inurl:.php?{param}= site:.ar','{kw} inurl:.php?{param}= site:.id',
    '{kw} inurl:.php?{param}= site:.ph','{kw} inurl:.php?{param}= site:.vn',
    'ext:php inurl:?{param}= "{kw}" site:.com','ext:php inurl:?{param}= "{kw}" site:.net',
    'ext:php inurl:?{param}= "{kw}" site:.org',
    # ── Multi-param ──
    '{kw} inurl:.php?id=1&cat=','{kw} inurl:.php?{param}=1&id=',
    'inurl:.php?id=&cat= "{kw}" ext:php','inurl:.php?page=&id= "{kw}"',
    'inurl:.php?{param}=&action= "{kw}"','inurl:.php?item=&id= "{kw}" ext:php',
    '~{kw} ext:php inurl:?{param}= site:com',
]

# ═══════════════════════════════════════════════════════════════════════════
#  PAYMENT KEYWORD TEMPLATES — 100% same
# ═══════════════════════════════════════════════════════════════════════════
PAYMENT_KEYWORD_TEMPLATES = [
    "credit card checkout","debit card payment","visa mastercard checkout",
    "online payment form","secure checkout page","card payment gateway",
    "credit card billing","debit card billing","card number entry",
    "payment processing site","credit card subscription","card details form",
    "buy with credit card","checkout credit card","payment credit card form",
    "online store checkout","ecommerce payment page","card accepted checkout",
    "visa payment form","mastercard payment form","amex payment checkout",
    "stripe payment form","paypal checkout credit card","square payment form",
    "credit card order form","debit card order form","card billing form",
    "secure payment page","enter card details","credit card number form",
    "cvv card checkout","card expiry billing","online shopping checkout",
    "payment gateway form","shop checkout credit card","store payment form",
    "buy now credit card","add card payment","card holder billing",
    "subscription credit card","membership credit card payment",
    "donate credit card","fund credit card checkout","renew card billing",
    "upgrade credit card payment","purchase credit card form",
    "woocommerce credit card","shopify checkout card","magento payment card",
    "opencart credit card","prestashop checkout card","bigcommerce card",
    "credit card form php","payment form php checkout","billing php card",
    "checkout php visa mastercard","order php credit card",
]

# ═══════════════════════════════════════════════════════════════════════════
#  KEYWORD TEMPLATES — 100% same
# ═══════════════════════════════════════════════════════════════════════════
KEYWORD_TEMPLATES = [
    "plans","issue report","api pricing","emulator not","to fix","failed",
    "error codes","issue today","cheapest plan","failed process","recording failed",
    "not connecting","common problem","booking price","appointment system",
    "traveller review","login","method without","game not","cancel","auth fail",
    "windows","plan","streaming issues","what fees","account","pricing for",
    "loading packages","price meaning","include taxes","month","pricing uk",
    "cheapest plans","hacked recovery","price canada","personal bookings",
    "tv remote","additional member","recovery email","payment method",
    "internet reddit","fix app","reviews","password login","student plans",
    "buffering","black screen","policy for","free trial","month plans",
    "basic plan","password","login portal","monthly membership","with vpn",
    "issue 2024","store page","fix buffering","problem series","to uninstall",
    "price uk","solve problem","failed attempting","admin","add people",
    "subscription","portal login","is stuck","issues signing","plans 2024",
    "to find","why not","why keeps","to open","fix problem","error code",
    "update price","refund","free download","billing online","fixed",
    "seller commission","comparison","plan deals","number not","channels",
    "registration not","checkout error","payment declined","billing failed",
    "subscription error","account suspended","login failed","verification failed",
    "transaction failed","order failed","payment not processed","card declined",
    "refund status","order cancelled","account hacked","password reset",
    "2fa problem","otp not received","account recovery","unable to pay",
    "payment gateway error","checkout problem","card not accepted",
    "payment processing","invoice download","subscription renewal",
    "auto renewal","membership expired","upgrade plan","downgrade plan",
    "billing cycle","payment history","transaction history","billing address",
] + PAYMENT_KEYWORD_TEMPLATES

# ═══════════════════════════════════════════════════════════════════════════
#  OTHER KEYWORD CATEGORIES — 100% same
# ═══════════════════════════════════════════════════════════════════════════
BANKING_KEYWORDS = [
    "online banking login","bank account statement","transaction history",
    "wire transfer form","ach payment","direct deposit setup","bank routing number",
    "account number entry","checking account balance","savings account details",
    "credit card statement","loan payment portal","mortgage payment",
    "auto loan payment","business banking login","corporate account access",
    "bank verification","identity verification","security question reset",
    "fraud alert report","account lockout","password change banking",
]

INSURANCE_KEYWORDS = [
    "insurance claim form","policy number entry","insurance quote",
    "auto insurance claim","health insurance claim","life insurance policy",
    "home insurance claim","renters insurance","liability coverage",
    "insurance payment portal","premium payment","renewal notice",
    "policy cancellation","claim status check","insured person details",
    "beneficiary change","coverage verification","insurance card download",
]

HEALTHCARE_KEYWORDS = [
    "patient portal login","medical billing statement","healthcare invoice",
    "insurance verification","copay payment","deductible status","prescription refill",
    "medication history","appointment scheduling","telehealth consult",
    "medical records request","test results download","healthcare account",
    "payment plan setup","financial assistance application","medical ID card",
    "explanation of benefits","claim denial appeal","preauthorization",
]

TRAVEL_KEYWORDS = [
    "flight booking confirmation","hotel reservation","car rental booking",
    "vacation package checkout","travel insurance purchase","itinerary download",
    "boarding pass retrieval","seat selection","upgrade request",
    "loyalty points redemption","travel voucher","group booking",
    "corporate travel account","expense report","travel invoice",
    "visa application","passport details","customs declaration",
]

EDUCATION_KEYWORDS = [
    "student login portal","tuition payment","financial aid application",
    "scholarship application","student account balance","course registration",
    "grade transcript download","enrollment verification","class schedule",
    "exam results access","homework submission","assignment grades",
    "library account","student ID card","campus parking permit",
    "meal plan payment","housing application",
]

SENSITIVE_GENERAL = [
    "account takeover","password reset link","two factor authentication",
    "security code entry","SSN entry","tax ID","driver license number",
    "passport number","mother maiden name","birthdate verification",
    "address proof","utility bill upload","bank statement upload",
    "API key generation","secret key","client secret","OAuth token",
    "session cookie","JWT token","refresh token","private key",
]

# ═══════════════════════════════════════════════════════════════════════════
#  GENERATOR FUNCTIONS — 100% same
# ═══════════════════════════════════════════════════════════════════════════

def generate_keywords(seed_brands, count_per_brand):
    """Same as bot — MANUAL seeds input"""
    results = set()
    templates = KEYWORD_TEMPLATES.copy()
    random.shuffle(templates)
    all_seeds = list(dict.fromkeys(
        [b.strip().lower() for b in seed_brands if b.strip()] + PAYMENT_KEYWORD_TEMPLATES
    ))
    for brand in all_seeds:
        for tmpl in templates:
            results.add(f"{brand} {tmpl}")
            results.add(f"{tmpl} {brand}")
    for pt in PAYMENT_KEYWORD_TEMPLATES:
        results.add(pt)
        for brand in [b.strip().lower() for b in seed_brands if b.strip()]:
            results.add(f"{brand} {pt}")
    for t in templates:
        results.add(t)
    out = list(results)
    random.shuffle(out)
    return out


def generate_dorks(keywords, limit=1_000_000):
    """Same as bot"""
    results = []
    templates = DORK_TEMPLATES.copy()
    params = PHP_PARAMS.copy()
    random.shuffle(templates)
    random.shuffle(params)
    kw_pool = keywords.copy()
    random.shuffle(kw_pool)
    if not kw_pool:
        kw_pool = ["shop"]
    tc = itertools.cycle(templates)
    pc = itertools.cycle(params)
    i = 0
    while len(results) < limit:
        t = next(tc)
        p = next(pc)
        kw = kw_pool[i % len(kw_pool)]
        i += 1
        results.append(t.replace("{kw}", kw).replace("{param}", p))
        if len(results) >= limit:
            break
    random.shuffle(results)
    return results


def generate_hq_sqli_dorks(keywords=None, limit=10_000, include_error_dorks=True,
                            include_payment_dorks=True, include_cms_dorks=True,
                            include_country_dorks=True, target_countries=None,
                            target_cms=None):
    """Same as bot"""
    if keywords is None:
        keywords = ["shop","store","checkout","payment","login","account"]
    if target_countries is None:
        target_countries = COUNTRY_SITES[:15]
    if target_cms is None:
        target_cms = list(CMS_DORKS.keys())
    results = set()
    params = PHP_PARAMS[:30]
    random.shuffle(params)
    pc = itertools.cycle(params)
    kw_pool = keywords.copy()
    random.shuffle(kw_pool)
    for kw in kw_pool:
        for pat in [
            'inurl:.php?id= "{kw}"','inurl:.php?cat= "{kw}"','inurl:.php?pid= "{kw}"',
            'inurl:.php?article= "{kw}"','inurl:.php?{param}= "{kw}" ext:php',
            'inurl:.php?{param}= site:com','inurl:.php?{param}= site:net',
            'inurl:index.php?id= "{kw}"','inurl:view.php?id= "{kw}"',
            'inurl:page.php?id= "{kw}"','inurl:detail.php?id= "{kw}"',
            'inurl:item.php?id= "{kw}"','inurl:news.php?id= "{kw}"',
            'inurl:product.php?id= "{kw}"','inurl:category.php?id= "{kw}"',
            'inurl:search.php?{param}= "{kw}"','inurl:.aspx?id= "{kw}"',
            'inurl:.asp?id= "{kw}"','inurl:.jsp?id= "{kw}"',
        ]:
            results.add(pat.replace("{kw}", kw).replace("{param}", next(pc)))
    if include_error_dorks:
        for pat in [
            'intext:"mysql_fetch_array()" inurl:.php?{param}=',
            'intext:"You have an error in your SQL syntax" inurl:.php?{param}=',
            'intext:"Warning: mysql_" inurl:.php?{param}=',
            'intext:"supplied argument is not a valid MySQL" inurl:.php',
            'intext:"mysqli_fetch_" inurl:.php?{param}=',
            'intext:"PDOException:" inurl:.php?{param}=',
            'intext:"SQLSTATE[" inurl:.php?{param}=',
            'intext:"Microsoft OLE DB Provider for SQL Server" inurl:.asp',
            'intext:"ORA-01756:" inurl:.php',
            'intext:"Incorrect syntax near" inurl:.asp?{param}=',
        ]:
            for _ in range(5):
                results.add(pat.replace("{param}", next(pc)))
    if include_payment_dorks:
        for kw in kw_pool[:20]:
            for pat in [
                'inurl:checkout.php intext:"credit card" ext:php',
                'inurl:payment.php intext:"card number" ext:php',
                'inurl:billing.php intext:"card number" ext:php',
                'intext:"cvv" intext:"card number" inurl:.php?id=',
                'intext:"credit card" intext:"expiry" inurl:.php?{param}=',
                'intext:"visa" intext:"mastercard" inurl:checkout.php',
                'intext:"stripe" inurl:checkout.php ext:php',
                '"{kw}" inurl:checkout.php?id=','"{kw}" inurl:payment.php?id=',
            ]:
                results.add(pat.replace("{kw}", kw).replace("{param}", next(pc)))
    if include_cms_dorks:
        for cms in target_cms:
            if cms in CMS_DORKS:
                for kw in kw_pool[:10]:
                    for pat in CMS_DORKS[cms]:
                        results.add(pat.replace("{kw}", kw).replace("{param}", next(pc)))
    if include_country_dorks:
        for c in target_countries:
            for kw in kw_pool[:10]:
                results.add(f'"{kw}" inurl:.php?id= {c}')
                results.add(f'"{kw}" inurl:.php?{random.choice(params)}= {c}')
                results.add(f'"{kw}" ext:php inurl:?id= {c}')
    d = list(results)[:limit]
    random.shuffle(d)
    return d


def generate_country_dorks(keywords, countries=None, limit=5_000):
    """Same as bot"""
    if countries is None:
        countries = COUNTRY_SITES[:20]
    results = set()
    params = PHP_PARAMS[:20]
    random.shuffle(params)
    pc = itertools.cycle(params)
    for c in countries:
        for kw in keywords[:50]:
            results.add(f'"{kw}" inurl:.php?id= {c}')
            results.add(f'"{kw}" inurl:.php?{next(pc)}= {c}')
            results.add(f'"{kw}" ext:php inurl:?id= {c}')
            results.add(f'ext:php inurl:?{next(pc)}= "{kw}" {c}')
            results.add(f'"{kw}" inurl:index.php?id= {c}')
    d = list(results)[:limit]
    random.shuffle(d)
    return d


def generate_cms_dorks(keywords, cms_list=None, limit=5_000):
    """Same as bot"""
    if cms_list is None:
        cms_list = list(CMS_DORKS.keys())
    results = set()
    params = PHP_PARAMS[:20]
    pc = itertools.cycle(params)
    for cms in cms_list:
        if cms not in CMS_DORKS:
            continue
        for kw in keywords[:30]:
            for pat in CMS_DORKS[cms]:
                results.add(pat.replace("{kw}", kw).replace("{param}", next(pc)))
    d = list(results)[:limit]
    random.shuffle(d)
    return d


def generate_exposed_dorks(keywords, limit=2_000):
    """Same as bot"""
    results = set()
    for kw in keywords[:50]:
        for pat in [
            'filetype:sql intext:"INSERT INTO" "{kw}"','filetype:env intext:"DB_PASSWORD" "{kw}"',
            'filetype:log intext:"password" "{kw}"','filetype:yml intext:"password" "{kw}"',
            'filetype:json intext:"api_key" "{kw}"','filetype:bak inurl:backup "{kw}"',
            'inurl:"/.env" intext:"DB_PASSWORD"','inurl:"/config.php" intext:"$db_pass"',
            'inurl:"/wp-config.php" intext:"DB_PASSWORD"','intitle:"Index of" intext:".sql" "{kw}"',
        ]:
            results.add(pat.replace("{kw}", kw))
    d = list(results)[:limit]
    random.shuffle(d)
    return d