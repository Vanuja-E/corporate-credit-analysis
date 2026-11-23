# Validation against Form 10-K financial statements

The model amount is the figure produced from the SEC companyfacts cache. The 10-K amount is the figure read from the filing cited on the row. Dollars, not millions. A match is a difference below one dollar.

Microsoft's fiscal 2025 Form 10-K is the primary hand check. Revenue, operating income, depreciation, amortization, the debt lines, interest expense, and the two ratios below were read from that filing. The other issuers are the same test on the fiscal 2025 statements.

| Company | Period end | Item | Model | 10-K | Match | Filing |
| --- | --- | --- | ---: | ---: | --- | --- |
| MSFT | 2025-06-30 | Revenue | 281,724,000,000 | 281,724,000,000 | yes | https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm |
| MSFT | 2025-06-30 | Operating income | 128,528,000,000 | 128,528,000,000 | yes | https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm |
| MSFT | 2025-06-30 | Depreciation | 22,000,000,000 | 22,000,000,000 | yes | https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm |
| MSFT | 2025-06-30 | Amortization of intangibles | 6,000,000,000 | 6,000,000,000 | yes | https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm |
| MSFT | 2025-06-30 | D&A used in EBITDA | 28,000,000,000 | 28,000,000,000 | yes | https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm |
| MSFT | 2025-06-30 | Interest burden | 2,385,000,000 | 2,385,000,000 | yes | https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm |
| MSFT | 2025-06-30 | Short-term borrowings | 0 | 0 | yes | https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm |
| MSFT | 2025-06-30 | Current portion of long-term debt | 2,999,000,000 | 2,999,000,000 | yes | https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm |
| MSFT | 2025-06-30 | Long-term debt | 40,152,000,000 | 40,152,000,000 | yes | https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm |
| MSFT | 2025-06-30 | Total debt | 43,151,000,000 | 43,151,000,000 | yes | https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm |
| MSFT | 2025-06-30 | Cash | 30,242,000,000 | 30,242,000,000 | yes | https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm |
| MSFT | 2025-06-30 | Cash from operations | 136,162,000,000 | 136,162,000,000 | yes | https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm |
| MSFT | 2025-06-30 | Capital expenditure | 64,551,000,000 | 64,551,000,000 | yes | https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm |
| MSFT | 2025-06-30 | Current assets | 191,131,000,000 | 191,131,000,000 | yes | https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm |
| MSFT | 2025-06-30 | Current liabilities | 141,218,000,000 | 141,218,000,000 | yes | https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm |
| MSFT | 2025-06-30 | Inventory | 938,000,000 | 938,000,000 | yes | https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm |
| MSFT | 2025-06-30 | Stockholders' equity | 343,479,000,000 | 343,479,000,000 | yes | https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm |
| MSFT | 2025-06-30 | EBITDA | 156,528,000,000 | 156,528,000,000 | yes | https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm |
| PEP | 2025-12-27 | Revenue | 93,925,000,000 | 93,925,000,000 | yes | https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm |
| PEP | 2025-12-27 | Operating income | 11,498,000,000 | 11,498,000,000 | yes | https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm |
| PEP | 2025-12-27 | D&A used in EBITDA | 3,451,000,000 | 3,451,000,000 | yes | https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm |
| PEP | 2025-12-27 | Income-statement interest tag | 1,121,000,000 | 1,121,000,000 | yes | https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm |
| PEP | 2025-12-27 | Current portion of long-term debt | 4,030,000,000 | 4,030,000,000 | yes | https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm |
| PEP | 2025-12-27 | Long-term debt | 42,321,000,000 | 42,321,000,000 | yes | https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm |
| PEP | 2025-12-27 | Short-term borrowings | 2,831,000,000 | 2,831,000,000 | yes | https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm |
| PEP | 2025-12-27 | Total debt | 49,182,000,000 | 49,182,000,000 | yes | https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm |
| PEP | 2025-12-27 | Cash | 9,159,000,000 | 9,159,000,000 | yes | https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm |
| HON | 2025-12-31 | Revenue | 37,442,000,000 | 37,442,000,000 | yes | https://www.sec.gov/Archives/edgar/data/773840/000077384026000013/hon-20251231.htm |
| HON | 2025-12-31 | Operating income | 8,127,000,000 | 8,127,000,000 | yes | https://www.sec.gov/Archives/edgar/data/773840/000077384026000013/hon-20251231.htm |
| HON | 2025-12-31 | D&A used in EBITDA | 1,388,000,000 | 1,388,000,000 | yes | https://www.sec.gov/Archives/edgar/data/773840/000077384026000013/hon-20251231.htm |
| HON | 2025-12-31 | Interest burden | 1,344,000,000 | 1,344,000,000 | yes | https://www.sec.gov/Archives/edgar/data/773840/000077384026000013/hon-20251231.htm |
| HON | 2025-12-31 | Short-term borrowings | 5,893,000,000 | 5,893,000,000 | yes | https://www.sec.gov/Archives/edgar/data/773840/000077384026000013/hon-20251231.htm |
| HON | 2025-12-31 | Current portion of long-term debt | 1,546,000,000 | 1,546,000,000 | yes | https://www.sec.gov/Archives/edgar/data/773840/000077384026000013/hon-20251231.htm |
| HON | 2025-12-31 | Long-term debt | 27,141,000,000 | 27,141,000,000 | yes | https://www.sec.gov/Archives/edgar/data/773840/000077384026000013/hon-20251231.htm |
| HON | 2025-12-31 | Finance lease liability | 64,000,000 | 64,000,000 | yes | https://www.sec.gov/Archives/edgar/data/773840/000077384026000013/hon-20251231.htm |
| HON | 2025-12-31 | Total debt | 34,516,000,000 | 34,516,000,000 | yes | https://www.sec.gov/Archives/edgar/data/773840/000077384026000013/hon-20251231.htm |
| HON | 2025-12-31 | Cash | 12,487,000,000 | 12,487,000,000 | yes | https://www.sec.gov/Archives/edgar/data/773840/000077384026000013/hon-20251231.htm |
| KHC | 2025-12-27 | Revenue | 24,942,000,000 | 24,942,000,000 | yes | https://www.sec.gov/Archives/edgar/data/1637459/000163745926000009/khc-20251227.htm |
| KHC | 2025-12-27 | Operating income | -4,669,000,000 | -4,669,000,000 | yes | https://www.sec.gov/Archives/edgar/data/1637459/000163745926000009/khc-20251227.htm |
| KHC | 2025-12-27 | D&A used in EBITDA | 968,000,000 | 968,000,000 | yes | https://www.sec.gov/Archives/edgar/data/1637459/000163745926000009/khc-20251227.htm |
| KHC | 2025-12-27 | Interest burden | 947,000,000 | 947,000,000 | yes | https://www.sec.gov/Archives/edgar/data/1637459/000163745926000009/khc-20251227.htm |
| KHC | 2025-12-27 | Short-term borrowings | 0 | 0 | yes | https://www.sec.gov/Archives/edgar/data/1637459/000163745926000009/khc-20251227.htm |
| KHC | 2025-12-27 | Current portion of long-term debt | 1,908,000,000 | 1,908,000,000 | yes | https://www.sec.gov/Archives/edgar/data/1637459/000163745926000009/khc-20251227.htm |
| KHC | 2025-12-27 | Long-term debt | 19,311,000,000 | 19,311,000,000 | yes | https://www.sec.gov/Archives/edgar/data/1637459/000163745926000009/khc-20251227.htm |
| KHC | 2025-12-27 | Finance lease liability | 160,000,000 | 160,000,000 | yes | https://www.sec.gov/Archives/edgar/data/1637459/000163745926000009/khc-20251227.htm |
| KHC | 2025-12-27 | Total debt | 21,059,000,000 | 21,059,000,000 | yes | https://www.sec.gov/Archives/edgar/data/1637459/000163745926000009/khc-20251227.htm |
| KHC | 2025-12-27 | Impairment losses | 9,306,000,000 | 9,306,000,000 | yes | https://www.sec.gov/Archives/edgar/data/1637459/000163745926000009/khc-20251227.htm |
| CCL | 2025-11-30 | Revenue | 26,622,000,000 | 26,622,000,000 | yes | https://www.sec.gov/Archives/edgar/data/815097/000081509726000007/ccl-20251130.htm |
| CCL | 2025-11-30 | Operating income | 4,483,000,000 | 4,483,000,000 | yes | https://www.sec.gov/Archives/edgar/data/815097/000081509726000007/ccl-20251130.htm |
| CCL | 2025-11-30 | D&A used in EBITDA | 2,790,000,000 | 2,790,000,000 | yes | https://www.sec.gov/Archives/edgar/data/815097/000081509726000007/ccl-20251130.htm |
| CCL | 2025-11-30 | Interest burden | 1,349,000,000 | 1,349,000,000 | yes | https://www.sec.gov/Archives/edgar/data/815097/000081509726000007/ccl-20251130.htm |
| CCL | 2025-11-30 | Short-term borrowings | 0 | 0 | yes | https://www.sec.gov/Archives/edgar/data/815097/000081509726000007/ccl-20251130.htm |
| CCL | 2025-11-30 | Current portion of long-term debt | 2,603,000,000 | 2,603,000,000 | yes | https://www.sec.gov/Archives/edgar/data/815097/000081509726000007/ccl-20251130.htm |
| CCL | 2025-11-30 | Long-term debt | 24,037,000,000 | 24,037,000,000 | yes | https://www.sec.gov/Archives/edgar/data/815097/000081509726000007/ccl-20251130.htm |
| CCL | 2025-11-30 | Total debt | 26,640,000,000 | 26,640,000,000 | yes | https://www.sec.gov/Archives/edgar/data/815097/000081509726000007/ccl-20251130.htm |

## Microsoft fiscal 2025 ratios

The income statement reports revenue of $281,724 million and operating income of $128,528 million. The debt lines are short-term debt of $0, current portion of long-term debt of $2,999 million, and long-term debt of $40,152 million. Interest expense in the other-income note is $2,385 million. Depreciation of $22,000 million and amortization of intangible assets of $6,000 million are the us-gaap facts in that filing. EBITDA in this model is $156,528 million, the sum of operating income and those two amounts. The cash-flow line 'depreciation, amortization, and other' is $34,153 million. The $6,153 million difference is the 'other' component and is not included in EBITDA.

Debt / EBITDA = 43,151,000,000 / 156,528,000,000 = 0.2757x.
EBITDA / Interest = 156,528,000,000 / 2,385,000,000 = 65.63x.

Both ratios use only the tied amounts above. Debt is short-term debt plus the current portion of long-term debt plus long-term debt. Finance leases and operating leases are not in that total. EBITDA is operating income plus depreciation plus amortization of intangibles.

## Notes on the other filings

**PEP.** Short-term debt obligations on the balance sheet are $6,861 million. The debt note splits that into current maturities of long-term debt of $4,030 million and the remainder, which is commercial paper and other short-term debt. Long-term debt obligations are $42,321 million. Total debt is $49,182 million. The income-statement line 'net interest expense and other' is $1,121 million. Cash interest paid, disclosed in the supplemental cash-flow information, is the coverage denominator when the 25 percent rule applies. Filing: https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm

**HON.** The balance sheet reports commercial paper and other short-term borrowings of $5,893 million, current maturities of long-term debt of $1,546 million, and long-term debt of $27,141 million. Those debt lines include finance lease liabilities of $64 million, which this model subtracts. Operating lease liabilities are not added. Interest and other financial charges are $1,344 million. Depreciation and amortization in the cash-flow discussion is $1,388 million. Filing: https://www.sec.gov/Archives/edgar/data/773840/000077384026000013/hon-20251231.htm

**KHC.** Operating income is a loss of $4,669 million. The filing presents impairment losses of $9,306 million above that line. EBITDA does not add the impairment back. Current portion of long-term debt is $1,908 million and long-term debt is $19,311 million. Finance lease obligations of $160 million are subtracted because the tagged debt concepts include capital leases. Interest expense is $947 million. Filing: https://www.sec.gov/Archives/edgar/data/1637459/000163745926000009/khc-20251227.htm

**CCL.** Total revenues are $26,622 million and operating income is $4,483 million. Current portion of long-term debt is $2,603 million and long-term debt is $24,037 million. The note total, net of unamortized debt issuance costs and discounts, is $26,640 million. Interest expense, net of capitalized interest, is $1,349 million. Operating lease liabilities are presented separately and are not in total debt. Filing: https://www.sec.gov/Archives/edgar/data/815097/000081509726000007/ccl-20251130.htm

No amount in this file was typed in as a substitute for a missing filing figure. Where the model and the 10-K differ, the match column says NO.
