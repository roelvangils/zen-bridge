#!/usr/bin/env python3
"""
Zen Browser Bridge CLI - Execute JavaScript in your browser from the command line.
"""
import sys
import os
import json
import click
import subprocess
import signal
from pathlib import Path
from .client import BridgeClient
from . import __version__
from . import config as zen_config

# Save built-in functions before they get shadowed by Click commands
_builtin_open = open
_builtin_next = next


def format_output(result: dict, format_type: str = "auto") -> str:
    """Format execution result for display."""
    if not result.get("ok"):
        error = result.get("error", "Unknown error")
        return f"Error: {error}"

    value = result.get("result")

    if format_type == "json":
        return json.dumps(value, indent=2)
    elif format_type == "raw":
        return str(value) if value is not None else ""
    else:  # auto
        if value is None:
            return "undefined"
        elif isinstance(value, str):
            return value
        elif isinstance(value, (dict, list)):
            return json.dumps(value, indent=2)
        else:
            return str(value)


class CustomGroup(click.Group):
    """Custom Click Group that shows all command options in help."""

    def format_help(self, ctx, formatter):
        self.format_usage(ctx, formatter)
        self.format_help_text(ctx, formatter)
        self.format_options(ctx, formatter)
        self.format_commands_with_options(ctx, formatter)
        self.format_epilog(ctx, formatter)

    def format_commands_with_options(self, ctx, formatter):
        """List all commands with their options."""
        commands = self.list_commands(ctx)

        if len(commands):
            formatter.write_paragraph()
            formatter.write_text("Commands:")
            formatter.write_paragraph()

            for subcommand in commands:
                cmd = self.get_command(ctx, subcommand)
                if cmd is None:
                    continue

                # Write command name and description
                help_text = cmd.get_short_help_str(limit=80)
                formatter.write_text(f"  {subcommand}")
                if help_text:
                    formatter.write_text(f"    {help_text}")

                # Write command options
                params = [p for p in cmd.params if isinstance(p, click.Option)]
                if params:
                    for param in params:
                        opts = ", ".join(param.opts)
                        help_text = param.help or ""
                        default = ""
                        if param.default is not None and not isinstance(param.default, bool):
                            default = f" [default: {param.default}]"
                        formatter.write_text(f"      {opts}  {help_text}{default}")

                formatter.write_paragraph()


@click.group(cls=CustomGroup)
@click.version_option(version=__version__)
def cli():
    """Zen Browser Bridge - Execute JavaScript in your browser from the CLI."""
    pass


@cli.command()
@click.argument("code", required=False)
@click.option("-f", "--file", type=click.Path(exists=True), help="Execute code from file")
@click.option("-t", "--timeout", type=float, default=10.0, help="Timeout in seconds (default: 10)")
@click.option("--format", type=click.Choice(["auto", "json", "raw"]), default="auto", help="Output format")
@click.option("--url", is_flag=True, help="Also print page URL")
@click.option("--title", is_flag=True, help="Also print page title")
def eval(code, file, timeout, format, url, title):
    """
    Execute JavaScript code in the active browser tab.

    Examples:

        zen eval "document.title"

        zen eval "alert('Hello from CLI!')"

        zen eval --file script.js

        echo "console.log('test')" | zen eval
    """
    client = BridgeClient()

    # Read from stdin if no code or file provided
    if not code and not file:
        if not sys.stdin.isatty():
            code = sys.stdin.read()
        else:
            click.echo("Error: No code provided. Use: zen eval CODE or zen eval --file FILE", err=True)
            sys.exit(1)

    try:
        if file:
            result = client.execute_file(file, timeout=timeout)
        else:
            result = client.execute(code, timeout=timeout)

        # Show metadata if requested
        if url and result.get("url"):
            click.echo(f"URL: {result['url']}", err=True)
        if title and result.get("title"):
            click.echo(f"Title: {result['title']}", err=True)

        # Show result
        output = format_output(result, format)
        click.echo(output)

        # Exit with error code if execution failed
        if not result.get("ok"):
            sys.exit(1)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option("-t", "--timeout", type=float, default=10.0, help="Timeout in seconds")
@click.option("--format", type=click.Choice(["auto", "json", "raw"]), default="auto", help="Output format")
def exec(filepath, timeout, format):
    """
    Execute JavaScript from a file.

    Example:

        zen exec script.js
    """
    client = BridgeClient()

    try:
        result = client.execute_file(filepath, timeout=timeout)
        output = format_output(result, format)
        click.echo(output)

        if not result.get("ok"):
            sys.exit(1)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _get_domain_metrics(domain):
    """Fetch domain metrics including IP, geolocation, WHOIS, and SSL info."""
    if not domain or domain == 'N/A':
        return None

    metrics = {}

    try:
        import socket
        import ssl
        import datetime
        import requests

        # Get IP address
        try:
            ip = socket.gethostbyname(domain)
            metrics['ip'] = ip

            # Get geolocation from ip-api.com (free, no auth required)
            try:
                geo_response = requests.get(f'http://ip-api.com/json/{ip}', timeout=3)
                if geo_response.status_code == 200:
                    geo_data = geo_response.json()
                    if geo_data.get('status') == 'success':
                        metrics['geolocation'] = {
                            'country': geo_data.get('country'),
                            'region': geo_data.get('regionName'),
                            'city': geo_data.get('city'),
                            'isp': geo_data.get('isp'),
                            'org': geo_data.get('org')
                        }
            except Exception:
                pass  # Geolocation is optional

        except socket.gaierror:
            pass  # Can't resolve domain

        # Get SSL certificate info
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=3) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()

                    # Extract issuer
                    issuer = dict(x[0] for x in cert.get('issuer', []))
                    issuer_name = issuer.get('organizationName', issuer.get('commonName', 'Unknown'))

                    # Extract expiry date
                    not_after = cert.get('notAfter')
                    if not_after:
                        expiry_date = datetime.datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                        days_remaining = (expiry_date - datetime.datetime.now()).days

                        metrics['ssl'] = {
                            'issuer': issuer_name,
                            'expiry': expiry_date.strftime('%Y-%m-%d'),
                            'days_remaining': days_remaining
                        }
        except Exception:
            pass  # SSL info is optional

        # Get WHOIS info (try python-whois if available)
        try:
            import whois
            w = whois.whois(domain)
            whois_data = {}

            # Handle dates (can be lists or single values)
            creation_date = w.creation_date
            if isinstance(creation_date, list):
                creation_date = creation_date[0]
            if creation_date:
                whois_data['creation_date'] = creation_date.strftime('%Y-%m-%d') if hasattr(creation_date, 'strftime') else str(creation_date)

            expiration_date = w.expiration_date
            if isinstance(expiration_date, list):
                expiration_date = expiration_date[0]
            if expiration_date:
                whois_data['expiration_date'] = expiration_date.strftime('%Y-%m-%d') if hasattr(expiration_date, 'strftime') else str(expiration_date)

            if w.registrar:
                whois_data['registrar'] = w.registrar if isinstance(w.registrar, str) else w.registrar[0] if isinstance(w.registrar, list) else str(w.registrar)

            if whois_data:
                metrics['whois'] = whois_data
        except ImportError:
            pass  # python-whois not installed
        except Exception:
            pass  # WHOIS lookup failed

    except Exception:
        pass  # Return whatever metrics we managed to collect

    return metrics if metrics else None


def _get_response_headers(url):
    """Fetch HTTP response headers from the given URL."""
    try:
        import requests

        response = requests.head(url, timeout=3, allow_redirects=True)
        headers = dict(response.headers)

        # Extract key headers
        return {
            'server': headers.get('Server'),
            'cacheControl': headers.get('Cache-Control'),
            'contentEncoding': headers.get('Content-Encoding'),
            'etag': headers.get('ETag'),
            'lastModified': headers.get('Last-Modified'),
            'contentType': headers.get('Content-Type'),
            # Security headers
            'xFrameOptions': headers.get('X-Frame-Options'),
            'xContentTypeOptions': headers.get('X-Content-Type-Options'),
            'strictTransportSecurity': headers.get('Strict-Transport-Security'),
            'contentSecurityPolicy': headers.get('Content-Security-Policy'),
            'permissionsPolicy': headers.get('Permissions-Policy'),
            'referrerPolicy': headers.get('Referrer-Policy'),
            'xXssProtection': headers.get('X-XSS-Protection')
        }
    except Exception:
        return None


def _get_robots_txt(url):
    """Fetch and parse robots.txt for the given URL."""
    try:
        from urllib.parse import urlparse
        import requests

        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        response = requests.get(robots_url, timeout=3)
        if response.status_code == 200:
            content = response.text
            lines = content.split('\n')

            # Parse key directives
            result = {
                'exists': True,
                'url': robots_url,
                'size': len(content),
                'lines': len(lines),
                'userAgents': [],
                'sitemaps': [],
                'disallowRules': 0,
                'allowRules': 0
            }

            current_agent = None
            for line in lines:
                line = line.strip()
                if line.startswith('User-agent:'):
                    agent = line.split(':', 1)[1].strip()
                    if agent and agent not in result['userAgents']:
                        result['userAgents'].append(agent)
                    current_agent = agent
                elif line.startswith('Disallow:'):
                    result['disallowRules'] += 1
                elif line.startswith('Allow:'):
                    result['allowRules'] += 1
                elif line.startswith('Sitemap:'):
                    sitemap = line.split(':', 1)[1].strip()
                    if sitemap:
                        result['sitemaps'].append(sitemap)

            return result
        else:
            return {'exists': False, 'status': response.status_code}

    except Exception as e:
        return {'exists': False, 'error': str(e)}


@cli.command()
@click.option("--extended", is_flag=True, help="Show extended information (language, meta tags, cookies)")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def info(extended, output_json):
    """Get information about the current browser tab."""
    client = BridgeClient()

    if extended:
        code = """
        ({
            url: location.href,
            title: document.title,
            domain: location.hostname,
            protocol: location.protocol,
            readyState: document.readyState,
            width: window.innerWidth,
            height: window.innerHeight,
            // Extended info
            specifiedLanguage: document.documentElement.lang || 'N/A',
            charset: document.characterSet || 'N/A',
            metaTags: Array.from(document.querySelectorAll('head meta')).map(meta => {
                const attrs = {};
                for (let attr of meta.attributes) {
                    attrs[attr.name] = attr.value;
                }
                return attrs;
            }),
            cookieCount: document.cookie.split(';').filter(c => c.trim()).length,
            // Additional useful info
            scriptCount: document.scripts.length,
            stylesheetCount: document.styleSheets.length,
            imageCount: document.images.length,
            linkCount: document.links.length,
            formCount: document.forms.length,
            iframeCount: document.querySelectorAll('iframe').length,
            scrollHeight: document.documentElement.scrollHeight,
            scrollWidth: document.documentElement.scrollWidth,
            hasServiceWorker: 'serviceWorker' in navigator,
            localStorageSize: (() => {
                try {
                    return Object.keys(localStorage).reduce((acc, key) =>
                        acc + key.length + localStorage[key].length, 0);
                } catch (e) {
                    return 0;
                }
            })(),
            sessionStorageSize: (() => {
                try {
                    return Object.keys(sessionStorage).reduce((acc, key) =>
                        acc + key.length + sessionStorage[key].length, 0);
                } catch (e) {
                    return 0;
                }
            })(),
            // Security Info
            security: {
                isSecure: location.protocol === 'https:',
                hasMixedContent: (() => {
                    const insecureResources = Array.from(document.querySelectorAll('script, img, link, iframe')).some(el => {
                        const src = el.src || el.href;
                        return src && src.startsWith('http:');
                    });
                    return location.protocol === 'https:' && insecureResources;
                })(),
                cspMeta: (() => {
                    const cspMeta = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
                    return cspMeta ? cspMeta.getAttribute('content') : null;
                })(),
                robotsMeta: (() => {
                    const robots = document.querySelector('meta[name="robots"]');
                    return robots ? robots.getAttribute('content') : null;
                })(),
                referrerPolicy: (() => {
                    const referrer = document.querySelector('meta[name="referrer"]');
                    return referrer ? referrer.getAttribute('content') : null;
                })()
            },
            // Accessibility
            accessibility: {
                landmarkCount: document.querySelectorAll('[role="banner"], [role="navigation"], [role="main"], [role="complementary"], [role="contentinfo"], [role="search"], [role="region"], header, nav, main, aside, footer').length,
                landmarks: (() => {
                    const landmarks = {};
                    document.querySelectorAll('[role="banner"], [role="navigation"], [role="main"], [role="complementary"], [role="contentinfo"], [role="search"], [role="region"], header:not([role]), nav:not([role]), main:not([role]), aside:not([role]), footer:not([role])').forEach(el => {
                        const role = el.getAttribute('role') || el.tagName.toLowerCase();
                        landmarks[role] = (landmarks[role] || 0) + 1;
                    });
                    return landmarks;
                })(),
                headingStructure: (() => {
                    const structure = {h1: 0, h2: 0, h3: 0, h4: 0, h5: 0, h6: 0};
                    document.querySelectorAll('h1, h2, h3, h4, h5, h6, [role="heading"]').forEach(h => {
                        if (h.hasAttribute('role')) {
                            const level = parseInt(h.getAttribute('aria-level') || '1');
                            const key = 'h' + level;
                            if (structure[key] !== undefined) structure[key]++;
                        } else {
                            structure[h.tagName.toLowerCase()]++;
                        }
                    });
                    return structure;
                })(),
                imagesWithoutAlt: Array.from(document.images).filter(img => !img.hasAttribute('alt')).length,
                formLabelsIssues: (() => {
                    const inputs = document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]), select, textarea');
                    let missingLabels = 0;
                    inputs.forEach(input => {
                        const hasLabel = input.labels && input.labels.length > 0;
                        const hasAriaLabel = input.hasAttribute('aria-label') || input.hasAttribute('aria-labelledby');
                        if (!hasLabel && !hasAriaLabel) missingLabels++;
                    });
                    return {total: inputs.length, missingLabels};
                })(),
                tabIndexIssues: document.querySelectorAll('[tabindex]').length
            },
            // SEO Metrics
            seo: {
                canonical: (() => {
                    const canonical = document.querySelector('link[rel="canonical"]');
                    return canonical ? canonical.href : null;
                })(),
                openGraph: (() => {
                    const og = {};
                    document.querySelectorAll('meta[property^="og:"]').forEach(meta => {
                        const prop = meta.getAttribute('property').replace('og:', '');
                        og[prop] = meta.getAttribute('content');
                    });
                    return og;
                })(),
                twitterCard: (() => {
                    const twitter = {};
                    document.querySelectorAll('meta[name^="twitter:"]').forEach(meta => {
                        const prop = meta.getAttribute('name').replace('twitter:', '');
                        twitter[prop] = meta.getAttribute('content');
                    });
                    return twitter;
                })(),
                robots: (() => {
                    const robots = document.querySelector('meta[name="robots"]');
                    return robots ? robots.getAttribute('content') : null;
                })(),
                description: (() => {
                    const desc = document.querySelector('meta[name="description"]');
                    return desc ? desc.getAttribute('content') : null;
                })(),
                keywords: (() => {
                    const kw = document.querySelector('meta[name="keywords"]');
                    return kw ? kw.getAttribute('content') : null;
                })()
            },
            // Browser/Device Info
            device: {
                userAgent: navigator.userAgent,
                screenResolution: screen.width + 'x' + screen.height,
                viewportSize: window.innerWidth + 'x' + window.innerHeight,
                devicePixelRatio: window.devicePixelRatio,
                touchSupport: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
                platform: navigator.platform,
                language: navigator.language,
                languages: navigator.languages.join(', '),
                cookiesEnabled: navigator.cookieEnabled,
                onlineStatus: navigator.onLine
            },
            // Technologies Detection
            technologies: (() => {
                const detected = {};

                // Helper to add detected tech
                const addTech = (category, name, version = null) => {
                    if (!detected[category]) detected[category] = [];
                    const tech = version ? `${name} ${version}` : name;
                    if (!detected[category].includes(tech)) {
                        detected[category].push(tech);
                    }
                };

                // JavaScript Frameworks & Libraries
                if (window.React || document.querySelector('[data-reactroot], [data-reactid]')) {
                    const version = window.React?.version;
                    addTech('JavaScript Framework', 'React', version);
                }
                if (window.Vue) {
                    const version = window.Vue?.version;
                    addTech('JavaScript Framework', 'Vue.js', version);
                }
                if (window.angular || document.querySelector('[ng-app], [ng-version]')) {
                    const ngVersion = document.querySelector('[ng-version]')?.getAttribute('ng-version');
                    addTech('JavaScript Framework', 'Angular', ngVersion);
                }
                if (window.Svelte) addTech('JavaScript Framework', 'Svelte');
                if (window.jQuery) {
                    const version = window.jQuery?.fn?.jquery;
                    addTech('JavaScript Library', 'jQuery', version);
                }
                if (window._) addTech('JavaScript Library', 'Lodash/Underscore');
                if (window.moment) addTech('JavaScript Library', 'Moment.js');
                if (window.THREE) addTech('JavaScript Library', 'Three.js');
                if (window.d3) addTech('JavaScript Library', 'D3.js');
                if (window.Chart) addTech('JavaScript Library', 'Chart.js');
                if (window.Alpine) addTech('JavaScript Framework', 'Alpine.js');
                if (window.htmx) addTech('JavaScript Library', 'htmx');

                // Next.js / Nuxt detection
                if (document.querySelector('#__next')) addTech('JavaScript Framework', 'Next.js');
                if (document.querySelector('#__nuxt')) addTech('JavaScript Framework', 'Nuxt.js');

                // CMS Detection
                const generator = document.querySelector('meta[name="generator"]')?.content;
                if (generator) {
                    if (generator.includes('WordPress')) addTech('CMS', 'WordPress', generator.match(/WordPress ([\\d.]+)/)?.[1]);
                    if (generator.includes('Drupal')) addTech('CMS', 'Drupal', generator.match(/Drupal ([\\d.]+)/)?.[1]);
                    if (generator.includes('Joomla')) addTech('CMS', 'Joomla');
                    if (generator.includes('Ghost')) addTech('CMS', 'Ghost');
                }
                if (window.Shopify) addTech('CMS', 'Shopify');
                if (document.querySelector('link[href*="shopify"]')) addTech('CMS', 'Shopify');
                if (document.querySelector('meta[content*="Wix.com"]')) addTech('CMS', 'Wix');
                if (document.querySelector('script[src*="squarespace"]')) addTech('CMS', 'Squarespace');
                if (document.querySelector('meta[name="notion-site"]')) addTech('CMS', 'Notion');

                // Analytics & Tracking
                if (window.ga || window.gtag || window.google_tag_manager) {
                    addTech('Analytics', 'Google Analytics');
                }
                if (window.dataLayer) addTech('Tag Manager', 'Google Tag Manager');
                if (window.fbq) addTech('Analytics', 'Facebook Pixel');
                if (window.hj) addTech('Analytics', 'Hotjar');
                if (window.mixpanel) addTech('Analytics', 'Mixpanel');
                if (window.analytics && window.analytics.initialize) addTech('Analytics', 'Segment');
                if (window._paq) addTech('Analytics', 'Matomo/Piwik');
                if (window.plausible) addTech('Analytics', 'Plausible');
                if (window.fathom) addTech('Analytics', 'Fathom');

                // UI Frameworks (check classes in body)
                const bodyClasses = document.body?.className || '';
                const allClasses = Array.from(document.querySelectorAll('[class]')).map(el => el.className).join(' ');

                if (document.querySelector('link[href*="bootstrap"]') || /\\bbs-|\\bbtn-|\\bcol-/.test(allClasses)) {
                    addTech('CSS Framework', 'Bootstrap');
                }
                if (/\\btw-|\\bflex|\\bgrid|\\bbg-|\\btext-/.test(allClasses) && document.querySelector('script[src*="tailwind"]')) {
                    addTech('CSS Framework', 'Tailwind CSS');
                }
                if (window.MaterialUI || document.querySelector('[class*="MuiButton"]')) {
                    addTech('CSS Framework', 'Material-UI');
                }
                if (document.querySelector('link[href*="bulma"]')) addTech('CSS Framework', 'Bulma');
                if (document.querySelector('link[href*="foundation"]')) addTech('CSS Framework', 'Foundation');

                // Font Services
                if (document.querySelector('link[href*="fonts.googleapis.com"]')) {
                    addTech('Font Service', 'Google Fonts');
                }
                if (document.querySelector('link[href*="typekit"], script[src*="typekit"]')) {
                    addTech('Font Service', 'Adobe Fonts (Typekit)');
                }

                // CDN Detection
                const scripts = Array.from(document.scripts).map(s => s.src);
                if (scripts.some(s => s.includes('cloudflare'))) addTech('CDN', 'Cloudflare');
                if (scripts.some(s => s.includes('fastly'))) addTech('CDN', 'Fastly');
                if (scripts.some(s => s.includes('jsdelivr'))) addTech('CDN', 'jsDelivr');
                if (scripts.some(s => s.includes('unpkg'))) addTech('CDN', 'unpkg');
                if (scripts.some(s => s.includes('cdnjs'))) addTech('CDN', 'cdnjs');

                // Payment Processors
                if (window.Stripe) addTech('Payment', 'Stripe');
                if (window.paypal) addTech('Payment', 'PayPal');
                if (window.Square) addTech('Payment', 'Square');

                // Server/Hosting hints from headers (limited in browser)
                const poweredBy = document.querySelector('meta[name="powered-by"]')?.content;
                if (poweredBy) addTech('Server', poweredBy);

                return detected;
            })()
        })
        """
    else:
        code = """
        ({
            url: location.href,
            title: document.title,
            domain: location.hostname,
            protocol: location.protocol,
            readyState: document.readyState,
            width: window.innerWidth,
            height: window.innerHeight
        })
        """

    try:
        result = client.execute(code)

        if result.get("ok"):
            data = result.get("result", {})

            # Get userscript version
            userscript_version = client.get_userscript_version() or 'unknown'

            # If extended, also run the extended_info.js script
            if extended:
                try:
                    script_path = Path(__file__).parent / "scripts" / "extended_info.js"
                    if script_path.exists():
                        with _builtin_open(script_path) as f:
                            extended_script = f.read()
                        extended_result = client.execute(extended_script, timeout=10.0)
                        if extended_result.get("ok"):
                            extended_data = extended_result.get("result", {})
                            # Merge extended data into main data
                            data['_extended'] = extended_data
                except Exception:
                    pass  # Extended info is optional

                # Add server-side data for JSON output
                if output_json:
                    # Add response headers
                    headers = _get_response_headers(data.get('url'))
                    if headers:
                        data['responseHeaders'] = headers

                    # Add robots.txt
                    robots_data = _get_robots_txt(data.get('url'))
                    if robots_data:
                        data['robotsTxt'] = robots_data

                    # Add domain metrics
                    domain_metrics = _get_domain_metrics(data.get('domain'))
                    if domain_metrics:
                        data['domainMetrics'] = domain_metrics

                    # Add detected language
                    try:
                        from langdetect import detect, LangDetectException
                        para_code = "Array.from(document.querySelectorAll('p')).map(p => p.textContent).join(' ').substring(0, 5000)"
                        para_result = client.execute(para_code, timeout=5.0)
                        if para_result.get("ok"):
                            para_text = para_result.get("result", "")
                            if para_text and len(para_text.strip()) > 50:
                                try:
                                    detected = detect(para_text)
                                    data['detectedLanguage'] = detected

                                    # Check if detected language matches declared language
                                    declared_lang = data.get('specifiedLanguage', '').lower()
                                    if declared_lang and declared_lang != 'n/a':
                                        data['languageMatch'] = declared_lang == detected.lower()
                                except LangDetectException:
                                    pass
                    except ImportError:
                        pass

            # If JSON output is requested, output JSON and exit
            if output_json:
                import json
                data['userscriptVersion'] = userscript_version
                click.echo(json.dumps(data, indent=2))
                return

            # Basic info
            click.echo(f"URL:      {data.get('url', 'N/A')}")
            click.echo(f"Title:    {data.get('title', 'N/A')}")
            click.echo(f"Domain:   {data.get('domain', 'N/A')}")
            click.echo(f"Protocol: {data.get('protocol', 'N/A')}")
            click.echo(f"State:    {data.get('readyState', 'N/A')}")
            click.echo(f"Size:     {data.get('width', 'N/A')}x{data.get('height', 'N/A')}")

            if extended:
                click.echo(f"")
                click.echo("=== Extended Information ===")
                click.echo(f"")

                # Language and encoding (with natural language detection)
                declared_lang = data.get('specifiedLanguage', 'N/A')
                click.echo(f"Language:           {declared_lang}")

                # Detect actual language using langdetect
                try:
                    from langdetect import detect, LangDetectException
                    # Extract paragraph text for language detection
                    para_code = "Array.from(document.querySelectorAll('p')).map(p => p.textContent).join(' ').substring(0, 5000)"
                    para_result = client.execute(para_code, timeout=5.0)
                    if para_result.get("ok"):
                        para_text = para_result.get("result", "")
                        if para_text and len(para_text.strip()) > 50:
                            try:
                                detected = detect(para_text)  # Returns ISO 639-1 code (e.g., 'en', 'fr')
                                if detected:
                                    # Compare with declared language
                                    if declared_lang != 'N/A' and declared_lang.lower() != detected.lower():
                                        click.echo(f"  Detected:         {detected}")
                                        click.echo(f"  ⚠️  Language mismatch! Content appears to be \"{detected}\" but lang=\"{declared_lang}\"")
                                    else:
                                        click.echo(f"  Detected:         {detected} ✓ matches")
                            except LangDetectException:
                                pass  # Could not detect language
                except ImportError:
                    pass  # langdetect not installed
                except Exception:
                    pass  # Language detection failed

                click.echo(f"Character Set:      {data.get('charset', 'N/A')}")

                # Resources
                click.echo(f"")
                click.echo("Resources:")
                click.echo(f"  Scripts:          {data.get('scriptCount', 0)}")
                click.echo(f"  Stylesheets:      {data.get('stylesheetCount', 0)}")
                click.echo(f"  Images:           {data.get('imageCount', 0)}")
                click.echo(f"  Links:            {data.get('linkCount', 0)}")
                click.echo(f"  Forms:            {data.get('formCount', 0)}")
                click.echo(f"  Iframes:          {data.get('iframeCount', 0)}")

                # Performance Metrics (from extended data)
                extended_data = data.get('_extended', {})
                perf = extended_data.get('performance', {})
                if perf:
                    click.echo(f"")
                    click.echo("Performance:")
                    if perf.get('pageLoadTime'):
                        click.echo(f"  Page Load Time:    {perf['pageLoadTime']}s")
                    if perf.get('domContentLoaded'):
                        click.echo(f"  DOM Content Loaded: {perf['domContentLoaded']}s")
                    if perf.get('timeToFirstByte'):
                        click.echo(f"  Time to First Byte: {perf['timeToFirstByte']}ms")
                    if perf.get('firstPaint'):
                        click.echo(f"  First Paint:       {perf['firstPaint']}s")
                    if perf.get('firstContentfulPaint'):
                        click.echo(f"  First Contentful Paint: {perf['firstContentfulPaint']}s")
                    if perf.get('largestContentfulPaint'):
                        click.echo(f"  Largest Contentful Paint: {perf['largestContentfulPaint']}s")

                # Media Content (from extended data)
                media = extended_data.get('media', {})
                if media and (media.get('videos', 0) > 0 or media.get('audio', 0) > 0 or media.get('svgImages', 0) > 0):
                    click.echo(f"")
                    click.echo("Media:")
                    if media.get('videos', 0) > 0:
                        click.echo(f"  Videos:            {media['videos']}")
                    if media.get('audio', 0) > 0:
                        click.echo(f"  Audio:             {media['audio']}")
                    if media.get('svgImages', 0) > 0:
                        click.echo(f"  SVG Images:        {media['svgImages']}")

                # Content Stats (from extended data)
                content = extended_data.get('content', {})
                if content:
                    click.echo(f"")
                    click.echo("Content:")
                    if content.get('wordCount'):
                        click.echo(f"  Word Count:        ~{content['wordCount']:,} words")
                    if content.get('estimatedReadingTime'):
                        click.echo(f"  Reading Time:      ~{content['estimatedReadingTime']} minutes")
                    if content.get('paragraphs'):
                        click.echo(f"  Paragraphs:        {content['paragraphs']}")
                    if content.get('lists'):
                        click.echo(f"  Lists:             {content['lists']}")
                    if content.get('languageSwitchers', 0) > 0:
                        click.echo(f"  Language Switchers: {content['languageSwitchers']}")

                # Document dimensions
                click.echo(f"")
                click.echo("Document Dimensions:")
                click.echo(f"  Total Height:     {data.get('scrollHeight', 'N/A')}px")
                click.echo(f"  Total Width:      {data.get('scrollWidth', 'N/A')}px")

                # Storage
                click.echo(f"")
                click.echo("Storage:")
                cookie_count = data.get('cookieCount', 0)
                click.echo(f"  Cookies:          {cookie_count}")

                # Get actual cookie names
                if cookie_count > 0:
                    try:
                        cookie_code = "document.cookie.split(';').map(c => c.trim().split('=')[0]).filter(Boolean)"
                        cookie_result = client.execute(cookie_code, timeout=2.0)
                        if cookie_result.get("ok"):
                            cookie_names = cookie_result.get("result", [])
                            if cookie_names:
                                for i, name in enumerate(cookie_names[:8], 1):
                                    click.echo(f"    {i}. {name}")
                                if len(cookie_names) > 8:
                                    click.echo(f"    ... and {len(cookie_names) - 8} more")
                    except Exception:
                        pass

                local_kb = data.get('localStorageSize', 0) / 1024
                click.echo(f"  LocalStorage:     {local_kb:.2f} KB")

                # Get localStorage keys
                if local_kb > 0:
                    try:
                        ls_code = "Object.keys(localStorage)"
                        ls_result = client.execute(ls_code, timeout=2.0)
                        if ls_result.get("ok"):
                            ls_keys = ls_result.get("result", [])
                            if ls_keys:
                                for i, key in enumerate(ls_keys[:8], 1):
                                    click.echo(f"    {i}. {key}")
                                if len(ls_keys) > 8:
                                    click.echo(f"    ... and {len(ls_keys) - 8} more")
                    except Exception:
                        pass

                session_kb = data.get('sessionStorageSize', 0) / 1024
                click.echo(f"  SessionStorage:   {session_kb:.2f} KB")

                # Get sessionStorage keys
                if session_kb > 0:
                    try:
                        ss_code = "Object.keys(sessionStorage)"
                        ss_result = client.execute(ss_code, timeout=2.0)
                        if ss_result.get("ok"):
                            ss_keys = ss_result.get("result", [])
                            if ss_keys:
                                for i, key in enumerate(ss_keys[:8], 1):
                                    click.echo(f"    {i}. {key}")
                                if len(ss_keys) > 8:
                                    click.echo(f"    ... and {len(ss_keys) - 8} more")
                    except Exception:
                        pass

                click.echo(f"  Service Worker:   {'Yes' if data.get('hasServiceWorker') else 'No'}")

                # Security Info
                security = data.get('security', {})
                if security:
                    click.echo(f"")
                    click.echo("Security:")
                    click.echo(f"  HTTPS:            {'Yes' if security.get('isSecure') else 'No'}")
                    if security.get('isSecure') and security.get('hasMixedContent'):
                        click.echo(f"  Mixed Content:    ⚠️  Warning - Insecure resources detected")
                    if security.get('cspMeta'):
                        csp = security.get('cspMeta', '')
                        if len(csp) > 50:
                            csp = csp[:47] + '...'
                        click.echo(f"  CSP Meta:         {csp}")
                    if security.get('referrerPolicy'):
                        click.echo(f"  Referrer Policy:  {security.get('referrerPolicy')}")

                # Accessibility
                a11y = data.get('accessibility', {})
                if a11y:
                    click.echo(f"")
                    click.echo("Accessibility:")
                    click.echo(f"  Landmarks:        {a11y.get('landmarkCount', 0)} total")
                    landmarks = a11y.get('landmarks', {})
                    if landmarks:
                        for role, count in landmarks.items():
                            click.echo(f"    {role}: {count}")

                    # Heading structure
                    heading_structure = a11y.get('headingStructure', {})
                    total_headings = sum(heading_structure.values())
                    if total_headings > 0:
                        click.echo(f"  Headings:         {total_headings} total")
                        for level in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                            count = heading_structure.get(level, 0)
                            if count > 0:
                                click.echo(f"    {level.upper()}: {count}")

                    # A11y issues
                    img_no_alt = a11y.get('imagesWithoutAlt', 0)
                    if img_no_alt > 0:
                        click.echo(f"  ⚠️  Images w/o alt: {img_no_alt}")

                    form_issues = a11y.get('formLabelsIssues', {})
                    if form_issues.get('missingLabels', 0) > 0:
                        click.echo(f"  ⚠️  Form inputs w/o labels: {form_issues['missingLabels']}/{form_issues['total']}")

                    # Extended accessibility info
                    a11y_ext = extended_data.get('accessibility', {})
                    if a11y_ext:
                        if a11y_ext.get('linksWithoutText', 0) > 0:
                            click.echo(f"  ⚠️  Links w/o text: {a11y_ext['linksWithoutText']}")
                        if a11y_ext.get('buttonsWithoutLabels', 0) > 0:
                            click.echo(f"  ⚠️  Buttons w/o labels: {a11y_ext['buttonsWithoutLabels']}")
                        if a11y_ext.get('hasSkipLink'):
                            click.echo(f"  ✓  Page has skip link")
                        if not a11y_ext.get('langAttribute'):
                            click.echo(f"  ⚠️  Missing lang attribute")
                        if a11y_ext.get('ariaAttributeCount'):
                            click.echo(f"  ARIA Usage:        {a11y_ext['ariaAttributeCount']} attributes")

                # Structured Data (from extended data)
                structured = extended_data.get('structuredData', {})
                if structured and (structured.get('jsonLdCount', 0) > 0 or structured.get('microdataCount', 0) > 0):
                    click.echo(f"")
                    click.echo("Structured Data:")
                    if structured.get('jsonLdCount', 0) > 0:
                        click.echo(f"  JSON-LD:           {structured['jsonLdCount']} blocks")
                        types = structured.get('jsonLdTypes', [])
                        if types:
                            click.echo(f"    Types: {', '.join(types[:5])}")
                    if structured.get('microdataCount', 0) > 0:
                        click.echo(f"  Microdata:         {structured['microdataCount']} items")

                # SEO Metrics
                seo = data.get('seo', {})
                if seo:
                    click.echo(f"")
                    click.echo("SEO:")
                    if seo.get('canonical'):
                        canonical = seo['canonical']
                        if len(canonical) > 60:
                            canonical = canonical[:57] + '...'
                        click.echo(f"  Canonical:        {canonical}")
                    if seo.get('description'):
                        desc = seo['description']
                        if len(desc) > 60:
                            desc = desc[:57] + '...'
                        click.echo(f"  Description:      {desc}")
                    if seo.get('keywords'):
                        kw = seo['keywords']
                        if len(kw) > 60:
                            kw = kw[:57] + '...'
                        click.echo(f"  Keywords:         {kw}")
                    if seo.get('robots'):
                        click.echo(f"  Robots:           {seo['robots']}")

                    # Open Graph
                    og = seo.get('openGraph', {})
                    if og:
                        click.echo(f"  Open Graph:       {len(og)} tags")
                        for key in ['title', 'type', 'image', 'url']:
                            if key in og:
                                value = og[key]
                                if len(value) > 50:
                                    value = value[:47] + '...'
                                click.echo(f"    og:{key}: {value}")

                    # Twitter Card
                    twitter = seo.get('twitterCard', {})
                    if twitter:
                        click.echo(f"  Twitter Card:     {len(twitter)} tags")
                        for key in ['card', 'title', 'description', 'image']:
                            if key in twitter:
                                value = twitter[key]
                                if len(value) > 50:
                                    value = value[:47] + '...'
                                click.echo(f"    twitter:{key}: {value}")

                    # SEO Extras (from extended data)
                    seo_extra = extended_data.get('seoExtra', {})
                    if seo_extra:
                        if seo_extra.get('favicon'):
                            click.echo(f"  Favicon:           {seo_extra['favicon']}")
                        if seo_extra.get('sitemap'):
                            sitemap = seo_extra['sitemap']
                            if len(sitemap) > 50:
                                sitemap = sitemap[:47] + '...'
                            click.echo(f"  Sitemap:           {sitemap}")
                        alt_langs = seo_extra.get('alternateLanguages', [])
                        if alt_langs:
                            click.echo(f"  Alternate Languages: {len(alt_langs)}")
                            for lang in alt_langs[:3]:
                                click.echo(f"    {lang['lang']}")

                # Robots.txt
                robots_data = _get_robots_txt(data.get('url'))
                if robots_data and robots_data.get('exists'):
                    click.echo(f"")
                    click.echo("Robots.txt:")
                    click.echo(f"  Status:            Found")
                    click.echo(f"  Size:              {robots_data['size']:,} bytes ({robots_data['lines']} lines)")
                    if robots_data.get('userAgents'):
                        agents = robots_data['userAgents']
                        if len(agents) <= 3:
                            click.echo(f"  User-agents:       {', '.join(agents)}")
                        else:
                            click.echo(f"  User-agents:       {len(agents)} defined")
                    if robots_data.get('disallowRules', 0) > 0:
                        click.echo(f"  Disallow rules:    {robots_data['disallowRules']}")
                    if robots_data.get('allowRules', 0) > 0:
                        click.echo(f"  Allow rules:       {robots_data['allowRules']}")
                    if robots_data.get('sitemaps'):
                        sitemaps = robots_data['sitemaps']
                        click.echo(f"  Sitemaps:          {len(sitemaps)} declared")
                        for sitemap in sitemaps[:2]:
                            if len(sitemap) > 50:
                                sitemap = sitemap[:47] + '...'
                            click.echo(f"    {sitemap}")

                # Third-Party Resources (from extended data)
                third_party = extended_data.get('thirdParty', {})
                if third_party and third_party.get('externalDomainCount', 0) > 0:
                    click.echo(f"")
                    click.echo("Third-Party:")
                    click.echo(f"  External Domains:  {third_party['externalDomainCount']}")
                    domains = third_party.get('externalDomains', [])
                    if domains:
                        for domain in domains[:8]:
                            click.echo(f"    - {domain}")

                # Browser/Device Info
                device = data.get('device', {})
                if device:
                    click.echo(f"")
                    click.echo("Browser/Device:")
                    click.echo(f"  Platform:         {device.get('platform', 'N/A')}")
                    click.echo(f"  Language:         {device.get('language', 'N/A')}")
                    click.echo(f"  Screen:           {device.get('screenResolution', 'N/A')}")
                    click.echo(f"  Viewport:         {device.get('viewportSize', 'N/A')}")
                    click.echo(f"  Pixel Ratio:      {device.get('devicePixelRatio', 'N/A')}")
                    click.echo(f"  Touch Support:    {'Yes' if device.get('touchSupport') else 'No'}")
                    click.echo(f"  Cookies Enabled:  {'Yes' if device.get('cookiesEnabled') else 'No'}")
                    click.echo(f"  Online:           {'Yes' if device.get('onlineStatus') else 'No'}")

                    ua = device.get('userAgent', '')
                    if ua:
                        if len(ua) > 80:
                            # Show first 80 chars on first line, rest on second line
                            click.echo(f"  User Agent:       {ua[:80]}")
                            remaining = ua[80:]
                            if len(remaining) > 60:
                                remaining = remaining[:57] + '...'
                            click.echo(f"                    {remaining}")
                        else:
                            click.echo(f"  User Agent:       {ua}")

                # Technologies Detected
                technologies = data.get('technologies', {})
                if technologies:
                    click.echo(f"")
                    click.echo("Technologies Detected:")
                    for category, techs in sorted(technologies.items()):
                        if techs:
                            click.echo(f"  {category}:")
                            for tech in techs:
                                click.echo(f"    - {tech}")

                # Domain Metrics (fetched from server-side)
                domain_metrics = _get_domain_metrics(data.get('domain'))
                if domain_metrics:
                    click.echo(f"")
                    click.echo("Domain Metrics:")

                    if domain_metrics.get('ip'):
                        click.echo(f"  IP Address:       {domain_metrics['ip']}")

                    geo = domain_metrics.get('geolocation', {})
                    if geo:
                        location_parts = [geo.get('city'), geo.get('region'), geo.get('country')]
                        location = ', '.join([p for p in location_parts if p])
                        if location:
                            click.echo(f"  Location:         {location}")
                        if geo.get('isp'):
                            click.echo(f"  ISP:              {geo['isp']}")
                        if geo.get('org'):
                            click.echo(f"  Organization:     {geo['org']}")

                    whois = domain_metrics.get('whois', {})
                    if whois:
                        if whois.get('creation_date'):
                            click.echo(f"  Registered:       {whois['creation_date']}")
                        if whois.get('expiration_date'):
                            click.echo(f"  Expires:          {whois['expiration_date']}")
                        if whois.get('registrar'):
                            click.echo(f"  Registrar:        {whois['registrar']}")

                    ssl_info = domain_metrics.get('ssl', {})
                    if ssl_info:
                        if ssl_info.get('issuer'):
                            click.echo(f"  SSL Issuer:       {ssl_info['issuer']}")
                        if ssl_info.get('expiry'):
                            click.echo(f"  SSL Expires:      {ssl_info['expiry']}")
                        if ssl_info.get('days_remaining'):
                            days = ssl_info['days_remaining']
                            if days < 30:
                                click.echo(f"  SSL Status:       ⚠️  Expires in {days} days")
                            else:
                                click.echo(f"  SSL Status:       Valid ({days} days remaining)")

                # Network Summary (from extended data)
                network = extended_data.get('network', {})
                if network:
                    click.echo(f"")
                    click.echo("Network:")
                    if network.get('totalRequests'):
                        click.echo(f"  Total Requests:    {network['totalRequests']}")
                    if network.get('totalSize'):
                        size_mb = network['totalSize'] / (1024 * 1024)
                        click.echo(f"  Total Size:        {size_mb:.2f} MB")
                    largest = network.get('largestResource')
                    if largest:
                        size_kb = largest['size'] / 1024
                        click.echo(f"  Largest Resource:  {largest['name']} ({size_kb:.2f} KB)")

                # Fonts (from extended data)
                fonts = extended_data.get('fonts', {})
                if fonts and (fonts.get('googleFonts') or fonts.get('customFonts') or fonts.get('totalFontFiles', 0) > 0):
                    click.echo(f"")
                    click.echo("Fonts:")
                    google_fonts = fonts.get('googleFonts', [])
                    if google_fonts:
                        click.echo(f"  Google Fonts:      {len(google_fonts)}")
                        for font in google_fonts[:5]:
                            click.echo(f"    - {font}")
                        if len(google_fonts) > 5:
                            click.echo(f"    ... and {len(google_fonts) - 5} more")
                    custom_fonts = fonts.get('customFonts', [])
                    if custom_fonts:
                        click.echo(f"  Custom @font-face: {len(custom_fonts)}")
                        for font in custom_fonts[:5]:
                            click.echo(f"    - {font}")
                        if len(custom_fonts) > 5:
                            click.echo(f"    ... and {len(custom_fonts) - 5} more")
                    if fonts.get('totalFontFiles', 0) > 0:
                        click.echo(f"  Font Files:        {fonts['totalFontFiles']}")

                # Form Details (from extended data)
                forms = extended_data.get('forms', [])
                if forms:
                    click.echo(f"")
                    click.echo(f"Forms ({len(forms)}):")
                    for form in forms:
                        click.echo(f"  {form['id']}:")
                        click.echo(f"    Method:          {form['method']}")
                        if form['action'] and form['action'] != 'JavaScript':
                            action = form['action']
                            if len(action) > 50:
                                action = action[:47] + '...'
                            click.echo(f"    Action:          {action}")
                        click.echo(f"    Fields:          {len(form['fields'])}")
                        if form['issues']:
                            click.echo(f"    ⚠️  Issues:       {len(form['issues'])}")
                            for issue in form['issues'][:3]:
                                click.echo(f"      - {issue}")
                            if len(form['issues']) > 3:
                                click.echo(f"      ... and {len(form['issues']) - 3} more")

                # Core Web Vitals (from extended data)
                cwv = extended_data.get('coreWebVitals', {})
                if cwv:
                    click.echo(f"")
                    click.echo("Core Web Vitals:")
                    if 'cls' in cwv:
                        cls_val = float(cwv['cls'])
                        cls_status = '✓ Good' if cls_val < 0.1 else '⚠️  Needs Improvement' if cls_val < 0.25 else '❌ Poor'
                        click.echo(f"  CLS:               {cwv['cls']} ({cls_status})")
                    if 'fid' in cwv:
                        fid_val = int(cwv['fid'])
                        fid_status = '✓ Good' if fid_val < 100 else '⚠️  Needs Improvement' if fid_val < 300 else '❌ Poor'
                        click.echo(f"  FID:               {cwv['fid']}ms ({fid_status})")
                    if 'inp' in cwv:
                        inp_val = int(cwv['inp'])
                        inp_status = '✓ Good' if inp_val < 200 else '⚠️  Needs Improvement' if inp_val < 500 else '❌ Poor'
                        click.echo(f"  INP:               {cwv['inp']}ms ({inp_status})")

                # Security Headers and Response Headers
                headers = _get_response_headers(data.get('url'))
                if headers:
                    # Security Headers
                    security_headers = {
                        'xFrameOptions': 'X-Frame-Options',
                        'xContentTypeOptions': 'X-Content-Type-Options',
                        'strictTransportSecurity': 'Strict-Transport-Security',
                        'contentSecurityPolicy': 'Content-Security-Policy',
                        'permissionsPolicy': 'Permissions-Policy',
                        'referrerPolicy': 'Referrer-Policy',
                        'xXssProtection': 'X-XSS-Protection'
                    }

                    has_security_headers = any(headers.get(k) for k in security_headers.keys())
                    if has_security_headers:
                        click.echo(f"")
                        click.echo("Security Headers:")
                        for key, label in security_headers.items():
                            value = headers.get(key)
                            if value:
                                if len(value) > 60:
                                    value = value[:57] + '...'
                                click.echo(f"  {label}: {value}")

                    # Response Headers
                    response_headers = {
                        'server': 'Server',
                        'cacheControl': 'Cache-Control',
                        'contentEncoding': 'Content-Encoding',
                        'etag': 'ETag',
                        'lastModified': 'Last-Modified',
                        'contentType': 'Content-Type'
                    }

                    has_response_headers = any(headers.get(k) for k in response_headers.keys())
                    if has_response_headers:
                        click.echo(f"")
                        click.echo("Response Headers:")
                        for key, label in response_headers.items():
                            value = headers.get(key)
                            if value:
                                if len(value) > 60:
                                    value = value[:57] + '...'
                                click.echo(f"  {label}: {value}")

                # Meta tags
                meta_tags = data.get('metaTags', [])
                if meta_tags:
                    click.echo(f"")
                    click.echo(f"Meta Tags ({len(meta_tags)}):")
                    for meta in meta_tags:
                        # Format meta tag nicely
                        if 'name' in meta and 'content' in meta:
                            content = meta['content']
                            if len(content) > 60:
                                content = content[:57] + '...'
                            click.echo(f"  {meta['name']}: {content}")
                        elif 'property' in meta and 'content' in meta:
                            content = meta['content']
                            if len(content) > 60:
                                content = content[:57] + '...'
                            click.echo(f"  {meta['property']}: {content}")
                        elif 'charset' in meta:
                            click.echo(f"  charset: {meta['charset']}")
                        elif 'http-equiv' in meta:
                            click.echo(f"  {meta['http-equiv']}: {meta.get('content', '')}")

            click.echo(f"")
            click.echo(f"Userscript version: {userscript_version}")
        else:
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
def server():
    """Manage the bridge server."""
    pass


@server.command()
@click.option("-p", "--port", type=int, default=8765, help="Port to run on (default: 8765)")
@click.option("-d", "--daemon", is_flag=True, help="Run in background")
def start(port, daemon):
    """Start the bridge server."""
    client = BridgeClient(port=port)

    if client.is_alive():
        click.echo(f"Bridge server is already running on port {port}")
        return

    if daemon:
        # Run in background
        click.echo(f"Starting WebSocket bridge server in background on port {port}...")
        subprocess.Popen(
            [sys.executable, "-m", "zen.bridge_ws"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        # Wait a bit and check if it started
        import time
        time.sleep(0.5)
        if client.is_alive():
            click.echo("WebSocket server started successfully on ports 8765 (HTTP) and 8766 (WebSocket)")
        else:
            click.echo("Failed to start server", err=True)
            sys.exit(1)
    else:
        # Run in foreground
        from .bridge_ws import main as start_ws_server
        try:
            import asyncio
            asyncio.run(start_ws_server())
        except KeyboardInterrupt:
            click.echo("\nServer stopped")


@server.command()
def status():
    """Check bridge server status."""
    client = BridgeClient()

    if client.is_alive():
        status = client.get_status()
        if status:
            click.echo("Bridge server is running")
            click.echo(f"  Pending requests:   {status.get('pending', 0)}")
            click.echo(f"  Completed requests: {status.get('completed', 0)}")
        else:
            click.echo("Bridge server is running (status unavailable)")
    else:
        click.echo("Bridge server is not running")
        click.echo("Start it with: zen server start")
        sys.exit(1)


@server.command()
def stop():
    """Stop the bridge server."""
    click.echo("Note: Use Ctrl+C to stop the server if running in foreground")
    click.echo("For daemon mode, use: pkill -f 'zen.bridge_ws'")


@cli.command()
def repl():
    """
    Start an interactive REPL session.

    Execute JavaScript interactively. Type 'exit' or press Ctrl+D to quit.
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    click.echo("Zen Browser REPL - Type JavaScript code, 'exit' to quit")
    click.echo("")

    # Get initial page info
    try:
        result = client.execute("({url: location.href, title: document.title})")
        if result.get("ok"):
            data = result.get("result", {})
            click.echo(f"Connected to: {data.get('title', 'Unknown')} ({data.get('url', 'Unknown')})")
            click.echo("")
    except:
        pass

    while True:
        try:
            code = click.prompt("zen>", prompt_suffix=" ", default="", show_default=False)

            if not code.strip():
                continue

            if code.strip().lower() in ["exit", "quit"]:
                break

            try:
                result = client.execute(code, timeout=10.0)
                output = format_output(result, "auto")
                if output:
                    click.echo(output)
            except (ConnectionError, TimeoutError, RuntimeError) as e:
                click.echo(f"Error: {e}", err=True)

        except (EOFError, KeyboardInterrupt):
            click.echo("")
            break

    click.echo("Goodbye!")


@cli.command()
@click.argument("selector")
@click.option("-c", "--color", default="red", help="Outline color (default: red)")
@click.option("--clear", is_flag=True, help="Clear all highlights")
def highlight(selector, color, clear):
    """
    Highlight elements matching a CSS selector on the page.

    Adds a 2px dashed outline around matching elements.

    Examples:

        zen highlight "h1, h2"

        zen highlight ".error" --color orange

        zen highlight "a" --clear
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    if clear:
        # Clear all highlights
        code = """
        document.querySelectorAll('[data-zen-highlight]').forEach(el => {
            el.style.outline = '';
            el.removeAttribute('data-zen-highlight');
        });
        'Highlights cleared'
        """
    else:
        # Add highlights
        code = f"""
        (function(selector, color) {{
            const elements = document.querySelectorAll(selector);

            if (elements.length === 0) {{
                return `No elements found matching: ${{selector}}`;
            }}

            // Clear previous highlights
            document.querySelectorAll('[data-zen-highlight]').forEach(el => {{
                el.style.outline = '';
                el.removeAttribute('data-zen-highlight');
            }});

            // Add new highlights
            elements.forEach((el, index) => {{
                el.style.outline = `2px dashed ${{color}}`;
                el.setAttribute('data-zen-highlight', index);
            }});

            return `Highlighted ${{elements.length}} element(s) matching: ${{selector}}`;
        }})('{selector}', '{color}')
        """

    try:
        result = client.execute(code, timeout=10.0)
        output = format_output(result, "auto")
        click.echo(output)

        if not result.get("ok"):
            sys.exit(1)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def userscript():
    """Display the userscript that needs to be installed in your browser."""
    script_path = Path(__file__).parent.parent / "userscript.js"

    if script_path.exists():
        click.echo(f"Userscript location: {script_path}")
        click.echo("")
        click.echo("To install:")
        click.echo("1. Install a userscript manager (Tampermonkey, Greasemonkey, Violentmonkey)")
        click.echo("2. Create a new script and paste the contents of userscript.js")
        click.echo("3. Save and enable the script")
        click.echo("")
        click.echo("Or use: cat userscript.js | pbcopy  (to copy to clipboard on macOS)")
    else:
        click.echo(f"Error: userscript.js not found at {script_path}", err=True)
        sys.exit(1)


@cli.command()
@click.option("-o", "--output", type=click.Path(), default=None, help="Output directory (default: ~/Downloads/<domain>)")
@click.option("--list", "list_only", is_flag=True, help="Only list files without downloading")
@click.option("-t", "--timeout", type=float, default=30.0, help="Timeout in seconds (default: 30)")
def download(output, list_only, timeout):
    """
    Find and download files from the current page.

    Discovers images, PDFs, videos, audio files, documents and archives.
    Uses interactive selection with gum choose.

    Examples:

        zen download

        zen download --output ~/Downloads

        zen download --list
    """
    import requests
    import os

    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Execute the find_downloads script
    script_path = Path(__file__).parent / "scripts" / "find_downloads.js"

    if not script_path.exists():
        click.echo(f"Error: find_downloads.js script not found at {script_path}", err=True)
        sys.exit(1)

    click.echo("Scanning page for downloadable files...")

    try:
        result = client.execute_file(str(script_path), timeout=timeout)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        result_data = result.get("result", {})

        # Handle new format with url and files
        if isinstance(result_data, dict) and 'files' in result_data:
            files_by_category = result_data['files']
            page_url = result_data.get('url', '')
        else:
            # Fallback for old format
            files_by_category = result_data
            page_url = ""

        # Count total files
        total_files = sum(len(files) for files in files_by_category.values())

        if total_files == 0:
            click.echo("No downloadable files found on this page.")
            return

        # Determine output directory
        if output is None:
            # Default: ~/Downloads/<domain>
            try:
                from urllib.parse import urlparse
                domain = urlparse(page_url).hostname or "unknown"
                domain = domain.replace('www.', '')  # Remove www. prefix
                downloads_dir = Path.home() / "Downloads" / domain
            except Exception:
                downloads_dir = Path.home() / "Downloads" / "zen-downloads"
        else:
            downloads_dir = Path(output)

        # Build options list for gum choose
        options = []
        option_map = {}  # Map display text to actual data

        # Category labels (lowercase)
        category_names = {
            'images': 'images',
            'pdfs': 'PDF documents',
            'videos': 'videos',
            'audio': 'audio files',
            'documents': 'documents',
            'archives': 'archives'
        }

        # Add "Download all" options per category
        for category, files in files_by_category.items():
            if files:
                count = len(files)
                display = f"Download all {category_names.get(category, category)} ({count} files)"
                options.append(display)
                option_map[display] = {'type': 'category', 'category': category, 'files': files}

        # Add separator
        if options:
            separator = "─" * 60
            options.append(separator)
            option_map[separator] = {'type': 'separator'}

        # Add individual files grouped by category
        for category, files in files_by_category.items():
            if files:
                # Add category header
                header = f"--- {category_names.get(category, category.upper())} ---"
                options.append(header)
                option_map[header] = {'type': 'header'}

                # Add individual files
                for file_info in files:
                    filename = file_info['filename']
                    url = file_info['url']

                    # Try to get file size if in list mode
                    display = f"  {filename}"
                    options.append(display)
                    option_map[display] = {
                        'type': 'file',
                        'filename': filename,
                        'url': url,
                        'category': category
                    }

        # List only mode
        if list_only:
            click.echo(f"\nFound {total_files} downloadable files:\n")
            for option in options:
                if option_map.get(option, {}).get('type') not in ['separator', 'category']:
                    click.echo(option)
            return

        # Simple numbered list selection
        click.echo(f"\nFound {total_files} files. Select what to download:\n")

        # Build simple menu
        menu_options = []

        # Find largest image if we have images
        largest_image = None
        if 'images' in files_by_category and files_by_category['images']:
            images_with_dims = [img for img in files_by_category['images']
                              if img.get('width', 0) > 0 and img.get('height', 0) > 0]
            if images_with_dims:
                # Find image with largest area
                largest_image = max(images_with_dims,
                                  key=lambda img: img.get('width', 0) * img.get('height', 0))

        # Add largest image option first
        if largest_image:
            width = largest_image.get('width', 0)
            height = largest_image.get('height', 0)
            menu_options.append({
                'text': f"Download the largest image ({width}×{height}px)",
                'data': {'type': 'file', 'files': [largest_image]}
            })

        # Add category download options
        for category, files in files_by_category.items():
            if files:
                count = len(files)
                menu_options.append({
                    'text': f"Download all {category_names.get(category, category)} ({count} files)",
                    'data': {'type': 'category', 'category': category, 'files': files}
                })

        # Display menu
        for i, opt in enumerate(menu_options, 1):
            click.echo(f" {i}. {opt['text']}")

        click.echo(f"\nFiles will be saved to:")
        click.echo(f"{downloads_dir}\n")

        try:
            choice = click.prompt("Enter number to download (0 to cancel)", type=int, default=0)

            if choice == 0:
                click.echo("Cancelled.")
                return

            if choice < 1 or choice > len(menu_options):
                click.echo("Invalid selection.")
                return

            selected_data = menu_options[choice - 1]['data']

        except (KeyboardInterrupt, EOFError):
            click.echo("\nCancelled.")
            return
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            return

        # Process selection (selected_data already set above)
        if not selected_data:
            click.echo("Invalid selection.")
            return

        # Prepare download list
        files_to_download = []

        if selected_data['type'] == 'category':
            # Download all files in category
            files_to_download = selected_data['files']
            click.echo(f"\nDownloading {len(files_to_download)} files...")
        elif selected_data['type'] == 'file':
            # Download file(s) - can be a list
            files_to_download = selected_data['files']
            click.echo(f"\nDownloading {len(files_to_download)} file(s)...")

        # Create output directory if needed
        downloads_dir.mkdir(parents=True, exist_ok=True)

        # Download files
        success_count = 0
        for file_info in files_to_download:
            filename = file_info['filename']
            url = file_info['url']
            output_path = downloads_dir / filename

            try:
                click.echo(f"  Downloading {filename}...")
                response = requests.get(url, timeout=30)
                response.raise_for_status()

                with _builtin_open(output_path, 'wb') as f:
                    f.write(response.content)

                file_size = len(response.content)
                size_mb = file_size / (1024 * 1024)
                if size_mb >= 1:
                    size_str = f"{size_mb:.1f} MB"
                else:
                    size_str = f"{file_size / 1024:.1f} KB"

                click.echo(f"    Saved to {output_path} ({size_str})")
                success_count += 1

            except Exception as e:
                click.echo(f"    Error downloading {filename}: {e}", err=True)

        click.echo(f"\nDownloaded {success_count} of {len(files_to_download)} files successfully.")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("text")
@click.option("--selector", "-s", default=None, help="CSS selector of element to type into")
def send(text, selector):
    """
    Send text to the browser by typing it character by character.

    Types the given text into the currently focused input field,
    or into a specific element if --selector is provided.

    Examples:
        zen send "Hello World"
        zen send "test@example.com" --selector "input[type=email]"
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Focus the element first if selector provided
    if selector:
        focus_code = f"""
        (function() {{
            const el = document.querySelector('{selector}');
            if (!el) {{
                return {{ error: 'Element not found: {selector}' }};
            }}
            el.focus();
            return {{ ok: true }};
        }})()
        """
        result = client.execute(focus_code, timeout=60.0)
        if not result.get("ok") or result.get("result", {}).get("error"):
            error = result.get("error") or result.get("result", {}).get("error", "Unknown error")
            click.echo(f"Error focusing element: {error}", err=True)
            sys.exit(1)

    # Load and execute the send_keys script
    script_path = Path(__file__).parent / "scripts" / "send_keys.js"
    with _builtin_open(script_path) as f:
        script = f.read()

    # Replace placeholder with properly escaped text
    # Escape quotes and backslashes for JavaScript
    escaped_text = text.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
    code = script.replace('TEXT_PLACEHOLDER', f'"{escaped_text}"')

    try:
        result = client.execute(code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})
        if response.get("error"):
            click.echo(f"Error: {response['error']}", err=True)
            if response.get("hint"):
                click.echo(f"Hint: {response['hint']}", err=True)
            sys.exit(1)

        click.echo(response.get("message", "Text sent successfully"))

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("selector", required=False)
def inspect(selector):
    """
    Select an element and show its details.

    If no selector is provided, shows details of the currently selected element.

    Examples:
        zen inspect "h1"              # Select and show details
        zen inspect "#header"
        zen inspect ".main-content"
        zen inspect                   # Show currently selected element
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # If no selector provided, just show the currently marked element
    if not selector:
        # Redirect to 'inspected' command
        return inspected.callback()

    # Mark the element
    mark_code = f"""
    (function() {{
        const el = document.querySelector('{selector}');
        if (!el) {{
            return {{ error: 'Element not found: {selector}' }};
        }}

        // Store reference
        window.__ZEN_INSPECTED_ELEMENT__ = el;

        // Highlight it briefly
        const originalOutline = el.style.outline;
        el.style.outline = '3px solid #0066ff';
        setTimeout(() => {{
            el.style.outline = originalOutline;
        }}, 1000);

        return {{ ok: true, message: 'Element marked for inspection' }};
    }})()
    """

    try:
        result = client.execute(mark_code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})
        if response.get("error"):
            click.echo(f"Error: {response['error']}", err=True)
            sys.exit(1)

        click.echo(f"Selected element: {selector}")

        # Now show details immediately by calling inspected
        click.echo("")
        return inspected.callback()

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def inspected():
    """
    Get information about the currently inspected element.

    Shows details about the element from DevTools inspection or from 'zen inspect'.

    To capture element from DevTools:
        1. Right-click element → Inspect
        2. In DevTools Console: zenStore()
        3. Run: zen inspected

    Or select programmatically:
        zen inspect "h1"
        zen inspected
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Load the get_inspected.js script
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'get_inspected.js')

    try:
        with _builtin_open(script_path, 'r') as f:
            code = f.read()
    except FileNotFoundError:
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    try:
        result = client.execute(code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})
        if response.get("error"):
            click.echo(f"Error: {response['error']}", err=True)
            if response.get("hint"):
                click.echo(f"Hint: {response['hint']}", err=True)
            sys.exit(1)

        # Display info
        click.echo(f"Tag:      <{response['tag']}>")
        click.echo(f"Selector: {response['selector']}")

        if response.get('parentTag'):
            click.echo(f"Parent:   <{response['parentTag']}>")

        if response.get('id'):
            click.echo(f"ID:       {response['id']}")

        if response.get('classes') and len(response['classes']) > 0:
            click.echo(f"Classes:  {', '.join(response['classes'])}")

        if response.get('textContent'):
            text = response['textContent']
            if len(text) > 60:
                text = text[:60] + '...'
            click.echo(f"Text:     {text}")

        # Dimensions
        dim = response['dimensions']
        click.echo(f"\nDimensions:")
        click.echo(f"  Position: x={dim['left']}, y={dim['top']}")
        click.echo(f"  Size:     {dim['width']}×{dim['height']}px")
        click.echo(f"  Bounds:   top={dim['top']}, right={dim['right']}, bottom={dim['bottom']}, left={dim['left']}")

        # Visibility
        vis = response.get('visibilityDetails', {})
        click.echo(f"\nVisibility:")
        click.echo(f"  Visible:     {'Yes' if response.get('visible') else 'No'}")
        click.echo(f"  In viewport: {'Yes' if vis.get('inViewport') else 'No'}")
        if vis.get('displayNone'):
            click.echo(f"  Issue:       display: none")
        if vis.get('visibilityHidden'):
            click.echo(f"  Issue:       visibility: hidden")
        if vis.get('opacityZero'):
            click.echo(f"  Issue:       opacity: 0")
        if vis.get('offScreen'):
            click.echo(f"  Issue:       positioned off-screen")

        # Accessibility
        a11y = response.get('accessibility', {})
        click.echo(f"\nAccessibility:")
        click.echo(f"  Role:            {a11y.get('role', 'N/A')}")

        # Accessible Name (computed)
        accessible_name = a11y.get('accessibleName', '')
        name_source = a11y.get('accessibleNameSource', 'none')
        if accessible_name:
            # Truncate if too long
            display_name = accessible_name if len(accessible_name) <= 50 else accessible_name[:50] + '...'
            click.echo(f"  Accessible Name: \"{display_name}\"")
            click.echo(f"  Name computed from: {name_source}")
        else:
            click.echo(f"  Accessible Name: (none)")
            if name_source == 'missing alt attribute':
                click.echo(f"  ⚠️  Warning: Image missing alt attribute")
            elif name_source == 'none':
                click.echo(f"  ⚠️  Warning: No accessible name found")

        if a11y.get('ariaLabel'):
            click.echo(f"  ARIA Label:      {a11y['ariaLabel']}")
        if a11y.get('ariaLabelledBy'):
            click.echo(f"  ARIA LabelledBy: {a11y['ariaLabelledBy']}")
        if a11y.get('alt'):
            click.echo(f"  Alt text:        {a11y['alt']}")
        click.echo(f"  Focusable:       {'Yes' if a11y.get('focusable') else 'No'}")
        if a11y.get('tabIndex') is not None:
            click.echo(f"  Tab index:       {a11y['tabIndex']}")
        if a11y.get('disabled'):
            click.echo(f"  Disabled:        Yes")
        if a11y.get('ariaHidden'):
            click.echo(f"  ARIA Hidden:     {a11y['ariaHidden']}")

        # Semantic info
        semantic = response.get('semantic', {})
        if semantic.get('isInteractive') or semantic.get('isFormElement') or semantic.get('isLandmark'):
            click.echo(f"\nSemantic:")
            if semantic.get('isInteractive'):
                click.echo(f"  Interactive element")
            if semantic.get('isFormElement'):
                click.echo(f"  Form element")
            if semantic.get('isLandmark'):
                click.echo(f"  Landmark element")
            if semantic.get('hasClickHandler'):
                click.echo(f"  Has click handler")

        # Children
        click.echo(f"\nStructure:")
        click.echo(f"  Children: {response.get('childCount', 0)}")

        # Styles
        click.echo(f"\nStyles:")
        for key, value in response['styles'].items():
            click.echo(f"  {key}: {value}")

        # Attributes
        if response.get('attributes'):
            click.echo(f"\nAttributes:")
            for key, value in response['attributes'].items():
                if len(str(value)) > 50:
                    value = str(value)[:50] + '...'
                click.echo(f"  {key}: {value}")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command(name="click")
@click.argument("selector", required=False, default="$0")
def click_element(selector):
    """
    Click on an element.

    Uses the stored element from 'zen inspect' by default, or specify a selector.

    Examples:
        # Click on stored element:
        zen inspect "button#submit"
        zen click

        # Click directly on element:
        zen click "button#submit"
        zen click ".primary-button"
    """
    _perform_click(selector, "click")


@cli.command(name="double-click")
@click.argument("selector", required=False, default="$0")
def double_click(selector):
    """
    Double-click on an element.

    Uses the stored element from 'zen inspect' by default, or specify a selector.

    Examples:
        zen double-click "div.item"
        zen inspect "div.item"
        zen double-click
    """
    _perform_click(selector, "dblclick")


@cli.command(name="doubleclick", hidden=True)
@click.argument("selector", required=False, default="$0")
def doubleclick_alias(selector):
    """Alias for double-click command."""
    _perform_click(selector, "dblclick")


@cli.command(name="right-click")
@click.argument("selector", required=False, default="$0")
def right_click(selector):
    """
    Right-click (context menu) on an element.

    Uses the stored element from 'zen inspect' by default, or specify a selector.

    Examples:
        zen right-click "a.download-link"
        zen inspect "a.download-link"
        zen right-click
    """
    _perform_click(selector, "contextmenu")


@cli.command(name="rightclick", hidden=True)
@click.argument("selector", required=False, default="$0")
def rightclick_alias(selector):
    """Alias for right-click command."""
    _perform_click(selector, "contextmenu")


def _perform_click(selector, click_type):
    """Helper function to perform click actions."""
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Load the click script
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'click_element.js')

    try:
        with _builtin_open(script_path, 'r') as f:
            script = f.read()
    except FileNotFoundError:
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    # Replace placeholders
    escaped_selector = selector.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
    code = script.replace('SELECTOR_PLACEHOLDER', escaped_selector)
    code = code.replace('CLICK_TYPE_PLACEHOLDER', click_type)

    try:
        result = client.execute(code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})

        if response.get("error"):
            click.echo(f"Error: {response['error']}", err=True)
            sys.exit(1)

        # Show confirmation
        action_name = {
            'click': 'Clicked',
            'dblclick': 'Double-clicked',
            'contextmenu': 'Right-clicked'
        }.get(click_type, 'Clicked')

        click.echo(f"{action_name}: {response.get('element', 'element')}")
        pos = response.get('position', {})
        if pos:
            click.echo(f"Position: x={pos.get('x')}, y={pos.get('y')}")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("selector")
@click.option("--timeout", "-t", type=int, default=30, help="Timeout in seconds (default: 30)")
@click.option("--visible", is_flag=True, help="Wait for element to be visible")
@click.option("--hidden", is_flag=True, help="Wait for element to be hidden")
@click.option("--text", type=str, help="Wait for element to contain specific text")
def wait(selector, timeout, visible, hidden, text):
    """
    Wait for an element to appear, be visible, hidden, or contain text.

    By default, waits for element to exist in the DOM.

    Examples:
        # Wait for element to exist (up to 30 seconds):
        zen wait "button#submit"

        # Wait for element to be visible:
        zen wait ".modal" --visible

        # Wait for element to be hidden:
        zen wait ".loading-spinner" --hidden

        # Wait for element to contain text:
        zen wait "h1" --text "Success"

        # Custom timeout (10 seconds):
        zen wait "div.result" --timeout 10
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Determine wait type
    if hidden:
        wait_type = 'hidden'
    elif visible:
        wait_type = 'visible'
    elif text:
        wait_type = 'text'
    else:
        wait_type = 'exists'

    # Load the wait script
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'wait_for.js')

    try:
        with _builtin_open(script_path, 'r') as f:
            script = f.read()
    except FileNotFoundError:
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    # Replace placeholders
    escaped_selector = selector.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
    escaped_text = (text or '').replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
    timeout_ms = timeout * 1000

    code = script.replace('SELECTOR_PLACEHOLDER', escaped_selector)
    code = code.replace('WAIT_TYPE_PLACEHOLDER', wait_type)
    code = code.replace('TEXT_PLACEHOLDER', escaped_text)
    code = code.replace('TIMEOUT_PLACEHOLDER', str(timeout_ms))

    # Show waiting message
    wait_msg = {
        'exists': f'Waiting for element: {selector}',
        'visible': f'Waiting for element to be visible: {selector}',
        'hidden': f'Waiting for element to be hidden: {selector}',
        'text': f'Waiting for element to contain "{text}": {selector}'
    }.get(wait_type, f'Waiting for: {selector}')

    click.echo(wait_msg)

    try:
        # Use longer timeout for the request (add 5 seconds buffer)
        result = client.execute(code, timeout=timeout + 5)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})

        if response.get("error"):
            click.echo(f"Error: {response['error']}", err=True)
            sys.exit(1)

        if response.get("timeout"):
            click.echo(f"✗ Timeout: {response.get('message', 'Operation timed out')}", err=True)
            sys.exit(1)

        # Success!
        waited_sec = response.get('waited', 0) / 1000
        click.echo(f"✓ {response.get('status', 'Condition met')}")
        if response.get('element'):
            click.echo(f"  Element: {response['element']}")
        click.echo(f"  Waited: {waited_sec:.2f}s")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("url")
@click.option("--wait", is_flag=True, help="Wait for page to finish loading")
@click.option("--timeout", "-t", type=int, default=30, help="Timeout in seconds when using --wait (default: 30)")
def open(url, wait, timeout):
    """
    Navigate to a URL.

    Examples:
        # Navigate to a URL:
        zen open "https://example.com"

        # Navigate and wait for page load:
        zen open "https://example.com" --wait

        # Navigate with custom timeout:
        zen open "https://example.com" --wait --timeout 60
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Basic navigation code
    nav_code = f"""
        window.location.href = {json.dumps(url)};
        true;
    """

    # If wait flag is set, wait for page load
    if wait:
        nav_code = f"""
            (async () => {{
                window.location.href = {json.dumps(url)};

                // Wait for navigation to complete
                await new Promise((resolve, reject) => {{
                    const startTime = Date.now();
                    const timeoutMs = {timeout * 1000};

                    const checkLoad = () => {{
                        if (document.readyState === 'complete') {{
                            resolve();
                        }} else if (Date.now() - startTime > timeoutMs) {{
                            reject(new Error('Page load timeout'));
                        }} else {{
                            setTimeout(checkLoad, 100);
                        }}
                    }};

                    if (document.readyState === 'complete') {{
                        resolve();
                    }} else {{
                        window.addEventListener('load', resolve, {{ once: true }});
                        setTimeout(() => reject(new Error('Page load timeout')), timeoutMs);
                    }}
                }});

                return {{ ok: true, url: window.location.href }};
            }})();
        """

    try:
        click.echo(f"Opening: {url}")
        result = client.execute(nav_code, timeout=timeout + 5 if wait else 10.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        if wait:
            response = result.get("result", {})
            if response.get("ok"):
                click.echo(f"✓ Page loaded: {response.get('url', url)}")
            else:
                click.echo("Navigation initiated")
        else:
            click.echo("✓ Navigation initiated")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def back():
    """
    Go back to the previous page in browser history.

    Example:
        zen back
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    code = "window.history.back(); true;"

    try:
        result = client.execute(code, timeout=10.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        click.echo("✓ Navigated back")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command(hidden=True)
def previous():
    """Alias for 'back' command."""
    ctx = click.get_current_context()
    ctx.invoke(back)


@cli.command()
def forward():
    """
    Go forward to the next page in browser history.

    Example:
        zen forward
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    code = "window.history.forward(); true;"

    try:
        result = client.execute(code, timeout=10.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        click.echo("✓ Navigated forward")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command(hidden=True)
def next():
    """Alias for 'forward' command."""
    ctx = click.get_current_context()
    ctx.invoke(forward)


@cli.command()
@click.option("--hard", is_flag=True, help="Hard reload (bypass cache)")
def reload(hard):
    """
    Reload the current page.

    Examples:
        # Normal reload:
        zen reload

        # Hard reload (bypass cache):
        zen reload --hard
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    if hard:
        code = "window.location.reload(true); true;"
        msg = "✓ Hard reload initiated"
    else:
        code = "window.location.reload(); true;"
        msg = "✓ Reload initiated"

    try:
        result = client.execute(code, timeout=10.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        click.echo(msg)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command(hidden=True)
@click.option("--hard", is_flag=True, help="Hard reload (bypass cache)")
def refresh(hard):
    """
    Reload the current page (alias for 'reload').

    Examples:
        # Normal reload:
        zen refresh

        # Hard reload (bypass cache):
        zen refresh --hard
    """
    # Just call the reload function
    from click.testing import CliRunner
    ctx = click.get_current_context()
    ctx.invoke(reload, hard=hard)


@cli.group()
def cookies():
    """Manage browser cookies."""
    pass


@cookies.command(name="list")
def cookies_list():
    """
    List all cookies for the current page.

    Example:
        zen cookies list
    """
    _execute_cookie_action('list')


@cookies.command(name="get")
@click.argument("name")
def cookies_get(name):
    """
    Get the value of a specific cookie.

    Example:
        zen cookies get session_id
    """
    _execute_cookie_action('get', cookie_name=name)


@cookies.command(name="set")
@click.argument("name")
@click.argument("value")
@click.option("--max-age", type=int, help="Max age in seconds")
@click.option("--expires", type=str, help="Expiration date (e.g., 'Wed, 21 Oct 2025 07:28:00 GMT')")
@click.option("--path", type=str, default="/", help="Cookie path (default: /)")
@click.option("--domain", type=str, help="Cookie domain")
@click.option("--secure", is_flag=True, help="Secure flag (HTTPS only)")
@click.option("--same-site", type=click.Choice(['Strict', 'Lax', 'None'], case_sensitive=False), help="SameSite attribute")
def cookies_set(name, value, max_age, expires, path, domain, secure, same_site):
    """
    Set a cookie.

    Examples:
        zen cookies set session_id abc123
        zen cookies set token xyz --max-age 3600
        zen cookies set user_pref dark --path / --secure
    """
    options = {
        'path': path
    }
    if max_age:
        options['maxAge'] = max_age
    if expires:
        options['expires'] = expires
    if domain:
        options['domain'] = domain
    if secure:
        options['secure'] = True
    if same_site:
        options['sameSite'] = same_site

    _execute_cookie_action('set', cookie_name=name, cookie_value=value, options=options)


@cookies.command(name="delete")
@click.argument("name")
def cookies_delete(name):
    """
    Delete a specific cookie.

    Example:
        zen cookies delete session_id
    """
    _execute_cookie_action('delete', cookie_name=name)


@cookies.command(name="clear")
def cookies_clear():
    """
    Clear all cookies for the current page.

    Example:
        zen cookies clear
    """
    _execute_cookie_action('clear')


def _execute_cookie_action(action, cookie_name='', cookie_value='', options=None):
    """Helper function to execute cookie actions."""
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Load the cookies script
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'cookies.js')

    try:
        with _builtin_open(script_path, 'r') as f:
            script = f.read()
    except FileNotFoundError:
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    # Replace placeholders
    options_json = json.dumps(options if options else {})
    code = script.replace('ACTION_PLACEHOLDER', action)
    code = code.replace('NAME_PLACEHOLDER', cookie_name)
    code = code.replace('VALUE_PLACEHOLDER', cookie_value)
    code = code.replace('OPTIONS_PLACEHOLDER', options_json)

    try:
        result = client.execute(code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})

        if response.get("error"):
            click.echo(f"Error: {response['error']}", err=True)
            sys.exit(1)

        # Display results based on action
        if action == 'list':
            cookies_dict = response.get('cookies', {})
            count = response.get('count', 0)

            if count == 0:
                click.echo("No cookies found")
            else:
                click.echo(f"Cookies ({count}):\n")
                for name, value in cookies_dict.items():
                    # Truncate long values
                    display_value = value if len(value) <= 60 else value[:60] + '...'
                    click.echo(f"  {name} = {display_value}")

        elif action == 'get':
            name = response.get('name')
            value = response.get('value')
            exists = response.get('exists')

            if exists:
                click.echo(f"{name} = {value}")
            else:
                click.echo(f"Cookie not found: {name}", err=True)
                sys.exit(1)

        elif action == 'set':
            click.echo(f"✓ Cookie set: {response.get('name')} = {response.get('value')}")

        elif action == 'delete':
            click.echo(f"✓ Cookie deleted: {response.get('name')}")

        elif action == 'clear':
            deleted = response.get('deleted', 0)
            click.echo(f"✓ Cleared {deleted} cookie(s)")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--raw", is_flag=True, help="Output only the text without formatting")
def selected(raw):
    """
    Get the current text selection in the browser.

    Returns the selected text along with metadata like position and container element.

    Examples:
        # Get selection with metadata:
        zen selected

        # Get just the raw text (no formatting):
        zen selected --raw
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Load the get_selection.js script
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'get_selection.js')

    try:
        with _builtin_open(script_path, 'r') as f:
            code = f.read()
    except FileNotFoundError:
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    try:
        result = client.execute(code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})

        if not response.get('hasSelection'):
            if not raw:
                click.echo("No text selected")
                click.echo("Hint: Select some text in the browser first, then run: zen selected")
            sys.exit(0)

        text = response.get('text', '')

        # Raw mode: just print the text, nothing else
        if raw:
            click.echo(text, nl=False)
            return

        # Display selection info
        click.echo(f"Selected Text ({response.get('length', 0)} characters):")
        click.echo("")

        # Show text (with proper formatting for long selections)
        if len(text) <= 200:
            click.echo(f'"{text}"')
        else:
            # Show first 200 chars with ellipsis
            click.echo(f'"{text[:200]}..."')
            click.echo("")
            click.echo(f"(showing first 200 of {len(text)} characters)")

        # Position info
        pos = response.get('position', {})
        click.echo(f"\nPosition:")
        click.echo(f"  x={pos.get('x')}, y={pos.get('y')}")
        click.echo(f"  Size: {pos.get('width')}×{pos.get('height')}px")

        # Container element
        container = response.get('container', {})
        if container.get('tag'):
            click.echo(f"\nContainer:")
            click.echo(f"  Tag:   <{container['tag']}>")
            if container.get('id'):
                click.echo(f"  ID:    {container['id']}")
            if container.get('class'):
                click.echo(f"  Class: {container['class']}")

        # HTML if different from text
        html = response.get('html', '')
        if html and html.strip() != text.strip():
            click.echo(f"\nHTML:")
            if len(html) <= 200:
                click.echo(f"  {html}")
            else:
                click.echo(f"  {html[:200]}...")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--selector", "-s", required=True, help="CSS selector of element to screenshot (or use $0 for inspected element)")
@click.option("--output", "-o", type=click.Path(), default=None, help="Output file path")
def screenshot(selector, output):
    """
    Take a screenshot of a specific element.

    Captures a DOM element and saves it as a PNG image.
    Use $0 to screenshot the currently inspected element in DevTools.

    Examples:
        zen screenshot --selector "#main"
        zen screenshot -s ".hero-section" -o hero.png
        zen screenshot -s "$0" -o inspected.png
    """
    import base64
    from datetime import datetime

    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Load screenshot script
    script_path = Path(__file__).parent / "scripts" / "screenshot_element.js"
    with _builtin_open(script_path) as f:
        script = f.read()

    # Replace selector placeholder
    escaped_selector = selector.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
    code = script.replace('SELECTOR_PLACEHOLDER', f'"{escaped_selector}"')

    try:
        click.echo(f"Capturing element: {selector}")
        result = client.execute(code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})
        if response.get("error"):
            click.echo(f"Error: {response['error']}", err=True)
            if response.get("details"):
                click.echo(f"Details: {response['details']}", err=True)
            sys.exit(1)

        # Get data URL and decode
        data_url = response.get("dataUrl")
        if not data_url:
            click.echo("Error: No image data received", err=True)
            sys.exit(1)

        # Extract base64 data
        if ',' in data_url:
            base64_data = data_url.split(',', 1)[1]
        else:
            base64_data = data_url

        # Decode base64 to bytes
        try:
            image_data = base64.b64decode(base64_data)
        except Exception as e:
            click.echo(f"Error decoding image data: {e}", err=True)
            sys.exit(1)

        # Determine output path
        if output:
            output_path = Path(output)
        else:
            # Generate filename from selector and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_selector = "".join(c if c.isalnum() else "_" for c in selector)
            filename = f"screenshot_{safe_selector}_{timestamp}.png"
            output_path = Path.cwd() / filename

        # Save image
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with _builtin_open(output_path, 'wb') as f:
            f.write(image_data)

        size_kb = len(image_data) / 1024
        click.echo(f"Screenshot saved: {output_path}")
        click.echo(f"Size: {response.get('width')}x{response.get('height')}px ({size_kb:.1f} KB)")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
def watch():
    """Watch browser events in real-time."""
    pass


@watch.command()
def input():
    """
    Watch keyboard input in real-time.

    Streams all keyboard events from the browser to the terminal.
    Press Ctrl+C to stop watching.

    Example:
        zen watch input
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Start watching keyboard
    script_path = Path(__file__).parent / "scripts" / "watch_keyboard.js"
    with _builtin_open(script_path) as f:
        watch_code = f.read()

    try:
        result = client.execute(watch_code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error starting keyboard watcher: {result.get('error')}", err=True)
            sys.exit(1)

        click.echo("Watching keyboard input... (Press Ctrl+C to stop)")
        click.echo("")

        # Now continuously poll for keyboard events
        # We'll use a loop that executes code to check for new events
        poll_code = """
        (function() {
            if (!window.__ZEN_KEYBOARD_EVENTS__) {
                window.__ZEN_KEYBOARD_EVENTS__ = [];
            }
            const events = window.__ZEN_KEYBOARD_EVENTS__.splice(0);
            return events;
        })()
        """

        # Set up signal handler for Ctrl+C
        def stop_watching(sig, frame):
            cleanup_code = """
            (function() {
                const watchId = '__ZEN_KEYBOARD_WATCH__';
                if (window[watchId]) {
                    document.removeEventListener('keydown', window[watchId], true);
                    delete window[watchId];
                }
                if (window.__ZEN_KEYBOARD_EVENTS__) {
                    delete window.__ZEN_KEYBOARD_EVENTS__;
                }
                return 'Keyboard watcher stopped';
            })()
            """
            client.execute(cleanup_code, timeout=2.0)
            click.echo("\n\nStopped watching keyboard input.")
            sys.exit(0)

        signal.signal(signal.SIGINT, stop_watching)

        # Poll for events
        import time
        while True:
            result = client.execute(poll_code, timeout=1.0)
            if result.get("ok"):
                events = result.get("result", [])
                for event in events:
                    click.echo(event, nl=False)
                    sys.stdout.flush()

            time.sleep(0.1)  # Poll every 100ms

    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)


@cli.command()
def control():
    """
    Control the browser remotely from your terminal.

    All keyboard input from your terminal will be sent directly to the browser,
    allowing you to navigate, type, and interact with the page remotely.

    Supports:
    - Regular text input
    - Special keys (arrows, Enter, Tab, Escape, etc.)
    - Modifier keys (Ctrl, Alt, Shift, Cmd)

    Press Ctrl+D to exit control mode.

    Example:
        zen control
    """
    import sys
    import tty
    import termios
    import select

    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Load configuration
    control_config = zen_config.get_control_config()
    config_json = json.dumps(control_config)

    # Load control script
    script_path = Path(__file__).parent / "scripts" / "control.js"

    try:
        with _builtin_open(script_path) as f:
            script_template = f.read()
    except FileNotFoundError:
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    # Start control mode
    start_code = script_template.replace('ACTION_PLACEHOLDER', 'start')
    start_code = start_code.replace('KEY_DATA_PLACEHOLDER', '{}')
    start_code = start_code.replace('CONFIG_PLACEHOLDER', config_json)

    try:
        result = client.execute(start_code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error starting control mode: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})
        title = response.get('title', 'Unknown')

        click.echo(f"Now controlling: {title}")
        click.echo("Press Ctrl+D to exit\n")

        # Save terminal settings
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            # Put terminal in raw mode
            tty.setraw(fd)

            while True:
                # Check for notifications before reading input
                # Use select with timeout to allow polling
                readable, _, _ = select.select([sys.stdin], [], [], 0.1)  # 100ms timeout

                if not readable:
                    # No input available, check for notifications
                    try:
                        import requests
                        resp = requests.get(f'http://{client.host}:{client.port}/notifications', timeout=0.5)
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get('ok') and data.get('notifications'):
                                for notification in data['notifications']:
                                    if notification['type'] == 'refocus':
                                        message = notification['message']
                                        sys.stderr.write(f"\r\n{message}\r\n")
                                        sys.stderr.flush()
                                        # Speak if speak-all is enabled
                                        if control_config.get('speak-all'):
                                            try:
                                                subprocess.run(['say', message], check=False, timeout=5)
                                            except Exception:
                                                pass
                    except Exception:
                        # Silently ignore notification check errors
                        pass
                    continue

                # Read one character
                char = sys.stdin.read(1)

                # Handle Ctrl+D (EOF)
                if char == '\x04':  # Ctrl+D
                    break

                # Map character to key data
                key_data = {}

                # Special key mappings
                if char == '\x1b':  # Escape sequence
                    # Read next characters for arrow keys, etc.
                    next_char = sys.stdin.read(1)
                    if next_char == '[':
                        arrow = sys.stdin.read(1)
                        if arrow == 'A':
                            key_data = {'key': 'ArrowUp', 'code': 'ArrowUp'}
                        elif arrow == 'B':
                            key_data = {'key': 'ArrowDown', 'code': 'ArrowDown'}
                        elif arrow == 'C':
                            key_data = {'key': 'ArrowRight', 'code': 'ArrowRight'}
                        elif arrow == 'D':
                            key_data = {'key': 'ArrowLeft', 'code': 'ArrowLeft'}
                        elif arrow == 'Z':
                            # Shift+Tab
                            key_data = {'key': 'Tab', 'code': 'Tab', 'shift': True}
                        else:
                            # Unknown sequence, skip
                            continue
                    else:
                        # Just Escape key
                        key_data = {'key': 'Escape', 'code': 'Escape'}
                elif char == '\r' or char == '\n':
                    key_data = {'key': 'Enter', 'code': 'Enter'}
                elif char == '\t':
                    key_data = {'key': 'Tab', 'code': 'Tab'}
                elif char == '\x7f':  # Backspace
                    key_data = {'key': 'Backspace', 'code': 'Backspace'}
                elif ord(char) < 32:  # Control character
                    # Handle Ctrl+letter combinations
                    letter = chr(ord(char) + 96)
                    key_data = {'key': letter, 'code': f'Key{letter.upper()}', 'ctrl': True}
                else:
                    # Regular character
                    key_data = {'key': char, 'code': f'Key{char.upper()}' if char.isalpha() else ''}

                # Send key to browser
                send_code = script_template.replace('ACTION_PLACEHOLDER', 'send')
                send_code = send_code.replace('KEY_DATA_PLACEHOLDER', json.dumps(key_data))
                send_code = send_code.replace('CONFIG_PLACEHOLDER', config_json)

                result = client.execute(send_code, timeout=60.0)

                # Check if control needs reinitialization (e.g., after page reload)
                # The browser returns {ok: true, result: {ok: false, needsRestart: true}}
                if result.get("ok"):
                    response = result.get("result", {})
                    if isinstance(response, dict) and response.get("needsRestart"):
                        # Auto-restart control mode
                        # Write directly to stderr (works in raw mode)
                        sys.stderr.write("\r\n🔄 Reinitializing after navigation...\r\n")
                        sys.stderr.flush()

                        restart_result = client.execute(start_code, timeout=60.0)
                        if control_config.get('verbose-logging'):
                            sys.stderr.write(f"[CLI] Restart: {restart_result.get('ok')}\r\n")
                            sys.stderr.flush()

                        # Retry the key send
                        result = client.execute(send_code, timeout=60.0)

                        if result.get("ok"):
                            sys.stderr.write("✅ Control restored!\r\n")
                            sys.stderr.flush()

                if result.get("ok"):
                    # Check if we should speak the accessible name
                    response = result.get("result", {})
                    if control_config.get('speak-name') and 'accessibleName' in response:
                        accessible_name = response.get('accessibleName', '').strip()
                        role = response.get('role', '')

                        if accessible_name:
                            # Build the text to speak
                            speak_text = accessible_name

                            # Optionally announce role
                            if control_config.get('announce-role') and role:
                                speak_text = f"{role}, {speak_text}"

                            # Use macOS say command
                            try:
                                subprocess.run(['say', speak_text], check=False, timeout=5)
                            except Exception:
                                # Silently ignore if say command fails
                                pass

                    # Display verbose messages if enabled
                    if control_config.get('verbose'):
                        # Check for opening message (when pressing Enter on links/buttons)
                        if 'message' in response:
                            message = response['message']
                            sys.stderr.write(f"\r\n{message}\r\n")
                            sys.stderr.flush()
                            if control_config.get('speak-all'):
                                try:
                                    subprocess.run(['say', message], check=False, timeout=5)
                                except Exception:
                                    pass

                        # Check for "opened" message (right after click)
                        if 'openedMessage' in response:
                            message = response['openedMessage']
                            sys.stderr.write(f"{message}\r\n")
                            sys.stderr.flush()
                            if control_config.get('speak-all'):
                                try:
                                    subprocess.run(['say', message], check=False, timeout=5)
                                except Exception:
                                    pass

                        # Check for refocus message (after page navigation)
                        if 'refocusMessage' in response:
                            message = response['refocusMessage']
                            sys.stderr.write(f"{message}\r\n")
                            sys.stderr.flush()
                            if control_config.get('speak-all'):
                                try:
                                    subprocess.run(['say', message], check=False, timeout=5)
                                except Exception:
                                    pass
                else:
                    # Silently ignore errors, keep going
                    pass

        finally:
            # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

            # Stop control mode
            stop_code = script_template.replace('ACTION_PLACEHOLDER', 'stop')
            stop_code = stop_code.replace('KEY_DATA_PLACEHOLDER', '{}')
            stop_code = stop_code.replace('CONFIG_PLACEHOLDER', config_json)
            client.execute(stop_code, timeout=2.0)

            click.echo("\n\nControl mode ended.")

    except Exception as e:
        # Make sure to restore terminal
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except:
            pass
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)


@watch.command()
def all():
    """
    Watch all user interactions - keyboard, focus, and accessible names.

    Features:
    - Groups regular typing on single lines
    - Shows special keys (Tab, Enter, arrows, modifiers) on separate lines
    - Displays accessible name when tabbing to focusable elements

    Press Ctrl+C to stop watching.

    Example:
        zen watch all
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Load watch_all script
    script_path = Path(__file__).parent / "scripts" / "watch_all.js"

    try:
        with _builtin_open(script_path) as f:
            script_template = f.read()
    except FileNotFoundError:
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    # Start watching
    start_code = script_template.replace('ACTION_PLACEHOLDER', 'start')

    try:
        result = client.execute(start_code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error starting watcher: {result.get('error')}", err=True)
            sys.exit(1)

        click.echo("Watching all interactions... (Press Ctrl+C to stop)")
        click.echo("")

        # Poll code
        poll_code = script_template.replace('ACTION_PLACEHOLDER', 'poll')

        # Cleanup code
        stop_code = script_template.replace('ACTION_PLACEHOLDER', 'stop')

        # Set up signal handler for Ctrl+C
        def stop_watching(sig, frame):
            client.execute(stop_code, timeout=2.0)
            click.echo("\n\nStopped watching.")
            sys.exit(0)

        signal.signal(signal.SIGINT, stop_watching)

        # Poll for events
        import time
        while True:
            result = client.execute(poll_code, timeout=1.0)
            if result.get("ok"):
                response = result.get("result", {})
                if response.get("hasEvents"):
                    events = response.get("events", [])
                    for event in events:
                        event_type = event.get('type')

                        if event_type == 'text':
                            # Regular text - print on same line
                            click.echo(event.get('content', ''))

                        elif event_type == 'key':
                            # Special key - print with brackets
                            click.echo(f"[{event.get('content', '')}]")

                        elif event_type == 'focus':
                            # Focus change - show accessible name
                            accessible_name = event.get('accessibleName', '')
                            element = event.get('element', '')
                            role = event.get('role', '')

                            if accessible_name and accessible_name != element:
                                click.echo(f"→ Focus: {accessible_name} {element}")
                            else:
                                click.echo(f"→ Focus: {element}")

            time.sleep(0.1)  # Poll every 100ms

    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)


@cli.command()
def describe():
    """
    Generate an AI-powered description of the page for screen reader users.

    Extracts page structure (landmarks, headings, links, images, forms) and
    uses AI to create a concise, natural description perfect for blind users
    to understand what the page offers at a glance.

    Examples:
        zen describe
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Check if mods is available
    try:
        subprocess.run(["mods", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        click.echo("Error: 'mods' command not found. Please install mods first.", err=True)
        click.echo("Visit: https://github.com/charmbracelet/mods", err=True)
        sys.exit(1)

    # Load and execute the extraction script
    script_path = Path(__file__).parent / "scripts" / "extract_page_structure.js"

    if not script_path.exists():
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    try:
        with _builtin_open(script_path) as f:
            script = f.read()

        click.echo("Analyzing page structure...", err=True)
        result = client.execute(script, timeout=30.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        page_data = result.get("result", {})

        # Format the page data as a readable structure for the AI
        structured_info = []

        structured_info.append(f"PAGE TITLE: {page_data.get('title', 'Untitled')}")
        structured_info.append("")

        # Languages
        languages = page_data.get('languages', [])
        if languages:
            primary = _builtin_next((l for l in languages if l['type'] == 'primary'), None)
            alternates = [l for l in languages if l['type'] == 'alternate']

            lang_info = f"PRIMARY LANGUAGE: {primary['lang'] if primary else 'unknown'}"
            if alternates:
                alt_langs = ', '.join([l['lang'] for l in alternates])
                lang_info += f"\nALTERNATE LANGUAGES: {alt_langs}"
            structured_info.append(lang_info)
            structured_info.append("")

        # Landmarks
        landmarks = page_data.get('landmarks', {})
        if landmarks:
            structured_info.append("LANDMARKS:")
            for landmark, count in landmarks.items():
                structured_info.append(f"  - {landmark}: {count}")
            structured_info.append("")

        # Navigation
        navigation = page_data.get('navigation', [])
        if navigation:
            structured_info.append("NAVIGATION:")
            for nav in navigation:
                structured_info.append(f"  {nav['label']} ({nav['linkCount']} links)")
                if nav['links']:
                    top_links = [link['text'] for link in nav['links'][:8]]
                    structured_info.append(f"    Top items: {', '.join(top_links)}")
            structured_info.append("")

        # Headings
        headings = page_data.get('headings', [])
        heading_count = page_data.get('headingCount', len(headings))
        if headings:
            structured_info.append(f"HEADINGS: {heading_count} total")
            for h in headings:
                indent = "  " * h['level']
                structured_info.append(f"{indent}H{h['level']}: {h['text']}")
            if heading_count > len(headings):
                structured_info.append(f"  (Showing first {len(headings)} of {heading_count})")
            structured_info.append("")

        # Main content
        main_content = page_data.get('mainContent', {})
        if main_content:
            structured_info.append("MAIN CONTENT:")
            structured_info.append(f"  Word count: {main_content.get('wordCount', 0)}")
            structured_info.append(f"  Estimated reading time: {main_content.get('estimatedReadingTime', 0)} minutes")
            structured_info.append(f"  Paragraphs: {main_content.get('paragraphCount', 0)}")
            structured_info.append(f"  Lists: {main_content.get('listCount', 0)}")
            structured_info.append("")

        # Images
        images = page_data.get('images', [])
        if images:
            meaningful_images = [img for img in images if img['hasAlt']]
            decorative_images = [img for img in images if not img['hasAlt']]

            structured_info.append(f"IMAGES: {len(images)} significant images")
            if meaningful_images:
                structured_info.append(f"  With alt text: {len(meaningful_images)}")
                for img in meaningful_images[:3]:
                    structured_info.append(f"    - \"{img['alt']}\"")
            if decorative_images:
                structured_info.append(f"  Decorative/unlabeled: {len(decorative_images)}")
            structured_info.append("")

        # Forms
        forms = page_data.get('forms', [])
        if forms:
            structured_info.append(f"FORMS: {len(forms)}")
            for form in forms:
                structured_info.append(f"  {form['label']} ({form['fieldCount']} fields)")
                if form['fields']:
                    field_summary = ', '.join([f"{f['type']}" for f in form['fields'][:5]])
                    structured_info.append(f"    Fields: {field_summary}")
            structured_info.append("")

        # Footer
        footer = page_data.get('footer', {})
        if footer and footer.get('linkCount', 0) > 0:
            structured_info.append(f"FOOTER: {footer['linkCount']} links")
            if footer.get('links'):
                structured_info.append(f"  Includes: {', '.join(footer['links'])}")
            structured_info.append("")

        # Link summary
        link_summary = page_data.get('linkSummary', {})
        if link_summary:
            structured_info.append(f"LINKS: {link_summary.get('total', 0)} total ({link_summary.get('internal', 0)} internal, {link_summary.get('external', 0)} external)")
            structured_info.append("")

        # Read the prompt
        prompt_path = Path(__file__).parent.parent / "prompts" / "describe.prompt"

        if not prompt_path.exists():
            click.echo(f"Error: Prompt file not found: {prompt_path}", err=True)
            sys.exit(1)

        with _builtin_open(prompt_path) as f:
            prompt = f.read().strip()

        # Combine prompt with structured data
        full_input = f"{prompt}\n\n{'='*60}\nPAGE STRUCTURE DATA:\n{'='*60}\n\n" + "\n".join(structured_info)

        click.echo("Generating description...", err=True)

        # Call mods
        try:
            result = subprocess.run(
                ["mods"],
                input=full_input,
                text=True,
                capture_output=True,
                check=True
            )

            click.echo(result.stdout)

        except subprocess.CalledProcessError as e:
            click.echo(f"Error calling mods: {e}", err=True)
            if e.stderr:
                click.echo(e.stderr, err=True)
            sys.exit(1)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def outline():
    """
    Display the page's heading structure as a nested outline.

    Shows all headings (H1-H6 and ARIA headings) in a hierarchical view.
    Heading levels are shown in gray, text in white.

    Examples:
        zen outline
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Load and execute the extract_outline script
    script_path = Path(__file__).parent / "scripts" / "extract_outline.js"

    if not script_path.exists():
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    try:
        with _builtin_open(script_path) as f:
            script = f.read()

        result = client.execute(script, timeout=30.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        data = result.get("result", {})
        headings = data.get("headings", [])

        if not headings:
            click.echo("No headings found on this page.", err=True)
            sys.exit(0)

        # Display the outline with proper indentation
        for heading in headings:
            level = heading["level"]
            text = heading["text"]

            # Calculate indentation (3 spaces per level, starting at level 1)
            indent = "   " * (level - 1)

            # Format: H{level} in gray, text in white
            level_label = click.style(f"H{level}", fg="bright_black")
            heading_text = text

            # Truncate very long headings
            if len(heading_text) > 100:
                heading_text = heading_text[:97] + "..."

            click.echo(f"{indent}{level_label} {heading_text}")

        # Show summary
        click.echo("", err=True)
        click.echo(f"Total: {len(headings)} headings", err=True)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _enrich_link_metadata(url: str) -> dict:
    """
    Fetch metadata for a single external link using curl.

    Returns dict with: http_status, mime_type, file_size, filename, page_title, page_language
    """
    import re

    enrichment = {
        "http_status": None,
        "mime_type": None,
        "file_size": None,
        "filename": None,
        "page_title": None,
        "page_language": None
    }

    try:
        # First, do a HEAD request to get headers
        head_result = subprocess.run(
            [
                "curl", "-L", "-I", "-s", "-m", "5",
                "--user-agent", "zen-bridge/1.0",
                url
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        if head_result.returncode != 0:
            return enrichment

        headers = head_result.stdout

        # Parse HTTP status code
        status_match = re.search(r'HTTP/[\d.]+ (\d+)', headers)
        if status_match:
            enrichment["http_status"] = int(status_match.group(1))

        # Parse Content-Type
        content_type_match = re.search(r'(?i)^Content-Type:\s*([^\r\n;]+)', headers, re.MULTILINE)
        if content_type_match:
            enrichment["mime_type"] = content_type_match.group(1).strip()

        # Parse Content-Length
        content_length_match = re.search(r'(?i)^Content-Length:\s*(\d+)', headers, re.MULTILINE)
        if content_length_match:
            enrichment["file_size"] = int(content_length_match.group(1))

        # Parse Content-Disposition for filename
        content_disp_match = re.search(r'(?i)^Content-Disposition:.*filename[*]?=["\']?([^"\'\r\n;]+)', headers, re.MULTILINE)
        if content_disp_match:
            enrichment["filename"] = content_disp_match.group(1).strip()

        # Parse Content-Language
        content_lang_match = re.search(r'(?i)^Content-Language:\s*([^\r\n;]+)', headers, re.MULTILINE)
        if content_lang_match:
            enrichment["page_language"] = content_lang_match.group(1).strip()

        # If this looks like HTML, fetch partial content to get title and lang
        mime_type = enrichment.get("mime_type", "").lower()
        if mime_type and ("html" in mime_type or mime_type == "text/html"):
            # Fetch first 16KB of content
            get_result = subprocess.run(
                [
                    "curl", "-L", "-s", "-m", "5",
                    "--user-agent", "zen-bridge/1.0",
                    "--max-filesize", "16384",
                    url
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if get_result.returncode == 0:
                html_content = get_result.stdout

                # Extract page title
                title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
                if title_match:
                    # Decode HTML entities and clean up
                    title = title_match.group(1).strip()
                    title = re.sub(r'\s+', ' ', title)  # Normalize whitespace
                    enrichment["page_title"] = title

                # Extract language from <html lang="...">
                if not enrichment["page_language"]:
                    lang_match = re.search(r'<html[^>]+lang=["\']?([^"\'\s>]+)', html_content, re.IGNORECASE)
                    if lang_match:
                        enrichment["page_language"] = lang_match.group(1).strip()

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, Exception):
        # Silently fail - return partial data
        pass

    return enrichment


def _enrich_external_links(links: list) -> list:
    """
    Enrich external links with metadata using parallel curl requests.
    Only processes up to 50 external links.

    Returns the same list with enrichment data added to external links.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Filter to get external links only
    external_links = [link for link in links if link.get("external") or link.get("type") == "external"]

    # Check if we should skip enrichment
    if len(external_links) > 50:
        return links

    # Create a mapping of URL to link object
    url_to_link = {}
    urls_to_enrich = []

    for link in external_links:
        url = link.get("url") or link.get("href")
        if url:
            url_to_link[url] = link
            urls_to_enrich.append(url)

    # Fetch metadata in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(_enrich_link_metadata, url): url for url in urls_to_enrich}

        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                enrichment = future.result()
                # Add enrichment data to the link object
                link_obj = url_to_link[url]
                link_obj.update(enrichment)
            except Exception:
                # Skip failed enrichments
                pass

    return links


@cli.command()
@click.option("--only-internal", is_flag=True, help="Show only internal links (same domain)")
@click.option("--only-external", is_flag=True, help="Show only external links (different domain)")
@click.option("--alphabetically", is_flag=True, help="Sort links alphabetically")
@click.option("--only-urls", is_flag=True, help="Show only URLs without anchor text")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON with detailed link information")
@click.option("--enrich-external", is_flag=True, help="Fetch additional metadata for external links (MIME type, file size, page title, language, HTTP status)")
def links(only_internal, only_external, alphabetically, only_urls, output_json, enrich_external):
    """
    Extract all links from the current page.

    By default, shows all links with their anchor text.
    Use filters to show only internal or external links.

    Examples:
        zen links                           # All links with anchor text
        zen links --only-internal           # Only links on same domain
        zen links --only-external           # Only links to other domains
        zen links --alphabetically          # Sort alphabetically
        zen links --only-urls               # Show only URLs
        zen links --only-external --only-urls  # External URLs only
        zen links --enrich-external         # Add metadata for external links
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Check for conflicting flags
    if only_internal and only_external:
        click.echo("Error: Cannot use --only-internal and --only-external together", err=True)
        sys.exit(1)

    # Load and execute the extract_links script
    script_path = Path(__file__).parent / "scripts" / "extract_links.js"

    if not script_path.exists():
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    try:
        with _builtin_open(script_path) as f:
            script = f.read()

        result = client.execute(script, timeout=30.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        data = result.get("result", {})
        all_links = data.get("links", [])
        domain = data.get("domain", "")

        if not all_links:
            click.echo("No links found on this page.", err=True)
            sys.exit(0)

        # Filter links
        filtered_links = all_links
        if only_internal:
            filtered_links = [link for link in all_links if link["type"] == "internal"]
        elif only_external:
            filtered_links = [link for link in all_links if link["type"] == "external"]

        if not filtered_links:
            filter_type = "internal" if only_internal else "external" if only_external else "total"
            click.echo(f"No {filter_type} links found.", err=True)
            sys.exit(0)

        # Enrich external links if requested
        if enrich_external:
            filtered_links = _enrich_external_links(filtered_links)

        # Sort if requested
        if alphabetically:
            if only_urls:
                # Sort by URL
                filtered_links.sort(key=lambda x: x["href"].lower())
            else:
                # Sort by anchor text
                filtered_links.sort(key=lambda x: x["text"].lower())

        # If JSON output is requested, output JSON and exit
        if output_json:
            import json
            output_data = {
                "links": filtered_links,
                "total": len(filtered_links),
                "domain": domain
            }
            click.echo(json.dumps(output_data, indent=2))
            return

        # Output links
        if only_urls:
            # Just print URLs, one per line
            for link in filtered_links:
                click.echo(link["href"])
        else:
            # Print with anchor text
            for link in filtered_links:
                text = link["text"]
                href = link["href"]
                # Truncate long text
                if len(text) > 60:
                    text = text[:57] + "..."
                # Show type indicator
                type_indicator = "↗" if link["type"] == "external" else "→"
                click.echo(f"{type_indicator} {text}")
                click.echo(f"  {href}")

                # Show enrichment data if available
                if enrich_external and link.get("type") == "external":
                    enrichment_lines = []

                    if link.get("http_status") is not None:
                        enrichment_lines.append(f"HTTP {link['http_status']}")

                    if link.get("mime_type"):
                        enrichment_lines.append(link["mime_type"])

                    if link.get("file_size") is not None:
                        # Format file size in human-readable format
                        size = link["file_size"]
                        if size < 1024:
                            size_str = f"{size} B"
                        elif size < 1024 * 1024:
                            size_str = f"{size / 1024:.1f} KB"
                        elif size < 1024 * 1024 * 1024:
                            size_str = f"{size / (1024 * 1024):.1f} MB"
                        else:
                            size_str = f"{size / (1024 * 1024 * 1024):.1f} GB"
                        enrichment_lines.append(size_str)

                    if link.get("filename"):
                        enrichment_lines.append(f"File: {link['filename']}")

                    if link.get("page_title"):
                        title = link["page_title"]
                        if len(title) > 60:
                            title = title[:57] + "..."
                        enrichment_lines.append(f"Title: {title}")

                    if link.get("page_language"):
                        enrichment_lines.append(f"Lang: {link['page_language']}")

                    if enrichment_lines:
                        click.echo(f"  {' | '.join(enrichment_lines)}")

                click.echo("")

        # Show summary
        total = len(all_links)
        shown = len(filtered_links)
        if only_internal or only_external:
            filter_type = "internal" if only_internal else "external"
            click.echo(f"Showing {shown} {filter_type} links (of {total} total)", err=True)
        else:
            click.echo(f"Total: {shown} links", err=True)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--format", type=click.Choice(["summary", "full"]), default="summary", help="Output format (summary or full article)")
def summarize(format):
    """
    Summarize the current article using AI.

    Extracts article content using Mozilla Readability and generates
    a concise summary using the mods command.

    Examples:
        zen summarize                    # Get AI summary
        zen summarize --format full      # Show full extracted article
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Check if mods is available
    if format == "summary":
        try:
            subprocess.run(["mods", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            click.echo("Error: 'mods' command not found. Please install mods first.", err=True)
            click.echo("Visit: https://github.com/charmbracelet/mods", err=True)
            sys.exit(1)

    # Load and execute the extract_article script
    script_path = Path(__file__).parent / "scripts" / "extract_article.js"

    if not script_path.exists():
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    try:
        with _builtin_open(script_path) as f:
            script = f.read()

        click.echo("Extracting article content...", err=True)
        result = client.execute(script, timeout=30.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        article = result.get("result", {})

        if article.get("error"):
            click.echo(f"Error: {article['error']}", err=True)
            sys.exit(1)

        title = article.get("title", "Untitled")
        content = article.get("content", "")
        byline = article.get("byline", "")

        if not content:
            click.echo("Error: No content extracted. This page may not be an article.", err=True)
            sys.exit(1)

        # If full format, just show the extracted article
        if format == "full":
            click.echo(f"Title: {title}")
            if byline:
                click.echo(f"By: {byline}")
            click.echo("")
            click.echo(content)
            return

        # Generate summary using mods
        click.echo(f"Generating summary for: {title}", err=True)

        # Read the prompt file
        prompt_path = Path(__file__).parent.parent / "prompts" / "summary.prompt"

        if not prompt_path.exists():
            click.echo(f"Error: Prompt file not found: {prompt_path}", err=True)
            sys.exit(1)

        with _builtin_open(prompt_path) as f:
            prompt = f.read().strip()

        # Prepare the input for mods
        full_input = f"{prompt}\n\nTitle: {title}\n\n{content}"

        # Call mods
        try:
            result = subprocess.run(
                ["mods"],
                input=full_input,
                text=True,
                capture_output=True,
                check=True
            )

            if byline:
                click.echo(f"By: {byline}")
                click.echo("")
            click.echo(result.stdout)

        except subprocess.CalledProcessError as e:
            click.echo(f"Error calling mods: {e}", err=True)
            if e.stderr:
                click.echo(e.stderr, err=True)
            sys.exit(1)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
