import unittest
from datetime import datetime, timezone, timedelta
from daily_brief import picks,render
class BriefTests(unittest.TestCase):
 def test_fresh_diverse_and_translated(self):
  now=datetime.now(timezone.utc)
  def item(n,hours=1,source=None):
   return dict(id=str(n),source=source or str(n),date=(now-timedelta(hours=hours)).isoformat(),score=9,url=f'https://example.com/{n}',title_ja='<AI>',title_en='AI',summary_ja='変更',summary_en='Change')
  data=[item(0,100),item(1,source='same'),item(2,source='same'),item(3),item(4),item(5)]
  selected=picks(data,now);self.assertEqual(len(selected),3);self.assertEqual(len({i['source'] for i in selected}),3);self.assertNotIn('0',[i['id'] for i in selected])
  html=render(data,'ja');self.assertIn('&lt;AI&gt;',html);self.assertNotIn('<AI>',html)
 def test_no_fake_brief(self):
  self.assertEqual(render([],'ja'),'')
  self.assertEqual(picks([{'score':10,'date':'invalid'}]),[])
if __name__=='__main__':unittest.main()
