"""E-mailhandtekening in de stijl van de nieuwe website (2026-10-08)."""
import pathlib
from playwright.sync_api import sync_playwright
D = pathlib.Path(__file__).parent
ICON = '''<svg width="96" height="96" viewBox="0 0 44 44" fill="none"><rect x="19" y="6" width="6" height="32" rx="1" fill="#FFFFFF"/><path d="M8 36 Q14 28 22 22 Q30 16 36 8" stroke="#9DBBE3" stroke-width="2.6" fill="none" stroke-linecap="round"/><circle cx="8" cy="36" r="2.8" fill="#9DBBE3"/><circle cx="36" cy="8" r="2.8" fill="#9DBBE3"/></svg>'''
LOGO_URL = 'https://insightance.ai/images/email-logo.png'

def sig(img_src):
    # tabel + inline stijlen: zo blijft het in Gmail, Outlook en Apple Mail heel
    return f'''<table cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;font-family:Arial,Helvetica,sans-serif;">
  <tr>
    <td style="padding:0 16px 0 0;vertical-align:middle;"><a href="https://insightance.ai/?utm_source=email&amp;utm_medium=handtekening" style="text-decoration:none;"><img src="{img_src}" width="64" height="64" alt="Insightance" style="display:block;width:64px;height:64px;border:0;border-radius:12px;"></a></td>
    <td style="padding:2px 0 2px 16px;border-left:2px solid #1F5EFF;vertical-align:middle;">
      <div style="font-size:16px;font-weight:bold;color:#17345F;line-height:22px;">Oussama Hlalouch</div>
      <div style="font-size:13px;color:#465369;line-height:19px;">Founder, Insightance</div>
      <div style="font-size:12px;color:#5E6C84;line-height:18px;">AI-automatisering voor ondernemers</div>
      <div style="font-size:12px;line-height:18px;padding-top:6px;"><a href="https://insightance.ai/?utm_source=email&amp;utm_medium=handtekening" style="color:#1F5EFF;font-weight:bold;text-decoration:none;">insightance.ai</a><span style="color:#9DBBE3;">&nbsp;&nbsp;·&nbsp;&nbsp;</span><a href="https://wa.me/31653340362" style="color:#465369;text-decoration:none;">+31 6 53340362</a></div>
    </td>
  </tr>
</table>'''

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    # 1. logo voor in de mail (2x zo groot voor scherpe weergave), afgeronde hoeken
    pg = b.new_page(viewport={'width': 128, 'height': 128})
    pg.set_content(f'<html><body style="margin:0;background:transparent"><div id="c" style="width:128px;height:128px;border-radius:24px;background:#17345F;display:flex;align-items:center;justify-content:center">{ICON}</div></body></html>')
    pg.locator('#c').screenshot(path=str(D / 'email-logo.png'), omit_background=True); pg.close()
    # 2. voorbeeld zoals de ontvanger hem ziet
    pg = b.new_page(viewport={'width': 640, 'height': 220}, device_scale_factor=2)
    pg.set_content(f'<html><body style="margin:0;padding:28px;background:#fff;font-family:Arial"><p style="font-size:14px;color:#222;margin:0 0 18px">Met vriendelijke groet,</p>{sig("data:image/png;base64," + __import__("base64").b64encode((D / "email-logo.png").read_bytes()).decode())}</body></html>')
    pg.wait_for_timeout(300); pg.screenshot(path=str(D / '_handtekening-voorbeeld.png')); pg.close()
    b.close()
# 3. pagina om te kopiëren naar Gmail (met het logo vanaf de website)
(D / 'handtekening-kopieren.html').write_text(f'''<!doctype html><html lang="nl"><head><meta charset="utf-8"><title>Handtekening kopiëren</title></head>
<body style="font-family:Arial,sans-serif;padding:32px;max-width:720px;color:#17345F">
<h2 style="margin:0 0 6px">Je nieuwe e-mailhandtekening</h2>
<p style="color:#465369;margin:0 0 24px">Selecteer alles in het kader hieronder (klik erin, dan Ctrl+A), kopieer het (Ctrl+C) en plak het in Gmail bij Instellingen &gt; Handtekening (Ctrl+V).</p>
<div contenteditable="true" style="border:1px dashed #C9D5E4;border-radius:12px;padding:24px;outline:none">{sig(LOGO_URL)}</div>
</body></html>''', encoding='utf-8')
print('ok')
