"""Explicit Amazon Japan offer; link format verified in Amazon Associates help."""
from html import escape
KU_URL = 'https://www.amazon.co.jp/kindle-dbs/hz/signup?tag=tsukiproduct-22'
SOURCE = 'https://affiliate.amazon.co.jp/help/node/topic/GDFUA9UXMWT4L5UR'

def kindle(lang='ja'):
    en = lang == 'en'
    label = 'Advertisement · Amazon Associate' if en else '広告 · Amazonアソシエイト'
    title = 'Explore books beyond the headlines' if en else 'ニュースで気になったテーマを、本でも学ぶ'
    description = 'Explore Kindle Unlimited on Amazon Japan. Check whether the books you want are included before subscribing.' if en else 'Kindle Unlimitedで関連する本を探す選択肢もあります。読みたい本が対象に含まれているか、登録前に確認してください。'
    conditions = 'Check current fees, renewal, cancellation and trial eligibility on Amazon. Books mentioned on SIGNAL are not necessarily included. Japanese marketplace.' if en else '料金・更新・解約方法・無料体験の対象条件はAmazonで確認してください。当サイトで紹介する本が読み放題対象とは限りません。'
    cta = 'Check Kindle Unlimited on Amazon Japan ↗' if en else 'Kindle Unlimitedの対象・利用条件を見る ↗'
    return f'<section class="rail-block amazon-offer" aria-label="{label}"><p class="ad-label">{label}</p><h2>{title}</h2><p>{description}</p><a class="amazon-cta" href="{escape(KU_URL)}" data-signal-event="affiliate_click" data-offer="kindle-unlimited" target="_blank" rel="sponsored noopener noreferrer">{cta}</a><p class="offer-note">{conditions}</p></section>'
